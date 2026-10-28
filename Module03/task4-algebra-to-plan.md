# Task 4 — one query from algebra to plan

This is additional AI-assisted technical study material based on the verified
city revenue query.

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

Let the aliases be (C), (O), (L), and (P). A readable extended
relational-algebra expression is:

[
	au_{revenue DESC}
left(
pi_{city, customers, revenue}
left(
gamma_{
  C.city;+  count_{distinct}(C.customer\_id)\rightarrow customers,+  sum(L.qty \times P.price)\rightarrow revenue
}
left(
sigma_{
  O.ordered\_on \geq '2025{-}01{-}01'
  \land
  O.ordered\_on < '2026{-}01{-}01'
}
left(
  ((C \bowtie_{C.customer\_id=O.customer\_id} O)
  \bowtie_{O.order\_id=L.order\_id} L)
  \bowtie_{L.product\_id=P.product\_id} P
ight)
ight)
ight)
ight)
]

## Mapping

| Algebra | SQL | Meaning |
|---|---|---|
| (owtie) | three `JOIN ... ON` clauses | Combine related customer, order, line, and product rows |
| (sigma) | `WHERE` | Keep only dates in 2025 |
| (gamma) | `GROUP BY`, `COUNT`, `SUM` | Form one group per city and calculate metrics |
| (pi) | `SELECT` list | Return only city and the two calculated values |
| (	au) | `ORDER BY` | Sort revenue descending |

Classical relational algebra uses set semantics, while SQL normally preserves
duplicates. That difference matters here: joining Orders to OrderLine
deliberately creates several rows per order, because each line contributes to
revenue. `COUNT(DISTINCT customer_id)` explicitly removes repetition only for
the customer metric. Replacing it with `COUNT(customer_id)` would count lines,
not customers.

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

This plan is consistent with the requested meaning: every line is visited,
related parent rows are found by primary key, and temporary structures implement
grouping, distinct counting, and sorting. The algebra states *what* result is
required; this plan states *how this SQLite version chose to produce it*.

**TODO — STUDENT:** Practise explaining why the line join multiplies rows but
does not inflate `COUNT(DISTINCT customer_id)`.
