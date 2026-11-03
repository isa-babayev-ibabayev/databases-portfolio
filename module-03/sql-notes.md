# Module 3 SQL notes

## 1. Module purpose

Module 3 connects complex SQL, relational algebra, query plans, measured index
behavior, AI verification, and parameter binding. Technical reproduction is
kept separate from details that were not saved during our classroom Tasks A,
B, and C.

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

These sources support the technical implementation. I did not use every source
during one classroom session; some were used later to check the explanations.

## Classroom collaboration — Module 3

In class, I joined the pod with Sanjay Pachan Maheshwari, Sebastian Emmanuel
Soon, and Myo Min Lin as a guest member. Jomarie was absent. We divided the work
as follows:

| Student | Workstream |
|---|---|
| Sanjay | Plan vocabulary |
| Sebastian | SQL clause order |
| Me | Relational algebra ↔ SQL |
| Myo | Tuning and security |

The supporting records are [Sanjay's shared notes](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Module03/sql-notes.md),
[Sebastian's notes](https://github.com/Emannual20/databases-portfolio/blob/main/Module03/sql-notes.md),
and [Sanjay's reflection](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Reflections/ref03.md).
These links support the group structure and shared exercises. Sanjay's
individual code and benchmark results are not part of my own implementation.

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
disposable reproduction resolves the technical behavior. I participated in
this activity, and my personally supplied predictions are documented below.
I added my prediction text later during portfolio finalization, so it remains
separate from the original group records and is not presented as a separately
preserved pre-execution classroom note.

### Task A — My Predictions

These are my personally supplied Task A predictions. I added this text later
during portfolio finalization, so I do not present it as a separately preserved
pre-execution classroom note.

**Before adding the index:**

1. **`technician = 'Beier'`:** I think SQLite will use `SCAN` because there is
   no index on the `technician` column yet.
2. **`machine_name = 'cnc-02'`:** I also expect `SCAN` because I do not think
   the machine name has an index.
3. **`technician LIKE '%ei%'`:** I think this will use `SCAN` because the search
   pattern starts with `%`, so SQLite cannot easily use a normal index.

**After adding the index:**

I think the first query will change from `SCAN` to `SEARCH` because we created
an index on the `technician` column. For the other two queries, I do not expect
much to change. The machine name still has no index, and the `LIKE` query starts
with `%`.

I wanted to compare these predictions with the actual query plans to see if I
understood them correctly. I compared them with the saved experiment:

| Query | Before index | After technician index |
|---|---|---|
| `technician = 'Beier'` | `SCAN` | `SEARCH` using `ix_job_tech` |
| `machine_name = 'cnc-02'` | `SCAN` | `SCAN` |
| `technician LIKE '%ei%'` | `SCAN` | `SCAN` |

I wrote down my predictions for the three queries and compared them with the
saved execution plans. The results matched my expectations. After creating the
technician index, only the first query changed to `SEARCH`. The actual output is
in [the saved Plan Safari evidence](evidence/plan-safari-prediction-verification.txt).

## 8. Independent Plan Safari verification

This technical exercise dated **2026-10-30** is separate from the classroom
record. Its predictions were made before the fresh execution. It independently
verifies the same plan behavior without turning my later-supplied prediction
text into a separately preserved pre-execution classroom record.

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

This was additional technical practice. It does not recreate the exact
prediction I made in the classroom.

## 9. Classroom Task B — my algebra contribution

My topic was relational algebra ↔ SQL. I translated this query and shared the
expression with the group:

```sql
SELECT * FROM maint_job WHERE technician = 'Beier';
```

Its relational algebra is:

`σ_{technician='Beier'}(maint_job)`

We compared the expression with Gemini. The comparison agreed that `σ`
represents the `WHERE` selection. A separate projection `π` is unnecessary
because `SELECT *` keeps all attributes, and no join belongs in this one-table
expression. We did not save the exact original Gemini transcript, so I have
not created a replacement. Sanjay's [reflection](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Reflections/ref03.md)
also mentions my help with the SQL-to-algebra mapping.

## 10. Task C — neighboring-pod discussion

I also participated in our exchange with a neighboring pod. We compared SQLite
execution plans on Windows and macOS and recorded matching plan
classifications. The known Windows screenshot shows SQLite CLI 3.53.4. We did
not record the macOS SQLite version, so it is not listed here.

One surprising result for our pod was that a function-wrapped predicate such as
`UPPER(technician)` still scanned when only an ordinary column index existed.
The neighboring pod discussed the leading-wildcard scan and covering-index
behavior. The groups recorded an unresolved question about optimizing
case-insensitive or partial-text searches for possible Discord follow-up.

[Sanjay's notes](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Module03/sql-notes.md)
and [Sebastian's notes](https://github.com/Emannual20/databases-portfolio/blob/main/Module03/sql-notes.md)
provide the shared record. My participation is also personally confirmed. The
neighboring pod's complete raw output and macOS SQLite version are still
unavailable.

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

### Curiosity Swap 1 — Classroom Discussion

**Status:** COMPLETE — DOCUMENTED AND STUDENT CONFIRMED

During Module 3, our group collected some questions about SQLite indexes and
query plans. We found these questions interesting:

1. Why does `LIKE '%ei%'` use `SCAN` even when the `technician` column has an
   index?
2. Why can using `UPPER()` on an indexed column prevent SQLite from using the
   normal index?
3. Why does an index stop being covering when a query needs another column?

We discussed these topics with a neighboring pod. One interesting thing was
that different queries could use different plans even when indexes were
available.

We also had a question about how to make partial-text searches faster. We could
not fully explain it, so we kept it as an unresolved question for Discord.

**Classroom and portfolio sources:**

- [Sanjay's shared Module 3 notes](https://github.com/yajnas-crpto/databases_portfolio_sanjay/blob/main/Module03/sql-notes.md)
- [Sebastian's Module 3 notes](https://github.com/Emannual20/databases-portfolio/blob/main/Module03/sql-notes.md)
- [My saved Task A Plan Safari results](evidence/plan-safari-prediction-verification.txt)
- [My Task C neighboring-pod notes](#10-task-c--neighboring-pod-discussion)
- [My posted Discord question](#discord-question)

I remember the questions and the neighboring-pod discussion, and I personally
confirm that this took place during the first scheduled curiosity exchange.

#### Technical follow-up

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

The shared record supports the questions and neighboring-pod discussion. I also
personally confirm that this was the first scheduled curiosity exchange. The
technical sources above explain the behavior.

### Independent curiosity experiment — when indexes do not help

**Status:** independently reproducible technical follow-up, separate from the
two person-to-person classroom exchanges.

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

### Curiosity Swap 2 — End-of-Class Exchange

**Status:** COMPLETE — STUDENT CONFIRMED; ORIGINAL DETAILS NOT RECORDED

We also exchanged curiosity questions a second time at the end of class. I
remember taking part in this exchange, but I did not save a separate list of the
questions from that discussion. I am adding this note now because the exchange
happened but was missing from my notes.

### Discord Question

I posted our Module 3 question about SQLite partial searches and index usage in
the course Discord server.

[My Module 3 Discord question](https://discord.com/channels/1064132619735928932/1064145704391561298/1566944448900898859)

The message may require access to the course server. No answer is claimed here,
and this post is not presented as a second person-to-person curiosity exchange.

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

- The two classroom records preserve conflicting group predictions. My own
  Task A predictions are documented and compared with the saved plans. I
  supplied the text later, and no separate pre-execution classroom note is
  claimed.
- I took part in the neighboring-pod segment, but the macOS SQLite version and
  complete raw output are unavailable.
- Both scheduled curiosity exchanges took place. The first exchange is
  documented above, while the second is confirmed from my memory and has no
  separate original question list.
- I posted the partial-search question in the course Discord server and linked
  the message above. No answer is claimed, and the post is separate from the
  two peer exchanges.
- The second-exchange completion is a retrospective student confirmation, not
  an independently preserved transcript or question list.

## 15. Final completion matrix

| Requirement | Status | Evidence or limitation |
|---|---|---|
| Five technical learning goals | **VERIFIED** | Queries, plans, benchmarks, injection demo, algebra mapping, tests |
| Task A classroom work | **COMPLETE** | I participated; the differing shared predictions remain intact; the execution plans are verified |
| My Task A predictions | **COMPLETE — DOCUMENTED AND COMPARED** | My predictions are present and match the saved execution plans; no separate pre-execution note is claimed |
| Task B algebra comparison | **COMPLETE** | My selection expression, our Gemini comparison, and Sanjay's reflection document the contribution |
| Task C neighboring-pod exchange | **COMPLETE** | I participated; shared notes record the event; the macOS version and complete raw output are unavailable |
| Studios 1–4 | **VERIFIED** | Task reports, SQL, plan evidence, benchmark and injection output |
| Optional Studio 5 | **VERIFIED** | Three equivalent query forms and automated comparison |
| Curiosity Swap 1 | **COMPLETE — DOCUMENTED AND STUDENT CONFIRMED** | Three index questions, their sources, and the neighboring-pod discussion are recorded above |
| Curiosity Swap 2 | **COMPLETE — STUDENT CONFIRMED; ORIGINAL DETAILS NOT RECORDED** | I confirm the end-of-class exchange; I did not preserve a separate question list |
| Person-to-person curiosity exchanges | **COMPLETE — TWO SEPARATE EXCHANGES CONFIRMED** | The first is documented; the second is retrospectively confirmed |
| Technical curiosity SQL experiment | **VERIFIED COMPLETE** | Disposable SQL and saved output; separate from the two human exchanges |
| Reflection | **VERIFIED AS DOCUMENTED** | Seven required reflection headings in `../Reflections/ref03.md` |
| Discord follow-up | **COMPLETE** | [Module 3 question posted and linked](https://discord.com/channels/1064132619735928932/1064145704391561298/1566944448900898859); no answer is required or claimed |
