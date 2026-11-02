# Module 3 technical completion report

## Current status — 2026-11-02

This section updates the historical delivery record below. The executable
HAVING exercise closes the complex-DQL evidence gap, the formal relational
algebra is repaired, and the seven-section reflection is complete. The
classroom pod was Sanjay, Sebastian, İsa, and Myo; İsa joined as a guest and
owned the algebra ↔ SQL workstream. Jomarie was absent. İsa has now personally
confirmed participation in Tasks A and C. The two shared Task A records still
contain different predictions. A dated personal review now records İsa's later
expectations and compares them with the saved plans without presenting them as
the original contemporaneous prediction. The neighboring pod's macOS version
and complete raw output remain unavailable. A second curiosity swap remains
unverified. İsa supplied a real Discord message link for the Module 3 question;
no answer is claimed. The original benchmark measurements remain unchanged.

## Executive summary

The technical Module 3 portfolio is implemented against the current professor
workbook. It includes the generated warehouse, verified AI query, raw plans,
five-run index benchmarks, injection demonstration, executable GROUP BY/HAVING
evidence, a readable algebra mapping, optional window rewrite, automated tests,
reconciled classroom notes, and a template-aligned reflection. All
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

Sanjay's record predicts SCAN, SEARCH, SCAN for technician equality, Machine
equality, and leading-wildcard LIKE. Sebastian's record predicts SCAN, SCAN,
SEARCH. Both records are shown rather than silently merged. İsa confirmed
participation. His later prediction review expects SCAN for all three baseline
queries and only the technician equality query to change to SEARCH after the
index. It matches the saved plans but is clearly dated after the classroom
activity, so the exact contemporaneous prediction is still not claimed.

An independent disposable reproduction used the Module 2 setup script. Before
the index, all three plans scanned. After `ix_job_tech`, technician equality
became an indexed SEARCH while Machine equality and leading-wildcard LIKE
remained scans; `upper(technician)` also scanned.

### Task B

The shared workstream record assigns relational algebra ↔ SQL to İsa. Sanjay's
reflection also credits İsa's help with the mapping. The documented query is
`SELECT * FROM maint_job WHERE technician = 'Beier'`, represented as
`σ_{technician='Beier'}(maint_job)`. The recorded Gemini comparison agrees on
selection; projection is optional because `SELECT *` retains all attributes.
The exact original Gemini transcript is not claimed.

### Task C

Sanjay's and Sebastian's notes document a neighboring-pod exchange, and İsa
has personally confirmed participation. The groups recorded matching
Windows/macOS plan classifications, a function-wrapped
predicate scan, leading-wildcard and covering-index surprises, and an
unresolved case-insensitive/partial-search question. The known Windows
screenshot displays SQLite CLI 3.53.4; the macOS SQLite version and raw output
were not preserved. No second swap, timing, transcript, or Discord answer was
invented. The supplied Discord link is recorded separately in `sql-notes.md`.

The local disposable experiment independently verifies the technical ideas:
`UPPER(technician)` scans with only the ordinary column index and searches with
a matching expression index; selecting only `a` uses a covering index while
selecting `a, b` still uses the index but must also visit the table.

