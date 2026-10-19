"""Executable data contract for the repaired maintenance database."""

import argparse
from datetime import date
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateTable


class ContractModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class Machine(ContractModel):
    machine_id: int = Field(ge=1)
    serial_no: str = Field(min_length=4)
    site: str = Field(min_length=1)
    installed: date

    @field_validator("serial_no")
    @classmethod
    def serial_has_prefix(cls, value: str) -> str:
        if not value.startswith("SN-"):
            raise ValueError("serial numbers must start with 'SN-'")
        return value


class Part(ContractModel):
    part_no: str = Field(pattern=r"^P-[0-9]+$")
    description: str = Field(min_length=1)
    unit_price: Decimal = Field(ge=Decimal("0"), max_digits=9, decimal_places=2)


class Technician(ContractModel):
    technician_id: int = Field(ge=1)
    name: str = Field(min_length=1)


class MaintenanceJob(ContractModel):
    job_id: int = Field(ge=1)
    machine_id: int = Field(ge=1)
    technician_id: int = Field(ge=1)
    done_on: date
    part_nos: list[str] = Field(default_factory=list)

    @field_validator("part_nos")
    @classmethod
    def parts_are_unique_and_well_formed(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("a part may appear only once in a maintenance job")
        if any(not value.startswith("P-") for value in values):
            raise ValueError("part numbers must start with 'P-'")
        return values


metadata = MetaData()

machine_t = Table(
    "machine",
    metadata,
    Column("machine_id", Integer, primary_key=True),
    Column("serial_no", String, nullable=False),
    Column("site", String, nullable=False),
    Column("installed", Date, nullable=False),
    UniqueConstraint("serial_no", name="uq_machine_serial"),
    CheckConstraint("machine_id > 0", name="ck_machine_id_positive"),
    CheckConstraint("serial_no LIKE 'SN-%'", name="ck_machine_serial_prefix"),
)

part_t = Table(
    "part",
    metadata,
    Column("part_no", String, primary_key=True),
    Column("description", String, nullable=False),
    Column("unit_price", Numeric(9, 2), nullable=False),
    CheckConstraint("unit_price >= 0", name="ck_part_price_nonnegative"),
)

technician_t = Table(
    "technician",
    metadata,
    Column("technician_id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    UniqueConstraint("name", name="uq_technician_name"),
)

maint_job_t = Table(
    "maint_job",
    metadata,
    Column("job_id", Integer, primary_key=True),
    Column("machine_id", Integer, ForeignKey("machine.machine_id"), nullable=False),
    Column("technician_id", Integer, ForeignKey("technician.technician_id"), nullable=False),
    Column("done_on", Date, nullable=False),
)

job_part_t = Table(
    "job_part",
    metadata,
    Column("job_id", Integer, ForeignKey("maint_job.job_id"), primary_key=True),
    Column("part_no", String, ForeignKey("part.part_no"), primary_key=True),
)


def make_engine(database: str = ":memory:") -> Engine:
    url = "sqlite://" if database == ":memory:" else f"sqlite:///{Path(database).as_posix()}"
    engine = create_engine(url)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    return engine


def ddl_for(engine: Engine) -> str:
    return "\n\n".join(
        f"{str(CreateTable(table).compile(engine)).strip()};"
        for table in metadata.sorted_tables
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default=":memory:")
    parser.add_argument("--ddl-output")
    args = parser.parse_args()
    engine = make_engine(args.database)
    metadata.create_all(engine)
    ddl = ddl_for(engine)
    if args.ddl_output:
        Path(args.ddl_output).write_text(ddl, encoding="utf-8")
    print(ddl, end="")
    with engine.connect() as connection:
        status = connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
        print(f"foreign_keys={status}")


if __name__ == "__main__":
    main()
