# Decision Record — Polyglot Persistence Boundary

**Status:** Proposed technical position — student to review and defend

**Date:** 2026-11-17

**Scope:** Factory telemetry portfolio; evidence-based engine selection, not an engine popularity ranking

## Decision

Use the smallest number of engines that gives each workload an acceptable operational
boundary. Keep SQLite as the authoritative operational store for constrained ingestion,
JSON metadata, and the current dashboard-session workload. Export an immutable analytical
snapshot to Parquet and query it with DuckDB for large scans and aggregations. Consider
PostgreSQL when authenticated multi-user server operation becomes a verified requirement;
no shared PostgreSQL result is claimed in this record.

| Workload | Engine and representation | Why this choice fits | Verified evidence | Cost accepted | What breaks if stale or missing? |
|---|---|---|---|---|---|
| Month-end analytical report | DuckDB over a versioned Parquet snapshot | Columnar scan and vectorized aggregation fit a two-million-row report. | In Module 6a, the dashboard query changed from **5,832.15 ms** in SQLite to **74.13 ms** in DuckDB (78.67×); the monthly query changed from 7,013.05 ms to 74.27 ms (94.43×). The refreshed Parquet file was 2,468,865 bytes; the earlier measured Task 2 export was 2,323,412 bytes. | A refresh pipeline, another file format, and snapshot version/freshness metadata. | Reports can be fast but wrong: late readings are absent and dashboard/report totals diverge from the operational database. |
| Sensor/job ingestion and integrity | SQLite normalized tables with transactions, foreign keys, checks, and conditional UPSERT | The local workload needs atomic batches and enforceable keys more than distributed scale. | Module 4 recorded **34 passing tests**. Two normal imports ended with 4 readings, zero duplicate natural keys, and one audit row; an invalid foreign-key batch rolled back. | Single-host deployment and one-writer-at-a-time behavior. | Without the database or enabled constraints, ingestion stops or accepts orphaned/invalid rows; without idempotency, replays duplicate facts. |
| Vendor-specific device metadata | SQLite `STRICT` table with validated JSON text plus expression indexes for selected paths | Relational identity stays constrained while optional vendor fields can vary. | This module stored **1,000/1,000 valid JSON rows**. The exact `json_extract(meta, '$.vendor')` expression used `ix_device_vendor`; the equivalent `->>` query scanned. Invalid JSON and a BLOB in the TEXT column were rejected. | JSON shape is only partly constrained; important paths need explicit checks/indexes, and queries must match expression indexes. | Missing metadata may be tolerable, but malformed or silently unindexed metadata queries can break filtering performance or downstream assumptions. |
| Dashboard session state | SQLite key/value table for now | The benchmark showed a very fast batched transactional write and SQLite supplies transactions, SQL inspection, constraints, and a clearer concurrency path. | At 20,000 pairs over five fresh trials, SQLite median write was **46.02 ms** versus shelve **13,381.62 ms**. Shelve median lookup was faster: **235.54 ms** versus SQLite **1,375.72 ms** for 20,000 individual lookups. Counts and SHA-256 digests matched. | SQLite individual lookup overhead was about 5.84× higher in this Python benchmark. | Lost session state mainly logs users out or resets filters; that lower business impact permits a simpler store, but corruption or a locked store still degrades the dashboard. |
| Concurrent multi-user operational service | PostgreSQL only after a real need and authenticated verification; SQLite remains the current local implementation | PostgreSQL adds a server, session isolation, richer concurrent-writer behavior, roles, and operational administration. Those costs need a demonstrated requirement. | Local evidence only: two SQLite writers produced `database is locked`, then a retry succeeded and final counter was 2. **Shared PostgreSQL observation is pending.** | Network/service administration, credentials, backups, migrations, monitoring, and a larger failure surface. | With SQLite under sustained writer contention, requests can wait or fail unless transactions are short and retry policy is deliberate. A server outage would instead affect every connected client. |

## Why not “one database for everything”?

SQLite can execute the analytical query correctly, but the verified two-million-row results
showed seconds rather than tens of milliseconds. DuckDB is therefore justified at the
analytical boundary. Conversely, using DuckDB for row-by-row operational ingestion would
sacrifice the already verified SQLite constraint/UPSERT workflow, and Module 6a measured
DuckDB's boundary insert/lookup experiment as substantially slower for that pattern.

## Consistency and recovery boundaries

- SQLite is the source of truth for operational facts. Transactions protect each ingestion
  batch; foreign keys must be enabled per connection.
- The Parquet file is a rebuildable analytical projection, not a second writable source of
  truth. Its identity must include source row count, maximum source timestamp, export time,
  and checksum or equivalent snapshot identifier.
- JSON metadata is valid JSON but not automatically a complete business schema. Stable,
  mandatory fields belong in relational columns or require explicit checks/application
  validation.
- Session state is disposable compared with production facts. Its recovery objective can be
  weaker, but a corrupt or unavailable store must fail visibly and be replaceable.
- A future PostgreSQL move would require measured concurrent load, transaction semantics,
  migration and rollback plans, least-privilege roles, backup/restore testing, and monitoring.

> **If Kortmann could run only one engine, which would it be—and what would break first?**
> **Proposed technical position — student to review and defend:** SQLite, because losing the
> operational constraints and transaction path would threaten authoritative facts. The
> month-end analytical report would break first as data volume grows: the verified dashboard
> query took 5,832.15 ms in SQLite versus 74.13 ms in DuckDB.

## Peer-defense record

**Peer/instructor feedback:** STUDENT INPUT REQUIRED — record the real question or objection.

**Change made after discussion:** STUDENT INPUT REQUIRED — record a genuine change, or state
that no change was made and why.

**Final acceptance:** STUDENT INPUT REQUIRED.
