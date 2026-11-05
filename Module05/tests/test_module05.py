"""Meaningful acceptance tests for Module 5."""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR))

from experiment import (  # noqa: E402
    DENORMALIZED_QUERY,
    NORMALIZED_QUERY,
    anomaly_results,
    build_database,
    dashboard_rows,
    query_plan,
    run_full,
    table_counts,
)


class AnomalyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = anomaly_results()

    def test_update_anomaly_creates_two_site_values(self) -> None:
        self.assertEqual([["Bielefeld", 1], ["Gütersloh", 2]], self.result["update"]["inconsistent_sites"])

    def test_normalized_site_update_changes_one_row(self) -> None:
        self.assertEqual(1, self.result["update"]["normalized_rows_changed"])

    def test_insert_anomaly_needs_null_job_placeholder(self) -> None:
        self.assertTrue(self.result["insert"]["placeholder_has_null_job_fields"])

    def test_normalized_part_insert_needs_no_job(self) -> None:
        self.assertEqual(1, self.result["insert"]["normalized_part_rows_inserted"])

    def test_delete_anomaly_loses_flat_price_but_not_part(self) -> None:
        self.assertEqual(0, self.result["delete"]["flat_after_count"])
        self.assertEqual([1, 7.0], self.result["delete"]["normalized_part"])


class LargeDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="module05-tests-")
        cls.database = Path(cls.temporary.name) / "normalize.db"
        cls.connection = build_database(cls.database)
        cls.result = run_full(cls.connection, trials=5)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.connection.close()
        cls.temporary.cleanup()

    def test_expected_table_counts(self) -> None:
        self.assertEqual(
            {
                "flat_jobpart": 200000,
                "machine": 50,
                "part": 10,
                "job": 20000,
                "job_part": 200000,
                "report_jobpart": 200000,
            },
            table_counts(self.connection),
        )

    def test_candidate_key_is_unique(self) -> None:
        duplicates = self.connection.execute(
            "SELECT COUNT(*) FROM (SELECT job_id,part_no,COUNT(*) n FROM flat_jobpart GROUP BY job_id,part_no HAVING n>1)"
        ).fetchone()[0]
        self.assertEqual(0, duplicates)

    def test_candidate_key_is_minimal_under_model(self) -> None:
        total = self.connection.execute("SELECT COUNT(*) FROM flat_jobpart").fetchone()[0]
        distinct_jobs = self.connection.execute("SELECT COUNT(DISTINCT job_id) FROM flat_jobpart").fetchone()[0]
        distinct_parts = self.connection.execute("SELECT COUNT(DISTINCT part_no) FROM flat_jobpart").fetchone()[0]
        self.assertLess(distinct_jobs, total)
        self.assertLess(distinct_parts, total)

    def test_job_functional_dependencies_hold(self) -> None:
        conflicts = self.connection.execute(
            "SELECT COUNT(*) FROM (SELECT job_id FROM flat_jobpart GROUP BY job_id HAVING COUNT(DISTINCT machine_id)>1 OR COUNT(DISTINCT technician)>1 OR COUNT(DISTINCT done_on)>1)"
        ).fetchone()[0]
        self.assertEqual(0, conflicts)

    def test_machine_to_site_dependency_holds(self) -> None:
        conflicts = self.connection.execute(
            "SELECT COUNT(*) FROM (SELECT machine_id FROM flat_jobpart GROUP BY machine_id HAVING COUNT(DISTINCT site)>1)"
        ).fetchone()[0]
        self.assertEqual(0, conflicts)

    def test_part_to_price_dependency_holds(self) -> None:
        conflicts = self.connection.execute(
            "SELECT COUNT(*) FROM (SELECT part_no FROM flat_jobpart GROUP BY part_no HAVING COUNT(DISTINCT part_price)>1)"
        ).fetchone()[0]
        self.assertEqual(0, conflicts)

    def test_part_has_ten_values_from_k_one_to_ten(self) -> None:
        self.assertEqual(("P-0002", "P-0011", 10), self.connection.execute("SELECT MIN(part_no),MAX(part_no),COUNT(*) FROM part").fetchone())

    def test_foreign_keys_and_integrity(self) -> None:
        self.assertEqual([], self.result["foreign_key_check"])
        self.assertEqual("ok", self.result["integrity_check"])

    def test_join_reconstructs_flat_relation_both_directions(self) -> None:
        self.assertEqual(0, self.result["flat_minus_join"])
        self.assertEqual(0, self.result["join_minus_flat"])

    def test_dashboard_outputs_are_equivalent(self) -> None:
        self.assertEqual(
            dashboard_rows(self.connection, NORMALIZED_QUERY),
            dashboard_rows(self.connection, DENORMALIZED_QUERY),
        )
        self.assertTrue(self.result["round4"]["equivalent"])

    def test_query_plans_are_captured(self) -> None:
        self.assertTrue(query_plan(self.connection, NORMALIZED_QUERY))
        self.assertTrue(query_plan(self.connection, DENORMALIZED_QUERY))

    def test_benchmark_has_five_samples_and_positive_medians(self) -> None:
        round4 = self.result["round4"]
        self.assertEqual(5, len(round4["normalized_samples_ms"]))
        self.assertEqual(5, len(round4["denormalized_samples_ms"]))
        self.assertGreater(round4["normalized_median_ms"], 0)
        self.assertGreater(round4["denormalized_median_ms"], 0)

    def test_normalized_update_affects_one_row(self) -> None:
        self.assertEqual(1, self.result["round5"]["normalized_update"]["affected_rows"])

    def test_denormalized_update_affects_four_thousand_rows(self) -> None:
        self.assertEqual(4000, self.result["round5"]["denormalized_update"]["affected_rows"])

    def test_update_benchmarks_restore_original_state(self) -> None:
        self.assertTrue(self.result["round5"]["normalized_update"]["rollback_verified"])
        self.assertTrue(self.result["round5"]["denormalized_update"]["rollback_verified"])
        self.assertEqual("Gütersloh", self.connection.execute("SELECT site FROM machine WHERE machine_id='cnc-02'").fetchone()[0])

    def test_storage_measurements_are_positive_when_available(self) -> None:
        storage = self.result["round5"]["storage"]
        if not storage["available"]:
            self.skipTest(storage["error"])
        self.assertGreater(storage["table_only_bytes"]["normalized"], 0)
        self.assertGreater(storage["table_only_bytes"]["denormalized"], 0)

    def test_index_experiment_has_five_samples_and_restores_index(self) -> None:
        index = self.result["round5"]["index_experiment"]
        self.assertEqual(5, len(index["indexed_samples_ms"]))
        self.assertEqual(5, len(index["unindexed_samples_ms"]))
        self.assertTrue(index["index_restored"])
        exists = self.connection.execute(
            "SELECT COUNT(*) FROM sqlite_schema WHERE type='index' AND name='ix_report_machine'"
        ).fetchone()[0]
        self.assertEqual(1, exists)

    def test_indexed_and_unindexed_plans_are_distinct(self) -> None:
        index = self.result["round5"]["index_experiment"]
        self.assertTrue(any("ix_report_machine" in row for row in index["indexed_plan"]))
        self.assertFalse(any("ix_report_machine" in row for row in index["unindexed_plan"]))


