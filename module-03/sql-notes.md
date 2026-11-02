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

## Classroom collaboration — Module 3

The shared notes identify the classroom pod as Sanjay Pachan Maheshwari,
Sebastian Emmanuel Soon, İsa Babayev, and Myo Min Lin. İsa joined this pod as a
guest member; Jomarie was recorded absent. The group divided the work as
follows:

| Student | Workstream |
|---|---|
| Sanjay | Plan vocabulary |
| Sebastian | SQL clause order |
| İsa | Relational algebra ↔ SQL |
| Myo | Tuning and security |

The supporting records are [Sanjay's shared notes](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Module03/sql-notes.md),
[Sebastian's notes](https://github.com/Emannual20/databases-portfolio/blob/main/Module03/sql-notes.md),
and [Sanjay's reflection](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Reflections/ref03.md).
They corroborate the classroom structure and shared exercises. They do not
make Sanjay's individual code or benchmark results part of İsa's individual
implementation.

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

One shared note claimed that SQLite rejects a `SELECT` alias in `WHERE`. An
isolated SQLite CLI 3.53.4 check of
`SELECT technician AS tech FROM maint_job WHERE tech = 'Beier'` returned
`Beier`, so that claim is not repeated here. Alias use in `WHERE` is
SQLite-specific and less portable than using `WHERE technician = 'Beier'`;
the logical clause order above is still the useful general model.

## 5. Workstream 3 — query-plan vocabulary

- `SCAN table`: visit every row, possibly in index order. A scan is reasonable
  when most rows are needed or the table is small.
- `SEARCH table USING INDEX`: use an index to select rows, then visit the table
  for columns not stored in the index.
- `SEARCH ... USING COVERING INDEX`: obtain every required value from the
  index without a separate table lookup.
- `SCAN ... USING COVERING INDEX`: traverse the index without a selective
  lookup while obtaining every requested value from it. The isolated
  [covering-scan demo](covering-scan-demo.sql) records
  `SCAN t USING COVERING INDEX i`; `INDEXED BY` deliberately forces this index
  so the plan shape can be studied. See the
  [recorded output](evidence/covering-scan-results.txt).
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

## 7. Classroom Task A — reconciled group record

The supplied classroom screenshot is not published because it visibly contains
another student's filesystem path. It shows Windows SQLite CLI 3.53.4 and
these after-index plans:

```text
technician equality: SEARCH maint_job USING INDEX ix_job_tech (technician=?)
machine-name equality: SCAN machine
leading-wildcard technician: SCAN maint_job
```

Sanjay's and Sebastian's shared notes preserve different original group
predictions. They should not be presented as one unanimous prediction:

| Query | Sanjay's record | Sebastian's record | Verified baseline | Verified after `ix_job_tech` |
|---|---|---|---|---|
| `technician = 'Beier'` | SCAN | SCAN | `SCAN maint_job` | `SEARCH maint_job USING INDEX ix_job_tech` |
| `machine_name = 'cnc-02'` | SEARCH | SCAN | `SCAN machine` | `SCAN machine` |
| `technician LIKE '%ei%'` | SCAN | SEARCH | `SCAN maint_job` | `SCAN maint_job` |

The group records differ for the Machine and wildcard queries. The clean
disposable reproduction resolves the technical behavior, but it does not
recover a separate individual prediction for İsa. After checking the plans,
the technician query changed to an index search. The Machine query still
scanned because the new index belongs to another table, and the leading-
wildcard query scanned because an ordinary B-tree has no fixed starting
prefix.

## 8. Independent Plan Safari verification

This technical exercise dated **2026-10-30** is separate from the classroom
record. Its predictions were made before the fresh execution and are not
presented as İsa's missing original prediction.

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

### Additional Plan Safari practice

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

This was additional technical practice. It does not supply an individual
historical prediction for İsa.

## 9. Classroom Task B — İsa's algebra contribution

The shared workstream record assigns relational algebra ↔ SQL to İsa. The
selected query was:

```sql
SELECT * FROM maint_job WHERE technician = 'Beier';
```

Its relational algebra is:

`σ_{technician='Beier'}(maint_job)`

The documented Gemini comparison agreed that `σ` represents the `WHERE`
selection. A separate projection `π` is unnecessary here because `SELECT *`
keeps all attributes, and no join belongs in this one-table expression. The
exact original Gemini transcript was not preserved, so no new transcript is
substituted for it. Sanjay's [reflection](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Reflections/ref03.md)
also credits İsa with helping map this SQL query into relational algebra.

## 10. Task C — neighboring-pod discussion

The pod's shared notes document an exchange with a neighboring group. The
groups compared SQLite execution plans on Windows and macOS and recorded
matching plan classifications. The known Windows screenshot shows SQLite CLI
3.53.4. The macOS SQLite version was not recorded, so no version is invented.

The pod's surprising result was that a function-wrapped predicate such as
`UPPER(technician)` still scanned when only an ordinary column index existed.
The neighboring pod discussed the leading-wildcard scan and covering-index
behavior. The groups recorded an unresolved question about optimizing
case-insensitive or partial-text searches for possible Discord follow-up.

[Sanjay's notes](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Module03/sql-notes.md)
and [Sebastian's notes](https://github.com/Emannual20/databases-portfolio/blob/main/Module03/sql-notes.md)
support this pod-level event. They do not independently show whether İsa was
present for the whole neighboring-pod segment. This portfolio therefore does
not turn the group record into a stronger personal-attendance claim.

### Cross-source technical comparison

The classroom screenshot displays SQLite CLI **3.53.4** in a separate worktree
whose visible path ends in `databases_portfolio_sanjay`. The downloaded
independent result records Python SQLite **3.46.1**. I reran the supplied
[Python experiment](plan-comparison.py) locally with Python SQLite **3.50.4**
and saved the [fresh output](evidence/plan-comparison-results.txt).

| Plan type | Screenshot 3.53.4 | Supplied reproduction 3.46.1 | Fresh reproduction 3.50.4 |
|---|---|---|---|
| Technician equality after index | `SEARCH ... USING INDEX ix_job_tech` | `SEARCH ... USING INDEX ix_job_tech` | `SEARCH ... USING INDEX ix_job_tech` |
| Machine-name lookup | `SCAN machine` | `SCAN machine` | `SCAN machine` |
| Leading-wildcard lookup | `SCAN maint_job` | `SCAN maint_job` | `SCAN maint_job` |

The SCAN/SEARCH classifications agree, but these are not three measurements of
one identical database environment. The two Python runs are controlled local
reproductions, not replacements for the neighboring pod's macOS version or raw
plan.

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

### Questions collected during Task C

- **Why do leading wildcards prevent normal index searches?** An ordinary
  B-tree is ordered from the beginning of each indexed value. A pattern such
  as `%ei%` has no fixed beginning that SQLite can use to narrow the index
  range, so the verified example scans. See the
  [LIKE optimization conditions](https://www.sqlite.org/optoverview.html#the_like_optimization).
- **How can we optimize case-insensitive and partial-text searches?** A
  `COLLATE NOCASE` index can support compatible case-insensitive equality or
  prefix comparisons. An expression index such as
  `ON technician_log(UPPER(technician))` can support a query using the same
  expression. FTS5 can support full-text use cases; configured with its
  `trigram` tokenizer it can support many substring searches, but normal
  trigram matching needs at least three characters. Therefore the two-letter
  pattern `%ei%` does not gain the usual trigram-index benefit. See
  [SQLite expression indexes](https://www.sqlite.org/expridx.html) and the
  [FTS5 trigram tokenizer](https://www.sqlite.org/fts5.html#the_trigram_tokenizer).
- **Why does selecting another column remove a covering benefit?** An index is
  covering only when it contains every value required by the query. The
  disposable experiment changes from `USING COVERING INDEX` for `SELECT a` to
  `USING INDEX` for `SELECT a, b`. See the
  [SQLite query planner](https://www.sqlite.org/queryplanner.html#covering_indexes).
- The dashboard uses three temporary B-trees —
  [raw plan](evidence/task1-plan.txt).
- An added index changed the plan and made an aggregate nearly nine times
  slower — [benchmark evidence](task2-benchmark.md).
- An SQL query can run but count joined lines rather than customers if
  `DISTINCT` is omitted — [edge-case tests](tests/test_module03.py).
- Relational algebra describes meaning while a query plan describes a physical
  strategy — [Task 4](task4-algebra-to-plan.md).

The shared record preserves questions and a pod-level neighboring-group
discussion. It does not independently prove a break-time person-to-person swap
by İsa. The workbook asks for a second swap at the end, but no second historical
swap is claimed.

### Independent curiosity experiment — when indexes do not help

**Status:** independently reproducible technical follow-up, not a claim of a
second person-to-person classroom exchange.

**Question:** Will an ordinary index on `technician` help both an equality
predicate and `LIKE '%ei%'`?

**Prediction:** equality should change from `SCAN` to `SEARCH`; the
leading-wildcard query should remain `SCAN`.

The disposable [SQL experiment](curiosity-index-experiment.sql) creates 1,000
in-memory rows and records equality, wildcard, function-expression, covering,
and non-covering plans. The [saved output](evidence/curiosity-index-results.txt)
shows the equality query changing from `SCAN` to `SEARCH`, the wildcard and
function-wrapped queries scanning with only the ordinary column index, the
matching expression index enabling a function-based `SEARCH`, and the extra
output column removing the covering benefit. No timing claim is made. The
result also illustrates the trade-off: indexes occupy storage and must be
maintained on writes even when a particular query cannot use them.

### Example questions for a future second curiosity swap

**Status:** examples with verified explanations; they were not actually
exchanged with Tunay or another student.

- **Example A:** Why does `WHERE technician LIKE '%ei%'`
  usually produce `SCAN` even when `ix_job_tech` exists? The leading `%`
  leaves an ordinary B-tree without a fixed starting prefix. Sources: the
  [fresh reproduction](evidence/plan-comparison-results.txt) and
  [SQLite query-plan documentation](https://www.sqlite.org/eqp.html).
- **Example B:** Why can
  `SELECT a FROM covering_demo WHERE a = 1` use a covering index, while
  `SELECT a, b FROM covering_demo WHERE a = 1` uses an ordinary index lookup?
  The index contains `a` but not `b`, so the second query must visit the table
  to retrieve `b`. Sources: the
  [curiosity experiment](curiosity-index-experiment.sql), its
  [recorded plans](evidence/curiosity-index-results.txt), and the official
  Module 3 covering-index material.

After a real exchange, this section can record the actual participant,
questions, answers, date, and medium. None of those details has been invented.

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

- The two classroom records preserve conflicting group predictions; no
  separate individual prediction for İsa is available.
- The neighboring-pod macOS SQLite version and raw output are unavailable, and
  İsa's presence for the complete segment is not independently established.
- A second technical curiosity is reproducible and example questions are
  prepared, but no completed second person-to-person swap is documented.
- The workbook's Discord step is conditional on a curiosity remaining shared
  or unresolved after the pod exchanges. No Discord post is claimed.
- These historical human activities require genuine external evidence; they
  cannot be completed retrospectively by technical automation.

## 15. Final completion matrix

| Requirement | Status | Evidence or limitation |
|---|---|---|
| Five technical learning goals | **VERIFIED** | Queries, plans, benchmarks, injection demo, algebra mapping, tests |
| Task A group record | **DOCUMENTED — TECHNICALLY VERIFIED** | Sanjay and Sebastian recorded conflicting predictions; screenshot and fresh reproduction verify final plans; İsa's individual prediction is unavailable |
| Task B algebra comparison | **DOCUMENTED — EXTERNALLY CORROBORATED** | İsa's selection expression, documented Gemini comparison, and Sanjay's credit |
| Task C neighboring-pod exchange | **DOCUMENTED AT POD LEVEL — PERSONAL CONFIRMATION NEEDED** | Shared notes record the event; İsa's presence for the full segment is not independently established |
| Studios 1–4 | **VERIFIED** | Task reports, SQL, plan evidence, benchmark and injection output |
| Optional Studio 5 | **VERIFIED** | Three equivalent query forms and automated comparison |
| Curiosity 1 | **POD QUESTIONS DOCUMENTED — PERSONAL EXCHANGE UNVERIFIED** | Shared notes preserve the questions and neighboring-pod discussion |
| Curiosity 2 technical exercise | **VERIFIED** | Disposable SQL and saved output |
| Curiosity swap 2 | **REQUIRES REAL PEER ACTIVITY** | Example questions and sources exist; no participant/response/date/medium supplied |
| Reflection | **VERIFIED AS DOCUMENTED** | Seven required reflection headings in `../Reflections/ref03.md` |
| Discord follow-up | **NOT CLAIMED / CONDITIONAL** | No unresolved/shared curiosity post is documented |
