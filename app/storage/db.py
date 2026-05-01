"""SQLite 영속 저장소 (사용자 알림·즐겨찾기 상태).

aiosqlite 비동기. 운영 시 redis와 병행:
- redis: 캐시 (단기, TTL)
- sqlite: 사용자 상태 (영구)

스키마:
- subscriptions: 키워드 알림 구독
- watchlist: 즐겨찾기 (공고/사업자/기관)
- digest_log: 일일 다이제스트 발송 이력
"""
from __future__ import annotations
from pathlib import Path
import aiosqlite

# 기본 DB 경로 (운영 시 환경변수로 변경 가능)
DB_PATH = Path(__file__).resolve().parent.parent.parent / "runtime" / "govprocu.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_token TEXT NOT NULL,
    keyword TEXT NOT NULL,
    biz_type TEXT,
    inst_name TEXT,
    region TEXT,
    min_amount INTEGER,
    max_amount INTEGER,
    notify_email TEXT,
    notify_kakao TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    active INTEGER NOT NULL DEFAULT 1,
    UNIQUE(user_token, keyword, biz_type, inst_name)
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user
    ON subscriptions(user_token, active);

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_token TEXT NOT NULL,
    item_type TEXT NOT NULL CHECK (item_type IN ('bid', 'vendor', 'agency', 'contract')),
    item_key TEXT NOT NULL,
    item_label TEXT,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(user_token, item_type, item_key)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_user
    ON watchlist(user_token, item_type);

CREATE TABLE IF NOT EXISTS digest_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_token TEXT NOT NULL,
    digest_date TEXT NOT NULL,
    digest_type TEXT NOT NULL CHECK (digest_type IN ('daily', 'weekly')),
    item_count INTEGER NOT NULL DEFAULT 0,
    sent_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(user_token, digest_date, digest_type)
);
"""


async def init_db() -> None:
    """DB 파일 + 스키마 초기화. 이미 있으면 no-op."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()


async def get_db() -> aiosqlite.Connection:
    """비동기 connection. 호출자가 close() 책임."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db
