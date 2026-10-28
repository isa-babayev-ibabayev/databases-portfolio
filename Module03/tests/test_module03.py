from __future__ import annotations

import csv
import json
import sqlite3
import statistics
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[1]
ROOT = MODULE_DIR.parent
sys.path.insert(0, str(MODULE_DIR))

import collect_evidence  # noqa: E402
import injection_demo  # noqa: E402
import reproduce_classroom_plans  # noqa: E402


class WarehouseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.database = Path(cls.temp_dir.name) / "warehouse-test.db"
        cls.conn = sqlite3.connect(cls.database)
        cls.setup_sql = (MODULE_DIR / "setup.sql").read_text(encoding="utf-8")
        cls.conn.executescript(cls.setup_sql)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.temp_dir.cleanup()

    def test_expected_tables_and_row_counts(self):
        tables = {
            row[0]
            for row in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertEqual(tables, {"customer", "product", "orders", "order_line"})
        expected = {
            "customer": 2_000,
            "product": 500,
            "orders": 60_000,
            "order_line": 240_000,
        }
        actual = {
            table: self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in expected
        }
        self.assertEqual(actual, expected)

    def test_generated_ranges_and_formatting(self):
        self.assertEqual(
            self.conn.execute(
                "SELECT MIN(customer_id), MAX(customer_id) FROM customer"
            ).fetchone(),
            (1, 2000),
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT MIN(product_id), MAX(product_id) FROM product"
            ).fetchone(),
            (1, 500),
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT MIN(order_id), MAX(order_id), "
                "MIN(ordered_on), MAX(ordered_on) FROM orders"
            ).fetchone(),
            (1, 60000, "2025-01-01", "2026-06-24"),
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT sku FROM product WHERE product_id=1"
            ).fetchone()[0],
            "SKU-00001",
        )

    def test_setup_is_rerunnable(self):
        self.conn.executescript(self.setup_sql)
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM order_line").fetchone()[0],
            240_000,
        )

    def test_task1_deterministic_result_and_order(self):
        rows = self.conn.execute(collect_evidence.TASK1_SQL).fetchall()
        self.assertEqual(
            rows,
            [
                ("Bielefeld", 500, 11242176.0),
                ("Gütersloh", 500, 8422344.0),
                ("Münster", 500, 5493504.0),
                ("Paderborn", 500, 2815656.0),
            ],
        )
        self.assertTrue(
            all(rows[i][2] >= rows[i + 1][2] for i in range(len(rows) - 1))
        )

    def test_task1_date_boundaries(self):
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM orders WHERE ordered_on >= '2025-01-01' "
                "AND ordered_on < '2026-01-01'"
            ).fetchone()[0],
            40_575,
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM orders WHERE ordered_on = '2025-01-01'"
            ).fetchone()[0],
            111,
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM orders WHERE ordered_on = '2026-01-01'"
            ).fetchone()[0],
            111,
        )

    def test_task1_edge_fixture_distinct_revenue_and_no_order_customer(self):
        conn = sqlite3.connect(":memory:")
        conn.executescript(
            """
            CREATE TABLE customer(customer_id INTEGER PRIMARY KEY, name TEXT, city TEXT);
            CREATE TABLE product(product_id INTEGER PRIMARY KEY, sku TEXT, price REAL);
            CREATE TABLE orders(order_id INTEGER PRIMARY KEY, customer_id INTEGER,
                                ordered_on TEXT, status TEXT);
            CREATE TABLE order_line(order_id INTEGER, product_id INTEGER, qty INTEGER);
            INSERT INTO customer VALUES
              (1,'A1','A'),(2,'A2','A'),(3,'B1','B'),(4,'C1','C');
            INSERT INTO product VALUES (10,'P10',10.0),(11,'P11',2.5);
            INSERT INTO orders VALUES
              (1,1,'2025-01-01','shipped'),(2,1,'2025-12-31','shipped'),
              (3,2,'2026-01-01','shipped'),(4,2,'2025-06-01','shipped'),
              (5,3,'2024-12-31','shipped');
            INSERT INTO order_line VALUES
              (1,10,1),(1,11,2),(2,10,2),(3,10,10),(4,11,4),(5,10,9);
            """
        )
        self.assertEqual(conn.execute(collect_evidence.TASK1_SQL).fetchall(), [("A", 2, 45.0)])
        conn.close()

    def test_task1_saved_plan_exists(self):
        plan = (MODULE_DIR / "evidence" / "task1-plan.txt").read_text(encoding="utf-8")
        self.assertIn("SCAN ol", plan)
        self.assertIn("USE TEMP B-TREE FOR count(DISTINCT)", plan)


