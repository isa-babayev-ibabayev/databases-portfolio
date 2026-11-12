"""Capture the official DuckDB EXPLAIN ANALYZE and the SQLite access plan."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import duckdb


HERE = Path(__file__).resolve().parent
HISTORY = HERE / "history.db"
PARQUET = HERE / "report_history.parquet"
QUERY = """SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM {src}
GROUP BY machine_id, site, technician"""


def sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def capture_plans() -> tuple[str, list[str]]:
    if not HISTORY.exists() or not PARQUET.exists():
        raise FileNotFoundError("run prepare.py and to_parquet.py first")
    duck_connection = duckdb.connect()
    try:
        duck_query = QUERY.format(src=f"read_parquet('{sql_path(PARQUET)}')")
        duck_plan = duck_connection.execute("EXPLAIN ANALYZE " + duck_query).fetchone()[1]
    finally:
        duck_connection.close()
    sqlite_connection = sqlite3.connect(
        f"file:{HISTORY.resolve().as_posix()}?mode=ro&immutable=1", uri=True
    )
    try:
        sqlite_query = QUERY.format(src="report_history")
        sqlite_plan = [
            " | ".join(str(value) for value in row)
            for row in sqlite_connection.execute("EXPLAIN QUERY PLAN " + sqlite_query)
        ]
    finally:
        sqlite_connection.close()
    return duck_plan, sqlite_plan


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    duck_plan, sqlite_plan = capture_plans()
    print("=== DuckDB EXPLAIN ANALYZE ===")
    print(duck_plan)
    print("\n=== SQLite EXPLAIN QUERY PLAN ===")
    print("\n".join(sqlite_plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