class PortfolioDocumentationTests(unittest.TestCase):
    def test_recommendation_uses_measured_evidence(self) -> None:
        text = (MODULE_DIR / "recommendation.md").read_text(encoding="utf-8")
        data = json.loads((MODULE_DIR / "evidence" / "benchmark-results.json").read_text(encoding="utf-8"))
        self.assertIn("Measured results", text)
        self.assertIn("synchron", text.lower())
        self.assertIn(f"{data['round4']['normalized_median_ms']:.4f}", text)
        self.assertIn(f"{data['round4']['denormalized_median_ms']:.4f}", text)
        self.assertIn("4,000 report rows", text)
        self.assertIn(f"{data['round5']['storage']['table_only_bytes']['denormalized'] / 1024:,.1f}", text)

    def test_curiosities_are_prepared_not_claimed_as_shared(self) -> None:
        text = (MODULE_DIR / "normalization-notes.md").read_text(encoding="utf-8")
        self.assertIn("Prepared curiosities", text)
        self.assertIn("not documented", text.lower())

    def test_saved_benchmark_summary_is_parseable(self) -> None:
        data = json.loads((MODULE_DIR / "evidence" / "benchmark-results.json").read_text(encoding="utf-8"))
        self.assertEqual(200000, data["counts"]["flat_jobpart"])
        self.assertTrue(data["round4"]["equivalent"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
