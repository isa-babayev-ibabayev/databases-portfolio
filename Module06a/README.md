# Module 6a — The Analytical Engine (DuckDB)

This module moves a two-year-style reporting workload from the operational
SQLite design into a reproducible Parquet snapshot queried by DuckDB. It uses
the [current official workbook](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/06a-duckdb-analytical-engine.md)
from `iotempire-teaching`; learning goals above
the workbook's draft boundary are authoritative, while the six-round procedure
below that boundary is explicitly provisional. The implementation records the
revision re-inspected on 2026-11-17 and flags one cross-engine `strftime`
compatibility correction instead of silently comparing different answers.

## Initial audit

| Requirement | Initial evidence | Initial status | Action taken |
|---|---|---|---|
| Module 5 source | `Module05/normalize.db`, `report_jobpart` | 200,000 readable rows | Hash, count, sum, dates, and preservation checked |
| Module 6a directory | None | Missing | Added scripts, notes, evidence, tests, and guide |
| Environment | `uv.lock`, `pyproject.toml` | DuckDB dependency present | `uv sync`; versions recorded |
| Generated-file rules | Repository-wide `*.db` and `*.parquet` | CSV rule missing | Added narrow `Module06a/*.csv` ignore rule |
| Git state | `main` tracking `origin/main`; unrelated `main.py` untracked | Understood | Preserved and excluded from this work |

The Module 5 source SHA-256 before and after generation was
`BCCCA944EEBFF2C42D18DA737F251587CAFB6EB93D84E561D1FCE9BEA6BA4C3D`.
The detailed starting record is [pre-session-audit.txt](evidence/pre-session-audit.txt).
The later requirement-by-requirement review is in
[comprehensive-audit.md](evidence/comprehensive-audit.md).

## Evidence map

| Round | Reproducible implementation | Recorded evidence | Verified result |
|---|---|---|---|
| 1 — Build | [prepare.py](prepare.py) | [history-validation.txt](evidence/history-validation.txt) | 200,000 × 10 = 2,000,000 rows; source unchanged |
| 2 — Convert | [to_parquet.py](to_parquet.py) | [parquet-validation.txt](evidence/parquet-validation.txt) | Same count, sums, ID checksum, dates, and null counts |
| 3 — Race | [race.py](race.py) | [samples](evidence/benchmark-results.csv), [summary](evidence/benchmark-summary.md) | DuckDB 78.67× and 94.43× faster for the two aggregates |
| 4 — Plan | [plan.py](plan.py) | [query-plan.txt](evidence/query-plan.txt) | Four projected columns, 2,000,000 scanned rows, 350 groups |
| 5 — Boundary | [boundary.py](boundary.py) | [boundary-results.md](evidence/boundary-results.md) | SQLite wins 1,000 row-at-a-time inserts and lookups |
| 6 — Decide | [recommendation.md](recommendation.md) | [compression result](evidence/compression-results.txt) | SQLite for operations; DuckDB + Parquet for reporting |
| 7 — Core homework | [compression.py](compression.py), [recommendation.md](recommendation.md) | [compression result](evidence/compression-results.txt) | Zstandard copy plus refresh/failure decision |
| Intense track (optional) | [refresh.py](refresh.py) | [two runs and checks](evidence/refresh-results.txt) | Safe direct-history refresh and mismatch exit code 1 |
| S1 JSON (optional) | [json_read.py](json_read.py) | [JSON join result](evidence/json-results.txt) | Three UTF-8 device rows joined to history |
| S2 statistics (optional) | [parquet_stats.py](parquet_stats.py) | [row-group result](evidence/parquet-statistics-results.txt) | Candidate groups 17 → 2; measured selective query |

The detailed beginner explanation is in [learning-guide.md](learning-guide.md),
and the round-by-round laboratory record is in
[duckdb-notes.md](duckdb-notes.md).

