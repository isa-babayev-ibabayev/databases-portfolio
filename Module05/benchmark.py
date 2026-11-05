"""Run the full Module 5 benchmark on a disposable SQLite database."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from experiment import build_database, json_text, run_full


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--trials", type=int, default=7)
    result.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return result


def main() -> int:
    args = parser().parse_args()
    if args.trials < 5:
        raise SystemExit("--trials must be at least 5")
    with tempfile.TemporaryDirectory(prefix="module05-benchmark-") as temporary:
        database = Path(temporary) / "normalize.db"
        connection = build_database(database)
        try:
            result = run_full(connection, args.trials)
        finally:
            connection.close()
    if database.exists():
        raise RuntimeError("temporary benchmark database was not removed")
    if args.json:
        print(json_text(result))
        return 0
    r4 = result["round4"]
    r5 = result["round5"]
    print("Module 5 benchmark")
    print(f"Python: {result['environment']['python']}")
    print(f"SQLite: {result['environment']['sqlite']}")
    print(f"Counts: {result['counts']}")
    print(f"Dashboard equivalent: {r4['equivalent']} ({r4['result_groups']} groups)")
    print(f"Normalized median: {r4['normalized_median_ms']:.3f} ms")
    print(f"Denormalized median: {r4['denormalized_median_ms']:.3f} ms")
    print(f"Denormalized speedup: {r4['denormalized_speedup_ratio']:.3f}x")
    print(f"Normalized update: {r5['normalized_update']['affected_rows']} row, "
          f"{r5['normalized_update']['median_ms']:.3f} ms median")
    print(f"Denormalized update: {r5['denormalized_update']['affected_rows']} rows, "
          f"{r5['denormalized_update']['median_ms']:.3f} ms median")
    storage = r5["storage"]
    if storage["available"]:
        print(f"Normalized table storage: {storage['table_only_bytes']['normalized'] / 1024:.1f} KB")
        print(f"Denormalized table storage: {storage['table_only_bytes']['denormalized'] / 1024:.1f} KB")
    else:
        print(f"dbstat unavailable: {storage['error']}")
    index = r5["index_experiment"]
    print(f"Report indexed median: {index['indexed_median_ms']:.3f} ms")
    print(f"Report unindexed median: {index['unindexed_median_ms']:.3f} ms")
    print("Temporary database removed: yes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