class BenchmarkEvidenceTests(unittest.TestCase):
    def test_benchmark_has_five_runs_and_correct_medians(self):
        csv_path = MODULE_DIR / "evidence" / "benchmark-results.csv"
        summary = json.loads(
            (MODULE_DIR / "evidence" / "benchmark-summary.json").read_text(
                encoding="utf-8"
            )
        )
        groups: dict[tuple[str, str], list[float]] = {}
        with csv_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                groups.setdefault((row["query"], row["stage"]), []).append(
                    float(row["per_execution_ms"])
                )
        for (query, stage), values in groups.items():
            self.assertGreaterEqual(len(values), 5)
            self.assertAlmostEqual(
                statistics.median(values),
                summary["medians_ms"][f"{query}/{stage}"],
                places=6,
            )

    def test_required_plans_and_negative_result_recorded(self):
        plans = (MODULE_DIR / "evidence" / "benchmark-plans.txt").read_text(
            encoding="utf-8"
        )
        for heading in (
            "dashboard / baseline",
            "dashboard / stage1_ordered_on",
            "dashboard / stage2_order_line_order",
            "dashboard / stage3_order_line_product",
        ):
            self.assertIn(heading, plans)
        self.assertIn("single_day / no_date_index\nSCAN o", plans)
        self.assertIn(
            "single_day / with_date_index\n"
            "SEARCH o USING INDEX ix_orders_ordered_on",
            plans,
        )
        self.assertIn("date_function / with_date_index\nSCAN o", plans)
        dashboard_stage3 = plans.split("## dashboard / stage3_order_line_product", 1)[1]
        dashboard_stage3 = dashboard_stage3.split("## single_day", 1)[0]
        self.assertNotIn("ix_orderline_product", dashboard_stage3)
        self.assertIn("USING COVERING INDEX ix_orders_ordered_on", plans)

    def test_benchmark_rows_and_measured_effects(self):
        summary = json.loads(
            (MODULE_DIR / "evidence" / "benchmark-summary.json").read_text(
                encoding="utf-8"
            )
        )["medians_ms"]
        self.assertGreater(
            summary["dashboard/stage2_order_line_order"],
            summary["dashboard/baseline"],
        )
        self.assertLess(
            summary["single_day/with_date_index"],
            summary["single_day/no_date_index"],
        )
        self.assertLess(
            summary["product_filter/with_product_index"],
            summary["product_filter/no_product_index"],
        )
        expected_rows = {"dashboard": 4, "single_day": 111, "product_filter": 480}
        with (MODULE_DIR / "evidence" / "benchmark-results.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            for row in csv.DictReader(handle):
                self.assertEqual(int(row["row_count"]), expected_rows[row["query"]])


class InjectionTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute(
            "CREATE TABLE customer(customer_id INTEGER PRIMARY KEY, name TEXT, city TEXT)"
        )
        self.conn.executemany(
            "INSERT INTO customer VALUES (?, ?, ?)",
            [(1, "Customer 1", "A"), (2, "O'Brien", "B"), (3, "Customer 3", "C")],
        )

    def tearDown(self):
        self.conn.close()

    def test_normal_and_apostrophe_safe_lookup(self):
        self.assertEqual(
            injection_demo.safe(self.conn, "Customer 1"), [(1, "Customer 1")]
        )
        self.assertEqual(
            injection_demo.safe(self.conn, "O'Brien"), [(2, "O'Brien")]
        )
        with self.assertRaises(sqlite3.Error):
            injection_demo.vulnerable(self.conn, "O'Brien")

    def test_payload_changes_vulnerable_query_but_not_safe_query(self):
        self.assertEqual(
            len(injection_demo.vulnerable(self.conn, injection_demo.PAYLOAD)), 3
        )
        self.assertEqual(
            injection_demo.safe(self.conn, injection_demo.PAYLOAD), []
        )
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM customer").fetchone()[0], 3
        )


class OptionalWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.conn = sqlite3.connect(Path(cls.temp_dir.name) / "window.db")
        cls.conn.executescript((MODULE_DIR / "setup.sql").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.temp_dir.cleanup()

    def test_grouped_correlated_and_window_results_match(self):
        grouped = self.conn.execute(collect_evidence.GROUPED_LATE).fetchall()
        correlated = self.conn.execute(collect_evidence.CORRELATED_LATE).fetchall()
        window = self.conn.execute(collect_evidence.WINDOW_LATE).fetchall()
        self.assertEqual(grouped, correlated)
        self.assertEqual(grouped, window)
        self.assertEqual(len(grouped), 400)


class RepositorySafetyTests(unittest.TestCase):
    def test_generated_database_is_ignored(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("*.db", gitignore)

    def test_disposable_classroom_plan_reproduction(self):
        output = reproduce_classroom_plans.reproduce()
        before, after = output.split("## after ix_job_tech")
        self.assertIn("technician equality:", before)
        self.assertIn("SCAN maint_job", before)
        self.assertIn(
            "SEARCH maint_job USING INDEX ix_job_tech (technician=?)", after
        )
        self.assertIn("function-wrapped technician:", after)
        self.assertIn("SCAN maint_job", after)

    def test_required_documentation_files_exist(self):
        for relative in (
            "README.md",
            "sql-notes.md",
            "task1-report.md",
            "task2-benchmark.md",
            "task4-algebra-to-plan.md",
            "task5-window-functions.md",
            "technical-completion-report.md",
        ):
            self.assertTrue((MODULE_DIR / relative).exists(), relative)

    def test_relative_markdown_links_resolve(self):
        import re

        markdown_files = list(MODULE_DIR.glob("*.md")) + [
            ROOT / "Reflections" / "ref03.md"
        ]
        pattern = re.compile(r"\[[^\]]+\]\((?!https?://|#)([^)#]+)(?:#[^)]+)?\)")
        missing = []
        for source in markdown_files:
            for relative in pattern.findall(source.read_text(encoding="utf-8")):
                if not (source.parent / relative).exists():
                    missing.append(f"{source.name} -> {relative}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