The final automated run completed **21 tests in 27.386 seconds, all passing**;
see [test-results.txt](evidence/test-results.txt).

## Reproduce the work in PowerShell

Start in the actual portfolio directory:

```powershell
Set-Location "C:\Users\HP\OneDrive - Azerbaijan Tourism and Management University\Desktop\databases-portfolio"
uv sync

# Round 1: safely validate existing outputs, or create them when absent.
uv run python -B Module06a/prepare.py

# Round 2: safely validate existing Parquet, or create it when absent.
uv run python -B Module06a/to_parquet.py

# Round 3: two equivalent queries, warm-ups, five interleaved trials.
uv run python -B Module06a/race.py --runs 5 --json

# Round 4: measured DuckDB plan and descriptive SQLite access plan.
uv run python -B Module06a/plan.py

# Round 5: five trials of the 1,000-statement OLTP boundary.
uv run python -B Module06a/boundary.py --runs 5 --json

# Core homework: make and compare the Zstandard Parquet copy.
uv run python -B Module06a/compression.py

# Optional intense track: rebuild from history.db, then check read-only.
uv run python -B Module06a/refresh.py
uv run python -B Module06a/refresh.py --check

# Optional S1: create UTF-8 devices.json and run the Parquet join.
uv run python -B Module06a/json_read.py

# Optional S2: create/reuse sorted.parquet and compare date filtering.
uv run python -B Module06a/parquet_stats.py --runs 5

# Automated verification (does not repeat the long performance race).
uv run python -B -m unittest discover -s Module06a/tests -v
```

Open the guide with `Get-Content Module06a/learning-guide.md`, or read it on
GitHub with rendered tables and headings.

## Safe rebuild and recovery

Normal runs validate and reuse an existing `history.db`, CSV, or Parquet; they
do not delete it. Use `--rebuild` only when a deliberate rebuild is required:

```powershell
uv run python -B Module06a/prepare.py --rebuild
uv run python -B Module06a/to_parquet.py --rebuild
```

The scripts first build a `.new` file, fully validate it, preserve the prior
output as a timestamped ignored backup, and only then replace the published
file. If a run stops halfway, inspect the `.new` file; do not rename it over the
last valid snapshot. Remove or archive an abandoned `.new` file only after
checking it, then rerun. `normalize.db` is opened read-only and is never a
rebuild target.

`refresh.py` is the implemented intense-track pipeline. Its normal mode writes
a unique temporary Parquet from read-only `history.db`, validates logical
summaries and schema, then replaces the published snapshot. `--check` is
read-only and exits 1 on mismatch. Matching summaries catch incomplete or
mis-shaped refreshes but cannot prove every individual value is identical.
`json_read.py` creates `devices.json`; `parquet_stats.py` creates
`sorted.parquet` only when no reusable validated copy exists. Both outputs are
derived and ignored.

## What is and is not in Git

Source code, tests, notes, the memo, and compact evidence are tracked. The
generated `history.db`, source CSV, default, Zstandard, and sorted Parquet
files, refresh temporaries, data backups, and `devices.json` are ignored. A
podmate can recreate them from the scripts and the Module 5 source.

## Important compatibility finding

The provisional workbook gives `strftime(done_on, '%Y-%m')` to both engines.
DuckDB accepts that order; SQLite expects `strftime('%Y-%m', done_on)` and
otherwise returns `NULL`. [race.py](race.py) uses each engine's correct spelling
of the same year-month calculation, then checks all result groups before any
timing is accepted. This is a necessary semantic correction, not a changed
business question.

## Academic status

All six technical rounds, core Zstandard homework, intense-track refresh, and
three optional stretchers are implemented and recorded. The six nearest-pod
discussions and a personal reflection remain
student classroom actions; no conversation or personal reaction has been
invented. [ref06a.md](../Reflections/ref06a.md) is therefore a truthful draft
structure with technical facts and explicit student-input placeholders.
