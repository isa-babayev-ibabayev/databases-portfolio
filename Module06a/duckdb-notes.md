# Module 6a laboratory notes

Official source re-inspected on 2026-11-17: `06a-duckdb-analytical-engine.md` on
the `main` branch of `iotempire/iotempire-teaching`. Its five learning goals
are above an explicit draft boundary; the six-round studio instructions below
that boundary are provisional. These notes distinguish executed evidence from
predictions and do not claim classroom conversations.

## Round 1 — Build

- **Objective:** Stretch Module 5's 200,000 `report_jobpart` rows into ten
  91-day-shifted periods in SQLite, while exporting only the original 200,000
  rows to CSV as the workbook specifies.
- **Technical expectation (not a student classroom prediction):** 2,000,000 history rows, price sum
  21,000,000, ten equal periods, and an unchanged source hash.
- **Command:** `uv run python -B Module06a/prepare.py`
- **Actual result:** 2,000,000 rows; price sum 21,000,000; dates 2026-01-01 to
  2028-06-27; ten periods of 200,000; 112,685,056-byte database; 200,000-row,
  10,805,002-byte CSV; no null or malformed dates; integrity `ok`; source hash
  unchanged.
- **Unexpected finding:** Fixed 91-day blocks do not start immediately after
  the previous block's final source date: a 90-day inclusive source range plus
  a 91-day shift leaves one calendar date between blocks. This follows the
  official arithmetic rather than inventing a calendar-quarter rule.
- **Additional experiment:** From 2025-01-31, SQLite returned 2025-05-01 for
  `+90 days`, 2025-05-02 for `+91 days`, and 2025-03-03 for `+1 month`.
  Calendar-month rollover is not the same as a fixed number of days.
- **Learned:** One source row is paired with every `k` from 0 through 9;
  changing `job_id` and `done_on` separates periods while the reporting
  dimensions remain comparable.
- **Nearest-pod question:** Why is 200,000 × 10 multiplication rather than
  adding ten rows, and what would a 90-day shift overlap?
- **Actual discussion:** Pending — genuine student/pod discussion required.

## Round 2 — Convert

- **Objective:** Use DuckDB to read the 200,000-row CSV, repeat it ten times,
  and write a typed 2,000,000-row Parquet file without loading it all into a
  Python list.
- **Technical expectation (not a student classroom prediction):** Parquet count, price sum, ID sum, and date
  range will equal SQLite, and the file will be much smaller because repeated
  column values compress well.
- **Command:** `uv run python -B Module06a/to_parquet.py`
- **Actual result:** 2,000,000 rows; price sum 21,000,000; job-ID sum
  9,020,001,000,000; matching dates; zero nulls; typed `DATE` and `DOUBLE`;
  2,323,412 bytes versus 112,685,056 bytes for SQLite.
- **Unexpected finding:** The CSV is 10,805,002 bytes but contains only 200,000
  source rows; comparing its size directly with the two-million-row files
  without this warning would be misleading.
- **Learned:** DuckDB is the engine doing the work; Parquet is the persistent
  columnar file. Count alone is weak evidence, so validation also uses sums,
  dates, schema, and null counts.
- **Nearest-pod question:** If two files have the same row count, what other
  checks would convince us they contain the same data?
- **Actual discussion:** Pending — genuine student/pod discussion required.

## Round 3 — Race

- **Objective:** Compare the same two aggregates over equivalent data using
  warm-ups, five interleaved runs, full result fetching, medians, and output
  checks.
- **Technical expectation (not a student classroom prediction):** DuckDB should win the full scans because it
  reads only needed Parquet columns and uses vectorized analytical execution;
  no numerical ratio was assumed in advance.
- **Command:** `uv run python -B Module06a/race.py --runs 5 --json`
- **Actual result:** Dashboard: SQLite 5,832.15 ms, DuckDB 74.13 ms, 78.67×.
  Monthly: SQLite 7,013.05 ms, DuckDB 74.27 ms, 94.43×. Both outputs matched.
