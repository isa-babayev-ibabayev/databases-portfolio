# Module 3 technical completion report

## Current status — 2026-10-30

This section updates the historical delivery record below. The executable
HAVING exercise now closes the remaining complex-DQL evidence gap, the formal
relational algebra has been repaired, and the seven-section reflection draft
is complete. The original benchmark measurements remain unchanged. Historical
human evidence is still limited: the original Plan Safari predictions were not
recorded, and neighboring-pod raw output/version, a second curiosity swap, and
a Discord post are unavailable.

## Executive summary

The technical Module 3 portfolio is implemented against the current professor
workbook. It includes the generated warehouse, verified AI query, raw plans,
five-run index benchmarks, injection demonstration, executable GROUP BY/HAVING
evidence, a readable algebra mapping, optional window rewrite, automated tests,
student-supplied classroom notes, and a template-aligned reflection draft. All
technically achievable requirements are implemented. Unsupported historical
human activities remain explicitly limited rather than reconstructed.

## Repository and environment

| Item | Value |
|---|---|
| Repository root | verified local `databases-portfolio/` checkout; absolute user path intentionally omitted from the public report |
| Expected/verified remote | `https://github.com/isa-babayev-ibabayev/databases-portfolio.git` |
| Branch | `main` |
| Baseline HEAD | `e147f66 Expand Module 2 study notes and verification` |
| Initial remote difference | 0 ahead / 0 behind |
| Initial unrelated change | untracked root `main.py`; preserved and not staged |
| Operating system | Windows 10 Home, NT 10.0.26300.0 |
| uv | 0.11.16 |
| uv Python | 3.14.5 |
| SQLite CLI | 3.53.4 |
| Python sqlite3 runtime | 3.50.4 |

No `Module03/` existed initially. An empty, untracked typo directory named
`modele-03/` existed; after verifying it contained no files, it was renamed
to the required `Module03/`. No student material was overwritten.

## Protected work

- `module-01/`, `module-02/`, and `Module02/` are protected.
- The final preservation check compares them to baseline commit `e147f66`.
- The unrelated root `main.py` remains untracked.
- The only root changes are Module 3 navigation in `README.md` and generated
  SQLite/cache ignore patterns in `.gitignore`.
- Tunay Daldaban's repository was not accessed or modified.

## Classroom Tasks A, B, and C

### Task A

The exact supplied image existed and was inspected. It shows SQLite CLI 3.53.4,
an indexed technician equality SEARCH, a Machine-name SCAN, a leading-wildcard
SCAN, and an initial syntax error caused by omitting the CREATE INDEX
semicolon. The screenshot also visibly contains another student's identifying
filesystem path, so it was not published. A faithful transcription and
evidence limitation are in [sql-notes.md](sql-notes.md).

The image is not represented as a before-index baseline or as proof of commands
run on the portfolio owner's laptop.

An independent disposable reproduction used the Module 2 setup script. Before
the index, all three plans scanned. After `ix_job_tech`, technician equality
became an indexed SEARCH while Machine equality and leading-wildcard LIKE
remained scans; `upper(technician)` also scanned.

### Task B

The supplied human explanation and Gemini comparison are quoted without
silently rewriting their wording. A separate clarification explains
(sigma), the selection predicate, the input relation, absence of a join, and
why projection is optional for `SELECT *`.

### Task C

The supplied neighboring-pod discussion is preserved as completed classroom
evidence. The Windows/macOS match is marked student-reported because raw
neighboring-pod output and version were not available. No names, transcript,
second swap, timing, or Discord post was invented.

## Warehouse setup

The authoritative [setup.sql](setup.sql) creates:

| Table | Actual rows |
|---|---:|
| customer | 2,000 |
| product | 500 |
| orders | 60,000 |
| order_line | 240,000 |

Verified ranges include customer IDs 1–2000, product IDs 1–500, order IDs
1–60000, and order dates 2025-01-01 through 2026-06-24. `SKU-00001` confirms
zero-padding, and the explicit `x=540` remainder check returns 2025-01-01.
The script remains free of Module 4 foreign keys.

## Learning Goal 1 — executable HAVING evidence

[having-example.sql](having-example.sql) filters late Orders rows with `WHERE`,
groups them by customer, and keeps completed groups with
`HAVING COUNT(*) > 20`. Read-only execution on SQLite 3.50.4 returned 400
customers. Every qualifying customer had exactly 30 late orders, with customer
IDs from 1 through 1996 in steps of five. The plan contains `SCAN orders`,
`USE TEMP B-TREE FOR GROUP BY`, and `USE TEMP B-TREE FOR ORDER BY`. Raw output
and independent aggregate checks are in
[having-results.txt](evidence/having-results.txt).

## Task 1 — AI query and verification

