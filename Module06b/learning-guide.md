# Learning Guide — Polyglot Persistence and the Decision

## 1. Begin with the decision, not the product name

Polyglot persistence means deliberately using more than one data representation or engine
because workloads have different requirements. It does not mean collecting databases. A good
decision begins with questions such as:

1. What is the unit of truth: a transaction, a document, a key/value, or a scan-oriented file?
2. Which rules must the store enforce?
3. Is the dominant operation a small indexed lookup, a write transaction, or a large scan?
4. How many independent writers exist?
5. What happens if the data is stale, unavailable, duplicated, or lost?
6. Can a secondary representation be rebuilt from an authoritative source?

In this portfolio, the answers create a useful boundary: SQLite owns operational facts;
Parquet is a rebuildable snapshot; DuckDB reads that snapshot for analytics; JSON holds variable
metadata inside a constrained relational row.

## 2. Embedded versus server database

SQLite is an embedded database. The application process loads a library and reads/writes a
local file. There is no separate database server to authenticate network clients. This makes
installation, copying, and local reproducibility excellent, but writes serialize through file
locking. Transactions should therefore be short and retries deliberate.

PostgreSQL is a database server. Clients communicate over a network protocol and the server
owns connections, roles, sessions, locks, logs, and durable storage. Multiple transactions can
operate concurrently, and MVCC lets readers observe a consistent snapshot while other
transactions write. The benefits come with operational work: credentials, TLS/SSL choices,
availability, backups, migrations, monitoring, and network failures.

### Local two-writer experiment

The local script performs this timeline:

```text
connection A: BEGIN IMMEDIATE -> UPDATE (+1) -> hold lock
connection B: BEGIN IMMEDIATE -> wait -> "database is locked"
connection A: COMMIT
connection B: retry -> UPDATE (+1) -> COMMIT
final value: 2
```

The recorded wait was 362.23 ms with a configured 250 ms busy timeout. Timing is scheduler and
filesystem dependent; the important evidence is the controlled lock, visible error, successful
retry, and correct final state.

### Common mistakes

- Treating two GUI tabs as independent sessions without checking.
- Assuming `INTEGER PRIMARY KEY` means the same auto-generation behavior in every engine.
- Holding a transaction open while waiting for user or network input.
- calling a local SQLite simulation a PostgreSQL result.
- committing hostnames, usernames, or passwords to a portfolio.

### Explain it to a professor

“SQLite links the database into the application and protects concurrent writes with file-level
coordination. My two-connection experiment made that boundary observable. PostgreSQL is a
separate authenticated server with its own session and transaction manager. I have documented
the classroom procedure, but I do not claim server observations without credentials and a real
second session.”

### Check your understanding

**Q: Does `database is locked` mean SQLite corrupted the data?**

A: No. The failed writer did not commit. After the first transaction committed, a controlled
retry succeeded and the final value reflected both increments.

**Q: Why is the local demo not a substitute for PostgreSQL?**

A: The engines have different concurrency implementations and failure surfaces. The demo proves
only the SQLite behavior that was actually executed.

**Q: When might PostgreSQL become justified?**

A: When independently authenticated users, sustained concurrent writers, centralized access,
roles, remote availability, or server-side administration become measured requirements.

## 3. JSON inside a relational database

### Business problem

Every device has a stable identity and name, but vendors describe different optional details:
some supply a calibration date, some only firmware, and a molder may add nozzle diameter.
Creating a nullable column for every possible vendor field produces a wide, sparse table. A JSON
attribute can preserve the common relational identity while allowing the optional shape to vary.

### Schema

```sql
CREATE TABLE device (
    device_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    meta TEXT NOT NULL CHECK (json_valid(meta))
) STRICT;
```

This combines three different protections:

- relational identity (`device_id`) and a required name;
- STRICT storage type for the column;
- syntactically valid JSON enforced by `json_valid`.

It does **not** require a vendor key, enforce the type of every nested value, or guarantee that
every vendor follows a shared JSON Schema.

### JSON vocabulary used here

- A **JSON object** is a collection inside `{}` such as `{"vendor":"Siemens"}`.
- A **key** is an object member name such as `vendor`; its **value** is `Siemens`.
- A **JSON path** such as `$.vendor` locates a value from the document root `$`.
- **Extraction** reads the value at a path using `json_extract` or `->>`.
- **Validation** checks whether the stored text is syntactically JSON; here the database enforces
  it with `CHECK(json_valid(meta))`.
