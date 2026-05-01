"""감사 로그 (audit log) — SQLite 기록.

NEXT6-5: 도구 호출 + 사용자 토큰 + 결과 상태 누적.
운영 시 보안 사고 추적 + 사용 패턴 분석.

스키마: app.storage.db audit_log 테이블 (자동 생성).
"""
from __future__ import annotations
import json
from datetime import datetime

import aiosqlite

from app.storage.db import DB_PATH


_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    user_token TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    args TEXT,
    status TEXT NOT NULL,
    error TEXT,
    duration_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_audit_user_ts
    ON audit_log(user_token, ts);

CREATE INDEX IF NOT EXISTS idx_audit_tool
    ON audit_log(tool_name, ts);
"""


async def init_audit() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()


async def log_audit(
    user_token: str,
    tool_name: str,
    args: dict | None = None,
    status: str = "success",
    error: str | None = None,
    duration_ms: int | None = None,
) -> None:
    """1건 audit 기록."""
    await init_audit()
    args_json = json.dumps(args, ensure_ascii=False)[:1000] if args else None
    error_short = (error or "")[:500]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO audit_log (user_token, tool_name, args, status, error, duration_ms)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_token, tool_name, args_json, status, error_short, duration_ms),
        )
        await db.commit()


async def query_recent_audit(
    user_token: str | None = None,
    tool_name: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """최근 audit 조회 (관리자용)."""
    await init_audit()
    sql = "SELECT * FROM audit_log WHERE 1=1"
    params: list = []
    if user_token:
        sql += " AND user_token=?"
        params.append(user_token)
    if tool_name:
        sql += " AND tool_name=?"
        params.append(tool_name)
    sql += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(sql, params)
        return [dict(r) for r in await cur.fetchall()]
