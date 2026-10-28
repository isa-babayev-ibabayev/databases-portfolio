# Module 3 SQL notes

## 1. Module purpose

Module 3 connects complex SQL, relational algebra, query plans, measured index
behavior, AI verification, and parameter binding. The technical work below is
separate from the authentic classroom Task A/B/C evidence supplied by the
student.

## 2. Learning references

| Reference | Use in this work |
|---|---|
| [Professor's Module 3 workbook](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/03-llm-assisted-sql-and-query-profiling.md) | Primary specification, fixture, queries, and exercise sequence |
| [SQLite EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html) | Official meanings of SCAN, SEARCH, and temporary B-trees |
| [SQLite query planner](https://www.sqlite.org/queryplanner.html) | Index selection and covering indexes |
| [SQLite expression indexes](https://www.sqlite.org/expridx.html) | Why an expression index must match the query expression |
| [SQLite query optimizer overview](https://www.sqlite.org/optoverview.html#the_like_optimization) | Conditions for prefix LIKE optimization and collations |
| [SQLite FTS5 trigram tokenizer](https://www.sqlite.org/fts5.html#the_trigram_tokenizer) | Indexed substring matching and short-token limits |
| [Relational algebra](https://en.wikipedia.org/wiki/Relational_algebra) | Selection, projection, join, and extended grouping notation |
| [SQLite plan operations](https://use-the-index-luke.com/sql/explain-plan/sqlite/operations) | Concise independent SCAN/SEARCH/covering glossary |
| [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet) | Parameterized queries and why manual escaping is discouraged |
| [Python 3.14 sqlite3](https://docs.python.org/3.14/library/sqlite3.html) | Python placeholder and parameter-binding API |

These sources were consulted during technical implementation. This is not a
claim that the student personally read every source in a classroom session.

## 3. Workstream 1 — Algebra ↔ SQL

| Algebra | SQL | Purpose |
|---|---|---|
| (sigma) selection | `WHERE` | filter rows |
| (pi) projection | `SELECT` list | choose output columns |
| (owtie) join | `JOIN ... ON` | combine related relations |
| (gamma) grouping | `GROUP BY` plus aggregates | calculate per-group values |
| (ho) rename | `AS` | name relations or values |

The complete city-revenue translation, including (sigma), (pi),
(owtie), and (gamma), is in
[task4-algebra-to-plan.md](task4-algebra-to-plan.md).

SQL keeps duplicate rows unless `DISTINCT` or a grouping operation changes
them. Classical relational algebra normally uses sets. This is why
`COUNT(DISTINCT customer_id)` is a meaningful part of the translation rather
than decoration.

## 4. Workstream 2 — clause order

Written order:

`SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY`

Logical evaluation order:

`FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY`

A counterexample is trying to filter an aggregate in `WHERE`:

```sql
SELECT city, COUNT(*) AS n
FROM customer
WHERE COUNT(*) > 10
GROUP BY city;
```

It fails because row filtering occurs before groups and their counts exist. The
condition belongs in `HAVING COUNT(*) > 10`.

## 5. Workstream 3 — query-plan vocabulary

- `SCAN table`: visit every row (possibly in index order).
- `SEARCH table USING INDEX`: use an index to visit a subset, then read table
  rows for other columns.
- `USING COVERING INDEX`: every requested value is in the index, so no table
  lookup is needed.
- `USE TEMP B-TREE`: SQLite built a temporary structure for sorting,
  grouping, or distinct processing.

Plans are optimizer choices, not relational-algebra expressions. They can
change with data size, statistics, indexes, and SQLite versions.

## 6. Workstream 4 — tuning and security

An index helps only a particular access pattern. The measured dashboard became
almost nine times slower after its join order changed, while the same date
index made a selective one-day query roughly thirteen times faster.

SQL values must be bound with placeholders. The local payload experiment
returned all rows through the vulnerable string-built query and zero rows
through the safe parameterized query. See [Task 3](task3-injection.md).

## 7. Classroom Task A — original screenshot and observations

### Original classroom notes — student-provided evidence

The supplied screenshot was reviewed at:
`Desktop/IMG-20261022-WA0019(1).jpg`. It was not copied into the public
repository because it visibly identifies another student's filesystem path.
The image is classroom-provided evidence, not proof that every command was run
on the portfolio owner's laptop.

Faithful transcription:

```text
EXPLAIN QUERY PLAN
SELECT * FROM maint_job WHERE technician = 'Beier';
SEARCH maint_job USING INDEX ix_job_tech (technician=?)

EXPLAIN QUERY PLAN
SELECT * FROM machine WHERE machine_name = 'cnc-02';
SCAN machine

EXPLAIN QUERY PLAN
SELECT * FROM maint_job WHERE technician LIKE '%ei%';
SCAN maint_job
```

The screenshot shows SQLite CLI 3.53.4 and an existing
`ix_job_tech(technician)` index. It also shows that `CREATE INDEX` was first
entered without its terminating semicolon, so the next `EXPLAIN` was appended
and produced a syntax error. Later commands succeeded. The screenshot does not
establish a clean before-index baseline.

### Technical clarification and reproducibility checks

- Appropriately indexed technician equality can use SEARCH.
- The technician index cannot help a Machine-name predicate.
- A leading wildcard has no fixed prefix for an ordinary B-tree range search.
- `upper(technician)` does not match an ordinary index on `technician`; an
  expression index on the same expression can help.

A separate local reproduction rebuilt Module 2's fixture in a disposable
database and compared plans before and after `ix_job_tech`. Before the index,
all three queries scanned. Afterwards, only technician equality changed to
`SEARCH maint_job USING INDEX ix_job_tech`; Machine equality, leading-wildcard
LIKE, and `upper(technician)` still scanned. See the
[raw reproduction](evidence/classroom-plan-reproduction.txt). The classroom
history above remains unchanged.

## 8. Classroom Task B — original human explanation and Gemini comparison

### Original classroom notes — student-provided evidence

> For Task B, we need to make mathematical equation. For SELECT * FROM
> maint_job WHERE technician = 'Beier'; command, logic and sequence should be
> like this: sigma technician (because we select from WHERE? from technician)
> equals 'Beier' is text value and (maint_job) means this means we are doing
> filtering to the main job table.

[
sigma_{technician='Beier'}(maint\_job)
]

> I asked Gemini to translate the same query. We completely agreed on using
> the selection operator for the WHERE clause. The only difference was that
> Gemini pointed out the projection operator is usually omitted entirely when
> the SQL query uses SELECT *.

### Technical clarification

(sigma) means row selection, `technician='Beier'` is the predicate, and
`maint_job` is the input relation. There is no join. Explicit projection can
be omitted for `SELECT *`; if shown, it would project every attribute.

## 9. Classroom Task C — neighboring-pod discussion

### Original classroom notes — student-provided evidence

**Plan comparison:** Our Windows SQLite plan matched the macOS SQLite plan from
the neighboring pod: both used SEARCH for direct equality matches.

**Our pod's surprise:** Wrapping an indexed column in a function, such as
`upper(technician)`, can prevent the ordinary index from supporting the
search and produce a scan.

**Neighboring pod's surprise:** Leading wildcards, such as `LIKE '%ei%'`,
prevent ordinary B-tree prefix-range searches. Requesting columns absent from
an index can also make a previously covering index non-covering.

**Unresolved question for Discord:** If functions and wildcards break indexes,
how do we efficiently optimize case-insensitive searches or partial-text
matches in SQLite?

Task C is reported as completed. No participant names, transcript, timing, or
unavailable neighboring-pod output has been invented. The cross-platform match
is student-reported and awaits the neighboring pod's raw plan/version if formal
corroboration is needed. There is no evidence that the question was posted to
Discord.

### Researched technical answer

- For compatible ASCII case-insensitive equality or prefix searches, define
  the column/index with `COLLATE NOCASE` and use a matching query collation.
- For `lower(column) = ?`, an expression index such as
  `CREATE INDEX ... ON t(lower(column))` can help when the query expression
  matches the indexed expression.
- For substring search, FTS5's trigram tokenizer supports suitable
  `LIKE '%text%'` patterns. Full-text tokens shorter than three Unicode
  characters do not match, and patterns without a non-wildcard run of at least
  three characters fall back to a scan. Therefore the classroom `'%ei%'`
  example is too short for the normal trigram advantage.
- Always verify the actual plan on the deployed SQLite version and data.

## 10. Independently reproduced technical checks

- Warehouse counts: Customer 2,000; Product 500; Orders 60,000; OrderLine
  240,000.
- Disposable Task A reproduction: equality changed from SCAN to SEARCH only
  after the technician index; unrelated, wildcard, and function predicates
  remained scans.
- Dashboard result: four cities; independent Python aggregation matched.
- Baseline dashboard plan: OrderLine scan, three primary-key searches, and
  three temporary B-trees.
- Date index ignored by dashboard but used by the single-day lookup.
- OrderLine join index changed the dashboard plan and made it much slower.
- Product index was unused by the dashboard but improved a direct product
  filter.
- Parameter binding neutralized the injection payload.
- Grouped, correlated, and window late-order queries returned identical rows.

## 11. Collected curiosities and sources

### Student-supported classroom curiosities

- `upper(technician)` can defeat the ordinary index — Task C notes and
  [SQLite expression indexes](https://www.sqlite.org/expridx.html).
- `LIKE '%ei%'` scans despite a technician index — Task A screenshot and
  [LIKE optimization](https://www.sqlite.org/optoverview.html#the_like_optimization).
- Adding an output column can change a covering search into a table lookup —
  Task C notes and [SQLite query planner](https://www.sqlite.org/queryplanner.html#covering_indexes).

### Additional AI-selected, experimentally verified curiosities

- The dashboard uses three `USE TEMP B-TREE` operations — [raw plan](evidence/task1-plan.txt).
- An index can change a plan and make a query almost nine times slower —
  [benchmark evidence](task2-benchmark.md).
- A query can execute but count lines instead of customers if `DISTINCT` is
  omitted — [edge-case tests](tests/test_module03.py).
- Relational algebra describes meaning while `EXPLAIN QUERY PLAN` describes a
  physical strategy — [algebra-to-plan exercise](task4-algebra-to-plan.md).

The current record supports one classroom collection swap in Task C. The latest
workbook asks for swaps at the break and end; no second historical swap is
invented here.

## 12. LLM questions, responses, and verified corrections

| Prompt/question | AI claim | Check and correction |
|---|---|---|
| Generate the city revenue report | Four joins, 2025 half-open range, distinct customers, revenue sum | Executed; Python aggregation and edge fixture matched |
| Predict its plan | Expected Orders scan and possible OrderLine automatic search | Wrong loop order: actual plan starts with `SCAN ol` |
| Which indexes optimize it? | Date and join indexes might help | Date index alone was ignored; join index changed plan but slowed median from 160.880 to 1429.524 ms |
| Rewrite late-order count with a window | `COUNT(*) OVER (PARTITION BY ...)` | Count correct but repeated per order; corrected with `ROW_NUMBER()` |
| How to handle substring search? | Consider trigram FTS | Verified limitation: a two-character term such as `ei` is too short for the normal trigram match |

## 13. Remaining student checkpoints

- TODO — STUDENT: Confirm the personal take-away and difficult parts in
  [ref03.md](../Reflections/ref03.md).
- TODO — STUDENT: Practise explaining one SCAN/SEARCH plan and the algebra
  expression without notes.
- TODO — STUDENT: Add a real Discord link only if the unresolved question was
  actually posted.
- TODO — STUDENT: Add neighboring-pod raw output/version only if available; do
  not repeat the already completed discussion.
