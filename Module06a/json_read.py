"""Create UTF-8 device metadata and join it to Parquet with DuckDB."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb


HERE = Path(__file__).resolve().parent
DEVICES = HERE / "devices.json"
PARQUET = HERE / "report_history.parquet"
DEVICE_ROWS = [
    {"machine_id": "cnc-01", "vendor": "Siemens", "firmware": "4.2"},
    {"machine_id": "cnc-02", "vendor": "Fanuc", "firmware": "3.9"},
    {"machine_id": "cnc-03", "vendor": "Siemens", "firmware": "4.0"},
]


def sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def run(devices: Path = DEVICES, parquet: Path = PARQUET) -> dict[str, Any]:
    if not parquet.exists():
        raise FileNotFoundError(f"Parquet snapshot is missing: {parquet}")
    devices.write_text(
        json.dumps(DEVICE_ROWS, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    # Re-read as UTF-8 JSON before DuckDB uses the generated file.
    decoded = json.loads(devices.read_text(encoding="utf-8"))
    if decoded != DEVICE_ROWS:
        raise RuntimeError("generated JSON did not round-trip as UTF-8")

    connection = duckdb.connect()
    try:
        rows = connection.execute(
            f"""SELECT d.vendor, r.machine_id, COUNT(*) AS rows,
                       ROUND(SUM(r.part_price), 2) AS cost
                FROM read_json_auto('{sql_path(devices)}') AS d
                JOIN read_parquet('{sql_path(parquet)}') AS r USING (machine_id)
                GROUP BY d.vendor, r.machine_id
                ORDER BY d.vendor, r.machine_id"""
        ).fetchall()
    finally:
        connection.close()
    if len(rows) != len(DEVICE_ROWS):
        raise RuntimeError(f"expected three joined machines, received {len(rows)}")
    return {
        "json_encoding": "UTF-8",
        "device_rows": len(DEVICE_ROWS),
        "joined_groups": [
            {
                "vendor": row[0],
                "machine_id": row[1],
                "history_rows": row[2],
                "cost": float(row[3]),
            }
            for row in rows
        ],
    }


def main() -> int:
    print(json.dumps(run(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
