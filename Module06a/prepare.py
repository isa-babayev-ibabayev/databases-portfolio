"""Build the official ten-quarter SQLite history and 200k-row source CSV safely."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "Module05" / "normalize.db"
HISTORY = HERE / "history.db"
CSV_PATH = HERE / "report_jobpart.csv"
QUARTERS = 10
COLUMNS = (
    "job_id",
    "machine_id",
    "site",
    "technician",
    "part_no",
    "part_price",
    "done_on",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_only(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro&immutable=1", uri=True)


def source_facts() -> dict[str, Any]:
    if not SOURCE.exists():
        raise RuntimeError(
            "Module05/normalize.db is missing; rebuild it with the Module 5 setup first"
        )
    connection = read_only(SOURCE)
    try:
        row = connection.execute(
            "SELECT COUNT(*), ROUND(SUM(part_price),2), MIN(done_on), MAX(done_on), "
            "MIN(job_id), MAX(job_id) FROM report_jobpart"
        ).fetchone()
    finally:
        connection.close()
    return {
        "rows": row[0],
        "sum_part_price": row[1],
        "min_date": row[2],
        "max_date": row[3],
        "min_job_id": row[4],
        "max_job_id": row[5],
        "sha256": sha256(SOURCE),
    }


def validate_history(path: Path, source: dict[str, Any]) -> dict[str, Any]:
    connection = read_only(path)
    try:
        summary = connection.execute(
            "SELECT COUNT(*), ROUND(SUM(part_price),2), MIN(done_on), MAX(done_on), "
            "SUM(CASE WHEN job_id IS NULL OR machine_id IS NULL OR site IS NULL "
            "OR technician IS NULL OR part_no IS NULL OR part_price IS NULL "
            "OR done_on IS NULL THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN date(done_on) IS NULL THEN 1 ELSE 0 END) "
            "FROM report_history"
        ).fetchone()
        periods = [
            list(row)
            for row in connection.execute(
                "SELECT CAST(job_id / 1000000 AS INTEGER) AS quarter, COUNT(*), "
                "MIN(job_id), MAX(job_id), MIN(done_on), MAX(done_on) "
                "FROM report_history GROUP BY quarter ORDER BY quarter"
            )
        ]
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        connection.close()

    expected_rows = source["rows"] * QUARTERS
    expected_sum = round(source["sum_part_price"] * QUARTERS, 2)
    valid = (
        summary[0] == expected_rows
        and abs(summary[1] - expected_sum) < 0.01
        and summary[4] == 0
        and summary[5] == 0
        and len(periods) == QUARTERS
        and all(row[1] == source["rows"] for row in periods)
        and integrity == "ok"
    )
    result = {
        "valid": valid,
        "rows": summary[0],
        "sum_part_price": summary[1],
        "min_date": summary[2],
        "max_date": summary[3],
        "null_rows": summary[4],
        "malformed_dates": summary[5],
        "periods": periods,
        "integrity_check": integrity,
        "bytes": path.stat().st_size,
    }
    if not valid:
        raise RuntimeError(f"history validation failed: {result}")
    return result


def build_history(target: Path) -> None:
    connection = sqlite3.connect(target, uri=True)
    try:
        source_uri = f"file:{SOURCE.as_posix()}?mode=ro&immutable=1"
        connection.execute("ATTACH DATABASE ? AS m5", (source_uri,))
        connection.execute(
            """CREATE TABLE report_history(
            job_id INTEGER, machine_id TEXT, site TEXT, technician TEXT,
            part_no TEXT, part_price REAL, done_on TEXT)"""
        )
        connection.execute(
            f"""INSERT INTO report_history
            SELECT r.job_id + k * 1000000, r.machine_id, r.site, r.technician,
                   r.part_no, r.part_price,
                   date(r.done_on, '+' || (k * 91) || ' days')
            FROM m5.report_jobpart AS r,
                 (WITH RECURSIVE n(k) AS (
                      SELECT 0 UNION ALL SELECT k + 1 FROM n WHERE k < {QUARTERS - 1})
                  SELECT k FROM n)"""
        )
        connection.commit()
    finally:
        connection.close()


def validate_csv(path: Path, expected_rows: int) -> dict[str, Any]:
    with path.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.reader(stream)
        header = tuple(next(reader))
        rows = sum(1 for _ in reader)
    result = {
        "valid": header == COLUMNS and rows == expected_rows,
        "header": list(header),
        "data_rows": rows,
        "bytes": path.stat().st_size,
    }
    if not result["valid"]:
        raise RuntimeError(f"CSV validation failed: {result}")
    return result


def export_source_csv(target: Path) -> None:
    connection = read_only(SOURCE)
    try:
        cursor = connection.execute("SELECT * FROM report_jobpart")
        with target.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(COLUMNS)
            while rows := cursor.fetchmany(10_000):
                writer.writerows(rows)
    finally:
        connection.close()


def backup_existing(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.stem}.backup-{stamp}{path.suffix}")
    path.replace(backup)
    return backup


def date_shift_experiment() -> list[dict[str, str]]:
    connection = sqlite3.connect(":memory:")
    try:
        rows = connection.execute(
            """SELECT d,
            date(d, '+90 days'), date(d, '+91 days'), date(d, '+1 month')
            FROM (SELECT '2025-01-15' AS d UNION ALL SELECT '2025-01-31')"""
        ).fetchall()
    finally:
        connection.close()
    return [
        {"start": row[0], "plus_90_days": row[1], "plus_91_days": row[2], "plus_1_month": row[3]}
        for row in rows
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="build new outputs and preserve existing outputs as timestamped backups",
    )
    args = parser.parse_args()
    source = source_facts()
    if source["rows"] != 200_000:
        raise SystemExit(f"unexpected Module 5 source count: {source['rows']}")
    source_hash_before = source["sha256"]
    backups: list[str] = []

    if HISTORY.exists() and not args.rebuild:
        history = validate_history(HISTORY, source)
        history_action = "reused validated existing file"
    else:
        temporary = HISTORY.with_name("history.new.db")
        if temporary.exists():
            raise SystemExit(f"temporary build file already exists: {temporary}")
        build_history(temporary)
        history = validate_history(temporary, source)
        if HISTORY.exists():
            backups.append(str(backup_existing(HISTORY)))
        temporary.replace(HISTORY)
        history_action = "built and atomically installed"

    if CSV_PATH.exists() and not args.rebuild:
        csv_result = validate_csv(CSV_PATH, source["rows"])
        csv_action = "reused validated existing file"
    else:
        temporary_csv = CSV_PATH.with_name("report_jobpart.new.csv")
        if temporary_csv.exists():
            raise SystemExit(f"temporary CSV file already exists: {temporary_csv}")
        export_source_csv(temporary_csv)
        csv_result = validate_csv(temporary_csv, source["rows"])
        if CSV_PATH.exists():
            backups.append(str(backup_existing(CSV_PATH)))
        temporary_csv.replace(CSV_PATH)
        csv_action = "exported source rows and atomically installed"

    source_hash_after = sha256(SOURCE)
    if source_hash_after != source_hash_before:
        raise RuntimeError("Module 5 source database changed during preparation")

    result = {
        "quarters": QUARTERS,
        "source": source,
        "history": history,
        "history_action": history_action,
        "csv": csv_result,
        "csv_action": csv_action,
        "csv_contains": "the original 200,000 report_jobpart rows, not the 2,000,000-row history",
        "source_hash_unchanged": True,
        "date_shift_experiment": date_shift_experiment(),
        "backups": backups,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
