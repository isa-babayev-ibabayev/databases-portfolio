.headers on
.mode column
.bail off
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS exercise_sensor;
DROP TABLE IF EXISTS exercise_machine;

CREATE TABLE exercise_machine (
    machine_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE exercise_sensor (
    sensor_id INTEGER PRIMARY KEY,
    machine_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES exercise_machine(machine_id)
);

INSERT INTO exercise_machine VALUES (1, 'CNC mill');
INSERT INTO exercise_sensor VALUES (101, 1, 'spindle temperature');
INSERT INTO exercise_sensor VALUES (102, 1, 'vibration');

SELECT m.machine_id, m.name, COUNT(s.sensor_id) AS sensor_count
FROM exercise_machine AS m
LEFT JOIN exercise_sensor AS s ON s.machine_id = m.machine_id
GROUP BY m.machine_id, m.name;

-- Expected constraint failure: parent 999 does not exist.
INSERT INTO exercise_sensor VALUES (103, 999, 'orphan attempt');

SELECT COUNT(*) AS sensors_after_rejected_orphan FROM exercise_sensor;
