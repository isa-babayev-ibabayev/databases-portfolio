# Engine Notes

## Source and evidence boundary

The implementation follows the current raw `main` version of the official
[Module 6b workbook](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/06b-polyglot-persistence.md),
reviewed on 2026-11-17. That revision sets the key-value workload to 20,000 records,
requires JSON query/plan evidence, and distinguishes shared PostgreSQL classroom work from
the local SQLite fallback. An older rendered/cached presentation showed a 50,000-record
variant. The current raw source controls this portfolio evidence.

The workbook labels content after the learning goals as draft. The experiments here are
therefore technical evidence for the stated goals, not a claim that every draft classroom
activity was personally completed.

## Learning-goal audit

| Official learning goal | Evidence | Status |
|---|---|---|
| Compare local embedded and remote/server databases | [concurrency demo](concurrency_demo.py), [saved result](evidence/concurrency-results.txt), server checklist below | **PARTIALLY VERIFIED** — local behavior verified; remote classroom observation pending |
| Store and query semi-structured JSON in a relational database | [JSON experiment](json_bench.py), [output](evidence/json-output.txt), [plans](evidence/json-plans.txt) | **VERIFIED** |
| Compare key-value and relational representations | [benchmark](kv_compare.py), [five-run results](evidence/kv-results.md) | **VERIFIED** for the stated local workload |
| Choose engines from workload and failure consequences | [decision record](decision-record.md) | **VERIFIED** as a technical proposal; personal defense pending |
| Explain polyglot trade-offs using ACID, BASE, and CAP correctly | [learning guide](learning-guide.md), decision boundaries below | **VERIFIED** in documentation; personal oral explanation pending |

## Task 1 — Local versus remote

### Verified local SQLite observation

`concurrency_demo.py` creates a temporary database and opens two independent connections.
Writer 1 begins an immediate transaction and updates a row without committing. Writer 2 has
a 250 ms busy timeout and tries to begin a conflicting write. It received `database is locked`
after 362.23 ms in the recorded run. After writer 1 committed, writer 2 retried successfully;
the final counter was 2. The temporary directory was removed.

This is evidence of a local SQLite write-lock boundary. It is **not** evidence of PostgreSQL
MVCC, shared-server latency, pgweb behavior, user/role isolation, or classroom concurrency.

### Shared PostgreSQL / pgweb checklist — HUMAN REQUIRED

Do not commit credentials. Obtain the authorized values from the LMS or instructor, then:

1. Confirm the authorized **host**, **port**, **database**, **user**, and **SSL mode**.
2. Connect through pgweb only to the supplied classroom database.
3. Record whether two browser tabs use distinct database sessions; tabs may share one session.
4. Create only the permitted temporary classroom object, using an explicit integer primary key.
   PostgreSQL `INTEGER PRIMARY KEY` does not auto-generate values unless identity/sequence
   behavior is declared.
5. In session A, begin a transaction and update the target row without committing.
6. In a genuinely separate session B, run the instructor-approved conflicting statement.
7. Record waiting, visibility, error, and post-commit behavior without including credentials.
8. Roll back or remove the authorized temporary object as instructed.

| Required classroom observation | Actual observation |
|---|---|
| What was easier on the shared server? | **STUDENT INPUT REQUIRED** |
| What was harder? | **STUDENT INPUT REQUIRED** |
| What new failure mode appeared? | **STUDENT INPUT REQUIRED** |
| Did the two pgweb tabs represent different sessions? | **STUDENT INPUT REQUIRED** |
| How did uncommitted data appear to the other session? | **STUDENT INPUT REQUIRED** |

## Task 2 — JSON in SQLite

The generated table is `STRICT` and keeps the flexible object in a TEXT column guarded by
`CHECK(json_valid(meta))`. The 1,000 deterministic rows contain three named examples and
997 generated rows with varying optional fields.

Verified outcomes:

- 1,000 rows and 1,000 values satisfying `json_valid`.
- `json_extract` returned the first five vendor fields; `->>` returned the first five firmware
  values; `json_each` expanded the complete `cnc-01` metadata object.
- malformed JSON was rejected by the check.
- a different valid object shape was accepted and a missing optional path returned SQL `NULL`.
- STRICT typing rejected a BLOB stored in the TEXT column.
- the exact indexed expression produced `SEARCH ... USING INDEX ix_device_vendor`.
- an equivalent `meta ->> 'vendor'` predicate produced `SCAN device`.

The conclusion is deliberately narrow: JSON reduces migration pressure for optional vendor
metadata, but stable identifiers, required facts, referential relationships, money, and other
strongly governed values should remain relational or gain explicit validation.

## Task 3 — Decision and defense

The [decision record](decision-record.md) uses measured portfolio evidence for five workload
boundaries. It proposes SQLite for operational truth, JSON metadata, and current sessions;
DuckDB/Parquet for analytical snapshots; and PostgreSQL only after an authenticated concurrent
server requirement is verified.

Likely defense questions and technical answers:

- **Why not put everything in DuckDB?** The two-million-row scans justify DuckDB, but the
  Module 4 ingestion path already verifies foreign keys, conditional UPSERT, atomic rollback,
  and idempotent natural keys in SQLite.
- **Why not put all metadata in JSON?** JSON syntax validation does not guarantee required keys,
  types at each path, uniqueness, or referential integrity.
- **Why SQLite rather than shelve for sessions?** Shelve won the measured lookup loop, but
  SQLite won the write workload and gives transactions, SQL inspection, and clearer integrity
  and concurrency semantics.
- **Why not PostgreSQL immediately?** A server adds valuable multi-user capabilities and
  substantial operational cost. This repository has no authenticated load evidence showing
  that the current local workload needs it.

**Actual peer question, feedback, and decision change: STUDENT INPUT REQUIRED.**

## Homework status

- Key-value benchmark: **VERIFIED**, five fresh trials at 20,000 records.
- Project ticket: three reproducible candidates prepared; **final selection HUMAN REQUIRED**.
- Reflection: technical facts structured; **personal writing HUMAN REQUIRED**.

## ACID, BASE, and CAP boundary notes

- **ACID** describes transaction properties: atomicity, consistency with declared rules,
  isolation, and durability. It does not promise that business rules were modeled correctly.
- **BASE** is an architectural tendency toward availability and eventual convergence in some
  distributed systems; it is not the opposite of all transactions and is not a database type.
- **CAP** applies when a distributed system experiences a network partition: it cannot both
  guarantee linearizable consistency and every request's availability during that partition.
  “Pick any two” is an unsafe slogan because partitions are not an optional steady-state
  feature, and systems make choices per operation and failure mode.
- A single local SQLite file is not meaningfully classified as CP or AP without a distributed
  partition model. The same caution applies to an unspecified single PostgreSQL server.
