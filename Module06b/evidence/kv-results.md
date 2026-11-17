# Key-value benchmark results

Measured on 2026-11-17 with Windows 11, Python 3.14.5, SQLite 3.50.4, and uv 0.11.16.

- Workload: 20,000 deterministic session key/value pairs.
- Trials: 5 per backend, alternating which backend ran first.
- Isolation: a fresh temporary fixture for every backend in every trial.
- Write boundary: database open/schema creation excluded; `sync()` or `commit()` included.
- Lookup boundary: all 20,000 keys read individually after the write.
- Validation: both backends stored 20,000 values with identical SHA-256 digest
  `45cf41525004ad60ad9ba5ad25d45f9ceb14fb294c015c25f24b9783f9c9aa54`.
- Limitation: lookups followed writes and may have benefited from the operating-system cache.

| Backend | Write samples (ms) | Median write | Lookup samples (ms) | Median lookup |
|---|---|---:|---|---:|
| shelve | 13381.62, 13774.69, 12916.98, 14446.38, 12781.70 | 13381.62 ms | 249.37, 260.27, 223.82, 235.54, 220.51 | 235.54 ms |
| SQLite | 46.02, 46.86, 45.39, 61.51, 44.43 | 46.02 ms | 1630.11, 1645.83, 1375.72, 1361.38, 1333.40 | 1375.72 ms |

Interpretation: on this machine and workload, SQLite's batched transactional write was
about 291 times faster by median, while shelve's individual key lookups were about 5.84
times faster. This is not a universal engine ranking. SQLite remains the proposed session
store here because it adds transactions, constraints, SQL inspection, and safer concurrent
access; the choice should be revisited if measured lookup latency becomes the dominant
requirement.
