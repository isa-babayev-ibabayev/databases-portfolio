# Module 4 — Integrity Notes

## Learning Goals

1. Enforce entity, referential, and domain integrity with SQLite constraints.
2. Derive a value with a generated column and verify its calculation.
3. Use triggers for vibration alarms and value-change audit records.
4. Implement replay-safe DML and UPSERT ingestion.
5. Explain and demonstrate realistic access controls for a file database.

## Study Sources

- [Official HSBI Module 4 workbook](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/04-integrity-constraints-and-triggers.md)
- [SQLite CREATE TABLE documentation](https://www.sqlite.org/lang_createtable.html)
- [SQLite STRICT tables](https://www.sqlite.org/stricttables.html)
- [SQLite foreign keys](https://www.sqlite.org/foreignkeys.html)
- [SQLite generated columns](https://www.sqlite.org/gencol.html)
- [SQLite CREATE TRIGGER documentation](https://www.sqlite.org/lang_createtrigger.html)
- [SQLite UPSERT documentation](https://www.sqlite.org/lang_upsert.html)
- [SQLite URI filenames](https://www.sqlite.org/uri.html)
- [Python `sqlite3` documentation](https://docs.python.org/3/library/sqlite3.html)
- [Microsoft `icacls` documentation](https://learn.microsoft.com/windows-server/administration/windows-commands/icacls)

## Entity Integrity

`sensor_id`, `reading_id`, `alarm_id`, and `audit_id` are `INTEGER PRIMARY KEY`
columns. Duplicate explicit identifiers are rejected. Composite uniqueness on
`sensor(machine_id, metric)` prevents two definitions for the same machine and
measurement, while the unique index on `reading(sensor_id, ts)` is the natural
key used for replay-safe ingestion.

## Referential Integrity

`reading.sensor_id` and `alarm.sensor_id` reference `sensor.sensor_id`. The
ingestion connection explicitly executes and verifies `PRAGMA foreign_keys=ON`
because SQLite enforcement is a per-connection setting. The missing sensor 99
fixture fails with `FOREIGN KEY constraint failed`; the transaction rolls back
the valid row that precedes it. `PRAGMA foreign_key_check` returns no rows after
the normal import.

## Domain Integrity

`NOT NULL` protects required fields. `CHECK` limits metrics, requires a positive
interval, and limits values to -273.15 through 5000 inclusive. These rules
reject tested nonsense such as metric `bogus`, value `9000`, and interval 0,
but they cannot establish full physical plausibility: `4500` passes the broad
range, and an empty `machine_id` currently passes `NOT NULL`. Timestamp syntax
is also not validated beyond requiring a text value.

## STRICT Tables

All main tables are `STRICT`. SQLite 3.50.4 rejected `hot` in the `REAL` value
column, but accepted the numeric string `42.5` and stored it as type `real`.
`STRICT` therefore prevents values that cannot be losslessly converted; it does
not mean that any input whose original representation was text is rejected.

## Generated Columns

`reading.energy_j` is a virtual generated column defined as
`value * interval_s`. The seed row calculates 41.5 × 1 = 41.5, a row with value
2.5 and interval 4 calculates 10.0, and a direct INSERT into the generated
column is rejected. The name comes from the assignment, but the physical unit
is only joules if `value` is power in watts and `interval_s` is seconds; for
temperature or vibration the expression is a derived value, not energy.

## Triggers

`trg_vib_alarm` runs after a reading INSERT and creates an alarm only when its
sensor metric is `vib_rms` and its value is greater than 2.0. Tests cover 2.7,
the exact 2.0 boundary, a high temperature, a rejected invalid value, and
transaction rollback. `trg_reading_audit` stores the reading identifier plus
old and new values after `UPDATE OF value`. As written for the baseline task it
also records no-op updates.

The alarm trigger is intentionally the assigned INSERT-only version. An UPSERT
that takes its UPDATE branch can cross from 1.0 to 3.0 without creating an
alarm, although it creates an audit row. This is a documented coverage gap,
not evidence that threshold-crossing updates are protected.

## UPSERT and Idempotent Ingestion

The natural key `(sensor_id, ts)` selects the conflict target. The assigned
UPSERT is preserved in [`upsert-demo.sql`](upsert-demo.sql), while
[`ingest.py`](ingest.py) adds a `WHERE` clause so identical values do not cause
a redundant UPDATE and audit record. It parses the CSV, uses bound parameters
with `executemany`, enables foreign keys, and commits the batch atomically.
After two imports there were four readings, zero duplicate keys, one audit row,
and one alarm row. The negative fixture exited with code 3 and left those
counts unchanged.

## Access Control in SQLite

The `machine_health` view supplies a smaller reporting interface but is not a
permission boundary. URI `mode=ro` and `PRAGMA query_only=ON` both allowed
SELECT and rejected DELETE in the disposable test database. On Windows, NTFS
ACLs replace the workbook's Unix `chmod` example; `icacls` inspection succeeded
without changing permissions. Details and the PostgreSQL comparison are in
[`access-control.md`](access-control.md).

## Task A — Unconstrained vs Constrained Database

The unconstrained table accepted `9000`, text `hot` in a `REAL`-affinity
column, unsupported metric `bogus`, value `-500`, and an all-NULL row. The
constrained `STRICT` table rejected each applicable invalid case through type,
domain, mandatory-value, key, or uniqueness enforcement. A separate comparison
proved that `CHECK(value > 0)` accepts NULL because the expression is unknown,
whereas `NOT NULL CHECK(value > 0)` rejects it. Full output is in
[`constraint-results.txt`](constraint-results.txt).

## Task B — Neighboring-Pod Exercise

**Illustrative neighboring-pod exchange exercise — no real peer exchange is
claimed or verified.**

### Findings from our experiments

- A `REAL` affinity column in a non-STRICT table stored `hot` as text.
- `STRICT` rejected `hot` but losslessly converted numeric text `42.5`.
- `CHECK` alone did not reject NULL.
- A composite `UNIQUE` constraint supplied the ingestion natural key.
- The broad range allowed a plausible-looking but inappropriate value of 4500.

### Example questions for another pod

1. Did numeric text get rejected or losslessly converted in your SQLite build?
2. Does your CHECK constraint explicitly combine with NOT NULL?
3. Which columns form a stable natural key for replayed sensor messages?
4. Can a value pass your range rule while still being wrong for its metric?

### Illustrative technical comparison

A pod using only affinity might report that invalid text was stored, while a
pod using `STRICT` should see a datatype constraint error for non-convertible
text. A pod using only `CHECK(value > 0)` may be surprised that NULL passes; a
schema combining it with `NOT NULL` rejects the missing value. These answers
come from the local reproducible tests, not from another student's report.

### Points to verify in a real exchange

The student's real exchange should record the other pod's actual schema,
SQLite version, exact failing or accepted input, and observed error/result.
Names, group number, date, or quotations still require genuine student evidence.

## Questions Asked to AI and Verification

1. **Can CHECK alone reject NULL?** Testable claim: it cannot when the
   expression evaluates to NULL. Observed: `check_only` accepted NULL, while
   `check_and_not_null` rejected it. Support: `constraint-results.txt` and the
   automated test.
2. **Does STRICT reject every numeric string for REAL?** Testable claim: a
   losslessly convertible numeric string is accepted. Observed: `42.5` was
   stored as `real`; `hot` was rejected. Support: the constraint harness and
   tests.
3. **When is the alarm trigger necessary?** Testable claim: an INSERT trigger
   can produce an atomic alarm without application code. Observed: inserting
   vibration 2.7 created one alarm, while rollback removed both reading and
   alarm. Support: trigger demo and tests.
4. **What differs between BEFORE and AFTER triggers?** Testable claim: BEFORE
   can abort invalid work and AFTER can observe successful work. Observed: the
   optional negative insert raised `ABORT` and produced no AFTER log; a valid
   insert produced both rows. Support: `trigger-stretcher.md`.
5. **Are foreign keys automatically enforced on every SQLite connection?**
   Testable claim: the application must enable and verify them per connection.
   Observed: `ingest.py` enables the PRAGMA, sensor 99 fails, and the automated
   suite confirms the setting. Support: ingestion output and tests.

## Difficulties and Solutions

The largest interaction issue was that UPSERT UPDATE branches activate the
audit trigger but not the INSERT-only alarm trigger. The implementation keeps
the assigned trigger, tests the gap explicitly, and avoids redundant no-op
audit rows with a conditional UPSERT. Another issue was testing permissions on
Windows safely; URI read-only mode and `query_only` were exercised, while ACLs
were inspected without modifying the repository.

## Key Takeaways

Integrity needs overlapping controls: keys identify rows, foreign keys protect
relationships, domain constraints limit values, and transactions keep batches
atomic. `STRICT`, generated columns, triggers, UPSERT, views, and read-only
connections each solve a narrower problem and each has boundaries that should
be tested. Reproducible negative cases are stronger evidence than a schema
listing alone.
