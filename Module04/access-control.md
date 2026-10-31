# Access Control Without a Database Server

## Reporting view

`machine_health` groups readings by machine and metric and exposes only the
peak and row count required for a small health report. It is a convenient query
interface, but it is not an authorization boundary: anyone who can open the
database without restrictions can still query the underlying tables.

## Verified SQLite protections

[`access-control-demo.py`](access-control-demo.py) creates a disposable database
and demonstrates two connection-level controls. A URI connection using
`mode=ro` can read both `reading` and `machine_health`, while `DELETE` fails with
`attempt to write a readonly database`. A separate connection with
`PRAGMA query_only = ON` can read data but rejects the same write with the same
error. The recorded output is in
[`access-control-results.txt`](access-control-results.txt).

`query_only` protects only the connection on which it is enabled. A later
connection is writable unless it independently uses read-only mode, enables
`query_only`, or is blocked by operating-system permissions.

## Windows filesystem controls

The workbook's `chmod 444` example is a Unix permission command; Windows uses
NTFS access control lists (ACLs) instead of the Unix owner/group/other mode
bits. `icacls` can inspect, grant, deny, save, and restore Windows ACL entries.
The demonstration inspected the ACL of the disposable database with `icacls`
and received exit code 0, but deliberately made no ACL changes. This avoids
locking the student out or changing inherited repository permissions, so an
OS-level denial is not claimed as verified evidence.

## SQLite and PostgreSQL comparison

PostgreSQL has server-managed roles and object privileges controlled with
commands such as `GRANT`, whereas SQLite has no native `CREATE ROLE` or `GRANT`
system and normally relies on file permissions and connection configuration.
SQLite read-only URI mode is useful for a process that should only query a
single-purpose edge database. That file-based isolation can be appropriate on
one controlled device, but it is not sufficient as the sole authorization
model for a multi-tenant web application where users require distinct,
server-enforced privileges.
