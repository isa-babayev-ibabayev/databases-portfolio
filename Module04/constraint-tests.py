"""Execute Module 4 acceptance tests and print the real SQLite outcomes."""

from __future__ import annotations

import sqlite3
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent


def attempt(connection: sqlite3.Connection, label: str, sql: str, parameters=()) -> None:
    try:
        connection.execute(sql, parameters)
    except sqlite3.Error as exc:
        print(f"{label}: REJECTED | {type(exc).__name__}: {exc}")
    else:
        print(f"{label}: ACCEPTED")


def run_scratch() -> None:
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        (MODULE_DIR / "scratch-constraints.sql").read_text(encoding="utf-8")
    )
    print("## Task A: unconstrained rows")
    for row in connection.execute(
        "SELECT sensor_id, metric, value, typeof(value) FROM t ORDER BY rowid"
    ):
        print(" | ".join("NULL" if value is None else str(value) for value in row))

    print("\n## Constrained acceptance cases")
    cases = [
        ("valid row", (1, 10, "temp_c", 42.5)),
        ("temperature 9000", (2, 11, "temp_c", 9000)),
        ("text hot in REAL", (3, 12, "temp_c", "hot")),
        ("unsupported metric", (4, 13, "bogus", 40)),
        ("value -500", (5, 14, "temp_c", -500)),
        ("NULL metric", (6, 15, None, 40)),
        ("NULL value", (7, 16, "temp_c", None)),
        ("duplicate natural key", (8, 10, "temp_c", 43)),
        ("numeric string 42.5", (9, 17, "temp_c", "42.5")),
        ("plausible but wrong 4500", (10, 18, "temp_c", 4500)),
        ("duplicate primary key", (1, 19, "vib_rms", 1.2)),
    ]
    for label, values in cases:
        attempt(
            connection,
            label,
            "INSERT INTO t_constrained(sample_id, sensor_id, metric, value) "
            "VALUES (?, ?, ?, ?)",
            values,
        )
    stored = connection.execute(
        "SELECT value, typeof(value) FROM t_constrained WHERE sample_id=9"
    ).fetchone()
    print(f"numeric string stored as: {stored[0]} | {stored[1]}")

    print("\n## CHECK and NULL")
    attempt(connection, "NULL with CHECK only", "INSERT INTO check_only VALUES (NULL)")
    attempt(
        connection,
        "NULL with CHECK plus NOT NULL",
        "INSERT INTO check_and_not_null VALUES (NULL)",
    )
    connection.close()


def run_main_schema() -> None:
    connection = sqlite3.connect(":memory:")
    connection.executescript((MODULE_DIR / "setup.sql").read_text(encoding="utf-8"))
    print("\n## Main edge schema")
    generated = connection.execute(
        "SELECT reading_id, sensor_id, value, interval_s, energy_j FROM reading"
    ).fetchone()
    print("generated row: " + " | ".join(map(str, generated)))

    main_cases = [
        (
            "domain violation 9000",
            "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (1,?,9000,1)",
            ("2026-03-01 11:00:01",),
        ),
        (
            "STRICT type hot",
            "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (1,?,'hot',1)",
            ("2026-03-01 11:00:02",),
        ),
        (
            "missing sensor 99",
            "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (99,?,40,1)",
            ("2026-03-01 11:00:03",),
        ),
        (
            "duplicate machine metric",
            "INSERT INTO sensor VALUES (3,'cnc-01','temp_c','degC')",
            (),
        ),
        (
            "missing timestamp",
            "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (1,NULL,40,1)",
            (),
        ),
        (
            "zero interval",
            "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (1,?,40,0)",
            ("2026-03-01 11:00:04",),
        ),
        (
            "duplicate reading primary key",
            "INSERT INTO reading(reading_id,sensor_id,ts,value,interval_s) "
            "VALUES (1,1,?,40,1)",
            ("2026-03-01 11:00:05",),
        ),
        (
            "direct generated-column write",
            "INSERT INTO reading(sensor_id,ts,value,interval_s,energy_j) "
            "VALUES (1,?,40,1,40)",
            ("2026-03-01 11:00:06",),
        ),
        (
            "lower boundary -273.15",
            "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (1,?,-273.15,1)",
            ("2026-03-01 11:00:07",),
        ),
        (
            "upper boundary 5000",
            "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (1,?,5000,1)",
            ("2026-03-01 11:00:08",),
        ),
        (
            "STRICT numeric string",
            "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (1,?,'42.5',1)",
            ("2026-03-01 11:00:09",),
        ),
        (
            "empty machine identifier",
            "INSERT INTO sensor VALUES (3,'','spindle_load','percent')",
            (),
        ),
    ]
    for label, sql, parameters in main_cases:
        attempt(connection, label, sql, parameters)

    numeric = connection.execute(
        "SELECT value, typeof(value) FROM reading WHERE ts='2026-03-01 11:00:09'"
    ).fetchone()
    print(f"numeric string stored as: {numeric[0]} | {numeric[1]}")
    print(f"foreign_key_check rows: {connection.execute('PRAGMA foreign_key_check').fetchall()}")
    print(f"integrity_check: {connection.execute('PRAGMA integrity_check').fetchone()[0]}")
    print(f"final reading count: {connection.execute('SELECT count(*) FROM reading').fetchone()[0]}")
    connection.close()


def main() -> None:
    print(f"Python SQLite runtime: {sqlite3.sqlite_version}")
    run_scratch()
    run_main_schema()


if __name__ == "__main__":
    main()