- **`json_each`** exposes each immediate member of an object (or element of an array) as a row.

### Querying scalar values and object members

```sql
SELECT name, json_extract(meta, '$.vendor') AS vendor
FROM device
ORDER BY device_id;
```

`json_extract` returns a scalar from a JSON path. The required `->>` shorthand query extracts
the first five firmware values:

```sql
SELECT name, meta ->> '$.firmware'
FROM device
ORDER BY device_id
LIMIT 5;
```

`json_each` is a table-valued function that turns the complete object into rows:

```sql
SELECT d.name, j.key, j.value
FROM device AS d, json_each(d.meta) AS j
WHERE d.name = 'cnc-01'
ORDER BY j.key;
```

The verified keys/values were `calibrated = 2026-01-10`, `firmware = 4.2`, and
`vendor = Siemens`.

### Expression indexes and exact spelling

```sql
CREATE INDEX ix_device_vendor
ON device(json_extract(meta, '$.vendor'));
```

The query using the exact expression produced:

```text
SEARCH device USING INDEX ix_device_vendor (<expr>=?)
```

The logically equivalent shorthand predicate `meta ->> 'vendor' = 'Fanuc'` produced:

```text
SCAN device
```

Both returned the same 334 rows, so correctness alone would not reveal the performance
difference. `EXPLAIN QUERY PLAN` is the evidence.

### Constraint experiments

The script verifies both success and failure paths inside a savepoint:

- valid JSON accepted;
- malformed JSON rejected by the CHECK;
- a different valid object shape accepted;
- a missing optional path returned SQL `NULL`;
- a BLOB rejected from the STRICT TEXT column.

The savepoint is rolled back, so the generated database remains exactly 1,000 rows.

### When JSON is the wrong boundary

Keep a field relational when it is required for nearly every row, participates in a foreign
key or unique constraint, drives frequent joins/filters, or carries a strong business type such
as price or timestamp. Promote a JSON path to a column when its governance or access pattern
becomes stable. Flexibility is valuable only while the cost of weak structure is understood.

### Check your understanding

**Q: Does `json_valid` prove the metadata is semantically correct?**

A: No. It proves syntax. `{"year":"unknown"}` can be valid JSON even if the application requires
an integer year.

**Q: Why can two equivalent predicates have different plans?**

A: SQLite matches an expression index to the parsed expression. The indexed `json_extract`
expression and the shorthand operator were not matched in the tested version.

**Q: Why use a savepoint for negative tests?**

A: It isolates accepted test rows and expected failures, then restores the fixture without
rebuilding it or polluting the final count.

## 4. Key-value representation versus a relational table

### Comparable workload

The benchmark writes keys such as `session-42` and values such as
`user-42:filter=city:2`. Both backends receive the same ordered 20,000 pairs. Every lookup value
is hashed in order, and the count and SHA-256 digest must match before timings are accepted.

The comparison controls several common sources of bias:

- five trials rather than one;
- alternating which backend runs first;
- a fresh temporary fixture for every backend/trial;
- opening and schema setup excluded from the write timer;
- persistence (`sync`/`commit`) included;
- all key lookups included;
- medians and ranges reported;
- cache limitation disclosed.

### Measured result

| Backend | Median write for 20,000 | Median lookup of 20,000 keys |
|---|---:|---:|
| shelve | 13,381.62 ms | 235.54 ms |
| SQLite | 46.02 ms | 1,375.72 ms |

SQLite's batched write was about 291× faster. Shelve's lookup loop was about 5.84× faster.
These numbers describe one Python implementation, one machine, and one workload. They do not
prove that SQLite is always faster or that key-value stores are always faster at lookup.

### Why the proposed decision is still SQLite

The session state has a simple key/value shape, so shelve is a credible local option. SQLite is
proposed because the measured write is strong and the store adds transactions, a portable query
language, inspection, constraints, and a clearer future concurrency path. If individual lookup
latency dominates in a real profile, the decision should be revisited—perhaps with batched
queries, an application cache, or a networked key-value system measured under realistic load.

For “retrieve session 101,” both stores offer a direct key lookup. For “count every session that
used the city:1 filter,” shelve must load and inspect values in application code, whereas SQLite
can filter and aggregate with SQL. SQLite can also join, enforce relational constraints, and
combine multiple changes in one transaction.

