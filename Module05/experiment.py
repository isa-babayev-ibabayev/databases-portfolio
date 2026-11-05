"""Shared, reproducible Module 5 experiment engine."""

from __future__ import annotations

import json
import platform
import sqlite3
import statistics
import time
from pathlib import Path
from typing import Any


MODULE_DIR = Path(__file__).resolve().parent
SETUP_SQL = (MODULE_DIR / "setup.sql").read_text(encoding="utf-8")

NORMALIZED_QUERY = """
SELECT m.machine_id, m.site, j.technician, SUM(p.part_price) AS cost
FROM job AS j
JOIN machine AS m ON m.machine_id = j.machine_id
JOIN job_part AS jp ON jp.job_id = j.job_id
JOIN part AS p ON p.part_no = jp.part_no
WHERE j.done_on >= date('2026-03-01')
GROUP BY m.machine_id, m.site, j.technician
ORDER BY m.machine_id, j.technician
"""

DENORMALIZED_QUERY = """
SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM report_jobpart
WHERE done_on >= date('2026-03-01')
GROUP BY machine_id, site, technician
ORDER BY machine_id, technician
"""


def connect(database: str | Path = ":memory:") -> sqlite3.Connection:
    # Disable Python's prepared-statement cache so EXPLAIN is reparsed after
    # CREATE/DROP INDEX during the controlled Round 5 comparison.
    connection = sqlite3.connect(database, cached_statements=0)
    connection.execute("PRAGMA foreign_keys = ON")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        connection.close()
        raise RuntimeError("foreign-key enforcement could not be enabled")
    return connection


def build_database(database: str | Path = ":memory:") -> sqlite3.Connection:
    connection = connect(database)
    connection.executescript(SETUP_SQL)
    connection.commit()
    return connection


def table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    names = ("flat_jobpart", "machine", "part", "job", "job_part", "report_jobpart")
    return {
        name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        for name in names
    }


