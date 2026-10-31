-- Rebuild the disposable Module 4 edge database.
-- Run with: sqlite3 Module04/edge.db ".read Module04/setup.sql"

PRAGMA foreign_keys = OFF;

DROP VIEW IF EXISTS machine_health;
DROP TRIGGER IF EXISTS trg_reading_audit;
DROP TRIGGER IF EXISTS trg_vib_alarm;
DROP TABLE IF EXISTS audit;
DROP TABLE IF EXISTS alarm;
DROP TABLE IF EXISTS reading;
DROP TABLE IF EXISTS sensor;

PRAGMA foreign_keys = ON;

CREATE TABLE sensor(
    sensor_id INTEGER PRIMARY KEY,
    machine_id TEXT NOT NULL,
    metric TEXT NOT NULL
        CHECK(metric IN ('temp_c','vib_rms','spindle_load')),
    unit TEXT NOT NULL,
    UNIQUE(machine_id, metric)
) STRICT;

CREATE TABLE reading(
    reading_id INTEGER PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(sensor_id),
    ts TEXT NOT NULL,
    value REAL NOT NULL,
    interval_s INTEGER NOT NULL CHECK(interval_s > 0),
    energy_j REAL GENERATED ALWAYS AS (value * interval_s) VIRTUAL,
    CHECK(value >= -273.15 AND value <= 5000)
) STRICT;

CREATE UNIQUE INDEX ux_reading_sensor_ts
ON reading(sensor_id, ts);

CREATE TABLE alarm(
    alarm_id INTEGER PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(sensor_id),
    ts TEXT NOT NULL,
    value REAL NOT NULL,
    reason TEXT NOT NULL
) STRICT;

CREATE TABLE audit(
    audit_id INTEGER PRIMARY KEY,
    reading_id INTEGER NOT NULL,
    old_value REAL,
    new_value REAL,
    changed_at TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;

CREATE TRIGGER trg_vib_alarm
AFTER INSERT ON reading
FOR EACH ROW
WHEN NEW.value > 2.0
AND (
    SELECT metric
    FROM sensor
    WHERE sensor_id = NEW.sensor_id
) = 'vib_rms'
BEGIN
    INSERT INTO alarm(sensor_id, ts, value, reason)
    VALUES (
        NEW.sensor_id,
        NEW.ts,
        NEW.value,
        'vibration over 2.0 mm/s'
    );
END;

-- This assigned baseline records every UPDATE statement, including no-op
-- assignments. ingest.py avoids redundant no-op UPSERT updates explicitly.
CREATE TRIGGER trg_reading_audit
AFTER UPDATE OF value ON reading
FOR EACH ROW
BEGIN
    INSERT INTO audit(reading_id, old_value, new_value)
    VALUES (NEW.reading_id, OLD.value, NEW.value);
END;

CREATE VIEW machine_health AS
SELECT
    s.machine_id,
    s.metric,
    MAX(r.value) AS peak,
    COUNT(*) AS n
FROM sensor AS s
JOIN reading AS r USING(sensor_id)
GROUP BY s.machine_id, s.metric;

INSERT INTO sensor
VALUES
    (1,'cnc-01','temp_c','degC'),
    (2,'cnc-01','vib_rms','mm/s');

INSERT INTO reading(sensor_id, ts, value, interval_s)
VALUES (1,'2026-03-01 08:00:00',41.5,1);

PRAGMA foreign_key_check;
PRAGMA integrity_check;
