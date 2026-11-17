# Module 5 Learning Guide — Normalization by Measurement

This guide explains the Module 5 concepts using the repository's real factory dataset and saved
measurements. It is technical study material, not a record of personal classroom experience.

## 1. Functional dependencies

A functional dependency `X → Y` means that any two rows agreeing on `X` must also agree on `Y`.
In the factory model, one job belongs to one machine, so `job_id → machine_id`. One machine has
one current site, so `machine_id → site`.

```sql
SELECT job_id
FROM flat_jobpart
GROUP BY job_id
HAVING COUNT(DISTINCT machine_id) > 1;
```

The verified generator produced no rows from this conflict query. That observation agrees with
the intended domain rule, but a small sample alone cannot prove a universal business rule.

## 2. Why `(job_id, part_no)` is the candidate key

One row records one part used in one job. `job_id` alone repeats ten times and `part_no` repeats
across many jobs. Together they are unique under the rule that a part appears at most once per
job.

```sql
SELECT job_id, part_no, COUNT(*)
FROM flat_jobpart
GROUP BY job_id, part_no
HAVING COUNT(*) > 1;
```

The result is empty. The key is minimal because removing either column no longer identifies one
job-part fact.

## 3. First Normal Form

1NF requires atomic values rather than repeating groups or comma-separated lists. The Module 5
flat table has one `part_no` per row. Ten parts for a job therefore create ten rows, not one cell
such as `P-0002,P-0003,...`.

This makes each part independently queryable and avoids string parsing, but 1NF alone does not
remove repeated site or price facts.

## 4. Second Normal Form

2NF starts from 1NF and removes a dependency on only part of a composite key. The flat row key is
`(job_id, part_no)`, but `part_no → part_price`. Therefore price belongs in `part`, whose key is
`part_no`.

```sql
CREATE TABLE part(
    part_no TEXT PRIMARY KEY,
    part_price REAL NOT NULL CHECK(part_price >= 0)
) STRICT;
```

The verified result has ten part rows instead of 200,000 repeated prices.

## 5. Third Normal Form

3NF removes an inappropriate transitive dependency inside a relation. The model has
`job_id → machine_id` and `machine_id → site`, so storing site on every job-part row repeats a
fact determined through the machine.

```sql
CREATE TABLE machine(
    machine_id TEXT PRIMARY KEY,
    site TEXT NOT NULL
) STRICT;
```

Site is stored once per machine. A job references the machine rather than copying its site.

## 6. Why four normalized tables exist

- `machine(machine_id, site)` owns the machine-site fact.
- `part(part_no, part_price)` owns the part-price fact.
- `job(job_id, machine_id, technician, done_on)` owns job facts.
- `job_part(job_id, part_no)` represents the many-to-many job/part relationship.

```sql
CREATE TABLE job_part(
    job_id INTEGER NOT NULL REFERENCES job(job_id),
    part_no TEXT NOT NULL REFERENCES part(part_no),
    PRIMARY KEY(job_id, part_no)
) STRICT;
```

The verified counts are 50 machines, 10 parts, 20,000 jobs, and 200,000 job-part rows. With
foreign keys enabled, `PRAGMA foreign_key_check` reported zero violations.

## 7. Update anomaly

In the five-row flat example, `cnc-01` appears three times. Updating only one copy changes one row
to Bielefeld while two still say Gütersloh.

```sql
UPDATE flat5
SET site = 'Bielefeld'
WHERE rowid = (SELECT MIN(rowid) FROM flat5 WHERE machine_id = 'cnc-01');
```

The actual demonstration returned `Bielefeld=1` and `Gütersloh=2`. In the normalized design the
same business change targets one `machine` row.

## 8. Insert anomaly

The flat table mixes the part catalog with job facts. To record a new unused part, the experiment
had to insert a row with NULL job, machine, site, and technician fields. SQLite accepted it, but
the row does not represent a real job-part event.

```sql
INSERT INTO part(part_no, part_price) VALUES ('P-0099', 12.50);
```

The normalized `part` table accepted exactly one clean catalog row without inventing a job.

