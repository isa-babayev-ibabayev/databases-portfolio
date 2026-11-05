# Module 5 — Normalization vs. Denormalization Benchmarking Studio

## Learning goals

1. Derive functional dependencies and candidate keys.
2. Explain and implement 1NF, 2NF, and 3NF.
3. Denormalize deliberately for a reporting workload.
4. Measure query latency, update amplification, storage, and index effects.
5. Recommend and defend a schema for an industrial workload.

## What this module builds

The professor's generator creates 20,000 jobs with 10 parts each: 200,000 flat
job-part rows. [`setup.sql`](setup.sql) decomposes them into `machine`, `part`,
`job`, and `job_part`, then builds a 200,000-row `report_jobpart` table. All
demonstrations create disposable databases under Windows Temp; generated `.db`
files are not committed.

Recorded environment: Python 3.14.5, SQLite 3.50.4, Windows 11. The project uses
only Python's standard library, so the SQLite CLI is optional.

## Evidence map

| Round | Implementation | Executed evidence |
|---|---|---|
| 1 — See it | [`normalization-notes.md`](normalization-notes.md) | FD analysis and two Mermaid ER diagrams |
| 2 — Break it | [`anomalies.sql`](anomalies.sql), [`experiment.py`](experiment.py) | [`evidence/anomaly-results.txt`](evidence/anomaly-results.txt) |
| 3 — Build it | [`setup.sql`](setup.sql) | [`evidence/row-counts.txt`](evidence/row-counts.txt) |
| 4 — Race it | [`reporting.sql`](reporting.sql), [`benchmark.py`](benchmark.py) | [`evidence/benchmark-results.csv`](evidence/benchmark-results.csv), [`evidence/query-plans.txt`](evidence/query-plans.txt) |
| 5 — Price it | [`experiment.py`](experiment.py), [`demo.py`](demo.py) | [`evidence/benchmark-summary.md`](evidence/benchmark-summary.md), [`evidence/update-results.txt`](evidence/update-results.txt), [`evidence/storage-results.txt`](evidence/storage-results.txt) |
| 6 — Decide | [`recommendation.md`](recommendation.md) | Memo citing measured results |
| 7 — Harvest | [`normalization-notes.md`](normalization-notes.md#round-7--prepared-curiosities) | Prepared curiosities; human sharing not claimed |

Machine-readable evidence is in
[`evidence/benchmark-results.json`](evidence/benchmark-results.json). Reflection
support is in [`reflection-evidence.md`](reflection-evidence.md); it is not a
final personal reflection.

## Run the experiments

From the repository root in PowerShell:

```powershell
# All seven technical rounds (the human gate activities remain separate).
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

The technical curiosity list is complete. Nearest-pod gates, a curiosity swap,
and Discord sharing are **not documented as completed** because no genuine
student confirmation was supplied.

## Optional DuckDB stretcher

**Not attempted.** Neither the DuckDB CLI nor Python package was installed. No
package was added because the task is optional and unnecessary dependencies
were prohibited.

## Automated tests

The saved run completed **26 tests**, all passing in 8.623 seconds. Coverage
includes FDs, candidate-key uniqueness, all three anomalies, exact counts,
foreign keys, two-way reconstruction, dashboard equivalence, plans, benchmark
sample counts, update amplification, rollback, storage, index restoration,
recommendation evidence, and honest curiosity status. See
[`evidence/test-results.txt`](evidence/test-results.txt).

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
- Round gates and human curiosity sharing require personal classroom evidence.
- No final Reflection 05 claims personal experience yet.
