# Integrity-defect analysis

The exact SQL is in [integrity-audit.sql](integrity-audit.sql); real output is
in [integrity-results.txt](integrity-results.txt).

## 1. Orphan maintenance job

The left join finds job 3 referencing `cnc-05`, which is absent from Machine.
Production reports cannot reliably assign this job to a site or asset. Replace
the text with a non-null `machine_id` foreign key and enable
`PRAGMA foreign_keys = ON`; the corrected test proves an orphan insert fails.

## 2. Duplicate part identity

`P-1003` occurs twice. Joins can double-count it, inventory changes are
ambiguous, and updates can change only one copy. Make `part_no` a primary key
(or use a surrogate key while keeping `part_no UNIQUE`). Existing duplicates
must be reviewed and merged before adding the constraint.

## 3. Price stored as TEXT

The workbook query `unit_price < '15'` returns only `12.50`; it incorrectly
excludes both `9.90` rows because strings are ordered lexicographically
(`'9'` is greater than `'1'`). Casting to NUMERIC returns all three rows
below 15. This can corrupt filters, totals, and invoices. The repaired design
uses `NUMERIC(9,2) NOT NULL CHECK (unit_price >= 0)`, while Pydantic uses a
bounded nonnegative `Decimal`.

SQLite uses dynamic typing, so the type declaration alone is not a full input
validator. The application contract, checks, and tests are all necessary.

## 4. Invalid installation date

The shape query finds `RANDOM-NAME | unknown`. A GLOB can reject that value
but cannot prove a real calendar date such as rejecting 2024-02-30. Pydantic
parses a real `date`; SQLAlchemy binds Python dates. A strict migration should
quarantine or correct `unknown`, not silently invent a date.

## 5. Comma-separated m:n relationship

The naive join returns jobs 2 and 3 but silently loses job 1, whose value is
`P-1001,P-1002`. It also returns job 2 twice because `P-1003` itself is
duplicated. Searching, joining, constraining, and updating individual parts
becomes unreliable. `job_part(job_id, part_no)` restores one value per field;
its foreign keys validate both parents and its composite primary key prevents a
duplicate pair.

## Migration policy

The fixture remains unchanged for audit evidence. A real migration would:

1. quarantine job 3 until `cnc-05` is matched or created by an owner;
2. deduplicate `P-1003` only after confirming the rows represent one part;
3. parse and validate every price and date, sending failures to an exception
   report;
4. split part lists into tokens, trim them, verify each part, and insert one
   junction row per distinct pair;
5. compare row counts and totals before switching applications.
