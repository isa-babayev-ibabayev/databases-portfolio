from __future__ import annotations

import json
import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parent
sys.path.insert(0, str(MODULE))

import concurrency_demo  # noqa: E402
import json_bench  # noqa: E402
import kv_compare  # noqa: E402


class JsonExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="module06b-json-test-")
        cls.database = Path(cls.temp.name) / "test.db"
        cls.result = json_bench.run_experiment(cls.database, rebuild=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_exactly_one_thousand_rows_are_valid_json(self) -> None:
        self.assertEqual(self.result["row_count"], 1_000)
        self.assertEqual(self.result["json_valid_rows"], 1_000)

    def test_three_vendors_account_for_every_row(self) -> None:
        self.assertEqual(sum(self.result["vendor_counts"].values()), 1_000)
        self.assertEqual(set(self.result["vendor_counts"]), {"Fanuc", "Siemens", "Arburg"})

    def test_json_extract_returns_first_five_vendors(self) -> None:
        self.assertEqual(
            self.result["vendor_first_five"],
            [
                {"name": "cnc-01", "vendor": "Siemens"},
                {"name": "cnc-02", "vendor": "Fanuc"},
                {"name": "molder-07", "vendor": "Arburg"},
                {"name": "device-0004", "vendor": "Fanuc"},
                {"name": "device-0005", "vendor": "Arburg"},
            ],
        )

    def test_arrow_operator_returns_first_five_firmware_values(self) -> None:
        self.assertEqual(
            [row["firmware"] for row in self.result["firmware_first_five"]],
            ["4.2", "3.9", "8.1", "4.4", "0.5"],
        )

    def test_json_each_expands_cnc_object(self) -> None:
        self.assertEqual(
            {row["key"]: row["value"] for row in self.result["json_each_for_cnc_01"]},
            {"vendor": "Siemens", "firmware": "4.2", "calibrated": "2026-01-10"},
        )

    def test_exact_and_shorthand_queries_are_logically_equal(self) -> None:
        self.assertTrue(self.result["queries_return_same_rows"])
        self.assertEqual(self.result["fanuc_result_count"], 334)

    def test_exact_expression_uses_expression_index(self) -> None:
        self.assertTrue(self.result["exact_expression_uses_index"])
        self.assertIn("ix_device_vendor", " ".join(self.result["exact_expression_plan"]))

    def test_shorthand_expression_scans(self) -> None:
        self.assertTrue(self.result["shorthand_scans_table"])

    def test_invalid_json_is_rejected(self) -> None:
        self.assertTrue(self.result["constraint_experiments"]["invalid_json_rejected"])

    def test_flexible_keys_and_missing_optional_key(self) -> None:
        constraints = self.result["constraint_experiments"]
        self.assertTrue(constraints["different_keys_accepted"])
        self.assertTrue(constraints["missing_optional_returns_null"])

    def test_strict_table_rejects_blob_in_text_column(self) -> None:
        self.assertTrue(self.result["constraint_experiments"]["strict_blob_rejected"])

    def test_existing_valid_database_is_reused(self) -> None:
        self.assertEqual(json_bench.build_database(self.database), "reused validated database")


class KeyValueTests(unittest.TestCase):
    def test_record_generator_is_deterministic(self) -> None:
        self.assertEqual(
            kv_compare.records(2),
            [
                ("session-0", "user-0:filter=city:0"),
                ("session-1", "user-1:filter=city:1"),
            ],
        )

    def test_backends_store_equivalent_values(self) -> None:
        result = kv_compare.benchmark(n=200, runs=2)
        self.assertTrue(result["verified_equivalent"])
        self.assertEqual(result["shelve"]["count"], 200)
        self.assertEqual(result["sqlite"]["count"], 200)

    def test_trial_order_is_alternated(self) -> None:
        result = kv_compare.benchmark(n=20, runs=3)
        self.assertEqual(result["trial_order"][0], ["shelve", "sqlite"])
        self.assertEqual(result["trial_order"][1], ["sqlite", "shelve"])

    def test_invalid_benchmark_size_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            kv_compare.benchmark(n=0, runs=1)


class ConcurrencyTests(unittest.TestCase):
    def test_two_writer_lock_and_retry(self) -> None:
        result = concurrency_demo.run_demo(busy_timeout_ms=100)
        self.assertEqual(result["independent_connections"], 2)
        self.assertIn("locked", result["second_writer_initial_result"])
        self.assertTrue(result["retry_after_first_commit_succeeded"])
        self.assertEqual(result["final_parts_produced"], 2)
        self.assertTrue(result["temporary_directory_removed"])

    def test_demo_is_explicitly_not_postgresql_evidence(self) -> None:
        self.assertIn("not a PostgreSQL", concurrency_demo.run_demo(50)["scope"])


class DocumentationTests(unittest.TestCase):
    def test_expected_documents_exist(self) -> None:
        expected = [
            "README.md",
            "engine-notes.md",
            "decision-record.md",
            "project-ticket.md",
            "learning-guide.md",
            "evidence/json-output.txt",
            "evidence/kv-results.md",
            "evidence/concurrency-results.txt",
        ]
        for relative in expected:
            self.assertTrue((MODULE / relative).is_file(), relative)

    def test_generated_databases_are_ignored(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("*.db", ignore)
        self.assertIn("Module06b/sessions*", ignore)

    def test_reflection_marks_human_input(self) -> None:
        reflection = (ROOT / "Reflections" / "ref06b.md").read_text(encoding="utf-8")
        self.assertIn("STUDENT INPUT REQUIRED", reflection)

    def test_decision_record_uses_measured_module06a_values(self) -> None:
        decision = (MODULE / "decision-record.md").read_text(encoding="utf-8")
        self.assertIn("5,832.15 ms", decision)
        self.assertIn("74.13 ms", decision)

    def test_decision_record_has_all_rows_and_human_boundary(self) -> None:
        decision = (MODULE / "decision-record.md").read_text(encoding="utf-8")
        for workload in [
            "Month-end analytical report",
            "Sensor/job ingestion and integrity",
            "Vendor-specific device metadata",
            "Dashboard session state",
            "Concurrent multi-user operational service",
        ]:
            self.assertIn(workload, decision)
        self.assertIn("STUDENT INPUT REQUIRED", decision)
        self.assertIn("If Kortmann could run only one engine", decision)

    def test_evidence_files_are_parseable_or_structured(self) -> None:
        json.loads((MODULE / "evidence" / "json-output.txt").read_text(encoding="utf-8"))
        json.loads((MODULE / "evidence" / "concurrency-results.txt").read_text(encoding="utf-8"))
        self.assertIn("20,000", (MODULE / "evidence" / "kv-results.md").read_text(encoding="utf-8"))

    def test_relative_markdown_links_resolve(self) -> None:
        for document in MODULE.rglob("*.md"):
            content = document.read_text(encoding="utf-8")
            for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", content):
                target = match.group(1).split("#", 1)[0]
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                self.assertTrue((document.parent / target).resolve().exists(), f"{document}: {target}")

    def test_readme_preserves_five_official_learning_goals(self) -> None:
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        for phrase in [
            "semi-structured data (JSON)",
            "key-value access pattern",
            "ACID vs. BASE",
            "defend the choice with a measurement",
            "when the same data lives on a **server**",
        ]:
            self.assertIn(phrase, readme)


if __name__ == "__main__":
    unittest.main()
