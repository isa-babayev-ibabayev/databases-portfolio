# Module 6b Project-Ticket Candidates

These are reproducible candidates, not a claim that a final project was selected.

## Candidate A — Maintenance planner: recurring failures and part demand

- **Person/role:** maintenance planner at a small factory.
- **Problem:** recurring machine failures and future spare-part demand are difficult to see
  from isolated work orders.
- **First query:** rank machines by repeat maintenance jobs and total parts used per month.
- **Reproducible data source:** the repository's Module 2 corrected maintenance schema and
  deterministic fixture/test data; expand only with a documented seeded generator.
- **Decision enabled:** which machine and part family should be investigated or stocked first?

## Candidate B — Production engineer: trustworthy telemetry anomalies

- **Person/role:** production engineer responsible for sensor quality.
- **Problem:** duplicate, late, or invalid readings can make an alert or dashboard misleading.
- **First query:** list sensors and hourly windows with duplicate natural keys, missing expected
  intervals, or values outside the configured range.
- **Reproducible data source:** Module 4 ingestion fixtures and audit log, plus a seeded extension
  that preserves `(sensor_id, ts)` as the natural key.
- **Decision enabled:** which data pipeline or sensor requires intervention before analysis?

## Candidate C — Operations manager: fresh month-end performance report

- **Person/role:** operations manager comparing factory lines.
- **Problem:** the operational database is slow for large report scans, while a stale snapshot
  can produce a fast but incorrect report.
- **First query:** compare monthly output and average sensor value by site, with snapshot age and
  source row-count reconciliation shown alongside the result.
- **Reproducible data source:** Module 6a's deterministic `seed.py` and export workflow.
- **Decision enabled:** which line should receive process-improvement attention, and is the
  evidence fresh enough to trust?

## Selection gate

**Final project selection: STUDENT INPUT REQUIRED.** Choose one real person/problem after
discussion, then record the genuine reason. Do not present a generated candidate as a
completed human decision.
