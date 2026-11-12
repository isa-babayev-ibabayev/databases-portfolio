# Module 6a learning guide — from SQLite operations to DuckDB analytics

This guide explains the real project in simple English. Small factory examples
are illustrations; numbers labeled **measured** came from the actual laptop on
2026-11-12. The official workbook was read from its current `main` revision on
that date. Its six-round studio is below an explicit provisional-draft boundary.

## Glossary

- **Database engine:** software that stores or reads data and executes queries.
- **SQLite:** an embedded engine that keeps a database in one file. It is very
  effective for small transactions, indexed lookups, and local applications.
- **DuckDB:** an embedded analytical engine designed to process many values in
  columns and query files such as Parquet directly.
- **Row:** one record, such as one part used in one maintenance job.
- **Column:** one property shared by records, such as `machine_id` or price.
- **Table:** named rows with the same columns.
- **Schema:** the column names, types, keys, and rules describing a table.
- **CSV:** a text file where commas separate values. It is portable but stores
  little type information and repeats text many times.
- **Parquet:** a typed, compressed, column-oriented file format. Parquet is a
  file format; DuckDB is an engine that can query it.
- **Operational workload / OLTP:** frequent small business actions—insert one
  job, update one status, or find one ID now.
- **Analytical workload / OLAP:** read many historical rows to calculate totals,
  trends, or grouped reports.
- **Aggregation:** turning many values into summaries with `SUM`, `COUNT`, and
  similar functions.
- **`GROUP BY`:** forms buckets of rows with the same selected key before an
  aggregate is calculated for each bucket.
- **Query plan:** the engine's work plan: what it scans, filters, projects,
  groups, or sorts.
- **Scan:** reading rows or column values from a table or file.
- **Index:** an extra search structure that can locate selected rows quickly;
  maintaining and scanning it also costs time and space.
- **Benchmark:** a controlled measurement of the same defined work.
- **Median:** the middle ordered result. It is less distorted by one unusually
  slow run than an average.
- **Speed-up:** old time divided by new time. `200 / 50 = 4`, so the measured
  workload is four times faster, not every possible workload.
- **Data freshness:** how closely a copy reflects the latest source changes.
- **Snapshot:** a read-only picture of data at a particular time.
- **Reproducibility:** another person can run the checked-in instructions and
  recreate the result instead of trusting a private generated file.

## Round 1 — Build ten periods of history

### 1. Business problem

Module 5 has only 90 days of reporting data. Controlling wants a long-history
report, so we need more time periods without changing the underlying mix of
machines, technicians, sites, parts, and prices. Reusing the same source keeps
the later engine comparison fair: if both the data and engine changed, we could
not know which change caused the timing difference.

The operational `normalize.db` must remain untouched. `history.db` is a separate
experiment, not the system of record.

### 2. Concept and analogy

Imagine photocopying one quarter's production report ten times and moving each
copy 91 days forward on a calendar. `k` is the copy number from 0 through 9.
The ID offset distinguishes jobs in different copies; it does not make each
job-part row unique because one job legitimately has several parts.

### 3. Miniature data and calculation

Source:

| job_id | machine_id | technician | part_price | done_on |
|---:|---|---|---:|---|
| 101 | CNC-01 | Anna | 50 | 2025-01-01 |
| 102 | CNC-02 | Ben | 80 | 2025-01-02 |
| 103 | CNC-01 | Anna | 20 | 2025-01-03 |

Copy 0 keeps the IDs and dates. Copy 1 adds `1 × 1,000,000` to each ID and
`1 × 91` days to each date:

| copy | job_id | machine_id | done_on |
|---:|---:|---|---|
| 0 | 101 | CNC-01 | 2025-01-01 |
| 0 | 102 | CNC-02 | 2025-01-02 |
| 0 | 103 | CNC-01 | 2025-01-03 |
| 1 | 1000101 | CNC-01 | 2025-04-02 |
| 1 | 1000102 | CNC-02 | 2025-04-03 |
| 1 | 1000103 | CNC-01 | 2025-04-04 |

Three rows × two periods = six rows. Likewise, 200,000 × 10 = 2,000,000;
we are not merely adding ten rows.

### 4. Relevant implementation, line by line

```python
QUARTERS = 10
connection.execute("ATTACH DATABASE ? AS m5", (source_uri,))
```

