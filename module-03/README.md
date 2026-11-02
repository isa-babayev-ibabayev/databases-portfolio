# Module 3 — LLM-Assisted SQL and Query Profiling

This portfolio implements the technical exercises from the current Module 3
workbook while preserving the student-supplied classroom Tasks A, B, and C.

## Learning goals and evidence

| Goal | Evidence |
|---|---|
| Complex DQL, joins, grouping/HAVING, subqueries, windows | [Task 1](task1-report.md), [HAVING SQL](having-example.sql), [HAVING results](evidence/having-results.txt), [optional Task 5](task5-window-functions.md) |
| Execution-plan analysis | [raw Task 1 plan](evidence/task1-plan.txt), [benchmark plans](evidence/benchmark-plans.txt), [Plan Safari verification](evidence/plan-safari-prediction-verification.txt), [covering-index scan](evidence/covering-scan-results.txt) |
| Index benchmarking | [benchmark report](task2-benchmark.md), [harness](bench.py) |
| Verify AI SQL | [query source](task1-query.sql), [results](evidence/task1-query-results.txt), [verification JSON](evidence/task1-verification.json) |
| SQL injection prevention | [demonstration](injection_demo.py), [analysis](task3-injection.md) |
| Algebra ↔ SQL ↔ plan | [Task 4](task4-algebra-to-plan.md) |
| Task A — Plan Safari | [classroom notes and predictions](sql-notes.md), [fresh plan verification](evidence/plan-safari-prediction-verification.txt) |
| Task B — algebra check | [classroom notes](sql-notes.md), [formal algebra mapping](task4-algebra-to-plan.md) |
| Task C — neighboring-pod discussion | [student discussion notes](sql-notes.md), [Python plan comparison](plan-comparison.py), [fresh comparison output](evidence/plan-comparison-results.txt) |
| Curiosity experiment | [SQL](curiosity-index-experiment.sql), [saved results](evidence/curiosity-index-results.txt) |
| Reflection | [ref03.md](../Reflections/ref03.md) |
| Automated verification | [tests](tests/test_module03.py), [saved results](evidence/test-results.txt) |
| Independent audit | [technical completion report](technical-completion-report.md) |

## Setup and reproduction

Run from the repository root in PowerShell:

```powershell
uv sync
sqlite3 module-03/warehouse.db ".read module-03/setup.sql"
sqlite3 module-03/warehouse.db ".read module-03/having-example.sql"
uv run python module-03/collect_evidence.py
uv run python module-03/reproduce_classroom_plans.py
uv run python module-03/plan-comparison.py
sqlite3 :memory: ".read module-03/curiosity-index-experiment.sql"
sqlite3 :memory: ".read module-03/covering-scan-demo.sql"
uv run python module-03/bench.py --repeats 5 --batch-iterations 100
uv run python module-03/injection_demo.py --output module-03/evidence/injection-output.txt
uv run python -m unittest discover -s module-03/tests -v
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
- A forced full traversal of a one-column index produced
  `SCAN t USING COVERING INDEX i`: it is a scan because no rows are filtered,
  and covering because the requested value is available in the index.
- The corrected relational-algebra expression maps the same city report to
  selection, projection, joins, grouping, aggregation, and sorting.

## Automated verification

The current suite ran **23 tests; all 23 passed**. It checks the fixture,
dashboard boundaries and edge cases, benchmark samples and medians, injection
behavior and source-database isolation, optional query equivalence, the HAVING
result and plan, both disposable index experiments, documentation links, and
control characters. The saved output is in
[evidence/test-results.txt](evidence/test-results.txt).

## Classroom Collaboration — Module 3

The shared classroom record identifies this pod and division of work:

| Student | Documented workstream |
|---|---|
| Sanjay Pachan Maheshwari | Plan vocabulary |
| Sebastian Emmanuel Soon | SQL clause order |
| İsa Babayev | Relational algebra ↔ SQL |
| Myo Min Lin | Tuning and security |

İsa joined the pod as a guest member. His documented contribution was the
algebra mapping for `SELECT * FROM maint_job WHERE technician = 'Beier'` and
the comparison of that expression with Gemini. Jomarie was recorded absent.
These are shared-classroom contributions; Sanjay's individual scripts and
portfolio implementation are not presented as İsa's work.

### Shared Classroom Evidence

- [Sanjay's shared SQL notes](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Module03/sql-notes.md) record the pod, workstreams, Tasks A–C, and curiosity questions.
- [Sebastian's Module 3 notes](https://github.com/Emannual20/databases-portfolio/blob/main/Module03/sql-notes.md) independently corroborate the pod work and shared exercises.
- [Sanjay's Reflection 03](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Reflections/ref03.md) credits İsa's SQL-to-algebra contribution.

## Classroom evidence and limitations

Tasks A, B, and C are preserved in [sql-notes.md](sql-notes.md) as
student-provided evidence. The Task A image was reviewed but not published
because it visibly contains another student's identifying filesystem path.
Its commands, results, version, and initial missing-semicolon error are
faithfully transcribed.

Sanjay's and Sebastian's Task A records disagree on two original predictions,
and no individual prediction for İsa was preserved. The notes show both
records and compare them with the disposable reproduction. Task B is supported
by all three portfolios and identifies İsa's algebra contribution.

The pod's shared notes document a Task C exchange with a neighboring group:
Windows and macOS plans matched, and the groups discussed function-wrapped
predicates, leading wildcards, covering indexes, and a question for Discord.
The known Windows screenshot shows SQLite CLI 3.53.4; the macOS SQLite version
was not recorded. The shared notes establish the pod-level event, but they do
not independently establish that İsa personally remained for the whole
neighboring-pod segment. No stronger personal claim is made.

A second curiosity is now demonstrated through a disposable technical
experiment, but it is not misrepresented as a second historical
person-to-person swap. The workbook's Discord step is conditional on a shared
or unresolved curiosity after the exchanges; no Discord post is claimed.

| Portfolio area | Status |
|---|---|
| Five technical learning goals, Studios 1–4, optional Studio 5 | **VERIFIED** |
| Task A group predictions and verified plans | **DOCUMENTED IN SHARED NOTES; records conflict; plans technically verified** |
| İsa's individual Task A prediction | **PERSONAL CONFIRMATION NEEDED; not preserved** |
| Task B algebra comparison | **DOCUMENTED IN SHARED NOTES AND EXTERNALLY CORROBORATED** |
| Task C neighboring-pod exchange | **DOCUMENTED AT POD LEVEL; İsa's full personal attendance not independently verified** |
| Second curiosity technical exercise | **VERIFIED** |
| First curiosity swap | **POD NOTES RECORD QUESTIONS; person-to-person exchange not independently verified** |
| Second curiosity swap | **EXAMPLES PREPARED; real peer activity still required** |
| Reflection | **VERIFIED AS DOCUMENTED** |
| Discord follow-up | **NOT CLAIMED / CONDITIONAL** |

The technically achievable portfolio work is complete. Personal confirmation,
a real second peer swap, any genuine Discord link, and instructor-specific
approval remain external requirements.
