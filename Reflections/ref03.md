# Reflection 03 — Checking SQL instead of only running it

## Take-away

The most important thing I learned is that SQL and relational algebra describe
the same database operations in different ways. A query that runs is not
automatically correct or efficient. I should check its result, read its query
plan, and measure it before deciding that an index helps.

## What was good?

We divided the classroom topics between the pod members. I worked on
relational algebra, while Sanjay, Sebastian, and Myo shared findings about
query plans, clause order, and tuning and security. Comparing a real SQL query
with a selection expression made the algebra easier to understand.

## What was difficult?

The difficult parts were deciding when a projection operator was needed and
reading the different query-plan lines. For `SELECT *`, a separate projection
is unnecessary because all columns remain. The plans also showed that an index
can be ignored or can even lead to slower work.

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

The portfolio also includes a disposable curiosity experiment with 1,000 rows. The
technician equality query changed from `SCAN` to `SEARCH` after its index was
created, while `LIKE '%ei%'` still scanned. This made the difference between
"an index exists" and "this particular predicate can use the index" clearer.

## Interaction with peers and instructors

During Module 3, I joined the pod with Sanjay, Sebastian, and Myo as a guest
member. My documented part was relational algebra. I mapped the Beier
technician query to `σ_{technician='Beier'}(maint_job)` and we compared it with
Gemini. The pod's shared notes also record an exchange with a neighboring group
about Windows and macOS plans, leading wildcards, functions, and covering
indexes. Those notes support the group event, but they do not independently
show that I stayed for the whole neighboring-pod segment. A second peer swap
and a Discord post are not claimed because there is no evidence for them.

## How did you verify AI suggestions?

AI suggestions were a starting point, not the final proof. The portfolio runs
the generated SQL, compares the result with a Python calculation and an edge
fixture, and checks `EXPLAIN QUERY PLAN`. Five timing runs showed that one index
suggestion made the query slower. We also compared the algebra expression with
Gemini, checked the window rewrite for duplicate rows, and compared unsafe SQL
string building with bound parameters.

## Help and extra work

The optional Studio Task 5 compares a grouped query, a correlated subquery, and
a window query. All three returned the same 400 customers, but their plans and
timings were different. The extra `HAVING` exercise connects written clause
order with logical evaluation order. The isolated covering-index scan and
index-curiosity examples are also small enough to reproduce without the
warehouse database.