The constant makes ten copies. `ATTACH` lets a new SQLite connection read the
Module 5 file under the short name `m5`; the URI opens it read-only.

```sql
INSERT INTO report_history
SELECT r.job_id + k * 1000000, r.machine_id, r.site, r.technician,
       r.part_no, r.part_price,
       date(r.done_on, '+' || (k * 91) || ' days')
FROM m5.report_jobpart AS r,
     (WITH RECURSIVE n(k) AS (
          SELECT 0 UNION ALL SELECT k + 1 FROM n WHERE k < 9)
      SELECT k FROM n)
```

- `WITH RECURSIVE` starts at `k=0`, then repeatedly adds one until `k=9`.
- `UNION ALL` keeps every generated number: 0, 1, …, 9.
- The comma in `FROM` pairs every source row `r` with every `k`: the Cartesian
  multiplication that creates ten copies.
- `r.job_id + k * 1000000` separates IDs between periods.
- `date(...)` shifts the date, while descriptive columns remain comparable.
- `commit()` makes the completed insert durable.
- The CSV writer fetches the original source in 10,000-row chunks, so Python
  does not hold two million rows in memory. The workbook deliberately exports
  200,000 source rows; Round 2 expands them again in DuckDB.

### 5. Actual execution and result

Command: `uv run python -B Module06a/prepare.py`.

**Measured:** 2,000,000 history rows, sum 21,000,000, dates 2026-01-01 through
2028-06-27, ten groups of 200,000, zero null-containing rows, zero malformed
dates, and SQLite integrity `ok`. The database is 112,685,056 bytes. The CSV
has 200,000 data rows and is 10,805,002 bytes. The Module 5 SHA-256 was identical
before and after.

### 6. Why it makes sense and what can go wrong

Every price is copied ten times, so 2,100,000 becomes 21,000,000. Common errors
are exporting the wrong table, generating only nine `k` values, reusing IDs
without an offset, shifting by the wrong unit, or deleting an existing output.
The script builds a temporary file, validates it, and only replaces on an
explicit `--rebuild`; a prior valid file is backed up.

Fixed days are not calendar months. For 2025-01-31, actual SQLite results were
May 1 for +90 days, May 2 for +91 days, and March 3 for +1 month. The official
91-day method is preserved even though calendar behavior deserves attention.

### 7. Testing

Checks cover source count and hash, history count/sum/dates, ten period sizes,
nulls, date parsing, integrity, CSV header/count, and safe reuse. Generated data
is ignored by Git.

### 8. One-minute professor explanation

> I reused Module 5's 200,000 rows so the distribution stayed constant. A
> recursive sequence creates `k=0..9`, and every source row is paired with every
> `k`, giving two million rows. I offset job IDs by one million and dates by 91
> days for each period. I validated counts, sums, dates, nulls, integrity, and
> the source hash. The source database remained unchanged, and the CSV contains
> the original 200,000 rows because DuckDB performs the next expansion.

### 9. Knowledge check

1. **Why two million?** 200,000 source rows × 10 generated `k` values.
2. **Why hash the source?** Matching hashes are strong evidence that its bytes
   did not change during the experiment.
3. **Is +91 days the same as +3 months?** No. Months vary in length; fixed-day
   arithmetic and calendar arithmetic can produce different dates.

## Round 2 — Convert to typed, columnar Parquet

### 1. Business problem

We need a reproducible analytical copy that DuckDB can scan efficiently. The
copy must contain the same facts as SQLite; merely producing a file is not
proof of a correct migration.

### 2. Concept and analogy

CSV resembles writing each complete factory record on one line. A row store
also keeps a record's fields together. Parquet stores similar column values
together—like separate shelves for machine IDs, prices, and dates—plus types
and compression. When a report needs only machine, site, technician, and price,
the engine can avoid reading unrelated job and part columns.

```text
Rows:     [job1, machine1, price1] [job2, machine2, price2]
Columns:  [job1, job2] [machine1, machine2] [price1, price2]
```

Compression stores repeated values compactly. It does not mean lost rows.

### 3. Miniature transformation

For two CSV rows and `range(0,2)`, DuckDB pairs each row with `k=0` and `k=1`:

