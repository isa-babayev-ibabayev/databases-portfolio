"""Windows-friendly live demonstration for Module 5."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Any

from experiment import anomaly_results, build_database, run_full


def print_plan(title: str, rows: list[str]) -> None:
    print(title)
    for row in rows:
        print(f"  {row}")


def print_round2() -> None:
    result = anomaly_results()
    print("\n=== Round 2 — Break it ===")
    update = result["update"]
    print(f"cnc-01 rows in flat table: {update['original_cnc01_rows']}")
    print(f"Intentional partial update changed: {update['partial_rows_changed']} row")
    print(f"Inconsistent sites: {update['inconsistent_sites']}")
    print(f"Correction changed all cnc-01 rows: {update['correction_rows_changed']}")
    print(f"Normalized machine update changed: {update['normalized_rows_changed']} row")
    insert = result["insert"]
    print(f"Flat standalone-part placeholder inserted: {insert['flat_rows_inserted']} row")
    print(f"Placeholder needs NULL job fields: {insert['placeholder_has_null_job_fields']}")
    print(f"Normalized part inserted cleanly: {insert['normalized_part_rows_inserted']} row")
    delete = result["delete"]
    print(f"P-0002 flat rows before delete: {delete['flat_before'][0]}")
    print(f"P-0002 flat rows after delete: {delete['flat_after_count']}")
    print(f"Normalized part still present: {delete['normalized_part']}")


def print_round3(result: dict[str, Any]) -> None:
    print("\n=== Round 3 — Build it ===")
    for name, count in result["counts"].items():
        print(f"{name}: {count:,}")
    print(f"flat EXCEPT normalized join: {result['flat_minus_join']}")
    print(f"normalized join EXCEPT flat: {result['join_minus_flat']}")
    print(f"foreign_key_check: {result['foreign_key_check']}")
    print(f"integrity_check: {result['integrity_check']}")
    print("Why part has 10 rows: k runs from 1 through 10, so (k % 40) + 1")
    print("produces only 2 through 11, not all forty possible values.")


def print_round4(result: dict[str, Any]) -> None:
    round4 = result["round4"]
    print("\n=== Round 4 — Race it ===")
    print(f"Equivalent dashboard output: {round4['equivalent']}")
    print(f"Result groups: {round4['result_groups']}")
    print("Normalized raw timings (ms): " + ", ".join(f"{x:.3f}" for x in round4["normalized_samples_ms"]))
    print("Denormalized raw timings (ms): " + ", ".join(f"{x:.3f}" for x in round4["denormalized_samples_ms"]))
    print(f"Normalized median: {round4['normalized_median_ms']:.3f} ms")
    print(f"Denormalized median: {round4['denormalized_median_ms']:.3f} ms")
    print(f"Denormalized speedup: {round4['denormalized_speedup_ratio']:.3f}x")
    print_plan("Normalized query plan:", round4["normalized_plan"])
    print_plan("Denormalized plan with machine index:", round4["denormalized_indexed_plan"])


def print_round5(result: dict[str, Any]) -> None:
    round4 = result["round4"]
    round5 = result["round5"]
    normalized = round5["normalized_update"]
    denormalized = round5["denormalized_update"]
    storage = round5["storage"]
    index = round5["index_experiment"]
    print("\n=== Round 5 — Price it ===")
    print("\n0. Database and equivalent dashboard context")
    for name, count in result["counts"].items():
        print(f"{name}: {count:,}")
    print(f"Equivalent dashboard output: {round4['equivalent']} ({round4['result_groups']} groups)")
    print(f"Normalized dashboard median: {round4['normalized_median_ms']:.3f} ms")
    print(f"Indexed report dashboard median: {round4['denormalized_median_ms']:.3f} ms")
    print_plan("Normalized dashboard plan:", round4["normalized_plan"])
    print_plan("Indexed report dashboard plan:", round4["denormalized_indexed_plan"])

    print("\n1. Write amplification")
    print(f"Normalized before: {normalized['before']}")
    print(f"Normalized after inside transaction: {normalized['after_during_transaction']}")
    print(f"Normalized affected rows: {normalized['affected_rows']}")
    print("Normalized raw update timings (ms): " + ", ".join(f"{x:.3f}" for x in normalized["samples_ms"]))
    print(f"Normalized update median: {normalized['median_ms']:.3f} ms")
    print(f"Denormalized before: {denormalized['before']}")
    print(f"Denormalized after inside transaction: {denormalized['after_during_transaction']}")
    print(f"Denormalized affected rows: {denormalized['affected_rows']}")
    print("Denormalized raw update timings (ms): " + ", ".join(f"{x:.3f}" for x in denormalized["samples_ms"]))
    print(f"Denormalized update median: {denormalized['median_ms']:.3f} ms")
    print(f"Both update experiments rolled back: {normalized['rollback_verified'] and denormalized['rollback_verified']}")

    print("\n2. Storage from dbstat")
    if storage["available"]:
        for design, value in storage["table_only_bytes"].items():
            print(f"{design} base table bytes: {value} ({value / 1024:.1f} KB)")
        for design, value in storage["index_inclusive_bytes"].items():
            print(f"{design} index-inclusive bytes: {value} ({value / 1024:.1f} KB)")
    else:
        print(f"dbstat unavailable: {storage['error']}")

    print("\n3. Report index experiment")
    print("Indexed raw timings (ms): " + ", ".join(f"{x:.3f}" for x in index["indexed_samples_ms"]))
    print("Unindexed raw timings (ms): " + ", ".join(f"{x:.3f}" for x in index["unindexed_samples_ms"]))
    print(f"Indexed median: {index['indexed_median_ms']:.3f} ms")
    print(f"Unindexed median: {index['unindexed_median_ms']:.3f} ms")
    print(f"Unindexed/indexed ratio: {index['unindexed_vs_indexed_ratio']:.3f}x")
    print_plan("Indexed plan:", index["indexed_plan"])
    print_plan("Unindexed plan:", index["unindexed_plan"])
    print(f"Machine index restored after experiment: {index['index_restored']}")

    print("\nInterpretation")
    print("The normalized update changes one authoritative machine row.")
    print("The report repeats that site on 4,000 rows, so one fact costs 4,000 writes.")
    print("The dashboard timings and index result are measurements, not assumptions.")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--round", choices=("2", "3", "4", "5", "all"), default="all")
    result.add_argument("--trials", type=int, default=7)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.trials < 5:
        raise SystemExit("--trials must be at least 5")
    if args.round in {"2", "all"}:
        print_round2()
    if args.round == "2":
        return 0
    with tempfile.TemporaryDirectory(prefix="module05-demo-") as temporary:
        database = Path(temporary) / "normalize.db"
        connection = build_database(database)
        try:
            result = run_full(connection, args.trials)
        finally:
            connection.close()
    if database.exists():
        raise RuntimeError("temporary demonstration database was not removed")
    print("\n=== Environment ===")
    for key, value in result["environment"].items():
        print(f"{key}: {value}")
    print(f"Disposable database: {database}")
    print("Disposable database removed: yes")
    if args.round in {"3", "all"}:
        print_round3(result)
    if args.round in {"4", "all"}:
        print_round4(result)
    if args.round in {"5", "all"}:
        print_round5(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
