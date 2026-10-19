# Module 01 - Task 6: CNC Telemetry Analysis

## Objective

The objective was to generate CNC machine telemetry, load it into SQLite, and answer three practical questions using SQL.

## 1. Dataset

I generated data for three CNC machines over two days, with one measurement per machine every three seconds.

- Total records: 172,800
- Records per machine: 57,600
- CSV file size: 7,776,040 bytes (7.78 MB)
- SQLite database size: 10,526,720 bytes (10.04 MiB)

## 2. Data ingestion

I created two Python scripts:

- generate_telemetry.py generates the CSV dataset.
- load_telemetry.py loads the CSV into SQLite.

The loader uses parameterized SQL with five question-mark placeholders:

INSERT INTO readings VALUES (?, ?, ?, ?, ?)

This separates the SQL statement from the data values.

## 3. SQL query results

### Query 1: Readings per machine

- cnc-01: 57,600
- cnc-02: 57,600
- cnc-03: 57,600

Execution time: 0.271258 seconds.

### Query 2: Maximum vibration

- cnc-01: 2.398 mm/s
- cnc-02: 3.168 mm/s
- cnc-03: 2.550 mm/s

Execution time: 0.261914 seconds.

cnc-02 recorded the highest maximum vibration.

### Query 3: Vibration alarms

A total of 11,714 readings exceeded the 2.0 mm/s vibration threshold.

Execution time: 0.070578 seconds.

## 4. Embedded vs. client/server databases

The SQLite database stores 172,800 measurements in a file of approximately 10.04 MiB. On my computer, the three required queries completed in under 0.3 seconds each.

For this small local monitoring workload, SQLite is a reasonable choice because it runs inside the application without a separate database server.

A client/server database such as PostgreSQL may be more appropriate if many users or applications need network access and concurrent writes.

## 5. Cloud cost and responsibility

Cloud storage for a dataset of this size would be small, but a hosted database could introduce additional costs for database hosting, administration, networking, and maintenance.

The machine-shop company would ultimately pay those operating costs. An exact monetary estimate would require selecting a cloud provider and service configuration.

For the current local monitoring scenario, SQLite avoids the need for a separately hosted database server.

## 6. Verification

I verified that the generated CSV contains 172,800 records and that the SQLite database contains the same number.

I executed all three queries and saved their output and measured execution times in telemetry-query-results.txt.

The database file and generated CSV are excluded from Git because they can be reconstructed using the committed Python scripts.

## Files

- [Telemetry generator](generate_telemetry.py)
- [SQLite loader](load_telemetry.py)
- [SQL queries](telemetry-queries.sql)
- [Query results and timing](telemetry-query-results.txt)
