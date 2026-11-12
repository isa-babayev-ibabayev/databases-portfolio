# Round 5 boundary results

Run on 2026-11-12. Each value below is the median of five measured runs of
1,000 inserts followed by 1,000 primary-key lookups. SQLite and DuckDB order
alternated by trial; every returned value was checked.

| Engine/method | Insert median | Lookup median |
|---|---:|---:|
| SQLite, row by row | 3.30 ms | 4.33 ms |
| DuckDB, row by row | 6,549.83 ms | 2,710.14 ms |
| DuckDB, Python `executemany` | 6,917.59 ms | 2,751.70 ms |

DuckDB was 1,987.33× slower for the row-by-row inserts and 625.22× slower for
the point lookups on this machine. Contrary to the provisional workbook's
approximate expectation, Python `executemany` did not improve the DuckDB median
in this run (0.947×, meaning slightly slower). That is an honest environment-
specific finding: this API still issues a parameterized statement for every
row and is not equivalent to a bulk `INSERT ... SELECT`, Arrow import, or
Parquet load.

This is the measured boundary: keep request-per-row transactional writes and
point lookups in SQLite; use DuckDB for bulk analytical scans.