- **Unexpected finding:** The workbook's shared monthly expression is not
  portable. DuckDB uses `strftime(date, format)`, SQLite uses
  `strftime(format, date)`. The original expression produces NULL months in
  SQLite, so the script uses equivalent engine-specific syntax.
- **Learned:** A fast number is meaningless until the answers match. Alternating
  the first engine by trial reduces systematic run-order bias; the spread shows
  that machine noise remains.
- **Nearest-pod question:** What workload or filter could let an indexed SQLite
  lookup beat a complete Parquet scan?
- **Actual discussion:** Pending — genuine student/pod discussion required.

## Round 4 — Plan

- **Objective:** Explain the aggregate with a measured DuckDB plan and compare
  it with SQLite's access-plan description.
- **Technical expectation (not a student classroom prediction):** DuckDB should show `READ_PARQUET`, four
  projected columns, two million input rows, and hash grouping; SQLite should
  show a table scan and temporary grouping structure.
- **Command:** `uv run python -B Module06a/plan.py`
- **Actual result:** DuckDB scanned/projected 2,000,000 rows from four columns
  and `HASH_GROUP_BY` produced 350 groups; total wall time was 0.0702 s in this
  plan run. SQLite reported `SCAN report_history` and `USE TEMP B-TREE FOR GROUP
  BY`.
- **Unexpected finding:** DuckDB's parallel operator times (0.21 s scan and
  0.22 s group) exceed the 0.0702 s wall time because operator timing can sum
  work across threads; these values must not be added as a serial timeline.
- **Learned:** Returning 350 rows does not mean only 350 rows were processed.
  A complete analytical scan can be the correct plan.
- **Nearest-pod question:** Which plan line proves the number of input rows and
  which line proves column pruning?
- **Actual discussion:** Pending — genuine student/pod discussion required.

## Round 5 — Boundary

- **Objective:** Measure a workload DuckDB is not designed for: 1,000 separate
  inserts and 1,000 separate primary-key lookups.
- **Technical expectation (not a student classroom prediction):** SQLite should win row-at-a-time work; the
  workbook predicts DuckDB `executemany` will improve but not close the gap.
- **Command:** `uv run python -B Module06a/boundary.py --runs 5 --json`
- **Actual result:** SQLite medians: 3.30 ms insert, 4.33 ms lookup. DuckDB:
  6,549.83 ms and 2,710.14 ms—1,987.33× and 625.22× slower. DuckDB
  `executemany` insert median was 6,917.59 ms.
- **Unexpected finding:** `executemany` was 0.947× relative to row-by-row, so it
  was slightly slower here. It still performs repeated parameterized work and
  is not a columnar bulk import; the recorded evidence overrides an approximate
  workbook expectation.
- **Learned:** Engine choice follows workload shape. Analytical scans and
  request-per-row operations have different overheads.
- **Nearest-pod question:** What would the application need to change to turn
  1,000 individual writes into a true bulk load?
- **Actual discussion:** Pending — genuine student/pod discussion required.

## Round 6 — Decide

- **Objective:** Give Lea Winter and Yasmin Kaya a 6–8 sentence, measured
  recommendation covering placement, refresh, staleness, and failure.
- **Technical expectation (not a student classroom prediction):** The hybrid boundary will keep SQLite as the
  operational source and publish a validated Parquet snapshot for DuckDB.
- **Command:** The memo is documentation derived from the prior commands;
  `uv run python -B Module06a/compression.py` supplies the core-homework size
  evidence.
- **Actual result:** [recommendation.md](recommendation.md) contains seven
  sentences and the actual aggregate, boundary, and file-size numbers. Zstandard
  reduced Parquet from 2,323,412 to 1,367,276 bytes (41.15%) while preserving
  count and sum; its warm query median was 53.44 ms versus 51.42 ms default.
- **Unexpected finding:** Better compression was slightly slower for this warm
  local query. Storage saving and query latency are separate decisions.
