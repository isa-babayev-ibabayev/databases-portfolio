from datetime import date
from decimal import Decimal
import importlib.util
from pathlib import Path
import tempfile
import unittest

from pydantic import ValidationError
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError


MODULE_PATH = Path(__file__).parents[1] / "contract.py"
SPEC = importlib.util.spec_from_file_location("module02_contract", MODULE_PATH)
contract = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(contract)


class PydanticContractTests(unittest.TestCase):
    def test_valid_models_and_structured_parts(self):
        machine = contract.Machine(
            machine_id=1, serial_no="SN-100", site="Bielefeld", installed="2024-01-31"
        )
        job = contract.MaintenanceJob(
            job_id=1, machine_id=1, technician_id=1,
            done_on="2026-02-20", part_nos=["P-1001", "P-1002"]
        )
        self.assertEqual(machine.installed, date(2024, 1, 31))
        self.assertEqual(job.part_nos, ["P-1001", "P-1002"])

    def test_invalid_serial_number(self):
        with self.assertRaises(ValidationError):
            contract.Machine(machine_id=1, serial_no="100", site="Bielefeld", installed="2024-01-01")

    def test_invalid_installation_date(self):
        with self.assertRaises(ValidationError):
            contract.Machine(machine_id=1, serial_no="SN-100", site="Bielefeld", installed="2024-02-30")

    def test_missing_required_attribute(self):
        with self.assertRaises(ValidationError):
            contract.Machine(machine_id=1, serial_no="SN-100", installed="2024-01-01")

    def test_invalid_price(self):
        with self.assertRaises(ValidationError):
            contract.Part(part_no="P-1", description="bearing", unit_price=Decimal("-0.01"))

    def test_duplicate_part_in_job_rejected_by_application(self):
        with self.assertRaises(ValidationError):
            contract.MaintenanceJob(
                job_id=1, machine_id=1, technician_id=1,
                done_on="2026-01-01", part_nos=["P-1", "P-1"]
            )


class DatabaseContractTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = contract.make_engine(str(Path(self.temp_dir.name) / "contract.db"))
        contract.metadata.create_all(self.engine)
        with self.engine.begin() as connection:
            connection.execute(insert(contract.machine_t), {
                "machine_id": 1, "serial_no": "SN-100", "site": "Bielefeld",
                "installed": date(2024, 1, 1),
            })
            connection.execute(insert(contract.technician_t), {
                "technician_id": 1, "name": "Beier",
            })
            connection.execute(insert(contract.part_t), [
                {"part_no": "P-1", "description": "Bearing", "unit_price": Decimal("12.50")},
                {"part_no": "P-2", "description": "Belt", "unit_price": Decimal("48.00")},
            ])

    def tearDown(self):
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_duplicate_machine_serial_rejected(self):
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(insert(contract.machine_t), {
                    "machine_id": 2, "serial_no": "SN-100", "site": "Gütersloh",
                    "installed": date(2025, 1, 1),
                })

    def test_orphan_machine_reference_rejected(self):
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(insert(contract.maint_job_t), {
                    "job_id": 1, "machine_id": 999, "technician_id": 1,
                    "done_on": date(2026, 1, 1),
                })

    def test_duplicate_job_part_rejected(self):
        with self.engine.begin() as connection:
            connection.execute(insert(contract.maint_job_t), {
                "job_id": 1, "machine_id": 1, "technician_id": 1,
                "done_on": date(2026, 1, 1),
            })
            connection.execute(insert(contract.job_part_t), {"job_id": 1, "part_no": "P-1"})
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(insert(contract.job_part_t), {"job_id": 1, "part_no": "P-1"})

    def test_many_to_many_relationship(self):
        with self.engine.begin() as connection:
            connection.execute(insert(contract.maint_job_t), [
                {"job_id": 1, "machine_id": 1, "technician_id": 1, "done_on": date(2026, 1, 1)},
                {"job_id": 2, "machine_id": 1, "technician_id": 1, "done_on": date(2026, 1, 2)},
            ])
            connection.execute(insert(contract.job_part_t), [
                {"job_id": 1, "part_no": "P-1"},
                {"job_id": 1, "part_no": "P-2"},
                {"job_id": 2, "part_no": "P-1"},
            ])
            rows = connection.execute(select(contract.job_part_t)).all()
        self.assertEqual(len(rows), 3)
        self.assertEqual(sum(row.part_no == "P-1" for row in rows), 2)

    def test_negative_price_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(insert(contract.part_t), {
                    "part_no": "P-3", "description": "Invalid", "unit_price": Decimal("-1.00")
                })


if __name__ == "__main__":
    unittest.main(verbosity=2)
