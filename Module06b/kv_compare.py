"""Compare a simple key-value workload in shelve and SQLite."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shelve
import sqlite3
import statistics
import tempfile
import time
from contextlib import closing
from pathlib import Path
from typing import Any


DEFAULT_N = 20_000
DEFAULT_RUNS = 5


def records(n: int) -> list[tuple[str, str]]:
    return [
        (f"session-{i}", f"user-{i % 100}:filter=city:{i % 4}")
        for i in range(n)
    ]


def digest_values(values: list[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def run_shelve(root: Path, rows: list[tuple[str, str]]) -> dict[str, Any]:
    path = str(root / "sessions")
    with shelve.open(path, flag="n") as db:
        start = time.perf_counter()
        for key, value in rows:
            db[key] = value
        db.sync()
        write_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        values = [db[key] for key, _ in rows]
        lookup_ms = (time.perf_counter() - start) * 1000
        count = len(db)
    return {
        "write_ms": write_ms,
        "lookup_ms": lookup_ms,
        "count": count,
        "digest": digest_values(values),
    }


def run_sqlite(root: Path, rows: list[tuple[str, str]]) -> dict[str, Any]:
    path = root / "sessions.db"
    with closing(sqlite3.connect(path)) as con:
        with con:
            con.execute("CREATE TABLE session(key TEXT PRIMARY KEY, value TEXT NOT NULL) STRICT")
            start = time.perf_counter()
            con.executemany("INSERT INTO session(key, value) VALUES (?, ?)", rows)
            con.commit()
            write_ms = (time.perf_counter() - start) * 1000

            start = time.perf_counter()
            values = [
                con.execute("SELECT value FROM session WHERE key = ?", (key,)).fetchone()[0]
                for key, _ in rows
            ]
            lookup_ms = (time.perf_counter() - start) * 1000
            count = con.execute("SELECT count(*) FROM session").fetchone()[0]
    return {
        "write_ms": write_ms,
        "lookup_ms": lookup_ms,
        "count": count,
        "digest": digest_values(values),
    }


def summarize(samples: list[dict[str, Any]]) -> dict[str, Any]:
    write = [sample["write_ms"] for sample in samples]
    lookup = [sample["lookup_ms"] for sample in samples]
    return {
        "write_samples_ms": write,
        "lookup_samples_ms": lookup,
        "median_write_ms": statistics.median(write),
        "median_lookup_ms": statistics.median(lookup),
        "min_write_ms": min(write),
        "max_write_ms": max(write),
        "min_lookup_ms": min(lookup),
        "max_lookup_ms": max(lookup),
    }


def benchmark(n: int = DEFAULT_N, runs: int = DEFAULT_RUNS) -> dict[str, Any]:
    if n <= 0 or runs <= 0:
        raise ValueError("n and runs must both be positive")
    rows = records(n)
    samples: dict[str, list[dict[str, Any]]] = {"shelve": [], "sqlite": []}
    orders: list[list[str]] = []
    for trial in range(runs):
        order = ["shelve", "sqlite"] if trial % 2 == 0 else ["sqlite", "shelve"]
        orders.append(order)
        for backend in order:
            with tempfile.TemporaryDirectory(prefix=f"module06b-{backend}-") as tmp:
                result = run_shelve(Path(tmp), rows) if backend == "shelve" else run_sqlite(Path(tmp), rows)
            samples[backend].append(result)

    expected_digest = digest_values([value for _, value in rows])
    verified = all(
        sample["count"] == n and sample["digest"] == expected_digest
        for backend_samples in samples.values()
        for sample in backend_samples
    )
    if not verified:
        raise RuntimeError("Benchmark validation failed: counts or value digests differ")

    return {
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "sqlite": sqlite3.sqlite_version,
        },
        "records": n,
        "runs": runs,
        "trial_order": orders,
        "timing_boundary": "open/schema excluded; write includes sync/commit; lookup reads all keys",
        "cache_note": "lookups follow writes and may benefit from operating-system cache",
        "fresh_fixture_each_backend_each_trial": True,
        "expected_digest": expected_digest,
        "verified_equivalent": verified,
        "shelve": {**summarize(samples["shelve"]), "count": n},
        "sqlite": {**summarize(samples["sqlite"]), "count": n},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--json", action="store_true", help="retained for an explicit machine-readable invocation")
    args = parser.parse_args()
    print(json.dumps(benchmark(args.n, args.runs), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
