# Reflection 05 Preparation Report

## Purpose and academic boundary

This report organizes verifiable Module 5 facts supporting İsa Babayev's personal reflection. It
is **not** the reflection and does not answer personal questions on the student's behalf. The
student's final supplied text is now published as [Reflection 05](../Reflections/ref05.md).

The heading names and order below were checked against the current official
[HSBI portfolio reflection template](https://github.com/iotempire/iot-portfolio-template/blob/main/Reflections/TEMPLATE.md)
on 2026-11-17.

## Sources reviewed

- Current official Module 5 workbook and all seven round gates.
- `Module05` scripts, SQL, diagrams, saved evidence, recommendation, tests, and preserved DB.
- Git history for commits `3291030` and `33aa3fd`.
- Existing `Reflections` files and repository-wide discussion-note search.
- Current task statement and accessible attachments relevant to Module 5.
- Student-supplied [group discussion notes](group-discussion-notes.md), member names, GitHub
  links, and group-document role allocation.
- [Group-document technical cross-check](group-document-technical-crosscheck.md). The referenced
  PDF binary was unavailable during publication, so the cross-check uses the student's explicit
  PDF-derived facts and records that limitation.
- Fresh disposable verification recorded in
  [audit-verification-2026-11-17.md](evidence/audit-verification-2026-11-17.md).

## Technical completion audit

| Round | Initial audit | Final technical status | Evidence | Human boundary |
|---|---|---|---|---|
| 1 — See it | Correct FD classification, minimal candidate key, two Mermaid diagrams, honest LLM comparison | **PASS** | [normalization-notes.md](normalization-notes.md), [group notes](group-discussion-notes.md) | Dependency/ER discussion supported; exact arrow gate not documented |
| 2 — Break it | Three executable anomalies and saved outcomes | **PASS** | [anomalies.sql](anomalies.sql), [anomaly-results.txt](evidence/anomaly-results.txt) | PDF-derived anomaly work is described; exact neighbor challenge not documented |
| 3 — Build it | Reproducible 200k build, 3NF tables, FK enforcement, counts and two-way reconstruction | **PASS** | [setup.sql](setup.sql), [row-counts.txt](evidence/row-counts.txt), [group notes](group-discussion-notes.md) | Rayan's build role supported; exact ten-part gate not documented |
| 4 — Race it | Equivalent queries, warmed/interleaved trials, real plans and timings | **PASS** | [benchmark summary](evidence/benchmark-summary.md), [plans](evidence/query-plans.txt), [group notes](group-discussion-notes.md) | Performance discussion supported; exact cross-pod plan gate not documented |
| 5 — Price it | Rollback-protected 1/4,000 updates, `dbstat`, with/without-index experiment | **PASS** | [update results](evidence/update-results.txt), [storage results](evidence/storage-results.txt), [group notes](group-discussion-notes.md) | Update/index discussion supported; prediction gate not documented |
| 6 — Decide | Six-sentence evidence-based memo and proposed refresh strategy | **PASS** | [recommendation.md](recommendation.md), [group notes](group-discussion-notes.md) | Design conclusion supported; exact “what if” gate not documented |
| 7 — Harvest | Eight grounded technical curiosities; later Module 6a supplies optional DuckDB evidence | **PASS** for technical collection; **OPTIONAL** stretcher later completed | [normalization-notes.md](normalization-notes.md), [Module 6a README](../Module06a/README.md) | Exact curiosity swap not documented |

## Group-note evidence matrix

| Note or observation | Source | Relevant round | Technical interpretation | Portfolio evidence | Status |
|---|---|---|---|---|---|
| The supplied discussion identifies Isa, Rayan, Arshia, and Asmin and covers dependencies, ER design, the build, performance, update costs, index behavior, and design choice. | [group-discussion-notes.md](group-discussion-notes.md) | Rounds 1, 3–6 | General group discussion is now documented | Student-supplied notes and role allocation | **SUPPORTED BY STUDENT-PROVIDED NOTES** |
| The “Example Group Discussion” is illustrative, not a verified transcript. | [group-discussion-notes.md](group-discussion-notes.md) source note | General | The themes are publishable, but wording is not independently authenticated line by line | Explicit source label | **SUPPORTED WITH SOURCE LIMITATION** |
| The supplied group document allocates anomaly, build, race, price, and recommendation work. | Student's PDF-derived publication instructions; [cross-check](group-document-technical-crosscheck.md) | Rounds 2–6 | Supports group provenance; the PDF binary was unavailable for fresh visual inspection | Role table and technical cross-check | **SUPPORTED BY STUDENT-SUPPLIED PDF SUMMARY** |
| Curiosities remain prepared without a specifically documented swap. | [normalization-notes.md](normalization-notes.md) | Round 7 | General technical discussion does not prove the exact harvest gate | Eight sourced curiosities | **NOT SPECIFICALLY DOCUMENTED** |

The notes now establish real participants and subject areas. They do not establish a date,
location, verbatim transcript, or completion of every exact workbook gate, and none is inferred.

## Seven discussion gates

| Round | Required gate | What can be established | Status | Information the student should supply |
|---|---|---|---|---|
| 1 | Which arrow disappears in the second ER diagram? | Dependencies and ER separation discussed; exact arrow question absent | **SUPPORTED TOPIC; GATE NOT SPECIFICALLY DOCUMENTED** | Exact answer only if separately recorded |
| 2 | Can a neighbor break an anomaly statement? | PDF-derived anomaly work exists; no challenge is recorded | **NOT SPECIFICALLY DOCUMENTED** | Challenger and outcome only if separately recorded |
| 3 | Why does `part` contain 10 rows? | Rayan's 200k build role is supported; exact ten-part question absent | **SUPPORTED TOPIC; GATE NOT SPECIFICALLY DOCUMENTED** | Exact exchange only if separately recorded |
| 4 | Did both pods get the same plan? | Query performance discussed; no cross-pod plan comparison recorded | **SUPPORTED TOPIC; GATE NOT SPECIFICALLY DOCUMENTED** | Other pod's plan only if separately recorded |
| 5 | Could the neighbor predict the numbers? | Update and index results discussed; prediction exercise absent | **SUPPORTED TOPIC; GATE NOT SPECIFICALLY DOCUMENTED** | Prediction only if separately recorded |
| 6 | Could the student defend the memo against a “what if”? | Final design choice discussed; no literal what-if defense recorded | **SUPPORTED TOPIC; GATE NOT SPECIFICALLY DOCUMENTED** | Question/change only if separately recorded |
| 7 | Which curiosities did the pods identify? | Curiosity list exists; swap is absent from supplied notes | **NOT SPECIFICALLY DOCUMENTED** | Swap details only if separately recorded |

The supplied reflection and general discussion record are complete. Missing gate details should
remain “not specifically documented” unless a separate authentic record becomes available.

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

- The student supplied a final reflection and discussion notes naming Isa, Rayan, Arshia, and
  Asmin as the Module 5 group members.
- The notes cover dependencies, ER diagrams, the 200,000-row build, query performance, update
  amplification, index behavior, and the normalized/reporting design choice.
- The example dialogue is explicitly illustrative rather than a verified transcript.
- The notes do not map every exact workbook gate to a recorded question and answer.

### Part B — Possible reflection themes

- Comparing predictions with measurements.
- Explaining why only ten parts were generated.
- Comparing query plans or challenging an anomaly example.
- Defending the refresh strategy against a staleness question.

These themes are supported by the supplied notes; they are not used to invent additional rounds.

### Part C — Questions for the student

The final reflection is already supplied. Only if separate gate evidence is later needed:

1. Was any exact gate question asked word for word?
2. Was there a specific challenge, prediction, “what if,” or curiosity swap?
3. Did any answer change the technical artifact?

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
- The supplied group allocation documents Rayan's build/benchmark work, Arshia and Asmin's ER
  sketches, and Isa's dependencies, Round 5 measurements, and recommendation.

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
| Take-away | Yes | Yes, final supplied text | Published in `Reflections/ref05.md` |
| What was good? | Yes | Yes, final supplied text | Published |
| What was difficult? | Yes | Yes, final supplied text | Published |
| Exploration and show stoppers | Yes | Yes, final supplied text | Published |
| Interaction with peers and instructors | Yes for general discussion | Yes, final supplied summary and notes | Published; exact seven gates remain separately classified |
| How did you verify AI suggestions? | Yes | Yes, final supplied text | Published |
| Help and extra work | Yes | Yes, final supplied text | Published |

## Publication completion checklist

- [x] Publish the student's exact seven-section Reflection 05.
- [x] Publish the supplied group discussion notes with an illustrative-transcript disclaimer.
- [x] Record the four Module 5 group members and documented role allocation.
- [x] Cross-check the supplied group-document claims against the executable portfolio.
- [x] Keep different benchmark runs separate.
- [x] Preserve unknown individual gates as not specifically documented.
- [x] Check technical numbers against the linked evidence.

No reflection rewrite remains. Only optional round-specific gate provenance could be added if a
separate authentic record becomes available.