The exact prompt and AI response are preserved in
[task1-query.sql](task1-query.sql). Actual result:

| City | Customers | Revenue |
|---|---:|---:|
| Bielefeld | 500 | 11,242,176.0 |
| Gütersloh | 500 | 8,422,344.0 |
| Münster | 500 | 5,493,504.0 |
| Paderborn | 500 | 2,815,656.0 |

Actual SQLite 3.50.4 plan:

```text
SCAN ol
SEARCH o USING INTEGER PRIMARY KEY (rowid=?)
SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
SEARCH p USING INTEGER PRIMARY KEY (rowid=?)
USE TEMP B-TREE FOR GROUP BY
USE TEMP B-TREE FOR count(DISTINCT)
USE TEMP B-TREE FOR ORDER BY
```

The AI plan prediction was wrong about the outer loop; SQLite scanned OrderLine,
not Orders. Correctness checks confirmed:

- 40,575 included 2025 orders;
- 2025-01-01 included and 2026-01-01 excluded;
- distinct customers are not multiplied by orders/lines;
- revenue equals the sum of quantity times price;
- cities are grouped and sorted correctly;
- an independent Python aggregation exactly matches SQL;
- a small fixture proves no-order omission and boundary behavior.

## Task 2 — measured index behavior

Method: disposable database copy; one process/session; one warm-up; five timed
samples; median; complete result fetching.

| Query/stage | Median ms | Plan/result |
|---|---:|---|
| Dashboard baseline | 160.879800 | OrderLine scan |
| Dashboard + date index | 154.832800 | unchanged; index ignored |
| Dashboard + order-line order index | 1429.524300 | index-driven plan, ~8.9× slower |
| Dashboard + product index | 1514.061800 | plan unchanged; product index unused |
| Single day, no date index | 3.832294 | `SCAN o` |
| Single day, date index | 0.297238 | indexed SEARCH |
| Product filter, no index | 13.714101 | `SCAN ol` |
| Product filter, product index | 2.782931 | indexed SEARCH |

The short-query numbers are per execution from 100-execution batches. Wrapping
`ordered_on` in `date()` forced a scan. Selecting only the indexed date used
a covering index; adding `customer_id` made it non-covering.

## Task 3 — injection prevention

The normal lookup succeeded. An apostrophe broke the vulnerable string-built
query but worked with a parameter. The payload `' OR '1'='1` returned 2,001
rows through the vulnerable function and zero through the bound query. The
temporary `O'Brien` row was rolled back. Unit tests confirm no unintended
modification.

## Task 4 — algebra to plan

[task4-algebra-to-plan.md](task4-algebra-to-plan.md) maps the city query through
selection `σ`, projection `π`, three joins `⋈`, grouping `γ`, and sorting `τ`.
The repaired GitHub-compatible expression includes the exact join conditions,
2025 selection, distinct-customer count, and revenue sum. It distinguishes
set-oriented algebra from SQL
duplicate semantics and separates logical meaning from the physical plan.

## Optional Task 5

Completed. Grouped, correlated, and de-duplicated window variants each returned
the same 400 customer rows.

| Variant | Median of 3 |
|---|---:|
| Grouped | 9.189100 ms |
| Correlated | 6249.788700 ms |
| Window | 24.976000 ms |

The first window draft's repeated-row trap is documented and corrected using
`ROW_NUMBER()`.

## Requirement status

| Requirement | Evidence | Status |
|---|---|---|
| Complex joins, grouping, DQL | Task 1, HAVING exercise, and Task 5 | PASS |
| HAVING/clause-order understanding | `having-example.sql` and verified results | PASS |
| Subquery | correlated Task 5 variant | PASS |
| Window function | corrected Task 5 variant | OPTIONAL COMPLETED |
| EXPLAIN QUERY PLAN | raw Task 1/benchmark/Task 5 plans | PASS |
| Index benchmark ≥3 runs | five runs and verified medians | PASS |
| Negative index result | 8.9× dashboard slowdown | PASS |
| AI query verification | SQL, Python calculation, edge fixture | PASS |
| SQL injection prevention | demo, raw output, tests | PASS |
| Relational algebra | Task 4 | PASS |
| Curiosity list with sources | sql-notes section 11 | PASS |
| Classroom Task A historical record | image transcription; original predictions absent | PARTIAL — historical limitation |
| New Plan Safari technical verification | dated AI-assisted predictions and disposable execution | PASS |
| Classroom Task B preservation | original text plus clarification | PASS |
| Classroom Task C record | supplied discussion; neighboring raw evidence unavailable | HUMAN ACTIVITY — UNVERIFIED |
| Second curiosity swap | no supporting record | EXTERNAL/HUMAN LIMITATION |
| Reflection draft | seven complete template sections | PASS — student factual review recommended |
| Discord evidence | no link/evidence supplied | EXTERNAL/HUMAN LIMITATION |

