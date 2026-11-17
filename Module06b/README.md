# Module 6b — Polyglot Persistence & the Decision

This module compares relational, JSON, key-value, analytical, embedded, and server-oriented
boundaries using reproducible evidence. Its conclusion is not “more databases are better.” The
goal is to choose the minimum architecture that fits each workload and its failure consequences.

**Official workbook:** [Module 6b — Polyglot Persistence](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/06b-polyglot-persistence.md)

**Workbook revision reviewed:** current raw `main`, 2026-11-17

**Draft boundary:** the workbook marks the material after its learning goals as draft; completion
claims below distinguish executable evidence from human-only classroom work.

## Learning Goals — Verification Evidence

| Learning goal | Verification evidence | Status |
|---|---|---|
| 1. Store **semi-structured data (JSON)** in SQLite and query it with `json_extract`/`json_each` and an **expression index**. | [json_bench.py](json_bench.py), [json-output.txt](evidence/json-output.txt), [json-plans.txt](evidence/json-plans.txt), [json-constraint-tests.txt](evidence/json-constraint-tests.txt) | **VERIFIED** |
| 2. Implement and evaluate a **key-value access pattern** against SQLite. | [kv_compare.py](kv_compare.py), [kv-results.md](evidence/kv-results.md) | **VERIFIED** for 20,000 local session pairs over five trials |
| 3. Explain **ACID vs. BASE** and the **CAP theorem** in terms of the systems actually run. | [learning-guide.md](learning-guide.md), [engine-notes.md](engine-notes.md), [concurrency-results.txt](evidence/concurrency-results.txt) | **VERIFIED** in written technical evidence; personal oral explanation pending |
| 4. Choose an engine per workload and **defend the choice with a measurement**. | [decision-record.md](decision-record.md), [project-ticket.md](project-ticket.md) | **VERIFIED** as a technical proposal; final personal defense/selection pending |
| 5. Say what changes—and what gets harder—when the same data lives on a **server**. | [engine-notes.md](engine-notes.md), [concurrency_demo.py](concurrency_demo.py), [concurrency-results.txt](evidence/concurrency-results.txt) | **PARTIALLY VERIFIED** — local fallback verified; authenticated PostgreSQL/pgweb observation is human-required |

## Headline Results

### JSON in SQLite

- Exactly **1,000** rows; all 1,000 passed `json_valid`.
- Invalid JSON and a BLOB in the STRICT TEXT column were rejected.
- Different valid object shapes were accepted; a missing optional path returned SQL `NULL`.
- The required `->>` query returned the first five firmware values; `json_each` expanded the
  complete `cnc-01` object into vendor, firmware, and calibrated key/value rows.
- Exact `json_extract(meta, '$.vendor')` predicate: `SEARCH ... USING INDEX`.
- Equivalent `meta ->> 'vendor'` predicate: `SCAN device`.
- Both predicates returned the same 334 Fanuc rows.

### Key-value comparison

| Backend | Median write, 20,000 pairs | Median 20,000 individual lookups |
|---|---:|---:|
| shelve | 13,381.62 ms | 235.54 ms |
| SQLite | 46.02 ms | 1,375.72 ms |

Five fresh, alternated trials were used. Counts were 20,000 and ordered value digests matched
for every trial. SQLite won the batched write; shelve won the Python lookup loop. The proposed
session-store choice remains SQLite because transactions, inspection, constraints, and a clearer
concurrency path matter here. This conclusion is specific to the measured workload.

### Local concurrency

Two independent SQLite connections produced a controlled `database is locked` outcome while
the first writer held `BEGIN IMMEDIATE`. After that writer committed, the retry succeeded and
the final counter was 2. This is local fallback evidence, **not a PostgreSQL result**.

### Portfolio architecture decision

- SQLite: authoritative operational ingestion, constrained device identity/JSON, current sessions.
- Parquet + DuckDB: rebuildable analytical snapshot and large scans.
- PostgreSQL: conditional future choice for verified multi-user server requirements.

The [decision record](decision-record.md) uses the student's existing Module 4 and Module 6a
measurements, records accepted costs, and states what fails when each representation is stale or
missing.

## Reproduce the Evidence

Run commands from the repository root.

```powershell
uv sync
uv run python -B Module06b/json_bench.py --rebuild
uv run python -B Module06b/kv_compare.py --n 20000 --runs 5 --json
uv run python -B Module06b/concurrency_demo.py
uv run python -B -m unittest discover -s Module06b/tests -v
```

### Mutation and recovery notes

- `json_bench.py` creates generated `Module06b/polyglot.db`. Without `--rebuild`, it validates
  and reuses a correct file. With `--rebuild`, it constructs and validates a temporary sibling
  before atomic replacement. The generated database is ignored by Git.
- `kv_compare.py` uses a fresh operating-system temporary directory for every backend/trial and
  removes it after the handles close. It does not write benchmark stores into the repository.
- `concurrency_demo.py` uses and removes a disposable temporary database.
- The tests use temporary fixtures and do not modify the portfolio evidence.
- If a generated JSON database is interrupted or invalid, rerun with `--rebuild`; the committed
  scripts and evidence remain the reproducible source.

## Evidence Inventory

| File | Purpose |
|---|---|
| [pre-session-audit.txt](evidence/pre-session-audit.txt) | Repository, environment, workbook, and evidence-boundary audit |
| [json-output.txt](evidence/json-output.txt) | Saved JSON query and constraint result summary |
| [json-plans.txt](evidence/json-plans.txt) | Exact indexed expression versus shorthand scan |
| [json-constraint-tests.txt](evidence/json-constraint-tests.txt) | Positive and negative JSON/STRICT outcomes |
| [kv-results.md](evidence/kv-results.md) | Five-trial samples, medians, equivalence digest, and limitations |
| [concurrency-results.txt](evidence/concurrency-results.txt) | Controlled local two-writer outcome |
| [test-results.txt](evidence/test-results.txt) | Automated verification output |
| [tests/test_module06b.py](tests/test_module06b.py) | Assertions for data, plans, equivalence, cleanup, locking, and docs |

## Human-Required Completion Boundary

The following items are intentionally not claimed as completed:

- authenticated shared PostgreSQL/pgweb observation using LMS/instructor credentials;
- confirmation that two pgweb tabs represent distinct server sessions;
- real peer or instructor defense and any resulting decision change;
- final project-ticket selection with a real person/problem;
- personal reflection wording and personal verification account.

The exact classroom checklist and blank observation fields are in
[engine-notes.md](engine-notes.md). The reflection template is
[Reflections/ref06b.md](../Reflections/ref06b.md). Credentials, invented observations, and
fabricated peer activity do not belong in this repository.

## Independent Verification Notes

The initial implementation audit found no earlier Module 6b folder. `Module06a` was preserved;
on Windows, `Module06A` resolves to that same directory rather than a second copy. The unrelated
untracked root `main.py` predates this work and remains untouched. Full details are saved in the
[pre-session audit](evidence/pre-session-audit.txt).
