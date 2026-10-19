# Module 2 technical completion report

## A. Executive summary

The mandatory technical work is complete and reproducible. The repository now
contains the supplied legacy fixture, four ER exercises, a corrected conceptual
model, executable cardinality and integrity audits, Pydantic 2 models,
SQLAlchemy 2 tables, generated SQLite DDL, and 11 automated tests. A fresh
rebuild reproduced all five intended defects and all tests passed.

The optional EER and Mermaid stretchers were also attempted. Human activities
remain pending: personal study and reflection, pod and cross-pod discussion,
peer review/checkpoint, diagram selection, and Discord posting.

## B. Repository and environment

| Item | Recorded value |
|---|---|
| Repository | https://github.com/isa-babayev-ibabayev/databases-portfolio |
| Branch | `main` |
| Initial HEAD | `84f5fcb47c271987fe5fec5ab3a2ab31c74f7799` |
| Technical implementation HEAD before this report | `b7f1a8c` |
| First complete report push | `4d9a8f8` on `origin/main` |
| Final delivery commit | See final `git log -1` and delivery response; a commit cannot contain its own hash without changing that hash |
| Push | Succeeded to `origin/main`; this factual status update is pushed in the final delivery commit |
| uv-managed Python | 3.14.5 |
| Python `sqlite3` | 3.50.4 |
| SQLite CLI | 3.53.4 |
| uv | 0.11.16 |
| Pydantic | 2.14.1 |
| SQLAlchemy | 2.1.5 |
| Working directory | `module-02/` |

The earlier `Module02/` directory contained a placeholder and was preserved.

## C. Preservation of Module 1

`git diff --exit-code -- module-01` returned exit code 0 after the clean-room
audit. No Module 1 file was staged or committed. The only intentional change
outside `module-02/` is one navigation link added to the root `README.md`.
The pre-existing untracked root `main.py` was not staged. Generated `*.db`
files remain ignored.

## D. Requirement-by-requirement comparison

| Professor requirement | Evidence | Verification | Status |
|---|---|---|---|
| Goal 1: reconstruct ER/EER | [er-audit.md](er-audit.md) | Entities, keys, diagram, observed/intended/enforced cardinalities compared | PASS |
| Goal 2: integrity auditing | [integrity-audit.sql](integrity-audit.sql), [integrity-results.txt](integrity-results.txt) | Five queries executed on rebuilt fixture | PASS |
| Goal 3: model decisions | [er-examples.md](er-examples.md) | Four relationship exercises with key choices | PASS |
| Goal 4: code-first contract | [contract.py](contract.py), [corrected-schema.sql](corrected-schema.sql) | Schema built; DDL loaded into SQLite; tests passed | PASS |
| Goal 5: missing rules | [integrity-audit.md](integrity-audit.md) and section H below | Rules allocated to application/database | PASS |
| Task A: references and technical log | [study-log.md](study-log.md) | Official sources checked; Q&A verified experimentally | PASS (technical) |
| Task A: genuine study | [study-log.md](study-log.md) | Requires student confirmation | PENDING |
| Task B: four sketches | [er-examples.md](er-examples.md) | Mermaid source reviewed; SQL proof executed | PASS |
| Task B: student can explain diagrams | Human checkpoint | No evidence yet | PENDING |
| Task C: pod exchange and agreed learning | Pending section in [study-log.md](study-log.md) | No meeting evidence supplied | PENDING |
| Task C: Discord share | Suggested caption only | Nothing posted | PENDING |
| Studio 1: reconstruct model | [er-audit.md](er-audit.md) | Counts and token split executed | PASS |
| Studio 2: five defects | Audit SQL/results/analysis | Exact anomalies reproduced | PASS |
| Studio 3: contract | Contract, DDL, tests | 11/11 tests pass | PASS |
| Reflection four questions | [reflection.md](reflection.md) | Technical claims trace to outputs | PASS (draft) |
| Personal reflection | Personal section | Student review required | PENDING |
| Optional 4: EER inheritance | [eer-stretcher.sql](eer-stretcher.sql) | Both schemas executed; expected failures captured | PASS (optional) |
| Optional 5: Mermaid lab | [mermaid-lab.md](mermaid-lab.md) | Three diagrams and round-trip critique prepared | PARTIAL (optional; no CLI render/Discord) |

## E. Files created or modified

| File | Purpose |
|---|---|
| `README.md` | Adds Module 2 navigation only |
| `module-02/README.md` | Evidence index and reproduction commands |
| `baseline.txt` | Initial Git, folder, and environment state |
| `legacy_setup.sql` | Authoritative flawed fixture |
| `cardinality-audit.sql`, `cardinality-results.txt` | Executable relationship evidence and output |
| `integrity-audit.sql`, `integrity-results.txt`, `integrity-audit.md` | Five defects, output, impact, and repairs |
| `sketch-proof.sql`, `sketch-proof-results.txt` | 1:n count and rejected orphan |
| `er-examples.md` | Four required modeling exercises |
| `er-audit.md` | Legacy reconstruction and corrected diagram |
| `contract.py` | Pydantic and SQLAlchemy contract plus DDL CLI |
| `corrected-schema.sql` | Generated corrected SQLite DDL |
| `tests/test_contract.py` | Isolated application and DB tests |
| `test-results.txt` | Captured 11-test passing run |
| `study-log.md` | References, questions, AI checks, diagram references, human placeholders |
| `reflection.md` | Four-question technical reflection plus personal placeholder |
| `eer-stretcher.sql`, `eer-stretcher-results.txt` | Optional inheritance comparison |
| `mermaid-lab.md` | Optional diagram collection and round trip |
| `technical-completion-report.md` | This independent-review handoff |

