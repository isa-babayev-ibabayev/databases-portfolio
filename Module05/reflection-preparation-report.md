# Reflection 05 Preparation Report

## Purpose and academic boundary

This report organizes verifiable Module 5 facts so İsa Babayev can write a truthful personal
reflection. It is **not** the reflection and does not answer personal questions on the student's
behalf. `Reflections/ref05.md` remains student-authored.

The heading names and order below were checked against the current official
[HSBI portfolio reflection template](https://github.com/iotempire/iot-portfolio-template/blob/main/Reflections/TEMPLATE.md)
on 2026-11-17.

## Sources reviewed

- Current official Module 5 workbook and all seven round gates.
- `Module05` scripts, SQL, diagrams, saved evidence, recommendation, tests, and preserved DB.
- Git history for commits `3291030` and `33aa3fd`.
- Existing `Reflections` files and repository-wide discussion-note search.
- Current task statement and accessible attachments relevant to Module 5.
- Fresh disposable verification recorded in
  [audit-verification-2026-11-17.md](evidence/audit-verification-2026-11-17.md).

## Technical completion audit

| Round | Initial audit | Final technical status | Evidence | Human boundary |
|---|---|---|---|---|
| 1 — See it | Correct FD classification, minimal candidate key, two Mermaid diagrams, honest LLM comparison | **PASS** | [normalization-notes.md](normalization-notes.md) | Exact neighboring-pod answer not documented |
| 2 — Break it | Three executable anomalies and saved outcomes | **PASS** | [anomalies.sql](anomalies.sql), [anomaly-results.txt](evidence/anomaly-results.txt) | Neighbor response not documented |
| 3 — Build it | Reproducible 200k build, 3NF tables, FK enforcement, counts and two-way reconstruction | **PASS** | [setup.sql](setup.sql), [row-counts.txt](evidence/row-counts.txt) | Gate explanation is prepared; actual exchange needs confirmation |
| 4 — Race it | Equivalent queries, warmed/interleaved trials, real plans and timings | **PASS** | [benchmark-summary.md](evidence/benchmark-summary.md), [query-plans.txt](evidence/query-plans.txt) | Plan comparison with another pod needs confirmation |
| 5 — Price it | Rollback-protected 1/4,000 updates, `dbstat`, with/without-index experiment | **PASS** | [update-results.txt](evidence/update-results.txt), [storage-results.txt](evidence/storage-results.txt) | Classmate prediction is not recorded |
| 6 — Decide | Six-sentence evidence-based memo and proposed refresh strategy | **PASS** | [recommendation.md](recommendation.md) | Actual spoken defense and “what if” question need confirmation |
| 7 — Harvest | Eight grounded technical curiosities; later Module 6a supplies optional DuckDB evidence | **PASS** for technical collection; **OPTIONAL** stretcher later completed | [normalization-notes.md](normalization-notes.md), [Module 6a README](../Module06a/README.md) | Curiosity swap details need confirmation |

## Group-note evidence matrix

| Note or observation | Source | Relevant round | Technical interpretation | Portfolio evidence | Status |
|---|---|---|---|---|---|
| “I have already discussed Module 5 with my groupmates.” | Current user-provided audit prompt | General Module 5 | Confirms that some real discussion occurred, but does not identify a round, gate question, speaker, answer, disagreement, or change | No round-specific note was found | **DISCUSSED, DETAILS INCOMPLETE** |
| The student states that notes were collected. | Current user-provided audit prompt | General Module 5 | The notes were not included as a separate accessible attachment and were not found in the repository | Search covered `Module05`, `Reflections`, Git history, and relevant attachments | **HUMAN CONFIRMATION REQUIRED** |
| “No actual neighboring-pod response is documented.” | [normalization-notes.md](normalization-notes.md) | Round 2 | Correctly distinguishes a prepared gate question from a recorded response | Three anomaly results remain technically verified | **NOT DOCUMENTED** |
| Round 3, 4, 5, and 6 gate answers are prepared. | [normalization-notes.md](normalization-notes.md) and [recommendation.md](recommendation.md) | Rounds 3–6 | Technical readiness is not proof that the exchanges occurred | Counts, plans, update/storage evidence, memo | **HUMAN CONFIRMATION REQUIRED** |
| Curiosities are “prepared, not documented as shared.” | [normalization-notes.md](normalization-notes.md) | Round 7 | The technical list exists; the swap participants and selected questions are unknown | Eight sourced curiosities | **HUMAN CONFIRMATION REQUIRED** |

No classmate quotation, name, attendance date, or round-specific response is inferred from the
general statement. The existing repository's earlier “not documented” wording is compatible with
the new confirmation: an activity can have happened without a sufficiently detailed record.

## Seven discussion gates

| Round | Required gate | What can be established | Status | Information the student should supply |
|---|---|---|---|---|
| 1 | Which arrow disappears in the second ER diagram? | Correct technical answer exists; no actual peer answer located | **HUMAN CONFIRMATION REQUIRED** | Who saw the diagrams, what answer they gave, and whether anything changed |
| 2 | Can a neighbor break an anomaly statement? | Statements and results are verified; no response located | **HUMAN CONFIRMATION REQUIRED** | Which anomaly they challenged and the outcome |
| 3 | Why does `part` contain 10 rows? | Correct answer is verified | **HUMAN CONFIRMATION REQUIRED** | Whether this exact question was asked and how it was answered |
| 4 | Did both pods get the same plan? | Local plans are saved | **HUMAN CONFIRMATION REQUIRED** | Other pod's plan/version and the observed similarity or difference |
| 5 | Could the neighbor predict the numbers? | Prediction logic and measurements exist | **HUMAN CONFIRMATION REQUIRED** | Their genuine prediction and what surprised them |
| 6 | Could the student defend the memo against a “what if”? | Prepared answer exists | **HUMAN CONFIRMATION REQUIRED** | Actual question, answer, and any memo change |
| 7 | Which curiosities did the pods identify? | Eight curiosities exist | **HUMAN CONFIRMATION REQUIRED** | Which were exchanged, which overlapped, and any unresolved question |

The student does not need to recreate a discussion. They should add only remembered or written
facts and may state that a specific detail was not recorded.

## Take-away

### Part A — Verified evidence

- Normalization reduced one machine-site change from 4,000 report-row updates to one authoritative
  machine-row update.
- The normalized join and denormalized report returned the same 350 groups.
- The indexed report was slower than the normalized join in the saved run; removing the unsuitable
  report index improved the broad aggregation.
- The denormalized base table used 10,832.0 KiB versus 3,976.0 KiB for normalized base tables.

### Part B — Possible reflection themes

- Schema design is a workload trade-off rather than a rule that every schema must be maximally
  normalized or denormalized.
- Rows touched and storage duplication can be more transferable than one local timing.
- A negative benchmark result can be more informative than the expected speedup.

### Part C — Questions for the student

1. Which one of these results do you most want to remember?
2. What advice would you give yourself before starting the benchmark?
3. Did a group discussion change your main conclusion? If so, how?

## What was good?

### Part A — Verified evidence

- The generator, decomposition, report build, anomalies, and benchmarks are reproducible.
- Two-way `EXCEPT` checks found zero reconstruction differences.
- Foreign-key and integrity checks passed.
- The test suite passed all 26 pre-audit tests; the expanded audit suite result is recorded in
  the final test evidence.

### Part B — Possible reflection themes

- Using executable checks rather than trusting row counts alone.
- Preserving raw timing samples and medians instead of selecting a favorable run.
- Using rollback transactions and temporary databases to protect the source.

### Part C — Questions for the student

1. Which measurement or explanation worked best when you discussed it?
2. Was there a script, diagram, or table you found especially clear?
3. What did a groupmate understand quickly from your evidence?

## What was difficult?

### Part A — Verified evidence

- The first development run exposed a cached `EXPLAIN QUERY PLAN` problem after dropping the
  index. The harness was corrected with `cached_statements=0` and rerun.
- The result contradicted the simple expectation that one table must beat four joins.
- Functional dependencies had to be separated into domain assumptions, generator observations,
  and constraints actually enforced by the database.

### Part B — Possible reflection themes

- Distinguishing a measurement-harness defect from a database result.
- Understanding why a broad index scan can cost more than a table scan.
- Explaining why sample data cannot establish every proposed dependency.

### Part C — Questions for the student

1. Which concept or experiment did you personally find difficult?
2. What was the root cause: SQL syntax, theory, tools, interpretation, or communication?
3. Did a groupmate or instructor clarify the difficult part? What exactly did they say?

## Exploration and show stoppers

### Part A — Verified evidence

- The index experiment deliberately tested the unexpected result and restored the index.
- The generator's `% 40` expression produced only ten parts because `k` never exceeded 10.
- The flat price began as TEXT and was explicitly converted during normalization.
- The preserved database remained byte-for-byte unchanged during the audit.

### Part B — Possible reflection themes

- Investigating the planner rather than changing numbers to fit an expectation.
- Treating the `DISTINCT` job load as an assumption check.
- Exploring the later DuckDB result as a separate Module 6a extension.

### Part C — Questions for the student

1. Which unexpected result led you to explore further?
2. Did you have a blocker that required another person or a new test?
3. Which curiosity did your group find worth discussing?

## Interaction with peers and instructors

### Part A — Verified evidence

- The student explicitly confirms that Module 5 group discussions occurred.
- No accessible source maps participants, questions, responses, or changes to the seven gates.
- The repository contains prepared technical answers but does not claim those are conversations.

### Part B — Possible reflection themes

- Comparing predictions with measurements.
- Explaining why only ten parts were generated.
- Comparing query plans or challenging an anomaly example.
- Defending the refresh strategy against a staleness question.

These are prompts, not claims about what happened.

### Part C — Questions for the student

1. Who did you actually discuss Module 5 with?
2. Which of the seven gate questions did you ask or answer?
3. What did you learn from them, and what did you explain in return?
4. Was there disagreement, correction, or a changed recommendation?
5. Do you have a note, message, screenshot, or remembered wording that can be cited honestly?

## How did you verify AI suggestions?

### Part A — Verified evidence

- The FD list was checked against domain assumptions and rejected sample-only dependencies.
- SQL assertions verified keys, counts, FDs, reconstruction, result equivalence, plans, and
  rollback behavior.
- Raw samples, medians, `dbstat`, and automated tests checked performance/storage claims.
- The cached-plan error is a concrete example where an initial automated result was discarded and
  the harness corrected.

### Part B — Possible reflection themes

- Why an AI-generated dependency must be checked against business meaning.
- Why real SQL output is stronger than a plausible explanation.
- Why preserving a negative result is part of verification.

### Part C — Questions for the student

1. Which AI suggestion did you personally inspect or challenge?
2. Which command or evidence file did you use to verify it?
3. Did you notice any wrong, exaggerated, or unclear suggestion?
4. Which evidence have you personally rerun or reviewed?

## Help and extra work

### Part A — Verified evidence

- The portfolio includes extra automated tests, a safe demonstration script, raw plans, storage
  scopes, rollback checks, professor-demonstration notes, and later Module 6a analytical evidence.
- AI assistance is disclosed in `normalization-notes.md`.
- No specific Module 5 helper, recipient, presentation, or peer contribution is documented.

### Part B — Possible reflection themes

- Additional work used to make the results independently verifiable.
- Genuine help received from groupmates or help given to them.
- Whether the later DuckDB work changed the Module 5 recommendation boundary.

### Part C — Questions for the student

1. Who helped you with Module 5, and what did they actually do?
2. Who did you help, and what did you explain or verify?
3. Did you present, share a query, fix a common issue, or contribute a useful question?
4. Which extra artifact was most valuable rather than merely more documentation?

## Reflection readiness checklist

| Reflection section | Technical evidence ready | Genuine student input available | Remaining action |
|---|---|---|---|
| Take-away | Yes | Not supplied in accessible source | Select the fact you personally want to remember and explain why |
| What was good? | Yes | Not supplied | Identify what genuinely worked well for you |
| What was difficult? | Yes | Not supplied | State your real difficulty and root cause |
| Exploration and show stoppers | Yes | Not supplied | Choose exploration you personally performed or reviewed |
| Interaction with peers and instructors | Partial | General discussion confirmed; details unavailable | Add participants, actual gate/question, learning, and contribution |
| How did you verify AI suggestions? | Yes | Not supplied | Describe checks you personally performed |
| Help and extra work | Yes | Not supplied | Record genuine help given/received and useful extra work |

## Student completion checklist

- [ ] Create `Reflections/ref05.md` from the official template.
- [ ] Write each section in your own words using only personal experience.
- [ ] Supply the accessible group-note text or summarize only what you genuinely remember.
- [ ] Map any remembered discussion to the relevant gate; leave unknown gates undocumented.
- [ ] State whether the memo was actually defended and whether it changed.
- [ ] State which curiosities were actually exchanged.
- [ ] Record which commands/evidence you personally reviewed to verify AI assistance.
- [ ] Check every technical number against the linked evidence before submission.