Python `shelve` also uses pickle-compatible serialization. Only a project-controlled shelf
should be opened; an untrusted shelf can execute unsafe deserialization behavior.

### Check your understanding

**Q: Why compare hashes rather than timing alone?**

A: A fast benchmark that writes or reads the wrong values is invalid. Equal deterministic
digests and counts establish basic workload equivalence.

**Q: Why use the median?**

A: It is less sensitive to a single scheduling, antivirus, or filesystem outlier than the mean.

**Q: Is this a benchmark of Redis or distributed key-value databases?**

A: No. It compares Python shelve with local SQLite for the workbook's small local exercise.

## 5. Making the architecture decision

A decision record should connect each workload to observable evidence and failure consequences.
The question is not “Which database is best?” but “Which engine is responsible for this state,
under these operations and failures?”

### Portfolio boundaries

- **Operational ingestion:** SQLite. Module 4 already verifies constraints, idempotent UPSERT,
  and atomic rollback.
- **Analytical report:** DuckDB over Parquet. Module 6a verifies roughly 79× and 94× speedups on
  two report queries over two million rows.
- **Variable device metadata:** JSON inside SQLite. This module verifies syntax enforcement,
  flexible keys, array queries, and expression-index behavior.
- **Session state:** SQLite for now. This module's benchmark and operational semantics support
  the proposal, while documenting shelve's lookup advantage.
- **Concurrent remote service:** PostgreSQL is a future conditional choice, not a claimed result.

### Freshness is part of correctness

The analytical Parquet file is a derived snapshot. If it is stale, DuckDB can return a very fast
wrong answer. A robust refresh records at least the source row count, maximum source timestamp,
export time, and a checksum or snapshot identifier. Readers should reject or visibly label a
snapshot outside the accepted freshness window.

### ACID

- **Atomicity:** all operations in a transaction commit or none do.
- **Consistency:** a committed transaction preserves the constraints that were actually
  declared; the database cannot enforce an omitted business rule.
- **Isolation:** concurrent transactions do not observe arbitrary intermediate states, according
  to the engine/isolation level.
- **Durability:** acknowledged commits survive the failures covered by the durability design.

### BASE

BASE is commonly expanded as Basically Available, Soft state, Eventual consistency. It describes
trade-offs used by some distributed architectures, where replicas may temporarily differ and
converge later. A system can use transactions locally and eventual consistency across services;
ACID and BASE are not mutually exclusive product labels.

### CAP without the slogan trap

CAP concerns a distributed system during a network partition. Under that failure, a system
cannot guarantee both linearizable consistency and a successful response to every request.
“Choose any two of C, A, P” hides the key point: if the system can partition, the design chooses
how each operation behaves during the partition. Normal-operation latency and consistency also
matter, but they are not the CAP theorem itself.

It is misleading to label a single SQLite file “CP” or “AP” without defining nodes, replicas,
and partitions. The same is true for an unspecified standalone PostgreSQL server.

### Final professor-ready explanation

“I used measured workload evidence and failure impact to define ownership. SQLite remains the
operational source of truth because its constraints and transaction workflow are verified.
DuckDB reads a rebuildable Parquet snapshot because it reduced the two-million-row report from
seconds to about 74 ms, but that snapshot requires freshness controls. JSON is limited to
variable metadata and uses validation plus an expression index. The session benchmark showed
a real trade-off, not a universal winner. PostgreSQL is a conditional future boundary because
the required authenticated classroom/server evidence is not available locally.”

## 6. Reproduce and challenge the claims

Run from the repository root:

```powershell
uv run python -B Module06b/json_bench.py --rebuild
uv run python -B Module06b/kv_compare.py --n 20000 --runs 5 --json
uv run python -B Module06b/concurrency_demo.py
uv run python -B -m unittest discover -s Module06b/tests -v
```

Then challenge the decision:

1. Confirm the JSON row count and both query plans.
2. Change only the indexed-query spelling and observe whether the plan changes.
3. Re-run the benchmark, retaining every sample and the equivalence digest.
4. Increase concurrent writers and define a bounded retry policy.
5. Ask what breaks first if each representation is stale, locked, corrupt, or unavailable.
6. Record real peer feedback and change the decision only when the evidence warrants it.
