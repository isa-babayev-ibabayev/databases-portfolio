-- Deterministic execution of the trigger example from the assignment.
-- Run after setup.sql in a disposable database.

INSERT INTO reading(sensor_id, ts, value, interval_s)
VALUES (2, '2026-03-01 09:00:00', 2.7, 1);

SELECT alarm_id, sensor_id, ts, value, reason
FROM alarm
ORDER BY alarm_id;

UPDATE reading
SET value = 1.4
WHERE sensor_id = 2
  AND ts = '2026-03-01 09:00:00';

SELECT audit_id, reading_id, old_value, new_value, changed_at
FROM audit
ORDER BY audit_id;
