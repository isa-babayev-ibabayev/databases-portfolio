"""Measure 10,000-row ingestion with and without the vibration trigger."""

from __future__ import annotations

import platform
import sqlite3
import statistics
import time
from datetime import datetime, timedelta


ROWS = 10_000
TRIALS = 5

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE sensor(
    sensor_id INTEGER PRIMARY KEY,
    metric TEXT NOT NULL
) STRICT;
CREATE TABLE reading(
    reading_id INTEGER PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(sensor_id),
    ts TEXT NOT NULL,
    value REAL NOT NULL
) STRICT;
CREATE TABLE alarm(
    alarm_id INTEGER PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(sensor_id),
    ts TEXT NOT NULL,
    value REAL NOT NULL,
    reason TEXT NOT NULL
) STRICT;
INSERT INTO sensor VALUES (2, 'vib_rms');
"""

TRIGGER = """
CREATE TRIGGER trg_vib_alarm
AFTER INSERT ON reading
FOR EACH ROW
WHEN NEW.value > 2.0
AND (SELECT metric FROM sensor WHERE sensor_id=NEW.sensor_id)='vib_rms'
BEGIN
    INSERT INTO alarm(sensor_id,ts,value,reason)
    VALUES(NEW.sensor_id,NEW.ts,NEW.value,'vibration over 2.0 mm/s');
END;
"""

START = datetime(2026, 3, 2, 8, 0, 0)
DATA = [
    (
        2,
        (START + timedelta(seconds=index)).isoformat(sep=" "),
        2.7 if index % 2 == 0 else 1.4,
    )
    for index in range(ROWS)
]


def run_once(with_trigger: bool) -> tuple[float, int, int]:
    connection = sqlite3.connect(":memory:")
    connection.executescript(SCHEMA)
    if with_trigger:
        connection.executescript(TRIGGER)
    start = time.perf_counter()
    with connection:
        connection.executemany(
            "INSERT INTO reading(sensor_id,ts,value) VALUES (?,?,?)", DATA
        )
    elapsed = time.perf_counter() - start
    readings = connection.execute("SELECT count(*) FROM reading").fetchone()[0]
    alarms = connection.execute("SELECT count(*) FROM alarm").fetchone()[0]
    connection.close()
    return elapsed, readings, alarms


def main() -> None:
    without: list[float] = []
    with_alarm: list[float] = []
    for trial in range(TRIALS):
        order = (False, True) if trial % 2 == 0 else (True, False)
        for enabled in order:
            elapsed, readings, alarms = run_once(enabled)
            if readings != ROWS or alarms != (ROWS // 2 if enabled else 0):
                raise RuntimeError("benchmark verification failed")
            (with_alarm if enabled else without).append(elapsed)

    without_median = statistics.median(without)
    with_median = statistics.median(with_alarm)
    overhead = (with_median / without_median - 1.0) * 100.0

    print(f"Python: {platform.python_version()}")
    print(f"SQLite runtime: {sqlite3.sqlite_version}")
    print(f"Rows per trial: {ROWS}")
    print(f"Trials per scenario: {TRIALS}")
    print("Without trigger trials (s): " + ", ".join(f"{v:.6f}" for v in without))
    print("With trigger trials (s): " + ", ".join(f"{v:.6f}" for v in with_alarm))
    print(f"Without trigger median (s): {without_median:.6f}")
    print(f"Without trigger throughput (rows/s): {ROWS / without_median:.2f}")
    print(f"With trigger median (s): {with_median:.6f}")
    print(f"With trigger throughput (rows/s): {ROWS / with_median:.2f}")
    print(f"Measured median overhead (%): {overhead:.2f}")
    print(f"Verified alarm rows per triggered trial: {ROWS // 2}")


if __name__ == "__main__":
    main()
