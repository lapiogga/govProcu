"""NTS API 일일 한도 추적 (기본 100건/일).

NEXT6-5: NTS 호출 카운트 SQLite 기록 + 80% 도달 경고 + 100% 차단.
"""
from __future__ import annotations
from datetime import datetime

import aiosqlite

from app.storage.db import DB_PATH


_SCHEMA = """
CREATE TABLE IF NOT EXISTS nts_quota (
    quota_date TEXT PRIMARY KEY,
    call_count INTEGER NOT NULL DEFAULT 0,
    last_call_at TEXT
);
"""

DAILY_LIMIT = 100  # NTS 표준 일일 한도


async def init_quota() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()


async def consume(count: int = 1) -> dict:
    """NTS 호출 1건 차감. 한도 초과 시 raise."""
    await init_quota()
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT call_count FROM nts_quota WHERE quota_date=?",
            (today,),
        )
        row = await cur.fetchone()
        used = row[0] if row else 0

        if used + count > DAILY_LIMIT:
            return {
                "ok": False,
                "used": used,
                "limit": DAILY_LIMIT,
                "remaining": max(0, DAILY_LIMIT - used),
                "error": "NTS 일일 한도 초과",
            }

        await db.execute(
            """INSERT INTO nts_quota (quota_date, call_count, last_call_at)
               VALUES (?, ?, ?)
               ON CONFLICT(quota_date) DO UPDATE SET
                 call_count = nts_quota.call_count + ?,
                 last_call_at = excluded.last_call_at""",
            (today, count, now, count),
        )
        await db.commit()

    new_used = used + count
    warning = new_used >= DAILY_LIMIT * 0.8
    return {
        "ok": True,
        "used": new_used,
        "limit": DAILY_LIMIT,
        "remaining": DAILY_LIMIT - new_used,
        "warning_80pct": warning,
    }


async def get_today_status() -> dict:
    """오늘 NTS 사용 현황."""
    await init_quota()
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT call_count, last_call_at FROM nts_quota WHERE quota_date=?",
            (today,),
        )
        row = await cur.fetchone()
    used = row[0] if row else 0
    return {
        "date": today,
        "used": used,
        "limit": DAILY_LIMIT,
        "remaining": DAILY_LIMIT - used,
        "last_call_at": row[1] if row else None,
    }
