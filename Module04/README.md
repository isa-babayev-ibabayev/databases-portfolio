# Module 4 — Data Integrity, Constraints & Edge Triggers

## Overview

This module builds a reproducible SQLite edge database for machine sensor
readings. It contrasts unsafe affinity-only storage with enforced integrity,
then verifies generated values, replay-safe ingestion, trigger side effects,
performance, reporting views, and read-only access. All generated databases are
disposable and excluded from Git; the committed SQL and Python files rebuild
the evidence.

## Learning Goals

1. **Constraints:** enforce `NOT NULL`, `UNIQUE`, `CHECK`, `PRIMARY KEY`,
   `FOREIGN KEY`, and `STRICT` rules.
2. **Generated columns:** calculate and verify a derived column.
3. **Triggers:** create automatic vibration alarms and change audits.
4. **DML and UPSERT:** ingest CSV data repeatedly without duplicate readings.
5. **DCL and access control:** demonstrate SQLite views, read-only connections,
   filesystem considerations, and contrast them with PostgreSQL privileges.

## Evidence Map

| Learning goal | Direct implementation | Executed evidence |
|---|---|---|
| LG1 — Constraints | [`setup.sql`](setup.sql), [`scratch-constraints.sql`](scratch-constraints.sql), [`constraint-tests.py`](constraint-tests.py) | [`constraint-results.txt`](constraint-results.txt), [`tests/test_module04.py`](tests/test_module04.py) |
| LG2 — Generated columns | [`setup.sql`](setup.sql) (`energy_j`), [`constraint-tests.py`](constraint-tests.py) | [`constraint-results.txt`](constraint-results.txt), [`test-results.txt`](test-results.txt) |
| LG3 — Triggers | [`triggers.sql`](triggers.sql), [`trigger-demo.sql`](trigger-demo.sql), [`trigger-demo.py`](trigger-demo.py), [`benchmark.py`](benchmark.py) | [`trigger-results.txt`](trigger-results.txt), [`benchmark-results.md`](benchmark-results.md) |
| LG4 — DML and UPSERT | [`upsert-demo.sql`](upsert-demo.sql), [`ingest.py`](ingest.py), [`readings.csv`](readings.csv), [`invalid-readings.csv`](invalid-readings.csv) | [`ingestion-results.txt`](ingestion-results.txt), [`test-results.txt`](test-results.txt) |
| LG5 — DCL and access control | [`access-control.md`](access-control.md), [`access-control-demo.py`](access-control-demo.py), `machine_health` in [`setup.sql`](setup.sql) | [`access-control-results.txt`](access-control-results.txt), [`test-results.txt`](test-results.txt) |

Supporting explanation is collected in
[`integrity-notes.md`](integrity-notes.md). Optional trigger-timing evidence is
in [`trigger-stretcher.md`](trigger-stretcher.md) and
[`trigger-stretcher.py`](trigger-stretcher.py).

## Environment and Requirements

Recorded verification environment:

- Windows with PowerShell
- Python 3.14.5 through `uv`
- Python SQLite runtime 3.50.4
- SQLite CLI 3.53.4

The implementation uses only the Python standard library. `uv` is used for the
documented commands; a compatible Python 3 installation can run the scripts
directly. SQLite 3.37 or newer is required for `STRICT` tables.

## Reproduction Steps

From the repository root in PowerShell:

```powershell
# Rebuild a disposable local database (edge.db is ignored by Git).
sqlite3 Module04/edge.db ".read Module04/setup.sql"

# Run acceptance cases that continue after expected failures.
uv run python Module04/constraint-tests.py

# Import the same CSV twice; the second run must not add duplicates.
uv run python Module04/ingest.py Module04/edge.db Module04/readings.csv
uv run python Module04/ingest.py Module04/edge.db Module04/readings.csv

# Run deterministic trigger, performance, access, and optional experiments.
uv run python Module04/trigger-demo.py
uv run python Module04/benchmark.py
uv run python Module04/access-control-demo.py
uv run python Module04/trigger-stretcher.py

# Run the isolated automated suite.
uv run python -m unittest discover -s Module04/tests -v
```

To initialize a database without using the SQLite CLI:

