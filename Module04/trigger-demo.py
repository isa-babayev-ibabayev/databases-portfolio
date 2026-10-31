"""Execute deterministic alarm, audit, and UPSERT-trigger demonstrations."""

from __future__ import annotations

import sqlite3
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent


def database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.executescript((MODULE_DIR / "setup.sql").read_text(encoding="utf-8"))
    return connection


def main() -> None:
    print(f"Python SQLite runtime: {sqlite3.sqlite_version}")

    connection = database()
    print("## Assigned trigger example")
    connection.execute(
        "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (2,?,2.7,1)",
        ("2026-03-01 09:00:00",),
    )
    alarm = connection.execute(
        "SELECT alarm_id,sensor_id,ts,value,reason FROM alarm"
    ).fetchone()
    print("alarm: " + " | ".join(map(str, alarm)))
    connection.execute("UPDATE reading SET value=1.4 WHERE sensor_id=2")
    audit = connection.execute(
        "SELECT audit_id,reading_id,old_value,new_value,changed_at FROM audit"
    ).fetchone()
    print("audit: " + " | ".join(map(str, audit)))
    connection.close()

    connection = database()
    print("\n## Threshold and metric checks")
    rows = [
        (2, "2026-03-01 09:10:00", 2.0, 1),
        (2, "2026-03-01 09:11:00", 1.9, 1),
        (1, "2026-03-01 09:12:00", 100.0, 1),
    ]
    connection.executemany(
        "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (?,?,?,?)", rows
    )
    print(f"alarms after threshold/metric controls: {connection.execute('SELECT count(*) FROM alarm').fetchone()[0]}")
    try:
        connection.execute(
            "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (2,?,9000,1)",
            ("2026-03-01 09:13:00",),
        )
    except sqlite3.IntegrityError as exc:
        print(f"invalid insert rejected: {exc}")
    print(f"alarms after rejected insert: {connection.execute('SELECT count(*) FROM alarm').fetchone()[0]}")
    connection.close()

    connection = database()
    print("\n## UPDATE and UPSERT side effects")
    connection.execute(
        "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (2,?,1.0,1)",
        ("2026-03-01 10:00:00",),
    )
    connection.execute(
        """
        INSERT INTO reading(sensor_id,ts,value,interval_s)
        VALUES (2,'2026-03-01 10:00:00',3.0,1)
        ON CONFLICT(sensor_id,ts) DO UPDATE SET value=excluded.value
        """
    )
    print(f"alarms after below-to-above UPSERT: {connection.execute('SELECT count(*) FROM alarm').fetchone()[0]}")
    print(f"audits after below-to-above UPSERT: {connection.execute('SELECT count(*) FROM audit').fetchone()[0]}")
    connection.execute(
        """
        INSERT INTO reading(sensor_id,ts,value,interval_s)
        VALUES (2,'2026-03-01 10:00:00',3.0,1)
        ON CONFLICT(sensor_id,ts) DO UPDATE SET value=excluded.value
        """
    )
    print(f"audits after baseline no-op UPSERT: {connection.execute('SELECT count(*) FROM audit').fetchone()[0]}")
    connection.execute(
        """
        INSERT INTO reading(sensor_id,ts,value,interval_s)
        VALUES (2,'2026-03-01 10:00:00',3.0,1)
        ON CONFLICT(sensor_id,ts) DO UPDATE SET value=excluded.value
        WHERE reading.value IS NOT excluded.value
        """
    )
    print(f"audits after conditional no-op UPSERT: {connection.execute('SELECT count(*) FROM audit').fetchone()[0]}")
    connection.close()


if __name__ == "__main__":
    main()
