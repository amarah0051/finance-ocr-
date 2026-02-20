import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config.settings import settings


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def iso_plus_days(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _conn() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_storage() -> None:
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workbooks (
                workbook_id TEXT PRIMARY KEY,
                output_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def upsert_workbook(workbook_id: str, output_path: Path) -> None:
    now = utc_now_iso()
    expires = iso_plus_days(settings.retention_days)
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO workbooks(workbook_id, output_path, created_at, updated_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(workbook_id)
            DO UPDATE SET output_path=excluded.output_path, updated_at=excluded.updated_at, expires_at=excluded.expires_at
            """,
            (workbook_id, str(output_path), now, now, expires),
        )
        conn.commit()


def get_workbook(workbook_id: str) -> sqlite3.Row | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM workbooks WHERE workbook_id = ?", (workbook_id,)).fetchone()
    return row


def cleanup_expired() -> int:
    now = datetime.now(timezone.utc)
    deleted = 0
    with _conn() as conn:
        rows = conn.execute("SELECT workbook_id, output_path, expires_at FROM workbooks").fetchall()
        for row in rows:
            expires_at = datetime.fromisoformat(row["expires_at"])
            if expires_at <= now:
                path = Path(row["output_path"])
                if path.exists():
                    os.remove(path)
                conn.execute("DELETE FROM workbooks WHERE workbook_id = ?", (row["workbook_id"],))
                deleted += 1
        conn.commit()
    return deleted
