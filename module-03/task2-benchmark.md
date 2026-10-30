# Task 2 — index benchmark

The reusable harness is [bench.py](bench.py). It copies `warehouse.db` into a
temporary database, uses one Python/SQLite process, performs one unmeasured
warm-up, records five samples per stage, and reports the median. The dashboard
stages are cumulative, exactly as the workbook specifies.

Environment: Python 3.14.5, Python SQLite runtime 3.50.4, Windows. Times include
query execution and result fetching but exclude Python process startup.

## Dashboard results

| Stage | Experimental indexes available | Median (ms) | Plan change |
|---|---|---:|---|
| Baseline | none | 160.879800 | `SCAN ol`, then PK searches |
| Stage 1 | `ix_orders_ordered_on` | 154.832800 | None; date index ignored |
| Stage 2 | plus `ix_orderline_order` | 1429.524300 | Date range SEARCH became outer loop; OrderLine searched by order ID |
| Stage 3 | plus `ix_orderline_product` | 1514.061800 | None from Stage 2; product index unused |

Stage 1's small timing difference is not evidence of improvement because its
plan did not change and the samples overlap the baseline range. Stage 2 is the
important negative result: the new indexes changed the plan but made the
aggregate about 8.9 times slower. The index-driven plan performs many
OrderLine lookups for 40,575 qualifying orders; the baseline sequentially scans
240,000 compact line rows once.

Stage 3 confirms that `ix_orderline_product` does not help this dashboard.
SQLite still reaches Product through its integer primary key, and the plan does
not mention the new index. The higher median is variability/slowdown under the
same plan, not proof that SQLite used the product index.

## Queries where indexes clearly help

| Query | Before median | After median | Plan evidence |
|---|---:|---:|---|
| Single day, 100-execution batches | 3.832294 ms | 0.297238 ms | `SCAN o` → `SEARCH o USING INDEX ix_orders_ordered_on` |
| Product 42 filter, 100-execution batches | 13.714101 ms | 2.782931 ms | `SCAN ol` → `SEARCH ol USING INDEX ix_orderline_product` |

The repeated batches amortize timer resolution for short queries. Every
execution fetched 111 rows for the date query and 480 rows for the product
query.

## Honest negative and covering cases

- `date(o.ordered_on) = '2026-02-14'` produced `SCAN o` even while the
  ordinary date index existed. The indexed expression is `ordered_on`, not
  `date(ordered_on)`.
- Selecting only `ordered_on` used
  `USING COVERING INDEX ix_orders_ordered_on`.
- Adding `customer_id` to the select list changed it to ordinary
  `USING INDEX`, because that value is absent from the index.
- No `INDEXED BY` hint was used; these are the optimizer's natural choices.

Raw evidence:

- [benchmark-results.csv](evidence/benchmark-results.csv)
- [benchmark-summary.json](evidence/benchmark-summary.json)
- [benchmark-plans.txt](evidence/benchmark-plans.txt)

The figures apply to this machine, data, SQLite version, cache state, and
measurement method. Plans and timings can differ after statistics, version, or
hardware changes.
