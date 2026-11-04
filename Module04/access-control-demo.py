"""Demonstrate SQLite and Windows controls on a disposable database."""

from __future__ import annotations

import ctypes
import os
import platform
import sqlite3
import subprocess
import tempfile
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent


def run_icacls(*arguments: str | Path) -> subprocess.CompletedProcess[str]:
    """Run icacls without a shell so paths and account names stay separate."""
    return subprocess.run(
        ["icacls", *(str(argument) for argument in arguments)],
        check=False,
        capture_output=True,
        text=True,
    )


def require_success(result: subprocess.CompletedProcess[str], action: str) -> None:
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"{action} failed with exit code {result.returncode}: {detail}")


def windows_filesystem(path: Path) -> str:
    """Return the Windows filesystem name without requiring administrator rights."""
    root = os.path.splitdrive(str(path.resolve()))[0] + "\\"
    filesystem = ctypes.create_unicode_buffer(261)
    success = ctypes.windll.kernel32.GetVolumeInformationW(
        root,
        None,
        0,
        None,
        None,
        None,
        filesystem,
        len(filesystem),
    )
    return filesystem.value if success else "unknown"


def displayed_acl(output: str, database: Path) -> str:
    """Keep the ACL evidence while replacing the random temporary path."""
    return output.strip().replace(str(database), r"<TEMP>\edge-access.db")


def demonstrate_windows_acl(database: Path) -> None:
    """Deny file writes, prove the denial, and restore the original ACL."""
    if os.name != "nt":
        print("Windows ACL demonstration: SKIPPED (requires Windows and icacls)")
        return

    resolved_database = database.resolve()
    system_temp = Path(tempfile.gettempdir()).resolve()
    repository = MODULE_DIR.parent.resolve()
    if not resolved_database.is_relative_to(system_temp):
        raise RuntimeError("ACL experiment target is not inside the Windows Temp directory")
    if resolved_database.is_relative_to(repository):
        raise RuntimeError("ACL experiment must never target a repository file")

    identity_result = subprocess.run(
        ["whoami"],
        check=False,
        capture_output=True,
        text=True,
    )
    require_success(identity_result, "whoami")
    identity = identity_result.stdout.strip()
    target = r"<TEMP>\edge-access.db"

    original = run_icacls(database)
    require_success(original, "original ACL inspection")
    original_acl = original.stdout.strip()
    if f"{identity.lower()}:(deny)" in original_acl.lower():
        raise RuntimeError("the new disposable file already has an explicit deny entry")

    print("\n## Windows ACL write-denial experiment")
    print(f"Windows environment: {platform.platform()}")
    print(f"temporary filesystem: {windows_filesystem(database)}")
    print(f"current identity: {identity}")
    print("elevation required: no (the current user owns the disposable Temp file)")
    print(f'command: icacls "{target}"')
    print("original ACL:")
    print(displayed_acl(original.stdout, database))
    print(f'command: icacls "{target}" /deny "{identity}:(WD,AD)" /c')

    deny_applied = False
    restore = None
    try:
        deny = run_icacls(database, "/deny", f"{identity}:(WD,AD)", "/c")
        require_success(deny, "temporary ACL write denial")
        deny_applied = True
        print(f"ACL deny exit code: {deny.returncode}")

        read_only = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            print(
                "ACL-protected read count: "
                f"{read_only.execute('SELECT count(*) FROM reading').fetchone()[0]}"
            )
        finally:
            read_only.close()

        read_write = sqlite3.connect(database.resolve().as_uri() + "?mode=rw", uri=True)
        try:
            query_only = read_write.execute("PRAGMA query_only").fetchone()[0]
            print(f"ACL mode=rw query_only setting: {query_only}")
            try:
                read_write.execute("DELETE FROM reading")
                read_write.commit()
            except sqlite3.OperationalError as exc:
                print(f"ACL mode=rw DELETE rejected: {exc}")
            else:
                raise RuntimeError("ACL-protected write unexpectedly succeeded")
        finally:
            read_write.close()
    finally:
        if deny_applied:
            print(f'command: icacls "{target}" /remove:d "{identity}" /c')
            restore = run_icacls(database, "/remove:d", identity, "/c")
            if restore.returncode != 0:
                reset = run_icacls(database, "/reset", "/c")
                require_success(reset, "fallback ACL reset")

    if restore is None:
        raise RuntimeError("ACL denial was not applied")
    print(f"ACL restore exit code: {restore.returncode}")

    restored = run_icacls(database)
    require_success(restored, "restored ACL inspection")
    restored_exactly = restored.stdout.strip() == original_acl
    print(f"ACL restored exactly: {'yes' if restored_exactly else 'no'}")
    if not restored_exactly:
        raise RuntimeError("the disposable file ACL does not match its original ACL")

    writable = sqlite3.connect(database)
    try:
        writable.execute("DELETE FROM reading")
        writable.rollback()
        print("post-restore write probe: SUCCESS (rolled back)")
    finally:
        writable.close()


def main() -> None:
    print(f"Python SQLite runtime: {sqlite3.sqlite_version}")
    temporary_path: Path | None = None
    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        database = Path(temporary) / "edge-access.db"
        connection = sqlite3.connect(database)
        connection.executescript((MODULE_DIR / "setup.sql").read_text(encoding="utf-8"))
        connection.close()

        read_only_uri = database.resolve().as_uri() + "?mode=ro"
        read_only = sqlite3.connect(read_only_uri, uri=True)
        print(f"mode=ro reading count: {read_only.execute('SELECT count(*) FROM reading').fetchone()[0]}")
        print(f"mode=ro view rows: {read_only.execute('SELECT count(*) FROM machine_health').fetchone()[0]}")
        try:
            read_only.execute("DELETE FROM reading")
        except sqlite3.OperationalError as exc:
            print(f"mode=ro DELETE rejected: {exc}")
        read_only.close()

        query_only = sqlite3.connect(database)
        query_only.execute("PRAGMA query_only = ON")
        print(f"query_only setting: {query_only.execute('PRAGMA query_only').fetchone()[0]}")
        try:
            query_only.execute("DELETE FROM reading")
        except sqlite3.OperationalError as exc:
            print(f"query_only DELETE rejected: {exc}")
        query_only.close()

        demonstrate_windows_acl(database)

    print(
        "disposable temporary directory removed: "
        f"{'yes' if temporary_path is not None and not temporary_path.exists() else 'no'}"
    )


if __name__ == "__main__":
    main()
