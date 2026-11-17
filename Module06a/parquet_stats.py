"""Compare date row-group statistics and selective scans before/after sorting."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

import duckdb


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "report_history.parquet"
SORTED = HERE / "sorted.parquet"
FILTER_START = "2027-01-01"
FILTER_END = "2027-02-01"


def sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def summary(connection: duckdb.DuckDBPyConnection, path: Path) -> tuple[Any, ...]:
    return connection.execute(
        f"SELECT COUNT(*), ROUND(SUM(part_price),2), SUM(job_id), "
        f"MIN(done_on), MAX(done_on) FROM read_parquet('{sql_path(path)}')"
    ).fetchone()


def metadata(
    connection: duckdb.DuckDBPyConnection, path: Path, limit: int | None = None
) -> list[tuple[Any, ...]]:
    sql = (
        "SELECT row_group_id, stats_min, stats_max, row_group_num_rows "
        f"FROM parquet_metadata('{sql_path(path)}') "
        "WHERE path_in_schema = 'done_on' ORDER BY row_group_id"
    )
    if limit is not None:
        sql += f" LIMIT {int(limit)}"
    return connection.execute(sql).fetchall()


def candidate_groups(rows: list[tuple[Any, ...]]) -> int:
    return sum(
        1
        for _, minimum, maximum, _ in rows
        if maximum >= FILTER_START and minimum < FILTER_END
    )


def is_clustered(rows: list[tuple[Any, ...]]) -> bool:
    minimums = [row[1] for row in rows]
    maximums = [row[2] for row in rows]
    return (
        minimums == sorted(minimums)
        and maximums == sorted(maximums)
        and len({(row[1], row[2]) for row in rows}) > 1
    )


def build_sorted(
    connection: duckdb.DuckDBPyConnection, source: Path, target: Path
) -> None:
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{target.stem}.build-",
        suffix=".parquet",
        dir=target.parent,
        delete=False,
    )
    temporary = Path(handle.name)
    handle.close()
    temporary.unlink()
    try:
        connection.execute(
            f"COPY (SELECT * FROM read_parquet('{sql_path(source)}') "
            f"ORDER BY done_on) TO '{sql_path(temporary)}' (FORMAT parquet)"
        )
        if summary(connection, temporary) != summary(connection, source):
            raise RuntimeError("sorted Parquet does not match the source summary")
        if not is_clustered(metadata(connection, temporary)):
            raise RuntimeError("sorted Parquet does not have clustered date statistics")
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def selective_sql(path: Path) -> str:
    return (
        "SELECT COUNT(*), ROUND(SUM(part_price),2) "
        f"FROM read_parquet('{sql_path(path)}') "
        f"WHERE done_on >= DATE '{FILTER_START}' AND done_on < DATE '{FILTER_END}'"
    )


def interleaved_samples(
    connection: duckdb.DuckDBPyConnection, runs: int
) -> tuple[list[float], list[float], tuple[Any, ...], list[list[str]]]:
    sql = {"unsorted": selective_sql(SOURCE), "sorted": selective_sql(SORTED)}
    expected = connection.execute(sql["unsorted"]).fetchone()
    if connection.execute(sql["sorted"]).fetchone() != expected:
        raise RuntimeError("sorted and unsorted selective results differ")
    samples: dict[str, list[float]] = {"unsorted": [], "sorted": []}
    order: list[list[str]] = []
    for trial in range(runs):
        sequence = (
            ("unsorted", "sorted") if trial % 2 == 0 else ("sorted", "unsorted")
        )
        order.append(list(sequence))
        for name in sequence:
            started = time.perf_counter()
            result = connection.execute(sql[name]).fetchone()
            samples[name].append((time.perf_counter() - started) * 1000)
            if result != expected:
                raise RuntimeError("selective query result changed during timing")
    return samples["unsorted"], samples["sorted"], expected, order


def experiment(runs: int = 5, rebuild: bool = False) -> dict[str, Any]:
    if not SOURCE.exists():
        raise FileNotFoundError("run Module06a/to_parquet.py first")
    if runs < 3 or runs % 2 == 0:
        raise ValueError("runs must be an odd number of at least 3")
    connection = duckdb.connect()
    try:
        if SORTED.exists() and not rebuild:
            reusable = (
                summary(connection, SORTED) == summary(connection, SOURCE)
                and is_clustered(metadata(connection, SORTED))
            )
        else:
            reusable = False
        if not reusable:
            build_sorted(connection, SOURCE, SORTED)
            action = "built and atomically installed"
        else:
            action = "reused validated existing file"

        source_metadata = metadata(connection, SOURCE)
        sorted_metadata = metadata(connection, SORTED)
        source_times, sorted_times, source_result, order = interleaved_samples(
            connection, runs
        )
    finally:
        connection.close()
    return {
        "action": action,
        "filter": f"{FILTER_START} <= done_on < {FILTER_END}",
        "query_result": {
            "rows": source_result[0],
            "sum_part_price": float(source_result[1]),
        },
        "warmups_discarded": 2,
        "execution_order": order,
        "unsorted": {
            "bytes": SOURCE.stat().st_size,
            "row_groups": len(source_metadata),
            "candidate_row_groups": candidate_groups(source_metadata),
            "first_five_date_statistics": [list(row) for row in source_metadata[:5]],
            "samples_ms": source_times,
            "median_ms": statistics.median(source_times),
        },
        "sorted": {
            "bytes": SORTED.stat().st_size,
            "row_groups": len(sorted_metadata),
            "candidate_row_groups": candidate_groups(sorted_metadata),
            "first_five_date_statistics": [list(row) for row in sorted_metadata[:5]],
            "samples_ms": sorted_times,
            "median_ms": statistics.median(sorted_times),
        },
        "equivalent": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    print(json.dumps(experiment(args.runs, args.rebuild), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
