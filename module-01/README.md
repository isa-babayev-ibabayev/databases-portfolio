
# Module 01 — Introduction & Local-First Foundations

## Learning Goals

### Learning Goal 1 — Understand how the class works

**Learning goal:** Explain how this class works — the CBL/PBL philosophy, the portfolio-based **project work** assessment, and the "moving bar" of a first-time course.

**Evidence:**
- [Portfolio README](../README.md) — documents the module-based portfolio and its practical learning purpose.
- [Module 1 reflection](reflection.md) — records learning through practical database work and reflection.

**Evidence gap:** The existing portfolio does not contain a dedicated explanation of CBL/PBL, the assessment structure, or the "moving bar."

### Learning Goal 2 — Set up a safe GitHub portfolio

**Learning goal:** Set up your personal GitHub portfolio from the course template, with a clean first commit and a `.gitignore` that keeps databases and secrets out of Git.

**Evidence:**
- [Portfolio README](../README.md) — shows the personalized HSBI Databases portfolio structure and module links.
- [.gitignore](../.gitignore) — excludes databases, generated data, virtual environments, caches, and `.env` secrets.
- [Initial portfolio commit](https://github.com/isa-babayev-ibabayev/databases-portfolio/commit/1b4dabc1a35eb0a7b19ee6cd6458ff862b69590f) — records the clean starting structure.

### Learning Goal 3 — Build a reproducible database toolchain

**Learning goal:** Set up the entire toolchain reproducibly with **`uv`** — one fixed Python plus SQLite, DuckDB, Datasette, and more — on Windows, macOS, or Linux, and verify it.

**Evidence:**
- [Dependency configuration](../pyproject.toml) — declares Python and the required database tools.
- [Environment lockfile](../uv.lock) — locks resolved dependency versions for reproducible installation.
- [Tool verification output](uv-check-output.txt) — records the Python, SQLite, DuckDB, Datasette, sqlite-utils, Pydantic, and SQLAlchemy versions.

### Learning Goal 4 — Compare embedded and client/server databases with measurements

**Learning goal:** Explain — with a measurement, not a slide — the difference between an **embedded** database and a **client/server** database, and why most local apps should not run a server.

**Evidence:**
- [Telemetry analysis](telemetry-analysis.md) — compares SQLite with a client/server database using the measured row count, database size, and query times.
- [Recorded telemetry query results](telemetry-query-results.txt) — contains the executed query outputs and measured timings.

### Learning Goal 5 — Load and query real SQLite data with bound parameters

**Learning goal:** Load real rows into SQLite and query them from Python using **bound parameters**.

**Evidence:**
- [Python telemetry loader](load_telemetry.py) — creates the SQLite table and loads real CSV rows with five `?` bound parameters.
- [Telemetry queries](telemetry-queries.sql) — contains the SQL used to aggregate and filter the imported rows.
- [Recorded telemetry query results](telemetry-query-results.txt) — proves the queries executed against 172,800 imported rows.

**Scope note:** Bound parameters are directly evidenced for Python ingestion; the committed analytical `SELECT` queries are SQL files, not parameterized Python `SELECT` calls.

### Learning Goal 6 — Verify LLM-generated SQL before trusting it

**Learning goal:** Take a first LLM-generated query, run it, and begin the habit that defines this course: **verify before you trust**.

**Evidence:**
- [AI-generated SQL](task7-ai-query.sql) — preserves the query that was tested.
- [AI verification report](task7-ai-verification.md) — records the prompt, results, boundary checks, limitations, and verification reasoning.
- [Query-plan output](task7-plan.txt) — proves that `EXPLAIN QUERY PLAN` was used to inspect execution.

## What I Plan to Explore

I want to learn how databases work, how to write SQL queries, and how SQLite can be used to analyze industrial production data.

## Practical Tasks

- [ ] Task 1 — Portfolio setup
- [ ] Task 2 — Git and Markdown
- [ ] Task 3 — Install database tools
- [ ] Task 4 — SQLite shell
- [ ] Task 5 — SQL Island
- [ ] Task 6 — Machine telemetry
- [ ] Task 7 — AI-assisted SQL verification

## Evidence and Results

I will add screenshots, commands, query results, and explanations as I complete the tasks.

## Reflection

I will describe what I learned, what problems I encountered, and how I verified my results.

## Task Pod and useful links

### My Task Pod

- Task Pod member: [Tunay Daldaban](https://github.com/tunaydaldaban-beep/databases-portfolio)
- We plan to compare our database exercises and review each other's SQL queries.

### Course and portfolio links

- [My portfolio homepage](../README.md)
- [Official course syllabus](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/syllabus.md)
- [Official Module 1 workbook](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/01-introduction-and-local-first.md)
- [My toolchain verification script](../uv-check.py)
- [My toolchain verification results](uv-check-output.txt)

### Contributions and peer review

**My completed work:** I created and configured my personal GitHub portfolio, installed the required database software, and verified the Python 3.14 environment.

**Pod collaboration:** We will document each person's contributions as we complete the practical database exercises.

**Peer review:** To be recorded after we review each other's SQL queries and results.

## Task 4 - SQLite shell reflection

I found the `.dump` command especially useful because it exports a database into SQL statements, allowing me to rebuild the database without uploading the original database file.

I also learned that `.tables` lists tables, `.schema` displays their structure, and `.timer on` measures query execution time.

For my CNC vibration example, the highest measurements were 1.2 for cnc-01 and 2.4 for cnc-02. My first timed query took approximately 0.0277 seconds.

## Task 5 - SQL Island

I completed the SQL Island learning game and received a Certificate of Completion.

[Read my SQL Island reflection and view my certificate](sql-island.md)

## Task 6 - CNC Telemetry Database

I generated and analyzed 172,800 CNC measurements using Python and SQLite.

[Read my Task 6 analysis and query results](telemetry-analysis.md)

## Task 7 - AI-Assisted SQL Verification

I generated, executed, profiled, and verified a SQL query using ChatGPT.

[Read my Task 7 verification report](task7-ai-verification.md)

## Final Module 1 Reflection

[Read my final reflection](reflection.md)