- **Learned:** Publish a new snapshot only after validation; on failure keep
  the last valid snapshot, alert the owner, and expose its timestamp rather
  than silently publishing incomplete data.
- **Nearest-pod question:** If the copy is one day old, which decisions are
  unsafe and how should the report warn its reader?
- **Actual discussion:** Pending — genuine student/pod discussion required.

## Task 7 — Core homework and optional intense-track refresh

- **Goal:** Keep the required Zstandard result and turn the proposed refresh
  into a safe, checkable script that rebuilds from `history.db`.
- **Commands:** `uv run python -B Module06a/refresh.py` twice, followed by
  `uv run python -B Module06a/refresh.py --check`.
- **First run:** 2,000,000 rows, logical checksum
  `C15A57C2CA9D078BEB2F7A303CBA295644340F964D4713A5E00D5153C8E5C544`,
  2,468,865 bytes, 3,414.89 ms.
- **Second run:** the same rows, checksum, and bytes in 3,219.00 ms. Logical
  idempotence was demonstrated; byte identity is not required by the workbook.
- **Read-only check:** SQLite and Parquet both reported 2,000,000 rows and
  price sum 21,000,000.00; exit code 0.
- **Deliberate failure:** a disposable two-row SQLite and one-row Parquet
  produced `CHECK FAIL` and exit code 1. A separate injected-failure test proved
  the previous published file remains unchanged when candidate validation fails.
- **What the check proves:** It compares count, price and ID sums, date limits,
  nulls, column names, and types, then hashes the normalized summary.
- **What it cannot prove:** Two datasets can share all summaries while differing
  in individual values; a production pipeline could add row-level hashes or
  source-to-target reconciliation for stronger assurance.
- **Core compression recheck:** After direct-history refresh, default Parquet
  was 2,468,865 bytes and Zstandard was 1,447,194 bytes (41.38% smaller), with
  equivalent count and sum.
- **Remaining issue:** Scheduling and alert delivery are architectural proposals,
  not a deployed service.

## Optional stretcher S1 — DuckDB reads JSON

- **Command:** `uv run python -B Module06a/json_read.py`
- **Actual result:** Three UTF-8 device records joined to `cnc-01`, `cnc-02`,
  and `cnc-03`. Each matched 40,000 historical rows and price sum 420,000.00.
- **Learned:** DuckDB can join file formats directly, but this small generated
  metadata file does not replace Module 6b's integrity discussion.
- **Discussion status:** Pending — genuine student/pod discussion required.

## Optional stretcher S2 — Parquet statistics and sorting

- **Command:** `uv run python -B Module06a/parquet_stats.py --runs 5`
- **Actual result:** Every one of 17 unsorted row groups spanned the complete
  date range. Sorting narrowed the one-month filter to two candidate groups.
- **Measured medians:** After one discarded warm-up per file and five trials
  with alternating first-file order, 12.5175 ms unsorted and 5.7473 ms sorted
  for 69,020 rows totaling 724,710.00, about 2.18× faster in this run.
- **Trade-off:** The sorted file grew from 2,468,865 to 6,508,574 bytes because
  date ordering disrupted compression patterns in other columns.
- **Limitation:** This demonstrates useful statistics for one filter on this
  laptop; it is not a universal index replacement or speed guarantee.
- **Discussion status:** Pending — genuine student/pod discussion required.

## Optional stretcher S3 — Compression

- **Command:** `uv run python -B Module06a/compression.py`
- **Current result:** 2,468,865-byte default versus 1,447,194-byte Zstandard,
  with equal 2,000,000 rows and price sum 21,000,000.00. Warm aggregate medians
  were 29.9520 and 33.0436 ms, so the smaller file was slightly slower here.
- **Historical evidence:** The original Task 2 write path produced 2,323,412
  and 1,367,276 bytes. Both result sets are retained and clearly dated.
- **Discussion status:** Pending — genuine student/pod discussion required.
