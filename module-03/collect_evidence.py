"""Collect deterministic Module 3 query, plan, and correctness evidence."""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import time
from collections import defaultdict
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = MODULE_DIR / "warehouse.db"
DEFAULT_EVIDENCE = MODULE_DIR / "evidence"

TASK1_SQL = """
SELECT
    c.city,
    COUNT(DISTINCT c.customer_id) AS customers,
    SUM(ol.qty * p.price) AS revenue
FROM customer AS c
JOIN orders AS o ON o.customer_id = c.customer_id
JOIN order_line AS ol ON ol.order_id = o.order_id
JOIN product AS p ON p.product_id = ol.product_id
WHERE o.ordered_on >= '2025-01-01'
  AND o.ordered_on < '2026-01-01'
GROUP BY c.city
ORDER BY revenue DESC
"""

GROUPED_LATE = """
SELECT c.customer_id, c.name, COUNT(*) AS late_orders
FROM orders AS o
JOIN customer AS c ON c.customer_id = o.customer_id
WHERE o.status = 'late'
GROUP BY c.customer_id, c.name
ORDER BY late_orders DESC, c.customer_id
"""

CORRELATED_LATE = """
SELECT c.customer_id, c.name,
       (SELECT COUNT(*) FROM orders AS o
        WHERE o.customer_id = c.customer_id AND o.status = 'late') AS late_orders
FROM customer AS c
WHERE EXISTS (
    SELECT 1 FROM orders AS o
    WHERE o.customer_id = c.customer_id AND o.status = 'late'
)
ORDER BY late_orders DESC, c.customer_id
"""

WINDOW_LATE = """
WITH counted AS (
    SELECT c.customer_id, c.name,
           COUNT(*) OVER (PARTITION BY c.customer_id) AS late_orders,
           ROW_NUMBER() OVER (
               PARTITION BY c.customer_id ORDER BY o.order_id
           ) AS row_in_customer
    FROM orders AS o
    JOIN customer AS c ON c.customer_id = o.customer_id
    WHERE o.status = 'late'
)
SELECT customer_id, name, late_orders
FROM counted
WHERE row_in_customer = 1
ORDER BY late_orders DESC, customer_id
"""


def format_table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> str:
    rendered = [[str(value) for value in row] for row in rows]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rendered))
        for index in range(len(headers))
    ]
    def render_line(values: tuple[str, ...] | list[str]) -> str:
        return "  ".join(
            value.ljust(widths[i]) if i < len(widths) - 1 else value
            for i, value in enumerate(values)
        )

    header = render_line(list(headers))
    rule = "  ".join("-" * width for width in widths)
    body = [
        render_line(row)
        for row in rendered
    ]
    return "\n".join([header, rule, *body]) + "\n"


