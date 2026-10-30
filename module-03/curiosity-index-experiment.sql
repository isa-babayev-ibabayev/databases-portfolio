-- Curiosity exercise: when an index helps, and when it does not.
-- Run safely with:
-- sqlite3 :memory: ".read module-03/curiosity-index-experiment.sql"

CREATE TABLE technician_log (
    log_id INTEGER PRIMARY KEY,
    technician TEXT NOT NULL,
    note TEXT NOT NULL
);

WITH RECURSIVE n(x) AS (
    SELECT 1
    UNION ALL
    SELECT x + 1 FROM n WHERE x < 1000
)
INSERT INTO technician_log(log_id, technician, note)
SELECT x,
       CASE x % 4
           WHEN 0 THEN 'Beier'
           WHEN 1 THEN 'Kaya'
           WHEN 2 THEN 'Smith'
           ELSE 'Garcia'
       END,
       'maintenance log ' || x
FROM n;

SELECT COUNT(*) AS total_rows,
       COUNT(DISTINCT technician) AS technicians,
       SUM(technician = 'Beier') AS beier_rows
FROM technician_log;

-- Prediction: without an index, equality must scan the table.
EXPLAIN QUERY PLAN
SELECT * FROM technician_log WHERE technician = 'Beier';

CREATE INDEX ix_technician_log_name
ON technician_log(technician);

-- Prediction: equality can now use the technician index.
EXPLAIN QUERY PLAN
SELECT * FROM technician_log WHERE technician = 'Beier';

-- Prediction: the leading wildcard still prevents a selective B-tree search.
EXPLAIN QUERY PLAN
SELECT * FROM technician_log WHERE technician LIKE '%ei%';

SELECT name, sql
FROM sqlite_master
WHERE type = 'index' AND name = 'ix_technician_log_name';