## Files created or modified

| File | Purpose |
|---|---|
| `Module03/setup.sql` | Professor's generated warehouse fixture |
| `Module03/having-example.sql` | Executable GROUP BY/HAVING exercise |
| `Module03/evidence/having-results.txt` | Verified HAVING output and plan |
| `Module03/evidence/plan-safari-prediction-verification.txt` | Dated AI-assisted prediction and fresh disposable plan comparison |
| `Module03/task1-query.sql` | Exact prompt and AI-generated query |
| `Module03/task1-report.md` | Result, plan, and correctness audit |
| `Module03/bench.py` | Repeatable disposable index benchmark |
| `Module03/task2-benchmark.md` | Timings and plan interpretation |
| `Module03/injection_demo.py` | Isolated unsafe/safe demonstration |
| `Module03/task3-injection.md` | Security analysis |
| `Module03/task4-algebra-to-plan.md` | SQL/algebra/plan mapping |
| `Module03/task5-queries.sql` | Optional three query variants |
| `Module03/task5-window-functions.md` | Optional comparison |
| `Module03/collect_evidence.py` | Deterministic evidence generator |
| `Module03/reproduce_classroom_plans.py` | Disposable Task A before/after reproduction |
| `Module03/sql-notes.md` | Classroom evidence, workstreams, curiosities |
| `Module03/README.md` | Navigation and reproduction |
| `Module03/tests/test_module03.py` | Automated verification |
| `Module03/evidence/*` | Raw plans, outputs, timings, and checks |
| `Reflections/ref03.md` | Complete seven-section student-level draft |
| `README.md` | Module 3 navigation |
| `.gitignore` | WAL/SHM and cache exclusions |

## Reproduction commands

```powershell
sqlite3 Module03/warehouse.db ".read Module03/setup.sql"
sqlite3 Module03/warehouse.db ".read Module03/having-example.sql"
uv run python Module03/collect_evidence.py
uv run python Module03/reproduce_classroom_plans.py
uv run python Module03/bench.py --repeats 5 --batch-iterations 100
uv run python Module03/injection_demo.py --output Module03/evidence/injection-output.txt
uv run python -m unittest discover -s Module03/tests -v
```

## Automated verification

The current suite ran 19 tests: 19 passed, 0 failed. It rebuilt the warehouse,
checked exact counts and ranges, reran setup, tested date boundaries,
distinct-customer and no-order behavior, validated saved plans and benchmark
medians, proved a genuine slowdown and two speedups, checked the injection
payload and apostrophe case, compared all optional query variants, reproduced
Task A on a disposable database, verified the HAVING result and plan, rejected
unexpected Markdown control characters, verified ignored databases, and
resolved every relative Markdown link. Raw output is in
[test-results.txt](evidence/test-results.txt).

## Risks and limitations

- Workbook content below its draft boundary is provisional.
- CLI SQLite is 3.53.4 while Python benchmarking uses SQLite 3.50.4; versions
  are recorded with each relevant artifact.
- Timing depends on this machine, filesystem cache, load, and SQLite build.
- The Task A image is authentic supplied evidence but intentionally not
  published because of another student's visible path.
- The neighboring macOS comparison lacks raw corroborating output/version.
- No evidence confirms a Discord post or a second curiosity swap.
- The fixture intentionally omits foreign keys; that is Module 4 material.

## Remaining external and final-review actions

- Read and understand the query-plan and benchmark findings.
- Read the completed reflection and confirm that its conservative first-person
  interpretations match the student's own experience.
- Practise explaining algebra, join multiplicity, indexing, and parameters.
- Add neighboring-pod raw output if formal corroboration is desired and
  available.
- Add a real Discord link only if one exists.
- Complete instructor-specific checkpoint requirements.

Technical automation cannot reconstruct the missing original Task A
predictions or independently confirm Task C. If the professor requires new
human participation or corroboration, that remains an external dependency.

## Delivery

- Commits:
  - `43ac0ec6497ba465a7c72cf8b2af6c4f9b256603` — warehouse setup and query-plan verification
  - `f6cb0f9ed9440c3108c99201aba45c3b40506846` — measured index benchmark
  - `8c90a3698d526c6471dd446757e117f5c44c3b36` — security, algebra, and window exercises
  - `b120801adfcd0355fc2172f406ff5306b651b600` — classroom evidence and documentation
  - `c15b1e69b06791070ca9925cf71beeb5b50e5a1e` — final technical verification evidence
- Push: succeeded to `origin/main` through `c15b1e6`.
- Final local/remote HEAD after this report-status commit is recorded in the
  delivery response; a commit cannot include its own hash without changing it.
- Overall status: **technically achievable implementation complete; student
  factual review and unsupported external human evidence remain separate**.
