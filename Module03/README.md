# Module 3 — LLM-Assisted SQL and Query Profiling

This portfolio implements the technical exercises from the current Module 3
workbook while preserving the student-supplied classroom Tasks A, B, and C.

## Learning goals and evidence

| Goal | Evidence |
|---|---|
| Complex DQL, joins, grouping/HAVING, subqueries, windows | [Task 1](task1-report.md), [HAVING SQL](having-example.sql), [HAVING results](evidence/having-results.txt), [optional Task 5](task5-window-functions.md) |
| Execution-plan analysis | [raw Task 1 plan](evidence/task1-plan.txt), [benchmark plans](evidence/benchmark-plans.txt) |
| Index benchmarking | [benchmark report](task2-benchmark.md), [harness](bench.py) |
| Verify AI SQL | [query source](task1-query.sql), [results](evidence/task1-query-results.txt), [verification JSON](evidence/task1-verification.json) |
| SQL injection prevention | [demonstration](injection_demo.py), [analysis](task3-injection.md) |
| Algebra ↔ SQL ↔ plan | [Task 4](task4-algebra-to-plan.md) |
| Classroom and curiosity notes | [sql-notes.md](sql-notes.md) |
| Reflection | [ref03.md](../Reflections/ref03.md) |
| Automated verification | [tests](tests/test_module03.py), [saved results](evidence/test-results.txt) |
| Independent audit | [technical completion report](technical-completion-report.md) |

## Setup and reproduction

Run from the repository root in PowerShell:

```powershell
uv sync
sqlite3 Module03/warehouse.db ".read Module03/setup.sql"
sqlite3 Module03/warehouse.db ".read Module03/having-example.sql"
uv run python Module03/collect_evidence.py
uv run python Module03/reproduce_classroom_plans.py
uv run python Module03/bench.py --repeats 5 --batch-iterations 100
uv run python Module03/injection_demo.py --output Module03/evidence/injection-output.txt
uv run python -m unittest discover -s Module03/tests -v
```

`warehouse.db`, journals, WAL/SHM files, caches, and benchmark databases are
ignored. The scripts use repository-relative paths.

## Warehouse fixture

Expected and verified counts:

| Table | Rows |
|---|---:|
| customer | 2,000 |
| product | 500 |
| orders | 60,000 |
| order_line | 240,000 |

Important setup constructs:

1. `WITH RECURSIVE` builds an integer sequence without a source table.
2. `INSERT INTO ... SELECT` inserts every row returned by the query; a
   zero-row result inserts nothing.
3. `(x % 2000) + 1` cycles IDs from 1 to 2000 but does not enforce that those
   customers exist. The Module 3 fixture intentionally has no Module 4 FKs.
4. The date modifier is built as text because SQLite's `date()` accepts
   modifier strings. For `x=540`, the remainder is zero, so the result is
   2025-01-01.
5. `printf('%05d', x)` produces SKUs such as `SKU-00001`, preserving useful
   lexical order and a consistent display width.

Dependent tables are dropped first so the order remains safe when later
versions introduce foreign keys. Re-running setup deliberately recreates this
generated fixture, so use a disposable database when preserving other work.

## Main technical findings

- The correct city report returned four ordered groups and matched an
  independent Python calculation.
- The executable `HAVING` query returned 400 customer groups; every group had
  exactly 30 late orders in the deterministic fixture.
- The baseline dashboard plan begins with `SCAN order_line`.
- A date index helped a selective day lookup but was ignored by the dashboard.
- A join index changed the dashboard plan and made it almost nine times slower.
- Bound parameters treated the injection payload as data.
- The optional three late-order query forms were result-equivalent, but the
  correlated form was far slower.
- The corrected relational-algebra expression maps the same city report to
  selection, projection, joins, grouping, aggregation, and sorting.

## Automated verification

The current suite ran **19 tests; all 19 passed**. It checks the fixture,
dashboard boundaries and edge cases, benchmark samples and medians, injection
behavior, optional query
equivalence, the HAVING result and plan, documentation links, and control
characters. The saved output is in
[evidence/test-results.txt](evidence/test-results.txt).

## Classroom evidence and limitations

Tasks A, B, and C are preserved in [sql-notes.md](sql-notes.md) as
student-provided evidence. The Task A image was reviewed but not published
because it visibly contains another student's identifying filesystem path.
Its commands, results, version, and initial missing-semicolon error are
faithfully transcribed.

The original Task A predictions were not recorded. A new, explicitly dated
AI-assisted prediction-and-verification exercise demonstrates the technical
behavior without pretending to be the missing classroom history. Task B has a
documented student explanation and AI comparison. Task C remains
student-reported because the neighboring pod's raw plan and SQLite version are
not available. A second curiosity swap and Discord post are not claimed.

The technically achievable portfolio work is complete. Any requirement for
new neighboring-pod participation, raw external evidence, or instructor
approval remains a genuine human/external dependency.
