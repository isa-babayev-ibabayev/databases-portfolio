SELECT
    machine,
    ROUND(AVG(spindle_load), 2) AS avg_spindle_load
FROM readings
WHERE time(ts) > '18:00:00'
GROUP BY machine
ORDER BY avg_spindle_load DESC;