| source job | k | new job | date rule |
|---:|---:|---:|---|
| 101 | 0 | 101 | original + 0 days |
| 101 | 1 | 1000101 | original + 91 days |
| 102 | 0 | 102 | original + 0 days |
| 102 | 1 | 1000102 | original + 91 days |

### 4. Relevant implementation, line by line

```sql
COPY (
  SELECT r.job_id + k * 1000000 AS job_id, r.machine_id, r.site,
         r.technician, r.part_no, r.part_price,
         CAST(r.done_on AS DATE) + CAST(k * 91 AS INTEGER) AS done_on
  FROM read_csv_auto('report_jobpart.csv', header=true) AS r,
       range(0, 10) AS t(k)
) TO 'report_history.parquet' (FORMAT parquet)
```

- `read_csv_auto` reads the header and infers source types.
- `range(0,10)` supplies the same ten multipliers as SQLite.
- `CAST(... AS DATE)` changes text into an actual date type.
- `COPY (...) TO` streams query output into Parquet; Python does not receive a
  two-million-row list.
- The output is first written to a temporary file and validated before publish.

### 5. Actual execution and result

Command: `uv run python -B Module06a/to_parquet.py`.

**Measured:** Parquet has 2,000,000 rows, price sum 21,000,000, ID sum
9,020,001,000,000, dates 2026-01-01 to 2028-06-27, and zero nulls. Its types
include `BIGINT`, `VARCHAR`, `DOUBLE`, and `DATE`. It is 2,323,412 bytes, versus
112,685,056 bytes for the two-million-row SQLite file. The 10,805,002-byte CSV
has only 200,000 rows, so its size is not a like-for-like storage comparison.

### 6. Why it makes sense and what can go wrong

Machine, site, technician, and part values repeat heavily, so column compression
is unusually effective. Risks include exporting only 200,000 rows, treating
dates as uncontrolled text, accepting matching counts but wrong values, or
publishing a half-written file. Validation compares count, two sums, both date
limits, schema, and every column's null count before atomic replacement.

### 7. Testing

Tests query Parquet with DuckDB, inspect its schema, and compare its summary
against read-only SQLite. The default and Zstandard copies also match on count
and sum.

### 8. One-minute professor explanation

> DuckDB reads the 200,000-row CSV, pairs every row with ten range values, and
> writes two million typed rows directly to Parquet. Parquet stores columns
> together, so repeated values compress and analytical queries can read only
> needed columns. I did not trust size or count alone: SQLite and Parquet match
> on row count, price sum, ID sum, dates, and null checks. DuckDB is the query
> engine; Parquet is the file format.

### 9. Knowledge check

1. **Is Parquet a database engine?** No, it is a file format; DuckDB is the
   engine querying it.
2. **Why is matching count insufficient?** Rows could have wrong prices, IDs,
   dates, or nulls while the count remains unchanged.
3. **Why is the CSV size misleading here?** It holds 200,000 rows, while SQLite
   and Parquet hold two million.

## Round 3 — Run a fair analytical race

### 1. Business problem

Lea needs evidence that the moved reports are both correct and faster. A fair
benchmark gives both engines the same rows and business question, like asking
two planners to total the same production ledger under comparable conditions.

### 2. Concept and example

The dashboard groups all applicable rows by machine, site, and technician and
sums part prices. If these rows exist:

| machine | site | technician | price |
|---|---|---|---:|
| M1 | North | Ana | 10 |
| M1 | North | Ana | 15 |
| M2 | South | Bo | 7 |

the output is `(M1, North, Ana, 25)` and `(M2, South, Bo, 7)`.

Warm-up runs load code and pages but are discarded. Timed trials alternate the
first engine: `SQLite → DuckDB`, then `DuckDB → SQLite`. This limits systematic
order bias from cache state or laptop activity.

For teaching only, times 12, 13, 14, 15, 80 ms have median 14 ms after sorting.
The mean is 26.8 ms because the 80-ms outlier pulls it upward. Actual evidence
uses the recorded samples, not these example numbers.

### 3. Relevant implementation, line by line

```python
elapsed = (time.perf_counter() - started) * 1000
sqlite_median = statistics.median(sqlite_times)
speedup = sqlite_median / duckdb_median
```

`perf_counter` is a monotonic high-resolution timer. Five is odd, so the median
is an actual middle run. Dividing SQLite time by DuckDB time produces the
workload-specific speed-up.

