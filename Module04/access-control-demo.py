"""Demonstrate SQLite view, URI read-only mode, query_only, and ACL inspection."""

from __future__ import annotations

import sqlite3
import subprocess
import tempfile
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent


def main() -> None:
    print(f"Python SQLite runtime: {sqlite3.sqlite_version}")
    with tempfile.TemporaryDirectory() as temporary:
        database = Path(temporary) / "edge-access.db"
        connection = sqlite3.connect(database)
        connection.executescript((MODULE_DIR / "setup.sql").read_text(encoding="utf-8"))
        connection.close()

        read_only_uri = database.resolve().as_uri() + "?mode=ro"
        read_only = sqlite3.connect(read_only_uri, uri=True)
        print(f"mode=ro reading count: {read_only.execute('SELECT count(*) FROM reading').fetchone()[0]}")
        print(f"mode=ro view rows: {read_only.execute('SELECT count(*) FROM machine_health').fetchone()[0]}")
        try:
            read_only.execute("DELETE FROM reading")
        except sqlite3.OperationalError as exc:
            print(f"mode=ro DELETE rejected: {exc}")
        read_only.close()

        query_only = sqlite3.connect(database)
        query_only.execute("PRAGMA query_only = ON")
        print(f"query_only setting: {query_only.execute('PRAGMA query_only').fetchone()[0]}")
        try:
            query_only.execute("DELETE FROM reading")
        except sqlite3.OperationalError as exc:
            print(f"query_only DELETE rejected: {exc}")
        query_only.close()

        acl = subprocess.run(
            ["icacls", str(database)],
            check=False,
            capture_output=True,
            text=True,
        )
        acl_lines = [line for line in acl.stdout.splitlines() if line.strip()]
        print(f"icacls inspection exit code: {acl.returncode}")
        print(f"icacls non-empty output lines: {len(acl_lines)}")
        print("ACLs were inspected only; no permissions were modified.")


if __name__ == "__main__":
    main()
