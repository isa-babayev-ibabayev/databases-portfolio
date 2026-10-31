"""Isolated acceptance tests for Module 4."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR))

from ingest import UPSERT_SQL, ingest  # noqa: E402


SETUP_SQL = (MODULE_DIR / "setup.sql").read_text(encoding="utf-8")
SCRATCH_SQL = (MODULE_DIR / "scratch-constraints.sql").read_text(encoding="utf-8")


class Module04Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.executescript(SETUP_SQL)

    def tearDown(self) -> None:
        self.connection.close()

    def insert_reading(
        self,
        sensor_id: int = 1,
        timestamp: str = "2026-03-01 10:00:00",
        value: object = 42.0,
        interval_s: int = 1,
    ) -> sqlite3.Cursor:
        return self.connection.execute(
            "INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (?,?,?,?)",
            (sensor_id, timestamp, value, interval_s),
        )

    # Constraints
    def test_valid_sensor_insertion(self) -> None:
        self.connection.execute(
            "INSERT INTO sensor VALUES (3,'cnc-02','spindle_load','percent')"
        )
        self.assertEqual(3, self.connection.execute("SELECT count(*) FROM sensor").fetchone()[0])

    def test_duplicate_sensor_natural_key_rejected(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO sensor VALUES (3,'cnc-01','temp_c','degC')"
            )

    def test_unsupported_metric_rejected(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO sensor VALUES (3,'cnc-02','humidity','percent')"
            )

    def test_missing_mandatory_value_rejected(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO reading(sensor_id,ts,interval_s) VALUES (1,'2026-03-01 10:00:00',1)"
            )

    def test_nonpositive_interval_rejected(self) -> None:
        for interval in (0, -1):
            with self.subTest(interval=interval), self.assertRaises(sqlite3.IntegrityError):
                self.insert_reading(timestamp=f"2026-03-01 10:00:0{abs(interval)}", interval_s=interval)

    def test_temperature_outside_domain_rejected(self) -> None:
        for value in (-273.16, 5000.01):
            with self.subTest(value=value), self.assertRaises(sqlite3.IntegrityError):
                self.insert_reading(timestamp=f"outside-{value}", value=value)

    def test_incorrect_real_type_rejected(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert_reading(value="hot")

    def test_foreign_key_rejected(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert_reading(sensor_id=99)

    def test_primary_key_uniqueness(self) -> None:
        self.connection.execute(
            "INSERT INTO reading(reading_id,sensor_id,ts,value,interval_s) VALUES (20,1,'pk-one',1,1)"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO reading(reading_id,sensor_id,ts,value,interval_s) VALUES (20,1,'pk-two',2,1)"
            )

    def test_generated_column_calculation(self) -> None:
        cursor = self.insert_reading(value=2.5, interval_s=4)
        energy = self.connection.execute(
            "SELECT energy_j FROM reading WHERE reading_id=?", (cursor.lastrowid,)
        ).fetchone()[0]
        self.assertEqual(10.0, energy)

    def test_manual_generated_column_assignment_rejected(self) -> None:
        with self.assertRaises(sqlite3.OperationalError):
            self.connection.execute(
                "INSERT INTO reading(sensor_id,ts,value,interval_s,energy_j) VALUES (1,'manual',2,3,999)"
            )

    def test_check_allows_null_without_not_null(self) -> None:
        self.connection.executescript(SCRATCH_SQL)
        self.connection.execute("INSERT INTO check_only VALUES (NULL)")
        self.assertIsNone(self.connection.execute("SELECT value FROM check_only").fetchone()[0])
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute("INSERT INTO check_and_not_null VALUES (NULL)")

    def test_strict_numeric_string_is_coerced(self) -> None:
        cursor = self.insert_reading(value="42.5")
        row = self.connection.execute(
            "SELECT value,typeof(value) FROM reading WHERE reading_id=?", (cursor.lastrowid,)
        ).fetchone()
        self.assertEqual((42.5, "real"), row)

    def test_empty_machine_identifier_is_currently_accepted(self) -> None:
        self.connection.execute(
            "INSERT INTO sensor VALUES (3,'','spindle_load','percent')"
        )
        self.assertEqual("", self.connection.execute("SELECT machine_id FROM sensor WHERE sensor_id=3").fetchone()[0])

    # UPSERT and ingestion
    def test_upsert_inserts_new_reading(self) -> None:
        self.connection.execute(UPSERT_SQL, (1, "new-upsert", 10.0, 1))
        self.assertEqual(1, self.connection.execute("SELECT count(*) FROM reading WHERE ts='new-upsert'").fetchone()[0])

    def test_duplicate_upsert_replay_does_not_duplicate(self) -> None:
        row = (1, "replay", 10.0, 1)
        self.connection.execute(UPSERT_SQL, row)
        self.connection.execute(UPSERT_SQL, row)
        self.assertEqual(1, self.connection.execute("SELECT count(*) FROM reading WHERE ts='replay'").fetchone()[0])

    def test_corrected_upsert_updates_existing_row(self) -> None:
        self.connection.execute(UPSERT_SQL, (1, "corrected", 10.0, 1))
        self.connection.execute(UPSERT_SQL, (1, "corrected", 11.0, 2))
        self.assertEqual((11.0, 2), self.connection.execute("SELECT value,interval_s FROM reading WHERE ts='corrected'").fetchone())

    def test_multiple_csv_imports_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "edge.db"
            first = ingest(database, MODULE_DIR / "readings.csv", initialize=True)
            second = ingest(database, MODULE_DIR / "readings.csv")
        self.assertEqual((4, 0), (first.readings_after, first.duplicate_keys))
        self.assertEqual((4, 0), (second.readings_after, second.duplicate_keys))
        self.assertEqual(first.audit_rows, second.audit_rows)

    def test_invalid_ingestion_rolls_back_complete_batch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "edge.db"
            with self.assertRaises(sqlite3.IntegrityError):
                ingest(database, MODULE_DIR / "invalid-readings.csv", initialize=True)
            connection = sqlite3.connect(database)
            try:
                count = connection.execute("SELECT count(*) FROM reading").fetchone()[0]
                audit_count = connection.execute("SELECT count(*) FROM audit").fetchone()[0]
                alarm_count = connection.execute("SELECT count(*) FROM alarm").fetchone()[0]
            finally:
                connection.close()
        self.assertEqual((1, 0, 0), (count, audit_count, alarm_count))

    # Triggers
    def test_vibration_over_threshold_creates_alarm(self) -> None:
        self.insert_reading(sensor_id=2, value=2.7)
        self.assertEqual(1, self.connection.execute("SELECT count(*) FROM alarm").fetchone()[0])

    def test_vibration_at_threshold_does_not_create_alarm(self) -> None:
        self.insert_reading(sensor_id=2, value=2.0)
        self.assertEqual(0, self.connection.execute("SELECT count(*) FROM alarm").fetchone()[0])

    def test_temperature_does_not_create_vibration_alarm(self) -> None:
        self.insert_reading(sensor_id=1, value=100.0)
        self.assertEqual(0, self.connection.execute("SELECT count(*) FROM alarm").fetchone()[0])

    def test_value_update_creates_audit(self) -> None:
        self.connection.execute("UPDATE reading SET value=42 WHERE reading_id=1")
        self.assertEqual(1, self.connection.execute("SELECT count(*) FROM audit").fetchone()[0])

    def test_audit_old_and_new_values_are_accurate(self) -> None:
        self.connection.execute("UPDATE reading SET value=42 WHERE reading_id=1")
        self.assertEqual((41.5, 42.0), self.connection.execute("SELECT old_value,new_value FROM audit").fetchone())

    def test_trigger_side_effect_rolls_back_with_reading(self) -> None:
        self.connection.execute("BEGIN")
        self.insert_reading(sensor_id=2, value=2.7)
        self.connection.rollback()
        self.assertEqual(0, self.connection.execute("SELECT count(*) FROM alarm").fetchone()[0])
        self.assertEqual(1, self.connection.execute("SELECT count(*) FROM reading").fetchone()[0])

    def test_rejected_insert_creates_no_alarm(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert_reading(sensor_id=2, value=9000)
        self.assertEqual(0, self.connection.execute("SELECT count(*) FROM alarm").fetchone()[0])

    def test_baseline_noop_update_audits_but_conditional_upsert_does_not(self) -> None:
        self.connection.execute("UPDATE reading SET value=value WHERE reading_id=1")
        self.assertEqual(1, self.connection.execute("SELECT count(*) FROM audit").fetchone()[0])
        self.connection.execute(UPSERT_SQL, (1, "2026-03-01 08:00:00", 41.5, 1))
        self.assertEqual(1, self.connection.execute("SELECT count(*) FROM audit").fetchone()[0])

    def test_insert_only_alarm_misses_upsert_threshold_crossing(self) -> None:
        self.connection.execute(UPSERT_SQL, (2, "crossing", 1.0, 1))
        self.connection.execute(UPSERT_SQL, (2, "crossing", 3.0, 1))
        self.assertEqual(0, self.connection.execute("SELECT count(*) FROM alarm").fetchone()[0])
        self.assertEqual(1, self.connection.execute("SELECT count(*) FROM audit").fetchone()[0])

    # Read-only behavior and consistency
    def test_machine_health_view(self) -> None:
        self.assertEqual(
            ("cnc-01", "temp_c", 41.5, 1),
            self.connection.execute("SELECT machine_id,metric,peak,n FROM machine_health").fetchone(),
        )

    def test_read_only_uri_refuses_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "edge.db"
            disk = sqlite3.connect(database)
            disk.executescript(SETUP_SQL)
            disk.close()
            read_only = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
            try:
                self.assertEqual(1, read_only.execute("SELECT count(*) FROM reading").fetchone()[0])
                with self.assertRaises(sqlite3.OperationalError):
                    read_only.execute("DELETE FROM reading")
            finally:
                read_only.close()

    def test_query_only_refuses_writes(self) -> None:
        self.connection.execute("PRAGMA query_only=ON")
        with self.assertRaises(sqlite3.OperationalError):
            self.connection.execute("DELETE FROM reading")

    def test_foreign_key_check_finds_no_violations(self) -> None:
        self.assertEqual([], self.connection.execute("PRAGMA foreign_key_check").fetchall())

    def test_integrity_check_succeeds(self) -> None:
        self.assertEqual("ok", self.connection.execute("PRAGMA integrity_check").fetchone()[0])

    def test_foreign_keys_are_enabled(self) -> None:
        self.assertEqual(1, self.connection.execute("PRAGMA foreign_keys").fetchone()[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
