# Task 4 — one query from algebra to plan

This exercise uses the verified city-revenue query and explains the same work
in SQL, extended relational algebra, and a physical SQLite query plan.

## SQL

```sql
SELECT c.city,
       COUNT(DISTINCT c.customer_id) AS customers,
       SUM(ol.qty * p.price) AS revenue
FROM customer AS c
JOIN orders AS o ON o.customer_id = c.customer_id
JOIN order_line AS ol ON ol.order_id = o.order_id
JOIN product AS p ON p.product_id = ol.product_id
WHERE o.ordered_on >= '2025-01-01'
  AND o.ordered_on < '2026-01-01'
GROUP BY c.city
ORDER BY revenue DESC;
```

## Relational algebra

Let `C`, `O`, `L`, and `P` represent Customer, Orders, OrderLine, and Product.
The query can be written with extended relational algebra as:

$$
\tau_{revenue\ DESC}
\left(
\pi_{city,\ customers,\ revenue}
\left(
\gamma_{C.city;\
\operatorname{count}_{distinct}(C.customer\_id) \rightarrow customers,\
\operatorname{sum}(L.qty \times P.price) \rightarrow revenue}
\left(
\sigma_{O.ordered\_on \geq '2025{-}01{-}01'\ \land\
O.ordered\_on < '2026{-}01{-}01'}
\left(
\left(
\left(C \bowtie_{C.customer\_id=O.customer\_id} O\right)
\bowtie_{O.order\_id=L.order\_id} L
\right)
\bowtie_{L.product\_id=P.product\_id} P
\right)
\right)
\right)
\right)
$$

The final `τ` is an extended operator for sorting. Classical relational
algebra does not define row order, so it may also be shown separately as the
SQL `ORDER BY` step.

## Mapping

| Algebra | SQL | Meaning |
|---|---|---|
| Join `⋈` | Three `JOIN ... ON` clauses | Combine related customer, order, line, and product rows |
| Selection `σ` | `WHERE` | Keep only order dates in 2025 |
| Grouping `γ` | `GROUP BY`, `COUNT`, `SUM` | Form one group per city and calculate its two metrics |
| Projection `π` | `SELECT` list | Return city, distinct-customer count, and revenue |
| Sort `τ` | `ORDER BY` | Put the largest revenue first |

The join conditions match the SQL foreign-key-style columns exactly. The date
selection happens before grouping. Grouping creates one result per city,
counts each customer once, and sums every order-line quantity multiplied by
its product price.

Classical relational algebra normally uses set semantics, while SQL normally
preserves duplicates. That difference matters here: joining Orders to
OrderLine creates several rows per order because each line contributes to
revenue. `COUNT(DISTINCT customer_id)` removes repetition only for the
customer metric. Replacing it with `COUNT(customer_id)` would count joined
lines instead of customers.

## Physical plan

```text
SCAN ol
SEARCH o USING INTEGER PRIMARY KEY (rowid=?)
SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
SEARCH p USING INTEGER PRIMARY KEY (rowid=?)
USE TEMP B-TREE FOR GROUP BY
USE TEMP B-TREE FOR count(DISTINCT)
USE TEMP B-TREE FOR ORDER BY
```

The algebra describes the required meaning. The physical plan describes how
SQLite 3.50.4 produced that result for this fixture: it scanned OrderLine,
looked up the three parent rows by primary key, and built temporary B-trees for
grouping, distinct counting, and sorting.
