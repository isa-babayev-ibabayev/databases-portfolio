# Module 5 Benchmark Summary

Environment: Python 3.14.5, SQLite 3.50.4, Windows 11. Each query or update has
seven raw samples; the reported value is the median. Query results were fetched
completely, and terminal printing was outside timed regions.

Both dashboard queries returned the same **350 groups**. A two-way `EXCEPT`
comparison between the flat table and reconstructed normalized join also found
zero missing rows in either direction.

The update statements measured inside rollback-protected transactions were:

```sql
UPDATE machine
SET site = 'Bielefeld'
WHERE machine_id = 'cnc-02';

UPDATE report_jobpart
SET site = 'Bielefeld'
WHERE machine_id = 'cnc-02';
```

| Design | Dashboard median (ms) | Site-update rows | Update median (ms) | Table storage (KB) | Redundancy |
|---|---:|---:|---:|---:|---|
| Normalized 3NF | 121.0052 | 1 | 1.2915 | 3976.0 | Minimal |
| Denormalized report, indexed | 151.9686 | 4000 | 22.6925 | 10832.0 | Site, technician, and price repeated |

On this run the indexed report was **0.796× as fast** as the normalized query,
or about **25.6% slower**. Denormalization did not improve this particular read
path because SQLite scanned the report's machine index and still built temporary
B-trees. That negative result is preserved rather than adjusted.

## Report index experiment

| Report scenario | Median (ms) | Plan start |
|---|---:|---|
| With `ix_report_machine` | 137.1854 | `SCAN report_jobpart USING INDEX ix_report_machine` |
| Without the index | 112.1664 | `SCAN report_jobpart` |

The unindexed median was about **18.2% lower**. For a query that needs a large
share of the table, walking the complete index and then fetching table columns
can cost more than one sequential scan. This does not mean indexes are generally
bad; it means this index did not match the filter and grouping workload well.

The controlled index change was:

```sql
DROP INDEX ix_report_machine;
```

The harness recreated the index after the experiment and verified its presence.

## Limitations

These are local measurements, not universal constants. Cache state, other
processes, SQLite version, storage, CPU, planner statistics, trial order, and
index choices can change the result. The harness alternates scenario order,
warms queries, uses the same data, and reports raw samples and medians. Python's
prepared-statement cache is disabled so `EXPLAIN` is reparsed after each index
change; this applies equally to both timed query designs.
