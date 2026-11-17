"""Reproducible SQLite JSON experiment for Module 6b.

The generated database is disposable evidence. A rebuild is created in a
temporary sibling file and replaces the old database only after validation.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_DATABASE = HERE / "polyglot.db"
ROW_COUNT = 1_000

SCHEMA = """
CREATE TABLE device (
    device_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    meta TEXT NOT NULL CHECK (json_valid(meta))
) STRICT;
"""

VENDORS = ("Siemens", "Fanuc", "Arburg")


def device_rows() -> list[tuple[int, str, str]]:
    named = [
        (1, "cnc-01", {"vendor": "Siemens", "firmware": "4.2", "calibrated": "2026-01-10"}),
        (2, "cnc-02", {"vendor": "Fanuc", "firmware": "3.9"}),
        (3, "molder-07", {"vendor": "Arburg", "firmware": "8.1", "calibrated": "2025-11-02", "nozzle_mm": 2.5}),
    ]
    rows = [(i, name, json.dumps(meta, separators=(",", ":"))) for i, name, meta in named]
    for i in range(4, ROW_COUNT + 1):
        vendor = VENDORS[i % len(VENDORS)]
        meta: dict[str, Any] = {"vendor": vendor, "firmware": f"{i % 5}.{i % 10}"}
        rows.append((i, f"device-{i:04d}", json.dumps(meta, separators=(",", ":"))))
    return rows


def validate_database(path: Path) -> dict[str, Any]:
    with closing(sqlite3.connect(path)) as con:
        count, valid = con.execute(
            "SELECT count(*), sum(json_valid(meta)) FROM device"
        ).fetchone()
        vendor_counts = dict(
            con.execute(
                """SELECT json_extract(meta, '$.vendor'), count(*)
                   FROM device GROUP BY 1 ORDER BY 1"""
            ).fetchall()
        )
    if count != ROW_COUNT or valid != ROW_COUNT:
        raise ValueError(f"Expected {ROW_COUNT} valid rows, found count={count}, valid={valid}")
    return {"row_count": count, "json_valid_rows": valid, "vendor_counts": vendor_counts}


def build_database(path: Path, *, rebuild: bool = False) -> str:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not rebuild:
        validate_database(path)
        return "reused validated database"

    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with closing(sqlite3.connect(temporary)) as con:
            with con:
                con.executescript(SCHEMA)
                con.executemany("INSERT INTO device(device_id, name, meta) VALUES (?, ?, ?)", device_rows())
                con.execute(
                    "CREATE INDEX ix_device_vendor ON device(json_extract(meta, '$.vendor'))"
                )
        validate_database(temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return "rebuilt via validated temporary database"


def query_plan(con: sqlite3.Connection, sql: str) -> list[str]:
    return [row[3] for row in con.execute(f"EXPLAIN QUERY PLAN {sql}")]


def constraint_experiments(con: sqlite3.Connection) -> dict[str, Any]:
    results: dict[str, Any] = {}
    con.execute("SAVEPOINT constraints")
    try:
        con.execute(
            "INSERT INTO device(device_id, name, meta) VALUES (?, ?, ?)",
            (20_001, "valid-extra", '{"vendor":"KUKA","payload_kg":10}'),
        )
        results["valid_json_accepted"] = True

        try:
            con.execute(
                "INSERT INTO device(device_id, name, meta) VALUES (?, ?, ?)",
                (20_002, "invalid", "{not valid json}"),
            )
            results["invalid_json_rejected"] = False
        except sqlite3.IntegrityError as exc:
            results["invalid_json_rejected"] = True
            results["invalid_json_error"] = str(exc)

        con.execute(
            "INSERT INTO device(device_id, name, meta) VALUES (?, ?, ?)",
            (20_003, "different-shape", '{"protocol":"OPC-UA"}'),
        )
        results["different_keys_accepted"] = True
        results["missing_optional_returns_null"] = (
            con.execute(
                "SELECT json_extract(meta, '$.vendor') FROM device WHERE device_id = 20003"
            ).fetchone()[0]
            is None
        )

        try:
            con.execute(
                "INSERT INTO device(device_id, name, meta) VALUES (?, ?, ?)",
                (20_004, "blob-value", sqlite3.Binary(b'{"vendor":"KUKA"}')),
            )
            results["strict_blob_rejected"] = False
        except sqlite3.IntegrityError as exc:
            results["strict_blob_rejected"] = True
            results["strict_blob_error"] = str(exc)
    finally:
        con.execute("ROLLBACK TO constraints")
        con.execute("RELEASE constraints")
    return results


def run_experiment(path: Path = DEFAULT_DATABASE, *, rebuild: bool = False) -> dict[str, Any]:
    disposition = build_database(path, rebuild=rebuild)
    validation = validate_database(path)
    exact_sql = "SELECT name FROM device WHERE json_extract(meta, '$.vendor') = 'Fanuc'"
    shorthand_sql = "SELECT name FROM device WHERE meta ->> 'vendor' = 'Fanuc'"

    with closing(sqlite3.connect(path)) as con:
        vendor_first_five = [
            {"name": row[0], "vendor": row[1]}
            for row in con.execute(
                """SELECT name, json_extract(meta, '$.vendor')
                   FROM device ORDER BY device_id LIMIT 5"""
            )
        ]
        firmware_first_five = [
            {"name": row[0], "firmware": row[1]}
            for row in con.execute(
                "SELECT name, meta ->> '$.firmware' FROM device ORDER BY device_id LIMIT 5"
            )
        ]
        cnc_meta_rows = [
            {"name": row[0], "key": row[1], "value": row[2]}
            for row in con.execute(
                """SELECT d.name, j.key, j.value
                   FROM device AS d, json_each(d.meta) AS j
                   WHERE d.name = 'cnc-01' ORDER BY j.key"""
            )
        ]
        exact_names = [row[0] for row in con.execute(exact_sql)]
        shorthand_names = [row[0] for row in con.execute(shorthand_sql)]
        exact_plan = query_plan(con, exact_sql)
        shorthand_plan = query_plan(con, shorthand_sql)
        constraints = constraint_experiments(con)

    return {
        "database": str(path.resolve()),
        "database_disposition": disposition,
        "sqlite_version": sqlite3.sqlite_version,
        **validation,
        "vendor_first_five": vendor_first_five,
        "firmware_first_five": firmware_first_five,
        "json_each_for_cnc_01": cnc_meta_rows,
        "fanuc_result_count": len(exact_names),
        "queries_return_same_rows": exact_names == shorthand_names,
        "exact_expression_plan": exact_plan,
        "shorthand_plan": shorthand_plan,
        "exact_expression_uses_index": any("ix_device_vendor" in item for item in exact_plan),
        "shorthand_scans_table": any("SCAN device" in item for item in shorthand_plan),
        "constraint_experiments": constraints,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--rebuild", action="store_true", help="safely replace the generated database")
    args = parser.parse_args()
    print(json.dumps(run_experiment(args.database, rebuild=args.rebuild), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
