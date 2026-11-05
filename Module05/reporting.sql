-- Round 4 dashboard queries. Both return the same logical result.
-- Date filter is the last 31 generated days, beginning 2026-03-01.

-- Normalized four-table query.
SELECT m.machine_id, m.site, j.technician, SUM(p.part_price) AS cost
FROM job AS j
JOIN machine AS m ON m.machine_id = j.machine_id
JOIN job_part AS jp ON jp.job_id = j.job_id
JOIN part AS p ON p.part_no = jp.part_no
WHERE j.done_on >= date('2026-03-01')
GROUP BY m.machine_id, m.site, j.technician
ORDER BY m.machine_id, j.technician;

-- Denormalized single-table query.
SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM report_jobpart
WHERE done_on >= date('2026-03-01')
GROUP BY machine_id, site, technician
ORDER BY machine_id, technician;