Before timing, `canonical()` sorts and normalizes returned tuples. The monthly
query needs two spellings: DuckDB uses `strftime(done_on, '%Y-%m')`; SQLite uses
`strftime('%Y-%m', done_on)`. The provisional workbook's shared spelling gives
SQLite NULL months and therefore different grouping. Correcting syntax preserves
the same business operation.

### 4. Actual execution and result

Command: `uv run python -B Module06a/race.py --runs 5 --json`.

| Workload | SQLite samples (ms) | SQLite median | DuckDB samples (ms) | DuckDB median | Speed-up |
|---|---|---:|---|---:|---:|
| Dashboard | 5832.15, 5563.32, 5709.07, 5862.72, 5853.56 | 5832.15 | 81.57, 65.69, 86.32, 58.02, 74.13 | 74.13 | 78.67× |
| Monthly | 6592.70, 7781.17, 7795.07, 7013.05, 6902.42 | 7013.05 | 77.32, 79.86, 74.27, 61.15, 71.98 | 74.27 | 94.43× |

The dashboard returned 350 equivalent groups; monthly returned 1,500.

### 5. Why it makes sense and what can go wrong

These queries scan and aggregate all history. DuckDB reads the four needed
columns from compressed Parquet and processes vectors of values. SQLite reads
row-oriented records and builds temporary grouping state. The result proves an
advantage for these data, queries, versions, and machine—not universal engine
superiority.

Wrong datasets, different filters, failure to fetch results, a single timing,
fixed run order, background load, or syntactically different semantics can all
invalidate a benchmark. The script checks output every timed run and reports
min–max spread to expose noise.

### 6. Testing

Automated tests execute both query forms and compare complete canonical results.
Evidence tests verify five samples per engine, alternating order, medians, and
ratios derived from the actual samples.

### 7. One-minute professor explanation

> I warmed both engines, alternated which ran first, measured five complete
> result fetches with a monotonic timer, and used the median. Before accepting a
> time I compared all groups. The dashboard was 5,832.15 versus 74.13 ms, or
> 78.67 times faster in DuckDB; monthly was 7,013.05 versus 74.27 ms, or 94.43
> times. This proves the analytical copy helps these full-history aggregates,
> not that DuckDB wins every query.

### 8. Knowledge check

1. **Why warm up?** First-use costs and cold pages should not become the claimed
   steady comparison.
2. **Why interleave?** Conditions can drift over time; alternating reduces one
   engine always benefiting from being later.
3. **How is 78.67× obtained?** `5832.15 / 74.13 ≈ 78.67` for that dashboard.

## Round 4 — Read the engine's work plan

### 1. Business problem

A timing tells us what happened; a plan helps explain how. If a factory manager
asks for total part value per team, the work is: read facts, keep needed fields,
form groups, sum prices, and return summaries.

### 2. Concept and miniature flow

```text
Parquet data → scan four columns → project 2,000,000 rows
             → hash groups and sums → 350 result rows
```

`EXPLAIN` normally shows a planned strategy. DuckDB `EXPLAIN ANALYZE` actually
runs the query and adds observed rows/times. SQLite `EXPLAIN QUERY PLAN` gives a
compact access description, not comparable per-operator runtime measurements.

### 3. Relevant implementation, line by line

```sql
EXPLAIN ANALYZE
SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM read_parquet('report_history.parquet')
GROUP BY machine_id, site, technician;
```

- `TABLE_SCAN READ_PARQUET` reads file column data.
- `Projections` lists only machine, site, technician, and price: column pruning.
- `PROJECTION` passes those values in the requested shape.
- `HASH_GROUP_BY` uses group keys to collect rows and applies `sum`.
- No filter or sort appears in this real query; inventing those operators would
  misdescribe the evidence.

### 4. Actual execution and result

Command: `uv run python -B Module06a/plan.py`.

**Measured plan:** 2,000,000 rows at DuckDB's scan and projection, four projected
columns, 350 rows after `HASH_GROUP_BY`, total wall time 0.0702 s. SQLite reports
`SCAN report_history` and `USE TEMP B-TREE FOR GROUP BY`.

Operator times can overlap across threads: the displayed 0.21 s scan and 0.22 s
group times must not be added and compared as a serial 0.43 s against 0.0702 s.

### 5. Why it makes sense and what can go wrong

