# Reflection 03 — Checking SQL instead of only running it

## Take-away

My main lesson from this module is that a working SQL query is not always a
correct or efficient query. I learned that I should check the result, read the
query plan, and measure the performance. The index benchmark was a useful
example because one added index changed the plan and made the dashboard much
slower instead of faster.

## What was good?

The city dashboard produced clear customer and revenue results for four
cities. Its result was checked with a separate Python calculation and with a
small edge-case dataset. The date boundaries were also checked, so orders from
2025 were included while `2026-01-01` was excluded. I liked this verification
because it showed more than simply saying that the query ran without an error.

## What was difficult?

The most difficult concept was understanding why SQLite does not always use an
index in the way I expect. I first connected an index with a faster query, but
the plans showed that loop order and repeated lookups are also important. It
also took care to understand the difference between `WHERE`, which filters
rows, and `HAVING`, which filters groups after `GROUP BY`.

## Exploration and show stoppers

The most interesting experiment was the benchmark. The dashboard baseline
median was about 160.88 ms, but the index-driven stage had a median of about
1429.52 ms. In contrast, the date index made a one-day lookup about 12.9 times
faster, and the product index made its direct filter about 4.9 times faster in
the recorded environment. This taught me that an index can help one query and
be ignored or harmful for another query. I also explored leading wildcards,
function-wrapped columns, and covering indexes.

I also ran a separate disposable curiosity experiment with 1,000 rows. The
technician equality query changed from `SCAN` to `SEARCH` after its index was
created, while `LIKE '%ei%'` still scanned. This made the difference between
"an index exists" and "this particular predicate can use the index" clearer.

## Interaction with peers and instructors

I participated in a classroom discussion with students from another group.
Our notes record a comparison between a Windows plan and the other group's
macOS plan, with discussion of function-wrapped columns, leading wildcards,
and covering indexes. I do not remember the group number or participant names,
and their raw output and SQLite version were not saved. I therefore label
those details as student-reported rather than independently verified. The
illustrative exchange and later disposable experiment in the study notes are
portfolio follow-up, not a verbatim classroom transcript or a second
person-to-person swap. The workbook's Discord step is conditional; I do not
claim a Discord post.

## How did you verify AI suggestions?

AI suggestions were used as a starting point, but the technical results were
checked against SQLite output. The dashboard result was compared with an
independent Python aggregation and an edge-case fixture. `EXPLAIN QUERY PLAN`
showed that the actual loop order was different from the prediction. Five
timing runs showed that an index suggestion could make the query slower. The
window-function rewrite was checked for repeated customer rows, and the SQL
injection example compared unsafe string building with bound parameters.

## Help and extra work

The optional exercise compared a grouped query, a correlated subquery, and a
window-function query. They returned the same 400 customers, but their plans
and timings were very different. The extra `HAVING` exercise also helped me
connect the written SQL order with the logical order. AI assistance was used
for drafting and technical verification, and the suggestions were checked
with query results, plans, tests, and documentation rather than accepted
without evidence. The additional index-curiosity SQL and saved plan output
provide another small example that a classmate can reproduce without using
the generated warehouse database.
