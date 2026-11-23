"""SQLite <-> plain-text SQL snapshot helper for Git-friendly database sync."""
import argparse
from datetime import datetime
import os
from pathlib import Path
import shutil
import sqlite3
import sys

DEFAULT_DB_PATH = "vtuber_songs.db"
DEFAULT_DUMP_PATH = "database_dump.sql"
REQUIRED_TABLES = ("vtubers", "songs", "artists", "videos", "singing_records")


def _get_user_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return sorted(row[0] for row in rows)


def _validate_required_tables(tables: list[str], source_label: str) -> None:
    missing = [tbl for tbl in REQUIRED_TABLES if tbl not in tables]
    if missing:
        raise ValueError(f"{source_label} 缺少必要資料表：{', '.join(missing)}")


def dump_database(
    db_path: str = DEFAULT_DB_PATH, dump_path: str = DEFAULT_DUMP_PATH
) -> dict:
    """Export SQLite database into an atomic UTF-8 plain-text SQL script."""
    abs_db = os.path.abspath(db_path)
    abs_dump = os.path.abspath(dump_path)

    if not os.path.exists(abs_db):
        raise FileNotFoundError(f"找不到來源資料庫檔案：{abs_db}")
    if os.path.getsize(abs_db) <= 0:
        raise ValueError(f"來源資料庫檔案為空：{abs_db}")

    ro_uri = Path(abs_db).as_uri() + "?mode=ro"
    conn = sqlite3.connect(ro_uri, uri=True, timeout=10.0)
    try:
        integrity = conn.execute("PRAGMA integrity_check;").fetchall()
        if integrity != [("ok",)]:
            raise ValueError(f"來源資料庫完整性檢查失敗：{integrity}")

        tables = _get_user_tables(conn)
        _validate_required_tables(tables, "來源資料庫")

        dump_lines = list(conn.iterdump())
    finally:
        conn.close()

    if not dump_lines:
        raise ValueError(f"SQL 匯出內容為空：{abs_db}")

    sql_text = "\n".join(dump_lines) + "\n"
    if not sql_text.endswith("COMMIT;\n"):
        raise ValueError("SQL 匯出未以 COMMIT; 結尾，檔案可能不完整")

    dump_dir = os.path.dirname(abs_dump)
    if dump_dir:
        os.makedirs(dump_dir, exist_ok=True)

    tmp_dump = abs_dump + ".tmp"
    try:
        with open(tmp_dump, "w", encoding="utf-8", newline="\n") as f:
            f.write(sql_text)
        os.replace(tmp_dump, abs_dump)
    except Exception:
        if os.path.exists(tmp_dump):
            os.remove(tmp_dump)
        raise

    return {
        "db_path": abs_db,
        "dump_path": abs_dump,
        "lines": len(dump_lines),
        "bytes": len(sql_text.encode("utf-8")),
        "tables": tables,
    }


def restore_database(
    dump_path: str = DEFAULT_DUMP_PATH,
    db_path: str = DEFAULT_DB_PATH,
    *,
    if_missing: bool = False,
    force: bool = False,
) -> dict:
    """Restore an SQLite database atomically from a plain-text SQL dump."""
    abs_dump = os.path.abspath(dump_path)
    abs_db = os.path.abspath(db_path)

    db_exists = os.path.exists(abs_db) and os.path.getsize(abs_db) > 0
    if db_exists:
        if if_missing:
            return {"restored": False, "skipped": True, "db_path": abs_db}
        if not force:
            raise FileExistsError(
                f"目標資料庫已存在：{abs_db}（若確定要覆寫，請加上 --force）"
            )

    if not os.path.exists(abs_dump):
        raise FileNotFoundError(f"找不到 SQL 快照檔案：{abs_dump}")
    if os.path.getsize(abs_dump) <= 0:
        raise ValueError(f"SQL 快照檔案為空：{abs_dump}")

    with open(abs_dump, "r", encoding="utf-8") as f:
        sql_text = f.read()

    if not sql_text.strip():
        raise ValueError(f"SQL 快照內容為空：{abs_dump}")

    db_dir = os.path.dirname(abs_db)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    tmp_db_path = abs_db + ".restore.tmp"
    if os.path.exists(tmp_db_path):
        os.remove(tmp_db_path)

    conn = None
    tables: list[str] = []
    try:
        conn = sqlite3.connect(tmp_db_path, timeout=10.0)
        conn.execute("PRAGMA foreign_keys=OFF;")
        conn.executescript(sql_text)
        conn.execute("PRAGMA foreign_keys=ON;")

        integrity = conn.execute("PRAGMA integrity_check;").fetchall()
        if integrity != [("ok",)]:
            raise ValueError(f"還原資料庫完整性檢查失敗：{integrity}")

        fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
        if fk_errors:
            raise ValueError(f"還原資料庫外鍵檢查失敗：{fk_errors[:5]}")

        tables = _get_user_tables(conn)
        _validate_required_tables(tables, "還原資料庫")
    except Exception:
        if conn is not None:
            conn.close()
            conn = None
        if os.path.exists(tmp_db_path):
            os.remove(tmp_db_path)
        raise
    finally:
        if conn is not None:
            conn.close()

    backup_path = None
    if os.path.exists(abs_db) and os.path.getsize(abs_db) > 0:
        backup_dir = os.path.join(db_dir or ".", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"pre_sql_restore_{timestamp}.db")
        shutil.copy2(abs_db, backup_path)

    os.replace(tmp_db_path, abs_db)
    return {
        "restored": True,
        "skipped": False,
        "db_path": abs_db,
        "tables": tables,
        "backup_path": backup_path,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DDDiary SQLite <-> plain-text SQL snapshot sync tool."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_dump = sub.add_parser("dump", help="Dump SQLite database to plain-text SQL.")
    p_dump.add_argument("--db", default=DEFAULT_DB_PATH, help="Source SQLite DB path.")
    p_dump.add_argument(
        "--dump", default=DEFAULT_DUMP_PATH, help="Target plain-text SQL dump path."
    )

    p_restore = sub.add_parser(
        "restore", help="Restore SQLite database from plain-text SQL dump."
    )
    p_restore.add_argument(
        "--db", default=DEFAULT_DB_PATH, help="Target SQLite DB path."
    )
    p_restore.add_argument(
        "--dump", default=DEFAULT_DUMP_PATH, help="Source plain-text SQL dump path."
    )
    p_restore.add_argument(
        "--if-missing",
        action="store_true",
        help="Only restore when target SQLite DB does not exist or is empty.",
    )
    p_restore.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing target SQLite DB (auto-creates pre-restore backup).",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        if args.command == "dump":
            print(f"[*] Exporting {args.db} -> {args.dump} ...")
            res = dump_database(db_path=args.db, dump_path=args.dump)
            size_kb = res["bytes"] / 1024.0
            print(
                f"[OK] SQL dump updated: {res['dump_path']} "
                f"({res['lines']} lines, {size_kb:.1f} KB, {len(res['tables'])} tables)"
            )
            return 0

        if args.command == "restore":
            res = restore_database(
                dump_path=args.dump,
                db_path=args.db,
                if_missing=args.if_missing,
                force=args.force,
            )
            if res.get("skipped"):
                print(f"[i] Target DB already exists, skipped restore: {res['db_path']}")
                return 0
            if res.get("backup_path"):
                print(f"[*] Pre-restore backup saved: {res['backup_path']}")
            print(
                f"[OK] Database restored: {res['db_path']} ({len(res['tables'])} tables)"
            )
            return 0
    except Exception as exc:
        print(f"[!] Error: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