A second downloaded Python experiment reproduces the screenshot's three
after-index plan types using the same `maint_job` and `machine` query shapes.
The supplied output used Python SQLite 3.46.1; the fresh local run used Python
SQLite 3.50.4. Both are controlled reproductions, not the unnamed group's
measurements. The screenshot separately displays SQLite CLI 3.53.4 in another
worktree.

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
source warehouse is opened read-only and copied to SQLite `:memory:` before
the temporary `O'Brien` row is inserted. Unit tests compare the source file
before and after the demo and confirm it is unchanged.

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
| Curiosity list with sources | sql-notes section 12 | PASS |
| Classroom Task A historical record | participation confirmed; conflicting shared predictions retained; dated later review matches saved plans; exact contemporaneous prediction absent | COMPLETE — LATER REVIEW ADDED |
| New Plan Safari technical verification | dated AI-assisted predictions and disposable execution | PASS |
| Classroom Task B preservation | shared notes, İsa's mapping, Gemini comparison, and Sanjay's reflection | COMPLETE — SHARED RECORDS LINKED |
| Classroom Task C record | participation confirmed; shared notes record Windows/macOS neighboring-pod exchange; macOS version/raw output unavailable | COMPLETE — TECHNICAL DETAILS PARTIAL |
| Second curiosity technical exercise | disposable equality, wildcard, expression-index and covering-index plans | PASS — not a second peer swap |
| Second curiosity swap | sourced example questions; no participant/response/date/medium supplied | REQUIRES REAL PEER ACTIVITY |
| Reflection | seven complete template sections with first-person classroom confirmation | PASS |
| Discord evidence | [student-supplied Module 3 message link](https://discord.com/channels/1064132619735928932/1064145704391561298/1566944448900898859); message body requires authenticated course access; no answer claimed | COMPLETE — LINK RECORDED |

## Files created or modified

| File | Purpose |
|---|---|
| `module-03/setup.sql` | Professor's generated warehouse fixture |
| `module-03/having-example.sql` | Executable GROUP BY/HAVING exercise |
| `module-03/evidence/having-results.txt` | Verified HAVING output and plan |
| `module-03/evidence/plan-safari-prediction-verification.txt` | Dated AI-assisted prediction and fresh disposable plan comparison |
| `module-03/plan-comparison.py` | Downloaded experiment integrated as an independently executable in-memory reproduction |
| `module-03/evidence/plan-comparison-results.txt` | Fresh Python SQLite 3.50.4 output and comparison with supplied 3.46.1 output |
| `module-03/curiosity-index-experiment.sql` | Disposable second curiosity experiment |
| `module-03/evidence/curiosity-index-results.txt` | Recorded plans and counts from the curiosity experiment |
| `module-03/covering-scan-demo.sql` | Isolated `SCAN ... USING COVERING INDEX` demonstration |
| `module-03/evidence/covering-scan-results.txt` | Recorded covering-index scan and explanation |
| `module-03/task1-query.sql` | Exact prompt and AI-generated query |
| `module-03/task1-report.md` | Result, plan, and correctness audit |
| `module-03/bench.py` | Repeatable disposable index benchmark |
| `module-03/task2-benchmark.md` | Timings and plan interpretation |
| `module-03/injection_demo.py` | Isolated unsafe/safe demonstration |
| `module-03/task3-injection.md` | Security analysis |
| `module-03/task4-algebra-to-plan.md` | SQL/algebra/plan mapping |
| `module-03/task5-queries.sql` | Optional three query variants |
| `module-03/task5-window-functions.md` | Optional comparison |
| `module-03/collect_evidence.py` | Deterministic evidence generator |
| `module-03/reproduce_classroom_plans.py` | Disposable Task A before/after reproduction |
| `module-03/sql-notes.md` | Classroom evidence, workstreams, curiosities |
| `module-03/README.md` | Navigation and reproduction |
| `module-03/tests/test_module03.py` | Automated verification |
| `module-03/evidence/*` | Raw plans, outputs, timings, and checks |
| `Reflections/ref03.md` | Complete seven-section student-level draft |
| `README.md` | Module 3 navigation |
| `.gitignore` | WAL/SHM and cache exclusions |

## Reproduction commands

```powershell
sqlite3 module-03/warehouse.db ".read module-03/setup.sql"
sqlite3 module-03/warehouse.db ".read module-03/having-example.sql"
uv run python module-03/collect_evidence.py
uv run python module-03/reproduce_classroom_plans.py
uv run python module-03/plan-comparison.py
sqlite3 :memory: ".read module-03/curiosity-index-experiment.sql"
sqlite3 :memory: ".read module-03/covering-scan-demo.sql"
uv run python module-03/bench.py --repeats 5 --batch-iterations 100
uv run python module-03/injection_demo.py --output module-03/evidence/injection-output.txt
uv run python -m unittest discover -s module-03/tests -v
```

## Automated verification

The current suite ran 23 tests: 23 passed, 0 failed. It rebuilt the warehouse,
checked exact counts and ranges, reran setup, tested date boundaries,
distinct-customer and no-order behavior, validated saved plans and benchmark
medians, proved a genuine slowdown and two speedups, checked the injection
payload, apostrophe case, and source-file isolation, compared all optional query variants, reproduced
Task A on a disposable database, verified the HAVING result and plan, checked
the equality, wildcard, expression-index, covering and non-covering curiosity
plans, reproduced `SCAN ... USING COVERING INDEX`, executed the Python
plan-comparison script and checked its classifications,
rejected unexpected Markdown control characters, verified ignored databases,
and resolved every relative Markdown link. Raw output is in
[test-results.txt](evidence/test-results.txt).

## Risks and limitations

- Workbook content below its draft boundary is provisional.
- The screenshot displays CLI SQLite 3.53.4, the downloaded result records
  Python SQLite 3.46.1, and the fresh local reproduction uses Python SQLite
  3.50.4. Versions and evidence origins are kept separate.
- Timing depends on this machine, filesystem cache, load, and SQLite build.
- The Task A image is authentic supplied evidence but intentionally not
  published because of another student's visible path.
- İsa confirmed participation in the neighboring-pod event, but the macOS
  SQLite version and complete raw output are unavailable.
- The second curiosity is technically reproducible and example questions are
  prepared, but no response/date/medium verifies a completed second swap.
- İsa supplied a Discord message link for the Module 3 question. The URL
  resolves, but the message body could not be inspected without authenticated
  course-server access; no answer is claimed.
- The fixture intentionally omits foreign keys; that is Module 4 material.

## Remaining external and final-review actions

- Read and understand the query-plan and benchmark findings.
- Practise explaining algebra, join multiplicity, indexing, and parameters.
- Add the neighboring-pod macOS version/raw output if it becomes available.
- Record the actual participant, questions, answers, date, and medium only
  after a real second curiosity exchange occurs.
- Complete instructor-specific checkpoint requirements.

The later Task A review cannot recover the exact contemporaneous wording, and
technical automation cannot create a genuine second peer response. If the
professor requires the neighboring pod's raw technical output, that also
remains an external dependency.

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
- Overall status: **technical implementation, confirmed Tasks A–C, later
  prediction review, and Discord link complete; the second peer exchange
  remains unverified**.
