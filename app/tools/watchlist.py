"""watchlist 영역 MCP 도구 — 즐겨찾기/관심 항목 관리.

사용자 5/2 22번 우선순위 P0 (필수, 시장 진입 자격).
4개 relational key(공고/사업자/기관/계약) 어떤 것이든 즐겨찾기 가능.

도구:
- add_to_watchlist: 항목 추가
- remove_from_watchlist: 항목 제거
- list_my_watchlist: 내 즐겨찾기 목록 (타입별 필터)

영속 저장소: app.storage.db (SQLite, watchlist 테이블)
"""
from __future__ import annotations
from typing import Literal

from app.storage.db import get_db, init_db
from app.core.auth import get_current_user_token


ItemType = Literal["bid", "vendor", "agency", "contract"]


async def add_to_watchlist(
    item_type: ItemType,
    item_key: str,
    user_token: str | None = None,
    item_label: str | None = None,
    note: str | None = None,
) -> dict:
    """즐겨찾기 추가.

    Args:
        item_type: 'bid'(공고), 'vendor'(업체), 'agency'(발주기관), 'contract'(계약)
        item_key: 공고번호+차수 / 사업자번호 / 기관코드 / 계약번호
        user_token: 사용자 토큰
        item_label: 표시 라벨 (예: "20240315678-00 통합정보화")
        note: 메모

    Returns:
        등록된 watchlist ID + 항목 정보.
    """
    if user_token is None:
        user_token = get_current_user_token()
    await init_db()
    db = await get_db()
    try:
        try:
            cur = await db.execute(
                """INSERT INTO watchlist (user_token, item_type, item_key, item_label, note)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_token, item_type, item_key, item_label, note),
            )
            await db.commit()
            return {
                "watchlist_id": cur.lastrowid,
                "user_token": user_token,
                "item_type": item_type,
                "item_key": item_key,
                "item_label": item_label,
                "note": note,
                "status": "added",
            }
        except Exception as exc:
            # UNIQUE 제약 위반 = 이미 즐겨찾기에 있음
            if "UNIQUE" in str(exc):
                return {
                    "user_token": user_token,
                    "item_type": item_type,
                    "item_key": item_key,
                    "status": "already_exists",
                    "note": "이미 즐겨찾기에 등록된 항목.",
                }
            raise
    finally:
        await db.close()


async def remove_from_watchlist(
    item_type: ItemType | None = None,
    item_key: str | None = None,
    watchlist_id: int | None = None,
    user_token: str | None = None,
) -> dict:
    """즐겨찾기 제거. watchlist_id 또는 (item_type + item_key) 필요."""
    if not watchlist_id and not (item_type and item_key):
        raise ValueError("watchlist_id 또는 (item_type + item_key) 필수")

    if user_token is None:
        user_token = get_current_user_token()
    await init_db()
    db = await get_db()
    try:
        if watchlist_id:
            cur = await db.execute(
                "DELETE FROM watchlist WHERE id=? AND user_token=?",
                (watchlist_id, user_token),
            )
        else:
            cur = await db.execute(
                "DELETE FROM watchlist WHERE item_type=? AND item_key=? AND user_token=?",
                (item_type, item_key, user_token),
            )
        await db.commit()
        return {
            "user_token": user_token,
            "removed_count": cur.rowcount,
            "watchlist_id": watchlist_id,
            "item_type": item_type,
            "item_key": item_key,
        }
    finally:
        await db.close()


async def list_my_watchlist(
    user_token: str | None = None,
    item_type: ItemType | None = None,
) -> dict:
    """내 즐겨찾기 목록.

    Args:
        user_token: 사용자 토큰
        item_type: 'bid'/'vendor'/'agency'/'contract' 필터 (선택)
    """
    if user_token is None:
        user_token = get_current_user_token()
    await init_db()
    db = await get_db()
    try:
        if item_type:
            cur = await db.execute(
                """SELECT id, item_type, item_key, item_label, note, created_at
                   FROM watchlist WHERE user_token=? AND item_type=?
                   ORDER BY created_at DESC""",
                (user_token, item_type),
            )
        else:
            cur = await db.execute(
                """SELECT id, item_type, item_key, item_label, note, created_at
                   FROM watchlist WHERE user_token=?
                   ORDER BY item_type, created_at DESC""",
                (user_token,),
            )
        rows = await cur.fetchall()
        items = [dict(r) for r in rows]

        # 타입별 통계
        type_counts: dict[str, int] = {}
        for item in items:
            t = item["item_type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "user_token": user_token,
            "filter_type": item_type,
            "total_count": len(items),
            "by_type": type_counts,
            "items": items,
        }
    finally:
        await db.close()
