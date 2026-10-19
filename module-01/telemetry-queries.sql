.headers on
.mode column
.timer on
.output module-01/telemetry-query-results.txt

.print === Query 1: Readings per machine ===
SELECT machine, COUNT(*) AS n
FROM readings
GROUP BY machine;

.print
.print === Query 2: Peak vibration per machine ===
SELECT machine, MAX(vib_rms) AS peak_vib
FROM readings
GROUP BY machine;

.print
.print === Query 3: Vibration alarms above 2.0 ===
SELECT COUNT(*) AS alarms
FROM readings
WHERE vib_rms > 2.0;

.output stdout
.timer off