## 9. Delete anomaly

`P-0002` appeared once in the five-row flat fixture. Deleting that job-part row also deleted the
only stored price for the part.

```sql
DELETE FROM flat5 WHERE part_no = 'P-0002';
```

The flat count became zero. The normalized `part` row remained with price 7.0 because catalog
identity and usage are stored separately.

## 10. The 200,000-row build

Two recursive sequences generate 20,000 jobs and ten part positions. `CROSS JOIN` returns every
combination: `20,000 × 10 = 200,000`.

```sql
FROM j CROSS JOIN p
```

The price is intentionally formatted as TEXT in the teaching table and cast to REAL during the
normalized load. Production money storage needs a deliberate decimal/cents policy; REAL is used
here to match the workbook experiment.

Only ten parts exist because `k` takes values 1 through 10. Consequently `(k % 40) + 1` produces
2 through 11, not forty identifiers. `COUNT(DISTINCT part_no)` returned 10.

## 11. Why denormalize a reporting path

The normalized dashboard joins four tables. A reporting copy stores site, technician, and price
beside every fact so a dashboard can scan one table.

```sql
SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM report_jobpart
WHERE done_on >= date('2026-03-01')
GROUP BY machine_id, technician;
```

Both versions returned the same 350 groups. The saved historical medians were 121.0052 ms for
the normalized join and 151.9686 ms for the indexed report, so denormalization did not win merely
because it used one table. The small dimension tables were cheap to join, while the report row
was wider.

## 12. Why an index can slow this query

`ix_report_machine` does not match the date filter and the query reads a large share of the
table. SQLite walked the whole index, fetched table columns, and still built temporary B-trees.

```text
with index:    SCAN report_jobpart USING INDEX ix_report_machine
without index: SCAN report_jobpart
```

Historically, the median improved from 137.1854 ms to 112.1664 ms without the index. The isolated
2026-11-17 audit again improved from 120.9963 ms to 88.5278 ms. This does not mean indexes are
bad; it means an index must fit the filter, ordering, selectivity, and required columns.

## 13. Why one update touches 1 versus 4,000 rows

There are 200,000 report rows spread evenly over 50 machines, so `cnc-02` appears 4,000 times.

```sql
UPDATE machine SET site='Bielefeld' WHERE machine_id='cnc-02';
UPDATE report_jobpart SET site='Bielefeld' WHERE machine_id='cnc-02';
```

The rollback-protected experiment changed one normalized row and 4,000 report rows. Historical
medians were 1.2915 ms and 22.6925 ms. The row counts are more transferable than the local timing
because they scale directly with duplicated facts.

## 14. Why storage differs

The normalized base tables store site, technician, and price at their owning entities. The report
copies those values onto 200,000 rows.

`dbstat` measured:

| Tables only | Bytes | KiB |
|---|---:|---:|
| Normalized | 4,071,424 | 3,976.0 |
| Report | 11,091,968 | 10,832.0 |

Including relevant indexes changes the comparison to 7,976.0 KiB versus 13,752.0 KiB. The full
database file is larger again because it includes every object and page; these scopes must not be
mixed.

## 15. Recommendation and limits of the evidence

The recommendation keeps the normalized tables as the source of truth and treats the report as a
rebuildable snapshot. A controlled transactional rebuild or scheduled refresh is proposed; no
automatic trigger or scheduler is claimed as implemented.

The experiments establish correctness, local query plans, local timing samples, write
amplification, and object storage for this generated workload. They do not prove that normalized
queries always win, that indexes are generally harmful, or that a production dashboard will have
the same timings. Cache, hardware, data distribution, concurrency, dimensions, and indexes can
change the decision.

## Short classmate explanation

“Normalization stores each fact once, so it prevents anomalies and makes updates cheap. The
report table deliberately copies facts to simplify a read, but that copy was larger and required
4,000 updates for one site change. On this dataset the indexed report was even slower because the
index caused a full index walk plus table lookups. The correct choice comes from the workload and
measurements, not from assuming that either more joins or fewer tables is always faster.”