## F. Commands actually executed

```powershell
git status --short --branch
git log -1 --format='%H%n%h %s%n%ci'
git remote -v
git fetch origin
git rev-list --left-right --count origin/main...HEAD
uv run python --version
uv run python -c "import sqlite3,pydantic,sqlalchemy; ..."
sqlite3 module-02/legacy.db ".read module-02/legacy_setup.sql"
sqlite3 module-02/legacy.db ".read module-02/integrity-audit.sql"
sqlite3 module-02/legacy.db ".read module-02/cardinality-audit.sql"
sqlite3 module-02/sketch-proof.db ".read module-02/sketch-proof.sql"
uv run python module-02/contract.py --database module-02/corrected.db --ddl-output module-02/corrected-schema.sql
sqlite3 :memory: ".read module-02/corrected-schema.sql" ".tables"
uv run python -m unittest discover -s module-02/tests -v
sqlite3 module-02/eer-fresh.db ".read module-02/eer-stretcher.sql"
git diff --exit-code -- module-01
```

The full clean audit used fresh ignored database names
`audit-fresh.db`, `sketch-fresh.db`, `contract-fresh.db`, and
`eer-fresh.db`.

## G. Database audit results

Legacy counts were Machine 4, Part 4, and MaintenanceJob 4.

| Defect | Actual result | Production impact | Correction |
|---|---|---|---|
| Orphan job | job 3 → `cnc-05` | Cannot attach maintenance/site history reliably | Non-null machine FK |
| Duplicate natural key | `P-1003` has 2 copies | Ambiguous updates and duplicate joins | PK/UNIQUE on part number |
| TEXT price | text query omitted both 9.90 rows | Wrong price filters/invoices | Decimal validation, NUMERIC and CHECK |
| Invalid date | `RANDOM-NAME → unknown` | Sorting/age calculations fail | Real date parsing; quarantine bad row |
| Comma list | job 1 vanished; job 2 doubled | Incomplete and duplicated reports | JobPart junction |

Cardinality findings: one job contains two encoded parts, `cnc-01` occurs in
two jobs, there are three technician strings, `P-1001` occurs in two jobs,
and only three of four jobs match a machine. These are observations of the
fixture, not proof of universal business limits.

## H. Data contract and missing business rules

Pydantic models validate positive IDs, required/trimmed strings, `SN-`
prefixes, real calendar dates, `P-<digits>` part numbers, nonnegative bounded
`Decimal` prices, and unique structured part lists.

SQLAlchemy defines Machine, Technician, MaintenanceJob, Part, and JobPart.
Database guarantees include primary keys, unique machine serial and technician
name, foreign keys, non-null fields, a nonnegative price check, and a composite
JobPart primary key. A connection event enables `PRAGMA foreign_keys = ON`;
the program printed `foreign_keys=1`.

Application validation gives useful input errors and validates calendar dates.
Database constraints remain authoritative across all writers for identity,
uniqueness, references, and shared numeric invariants. SQLite's dynamic type
system means `NUMERIC(9,2)` alone is not perfect domain validation.

Migration must not silently repair the fixture: orphan job 3, duplicate
`P-1003`, `unknown`, and each list token require an exception/owner decision.

## I. Test results

Eleven tests ran and eleven passed; zero failed.

Pydantic tests:

- valid models and structured parts;
- invalid serial number;
- invalid installation date;
- missing required attribute;
- invalid negative price;
- duplicate part in job.

Database tests:

- duplicate machine serial rejected;
- orphan machine reference rejected;
- duplicate job-part rejected;
- correct m:n rows accepted;
- negative price rejected.

The first development run had six Pydantic import errors and one DDL formatting
exception. These were fixed by avoiding postponed annotations in the
dynamically loaded test module and converting the DDL compiler to text before
normalization. The recorded final run is green.

## J. Human participation pending

- Genuinely study the concepts and record the date/duration.
- Review every diagram and practice explaining keys and cardinalities.
- Rewrite or confirm the personal reflection in the student's own voice.
- Discuss the work with the Task Pod and another pod.
- Record three to five genuinely agreed lessons and any disagreement.
- Obtain real peer-review/checkpoint feedback.
- Select one diagram with the pod and post it to Discord.
- Add the real discussion, reviewer, and Discord evidence.

## K. Risks and limitations

- The official workbook marks content below its draft boundary as provisional.
- The fixture is tiny; observed counts do not establish business-wide
  cardinality.
- SQLite has no native strict calendar-date type; Pydantic performs the strong
  parse in this implementation.
- A 1:1 child FK plus uniqueness enforces at most one child, not mandatory
  existence of a child for every parent.
- Mermaid CLI was not installed. Syntax was checked against Mermaid's official
  ER grammar and uses standard GitHub-supported `erDiagram`; visual rendering
  should still be inspected on GitHub after push.
- External links can change. The official workbook, SQLite, Mermaid, Pydantic,
  and SQLAlchemy sources were accessed during this work.

## L. Recommended independent-review checks

1. Run the README commands from a fresh clone.
2. Confirm the intentional SQL errors are followed by unchanged counts.
3. Compare every Mermaid edge with the DDL foreign keys and nullability.
4. Check the text-vs-numeric price counterexample.
5. Confirm all `*.db` files are ignored and `main.py` is absent from commits.
6. Confirm `git diff 84f5fcb..HEAD -- module-01` is empty.
7. Render the Mermaid blocks in GitHub and inspect labels visually.

## M. Final status

**Technical implementation complete, human activities pending.**

This status does not claim academic completion, pod participation, peer
approval, personal study, or Discord submission.
