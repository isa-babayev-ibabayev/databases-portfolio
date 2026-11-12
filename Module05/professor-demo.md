# Professor Demonstration — Round 5

## PowerShell commands

```powershell
$Portfolio = "C:\Users\HP\OneDrive - Azerbaijan Tourism and Management University\Desktop\databases-portfolio"
Push-Location $Portfolio
python --version
uv run python -B Module05/demo.py --round 5
Pop-Location
```

The demo creates a new database under Windows Temp, runs seven measurements per
scenario, restores the report index, closes the connection, and deletes the
database. It does not create `Module05/normalize.db`.

The reusable `Module05/normalize.db` is kept separately for the following
session. Confirm it and the DuckDB environment before class:

```powershell
uv sync
Test-Path Module05/normalize.db
uv run python -c "import duckdb; print(duckdb.__version__); print(duckdb.sql('SELECT 42').fetchone()[0])"
```

The single Round 5 command displays the required table counts, equivalent
dashboard timings, both dashboard plans, one-versus-4,000 update rows, `dbstat`
storage, and the indexed-versus-unindexed plans and timings. `Pop-Location`
returns PowerShell to the directory from which the demonstration started.

For the executable Round 2-5 demonstrations:

```powershell
uv run python -B Module05/demo.py --round all
```

For the automated suite:

```powershell
uv run python -B -m unittest discover -s Module05/tests -v
```

## What to point out

1. The environment and SQLite version appear first.
2. The counts must be 200,000 flat/report/job-part rows, 20,000 jobs, 50
   machines, and 10 parts.
3. Round 5 must show one normalized row and 4,000 denormalized rows affected.
4. `dbstat` should print bytes and KB. If unavailable, the demo says so rather
   than inventing values.
5. The indexed plan should name `ix_report_machine`; the unindexed plan should
   say `SCAN report_jobpart` without that index.
6. Timings will differ from the saved results, but every scenario must have at
   least five positive samples and a median.
7. The final lines must confirm rollback, index restoration, and temporary-file
   removal.

## 60–90 second explanation

I kept the transactional data normalized so each machine site and part price is
stored once. I also built a 200,000-row report table that repeats those values
for dashboard reads. In Round 5, changing `cnc-02` updated one machine row but
4,000 report rows. The report table used 10,832 KB, compared with 3,976 KB for
the normalized base tables. On my saved run, the indexed report query was
slower than the normalized join, but removing the unsuitable machine index made
the report faster. This shows that denormalization and indexing are workload
decisions, not automatic improvements. I would keep 3NF as the source of truth
and rebuild the report in a controlled refresh.

## 3–5 minute explanation

First, I created a flat 200,000-row job-part relation and decomposed it into
machine, part, job, and job-part tables. The normalized design stores a machine
site once and stores each part price once. I checked both directions with
`EXCEPT`, so the normalized join reconstructs the same data.

For the dashboard, I created `report_jobpart`. It copies the site, technician,
and price onto every report row. Both dashboard queries return the same 350
groups, which is important because a faster wrong query would not be useful.

Round 5 measures the cost of that copied data. I update `cnc-02` inside a
transaction and roll it back after every measurement. The normalized statement
changes one row. The report statement changes 4,000 rows because every job-part
row for the machine contains another copy of the site.

I use SQLite `dbstat` for table storage. The normalized base tables used 3,976
KB, while the report table used 10,832 KB without indexes. This is the storage
cost of redundancy.

The saved dashboard medians were 121.0052 ms for the normalized join and
151.9686 ms for the indexed report. The report index caused a complete index
scan plus table lookups. After I dropped it, SQLite used one table scan and the
median improved to 112.1664 ms. These values can change on another computer,
but the plans and raw samples explain the result.

My conclusion is to keep the normalized tables as the source of truth. A report
snapshot can be useful for a frequent dashboard, but it must be refreshed after
source changes. This project proposes a controlled rebuild; it does not claim
that automatic synchronization is already implemented.

## Likely questions and answers

1. **What is normalization?** It separates facts so each dependency is stored
   with the key that determines it.
2. **What is denormalization?** It deliberately copies facts into a read model
   to simplify a workload.
3. **Why use 3NF?** It prevents partial and transitive dependencies from causing
   update, insert, and delete anomalies.
4. **Why does the normalized update affect one row?** Site is stored once in
   `machine`.
5. **Why does the report update 4,000 rows?** That site is copied to all 4,000
   job-part rows belonging to `cnc-02`.
6. **Why might a report query be faster?** It can avoid joins and use a layout
   tailored to one read path.
7. **Why was the indexed report slower here?** The query needed much of the
   table, so walking the full index and fetching table columns cost more than a
   sequential scan.
8. **What does `EXPLAIN QUERY PLAN` show?** It shows scans, targeted searches,
   chosen indexes, join order, and temporary structures.
9. **How was storage measured?** With `dbstat`, summing pages for explicitly
   named objects and reporting whether indexes were included.
10. **How would the report stay synchronized?** This recommendation uses a
    controlled transactional rebuild after relevant changes or on a schedule.
11. **What if a machine changes site?** The report is stale until refreshed;
    that is why it cannot be the source of truth.
12. **Why do timings differ on another laptop?** CPU, cache, storage, SQLite
    version, planner choices, and background work affect latency.
13. **Why does `part` contain 10 rows?** `k` runs only from 1 to 10, producing
    part numbers 2 through 11.
14. **What is the Industrial Engineering trade-off?** Reliable transactional
    maintenance data favors normalized integrity, while frequent operational
    dashboards may justify a controlled reporting copy.

## Troubleshooting

- **`python` is not recognized:** use `uv run python` from the repository, or
  install/configure Python separately before the demonstration.
- **SQLite CLI is missing:** the demo uses Python's standard `sqlite3`; no CLI
  is required.
- **Database does not exist:** this is expected. The demo creates a disposable
  one automatically.
- **Plan differs:** record `sqlite3.sqlite_version`, verify the index state, and
  explain that planner decisions vary by version and statistics.
- **`dbstat` is unavailable:** report storage as unavailable; keep row-count and
  update evidence. Do not invent bytes.
- **Benchmark numbers differ:** compare plans and medians, not one exact timing.
- **Command is run twice:** every run uses a fresh Temp directory, so rerunning
  is safe.
- **Temporary database cannot be recreated:** close programs holding old SQLite
  files and rerun; do not delete unrelated repository files.
