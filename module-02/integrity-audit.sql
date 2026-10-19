.headers on
.mode column

SELECT 'DEFECT 1 - orphan maintenance jobs' AS section;
SELECT m.job_id, m.machine_name
FROM maint_job AS m
LEFT JOIN machine AS x ON m.machine_name = x.machine_name
WHERE x.machine_name IS NULL;

SELECT 'DEFECT 2 - duplicate natural keys' AS section;
SELECT part_no, COUNT(*) AS copies
FROM part
GROUP BY part_no
HAVING COUNT(*) > 1;

SELECT 'DEFECT 3A - TEXT comparison from workbook' AS section;
SELECT part_no, unit_price
FROM part
WHERE unit_price < '15';

SELECT 'DEFECT 3B - numeric comparison' AS section;
SELECT part_no, unit_price, CAST(unit_price AS NUMERIC) AS numeric_price
FROM part
WHERE CAST(unit_price AS NUMERIC) < 15;

SELECT 'DEFECT 3C - explicit counterexample' AS section;
SELECT '9.90' < '15' AS text_says_less,
       CAST('9.90' AS NUMERIC) < 15 AS numeric_says_less;

SELECT 'DEFECT 4 - invalid installation date shape' AS section;
SELECT machine_name, installed
FROM machine
WHERE installed NOT GLOB
      '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]';

SELECT 'DEFECT 5 - naive comma-list join' AS section;
SELECT j.job_id, j.parts_used, p.part_no, p.description
FROM maint_job AS j
JOIN part AS p ON p.part_no = j.parts_used
ORDER BY j.job_id, p.rowid;

SELECT 'ADDITIONAL - declared schema constraints' AS section;
SELECT name, sql FROM sqlite_master
WHERE type = 'table'
ORDER BY name;
