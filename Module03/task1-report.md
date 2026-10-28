# Task 1 — AI-generated city revenue query

## Exact prompt

> SQLite schema: customer(customer_id, name, city), product(product_id, sku,
> price), orders(order_id, customer_id, ordered_on, status),
> order_line(order_id, product_id, qty). Write a query that returns, for each
> city, the number of distinct customers and the total revenue (sum of
> qty*price) of orders placed in 2025, ordered by revenue descending.

The response saved in [task1-query.sql](task1-query.sql) matches the workbook
reference query. It is recorded as an AI-assisted draft, not as independently
student-authored SQL.

## AI prediction before execution

The predicted plan was:

- scan the 2025 Orders rows because there was no date index;
- search Customer and Product through their integer primary keys;
- scan or automatically search OrderLine for each order;
- use temporary B-trees for grouping, distinct counting, and revenue ordering.

This prediction was partly wrong. SQLite 3.50.4 chose OrderLine as the outer
loop and produced `SCAN ol`, then primary-key searches into Orders, Customer,
and Product. No automatic OrderLine index appeared. The three predicted
temporary B-trees did appear.

## Actual result

| City | Distinct customers | Revenue |
|---|---:|---:|
| Bielefeld | 500 | 11,242,176.0 |
| Gütersloh | 500 | 8,422,344.0 |
| Münster | 500 | 5,493,504.0 |
| Paderborn | 500 | 2,815,656.0 |

Raw output: [task1-query-results.txt](evidence/task1-query-results.txt)

## Actual plan

```text
SCAN ol
SEARCH o USING INTEGER PRIMARY KEY (rowid=?)
SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
SEARCH p USING INTEGER PRIMARY KEY (rowid=?)
USE TEMP B-TREE FOR GROUP BY
USE TEMP B-TREE FOR count(DISTINCT)
USE TEMP B-TREE FOR ORDER BY
```

Raw plan: [task1-plan.txt](evidence/task1-plan.txt)

## Correctness checks

- The half-open interval includes 2025-01-01 and excludes 2026-01-01.
- The generated data contains 40,575 orders in 2025, 111 exactly on
  2025-01-01, and 111 on the excluded 2026-01-01 boundary.
- `COUNT(DISTINCT c.customer_id)` prevents repeat orders and multiple lines
  from multiplying the customer count.
- Revenue is `SUM(qty * price)` across qualifying lines.
- An independent Python aggregation over the joined detail rows exactly matched
  all four SQL groups and revenues.
- Revenues are in descending order.
- A deterministic edge fixture proves that a customer with several orders and
  lines is counted once, boundary dates behave correctly, and a customer with
  no qualifying order is omitted.

The inner joins intentionally report cities represented by qualifying orders;
they do not return a zero-revenue row for a city whose customers have no 2025
orders. A report requiring zero rows would start from Customer and use
date-filtered left joins.

Machine-readable checks: [task1-verification.json](evidence/task1-verification.json).
