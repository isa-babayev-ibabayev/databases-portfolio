# Module 5 — Normalization vs. Denormalization Benchmarking Studio

## Learning goals

1. Derive functional dependencies and candidate keys.
2. Explain and implement 1NF, 2NF, and 3NF.
3. Denormalize deliberately for a reporting workload.
4. Measure query latency, update amplification, storage, and index effects.
5. Recommend and defend a schema for an industrial workload.

## Module 5 — Group Members and Contributions

These are the members who participated in this Module 5 pod assignment. The allocation is based
on the student's supplied group document and describes the shared assignment's division of work;
it does not claim that every member co-authored every file in this personal portfolio.

| Group member | GitHub | Documented contributions |
|---|---|---|
| Isa Babayev | [GitHub portfolio](https://github.com/isa-babayev-ibabayev/databases-portfolio) | Round 1 functional dependencies; Round 5 price, update, query, storage, and index measurements; Round 6 recommendation |
| Rayan Slassi | [GitHub portfolio](https://github.com/rayansls/Databases) | Round 1 LLM FD comparison; Round 3 build; Round 4 race, database, and performance work |
| Arshia Ziaee | [GitHub profile](https://github.com/Arshia-zi) | ER sketches, with Asmin |
| Asmin Metin | [GitHub portfolio](https://github.com/asminmetin/databases-portfolio) | ER sketches, with Arshia |

Tunay was absent for this Module 5 session and is not credited with these contributions. Group
membership in other course modules is separate.

Published academic documentation:

- [Module 5 Group Discussion Notes](group-discussion-notes.md)
- [My Reflection 05](../Reflections/ref05.md)
- [Group Document Technical Cross-check](group-document-technical-crosscheck.md)
- [Normalization Notes](normalization-notes.md)
- [Recommendation](recommendation.md)
- [Reflection Preparation Report](reflection-preparation-report.md)
- [Professor Demonstration](professor-demo.md)

## What this module builds

The professor's generator creates 20,000 jobs with 10 parts each: 200,000 flat
job-part rows. [`setup.sql`](setup.sql) decomposes them into `machine`, `part`,
`job`, and `job_part`, then builds a 200,000-row `report_jobpart` table. The
reusable classroom database is `Module05/normalize.db`. Demonstrations still
create separate disposable databases under Windows Temp so they cannot modify
that preserved copy.

Recorded environment: Python 3.14.5, SQLite 3.50.4, Windows 11. The Module 5
benchmark scripts use only Python's standard library, so the SQLite CLI is
optional; DuckDB is installed separately for Module 6a.

`normalize.db` is intentionally ignored by the repository-wide `*.db` rule and
is preserved locally rather than committed as a 35.4 MiB binary. If it is
missing, rebuild it from the repository root with the exact checked-in setup:

```powershell
uv run python -B -c "import sys; sys.path.insert(0, 'Module05'); from experiment import build_database; c=build_database('Module05/normalize.db'); c.close()"
```

Do not run that command over an existing database. The pre-session database and
environment verification is recorded in
[`evidence/pre-session-verification.txt`](evidence/pre-session-verification.txt).

## Evidence map

| Round | Implementation | Executed evidence |
|---|---|---|
| 1 — See it | [`normalization-notes.md`](normalization-notes.md), [`group-document-technical-crosscheck.md`](group-document-technical-crosscheck.md) | FD analysis, two Mermaid ER diagrams, and group-document discrepancy check |
| 2 — Break it | [`anomalies.sql`](anomalies.sql), [`experiment.py`](experiment.py) | [`evidence/anomaly-results.txt`](evidence/anomaly-results.txt) |
| 3 — Build it | [`setup.sql`](setup.sql) | [`evidence/row-counts.txt`](evidence/row-counts.txt) |
| 4 — Race it | [`reporting.sql`](reporting.sql), [`benchmark.py`](benchmark.py) | [`evidence/benchmark-results.csv`](evidence/benchmark-results.csv), [`evidence/query-plans.txt`](evidence/query-plans.txt) |
| 5 — Price it | [`experiment.py`](experiment.py), [`demo.py`](demo.py) | [`evidence/benchmark-summary.md`](evidence/benchmark-summary.md), [`evidence/update-results.txt`](evidence/update-results.txt), [`evidence/storage-results.txt`](evidence/storage-results.txt) |
| 6 — Decide | [`recommendation.md`](recommendation.md) | Memo citing measured results |
| 7 — Harvest | [`normalization-notes.md`](normalization-notes.md#round-7--prepared-curiosities), [`group-discussion-notes.md`](group-discussion-notes.md) | Prepared curiosities and supplied general discussion; exact curiosity swap not documented |

Machine-readable evidence is in
[`evidence/benchmark-results.json`](evidence/benchmark-results.json). Reflection
support is in the detailed
[`reflection-preparation-report.md`](reflection-preparation-report.md); it is not
a final personal reflection. The beginner-facing
[`learning-guide.md`](learning-guide.md) connects the concepts to the actual SQL
and measurements. A fresh independent rerun is recorded separately in
[`evidence/audit-verification-2026-11-17.md`](evidence/audit-verification-2026-11-17.md)
without replacing the historical evidence.

## Run the experiments

From the repository root in PowerShell:

```powershell
# Executable demonstrations for Rounds 2-5; Rounds 1, 6 and 7 are documents.
uv run python -B Module05/demo.py --round all

# The main Round 5 professor demonstration.
uv run python -B Module05/demo.py --round 5

# Machine-readable full benchmark.
uv run python -B Module05/benchmark.py --trials 7 --json

# Automated suite.
uv run python -B -m unittest discover -s Module05/tests -v
```

Each benchmark uses a new Temp directory and removes it when finished. Timing
values will vary; deterministic success criteria are the table counts, output
equivalence, one-versus-4,000 update rows, valid plans, rollback checks, index
restoration, integrity checks, and successful cleanup.

## Round 1 — Functional dependencies and diagrams

The intended dependencies are `job_id → machine_id`,
`job_id → technician`, `machine_id → site`, and `part_no → part_price`.
`job_id → site` follows transitively. Under the rule that one job uses a part at
most once, `(job_id,part_no)` is the minimal candidate key. The notes distinguish
domain rules from patterns visible only in five rows and disclose that no
independently handwritten pre-AI FD list was preserved.

## Round 2 — Anomalies

The update demonstration creates inconsistent site values by changing one of
three `cnc-01` rows. The insert demonstration accurately shows that SQLite
accepts a NULL-filled flat placeholder for an unused part—the anomaly is the
mixing of unrelated facts, not an engine rejection. Deleting the only
`P-0002` flat row loses its catalog price, while normalized `part` preserves it.

## Round 3 — 3NF build

| Table | Measured rows |
|---|---:|
| `flat_jobpart` | 200,000 |
| `machine` | 50 |
| `part` | 10 |
| `job` | 20,000 |
| `job_part` | 200,000 |
| `report_jobpart` | 200,000 |

Two-way `EXCEPT` checks found zero differences between the flat data and the
normalized reconstruction. `foreign_key_check` returned no rows and
`integrity_check` returned `ok`.

## Rounds 4 and 5 — Actual benchmark

Both dashboards returned the same 350 groups.

| Design | Dashboard median (ms) | Update rows | Update median (ms) | Base-table storage (KB) |
|---|---:|---:|---:|---:|
| Normalized 3NF | 121.0052 | 1 | 1.2915 | 3,976.0 |
| Denormalized report with index | 151.9686 | 4,000 | 22.6925 | 10,832.0 |

The indexed report was about 25.6% slower than the normalized query in the
recorded run. Dropping `ix_report_machine` changed the plan from a complete
index scan to a table scan and improved the report median from 137.1854 ms to
112.1664 ms in the controlled index experiment. This is a genuine negative
index result, not a claim that all indexes are harmful.

Storage values above are the workbook's table-only `dbstat` comparison. An
additional index-inclusive comparison is recorded separately.

## Round 6 — Recommendation

The [recommendation to Yasmin Kaya](recommendation.md) keeps normalized tables
as the source of truth and proposes a controlled transactional report rebuild.
Synchronization is proposed, not falsely claimed as implemented.

## Round 7 and classroom gates

The technical curiosity list is complete, and the student-provided
[`group-discussion-notes.md`](group-discussion-notes.md) now identifies Isa, Rayan, Arshia, and
Asmin and documents discussion of dependencies, diagrams, the 200,000-row build, query
performance, update amplification, index behavior, and the design recommendation. The section
labeled “Example Group Discussion” is illustrative rather than a verified word-for-word
transcript. The notes still do not establish every exact nearest-pod gate, so those are classified
individually in the [reflection preparation report](reflection-preparation-report.md).

## Optional DuckDB stretcher

The optional comparison was not recorded as a Module 5 classroom activity. It
was later completed and substantially extended in
[`Module06a`](../Module06a/README.md): the same analytical boundary was tested on
a two-million-row history with Parquet and DuckDB. This later evidence may inform
the architecture discussion, but it must not be presented as a Round 7 peer
exchange or as work performed during the earlier Module 5 class.

## Preparation for Module 6a

Run these commands once from the repository root before class:

```powershell
uv sync
uv run python -c "import duckdb; print(duckdb.__version__); print(duckdb.sql('SELECT 42 AS answer').fetchone()[0])"
uv run python -c "import sqlite3; print(sqlite3.sqlite_version)"
Test-Path Module05/normalize.db
```

The preserved database is the starting dataset for the next session. Do not
insert the planned 2,000,000-row history or create Parquet exports until the
professor supplies the Module 6a instructions. Bring
[`recommendation.md`](recommendation.md) for the 15-minute recap.

## Automated tests

The original saved run completed **26 tests**, all passing in 8.623 seconds. Coverage
includes FDs, candidate-key uniqueness, all three anomalies, exact counts,
foreign keys, two-way reconstruction, dashboard equivalence, plans, benchmark
sample counts, update amplification, rollback, storage, index restoration,
recommendation evidence, and honest curiosity status. See
[`evidence/test-results.txt`](evidence/test-results.txt). The final publication result
completed **35 tests**, all passing, and also verifies the learning/reflection documentation,
published group evidence, technical cross-check, and Markdown links.

## Professor demonstration

[`professor-demo.md`](professor-demo.md) provides tested PowerShell commands,
short and detailed speaking versions, likely questions and troubleshooting.

## Known limitations

- Timings are local measurements and will vary by machine and cache state.
- The report is a snapshot; automatic refresh or trigger synchronization is not
  implemented.
- `dbstat` must be available for object-level storage measurements.
- The generator stores flat prices as TEXT exactly as assigned, then casts to
  REAL during normalization; a production money model would need a deliberate
  decimal representation.
- Module 5 group discussion and member roles are now student-supplied and published, but several
  exact round gates remain not specifically documented.
- Reflection 05 is published from the student's final supplied text.