```powershell
uv run python Module04/ingest.py Module04/edge.db Module04/readings.csv --init
```

The negative fixture is intentionally separate from the normal import:

```powershell
uv run python Module04/ingest.py Module04/edge.db Module04/invalid-readings.csv
```

It should exit with code 3 on the missing sensor and roll back its complete
batch.

## Task A — Integrity Acceptance Tests

The unconstrained table accepted out-of-range numbers, unsupported metrics,
NULLs, and text in a REAL-affinity column. The constrained `STRICT` version
rejected incompatible types and violations of key, uniqueness, mandatory-value,
and domain rules. It also demonstrated two important boundaries: CHECK alone
accepts NULL, and the broad range still accepts the plausible but wrong value
4500. See [`constraint-results.txt`](constraint-results.txt).

## Task B — Pod Study

[`integrity-notes.md`](integrity-notes.md#task-b--neighboring-pod-exercise)
contains an **illustrative neighboring-pod exchange exercise** based on the
executed results. No real neighboring-pod exchange, participant, date, or
Discord post is claimed. Actual collaborative participation remains subject to
student confirmation and evidence.

## Studio Task 1 — Constraints

The edge schema combines primary and foreign keys, a composite unique key,
`NOT NULL`, `CHECK`, and `STRICT`. The virtual generated column calculates
`value * interval_s`; its output and write protection are tested. Foreign-key
and database integrity checks both pass.

## Studio Task 2 — UPSERT Ingestion

`ingest.py` validates CSV structure and conversions, binds parameters, enables
foreign keys, and imports the batch transactionally. `(sensor_id, ts)` is the
natural conflict key. A conditional UPSERT changes corrected readings but
skips identical values, preventing duplicate readings and redundant no-op
audit rows. Two normal imports ended with four readings and zero duplicate
keys; the invalid batch left the database unchanged.

## Studio Task 3 — Triggers and Audit

The required AFTER INSERT trigger creates alarms for vibration values greater
than 2.0, and the AFTER UPDATE trigger records old and new values. Exact
threshold, wrong metric, constraint failure, rollback, no-op, and UPSERT paths
are tested. The 10,000-row benchmark measured a 0.009106 s median without the
alarm trigger and 0.027644 s with it in the recorded environment, a 203.59%
median overhead with 5,000 alarm writes.

## Studio Task 4 — Access Control

The `machine_health` view returns grouped reporting data. URI `mode=ro` and
`PRAGMA query_only=ON` both allowed reads and rejected a DELETE. Windows ACLs
were inspected on a disposable database with `icacls`; no permissions were
changed. A view and connection PRAGMA are not substitutes for PostgreSQL-style
roles and grants or for appropriate OS controls.

## Optional Task 5 — Trigger Timing

The completed optional experiment proves that a BEFORE trigger can reject an
insert with `RAISE`, an AFTER trigger records only successful work, and an
INSTEAD OF trigger can route an INSERT on a view to its base table. See
[`trigger-stretcher.md`](trigger-stretcher.md).

## Automated Test Results

The command below executed **34 tests**, all passing:

```text
Ran 34 tests in 0.614s

OK
```

The full recorded output is in [`test-results.txt`](test-results.txt).

## Known Limitations

- The assigned alarm trigger handles INSERT only; an UPSERT UPDATE that crosses
  the threshold does not create an alarm. The test suite preserves and proves
  this limitation.
- The assigned audit trigger records every `UPDATE OF value`, including a no-op.
  The ingestion UPSERT avoids no-op updates, but arbitrary SQL can still create
  such audit rows.
- The broad value range is not metric-specific, an empty machine identifier is
  currently accepted, and timestamp format is not validated.
- `energy_j` is physically an energy value only when `value` represents power;
  with temperature or vibration it is merely the assignment's derived product.
- Foreign-key enforcement and `query_only` are connection-specific. The view is
  not an access-control boundary.
- Windows ACL changes were not performed, so OS-level write denial is not
  claimed. The actual peer exchange also remains unverified.
- Benchmark values describe one run and will vary by software build, hardware,
  and system load.

## Reflection

The Module 4 reflection draft is available at
[`../Reflections/ref04.md`](../Reflections/ref04.md).