def collect(database: Path, evidence_dir: Path) -> dict[str, object]:
    if not database.exists():
        raise FileNotFoundError(f"{database} not found; run setup.sql first")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database)

    counts = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("customer", "product", "orders", "order_line")
    }
    setup_text = "SQLite runtime: " + sqlite3.sqlite_version + "\n"
    setup_text += format_table(
        ("table_name", "row_count"), list(counts.items())
    )
    ranges = conn.execute(
        """
        SELECT MIN(customer_id), MAX(customer_id),
               (SELECT MIN(product_id) FROM product),
               (SELECT MAX(product_id) FROM product),
               (SELECT MIN(order_id) FROM orders),
               (SELECT MAX(order_id) FROM orders),
               (SELECT MIN(ordered_on) FROM orders),
               (SELECT MAX(ordered_on) FROM orders)
        FROM customer
        """
    ).fetchone()
    setup_text += (
        f"customer_id range: {ranges[0]}..{ranges[1]}\n"
        f"product_id range: {ranges[2]}..{ranges[3]}\n"
        f"order_id range: {ranges[4]}..{ranges[5]}\n"
        f"ordered_on range: {ranges[6]}..{ranges[7]}\n"
        "x=540 date check: "
        + conn.execute(
            "SELECT date('2025-01-01', '+' || (540 % 540) || ' days')"
        ).fetchone()[0]
        + "\n"
        "SKU formatting check: "
        + conn.execute("SELECT sku FROM product WHERE product_id=1").fetchone()[0]
        + "\n"
    )
    (evidence_dir / "setup-counts.txt").write_text(setup_text, encoding="utf-8")

    task1_rows = conn.execute(TASK1_SQL).fetchall()
    task1_text = "SQLite runtime: " + sqlite3.sqlite_version + "\n"
    task1_text += format_table(("city", "customers", "revenue"), task1_rows)
    (evidence_dir / "task1-query-results.txt").write_text(
        task1_text, encoding="utf-8"
    )

    task1_plan = [
        str(row[3])
        for row in conn.execute("EXPLAIN QUERY PLAN " + TASK1_SQL)
    ]
    plan_text = (
        f"SQLite runtime: {sqlite3.sqlite_version}\n"
        "Query: task1 dashboard\n"
        + "\n".join(task1_plan)
        + "\n"
    )
    (evidence_dir / "task1-plan.txt").write_text(plan_text, encoding="utf-8")

    # Independent Python aggregation checks the SQL result rather than merely
    # executing the same aggregate a second time.
    customer_sets: dict[str, set[int]] = defaultdict(set)
    revenues: dict[str, float] = defaultdict(float)
    for city, customer_id, qty, price in conn.execute(
        """
        SELECT c.city, c.customer_id, ol.qty, p.price
        FROM customer AS c
        JOIN orders AS o ON o.customer_id = c.customer_id
        JOIN order_line AS ol ON ol.order_id = o.order_id
        JOIN product AS p ON p.product_id = ol.product_id
        WHERE o.ordered_on >= '2025-01-01'
          AND o.ordered_on < '2026-01-01'
        """
    ):
        customer_sets[city].add(customer_id)
        revenues[city] += qty * price
    python_rows = sorted(
        (
            (city, len(customer_sets[city]), revenues[city])
            for city in customer_sets
        ),
        key=lambda row: row[2],
        reverse=True,
    )
    python_matches_sql = all(
        sql_row[0] == python_row[0]
        and sql_row[1] == python_row[1]
        and abs(sql_row[2] - python_row[2]) < 1e-6
        for sql_row, python_row in zip(task1_rows, python_rows, strict=True)
    )
    boundary = {
        "before_2025": conn.execute(
            "SELECT COUNT(*) FROM orders WHERE ordered_on < '2025-01-01'"
        ).fetchone()[0],
        "in_2025": conn.execute(
            "SELECT COUNT(*) FROM orders WHERE ordered_on >= '2025-01-01' "
            "AND ordered_on < '2026-01-01'"
        ).fetchone()[0],
        "after_2025": conn.execute(
            "SELECT COUNT(*) FROM orders WHERE ordered_on >= '2026-01-01'"
        ).fetchone()[0],
        "on_2025_01_01": conn.execute(
            "SELECT COUNT(*) FROM orders WHERE ordered_on = '2025-01-01'"
        ).fetchone()[0],
        "on_2026_01_01": conn.execute(
            "SELECT COUNT(*) FROM orders WHERE ordered_on = '2026-01-01'"
        ).fetchone()[0],
        "cities_returned": len(task1_rows),
        "python_reference_matches_sql": python_matches_sql,
        "descending_revenue": all(
            task1_rows[i][2] >= task1_rows[i + 1][2]
            for i in range(len(task1_rows) - 1)
        ),
    }
    (evidence_dir / "task1-verification.json").write_text(
        json.dumps(boundary, indent=2) + "\n", encoding="utf-8"
    )

    late_results = {}
    window_text = [f"SQLite runtime: {sqlite3.sqlite_version}", ""]
    late_timings = {}
    for name, sql in (
        ("grouped", GROUPED_LATE),
        ("correlated", CORRELATED_LATE),
        ("window", WINDOW_LATE),
    ):
        rows = conn.execute(sql).fetchall()
        late_results[name] = rows
        conn.execute(sql).fetchall()
        samples = []
        for _ in range(3):
            started = time.perf_counter_ns()
            conn.execute(sql).fetchall()
            samples.append((time.perf_counter_ns() - started) / 1_000_000)
        late_timings[name] = samples
        window_text.append(f"## {name}")
        window_text.append(f"rows={len(rows)} first_5={rows[:5]}")
        window_text.append(
            "timings_ms="
            + ",".join(f"{value:.6f}" for value in samples)
            + f"; median_ms={statistics.median(samples):.6f}"
        )
        window_text.extend(
            str(row[3])
            for row in conn.execute("EXPLAIN QUERY PLAN " + sql)
        )
        window_text.append("")
    window_text.append(
        "equivalent="
        + str(
            late_results["grouped"]
            == late_results["correlated"]
            == late_results["window"]
        )
    )
    (evidence_dir / "task5-results.txt").write_text(
        "\n".join(window_text) + "\n", encoding="utf-8"
    )
    conn.close()
    return {
        "counts": counts,
        "task1_rows": task1_rows,
        "task1_plan": task1_plan,
        "task1_verification": boundary,
        "window_equivalent": (
            late_results["grouped"]
            == late_results["correlated"]
            == late_results["window"]
        ),
        "window_medians_ms": {
            name: round(statistics.median(samples), 6)
            for name, samples in late_timings.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    args = parser.parse_args()
    print(
        json.dumps(
            collect(args.database, args.evidence_dir),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
