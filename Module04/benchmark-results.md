# Trigger Benchmark Results

The benchmark inserted the same deterministic 10,000-row vibration dataset in
one transaction into equivalent in-memory schemas. Five trials were run for
each scenario, and execution order alternated to reduce order bias. Half of the
rows exceeded the alarm threshold, so every triggered trial also verified
5,000 alarm rows.

Environment: Python 3.14.5, SQLite runtime 3.50.4, Windows. Timing used
`time.perf_counter()`.

| Scenario | Rows | Median time (s) | Median throughput (rows/s) |
|---|---:|---:|---:|
| Without alarm trigger | 10,000 | 0.009106 | 1,098,225.27 |
| With alarm trigger | 10,000 | 0.027644 | 361,747.38 |

Measured median overhead: **203.59%**.

## Recorded trials

- Without trigger: 0.008788, 0.009618, 0.009106, 0.008513, 0.009353 seconds.
- With trigger: 0.033317, 0.032391, 0.025781, 0.027644, 0.025882 seconds.

The triggered case was slower in this run because each qualifying row evaluated
the trigger predicate and 5,000 rows caused an additional `alarm` write. The
result depends on predicate selectivity, transaction boundaries, storage,
hardware load, Python and SQLite builds, so it should not be treated as a
universal constant. Both scenarios used the same batch size, transaction scope,
SQLite runtime, schema except for the trigger, and input data.
