-- Module 4 alarm and audit triggers.
-- These definitions are also included by setup.sql for a one-command rebuild.

DROP TRIGGER IF EXISTS trg_reading_audit;
DROP TRIGGER IF EXISTS trg_vib_alarm;

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

-- The assigned baseline records every UPDATE OF value, including a no-op.
-- ingest.py prevents redundant no-op UPSERT updates at the statement level.
CREATE TRIGGER trg_reading_audit
AFTER UPDATE OF value ON reading
FOR EACH ROW
BEGIN
    INSERT INTO audit(reading_id, old_value, new_value)
    VALUES (NEW.reading_id, OLD.value, NEW.value);
END;
