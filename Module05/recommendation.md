# Recommendation to Yasmin Kaya

The transactional machine, job, part, and job-part tables should remain in 3NF
because one machine-site change then updates only one authoritative row. The
denormalized report can still be useful as a controlled dashboard snapshot, but
it should not replace those source tables. **Measured results** on this workload
showed a 121.0052 ms normalized dashboard median and a 151.9686 ms indexed report
median, so the report was not faster until the unsuitable machine index was
removed; the unindexed report median was 112.1664 ms. Moving `cnc-02` changed one
normalized row but 4,000 report rows, and the report table used 10,832.0 KB
compared with 3,976.0 KB for the normalized base tables. I recommend rebuilding
the report table in one controlled transaction after relevant source changes or
on a schedule before dashboard use. That refresh strategy is proposed here; an
automatic synchronization trigger or refresh scheduler is not implemented in
this module.

## Prepared “what if” answer

If a machine changes location after the report was created, the normalized
`machine` row becomes correct immediately but the copied report rows become
stale. The dashboard must not use that snapshot until the controlled refresh
rebuilds it. A future production design could use triggers, a refresh job, or a
versioned snapshot, but each option needs its own correctness and performance
tests.
