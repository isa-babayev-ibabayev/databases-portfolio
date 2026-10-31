"""Optional BEFORE/AFTER and INSTEAD OF trigger experiments."""

from __future__ import annotations

import sqlite3


def main() -> None:
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE gated_reading(
            reading_id INTEGER PRIMARY KEY,
            value REAL NOT NULL
        ) STRICT;
        CREATE TABLE after_log(
            reading_id INTEGER NOT NULL,
            value REAL NOT NULL
        ) STRICT;
        CREATE TRIGGER before_reject_negative
        BEFORE INSERT ON gated_reading
        WHEN NEW.value < 0
        BEGIN
            SELECT RAISE(ABORT, 'negative values blocked by BEFORE trigger');
        END;
        CREATE TRIGGER after_record_success
        AFTER INSERT ON gated_reading
        BEGIN
            INSERT INTO after_log VALUES(NEW.reading_id, NEW.value);
        END;

        CREATE TABLE routed_reading(
            reading_id INTEGER PRIMARY KEY,
            value REAL NOT NULL
        ) STRICT;
        CREATE VIEW reading_entry AS
        SELECT reading_id, value FROM routed_reading;
        CREATE TRIGGER route_view_insert
        INSTEAD OF INSERT ON reading_entry
        BEGIN
            INSERT INTO routed_reading(reading_id,value)
            VALUES(NEW.reading_id,NEW.value);
        END;
        """
    )
    print(f"Python SQLite runtime: {sqlite3.sqlite_version}")
    try:
        connection.execute("INSERT INTO gated_reading(value) VALUES(-1)")
    except sqlite3.IntegrityError as exc:
        print(f"BEFORE trigger rejection: {exc}")
    print(f"rows after rejected BEFORE insert: {connection.execute('SELECT count(*) FROM gated_reading').fetchone()[0]}")
    print(f"AFTER log rows after rejection: {connection.execute('SELECT count(*) FROM after_log').fetchone()[0]}")
    connection.execute("INSERT INTO gated_reading(value) VALUES(2.5)")
    print(f"successful row: {connection.execute('SELECT reading_id,value FROM gated_reading').fetchone()}")
    print(f"AFTER log row: {connection.execute('SELECT reading_id,value FROM after_log').fetchone()}")
    connection.execute("INSERT INTO reading_entry(reading_id,value) VALUES(10,7.5)")
    print(f"INSTEAD OF routed row: {connection.execute('SELECT reading_id,value FROM routed_reading').fetchone()}")
    connection.close()


if __name__ == "__main__":
    main()
