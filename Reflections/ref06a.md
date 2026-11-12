# Reflection 06a — The analytical engine

> Draft structure based on reproducible Module 6a technical evidence. It is not
> a final personal reflection. The student must revise the personal-experience
> and interaction sections after the actual class.

## Take-away

Technical evidence available for personal reflection: the same two-million-row
data produced very different results depending on workload. DuckDB over Parquet
was 78.67× and 94.43× faster for two full-history aggregates, while SQLite was
hundreds to thousands of times faster for 1,000 separate inserts and lookups.

**Student input required:** What do I personally want to remember, and what
advice would I give after doing or reviewing the exercise?

## What was good?

Technical evidence available: the export was checked by count, price sum, ID
sum, date limits, schema, and nulls; every benchmark compared results before
accepting timings. The source database hash remained unchanged.

**Student input required:** Which part of the session felt useful or worked well
for me?

## What was difficult?

Technical issue available for reflection: the provisional workbook uses
DuckDB's `strftime(date, format)` argument order for SQLite too. SQLite silently
returned NULL months, so a fair comparison required the equivalent SQLite form
`strftime(format, date)`.

**Student input required:** Did I encounter this or another difficulty myself,
and how did I respond?

## Exploration and show stoppers

Executed exploration: fixed +90 days, +91 days, and +1 month produced different
calendar behavior. Zstandard reduced Parquet size by 41.15% but was slightly
slower in the warm aggregate. DuckDB `executemany` also failed to improve its
row-at-a-time median on this machine.

**Student input required:** Which result surprised me, and is there a question I
want to take to the professor?

## Interaction with peers and instructors

No nearest-pod discussion, Tunay conversation, instructor feedback, or Discord
sharing is documented as completed. The six discussion questions are prepared
in `Module06a/duckdb-notes.md`.

**Student input required:** Add only the real participants, questions, feedback,
and value of an actual classroom interaction.

## How did you verify AI suggestions?

Reproducible verification available: scripts were executed on real data;
SQLite and Parquet summaries were cross-checked; result sets were compared;
five interleaved timings were recorded; plans were captured; source hashes and
Git ignore behavior were checked; and automated tests cover the evidence.

**Student input required:** Explain in my own words which checks I understood or
personally repeated before submitting.

## Help and extra work

Technical extra work available: safe temporary-file publication, source-hash
preservation, the date arithmetic experiment, Zstandard compression comparison,
and a compatibility correction for cross-engine `strftime` semantics.

**Student input required:** Record genuine help given or received and any work I
personally completed beyond the core studio.
