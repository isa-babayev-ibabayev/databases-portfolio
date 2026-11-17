# Independent Audit Verification — 2026-11-17

This is a new verification run. It does not replace the preserved historical benchmark in
`benchmark-results.json`, because timing values depend on machine load and cache state.

## Workbook comparison

The current official raw `main` workbook was reviewed on 2026-11-17. The current attachment
directory contained the audit prompt but no second standalone workbook file to diff line by line.
The prompt's seven-round checklist agrees with the official structure. Relevant current details
are: every round has a nearest-pod gate; Rounds 5–7 are homework; the report-index removal is an
explicit negative-result experiment; and DuckDB is an optional bridge to Module 6a. No material
conflict between the supplied checklist and the accessible official workbook was found.

## Environment and safety boundary

- Windows 11 (`Windows-11-10.0.26300-SP0`)
- Python 3.14.5
- SQLite 3.50.4
- uv 0.11.16
- Benchmark trials: 7, warmed and alternated by the existing harness
- Benchmark database: disposable temporary database
- Anomaly database: disposable in-memory database
- Preserved `normalize.db` SHA-256 before and after verification:
  `BCCCA944EEBFF2C42D18DA737F251587CAFB6EB93D84E561D1FCE9BEA6BA4C3D`

## Deterministic verification

| Check | Result |
|---|---:|
| `flat_jobpart` | 200,000 rows |
| `machine` | 50 rows |
| `part` | 10 rows |
| `job` | 20,000 rows |
| `job_part` | 200,000 rows |
| `report_jobpart` | 200,000 rows |
| Dashboard groups | 350 |
| Normalized/denormalized dashboard equality | true |
| Flat minus reconstructed join | 0 |
| Reconstructed join minus flat | 0 |
| `PRAGMA foreign_key_check` | 0 violations |
| `PRAGMA integrity_check` | `ok` |
| Normalized update rows | 1 |
| Denormalized update rows | 4,000 |
| Both update rollbacks | verified |
| Report index restored | verified |

The anomaly demonstration also reproduced the expected outcomes: the partial `cnc-01` update
created one Bielefeld row and two Gütersloh rows; the unused part required a NULL-filled flat
placeholder but inserted independently into `part`; deleting the only flat `P-0002` row removed
its flat price while the normalized part remained.

## Isolated timing rerun

| Measurement | Seven-run median |
|---|---:|
| Normalized dashboard | 105.2740 ms |
| Indexed denormalized dashboard | 122.0734 ms |
| Normalized site update | 1.4530 ms |
| Denormalized site update | 10.1288 ms |
| Indexed report in index experiment | 120.9963 ms |
| Unindexed report in index experiment | 88.5278 ms |

The new run agrees with the historical conclusion: the indexed report did not beat the
normalized join, and removing `ix_report_machine` improved this broad aggregation. These new
numbers are audit evidence only; the recommendation continues to cite the original saved run so
the portfolio does not silently rewrite measurements.

## Actual plans

Normalized dashboard:

```text
SCAN jp
SEARCH j USING INTEGER PRIMARY KEY (rowid=?)
SEARCH m USING INDEX sqlite_autoindex_machine_1 (machine_id=?)
SEARCH p USING INDEX sqlite_autoindex_part_1 (part_no=?)
USE TEMP B-TREE FOR GROUP BY
USE TEMP B-TREE FOR ORDER BY
```

Indexed report:

```text
SCAN report_jobpart USING INDEX ix_report_machine
USE TEMP B-TREE FOR GROUP BY
USE TEMP B-TREE FOR ORDER BY
```

Unindexed report:

```text
SCAN report_jobpart
USE TEMP B-TREE FOR GROUP BY
USE TEMP B-TREE FOR ORDER BY
```

## Storage reproduction

`dbstat`, 4,096-byte pages:

| Scope | Normalized | Denormalized |
|---|---:|---:|
| Tables only | 4,071,424 bytes / 3,976.0 KiB | 11,091,968 bytes / 10,832.0 KiB |
| Relevant tables and indexes | 8,167,424 bytes / 7,976.0 KiB | 14,082,048 bytes / 13,752.0 KiB |

The preserved database file is 37,134,336 bytes (35.414 MiB). That file size includes all
tables, indexes, schema, and database pages and must not be confused with the object-level
`dbstat` table comparison.

## Automated verification

```text
uv run python -B -m unittest discover -s Module05/tests -v
Ran 31 tests in 7.804s
OK
```

The first development run of a new README assertion failed because the expected phrase crossed a
Markdown line wrap. The README was correct; the assertion was fixed to normalize whitespace and
the full suite then passed. The suite used temporary databases and left the preserved database
hash unchanged.