The final answer is small, but every historical row can affect a total, so two
million input rows are necessary. A full scan is not automatically bad; for a
full-history aggregate it is appropriate. Mistakes include reading the plan
top-down as execution order (physical data flows bottom-up), confusing estimated
and actual figures, or claiming unshown filters and indexes.

### 6. Testing

The plan-capture test checks for `READ_PARQUET`, `HASH_GROUP_BY`, the four
projected names, two-million-row evidence, SQLite scan, and temporary B-tree.

### 7. One-minute professor explanation

> The plan shows why the result can be only 350 rows while the engine still
> processes two million. DuckDB reads four of seven Parquet columns, projects
> two million values, then hash-groups them into 350 totals. SQLite predicts a
> full table scan plus a temporary B-tree for grouping. The scan is appropriate
> because every historical row contributes; column pruning and analytical
> execution make that scan efficient.

### 8. Knowledge check

1. **Which operator reads the file?** `TABLE_SCAN` with `READ_PARQUET`.
2. **Why four columns?** The aggregate needs three group keys and one price;
   `job_id`, `part_no`, and `done_on` are unnecessary in this unfiltered plan.
3. **Why are 350 returned after reading two million?** `GROUP BY` collapses many
   input rows sharing keys into one summary per group.

## Round 5 — Measure where DuckDB loses

### 1. Business problem

Operational software repeatedly inserts one completed job or fetches one job by
ID. That differs from reading an entire warehouse report. The experiment asks
for 1,000 separate inserts and 1,000 separate primary-key lookups in each engine.

### 2. Concept and miniature example

Analytics is reading every folder to produce a yearly summary. A point lookup
is retrieving folder 12345 from a labeled cabinet. SQLite's primary-key structure
and low per-statement overhead fit the second task. DuckDB's vectorized strengths
cannot help much when Python sends one tiny request after another.

For IDs 0, 1, 2, the loop does three distinct calls:

```python
for i in range(3):
    con.execute("INSERT INTO s VALUES (?, ?, ?)", (i, f"k{i}", i * 1.5))
```

Iteration 0 inserts `(0,k0,0.0)`, iteration 1 inserts `(1,k1,1.5)`, and
iteration 2 inserts `(2,k2,3.0)`. The lookup loop asks for each ID separately.

### 3. Relevant implementation, line by line

Both engines create an in-memory table with `id` as the primary key. Timing
starts immediately before the 1,000-statement loop and stops afterward. Values
returned by all lookups are summed and checked, so a quick but wrong lookup
cannot win. Five runs alternate engine order, and medians are reported.

`executemany` is also tried. In these Python APIs it is repeated parameterized
execution, not necessarily one vectorized `INSERT ... SELECT` or Arrow bulk
load; the result must be measured rather than assumed.

### 4. Actual execution and result

Command: `uv run python -B Module06a/boundary.py --runs 5 --json`.

| Workload (1,000 statements) | SQLite median | DuckDB median | Measured winner |
|---|---:|---:|---|
| Row-by-row inserts | 3.30 ms | 6,549.83 ms | SQLite, DuckDB 1,987.33× slower |
| Primary-key lookups | 4.33 ms | 2,710.14 ms | SQLite, DuckDB 625.22× slower |

DuckDB `executemany` had a 6,917.59-ms insert median, slightly worse than its
row-by-row 6,549.83 ms here. That contradicts the provisional workbook's rough
expectation of an improvement, so the honest measured result is recorded.

### 5. Why it makes sense and what can go wrong

Repeated parser/binder/execution and client-call overhead dominates tiny DuckDB
statements. This experiment does not say DuckDB cannot ingest data efficiently;
bulk SQL, Arrow, or Parquet loading is a different workload. It also does not
prove all SQLite deployments are faster under concurrent server traffic.

Unfair mistakes include timing table creation for one engine only, omitting a
commit for one side, comparing different keys, or failing to verify returned
values. Here both databases are in memory and use equivalent primary keys.

### 6. Testing

The fast automated test uses a small equivalent workload to validate result
correctness and timing structure. The checked-in five-run evidence validates
sample counts, medians, and that the claimed winner follows from them.

### 7. One-minute professor explanation

