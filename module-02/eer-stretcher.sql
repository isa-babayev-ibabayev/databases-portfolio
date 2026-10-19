.headers on
.mode column
.bail off
PRAGMA foreign_keys = ON;

-- Alternative A: single table with discriminator.
CREATE TABLE single_machine (
    machine_id INTEGER PRIMARY KEY,
    machine_type TEXT NOT NULL CHECK (machine_type IN ('cnc_mill', 'injection_molder')),
    serial_no TEXT NOT NULL UNIQUE,
    spindle_speed_rpm INTEGER,
    clamping_force_kn INTEGER,
    CHECK (
      (machine_type = 'cnc_mill'
       AND spindle_speed_rpm IS NOT NULL
       AND clamping_force_kn IS NULL)
      OR
      (machine_type = 'injection_molder'
       AND clamping_force_kn IS NOT NULL
       AND spindle_speed_rpm IS NULL)
    )
);

INSERT INTO single_machine VALUES (1, 'cnc_mill', 'SN-CNC-1', 12000, NULL);
INSERT INTO single_machine VALUES (2, 'injection_molder', 'SN-IM-1', NULL, 500);
SELECT machine_id, machine_type FROM single_machine ORDER BY machine_id;

-- Expected CHECK failure: subtype fields conflict with discriminator.
INSERT INTO single_machine VALUES (3, 'cnc_mill', 'SN-BAD-1', NULL, 500);

-- Alternative B: shared supertype plus one-to-one subtype tables.
CREATE TABLE base_machine (
    machine_id INTEGER PRIMARY KEY,
    serial_no TEXT NOT NULL UNIQUE
);
CREATE TABLE cnc_mill (
    machine_id INTEGER PRIMARY KEY REFERENCES base_machine(machine_id),
    spindle_speed_rpm INTEGER NOT NULL CHECK (spindle_speed_rpm > 0)
);
CREATE TABLE injection_molder (
    machine_id INTEGER PRIMARY KEY REFERENCES base_machine(machine_id),
    clamping_force_kn INTEGER NOT NULL CHECK (clamping_force_kn > 0)
);

INSERT INTO base_machine VALUES (10, 'SN-CNC-10');
INSERT INTO cnc_mill VALUES (10, 15000);

-- Expected FK failure: subtype row has no supertype.
INSERT INTO injection_molder VALUES (999, 400);

SELECT b.machine_id, b.serial_no, c.spindle_speed_rpm
FROM base_machine AS b
JOIN cnc_mill AS c USING (machine_id);
