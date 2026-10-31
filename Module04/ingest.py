"""Replay-safe CSV ingestion for the Module 4 SQLite edge database."""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent
SETUP_SQL = MODULE_DIR / "setup.sql"
REQUIRED_COLUMNS = ("sensor_id", "ts", "value", "interval_s")
UPSERT_SQL = """
INSERT INTO reading(sensor_id, ts, value, interval_s)
VALUES (?, ?, ?, ?)
ON CONFLICT(sensor_id, ts)
DO UPDATE SET
    value = excluded.value,
    interval_s = excluded.interval_s
WHERE reading.value IS NOT excluded.value
   OR reading.interval_s IS NOT excluded.interval_s
"""


class CsvValidationError(ValueError):
    """Raised when a CSV row cannot be converted into a reading."""


@dataclass(frozen=True)
class IngestionResult:
    input_rows: int
    readings_before: int
    readings_after: int
    duplicate_keys: int
    audit_rows: int
    alarm_rows: int


def read_rows(csv_path: Path) -> list[tuple[int, str, float, int]]:
    rows: list[tuple[int, str, float, int]] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != list(REQUIRED_COLUMNS):
            raise CsvValidationError(
                f"expected columns {list(REQUIRED_COLUMNS)}, got {reader.fieldnames}"
            )
        for line_number, row in enumerate(reader, start=2):
            try:
                sensor_id = int(row["sensor_id"])
                timestamp = row["ts"].strip()
                value = float(row["value"])
                interval_s = int(row["interval_s"])
            except (TypeError, ValueError) as exc:
                raise CsvValidationError(f"line {line_number}: {exc}") from exc
            if not timestamp:
                raise CsvValidationError(f"line {line_number}: ts must not be empty")
            rows.append((sensor_id, timestamp, value, interval_s))
    if not rows:
        raise CsvValidationError("CSV contains no data rows")
    return rows


def connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]
    if enabled != 1:
        connection.close()
        raise RuntimeError("foreign-key enforcement could not be enabled")
    return connection


def initialize_if_needed(connection: sqlite3.Connection, initialize: bool) -> None:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_schema WHERE type='table' AND name='sensor'"
    ).fetchone()
    if exists:
        return
    if not initialize:
        raise RuntimeError("database is not initialized; rerun with --init")
    connection.executescript(SETUP_SQL.read_text(encoding="utf-8"))
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError("setup did not leave foreign-key enforcement enabled")


def ingest(database_path: Path, csv_path: Path, *, initialize: bool = False) -> IngestionResult:
    rows = read_rows(csv_path)
    connection = connect(database_path)
    try:
        initialize_if_needed(connection, initialize)
        readings_before = connection.execute("SELECT count(*) FROM reading").fetchone()[0]
        with connection:
            connection.executemany(UPSERT_SQL, rows)
        readings_after = connection.execute("SELECT count(*) FROM reading").fetchone()[0]
        duplicate_keys = connection.execute(
            """
            SELECT count(*)
            FROM (
                SELECT sensor_id, ts
                FROM reading
                GROUP BY sensor_id, ts
                HAVING count(*) > 1
            )
            """
        ).fetchone()[0]
        audit_rows = connection.execute("SELECT count(*) FROM audit").fetchone()[0]
        alarm_rows = connection.execute("SELECT count(*) FROM alarm").fetchone()[0]
        return IngestionResult(
            len(rows),
            readings_before,
            readings_after,
            duplicate_keys,
            audit_rows,
            alarm_rows,
        )
    finally:
        connection.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="SQLite database path")
    parser.add_argument("csv_file", type=Path, help="CSV readings path")
    parser.add_argument(
        "--init",
        action="store_true",
        help="initialize a missing database from Module04/setup.sql",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = ingest(args.database, args.csv_file, initialize=args.init)
    except CsvValidationError as exc:
        print(f"CSV validation failed: {exc}", file=sys.stderr)
        return 2
    except (sqlite3.Error, OSError, RuntimeError) as exc:
        print(f"ingestion failed: {exc}", file=sys.stderr)
        return 3

    print(f"input rows: {result.input_rows}")
    print(f"readings before: {result.readings_before}")
    print(f"readings after: {result.readings_after}")
    print(f"duplicate natural keys: {result.duplicate_keys}")
    print(f"audit rows: {result.audit_rows}")
    print(f"alarm rows: {result.alarm_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
