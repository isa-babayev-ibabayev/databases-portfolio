"""Reproduce Task A plans on a disposable copy of the Module 2 fixture."""

from __future__ import annotations

import argparse
import sqlite3
import tempfile
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent
ROOT = MODULE_DIR.parent
LEGACY_SETUP = ROOT / "module-02" / "legacy_setup.sql"
DEFAULT_OUTPUT = MODULE_DIR / "evidence" / "classroom-plan-reproduction.txt"

QUERIES = (
    (
        "technician equality",
        "SELECT * FROM maint_job WHERE technician = 'Beier'",
    ),
    (
        "machine-name equality",
        "SELECT * FROM machine WHERE machine_name = 'cnc-02'",
    ),
    (
        "leading-wildcard technician",
        "SELECT * FROM maint_job WHERE technician LIKE '%ei%'",
    ),
)


def plan(conn: sqlite3.Connection, sql: str) -> list[str]:
    return [str(row[3]) for row in conn.execute("EXPLAIN QUERY PLAN " + sql)]


def reproduce(setup_path: Path = LEGACY_SETUP) -> str:
    if not setup_path.exists():
        raise FileNotFoundError(setup_path)
    with tempfile.TemporaryDirectory(prefix="module03-task-a-") as temp_dir:
        conn = sqlite3.connect(Path(temp_dir) / "legacy-copy.db")
        conn.executescript(setup_path.read_text(encoding="utf-8"))
        lines = [
            f"Python SQLite runtime: {sqlite3.sqlite_version}",
            "Database: disposable copy rebuilt from module-02/legacy_setup.sql",
            "",
            "## before index",
        ]
        for label, sql in QUERIES:
            lines.append(f"{label}: {sql}")
            lines.extend(plan(conn, sql))
        conn.execute(
            "CREATE INDEX ix_job_tech ON maint_job(technician)"
        )
        lines.extend(["", "## after ix_job_tech"])
        for label, sql in QUERIES:
            lines.append(f"{label}: {sql}")
            lines.extend(plan(conn, sql))
        function_sql = (
            "SELECT * FROM maint_job "
            "WHERE upper(technician) = upper('Beier')"
        )
        lines.append(f"function-wrapped technician: {function_sql}")
        lines.extend(plan(conn, function_sql))
        conn.close()
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = reproduce()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
