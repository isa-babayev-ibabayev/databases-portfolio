-- Task A: unconstrained acceptance table and constrained comparison table.

DROP TABLE IF EXISTS t;
DROP TABLE IF EXISTS t_constrained;
DROP TABLE IF EXISTS check_only;
DROP TABLE IF EXISTS check_and_not_null;

CREATE TABLE t(
    sensor_id INTEGER,
    metric TEXT,
    value REAL
);

INSERT INTO t VALUES
    (1, 'temp_c', 9000),
    (1, 'temp_c', 'hot'),
    (2, 'bogus', -500),
    (NULL, NULL, NULL);

CREATE TABLE t_constrained(
    sample_id INTEGER PRIMARY KEY,
    sensor_id INTEGER NOT NULL,
    metric TEXT NOT NULL
        CHECK(metric IN ('temp_c', 'vib_rms', 'spindle_load')),
    value REAL NOT NULL
        CHECK(value BETWEEN -273.15 AND 5000),
    UNIQUE(sensor_id, metric)
) STRICT;

CREATE TABLE check_only(
    value REAL CHECK(value > 0)
) STRICT;

CREATE TABLE check_and_not_null(
    value REAL NOT NULL CHECK(value > 0)
) STRICT;
