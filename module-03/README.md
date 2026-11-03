# Module 3 — LLM-Assisted SQL and Query Profiling

This portfolio contains my technical exercises from the current Module 3
workbook and the notes from our classroom Tasks A, B, and C.

## Learning goals and evidence

| Goal | Evidence |
|---|---|
| Complex DQL, joins, grouping/HAVING, subqueries, windows | [Task 1](task1-report.md), [HAVING SQL](having-example.sql), [HAVING results](evidence/having-results.txt), [optional Task 5](task5-window-functions.md) |
| Execution-plan analysis | [raw Task 1 plan](evidence/task1-plan.txt), [benchmark plans](evidence/benchmark-plans.txt), [Plan Safari verification](evidence/plan-safari-prediction-verification.txt), [covering-index scan](evidence/covering-scan-results.txt) |
| Index benchmarking | [benchmark report](task2-benchmark.md), [harness](bench.py) |
| Verify AI SQL | [query source](task1-query.sql), [results](evidence/task1-query-results.txt), [verification JSON](evidence/task1-verification.json) |
| SQL injection prevention | [demonstration](injection_demo.py), [analysis](task3-injection.md) |
| Algebra ↔ SQL ↔ plan | [Task 4](task4-algebra-to-plan.md) |
| Task A — Plan Safari | [my Task A predictions](sql-notes.md#task-a--my-predictions), [classroom records](sql-notes.md), [saved plan verification](evidence/plan-safari-prediction-verification.txt) |
| Task B — algebra check | [classroom notes](sql-notes.md), [formal algebra mapping](task4-algebra-to-plan.md) |
| Task C — neighboring-pod discussion | [classroom discussion notes](sql-notes.md), [Python plan comparison](plan-comparison.py), [fresh comparison output](evidence/plan-comparison-results.txt) |
| Curiosity Swap 1 | [documented first exchange](sql-notes.md#curiosity-swap-1--classroom-discussion) |
| Curiosity Swap 2 | [student-confirmed end-of-class exchange](sql-notes.md#curiosity-swap-2--end-of-class-exchange) |
| Curiosity experiment | [SQL](curiosity-index-experiment.sql), [saved results](evidence/curiosity-index-results.txt) |
| Discord question | [posted Module 3 question](https://discord.com/channels/1064132619735928932/1064145704391561298/1566944448900898859) |
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

| Group member | Workstream |
|---|---|
| Sanjay Pachan Maheshwari | Plan vocabulary |
| Sebastian Emmanuel Soon | SQL clause order |
| Me | Relational algebra ↔ SQL |
| Myo Min Lin | Tuning and security |

I joined Sanjay's pod as a guest member. My part was relational algebra. I
mapped `SELECT * FROM maint_job WHERE technician = 'Beier'` to an algebra
expression and compared it with Gemini. Jomarie was absent from this session.
The links below support our shared classroom work; Sanjay's individual scripts
and portfolio implementation are not presented as my work.

### Shared Classroom Evidence

- [Sanjay's shared SQL notes](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Module03/sql-notes.md) record the pod, workstreams, Tasks A–C, and curiosity questions.
- [Sebastian's Module 3 notes](https://github.com/Emannual20/databases-portfolio/blob/main/Module03/sql-notes.md) provide another record of our pod work and shared exercises.
- [Sanjay's Reflection 03](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Reflections/ref03.md) mentions my SQL-to-algebra contribution.

## Classroom evidence and limitations

Tasks A, B, and C are preserved in [sql-notes.md](sql-notes.md). The Task A
image was reviewed but not published
because it visibly contains another student's identifying filesystem path.
Its commands, results, version, and initial missing-semicolon error are
faithfully transcribed.

I participated in Task A with the group. Sanjay's and Sebastian's notes contain
different predictions for two queries, so both versions are shown. My
personally supplied [Task A predictions](sql-notes.md#task-a--my-predictions)
are also documented and compared with the saved plans. I supplied this text
later during portfolio finalization, so it is not presented as a separately
preserved pre-execution classroom note. Task B records my algebra contribution
and our comparison with Gemini.

I also participated in Task C with a neighboring pod. We compared Windows and
macOS query plans and discussed function-wrapped predicates, leading
wildcards, covering indexes, and an unresolved question about partial searches.
The known Windows screenshot shows SQLite CLI 3.53.4. The macOS SQLite version
and the neighboring pod's complete raw output were not recorded.

I remember our classroom questions about leading wildcards, `UPPER()` on an
indexed column, and covering indexes. We discussed these topics with a
neighboring pod during the first scheduled curiosity exchange, and the original
group notes support that discussion. I also took part in the second exchange at
the end of class, but I did not preserve a separate list of its questions.

The disposable curiosity experiment is technical follow-up, not evidence of a
person-to-person swap. I posted our question about SQLite partial searches and
index usage in the course Discord server:
[My Module 3 Discord question](https://discord.com/channels/1064132619735928932/1064145704391561298/1566944448900898859).
No answer is claimed, and the post is separate from the two peer exchanges.

| Portfolio area | Status |
|---|---|
| Five technical learning goals, Studios 1–4, optional Studio 5 | **VERIFIED** |
| Task A participation and verified plans | **COMPLETE — I participated and the execution plans are verified** |
| My Task A predictions | **COMPLETE — My predictions are documented and compared with the verified query plans** |
| Task B algebra comparison | **COMPLETE — my workstream and Gemini comparison are documented** |
| Task C neighboring-pod discussion | **COMPLETE — Student confirmed and documented** |
| Curiosity Swap 1 | **COMPLETE — Documented and student confirmed** |
| Curiosity Swap 2 | **COMPLETE — Student confirmed; original details not recorded** |
| Person-to-person curiosity exchanges | **COMPLETE — Two separate exchanges confirmed** |
| Technical curiosity SQL experiment | **VERIFIED COMPLETE — Separate technical exercise** |
| Reflection | **COMPLETE** |
| Discord question | **COMPLETE — [Posted and linked](https://discord.com/channels/1064132619735928932/1064145704391561298/1566944448900898859); no answer claimed** |

The technical portfolio, classroom questions, confirmed Tasks A–C, and both
curiosity exchanges are complete. The second exchange is recorded
retrospectively from my confirmation because its original question list was not
preserved. Any instructor-specific approval remains outside the current evidence.
