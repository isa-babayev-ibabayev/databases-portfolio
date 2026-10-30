# Module 3 SQL notes

## 1. Module purpose

Module 3 connects complex SQL, relational algebra, query plans, measured index
behavior, AI verification, and parameter binding. Technical reproduction is
kept separate from student-reported classroom Tasks A, B, and C.

## 2. Learning references

| Reference | Use in this work |
|---|---|
| [Professor's Module 3 workbook](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/03-llm-assisted-sql-and-query-profiling.md) | Primary specification, fixture, queries, and exercise sequence |
| [SQLite EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html) | Meanings of `SCAN`, `SEARCH`, and temporary B-trees |
| [SQLite query planner](https://www.sqlite.org/queryplanner.html) | Index selection and covering indexes |
| [SQLite expression indexes](https://www.sqlite.org/expridx.html) | Why an expression index must match the query expression |
| [SQLite LIKE optimization](https://www.sqlite.org/optoverview.html#the_like_optimization) | Conditions for prefix `LIKE` optimization |
| [SQLite FTS5 trigram tokenizer](https://www.sqlite.org/fts5.html#the_trigram_tokenizer) | Indexed substring matching and short-token limits |
| [Relational algebra](https://en.wikipedia.org/wiki/Relational_algebra) | Selection, projection, joins, and extended grouping notation |
| [SQLite plan operations](https://use-the-index-luke.com/sql/explain-plan/sqlite/operations) | Independent plan glossary |
| [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html) | Parameterized queries and manual-escaping risks |
| [Python sqlite3](https://docs.python.org/3/library/sqlite3.html) | Placeholder and parameter-binding API |

These sources support the technical implementation. This list does not claim
that the student personally read every source during one classroom session.

## 3. Workstream 1 — algebra ↔ SQL

| Algebra | SQL | Purpose |
|---|---|---|
| Selection `σ` | `WHERE` | Filter rows |
| Projection `π` | `SELECT` list | Choose output columns |
| Join `⋈` | `JOIN ... ON` | Combine related relations |
| Grouping `γ` | `GROUP BY` plus aggregates | Calculate values per group |
| Rename `ρ` | `AS` | Name relations or calculated values |

The complete city-revenue translation is in
[task4-algebra-to-plan.md](task4-algebra-to-plan.md). SQL preserves duplicate
rows unless `DISTINCT` or grouping changes them, while classical relational
algebra normally uses sets. That is why `COUNT(DISTINCT customer_id)` matters
after Orders is joined to OrderLine.

## 4. Workstream 2 — clause order and HAVING

Written order:

`SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY`

Logical evaluation order:

`FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY`

This query is wrong because `WHERE` runs before the groups and their counts
exist:

```sql
SELECT city, COUNT(*) AS n
FROM customer
WHERE COUNT(*) > 10
GROUP BY city;
```

An aggregate condition belongs in `HAVING`. The executable
[HAVING exercise](having-example.sql) filters individual Orders rows with
`WHERE status = 'late'`, creates one group per customer, and then keeps groups
with `HAVING COUNT(*) > 20`. The verified output contains 400 customers with
30 late orders each. See [having-results.txt](evidence/having-results.txt).

## 5. Workstream 3 — query-plan vocabulary

- `SCAN table`: visit every row, possibly in index order. A scan is reasonable
  when most rows are needed or the table is small.
- `SEARCH table USING INDEX`: use an index to select rows, then visit the table
  for columns not stored in the index.
- `SEARCH ... USING COVERING INDEX`: obtain every required value from the
  index without a separate table lookup.
- `USE TEMP B-TREE`: build temporary storage for sorting, grouping, or distinct
  processing when no existing index supplies the required order.

Plan lines are a loop order: the first table is the outer loop. Plans can
change with data size, statistics, indexes, and SQLite version.

## 6. Workstream 4 — tuning and security

An index helps a particular access pattern, not every query. The recorded
dashboard became about 8.9 times slower after an index changed its loop order,
while the date index made a selective one-day lookup about 12.9 times faster.

SQL values must be bound with placeholders. The local payload returned all
rows through the intentionally vulnerable string-built query and zero rows
through the safe parameterized query. See [Task 3](task3-injection.md).

## 7. Classroom Task A — preserved historical evidence

The supplied classroom screenshot was inspected at
`Desktop/IMG-20261022-WA0019(1).jpg`. It is not published because it visibly
contains another student's filesystem path. It shows SQLite CLI 3.53.4 and
these after-index plans:

```text
technician equality: SEARCH maint_job USING INDEX ix_job_tech (technician=?)
machine-name equality: SCAN machine
leading-wildcard technician: SCAN maint_job
```

It also records an initial missing-semicolon error while entering
`CREATE INDEX`. It does not establish a clean before-index baseline and does
not contain the original pre-execution predictions. Those historical
predictions cannot be recovered word for word.

### Student recollection and reconstructed explanation

I participated in this classroom activity with students from another group
and remember making predictions before running the queries. I did not preserve
the exact wording of those predictions, the other group's number, or the
participants' names. The following is therefore an **illustrative
reconstruction of the reasoning, not a contemporaneous transcript**:

| Query | Reconstructed expectation | Screenshot observation |
|---|---|---|
| `technician = 'Beier'` | An equality predicate can use a matching technician index | `SEARCH maint_job USING INDEX ix_job_tech` |
| `machine_name = 'cnc-02'` | A technician index cannot help a query on Machine | `SCAN machine` |
| `technician LIKE '%ei%'` | A leading wildcard gives an ordinary B-tree no fixed prefix | `SCAN maint_job` |

The screenshot supports the displayed observations, while the recollection of
making predictions is student-reported. The clean, independently reproducible
before/after exercise below supplies technical evidence without replacing the
missing historical record.

## 8. New AI-assisted Plan Safari prediction and verification

This is a new technical exercise dated **2026-10-30**. The predictions were
made by the AI-assisted development process before this fresh execution. They
are not attributed to the student and are not presented as the missing
classroom predictions.

| Query | Prediction before fresh run | Observed before index | Observed after `ix_job_tech` |
|---|---|---|---|
| `technician = 'Beier'` | SCAN before; selective SEARCH after | `SCAN maint_job` | `SEARCH maint_job USING INDEX ix_job_tech` |
| `machine_name = 'cnc-02'` | SCAN both times because the new index belongs to another table | `SCAN machine` | `SCAN machine` |
| `technician LIKE '%ei%'` | SCAN both times because the pattern has no fixed prefix | `SCAN maint_job` | `SCAN maint_job` |
| `upper(technician)=upper('Beier')` | Ordinary technician index will not match the expression | Not part of the baseline three | `SCAN maint_job` |

All predictions matched the clean disposable reproduction. Raw output:
[plan-safari-prediction-verification.txt](evidence/plan-safari-prediction-verification.txt).

The technician equality can use the index because it searches the indexed
column for one value. The Machine query is unrelated to that index. A leading
wildcard has no starting prefix for an ordinary B-tree range search. A
function-wrapped column needs a matching expression index. None of these scans
is automatically a mistake, especially in the four-row classroom fixture.

### Task A — Additional Plan Safari Practice

I practiced reading SQLite query plans using the Module 2 maintenance database.

**Runtime distinction:** the preserved classroom screenshot displays SQLite
3.53.4. The clean disposable reproduction linked above used Python's SQLite
3.50.4. These are separate executions and are not merged into one record.

I used `EXPLAIN QUERY PLAN` before and after creating the index `ix_job_tech`.

| Query                         | Before index   | After index                              |
| ----------------------------- | -------------- | ---------------------------------------- |
| `technician = 'Beier'`        | SCAN maint_job | SEARCH maint_job USING INDEX ix_job_tech |
| `machine_name = 'cnc-02'`     | SCAN machine   | SCAN machine                             |
| `technician LIKE '%ei%'`      | SCAN maint_job | SCAN maint_job                           |
| `UPPER(technician) = 'BEIER'` | Not tested     | SCAN maint_job                           |

**What I learned from the results:**

An index can help SQLite search for a specific value. However, it does not help every query. The machine-name query used a different column, so the technician index did not help.

The query with `LIKE '%ei%'` still used SCAN because the pattern starts with a wildcard. The `UPPER(technician)` query also used SCAN because the ordinary index was not created on that expression.

This was an additional practice exercise. My original classroom predictions were not recorded before the first execution, so these results are not presented as historical predictions.

## 9. Classroom Task B — algebra comparison

The student-provided explanation selected:

```sql
SELECT * FROM maint_job WHERE technician = 'Beier';
```

Its relational algebra is:

`σ_{technician='Beier'}(maint_job)`

The preserved Gemini comparison agreed on selection `σ`. Projection `π` can
be omitted because `SELECT *` keeps all attributes, and no join belongs in
this expression.

## 10. Classroom Task C — neighboring-pod exchange and limits

I participated in the classroom discussion with students from another group.
The student-provided notes report that a Windows plan matched the other
group's macOS equality-search plan. They also report discussion of
function-wrapped columns, leading wildcards, and covering indexes, followed by
one curiosity exchange.

The other group's number, participant names, raw plan, SQLite version, and a
second person-to-person curiosity swap are not available. Therefore, the
participation and cross-platform comparison are **student-reported and not
independently corroborated**. No missing name, version, output, or transcript
has been invented.

### Illustrative exchange reconstruction — not a verbatim transcript

The following dialogue is a teaching reconstruction of the reported topics:

- **Question:** Why can the equality query become `SEARCH`? **Explanation:** A
  matching equality constraint can probe `ix_job_tech` directly.
- **Question:** Why does `LIKE '%ei%'` remain a scan? **Explanation:** The
  leading wildcard removes the fixed prefix needed for the usual B-tree range
  optimization.
- **Question:** Why can `upper(technician)` remain a scan? **Explanation:** The
  expression does not match an ordinary index on the raw column.
- **Question:** When is an index covering? **Explanation:** When it contains
  every column needed by that query, avoiding a table lookup.

These questions and answers demonstrate the technical comparison; they are
not claimed as exact words spoken by either group.

Technical research suggests matching `COLLATE NOCASE` indexes for compatible
case-insensitive prefix/equality searches, expression indexes for matching
expressions such as `lower(column)`, and FTS5 trigram indexes for suitable
substring searches. The classroom pattern `%ei%` is too short for the usual
three-character trigram advantage.

## 11. Independently reproduced technical checks

- Warehouse counts: Customer 2,000; Product 500; Orders 60,000; OrderLine
  240,000.
- Plan Safari: only technician equality changed from SCAN to SEARCH after its
  index was added.
- HAVING exercise: 400 qualifying customers, each with 30 late orders.
- Dashboard: four cities; independent Python aggregation matched the SQL.
- Baseline dashboard plan: OrderLine scan, three primary-key searches, and
  three temporary B-trees.
- Date index ignored by the dashboard but used by the one-day lookup.
- OrderLine join index changed the dashboard plan and made it much slower.
- Product index unused by the dashboard but useful for a direct product filter.
- Parameter binding neutralized the injection payload.
- Grouped, correlated, and window late-order queries returned identical rows.

## 12. Curiosities and sources

- `upper(technician)` can defeat an ordinary index — Task A notes and
  [SQLite expression indexes](https://www.sqlite.org/expridx.html).
- `LIKE '%ei%'` scans despite a technician index — Task A evidence and
  [LIKE optimization](https://www.sqlite.org/optoverview.html#the_like_optimization).
- Adding an output column can make a covering index non-covering — benchmark
  plans and the [SQLite query planner](https://www.sqlite.org/queryplanner.html#covering_indexes).
- The dashboard uses three temporary B-trees —
  [raw plan](evidence/task1-plan.txt).
- An added index changed the plan and made an aggregate nearly nine times
  slower — [benchmark evidence](task2-benchmark.md).
- An SQL query can run but count joined lines rather than customers if
  `DISTINCT` is omitted — [edge-case tests](tests/test_module03.py).
- Relational algebra describes meaning while a query plan describes a physical
  strategy — [Task 4](task4-algebra-to-plan.md).

The record supports one student-reported classroom collection swap. The
workbook asks for another swap at the end, but no second historical swap is
claimed.

### Curiosity Exchange 2 — When Indexes Do Not Help

**Status:** independently reproducible technical follow-up, not a claim of a
second person-to-person classroom exchange.

**Question:** Will an ordinary index on `technician` help both an equality
predicate and `LIKE '%ei%'`?

**Prediction:** equality should change from `SCAN` to `SEARCH`; the
leading-wildcard query should remain `SCAN`.

The disposable [SQL experiment](curiosity-index-experiment.sql) creates 1,000
in-memory rows, records the equality plan, adds the index, and records both the
equality and wildcard plans. The [saved output](evidence/curiosity-index-results.txt)
shows `SCAN technician_log` before the index, `SEARCH technician_log USING
INDEX ix_technician_log_name` afterward, and `SCAN technician_log` for the
wildcard query. No timing claim is made. The result also illustrates the
trade-off: the index occupies storage and must be maintained on writes even
when a particular query cannot use it.

## 13. LLM questions, checks, and corrections

| Prompt or question | AI-assisted claim | Verification and correction |
|---|---|---|
| Generate the city revenue report | Four-table join, half-open 2025 range, distinct customers, revenue sum | Executed; Python aggregation and edge fixture matched |
| Predict its plan | Expected Orders scan and possible OrderLine automatic search | Actual plan starts with `SCAN ol`; prediction corrected |
| Which indexes optimize it? | Date and join indexes might help | Date index alone was ignored; join-index stage slowed median from 160.880 to 1429.524 ms |
| Rewrite late-order count with a window | Use `COUNT(*) OVER (PARTITION BY ...)` | Count repeated on every order row; corrected with `ROW_NUMBER()` |
| Explain `GROUP BY` and `HAVING` | `WHERE` filters rows; `HAVING` filters groups | Executed against the warehouse and verified with aggregate checks |
| How to handle substring search? | Consider trigram FTS | Two-character `ei` is too short for the normal trigram match |

## 14. Remaining external limitations

- The exact original classroom Plan Safari predictions were not recorded; the
  student recollection and reconstructed explanation are labeled separately.
- Neighboring-pod raw output and SQLite version are unavailable.
- A second technical curiosity is reproducible, but it is not evidence of a
  second historical person-to-person swap.
- The workbook's Discord step is conditional on a curiosity remaining shared
  or unresolved after the pod exchanges. No Discord post is claimed.
- These historical human activities require genuine external evidence; they
  cannot be completed retrospectively by technical automation.

## 15. Final completion matrix

| Requirement | Status | Evidence or limitation |
|---|---|---|
| Five technical learning goals | **VERIFIED** | Queries, plans, benchmarks, injection demo, algebra mapping, tests |
| Task A classroom participation | **STUDENT-REPORTED — PARTIALLY VERIFIED** | Participation and prior predictions are recollection; screenshot verifies displayed after-index plans; fresh reproduction verifies behavior |
| Task B algebra comparison | **VERIFIED** | Selection expression and documented Gemini comparison |
| Task C other-group exchange | **STUDENT-REPORTED — NOT INDEPENDENTLY VERIFIED** | Topics and cross-platform match recorded; other group's raw output/version and identities unavailable |
| Studios 1–4 | **VERIFIED** | Task reports, SQL, plan evidence, benchmark and injection output |
| Optional Studio 5 | **VERIFIED** | Three equivalent query forms and automated comparison |
| Curiosity 1 | **STUDENT-REPORTED** | One classroom collection swap recorded |
| Curiosity 2 | **VERIFIED AS TECHNICAL EXERCISE** | Disposable SQL and saved output; not a second peer swap |
| Reflection | **VERIFIED AS DOCUMENTED** | Seven required reflection headings in `../Reflections/ref03.md` |
| Discord follow-up | **NOT CLAIMED / CONDITIONAL** | No unresolved/shared curiosity post is documented |