> DuckDB was excellent for scanning two million rows but poor for 1,000 tiny
> requests. SQLite inserted them in 3.30 ms and looked them up in 4.33 ms;
> DuckDB needed 6,549.83 and 2,710.14 ms. Even Python `executemany` did not help
> in this environment. Therefore I keep row-at-a-time operational work in
> SQLite and do not generalize the analytical win to OLTP.

### 8. Knowledge check

1. **What is the boundary?** Repeated small inserts/lookups versus bulk scans.
2. **Does this prove DuckDB cannot bulk-load?** No; this measured repeated Python
   statements, not Arrow or a single set-based load.
3. **Why verify lookup sums?** Performance evidence is invalid if the engines
   did not return the intended values.

## Round 6 — Choose a hybrid architecture

### 1. Business problem

During a shift, workers record jobs and supervisors retrieve current records.
At month-end, controlling aggregates years of production. Running large reports
on an active source can compete for CPU, cache, I/O, and transaction resources;
SQLite locking details depend on journal and transaction mode, so we do not
claim every reader always blocks every writer.

### 2. Concept and architecture

```text
Operational SQLite
    → scripted snapshot after the shift
    → count/sum/date/null validation
    → atomic Parquet publication
    → DuckDB analytical queries
    → timestamped reports
```

SQLite remains authoritative for current, small operations. Parquet is a
snapshot; DuckDB reads it for large summaries. The arrow means a controlled
copy, not live two-way synchronization.

### 3. Miniature freshness example

Suppose SQLite has records through 14:00, but Parquet was built at 12:00. A
14:05 report may omit two hours. A **watermark**—the latest source timestamp or
snapshot version—lets readers see that limit. “Export completed” is not enough:
the new file could have missing rows or wrong values.

### 4. Refresh design, step by step

1. After the last shift, read a stable source snapshot.
2. Build new SQLite history/CSV/Parquet under temporary names.
3. Validate row count, price sum, ID sum, minimum/maximum dates, types, and nulls.
4. If every check passes, atomically replace the published Parquet and record
   its timestamp/watermark.
5. If any step fails, keep the last validated file, alert the report owner, and
   label its age. Never publish the partial output.

The portfolio scripts implement safe local build/validation behavior. Scheduling
and production alerting are an architectural proposal, not falsely claimed as
deployed infrastructure.

### 5. Actual evidence and decision

The decision uses both sides of the measurements:

- Full-history dashboard: 5,832.15 ms SQLite versus 74.13 ms DuckDB.
- Monthly: 7,013.05 ms versus 74.27 ms.
- 1,000 inserts: 3.30 ms SQLite versus 6,549.83 ms DuckDB.
- 1,000 lookups: 4.33 ms versus 2,710.14 ms.
- Default Parquet: 2,323,412 bytes. Zstandard: 1,367,276 bytes, 41.15%
  smaller with equivalent count/sum.
- Warm aggregate medians were 51.42 ms default and 53.44 ms Zstandard; better
  compression did not mean faster execution in this local run.

Therefore, reports move to DuckDB over Parquet; transactions stay in SQLite.
The seven-sentence [recommendation memo](recommendation.md) tells Lea and Yasmin
what moves, how it refreshes, and what happens when stale or failed.

### 6. What can go wrong and how it is tested

A stale snapshot can omit new production, an interrupted export can publish an
incomplete file, or a count-only validation can miss corrupted values. The
scripts use temporary outputs and multiple invariants before replacement.
Tests check that the memo quotes measured numbers, states the workload boundary,
defines validation, and explains failure behavior. Human scheduling/monitoring
would still need implementation in a real company.

### 7. One-minute professor explanation

> I recommend a hybrid design. SQLite stays the operational source because the
> row-at-a-time experiment was hundreds to thousands of times faster there.
> After the shift, a script builds and validates a Parquet snapshot, then DuckDB
> runs the full-history reports that were about 79 to 94 times faster. A new
> snapshot is published only after count, sums, dates, types, and nulls match.
> If refresh fails, we keep and timestamp the last valid copy instead of showing
> incomplete data.

### 8. Knowledge check

1. **What does freshness mean?** How current the snapshot is relative to source
   changes.
2. **What happens after a failed refresh?** Keep the previous validated snapshot,
   alert the owner, and disclose its timestamp; do not publish partial data.
3. **Why use both engines?** Their measured strengths match different workload
   shapes: SQLite for OLTP and DuckDB/Parquet for OLAP.