def canonical(rows: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    return [tuple(round(value, 8) if isinstance(value, float) else value for value in row) for row in rows]


def dashboard_rows(connection: sqlite3.Connection, query: str) -> list[tuple[Any, ...]]:
    return canonical(connection.execute(query).fetchall())


def query_plan(connection: sqlite3.Connection, query: str) -> list[str]:
    return [" | ".join(str(value) for value in row) for row in connection.execute("EXPLAIN QUERY PLAN " + query)]


def time_query(connection: sqlite3.Connection, query: str) -> float:
    started = time.perf_counter_ns()
    connection.execute(query).fetchall()
    return (time.perf_counter_ns() - started) / 1_000_000


def benchmark_dashboards(connection: sqlite3.Connection, trials: int = 7) -> dict[str, Any]:
    normalized_rows = dashboard_rows(connection, NORMALIZED_QUERY)
    denormalized_rows = dashboard_rows(connection, DENORMALIZED_QUERY)
    if normalized_rows != denormalized_rows:
        raise RuntimeError("normalized and denormalized dashboard results differ")

    connection.execute(NORMALIZED_QUERY).fetchall()
    connection.execute(DENORMALIZED_QUERY).fetchall()
    normalized_samples: list[float] = []
    denormalized_samples: list[float] = []
    for trial in range(trials):
        order = (
            (("normalized", NORMALIZED_QUERY), ("denormalized", DENORMALIZED_QUERY))
            if trial % 2 == 0
            else (("denormalized", DENORMALIZED_QUERY), ("normalized", NORMALIZED_QUERY))
        )
        for label, query in order:
            sample = time_query(connection, query)
            (normalized_samples if label == "normalized" else denormalized_samples).append(sample)

    normalized_median = statistics.median(normalized_samples)
    denormalized_median = statistics.median(denormalized_samples)
    return {
        "result_groups": len(normalized_rows),
        "equivalent": True,
        "normalized_samples_ms": normalized_samples,
        "denormalized_samples_ms": denormalized_samples,
        "normalized_median_ms": normalized_median,
        "denormalized_median_ms": denormalized_median,
        "denormalized_speedup_ratio": normalized_median / denormalized_median,
        "normalized_plan": query_plan(connection, NORMALIZED_QUERY),
        "denormalized_indexed_plan": query_plan(connection, DENORMALIZED_QUERY),
    }


def timed_update(
    connection: sqlite3.Connection,
    table: str,
    trials: int = 7,
) -> dict[str, Any]:
    if table not in {"machine", "report_jobpart"}:
        raise ValueError("unsupported update table")
    before = connection.execute(
        f"SELECT COUNT(*), COUNT(DISTINCT site), MIN(site), MAX(site) FROM {table} WHERE machine_id='cnc-02'"
    ).fetchone()
    samples: list[float] = []
    affected: list[int] = []
    after: tuple[Any, ...] | None = None
    for _ in range(trials):
        connection.execute("BEGIN")
        started = time.perf_counter_ns()
        cursor = connection.execute(
            f"UPDATE {table} SET site='Bielefeld' WHERE machine_id='cnc-02'"
        )
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
        affected.append(cursor.rowcount)
        after = connection.execute(
            f"SELECT COUNT(*), COUNT(DISTINCT site), MIN(site), MAX(site) FROM {table} WHERE machine_id='cnc-02'"
        ).fetchone()
        connection.rollback()
        restored = connection.execute(
            f"SELECT COUNT(*), COUNT(DISTINCT site), MIN(site), MAX(site) FROM {table} WHERE machine_id='cnc-02'"
        ).fetchone()
        if restored != before:
            raise RuntimeError(f"{table} update rollback did not restore the data")
    if len(set(affected)) != 1:
        raise RuntimeError(f"inconsistent row counts for {table} update")
    return {
        "table": table,
        "before": list(before),
        "after_during_transaction": list(after or ()),
        "affected_rows": affected[0],
        "samples_ms": samples,
        "median_ms": statistics.median(samples),
        "rollback_verified": True,
    }


def storage_bytes(connection: sqlite3.Connection) -> dict[str, Any]:
    try:
        table_only = {
            "normalized": connection.execute(
                "SELECT COALESCE(SUM(pgsize),0) FROM dbstat "
                "WHERE name IN ('machine','part','job','job_part')"
            ).fetchone()[0],
            "denormalized": connection.execute(
                "SELECT COALESCE(SUM(pgsize),0) FROM dbstat WHERE name='report_jobpart'"
            ).fetchone()[0],
        }
        index_inclusive = {
            "normalized": connection.execute(
                "SELECT COALESCE(SUM(pgsize),0) FROM dbstat WHERE name IN "
                "('machine','part','job','job_part','sqlite_autoindex_machine_1',"
                "'sqlite_autoindex_part_1','sqlite_autoindex_job_part_1')"
            ).fetchone()[0],
            "denormalized": connection.execute(
                "SELECT COALESCE(SUM(pgsize),0) FROM dbstat "
                "WHERE name IN ('report_jobpart','ix_report_machine')"
            ).fetchone()[0],
        }
    except sqlite3.Error as exc:
        return {"available": False, "error": str(exc)}
    return {
        "available": True,
        "page_size": connection.execute("PRAGMA page_size").fetchone()[0],
        "table_only_bytes": table_only,
        "index_inclusive_bytes": index_inclusive,
    }


def set_report_index(connection: sqlite3.Connection, enabled: bool) -> None:
    if enabled:
        connection.execute(
            "CREATE INDEX IF NOT EXISTS ix_report_machine ON report_jobpart(machine_id)"
        )
    else:
        connection.execute("DROP INDEX IF EXISTS ix_report_machine")
    connection.commit()


def benchmark_report_index(connection: sqlite3.Connection, trials: int = 7) -> dict[str, Any]:
    samples = {"indexed": [], "unindexed": []}
    plans: dict[str, list[str]] = {}
    expected_rows = dashboard_rows(connection, DENORMALIZED_QUERY)
    try:
        for trial in range(trials):
            order = (True, False) if trial % 2 == 0 else (False, True)
            for enabled in order:
                set_report_index(connection, enabled)
                label = "indexed" if enabled else "unindexed"
                if dashboard_rows(connection, DENORMALIZED_QUERY) != expected_rows:
                    raise RuntimeError(f"{label} report-index result changed")
                samples[label].append(time_query(connection, DENORMALIZED_QUERY))
                plans[label] = query_plan(connection, DENORMALIZED_QUERY)
    finally:
        set_report_index(connection, True)
    indexed_median = statistics.median(samples["indexed"])
    unindexed_median = statistics.median(samples["unindexed"])
    return {
        "indexed_samples_ms": samples["indexed"],
        "unindexed_samples_ms": samples["unindexed"],
        "indexed_median_ms": indexed_median,
        "unindexed_median_ms": unindexed_median,
        "unindexed_vs_indexed_ratio": unindexed_median / indexed_median,
        "indexed_plan": plans["indexed"],
        "unindexed_plan": plans["unindexed"],
        "index_restored": True,
    }


def anomaly_results() -> dict[str, Any]:
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE flat5(job_id INTEGER,machine_id TEXT,site TEXT,
          technician TEXT,part_no TEXT,part_price REAL);
        INSERT INTO flat5 VALUES
          (1,'cnc-01','Gütersloh','tech-0','P-0001',6.00),
          (1,'cnc-01','Gütersloh','tech-0','P-0002',7.00),
          (2,'cnc-02','Gütersloh','tech-1','P-0001',6.00),
          (2,'cnc-02','Gütersloh','tech-1','P-0003',8.50),
          (3,'cnc-01','Gütersloh','tech-0','P-0003',8.50);
        CREATE TABLE machine(machine_id TEXT PRIMARY KEY,site TEXT NOT NULL);
        CREATE TABLE part(part_no TEXT PRIMARY KEY,part_price REAL NOT NULL);
        INSERT INTO machine VALUES('cnc-01','Gütersloh'),('cnc-02','Gütersloh');
        INSERT INTO part VALUES('P-0001',6.00),('P-0002',7.00),('P-0003',8.50);
        """
    )
    original_cnc01 = connection.execute(
        "SELECT COUNT(*) FROM flat5 WHERE machine_id='cnc-01'"
    ).fetchone()[0]
    partial = connection.execute(
        "UPDATE flat5 SET site='Bielefeld' WHERE job_id=1 AND part_no='P-0001'"
    ).rowcount
    inconsistent = connection.execute(
        "SELECT site,COUNT(*) FROM flat5 WHERE machine_id='cnc-01' GROUP BY site ORDER BY site"
    ).fetchall()
    corrected = connection.execute(
        "UPDATE flat5 SET site='Bielefeld' WHERE machine_id='cnc-01'"
    ).rowcount
    normalized_update = connection.execute(
        "UPDATE machine SET site='Bielefeld' WHERE machine_id='cnc-01'"
    ).rowcount

    flat_insert = connection.execute(
        "INSERT INTO flat5(job_id,machine_id,site,technician,part_no,part_price) "
        "VALUES(NULL,NULL,NULL,NULL,'P-0099',12.50)"
    ).rowcount
    normalized_insert = connection.execute(
        "INSERT INTO part VALUES('P-0099',12.50)"
    ).rowcount
    null_job_fields = connection.execute(
        "SELECT COUNT(*) FROM flat5 WHERE part_no='P-0099' "
        "AND job_id IS NULL AND machine_id IS NULL AND technician IS NULL"
    ).fetchone()[0]

    before_delete = connection.execute(
        "SELECT COUNT(*),MIN(part_price),MAX(part_price) FROM flat5 WHERE part_no='P-0002'"
    ).fetchone()
    deleted = connection.execute("DELETE FROM flat5 WHERE part_no='P-0002'").rowcount
    after_delete = connection.execute(
        "SELECT COUNT(*) FROM flat5 WHERE part_no='P-0002'"
    ).fetchone()[0]
    normalized_part_remains = connection.execute(
        "SELECT COUNT(*),part_price FROM part WHERE part_no='P-0002'"
    ).fetchone()
    connection.close()
    return {
        "update": {
            "original_cnc01_rows": original_cnc01,
            "partial_rows_changed": partial,
            "inconsistent_sites": [list(row) for row in inconsistent],
            "correction_rows_changed": corrected,
            "normalized_rows_changed": normalized_update,
        },
        "insert": {
            "flat_rows_inserted": flat_insert,
            "placeholder_has_null_job_fields": null_job_fields == 1,
            "normalized_part_rows_inserted": normalized_insert,
        },
        "delete": {
            "flat_before": list(before_delete),
            "flat_rows_deleted": deleted,
            "flat_after_count": after_delete,
            "normalized_part": list(normalized_part_remains),
        },
    }


def run_full(connection: sqlite3.Connection, trials: int = 7) -> dict[str, Any]:
    counts = table_counts(connection)
    flat_join_mismatches = connection.execute(
        """
        SELECT COUNT(*) FROM (
          SELECT f.job_id,f.machine_id,f.site,f.technician,f.part_no,
                 CAST(f.part_price AS REAL) AS part_price,f.done_on
          FROM flat_jobpart AS f
          EXCEPT
          SELECT j.job_id,m.machine_id,m.site,j.technician,jp.part_no,p.part_price,j.done_on
          FROM job AS j JOIN machine AS m ON m.machine_id=j.machine_id
          JOIN job_part AS jp ON jp.job_id=j.job_id
          JOIN part AS p ON p.part_no=jp.part_no
        )
        """
    ).fetchone()[0]
    reverse_mismatches = connection.execute(
        """
        SELECT COUNT(*) FROM (
          SELECT j.job_id,m.machine_id,m.site,j.technician,jp.part_no,p.part_price,j.done_on
          FROM job AS j JOIN machine AS m ON m.machine_id=j.machine_id
          JOIN job_part AS jp ON jp.job_id=j.job_id
          JOIN part AS p ON p.part_no=jp.part_no
          EXCEPT
          SELECT f.job_id,f.machine_id,f.site,f.technician,f.part_no,
                 CAST(f.part_price AS REAL),f.done_on FROM flat_jobpart AS f
        )
        """
    ).fetchone()[0]
    environment = {
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
        "platform": platform.platform(),
        "trials": trials,
    }
    return {
        "environment": environment,
        "counts": counts,
        "foreign_key_check": connection.execute("PRAGMA foreign_key_check").fetchall(),
        "integrity_check": connection.execute("PRAGMA integrity_check").fetchone()[0],
        "flat_minus_join": flat_join_mismatches,
        "join_minus_flat": reverse_mismatches,
        "round4": benchmark_dashboards(connection, trials),
        "round5": {
            "normalized_update": timed_update(connection, "machine", trials),
            "denormalized_update": timed_update(connection, "report_jobpart", trials),
            "storage": storage_bytes(connection),
            "index_experiment": benchmark_report_index(connection, trials),
        },
    }


def json_text(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)
