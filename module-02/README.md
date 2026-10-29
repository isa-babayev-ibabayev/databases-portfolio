# Module 2 — Data Contracts and Legacy Schema Audits

This directory reconstructs and audits the deliberately flawed maintenance
database from the official Module 2 workbook. Generated database files are
ignored; every result can be rebuilt from source.

## Evidence map

- [Learning goals and study material](study-log.md)
- [Four ER modeling exercises](er-examples.md)
- [Legacy database fixture](legacy_setup.sql)
- [Reconstructed model and cardinality audit](er-audit.md)
- [Cardinality queries](cardinality-audit.sql) and [actual results](cardinality-results.txt)
- [Five integrity-defect queries](integrity-audit.sql), [actual results](integrity-results.txt), and [analysis](integrity-audit.md)
- [Pydantic and SQLAlchemy contract](contract.py)
- [Generated corrected DDL](corrected-schema.sql)
- [Automated tests](tests/test_contract.py) and [test output](test-results.txt)
- [Reflection](reflection.md)
- [Technical completion report](technical-completion-report.md)

## Reproduce on Windows PowerShell

```powershell
uv sync
sqlite3 module-02/legacy.db ".read module-02/legacy_setup.sql"
sqlite3 module-02/legacy.db ".read module-02/integrity-audit.sql"
sqlite3 module-02/legacy.db ".read module-02/cardinality-audit.sql"
sqlite3 module-02/sketch-proof.db ".read module-02/sketch-proof.sql"
uv run python module-02/contract.py --database module-02/corrected.db --ddl-output module-02/corrected-schema.sql
uv run python -m unittest discover -s module-02/tests -v
```

The constraint error in the sketch proof is intentional evidence that the
orphan insert was rejected. The databases are disposable and excluded by
`.gitignore`.

## Learning Goals — Verification Evidence

### Learning Goal 1 — Reconstruct an ER/EER model

**Learning goal:** Reconstruct an ER/EER model (entities, attributes, keys, relationships, cardinalities) from an undocumented SQL schema.

**Verification evidence:**
- [er-audit.md](er-audit.md) — identifies the entities, attributes, natural and surrogate keys, relationships, corrected ER diagram, and observed, intended, and enforced cardinalities.
- [legacy_setup.sql](legacy_setup.sql) — provides the original undocumented and deliberately unconstrained SQL schema that was reconstructed.
- [cardinality-audit.sql](cardinality-audit.sql) — contains the queries used to establish cardinalities from data rather than assumptions.
- [cardinality-results.txt](cardinality-results.txt) — records the executed counts, including the hidden many-to-many part relationship and the orphan job.

### Learning Goal 2 — Identify integrity defects with queries

**Learning goal:** Identify integrity defects — missing foreign keys, orphan rows, redundant data, normalization violations — with queries, not intuition.

**Verification evidence:**
- [integrity-audit.sql](integrity-audit.sql) — contains executable queries for the orphan reference, duplicate part, TEXT price comparison, invalid date, and comma-separated many-to-many defect.
- [integrity-results.txt](integrity-results.txt) — records the actual output produced by all five defect queries.
- [integrity-audit.md](integrity-audit.md) — explains each proven defect, its production consequence, and an appropriate migration or schema correction without claiming the legacy fixture was repaired.

### Learning Goal 3 — Distinguish entities, relationships, attributes, and keys

**Learning goal:** Distinguish an entity relationship from an attribute, and a surrogate key from a natural key, and justify the choice.

**Verification evidence:**
- [er-examples.md](er-examples.md) — documents the required 1:1, 1:n, m:n, and MaintenanceJob modeling exercises and justifies entity, attribute, foreign-key, natural-key, and surrogate-key choices.
- [er-audit.md](er-audit.md) — applies those distinctions to the inherited maintenance schema.
- [sketch-proof.sql](sketch-proof.sql) — provides an executable 1:n machine-to-sensor model with a foreign-key constraint and count query.
- [sketch-proof-results.txt](sketch-proof-results.txt) — records two sensors for one machine and the rejected orphan-sensor insertion.

### Learning Goal 4 — Express an enforceable code-first data contract

**Learning goal:** Express a schema as a code-first data contract (Pydantic / SQLAlchemy) that an application can enforce.

**Verification evidence:**
- [contract.py](contract.py) — defines Pydantic input models, SQLAlchemy tables, constraints, a normalized junction table, and automatic SQLite foreign-key enforcement.
- [corrected-schema.sql](corrected-schema.sql) — records the generated database contract with primary keys, foreign keys, uniqueness, non-null fields, checks, and the JobPart composite key.
- [tests/test_contract.py](tests/test_contract.py) — asserts application validation, database constraints, and the many-to-many relationship.
- [test-results.txt](test-results.txt) — records the successful run of all 11 automated contract tests.

### Learning Goal 5 — Recover the business rules the legacy schema omitted

**Learning goal:** Write the requirements the schema forgot: the business rules nobody encoded.

**Verification evidence:**
- [integrity-audit.md](integrity-audit.md) — derives missing identity, reference, value, date, and relationship rules from proven legacy defects.
- [contract.py](contract.py) — enforces application rules for identifiers, serial and part formats, real dates, nonnegative prices, required values, structured part lists, and duplicate associations.
- [corrected-schema.sql](corrected-schema.sql) — enforces shared database rules through keys, foreign keys, uniqueness, non-null constraints, checks, and a junction table.
- [tests/test_contract.py](tests/test_contract.py) — verifies that representative invalid values, orphan references, duplicate serials, negative prices, and duplicate job-part associations are rejected.

**Enforcement note:** Pydantic validates real calendar dates; the SQLite DDL requires a non-null `DATE` value but does not by itself guarantee full calendar validity.

## Human work still required

The technical exercises are reproducible. Personal study, personal reflection,
pod discussion, peer review, and Discord sharing are explicitly marked pending
in [study-log.md](study-log.md) and [reflection.md](reflection.md).

The pre-existing `Module02/` directory is retained unchanged because it
contains an older placeholder. Canonical assessed evidence is here in
`module-02/`.
