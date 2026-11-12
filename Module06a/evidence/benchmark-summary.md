# Round 3 benchmark summary

Run on 2026-11-12 with Python 3.14.5, SQLite 3.50.4, DuckDB 1.5.6,
and Windows 11. Each engine received one untimed warm-up per workload. Five
timed runs were interleaved with the first engine alternating by trial, every
query was fully fetched, and medians—not a single run—are reported.

| Workload | Result groups | SQLite median | DuckDB median | DuckDB speed-up | SQLite range | DuckDB range |
|---|---:|---:|---:|---:|---:|---:|
| Dashboard | 350 | 5,832.15 ms | 74.13 ms | 78.67× | 5,563.32–5,862.72 ms | 58.02–86.32 ms |
| Monthly | 1,500 | 7,013.05 ms | 74.27 ms | 94.43× | 6,592.70–7,795.07 ms | 61.15–79.86 ms |

The result sets were compared after normalizing harmless floating-point
representation and were equivalent for both workloads. The detailed samples
and run order are in [benchmark-results.csv](benchmark-results.csv).

## Workbook query correction

The provisional workbook writes `strftime(done_on, '%Y-%m')` once and sends it
to both engines. That is DuckDB's argument order; SQLite requires
`strftime('%Y-%m', done_on)`. Unchanged, the workbook expression silently
returns `NULL` months in SQLite and compares different aggregates. `race.py`
therefore uses the engine-specific spellings of the same year-month operation.
This correction is necessary for the claimed same-data, same-result race.
