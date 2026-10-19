# Module 2 reflection

This draft reflects facts demonstrated by the repository. Personal reactions
must be reviewed and completed by the student.

## 1. What worked?

Rebuilding the supplied fixture from SQL made the audit repeatable. Count
queries showed concrete relationships: `cnc-01` appears in two jobs, job 1
contains two encoded parts, and `P-1001` occurs in two jobs. Separating
Pydantic input models from SQLAlchemy tables worked well: Pydantic rejected bad
dates and malformed values before persistence, while SQLite rejected duplicate
keys, orphan references, and negative prices.

## 2. What broke?

The legacy equality join treated the complete comma-separated field as one key.
It omitted job 1 and duplicated job 2 because the Part table contains two
`P-1003` rows. Text price comparison also excluded `9.90` from values below
`15`. During implementation, the first DDL emission called `.strip()`
directly on SQLAlchemy's compiler object, and the first dynamic test import
interacted badly with postponed annotations. Converting the compiler to
`str` and using runtime annotations fixed both issues; all 11 tests then
passed.

## 3. How did the model shift?

The useful technical shift is from trusting labels to asking what the database
enforces. A field called `job_id` is not a key until a constraint says so, and
two columns with the same meaning are not a relationship without a foreign key.
MaintenanceJob is more useful as an entity than as a bare relationship because
it owns a date and participates in the JobPart relationship.

## 4. How were AI suggestions verified?

Each AI-assisted claim was translated into a check. `sqlite_master` exposed
the absence of constraints; joins and counts tested cardinality claims; text
and numeric comparisons were run side by side; invalid Pydantic inputs and
violating database inserts were automated in isolated temporary databases.
The wording was narrowed where necessary—for example, text pricing does not
make every comparison fail, but the captured `9.90` counterexample proves it
can silently produce the wrong result.

## Personal reflection

**HUMAN INPUT REQUIRED:** Rewrite or confirm the sections above in your own
voice. Add what surprised you, what remains difficult, and what you can now
explain without notes. Do not mark the pod or peer-review work complete until it
actually occurs.
