"""A controlled local SQLite two-writer lock and retry demonstration."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any


def run_demo(busy_timeout_ms: int = 250) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="module06b-concurrency-") as tmp:
        database = Path(tmp) / "concurrency.db"
        setup = sqlite3.connect(database)
        try:
            setup.execute(
                """CREATE TABLE machine(
                       machine_id INTEGER PRIMARY KEY,
                       site TEXT NOT NULL,
                       parts_produced INTEGER NOT NULL DEFAULT 0
                   ) STRICT"""
            )
            setup.execute("INSERT INTO machine(machine_id, site) VALUES (1, 'Bielefeld')")
            setup.commit()
        finally:
            setup.close()

        first = sqlite3.connect(database, isolation_level=None)
        second = sqlite3.connect(database, isolation_level=None)
        lock_error = ""
        wait_ms = 0.0
        retry_succeeded = False
        try:
            second.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
            first.execute("BEGIN IMMEDIATE")
            first.execute(
                "UPDATE machine SET parts_produced = parts_produced + 1 WHERE machine_id = 1"
            )

            start = time.perf_counter()
            try:
                second.execute("BEGIN IMMEDIATE")
                second.execute(
                    "UPDATE machine SET parts_produced = parts_produced + 1 WHERE machine_id = 1"
                )
                second.execute("COMMIT")
            except sqlite3.OperationalError as exc:
                wait_ms = (time.perf_counter() - start) * 1000
                lock_error = str(exc)
                if second.in_transaction:
                    second.execute("ROLLBACK")

            first.execute("COMMIT")
            second.execute("BEGIN IMMEDIATE")
            second.execute(
                "UPDATE machine SET parts_produced = parts_produced + 1 WHERE machine_id = 1"
            )
            second.execute("COMMIT")
            retry_succeeded = True
            final_value = second.execute(
                "SELECT parts_produced FROM machine WHERE machine_id = 1"
            ).fetchone()[0]
        finally:
            first.close()
            second.close()

        exists_during_demo = database.exists()
    return {
        "scope": "local SQLite simulation; not a PostgreSQL classroom observation",
        "independent_connections": 2,
        "first_writer_transaction": "BEGIN IMMEDIATE; increment; hold; COMMIT",
        "second_writer_initial_result": lock_error,
        "busy_timeout_ms": busy_timeout_ms,
        "observed_wait_ms": wait_ms,
        "retry_after_first_commit_succeeded": retry_succeeded,
        "final_parts_produced": final_value,
        "database_existed_during_demo": exists_during_demo,
        "temporary_directory_removed": not database.parent.exists(),
    }


def main() -> None:
    print(json.dumps(run_demo(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
