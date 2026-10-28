# Reflection 03 — SQL profiling and verification

## Take-away

The technical evidence shows that an index is not automatically an
improvement: the query plan and repeated measurements both matter.

TODO — STUDENT: Add the result you personally want to remember and advice to
your past self.

## What was good?

The warehouse fixture rebuilt to the exact row counts, the AI-generated city
query matched an independent Python calculation, and all three late-order
query variants returned equivalent results. Bound parameters also handled both
an apostrophe-containing name and the injection payload correctly.

TODO — STUDENT: Confirm which result you personally considered successful.

## What was difficult?

The measured dashboard changed from a 160.880 ms median to 1429.524 ms after
the join index changed the loop order. This is technically important because
the apparently more indexed plan was worse for this aggregate.

TODO — STUDENT: Describe what you personally found difficult; do not simply
adopt the technical statement above if it was not your experience.

## Exploration and show stoppers

The experiments compared a leading-wildcard scan, a function-wrapped date
scan, an expression-index option, a covering index, and an FTS5 trigram option.
The original classroom Task A also retained the initial missing-semicolon
syntax error instead of hiding it.

TODO — STUDENT: Add any real show stopper or instructor question you had.

## Interaction with peers and instructors

Student-supplied Task C notes report that the pod compared a Windows plan with
a neighboring pod's macOS plan, discussed functions and leading wildcards, and
prepared a question about case-insensitive and substring search. The other
pod's raw plan/version and any Discord link were not supplied, so the report
does not claim independent corroboration or posting.

TODO — STUDENT: Add names or personal learning only if appropriate and
factually supported.

## How did you verify AI suggestions?

The generated SQL was executed against 60,000 orders and 240,000 lines. Its
result was checked with an independent Python aggregation and a small
edge-case fixture. Index suggestions were tested with five timing runs and
saved plans instead of assumed to help. Injection behavior and window-query
equivalence were covered by automated tests.

## Help and extra work

The technical extension added repeatable benchmark, security, algebra, and
optional window-function evidence. AI assistance was used for implementation
and drafting, then checked against SQLite output, tests, and primary
documentation. AI is not listed as a human pod member or contributor.

TODO — STUDENT: Record any genuine help you gave or received and any real
presentation/checkpoint work.
