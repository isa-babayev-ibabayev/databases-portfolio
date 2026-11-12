"""Expand the official 200k-row CSV into a validated 2M-row Parquet file."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb


HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "report_jobpart.csv"
HISTORY = HERE / "history.db"
PARQUET = HERE / "report_history.parquet"
EXPECTED_COLUMNS = (
    "job_id",
    "machine_id",
    "site",
    "technician",
    "part_no",
    "part_price",
    "done_on",
)


def sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def sqlite_summary() -> dict[str, Any]:
    connection = sqlite3.connect(
        f"file:{HISTORY.resolve().as_posix()}?mode=ro&immutable=1", uri=True
    )
    try:
        row = connection.execute(
            "SELECT COUNT(*), ROUND(SUM(part_price),2), SUM(job_id), "
            "MIN(done_on), MAX(done_on) FROM report_history"
        ).fetchone()
    finally:
        connection.close()
    return {
        "rows": row[0],
        "sum_part_price": row[1],
        "sum_job_id": row[2],
        "min_date": row[3],
        "max_date": row[4],
    }


def parquet_summary(path: Path) -> dict[str, Any]:
    connection = duckdb.connect()
    parquet = sql_path(path)
    try:
        row = connection.execute(
            f"SELECT COUNT(*), ROUND(SUM(part_price),2), SUM(job_id), "
            f"MIN(done_on), MAX(done_on) FROM read_parquet('{parquet}')"
        ).fetchone()
        description = connection.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{parquet}')"
        ).fetchall()
        nulls = connection.execute(
            f"SELECT "
            + ", ".join(
                f"SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END)"
                for column in EXPECTED_COLUMNS
            )
            + f" FROM read_parquet('{parquet}')"
        ).fetchone()
    finally:
        connection.close()
    return {
        "rows": row[0],
        "sum_part_price": float(row[1]),
        "sum_job_id": row[2],
        "min_date": str(row[3]),
        "max_date": str(row[4]),
        "schema": [[item[0], item[1]] for item in description],
        "null_counts": dict(zip(EXPECTED_COLUMNS, nulls, strict=True)),
        "bytes": path.stat().st_size,
    }


def validate(path: Path) -> dict[str, Any]:
    sqlite = sqlite_summary()
    parquet = parquet_summary(path)
    columns = tuple(item[0] for item in parquet["schema"])
    valid = (
        columns == EXPECTED_COLUMNS
        and parquet["rows"] == sqlite["rows"] == 2_000_000
        and abs(parquet["sum_part_price"] - sqlite["sum_part_price"]) < 0.01
        and parquet["sum_job_id"] == sqlite["sum_job_id"]
        and parquet["min_date"] == sqlite["min_date"]
        and parquet["max_date"] == sqlite["max_date"]
        and all(value == 0 for value in parquet["null_counts"].values())
    )
    result = {"valid": valid, "sqlite": sqlite, "parquet": parquet}
    if not valid:
        raise RuntimeError(f"Parquet validation failed: {result}")
    return result


def build(target: Path) -> None:
    connection = duckdb.connect()
    csv_path = sql_path(CSV_PATH)
    target_path = sql_path(target)
    try:
        connection.execute(
            f"""COPY (
              SELECT r.job_id + k * 1000000 AS job_id, r.machine_id, r.site,
                     r.technician, r.part_no, r.part_price,
                     CAST(r.done_on AS DATE) + CAST(k * 91 AS INTEGER) AS done_on
              FROM read_csv_auto('{csv_path}', header = true) AS r,
                   range(0, 10) AS t(k)
            ) TO '{target_path}' (FORMAT parquet)"""
        )
    finally:
        connection.close()


def backup_existing(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.stem}.backup-{stamp}{path.suffix}")
    path.replace(backup)
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    if not CSV_PATH.exists() or not HISTORY.exists():
        raise SystemExit("run Module06a/prepare.py first")
    backup: str | None = None
    if PARQUET.exists() and not args.rebuild:
        result = validate(PARQUET)
        action = "reused validated existing file"
    else:
        temporary = PARQUET.with_name("report_history.new.parquet")
        if temporary.exists():
            raise SystemExit(f"temporary Parquet file already exists: {temporary}")
        build(temporary)
        result = validate(temporary)
        if PARQUET.exists():
            backup = str(backup_existing(PARQUET))
        os.replace(temporary, PARQUET)
        action = "built and atomically installed"
    result.update(
        {
            "action": action,
            "backup": backup,
            "duckdb_version": duckdb.__version__,
            "history_db_bytes": HISTORY.stat().st_size,
            "source_csv_bytes": CSV_PATH.stat().st_size,
        }
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
