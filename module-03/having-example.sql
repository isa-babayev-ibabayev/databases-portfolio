-- Learning Goal 1: executable GROUP BY and HAVING evidence.
--
-- WHERE filters individual order rows before grouping. GROUP BY then creates
-- one group per customer. HAVING filters those completed groups by their
-- aggregate COUNT(*).
SELECT customer_id,
       COUNT(*) AS late_orders
FROM orders
WHERE status = 'late'
GROUP BY customer_id
HAVING COUNT(*) > 20
ORDER BY late_orders DESC, customer_id;

-- Compact independent checks for the result above. The expected result is
-- derived from the data, not hard-coded into the query.
WITH qualifying_customers AS (
    SELECT customer_id,
           COUNT(*) AS late_orders
    FROM orders
    WHERE status = 'late'
    GROUP BY customer_id
    HAVING COUNT(*) > 20
)
SELECT COUNT(*) AS qualifying_customers,
       MIN(customer_id) AS first_customer_id,
       MAX(customer_id) AS last_customer_id,
       MIN(late_orders) AS minimum_late_orders,
       MAX(late_orders) AS maximum_late_orders,
       COUNT(DISTINCT late_orders) AS distinct_late_order_counts
FROM qualifying_customers;

EXPLAIN QUERY PLAN
SELECT customer_id,
       COUNT(*) AS late_orders
FROM orders
WHERE status = 'late'
GROUP BY customer_id
HAVING COUNT(*) > 20
ORDER BY late_orders DESC, customer_id;
