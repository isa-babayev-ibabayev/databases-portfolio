# Task 3 — SQL injection drill

The demonstration is isolated in [injection_demo.py](injection_demo.py). It
opens the generated warehouse read-only, copies it into SQLite `:memory:`, and
runs every unsafe and safe query on that disposable copy. `O'Brien` is inserted
only into memory; the source database is never written.

Observed behavior:

- normal vulnerable lookup for `Customer 1`: one legitimate row;
- vulnerable lookup for `O'Brien`: syntax error;
- parameterized lookup for `O'Brien`: the intended row;
- vulnerable payload `' OR '1'='1`: 2,001 rows;
- parameterized payload: no rows;
- the source database remains read-only and unchanged.

Raw output: [injection-output.txt](evidence/injection-output.txt).

The unsafe function puts input inside SQL syntax. The payload closes the string
literal and adds a condition that is true for every row. The safe function
keeps SQL fixed and sends the value separately with `?`; SQLite therefore
treats every quote and operator as data.

Manual escaping or deleting apostrophes is not a reliable defense. It can
corrupt legitimate names, depends on SQL dialect and context, misses non-string
contexts and encoding rules, and makes the application responsible for
reimplementing the database driver's parser. Bound parameters are the general
defense for data values. Dynamic identifiers require a fixed allow-list because
placeholders cannot represent table or column names.

The intentionally vulnerable function exists only for this educational file
and is not reused by application code.
