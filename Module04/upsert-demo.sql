-- Assigned baseline UPSERT: updates the existing natural key.
INSERT INTO reading(sensor_id, ts, value, interval_s)
VALUES (1,'2026-03-01 08:00:00',41.7,1)
ON CONFLICT(sensor_id, ts)
DO UPDATE SET value = excluded.value;

-- Replay-safe variant used by ingest.py. The WHERE clause prevents a no-op
-- UPDATE from creating a redundant audit row.
INSERT INTO reading(sensor_id, ts, value, interval_s)
VALUES (1,'2026-03-01 08:00:00',41.7,1)
ON CONFLICT(sensor_id, ts)
DO UPDATE SET
    value = excluded.value,
    interval_s = excluded.interval_s
WHERE reading.value IS NOT excluded.value
   OR reading.interval_s IS NOT excluded.interval_s;
