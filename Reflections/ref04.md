# Reflection 04 — Data integrity at the edge

> Draft based on the reproducible Module 4 evidence. The peer-interaction
> paragraph is intentionally left for personal confirmation before submission.

## Take-away

My main takeaway is that data integrity is not one constraint or one test. A
reliable database combines keys, foreign keys, mandatory fields, domain rules,
transactions, and application-side validation. The negative tests made these
roles easier to distinguish because each rejected input showed which rule was
responsible. I also learned that SQLite features such as `STRICT`, triggers,
UPSERT, and read-only mode are useful but have specific boundaries.

## What was good?

The strongest part of the module is its reproducibility. The unconstrained
table visibly accepts bad data, while the constrained version reports concrete
errors and continues with the remaining cases. Importing the same four-row CSV
twice leaves four readings and no duplicate natural keys. The invalid batch
also demonstrates transaction behavior: the foreign-key error rolls back the
valid row that appeared earlier in that batch.

## What was difficult?

The most subtle issue was the interaction between UPSERT and triggers. When an
UPSERT takes its UPDATE branch, the audit trigger runs, but the required
INSERT-only alarm trigger does not. The tests therefore show that a vibration
value can cross from 1.0 to 3.0 without creating an alarm. Another surprising
detail was that `STRICT` accepts numeric text such as `42.5` when SQLite can
convert it without loss, although it correctly rejects `hot` for a REAL column.

## Exploration and show stoppers

The generated-column experiment verified both the calculation and the fact
that callers cannot assign the generated value directly. Its name `energy_j`
also led to an important modeling limitation: multiplying value by seconds has
energy units only when the value is power, not when it is temperature or
vibration. The performance exploration inserted 10,000 identical deterministic
inputs in each scenario. The median changed from 0.009106 seconds without the
alarm trigger to 0.027644 seconds with it, with 5,000 additional alarm rows;
these measurements apply only to the recorded environment.

## Interaction with peers and instructors

The neighboring-pod material in `integrity-notes.md` is an illustrative
technical comparison, not a record of a real conversation. I still need to
replace or confirm this paragraph with my actual Module 4 classroom exchange,
including only details I genuinely remember or recorded. No group number,
student name, date, quotation, or Discord activity has been invented.

## How did you verify AI suggestions?

AI-assisted explanations were converted into testable claims. Separate tables
checked whether CHECK accepts NULL, and `typeof()` checked how numeric text is
stored in a STRICT REAL column. Trigger tests covered the exact threshold,
wrong metric, rollback, no-op updates, and threshold-crossing UPSERTs. The
ingestion ran twice and then processed a failing fixture, while the access test
attempted real DELETE statements through both URI read-only mode and
`query_only`. Finally, 34 isolated automated tests passed and both
`foreign_key_check` and `integrity_check` reported a consistent database.

## Help and extra work

The optional trigger-timing exercise added a BEFORE trigger that rejects a
negative value, an AFTER trigger that logs only successful inserts, and an
INSTEAD OF trigger that routes a view insert to a real table. I also compared
SQLite's file and connection controls with PostgreSQL roles and `GRANT`.
Windows ACLs were inspected with `icacls`, but no permissions were modified, so
I do not claim an OS-level denial experiment that was not performed.
