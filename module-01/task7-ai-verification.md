# Module 01 - Task 7: AI-Assisted SQL Verification

## 1. Objective

I used ChatGPT to generate a SQLite query, executed it against my CNC telemetry database, inspected the execution plan, and tested the filtering logic.

## 2. Exact AI prompt

Here is my SQLite table:

readings(ts TEXT, machine TEXT, temp_c REAL, vib_rms REAL, spindle_load REAL)

Write a query that returns, for each machine, the average spindle load for readings taken overnight (after 18:00), ordered by average load descending.

## 3. AI-generated SQL

    SELECT
        machine,
        ROUND(AVG(spindle_load), 2) AS avg_spindle_load
    FROM readings
    WHERE time(ts) > '18:00:00'
    GROUP BY machine
    ORDER BY avg_spindle_load DESC;

## 4. Results

I successfully executed the AI-generated query on a database containing 172,800 records.

| Machine | Average spindle load |
|---|---:|
| cnc-03 | 60.43 |
| cnc-01 | 60.37 |
| cnc-02 | 60.36 |

## 5. Execution plan

I used EXPLAIN QUERY PLAN and received:

    SCAN readings
    USE TEMP B-TREE FOR GROUP BY
    USE TEMP B-TREE FOR ORDER BY

SQLite performed a full-table scan and used temporary B-trees for grouping and sorting.

## 6. Verification test

I compared filtering by the time of day against filtering after a fixed date and time.

| Test | Records |
|---|---:|
| Exactly at 18:00 | 6 |
| After 18:00 on each day | 43,194 |
| After 2026-01-05 18:00:00 | 129,597 |

The second filter includes daytime records from subsequent days, so it does not answer the same question.

The strict greater-than comparison also excludes records taken exactly at 18:00.

## 7. AI verification reflection

ChatGPT generated a valid query that calculated the average spindle load for each machine and sorted the results correctly. I verified that the query executed successfully and inspected its execution plan. I also tested a potentially misleading date-time condition, which returned 129,597 records instead of 43,194. This showed me that a query can execute successfully while answering the wrong question. The generated query also interprets "after 18:00" as the period before midnight; a full overnight period extending into the early morning would require different filtering logic.

## 8. Conclusion

I learned to verify AI-generated SQL instead of trusting it immediately. Checking execution results, query plans, and boundary conditions helps identify possible errors.

## Evidence

- [AI query](task7-ai-query.sql)
- [Query results](task7-results.txt)
- [Execution plan](task7-plan.txt)
- [Boundary test](task7-boundary-test.txt)
