.headers on
.mode column

SELECT 'parts per job encoded in text' AS section;
SELECT job_id, parts_used,
       LENGTH(parts_used) - LENGTH(REPLACE(parts_used, ',', '')) + 1 AS n_parts
FROM maint_job
ORDER BY job_id;

SELECT 'jobs with multiple parts' AS section;
SELECT COUNT(*) AS jobs_with_multiple_parts
FROM maint_job
WHERE LENGTH(parts_used) - LENGTH(REPLACE(parts_used, ',', '')) + 1 > 1;

SELECT 'machines occurring in multiple jobs' AS section;
SELECT machine_name, COUNT(*) AS job_count
FROM maint_job
GROUP BY machine_name
HAVING COUNT(*) > 1;

SELECT 'distinct technicians' AS section;
SELECT COUNT(DISTINCT technician) AS distinct_technicians
FROM maint_job;

SELECT 'part tokens occurring in multiple jobs' AS section;
WITH RECURSIVE split(job_id, rest, part_no) AS (
  SELECT job_id, COALESCE(parts_used, '') || ',', '' FROM maint_job
  UNION ALL
  SELECT job_id,
         SUBSTR(rest, INSTR(rest, ',') + 1),
         TRIM(SUBSTR(rest, 1, INSTR(rest, ',') - 1))
  FROM split WHERE rest <> ''
)
SELECT part_no, COUNT(DISTINCT job_id) AS job_count
FROM split
WHERE part_no <> ''
GROUP BY part_no
HAVING COUNT(DISTINCT job_id) > 1;

SELECT 'observed job-to-machine matching' AS section;
SELECT COUNT(*) AS total_jobs,
       COUNT(x.machine_name) AS jobs_matching_a_machine,
       COUNT(*) - COUNT(x.machine_name) AS orphan_jobs
FROM maint_job AS j
LEFT JOIN machine AS x ON x.machine_name = j.machine_name;
