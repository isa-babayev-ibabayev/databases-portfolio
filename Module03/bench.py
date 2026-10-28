"""Reproducible Module 3 SQLite index benchmark.

The benchmark copies warehouse.db into a disposable temporary database so the
source fixture and any student work remain unchanged.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sqlite3
import statistics
import tempfile
import time
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = MODULE_DIR / "warehouse.db"
DEFAULT_EVIDENCE = MODULE_DIR / "evidence"

DASHBOARD_SQL = """
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

SINGLE_DAY_SQL = """
SELECT o.order_id, o.ordered_on, c.name
FROM orders AS o
JOIN customer AS c ON c.customer_id = o.customer_id
WHERE o.ordered_on = '2026-02-14'
"""

FUNCTION_WRAPPED_SQL = """
SELECT o.order_id, o.ordered_on, c.name
FROM orders AS o
JOIN customer AS c ON c.customer_id = o.customer_id
WHERE date(o.ordered_on) = '2026-02-14'
"""

PRODUCT_FILTER_SQL = """
SELECT ol.order_id, ol.product_id, ol.qty
FROM order_line AS ol
WHERE ol.product_id = 42
"""

INDEXES = (
    ("stage1_ordered_on", "CREATE INDEX ix_orders_ordered_on ON orders(ordered_on)"),
    ("stage2_order_line_order", "CREATE INDEX ix_orderline_order ON order_line(order_id)"),
    ("stage3_order_line_product", "CREATE INDEX ix_orderline_product ON order_line(product_id)"),
)


def plan(conn: sqlite3.Connection, sql: str) -> list[str]:
    return [str(row[3]) for row in conn.execute("EXPLAIN QUERY PLAN " + sql)]


def timed_runs(
    conn: sqlite3.Connection,
    query_name: str,
    stage: str,
    sql: str,
    repeats: int,
    iterations: int = 1,
) -> list[dict[str, object]]:
    # One untimed warm-up keeps process startup and statement compilation out
    # of the reported samples. Cache effects are still discussed in the report.
    conn.execute(sql).fetchall()
    samples: list[dict[str, object]] = []
    for run in range(1, repeats + 1):
        started = time.perf_counter_ns()
        row_count = 0
        for _ in range(iterations):
            row_count = len(conn.execute(sql).fetchall())
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        samples.append(
            {
                "query": query_name,
                "stage": stage,
                "run": run,
                "iterations": iterations,
                "elapsed_ms": round(elapsed_ms, 6),
                "per_execution_ms": round(elapsed_ms / iterations, 6),
                "row_count": row_count,
            }
        )
    return samples


def add_plan(blocks: list[str], heading: str, conn: sqlite3.Connection, sql: str) -> None:
    blocks.append(f"## {heading}")
    blocks.extend(plan(conn, sql))
    blocks.append("")


def run_benchmark(
    source_db: Path,
    evidence_dir: Path,
    repeats: int = 5,
    batch_iterations: int = 100,
) -> dict[str, object]:
    if not source_db.exists():
        raise FileNotFoundError(f"{source_db} not found; run setup.sql first")
    if repeats < 3:
        raise ValueError("at least three timing runs are required")

    evidence_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    plan_blocks = [
        f"SQLite runtime: {sqlite3.sqlite_version}",
        f"Python: {platform.python_version()}",
        f"Repeats: {repeats}; warm-up: 1 unmeasured execution",
        "",
    ]

    with tempfile.TemporaryDirectory(prefix="module03-benchmark-") as temp_dir:
        benchmark_db = Path(temp_dir) / "benchmark.db"
        source = sqlite3.connect(source_db)
        target = sqlite3.connect(benchmark_db)
        source.backup(target)
        source.close()
        conn = target
        conn.execute("PRAGMA foreign_keys = OFF")
        for index_name in (
            "ix_orders_ordered_on",
            "ix_orderline_order",
            "ix_orderline_product",
        ):
            conn.execute(f"DROP INDEX IF EXISTS {index_name}")

        stages = [("baseline", None), *INDEXES]
        for stage, ddl in stages:
            if ddl:
                conn.execute(ddl)
                conn.commit()
            add_plan(plan_blocks, f"dashboard / {stage}", conn, DASHBOARD_SQL)
            results.extend(
                timed_runs(conn, "dashboard", stage, DASHBOARD_SQL, repeats)
            )

        # Independent single-day before/after comparison on the same disposable DB.
        conn.execute("DROP INDEX IF EXISTS ix_orders_ordered_on")
        conn.commit()
        add_plan(plan_blocks, "single_day / no_date_index", conn, SINGLE_DAY_SQL)
        results.extend(
            timed_runs(
                conn, "single_day", "no_date_index", SINGLE_DAY_SQL,
                repeats, batch_iterations
            )
        )
        conn.execute("CREATE INDEX ix_orders_ordered_on ON orders(ordered_on)")
        conn.commit()
        add_plan(plan_blocks, "single_day / with_date_index", conn, SINGLE_DAY_SQL)
        results.extend(
            timed_runs(
                conn, "single_day", "with_date_index", SINGLE_DAY_SQL,
                repeats, batch_iterations
            )
        )
        add_plan(plan_blocks, "date_function / with_date_index", conn, FUNCTION_WRAPPED_SQL)

        # Independent product filter before/after comparison.
        conn.execute("DROP INDEX IF EXISTS ix_orderline_product")
        conn.commit()
        add_plan(plan_blocks, "product_filter / no_product_index", conn, PRODUCT_FILTER_SQL)
        results.extend(
            timed_runs(
                conn, "product_filter", "no_product_index", PRODUCT_FILTER_SQL,
                repeats, batch_iterations
            )
        )
        conn.execute("CREATE INDEX ix_orderline_product ON order_line(product_id)")
        conn.commit()
        add_plan(plan_blocks, "product_filter / with_product_index", conn, PRODUCT_FILTER_SQL)
        results.extend(
            timed_runs(
                conn, "product_filter", "with_product_index", PRODUCT_FILTER_SQL,
                repeats, batch_iterations
            )
        )

        add_plan(
            plan_blocks,
            "covering / indexed_column_only",
            conn,
            "SELECT ordered_on FROM orders WHERE ordered_on = '2026-02-14'",
        )
        add_plan(
            plan_blocks,
            "noncovering / extra_table_column",
            conn,
            "SELECT ordered_on, customer_id FROM orders WHERE ordered_on = '2026-02-14'",
        )
        conn.close()

    csv_path = evidence_dir / "benchmark-results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    medians: dict[str, float] = {}
    grouped: dict[tuple[str, str], list[float]] = {}
    for row in results:
        key = (str(row["query"]), str(row["stage"]))
        grouped.setdefault(key, []).append(float(row["per_execution_ms"]))
    for (query_name, stage), values in grouped.items():
        medians[f"{query_name}/{stage}"] = round(statistics.median(values), 6)

    summary = {
        "sqlite_version": sqlite3.sqlite_version,
        "python_version": platform.python_version(),
        "repeats": repeats,
        "batch_iterations": batch_iterations,
        "medians_ms": medians,
    }
    (evidence_dir / "benchmark-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "benchmark-plans.txt").write_text(
        "\n".join(plan_blocks), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--batch-iterations", type=int, default=100)
    args = parser.parse_args()
    summary = run_benchmark(
        args.database, args.evidence_dir, args.repeats, args.batch_iterations
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
