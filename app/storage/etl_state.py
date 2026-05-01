"""ETL 증분 동기화 상태 관리.

NEXT2-3 R2 단계: 일일 증분 동기화의 last_synced_at 추적.
SQLite (govprocu.db) 에 etl_state 테이블 추가.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import aiosqlite

from app.storage.db import DB_PATH


_SCHEMA = """
CREATE TABLE IF NOT EXISTS etl_state (
    job_name TEXT PRIMARY KEY,
    last_synced_at TEXT NOT NULL,
    last_success_at TEXT,
    last_error TEXT,
    success_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    metadata TEXT
);
"""


async def init_etl_state() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()


async def get_last_synced_at(job_name: str) -> datetime | None:
    """job_name의 마지막 동기화 시각."""
    await init_etl_state()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT last_synced_at FROM etl_state WHERE job_name=?",
            (job_name,),
        )
        row = await cur.fetchone()
        if not row:
            return None
        try:
            return datetime.fromisoformat(row[0])
        except ValueError:
            return None


async def mark_success(
    job_name: str,
    metadata: str | None = None,
) -> None:
    """동기화 성공 기록."""
    await init_etl_state()
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO etl_state (job_name, last_synced_at, last_success_at,
                                    success_count, error_count, metadata)
            VALUES (?, ?, ?, 1, 0, ?)
            ON CONFLICT(job_name) DO UPDATE SET
                last_synced_at = excluded.last_synced_at,
                last_success_at = excluded.last_success_at,
                success_count = etl_state.success_count + 1,
                last_error = NULL,
                metadata = excluded.metadata
            """,
            (job_name, now, now, metadata),
        )
        await db.commit()


async def mark_error(job_name: str, error: str) -> None:
    """동기화 실패 기록."""
    await init_etl_state()
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO etl_state (job_name, last_synced_at, last_error,
                                    success_count, error_count)
            VALUES (?, ?, ?, 0, 1)
            ON CONFLICT(job_name) DO UPDATE SET
                last_synced_at = excluded.last_synced_at,
                last_error = excluded.last_error,
                error_count = etl_state.error_count + 1
            """,
            (job_name, now, error[:500]),
        )
        await db.commit()


async def list_jobs() -> list[dict]:
    """모든 ETL job 상태."""
    await init_etl_state()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM etl_state ORDER BY last_synced_at DESC"
        )
        return [dict(r) for r in await cur.fetchall()]
