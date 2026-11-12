"""Measure the official 1,000-row insert and point-lookup workload boundary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import time
from typing import Any

import duckdb


N = 1_000
EXPECTED_SUM = sum(index * 1.5 for index in range(N))


def sqlite_once() -> dict[str, float]:
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE s(id INTEGER PRIMARY KEY, k TEXT, v REAL)")
        started = time.perf_counter()
        for index in range(N):
            connection.execute(
                "INSERT INTO s VALUES (?, ?, ?)", (index, f"k{index}", index * 1.5)
            )
        connection.commit()
        insert = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        values = [
            connection.execute("SELECT v FROM s WHERE id = ?", (index,)).fetchone()[0]
            for index in range(N)
        ]
        lookup = (time.perf_counter() - started) * 1000
    finally:
        connection.close()
    if abs(sum(values) - EXPECTED_SUM) > 1e-9:
        raise RuntimeError("SQLite lookup result mismatch")
    return {"insert_ms": insert, "lookup_ms": lookup}


def duckdb_once(*, batched: bool = False) -> dict[str, float]:
    connection = duckdb.connect()
    try:
        connection.execute("CREATE TABLE s(id INTEGER PRIMARY KEY, k TEXT, v DOUBLE)")
        rows = [(index, f"k{index}", index * 1.5) for index in range(N)]
        started = time.perf_counter()
        if batched:
            connection.executemany("INSERT INTO s VALUES (?, ?, ?)", rows)
        else:
            for row in rows:
                connection.execute("INSERT INTO s VALUES (?, ?, ?)", row)
        insert = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        values = [
            connection.execute("SELECT v FROM s WHERE id = ?", (index,)).fetchone()[0]
            for index in range(N)
        ]
        lookup = (time.perf_counter() - started) * 1000
    finally:
        connection.close()
    if abs(sum(values) - EXPECTED_SUM) > 1e-9:
        raise RuntimeError("DuckDB lookup result mismatch")
    return {"insert_ms": insert, "lookup_ms": lookup}


def benchmark(runs: int = 5) -> dict[str, Any]:
    if runs < 3 or runs % 2 == 0:
        raise ValueError("runs must be an odd number of at least 3")
    samples = {
        "sqlite": {"insert_ms": [], "lookup_ms": []},
        "duckdb": {"insert_ms": [], "lookup_ms": []},
        "duckdb_executemany": {"insert_ms": [], "lookup_ms": []},
    }
    order: list[list[str]] = []
    for trial in range(runs):
        sequence = (
            (("sqlite", sqlite_once), ("duckdb", duckdb_once))
            if trial % 2 == 0
            else (("duckdb", duckdb_once), ("sqlite", sqlite_once))
        )
        order.append([item[0] for item in sequence])
        for name, call in sequence:
            result = call()
            for metric, value in result.items():
                samples[name][metric].append(value)
        batched = duckdb_once(batched=True)
        for metric, value in batched.items():
            samples["duckdb_executemany"][metric].append(value)

    medians = {
        engine: {metric: statistics.median(values) for metric, values in metrics.items()}
        for engine, metrics in samples.items()
    }
    return {
        "statements": N,
        "runs": runs,
        "execution_order": order,
        "samples": samples,
        "medians": medians,
        "duckdb_vs_sqlite_insert_slowdown": medians["duckdb"]["insert_ms"]
        / medians["sqlite"]["insert_ms"],
        "duckdb_vs_sqlite_lookup_slowdown": medians["duckdb"]["lookup_ms"]
        / medians["sqlite"]["lookup_ms"],
        "duckdb_batch_insert_improvement": medians["duckdb"]["insert_ms"]
        / medians["duckdb_executemany"]["insert_ms"],
        "results_verified": True,
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
    for engine, metrics in result["medians"].items():
        print(
            f"{engine:20s} inserts {metrics['insert_ms']:9.2f} ms | "
            f"lookups {metrics['lookup_ms']:9.2f} ms"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
