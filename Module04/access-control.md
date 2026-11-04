# Access Control Without a Database Server

## Reporting view

`machine_health` groups readings by machine and metric and exposes only the
peak and row count required for a small health report. It is a convenient query
interface, but it is not an authorization boundary: anyone who can open the
database without restrictions can still query the underlying tables.

## Verified SQLite protections

[`access-control-demo.py`](access-control-demo.py) creates a disposable database
and first demonstrates two connection-level controls. A URI connection using
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
bits. The demonstration uses a newly created database in the Windows Temp
directory, never a repository or OneDrive file. No elevation is needed because
the current user owns this disposable file.

The script records the original ACL and then runs the Windows equivalent below.
`WD` means write data and `AD` means append data; denying only those rights
still permits a read-only connection to open the file.

```powershell
$AclIdentity = (whoami).Trim()
icacls "<TEMP>\edge-access.db" /deny "${AclIdentity}:(WD,AD)" /c
```

With that deny entry active, a `mode=ro` connection successfully read one row.
A separate `mode=rw` connection reported `PRAGMA query_only = 0`, so its failed
`DELETE` was not caused by SQLite's read-only URI or `query_only`. The write
failed with `attempt to write a readonly database` because Windows denied write
access to the file.

A guaranteed `finally` block removes only the temporary deny entry:

```powershell
icacls "<TEMP>\edge-access.db" /remove:d $AclIdentity /c
```

The script then compares the restored ACL with the recorded original, performs
a successful write probe inside a rolled-back transaction, and verifies that
the complete temporary directory was removed. The saved run reports exit code
0 for both ACL changes, an exact ACL match after restoration, and successful
cleanup. If adding or removing the ACL fails, the script raises an error rather
than reporting success.

## SQLite and PostgreSQL comparison

PostgreSQL has server-managed roles and object privileges controlled with
commands such as `GRANT`, whereas SQLite has no native `CREATE ROLE` or `GRANT`
system and normally relies on file permissions and connection configuration.
SQLite read-only URI mode is useful for a process that should only query a
single-purpose edge database. That file-based isolation can be appropriate on
one controlled device, but it is not sufficient as the sole authorization
model for a multi-tenant web application where users require distinct,
server-enforced privileges.
