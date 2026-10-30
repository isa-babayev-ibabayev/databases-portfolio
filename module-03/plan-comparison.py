"""Reproduce Module 3 query plans in a disposable in-memory database.

This is an independent local reproduction, not a neighboring pod's output.
"""

import sqlite3


def main() -> None:
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE maint_job (
            job_id INTEGER PRIMARY KEY,
            technician TEXT NOT NULL,
            notes TEXT NOT NULL
        );
        CREATE TABLE machine (
            machine_id INTEGER PRIMARY KEY,
            machine_name TEXT NOT NULL
        );
        """
    )
    connection.executemany(
        "INSERT INTO maint_job (technician, notes) VALUES (?, ?)",
        [
            (
                "Beier" if i % 13 == 0 else "Meier" if i % 7 == 0 else "Müller",
                f"job {i}",
            )
            for i in range(1000)
        ],
    )
    connection.executemany(
        "INSERT INTO machine (machine_name) VALUES (?)",
        [(f"cnc-{i:02d}",) for i in range(1, 11)],
    )

    queries = [
        (
            "Equality on technician",
            "SELECT * FROM maint_job WHERE technician = 'Beier'",
        ),
        ("Machine name", "SELECT * FROM machine WHERE machine_name = 'cnc-02'"),
        (
            "Leading wildcard",
            "SELECT * FROM maint_job WHERE technician LIKE '%ei%'",
        ),
    ]

    print(
        "Source: independent reproducible local Python sqlite3 test, "
        "not a neighboring pod"
    )
    print("SQLite runtime version:", sqlite3.sqlite_version)
    print("Database: disposable in-memory simulation, NOT the original legacy.db")
    print("Data: 1000 maint_job rows; 10 machine rows")

    title, query = queries[0]
    print("\nBEFORE INDEX:", title)
    print("EXPLAIN QUERY PLAN " + query + ";")
    for row in connection.execute("EXPLAIN QUERY PLAN " + query):
        print(" | ".join(map(str, row)))

    connection.execute("CREATE INDEX ix_job_tech ON maint_job(technician)")
    for title, query in queries:
        print("\nAFTER INDEX:", title)
        print("EXPLAIN QUERY PLAN " + query + ";")
        for row in connection.execute("EXPLAIN QUERY PLAN " + query):
            print(" | ".join(map(str, row)))

    connection.close()


if __name__ == "__main__":
    main()
