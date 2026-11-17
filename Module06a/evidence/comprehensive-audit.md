# Module 6a comprehensive audit — 2026-11-17

The audit began at commit `0642e55` on `main`, synchronized with `origin/main`.
The only working-tree item was the unrelated untracked root `main.py`; it was
left untouched. The official workbook `main` revision was retrieved again on
2026-11-17. Its learning goals are authoritative and its detailed exercises
remain below the explicit provisional-draft boundary.

## Directory mapping

| Directory | Purpose | Existing content at audit start | Problem | Action |
|---|---|---|---|---|
| `Module06a` | Canonical analytical-engine studio | Six core scripts, compression, notes, guide, evidence, and 16 tests | Intense track, S1, and S2 absent | Preserve core; add optional extensions |
| `Module06` | Possible earlier Module 6 | Did not exist | None | No directory created or merged |
| `Module06A` | Case variant on Windows | Resolves to `Module06a` | Not an independent directory | Use canonical tracked spelling `Module06a` |
| `Module05` | Read-only source dependency | `normalize.db`, 200,000 report rows | None | Preserve and hash before/after |
| `Reflections` | Student academic record | Honest `ref06a.md` draft | Personal sections incomplete by design | Leave human-owned |

No Module 6b implementation was mixed into Module 6a.

## Initial requirement audit

| Requirement | Initial status | Existing evidence | Missing or incorrect item | Action |
|---|---|---|---|---|
| Task 1 — Build | PASS | `prepare.py`, history evidence, real generated data | One period-6 date typo in compact evidence | Correct evidence only |
| Task 2 — Convert | PASS | `to_parquet.py`, Parquet evidence | None | Preserve |
| Task 3 — Race | PASS | `race.py`, samples, summary | None; engine-specific `strftime` already correct | Preserve historical timings |
| Task 4 — Plan | PASS | `plan.py`, real captured plan | None | Preserve |
| Task 5 — Boundary | PASS | `boundary.py`, five-run evidence | None | Preserve unexpected `executemany` result |
| Task 6 — Decide | PASS | Seven-sentence memo | Intense-track check limitation not yet stated | Extend memo without exceeding eight sentences |
| Task 7 — Core homework | PASS | `compression.py`, size evidence, refresh/failure prose | None | Reverify after direct-history refresh |
| Intense Track `refresh.py` | OPTIONAL NOT STARTED | Refresh design only | Script, two runs, check, mismatch test absent | Implement and test |
| S1 — JSON | OPTIONAL NOT STARTED | None | `json_read.py` and evidence absent | Implement and test |
| S2 — Parquet statistics | OPTIONAL NOT STARTED | None | Sorted copy and metadata experiment absent | Implement and measure |
| S3 — Compression | OPTIONAL COMPLETE | `compression.py`, evidence | None | Reverify current refreshed file |
| Technical notes | PARTIAL | Tasks 1–6 recorded honestly | No Task 7/intense/S1/S2 sections | Append executed evidence |
| Learning guide | PARTIAL | Complete six-round guide | No implemented refresh or optional results | Add focused sections |
| README | PARTIAL | Core commands and evidence | No optional commands/status | Add only tested commands |
| Tests | PASS for existing scope | 16/16 passed at audit start | No refresh/S1/S2 coverage | Extend suite |
| Portfolio evidence | PARTIAL | All required core evidence | Optional outputs absent | Add compact evidence files |
| Student reflection | HUMAN REQUIRED | Honest structure exists | Student experience still required | Do not invent content |
| Peer discussions | HUMAN REQUIRED | Six prepared questions | No genuine discussion evidence | Leave pending |

## Core re-verification before changes

- `uv run python -B -m unittest discover -s Module06a/tests -v`: 16 tests,
  all passed in 16.754 seconds.
- `prepare.py`: reused validated files; 2,000,000 history rows; source hash
  unchanged.
- `to_parquet.py`: reused validated Parquet; count, sums, dates, schema, and
  null counts matched.
- UTF-8 inspection found U+00FC in source `Gütersloh` and bytes `C3 BC` in the
  CSV; no replacement-character bytes were present.
- Module 5 SHA-256 before changes:
  `BCCCA944EEBFF2C42D18DA737F251587CAFB6EB93D84E561D1FCE9BEA6BA4C3D`.
