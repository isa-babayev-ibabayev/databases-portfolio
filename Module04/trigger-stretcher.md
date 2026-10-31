# Optional Task 5 — Trigger Timing

[`trigger-stretcher.py`](trigger-stretcher.py) runs two isolated experiments.
A `BEFORE INSERT` trigger uses `RAISE(ABORT, ...)` to reject a negative value,
and an `AFTER INSERT` trigger records only successful inserts. An
`INSTEAD OF INSERT` trigger on a view routes a write to its underlying table.

Recorded output with Python 3.14.5 and SQLite 3.50.4:

```text
Python SQLite runtime: 3.50.4
BEFORE trigger rejection: negative values blocked by BEFORE trigger
rows after rejected BEFORE insert: 0
AFTER log rows after rejection: 0
successful row: (1, 2.5)
AFTER log row: (1, 2.5)
INSTEAD OF routed row: (10, 7.5)
```

The experiment shows that a SQLite `BEFORE` trigger can reject an operation;
it is not limited to changing values. The `AFTER` trigger sees the completed
row and its log entry is part of the same transaction. Because SQLite views
are read-only by default, `INSTEAD OF` is the appropriate timing for routing a
view write into a real table.
