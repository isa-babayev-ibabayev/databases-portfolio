"""Independent checks for the Module 6a generated data and recorded evidence."""

from __future__ import annotations

import csv
import hashlib
import importlib
import sqlite3
import statistics
import subprocess
import sys
import unittest
from collections import defaultdict
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "Module06a"
sys.path.insert(0, str(MODULE))

boundary = importlib.import_module("boundary")
plan = importlib.import_module("plan")
prepare = importlib.import_module("prepare")
race = importlib.import_module("race")
to_parquet = importlib.import_module("to_parquet")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


class GeneratedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = prepare.source_facts()
        cls.history = prepare.validate_history(prepare.HISTORY, cls.source)
        cls.csv = prepare.validate_csv(prepare.CSV_PATH, cls.source["rows"])
        cls.parquet = to_parquet.validate(to_parquet.PARQUET)

    def test_01_source_is_the_expected_preserved_module5_dataset(self) -> None:
        self.assertEqual(self.source["rows"], 200_000)
        self.assertEqual(self.source["sum_part_price"], 2_100_000.0)
        self.assertEqual(
            self.source["sha256"],
            "BCCCA944EEBFF2C42D18DA737F251587CAFB6EB93D84E561D1FCE9BEA6BA4C3D",
        )

    def test_02_history_has_ten_complete_periods(self) -> None:
        self.assertEqual(self.history["rows"], 2_000_000)
        self.assertEqual(self.history["sum_part_price"], 21_000_000.0)
        self.assertEqual(len(self.history["periods"]), 10)
        self.assertTrue(all(row[1] == 200_000 for row in self.history["periods"]))
        self.assertEqual(self.history["periods"][1][2:4], [1_000_001, 1_020_000])

    def test_03_history_dates_nulls_and_integrity_are_valid(self) -> None:
        self.assertEqual((self.history["min_date"], self.history["max_date"]),
                         ("2026-01-01", "2028-06-27"))
        self.assertEqual(self.history["null_rows"], 0)
        self.assertEqual(self.history["malformed_dates"], 0)
        self.assertEqual(self.history["integrity_check"], "ok")

    def test_04_csv_is_the_200k_source_export(self) -> None:
        self.assertEqual(self.csv["data_rows"], 200_000)
        self.assertEqual(tuple(self.csv["header"]), prepare.COLUMNS)

    def test_05_parquet_matches_sqlite_on_multiple_invariants(self) -> None:
        result = self.parquet
        self.assertTrue(result["valid"])
        for key in ("rows", "sum_part_price", "sum_job_id", "min_date", "max_date"):
            self.assertEqual(result["sqlite"][key], result["parquet"][key])
        self.assertTrue(all(value == 0 for value in result["parquet"]["null_counts"].values()))

    def test_06_parquet_schema_preserves_typed_date_and_price(self) -> None:
        schema = dict(self.parquet["parquet"]["schema"])
        self.assertEqual(schema["done_on"], "DATE")
        self.assertEqual(schema["part_price"], "DOUBLE")
        self.assertEqual(schema["job_id"], "BIGINT")

    def test_07_prepare_normal_run_is_safe_and_idempotent(self) -> None:
        before = file_hash(prepare.SOURCE)
        completed = subprocess.run(
            [sys.executable, "-B", str(MODULE / "prepare.py")],
            cwd=ROOT, capture_output=True, text=True, timeout=60, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"source_hash_unchanged": true', completed.stdout)
        self.assertIn("reused validated existing file", completed.stdout)
        self.assertEqual(file_hash(prepare.SOURCE), before)


class QueryAndPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sqlite_connection = sqlite3.connect(
            f"file:{prepare.HISTORY.resolve().as_posix()}?mode=ro&immutable=1", uri=True
        )
        duck_connection = duckdb.connect()
        parquet = f"read_parquet('{race.sql_path(to_parquet.PARQUET)}')"
        try:
            cls.dashboard_sqlite = race.canonical(
                sqlite_connection.execute(
                    race.DASHBOARD.format(src="report_history")
                ).fetchall()
            )
            cls.dashboard_duck = race.canonical(
                duck_connection.execute(race.DASHBOARD.format(src=parquet)).fetchall()
            )
            cls.monthly_sqlite = race.canonical(
                sqlite_connection.execute(
                    race.MONTHLY_SQLITE.format(src="report_history")
                ).fetchall()
            )
            cls.monthly_duck = race.canonical(
                duck_connection.execute(
                    race.MONTHLY_DUCKDB.format(src=parquet)
                ).fetchall()
            )
        finally:
            sqlite_connection.close()
            duck_connection.close()

    def test_08_dashboard_results_are_equivalent(self) -> None:
        self.assertEqual(self.dashboard_sqlite, self.dashboard_duck)
        self.assertEqual(len(self.dashboard_sqlite), 350)

    def test_09_monthly_results_are_equivalent(self) -> None:
        self.assertEqual(self.monthly_sqlite, self.monthly_duck)
        self.assertEqual(len(self.monthly_sqlite), 1_500)
        self.assertIsNotNone(self.monthly_sqlite[0][0])

    def test_10_real_benchmark_evidence_is_interleaved_and_median_based(self) -> None:
        with (MODULE / "evidence/benchmark-results.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            rows = list(csv.DictReader(stream))
        grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
        for row in rows:
            grouped[(row["workload"], row["engine"])].append(float(row["elapsed_ms"]))
        self.assertTrue(all(len(samples) == 5 for samples in grouped.values()))
        self.assertAlmostEqual(statistics.median(grouped[("dashboard", "sqlite")]),
                               5832.1468, places=4)
        self.assertAlmostEqual(statistics.median(grouped[("monthly", "duckdb")]),
                               74.2686, places=4)
        for workload in ("dashboard", "monthly"):
            run_one = [r for r in rows if r["workload"] == workload and r["run"] == "1"]
            run_two = [r for r in rows if r["workload"] == workload and r["run"] == "2"]
            self.assertEqual(min(run_one, key=lambda r: r["order_position"])["engine"], "sqlite")
            self.assertEqual(min(run_two, key=lambda r: r["order_position"])["engine"], "duckdb")

    def test_11_plans_contain_the_observed_scan_and_group_operators(self) -> None:
        duck_plan, sqlite_plan = plan.capture_plans()
        self.assertIn("READ_PARQUET", duck_plan)
        self.assertIn("HASH_GROUP_BY", duck_plan)
        self.assertIn("2,000,000 rows", duck_plan)
        self.assertIn("machine_id", duck_plan)
        self.assertTrue(any("SCAN report_history" in line for line in sqlite_plan))
        self.assertTrue(any("TEMP B-TREE" in line for line in sqlite_plan))


class BoundaryAndDecisionTests(unittest.TestCase):
    def test_12_boundary_functions_return_correct_results_on_small_sample(self) -> None:
        old_n, old_sum = boundary.N, boundary.EXPECTED_SUM
        boundary.N = 20
        boundary.EXPECTED_SUM = sum(index * 1.5 for index in range(boundary.N))
        try:
            sqlite_result = boundary.sqlite_once()
            duck_result = boundary.duckdb_once()
            batched_result = boundary.duckdb_once(batched=True)
        finally:
            boundary.N, boundary.EXPECTED_SUM = old_n, old_sum
        for result in (sqlite_result, duck_result, batched_result):
            self.assertGreater(result["insert_ms"], 0)
            self.assertGreater(result["lookup_ms"], 0)

    def test_13_boundary_evidence_supports_the_reported_winner(self) -> None:
        text = (MODULE / "evidence/boundary-results.md").read_text(encoding="utf-8")
        self.assertIn("3.30 ms", text)
        self.assertIn("6,549.83 ms", text)
        self.assertIn("1,987.33× slower", text)
        self.assertIn("625.22× slower", text)
        self.assertIn("did not improve", text)

    def test_14_compressed_copy_matches_default_parquet(self) -> None:
        default = race.sql_path(MODULE / "report_history.parquet")
        zstd = race.sql_path(MODULE / "report_zstd.parquet")
        connection = duckdb.connect()
        try:
            query = "SELECT COUNT(*), ROUND(SUM(part_price),2) FROM read_parquet('{}')"
            self.assertEqual(
                connection.execute(query.format(default)).fetchone(),
                connection.execute(query.format(zstd)).fetchone(),
            )
        finally:
            connection.close()
        self.assertLess((MODULE / "report_zstd.parquet").stat().st_size,
                        (MODULE / "report_history.parquet").stat().st_size)

    def test_15_recommendation_uses_measurements_and_failure_behavior(self) -> None:
        text = (MODULE / "recommendation.md").read_text(encoding="utf-8")
        for expected in ("5,832.15", "74.13", "7,013.05", "74.27", "1,367,276"):
            self.assertIn(expected, text)
        self.assertIn("If that refresh fails", text)
        self.assertIn("last validated file", text)
        self.assertIn("SQLite remains the operational system of record", text)

    def test_16_generated_outputs_are_gitignored(self) -> None:
        paths = [
            "Module06a/history.db",
            "Module06a/report_jobpart.csv",
            "Module06a/report_history.parquet",
            "Module06a/report_zstd.parquet",
        ]
        for path in paths:
            with self.subTest(path=path):
                completed = subprocess.run(
                    ["git", "check-ignore", "--quiet", path], cwd=ROOT, check=False
                )
                self.assertEqual(completed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
