# Optional Task 5 — grouped, correlated, and window queries

The three executable variants are in [task5-queries.sql](task5-queries.sql).
They use the workbook semantics: only customers with at least one late order
appear.

## AI-first result and correction

The first window-style draft used
`COUNT(*) OVER (PARTITION BY customer_id)` directly. That returns the correct
count on every late order row, so it duplicates each customer. The corrected
version adds `ROW_NUMBER()` and keeps `row_in_customer = 1`.

## Verified comparison

| Variant | Rows | Median of 3 (ms) | Important plan behavior |
|---|---:|---:|---|
| Grouped | 400 | 9.189100 | One Orders scan, PK Customer searches, temp grouping/order |
| Correlated | 400 | 6249.788700 | Customer scan plus two correlated Orders scans |
| Window | 400 | 24.976000 | Orders scan, co-routines, temporary ordering |

All three result lists were exactly equal, including ordering. Every returned
customer had 30 late orders in this deterministic fixture. The grouped query is
shortest and fastest here. The correlated version is readable as a per-customer
question but extremely slow without a supporting `orders(customer_id,status)`
index. The window version is useful when detail rows and per-customer counts
must coexist, but needs explicit de-duplication for this one-row-per-customer
report.

Raw timings and plans: [task5-results.txt](evidence/task5-results.txt).

Customers with zero late orders are excluded by the grouped query. The
correlated version uses `EXISTS` to match that rule; without it, it would
return all customers with zeros and would no longer be equivalent.
