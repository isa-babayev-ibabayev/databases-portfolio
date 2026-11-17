"""Safely rebuild or check the analytical Parquet snapshot from history.db."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

import duckdb


HERE = Path(__file__).resolve().parent
HISTORY = HERE / "history.db"
PARQUET = HERE / "report_history.parquet"
COLUMNS = (
    "job_id",
    "machine_id",
    "site",
    "technician",
    "part_no",
    "part_price",
    "done_on",
)


class ValidationError(RuntimeError):
    """Raised when a candidate snapshot does not match the SQLite source."""


def sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def normalized_price(value: Any) -> str:
    return f"{Decimal(str(value)).quantize(Decimal('0.01')):.2f}"


def sqlite_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"SQLite history is missing: {path}")
    connection = sqlite3.connect(
        f"file:{path.resolve().as_posix()}?mode=ro&immutable=1", uri=True
    )
    try:
        row = connection.execute(
            "SELECT COUNT(*), ROUND(SUM(part_price),2), SUM(job_id), "
            "MIN(done_on), MAX(done_on), "
            "SUM(CASE WHEN job_id IS NULL OR machine_id IS NULL OR site IS NULL "
            "OR technician IS NULL OR part_no IS NULL OR part_price IS NULL "
            "OR done_on IS NULL THEN 1 ELSE 0 END) FROM report_history"
        ).fetchone()
    finally:
        connection.close()
    return {
        "rows": row[0],
        "sum_part_price": normalized_price(row[1]),
        "sum_job_id": row[2],
        "min_date": row[3],
        "max_date": row[4],
        "null_rows": row[5],
    }


def parquet_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Parquet snapshot is missing: {path}")
    connection = duckdb.connect()
    try:
        parquet = sql_path(path)
        row = connection.execute(
            "SELECT COUNT(*), ROUND(SUM(part_price),2), SUM(job_id), "
            "CAST(MIN(done_on) AS VARCHAR), CAST(MAX(done_on) AS VARCHAR), "
            "SUM(CASE WHEN job_id IS NULL OR machine_id IS NULL OR site IS NULL "
            "OR technician IS NULL OR part_no IS NULL OR part_price IS NULL "
            "OR done_on IS NULL THEN 1 ELSE 0 END) "
            f"FROM read_parquet('{parquet}')"
        ).fetchone()
        schema = connection.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{parquet}')"
        ).fetchall()
    finally:
        connection.close()
    return {
        "rows": row[0],
        "sum_part_price": normalized_price(row[1]),
        "sum_job_id": row[2],
        "min_date": row[3],
        "max_date": row[4],
        "null_rows": row[5],
        "columns": [item[0] for item in schema],
        "types": [item[1] for item in schema],
    }


def logical_checksum(summary: dict[str, Any]) -> str:
    logical = {
        key: summary[key]
        for key in (
            "rows",
            "sum_part_price",
            "sum_job_id",
            "min_date",
            "max_date",
            "null_rows",
        )
    }
    payload = json.dumps(logical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def compare_files(history: Path, parquet: Path) -> dict[str, Any]:
    sqlite = sqlite_summary(history)
    parquet_result = parquet_summary(parquet)
    comparable_parquet = {
        key: parquet_result[key]
        for key in (
            "rows",
            "sum_part_price",
            "sum_job_id",
            "min_date",
            "max_date",
            "null_rows",
        )
    }
    expected_types = [
        "BIGINT",
        "VARCHAR",
        "VARCHAR",
        "VARCHAR",
        "VARCHAR",
        "DOUBLE",
        "DATE",
    ]
    match = (
        sqlite == comparable_parquet
        and parquet_result["columns"] == list(COLUMNS)
        and parquet_result["types"] == expected_types
    )
    return {
        "match": match,
        "sqlite": sqlite,
        "parquet": parquet_result,
        "logical_checksum": logical_checksum(sqlite),
    }


def build_parquet(history: Path, target: Path) -> None:
    connection = duckdb.connect()
    try:
        connection.execute(
            f"""COPY (
              SELECT CAST(job_id AS BIGINT) AS job_id,
                     CAST(machine_id AS VARCHAR) AS machine_id,
                     CAST(site AS VARCHAR) AS site,
                     CAST(technician AS VARCHAR) AS technician,
                     CAST(part_no AS VARCHAR) AS part_no,
                     CAST(part_price AS DOUBLE) AS part_price,
                     CAST(done_on AS DATE) AS done_on
              FROM sqlite_scan('{sql_path(history)}', 'report_history')
            ) TO '{sql_path(target)}' (FORMAT parquet)"""
        )
    finally:
        connection.close()


def refresh_snapshot(
    history: Path,
    parquet: Path,
    builder: Callable[[Path, Path], None] = build_parquet,
) -> dict[str, Any]:
    started = time.perf_counter()
    parquet.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{parquet.stem}.refresh-",
        suffix=".parquet",
        dir=parquet.parent,
        delete=False,
    )
    temporary = Path(handle.name)
    handle.close()
    temporary.unlink()
    try:
        builder(history, temporary)
        comparison = compare_files(history, temporary)
        if not comparison["match"]:
            raise ValidationError(
                "candidate snapshot does not match SQLite: "
                f"{json.dumps(comparison, default=str)}"
            )
        os.replace(temporary, parquet)
        published = compare_files(history, parquet)
        if not published["match"]:
            raise ValidationError("published snapshot failed its final check")
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        **published,
        "parquet_bytes": parquet.stat().st_size,
        "elapsed_ms": (time.perf_counter() - started) * 1000,
    }


def print_comparison(result: dict[str, Any]) -> None:
    sqlite = result["sqlite"]
    parquet = result["parquet"]
    print(
        f"SQLite rows={sqlite['rows']} sum_part_price={sqlite['sum_part_price']}"
    )
    print(
        f"Parquet rows={parquet['rows']} sum_part_price={parquet['sum_part_price']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the existing Parquet with SQLite without rebuilding",
    )
    parser.add_argument("--history", type=Path, default=HISTORY)
    parser.add_argument("--parquet", type=Path, default=PARQUET)
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        if args.check:
            result = compare_files(args.history, args.parquet)
            result["parquet_bytes"] = args.parquet.stat().st_size
            result["elapsed_ms"] = (time.perf_counter() - started) * 1000
            print_comparison(result)
            status = "PASS" if result["match"] else "FAIL"
            print(
                f"CHECK {status} rows={result['parquet']['rows']} "
                f"checksum={result['logical_checksum']} "
                f"parquet_bytes={result['parquet_bytes']} "
                f"elapsed_ms={result['elapsed_ms']:.2f}"
            )
            return 0 if result["match"] else 1

        result = refresh_snapshot(args.history, args.parquet)
        print(
            f"REFRESH OK rows={result['parquet']['rows']} "
            f"checksum={result['logical_checksum']} "
            f"parquet_bytes={result['parquet_bytes']} "
            f"elapsed_ms={result['elapsed_ms']:.2f}"
        )
        return 0
    except (FileNotFoundError, ValidationError, duckdb.Error, sqlite3.Error) as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
