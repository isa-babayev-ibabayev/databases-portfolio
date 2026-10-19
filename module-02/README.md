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

## Learning goals

1. Reconstruct an ER/EER model from SQL.
2. Prove integrity defects with queries.
3. Justify entities, attributes, relationships, keys, and cardinalities.
4. Express a corrected contract in Pydantic and SQLAlchemy.
5. State and enforce missing business rules.

## Human work still required

The technical exercises are reproducible. Personal study, personal reflection,
pod discussion, peer review, and Discord sharing are explicitly marked pending
in [study-log.md](study-log.md) and [reflection.md](reflection.md).

The pre-existing `Module02/` directory is retained unchanged because it
contains an older placeholder. Canonical assessed evidence is here in
`module-02/`.
