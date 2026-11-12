"""Benchmark the official aggregates fairly in SQLite and DuckDB."""

from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import statistics
import time
from pathlib import Path
from typing import Any, Callable

import duckdb


HERE = Path(__file__).resolve().parent
HISTORY = HERE / "history.db"
PARQUET = HERE / "report_history.parquet"

DASHBOARD = """SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM {src} WHERE done_on >= '2026-01-01'
GROUP BY machine_id, site, technician"""

MONTHLY_DUCKDB = """SELECT strftime(done_on, '%Y-%m') AS month, machine_id,
COUNT(*) AS jobs, SUM(part_price) AS cost
FROM {src} GROUP BY month, machine_id ORDER BY month, machine_id"""

# SQLite and DuckDB accept the strftime arguments in opposite orders.  The
# workbook's shared SQL uses DuckDB's order; using it unchanged in SQLite
# silently returns NULL months and therefore does not compare the same result.
MONTHLY_SQLITE = """SELECT strftime('%Y-%m', done_on) AS month, machine_id,
COUNT(*) AS jobs, SUM(part_price) AS cost
FROM {src} GROUP BY month, machine_id ORDER BY month, machine_id"""


def sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def canonical(rows: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    normalized = [
        tuple(round(value, 6) if isinstance(value, float) else value for value in row)
        for row in rows
    ]
    return sorted(normalized, key=repr)


def timed_ms(call: Callable[[], list[tuple[Any, ...]]]) -> tuple[float, list[tuple[Any, ...]]]:
    started = time.perf_counter()
    rows = call()
    return (time.perf_counter() - started) * 1000, rows


def benchmark(runs: int = 5) -> dict[str, Any]:
    if runs < 3 or runs % 2 == 0:
        raise ValueError("runs must be an odd number of at least 3")
    if not HISTORY.exists() or not PARQUET.exists():
        raise FileNotFoundError("run prepare.py and to_parquet.py first")
    sqlite_connection = sqlite3.connect(
        f"file:{HISTORY.resolve().as_posix()}?mode=ro&immutable=1", uri=True
    )
    duck_connection = duckdb.connect()
    parquet_source = f"read_parquet('{sql_path(PARQUET)}')"
    results: dict[str, Any] = {}
    try:
        workloads = (
            ("dashboard", DASHBOARD, DASHBOARD),
            ("monthly", MONTHLY_SQLITE, MONTHLY_DUCKDB),
        )
        for name, sqlite_template, duck_template in workloads:
            sqlite_sql = sqlite_template.format(src="report_history")
            duck_sql = duck_template.format(src=parquet_source)
            run_sqlite = lambda sql=sqlite_sql: sqlite_connection.execute(sql).fetchall()
            run_duckdb = lambda sql=duck_sql: duck_connection.execute(sql).fetchall()
            sqlite_expected = canonical(run_sqlite())
            duck_expected = canonical(run_duckdb())
            if sqlite_expected != duck_expected:
                raise RuntimeError(f"{name} outputs differ")
            sqlite_times: list[float] = []
            duck_times: list[float] = []
            order: list[list[str]] = []
            for trial in range(runs):
                sequence = (
                    (("sqlite", run_sqlite), ("duckdb", run_duckdb))
                    if trial % 2 == 0
                    else (("duckdb", run_duckdb), ("sqlite", run_sqlite))
                )
                order.append([item[0] for item in sequence])
                for engine, call in sequence:
                    elapsed, rows = timed_ms(call)
                    if canonical(rows) != sqlite_expected:
                        raise RuntimeError(f"{name} changed during {engine} timing")
                    (sqlite_times if engine == "sqlite" else duck_times).append(elapsed)
            sqlite_median = statistics.median(sqlite_times)
            duck_median = statistics.median(duck_times)
            results[name] = {
                "result_groups": len(sqlite_expected),
                "equivalent": True,
                "warmups_discarded": 2,
                "execution_order": order,
                "sqlite_samples_ms": sqlite_times,
                "duckdb_samples_ms": duck_times,
                "sqlite_median_ms": sqlite_median,
                "duckdb_median_ms": duck_median,
                "speedup_sqlite_over_duckdb": sqlite_median / duck_median,
                "sqlite_spread_ms": [min(sqlite_times), max(sqlite_times)],
                "duckdb_spread_ms": [min(duck_times), max(duck_times)],
            }
    finally:
        sqlite_connection.close()
        duck_connection.close()
    return {
        "environment": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "duckdb": duckdb.__version__,
            "platform": platform.platform(),
            "runs": runs,
        },
        "workloads": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = benchmark(args.runs)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    for name, data in result["workloads"].items():
        print(
            f"{name:10s} sqlite {data['sqlite_median_ms']:8.2f} ms "
            f"[{data['sqlite_spread_ms'][0]:.2f}-{data['sqlite_spread_ms'][1]:.2f}] "
            f"duckdb {data['duckdb_median_ms']:8.2f} ms "
            f"[{data['duckdb_spread_ms'][0]:.2f}-{data['duckdb_spread_ms'][1]:.2f}] "
            f"speedup {data['speedup_sqlite_over_duckdb']:.2f}x"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
