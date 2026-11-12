"""Create and validate the core-homework zstd Parquet copy."""

from __future__ import annotations

import json
import os
import statistics
import time
from pathlib import Path

import duckdb


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "report_history.parquet"
ZSTD = HERE / "report_zstd.parquet"


def sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def query_times(connection: duckdb.DuckDBPyConnection, path: Path) -> list[float]:
    query = (
        "SELECT machine_id, site, technician, SUM(part_price) "
        f"FROM read_parquet('{sql_path(path)}') "
        "GROUP BY machine_id, site, technician"
    )
    connection.execute(query).fetchall()
    samples: list[float] = []
    for _ in range(5):
        started = time.perf_counter()
        connection.execute(query).fetchall()
        samples.append((time.perf_counter() - started) * 1000)
    return samples


def main() -> int:
    if not SOURCE.exists():
        raise SystemExit("run Module06a/to_parquet.py first")
    temporary = ZSTD.with_name("report_zstd.new.parquet")
    if temporary.exists():
        raise SystemExit(f"temporary output already exists: {temporary}")
    connection = duckdb.connect()
    try:
        connection.execute(
            f"COPY (SELECT * FROM read_parquet('{sql_path(SOURCE)}')) "
            f"TO '{sql_path(temporary)}' (FORMAT parquet, COMPRESSION zstd)"
        )
        source_summary = connection.execute(
            f"SELECT COUNT(*), ROUND(SUM(part_price),2) FROM read_parquet('{sql_path(SOURCE)}')"
        ).fetchone()
        zstd_summary = connection.execute(
            f"SELECT COUNT(*), ROUND(SUM(part_price),2) FROM read_parquet('{sql_path(temporary)}')"
        ).fetchone()
        if source_summary != zstd_summary:
            raise RuntimeError("zstd copy does not match the source Parquet")
        if ZSTD.exists():
            existing_summary = connection.execute(
                f"SELECT COUNT(*), ROUND(SUM(part_price),2) FROM read_parquet('{sql_path(ZSTD)}')"
            ).fetchone()
            if existing_summary != source_summary:
                raise RuntimeError("existing zstd file contains different data")
        os.replace(temporary, ZSTD)
        source_times = query_times(connection, SOURCE)
        zstd_times = query_times(connection, ZSTD)
    finally:
        connection.close()
        if temporary.exists():
            temporary.unlink()
    result = {
        "rows": source_summary[0],
        "sum_part_price": float(source_summary[1]),
        "source_bytes": SOURCE.stat().st_size,
        "zstd_bytes": ZSTD.stat().st_size,
        "size_ratio_zstd_over_source": ZSTD.stat().st_size / SOURCE.stat().st_size,
        "source_query_samples_ms": source_times,
        "zstd_query_samples_ms": zstd_times,
        "source_query_median_ms": statistics.median(source_times),
        "zstd_query_median_ms": statistics.median(zstd_times),
        "equivalent": True,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
