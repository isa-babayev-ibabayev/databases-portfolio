-- Round 2 reference SQL. Run only on a disposable database.
CREATE TABLE flat5(
    job_id INTEGER,
    machine_id TEXT,
    site TEXT,
    technician TEXT,
    part_no TEXT,
    part_price REAL
);

INSERT INTO flat5 VALUES
    (1,'cnc-01','Gütersloh','tech-0','P-0001',6.00),
    (1,'cnc-01','Gütersloh','tech-0','P-0002',7.00),
    (2,'cnc-02','Gütersloh','tech-1','P-0001',6.00),
    (2,'cnc-02','Gütersloh','tech-1','P-0003',8.50),
    (3,'cnc-01','Gütersloh','tech-0','P-0003',8.50);

-- Update anomaly: this intentionally updates only one of three cnc-01 rows.
UPDATE flat5
SET site = 'Bielefeld'
WHERE job_id = 1 AND part_no = 'P-0001';
SELECT machine_id, site, COUNT(*) AS rows
FROM flat5 WHERE machine_id = 'cnc-01'
GROUP BY machine_id, site ORDER BY site;

-- Insert anomaly: SQLite accepts this NULL-filled placeholder because flat5 has
-- no constraints, but unrelated job facts must be invented or left missing.
INSERT INTO flat5(job_id,machine_id,site,technician,part_no,part_price)
VALUES(NULL,NULL,NULL,NULL,'P-0099',12.50);

-- Delete anomaly: P-0002 occurs once, so its only stored price vanishes.
DELETE FROM flat5 WHERE part_no = 'P-0002';
SELECT COUNT(*) AS remaining_p0002_rows FROM flat5 WHERE part_no = 'P-0002';
