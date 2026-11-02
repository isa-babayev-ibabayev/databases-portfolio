"""Educational SQL-injection demonstration on an isolated in-memory copy."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = MODULE_DIR / "warehouse.db"
PAYLOAD = "' OR '1'='1"


def vulnerable(conn: sqlite3.Connection, name: str) -> list[tuple[int, str]]:
    """Intentionally unsafe. Never copy this pattern into application code."""
    sql = f"SELECT customer_id, name FROM customer WHERE name = '{name}'"
    return conn.execute(sql).fetchall()


def safe(conn: sqlite3.Connection, name: str) -> list[tuple[int, str]]:
    """Bind the value so SQLite never parses it as SQL syntax."""
    sql = "SELECT customer_id, name FROM customer WHERE name = ?"
    return conn.execute(sql, (name,)).fetchall()


def isolated_copy(database: Path) -> sqlite3.Connection:
    """Copy a source database opened read-only into a writable memory database."""
    if not database.exists():
        raise FileNotFoundError(f"{database} not found; run setup.sql first")
    source = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    destination = sqlite3.connect(":memory:")
    try:
        source.backup(destination)
    finally:
        source.close()
    return destination


def run_demo(database: Path) -> str:
    conn = isolated_copy(database)
    lines = [f"SQLite runtime: {sqlite3.sqlite_version}"]
    try:
        # This row exists only in the in-memory copy.
        test_id = conn.execute("SELECT MAX(customer_id) + 1 FROM customer").fetchone()[0]
        conn.execute(
            "INSERT INTO customer(customer_id, name, city) VALUES (?, ?, ?)",
            (test_id, "O'Brien", "Test City"),
        )
        apostrophe_name = "O'Brien"
        normal = vulnerable(conn, "Customer 1")
        lines.append(f"normal vulnerable lookup: {normal}")
        try:
            vulnerable(conn, apostrophe_name)
        except sqlite3.Error as error:
            lines.append(f"apostrophe vulnerable lookup: ERROR {error}")
        lines.append(f"apostrophe safe lookup: {safe(conn, apostrophe_name)}")
        injected = vulnerable(conn, PAYLOAD)
        lines.append(
            f"payload vulnerable lookup: {len(injected)} rows; first 3={injected[:3]}"
        )
        lines.append(f"payload safe lookup: {safe(conn, PAYLOAD)}")
        lines.append(
            "database isolation: source opened read-only; in-memory copy discarded"
        )
    finally:
        conn.close()
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = run_demo(args.database)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
