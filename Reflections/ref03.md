# Reflection 03 — Checking SQL instead of only running it

## Take-away

In this module, I learned how SQL, relational algebra, and query plans describe
different parts of the same database work. I also learned that a query that
runs is not automatically correct or efficient. I need to check the result and
the plan before deciding that an index helps.

## What was good?

I enjoyed working with Sanjay, Sebastian, and Myo in the classroom. We divided
the topics and then shared what we learned. My topic was relational algebra.
Comparing a real SQL query with a selection expression made the algebra easier
for me to understand.

## What was difficult?

At first, some query-plan results were confusing because one query used an
index while another query scanned the table. I also had to understand when a
projection operator was needed. For `SELECT *`, a separate projection is not
necessary because the query keeps all columns.

## Exploration and show stoppers

The most interesting experiment was the benchmark. The dashboard baseline
median was about 160.88 ms, but the index-driven stage had a median of about
1429.52 ms. In contrast, the date index made a one-day lookup about 12.9 times
faster, and the product index made its direct filter about 4.9 times faster in
the recorded environment. This taught me that an index can help one query and
be ignored or harmful for another query. I also explored leading wildcards,
function-wrapped columns, and covering indexes.

I also checked a SQLite-specific detail from the shared clause-order notes.
SQLite accepted a `SELECT` alias in `WHERE` for the tested query, although this
is not portable SQL. I kept the normal column name in the final example instead
of repeating the claim that SQLite rejects it.

I also used a disposable curiosity experiment with 1,000 rows. The
technician equality query changed from `SCAN` to `SEARCH` after its index was
created, while `LIKE '%ei%'` still scanned. This made the difference between
"an index exists" and "this particular predicate can use the index" clearer.

I also wrote a later review of my Plan Safari predictions. I expected all three
queries to scan before the technician index. After the index, I expected only
the technician equality query to change to `SEARCH`. These expectations matched
the saved execution plans. This review was written after the classroom activity,
not preserved from before the original execution.

## Interaction with peers and instructors

During Module 3, I joined Sanjay's pod with Sebastian and Myo as a guest member.
My part was relational algebra. I mapped the Beier technician query to
`σ_{technician='Beier'}(maint_job)` and explained it to the group. We also
compared the expression with Gemini. I participated in the exchange with a
neighboring pod, where we compared Windows and macOS plans and discussed
leading wildcards, functions, and covering indexes. I also posted our question
about SQLite partial searches and index usage in the course Discord server. I
do not claim that the question received an answer.

During this classroom work, we collected three questions: why a leading-
wildcard `LIKE` still scans, why `UPPER()` can prevent use of a normal index,
and why an index stops being covering when another column is needed. I remember
discussing these ideas with the neighboring pod. We exchanged curiosity
questions twice during the class. I wrote down the questions from the first
exchange, but I did not keep a separate list from the second one.

## How did you verify AI suggestions?

I did not accept an AI suggestion only because the SQL executed. I ran the
generated query, compared its result with a Python calculation and an edge-case
fixture, and used `EXPLAIN QUERY PLAN`. Five timing runs showed that one index
suggestion made the query slower. We also compared my algebra expression with
Gemini. I checked the window rewrite for duplicate rows and compared unsafe SQL
string building with bound parameters.

## Help and extra work

Working with the group helped me understand the topics that the other members
studied. I also completed optional Studio Task 5, which compares a grouped
query, a correlated subquery, and a window query. All three returned the same
400 customers, but their plans and timings were different. The extra `HAVING`,
covering-index, and index-curiosity exercises gave me more examples to test.
