# Module 6b Reflection — Polyglot Persistence

## Take-away

The technical evidence shows that a database choice is a workload decision, not a universal
ranking. In the measured portfolio, DuckDB fits large analytical scans, while SQLite fits the
constrained operational workflow and the current session-store requirements. JSON is useful
for variable metadata, but `json_valid()` does not replace a business schema. The local
two-writer experiment also makes SQLite's one-writer boundary visible.

**Personal take-away: STUDENT INPUT REQUIRED.** Rewrite or extend this section in your own words
after reviewing the evidence.

## What was good?

Verified technical outcomes include 1,000 valid JSON rows, expression-index plan evidence,
equivalent key-value contents in both backends, and a reproducible lock/retry demonstration.

**Personal observation: STUDENT INPUT REQUIRED.** State what genuinely worked well for you.

## What was difficult?

The main technical trade-off was not simply speed: shelve won the measured individual lookup
loop, whereas SQLite won the batched write by a large margin and offers stronger operational
semantics. Separating a local SQLite simulation from a real shared PostgreSQL observation was
also essential for honest evidence.

**Personal observation: STUDENT INPUT REQUIRED.** Record the part you personally found difficult.

## Exploration and show stoppers

The JSON experiment showed that an indexed `json_extract(...)` expression produced `SEARCH`,
while the logically equivalent `->>` spelling produced `SCAN`. The first Windows verification
also exposed that committing a Python `sqlite3.Connection` context does not close its file
handle; the new scripts now close connections explicitly before replacing or deleting
temporary files.

No PostgreSQL credentials or authenticated classroom connection were available. Therefore the
shared-server observation is intentionally not marked complete.

**Further exploration performed by the student: STUDENT INPUT REQUIRED.**

## Interaction with peers and instructors

**STUDENT INPUT REQUIRED.** Record only the discussion that actually happened: who participated,
what question or criticism was raised, and whether the decision changed. No peer or instructor
interaction is claimed by the generated technical work.

## How did you verify AI suggestions?

The repository contains executable experiments, saved measured output, query-plan evidence,
constraint failures, digest/count equivalence checks, and automated tests. These make the
technical suggestions independently inspectable.

**Student verification process: STUDENT INPUT REQUIRED.** Describe which commands and outputs
you personally reviewed, and any suggestion you rejected or corrected.

## Help and extra work

Technical automation assisted with implementation, tests, evidence capture, and documentation.
Human-only classroom PostgreSQL work, peer defense, project selection, and personal reflection
remain visibly pending.

**Additional help or work: STUDENT INPUT REQUIRED.** Add only genuine assistance or activity.
