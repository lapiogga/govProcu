"""alerts 영역 MCP 도구 — 키워드 구독 + 다이제스트.

사용자 5/2 22번 우선순위 P0 (필수, 시장 진입 자격).
경쟁사(인포21C·비드프로·비드큐·웰로비즈 등) 모두 보유한 표준 기능.

도구:
- subscribe_keyword_alerts: 키워드/기관/업종/금액대 구독 등록
- unsubscribe_keyword_alerts: 구독 해제
- list_my_subscriptions: 내 구독 목록
- daily_bid_digest: 오늘 신규공고 다이제스트 (구독 매칭)
- weekly_bid_digest: 지난 7일 요약

영속 저장소: app.storage.db (SQLite, subscriptions 테이블)
알림 디스패처: 현재 placeholder. 운영 단계에서 이메일/카카오톡/슬랙 추가.
"""
from __future__ import annotations
from typing import Any

from app.storage.db import get_db, init_db
from app.tools import bid as bid_tools
from app.core.auth import get_current_user_token


async def subscribe_keyword_alerts(
    keyword: str,
    user_token: str | None = None,
    biz_type: str | None = None,
    inst_name: str | None = None,
    region: str | None = None,
    min_amount: int | None = None,
    max_amount: int | None = None,
    notify_email: str | None = None,
    notify_kakao: str | None = None,
) -> dict:
    """키워드/조건 기반 입찰 알림 구독.

    Args:
        keyword: 공고명 부분일치 키워드 (필수)
        user_token: 사용자 토큰 (기본 "default" - 운영 시 인증 미들웨어가 주입)
        biz_type: 업종 ('공사'/'용역'/'물품')
        inst_name: 발주기관명 부분일치
        region: 지역 (시도명)
        min_amount, max_amount: 추정가 범위 (원 단위)
        notify_email: 알림 이메일
        notify_kakao: 카카오톡 채널 ID 등

    Returns:
        등록된 구독 ID + 매칭 룰 요약.
    """
    if user_token is None:
        user_token = get_current_user_token()
    await init_db()
    db = await get_db()
    try:
        cur = await db.execute(
            """
            INSERT OR REPLACE INTO subscriptions
            (user_token, keyword, biz_type, inst_name, region, min_amount, max_amount,
             notify_email, notify_kakao, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (user_token, keyword, biz_type, inst_name, region, min_amount, max_amount,
             notify_email, notify_kakao),
        )
        await db.commit()
        return {
            "subscription_id": cur.lastrowid,
            "user_token": user_token,
            "rule": {
                "keyword": keyword,
                "biz_type": biz_type,
                "inst_name": inst_name,
                "region": region,
                "amount_range": [min_amount, max_amount],
            },
            "notify": {"email": notify_email, "kakao": notify_kakao},
            "status": "active",
            "note": "다음 daily_bid_digest 실행 시부터 매칭 시작.",
        }
    finally:
        await db.close()


async def unsubscribe_keyword_alerts(
    subscription_id: int | None = None,
    keyword: str | None = None,
    user_token: str = "default",
) -> dict:
    """구독 해제. subscription_id 또는 keyword 중 하나 필수."""
    if not (subscription_id or keyword):
        raise ValueError("subscription_id 또는 keyword 필수")

    await init_db()
    db = await get_db()
    try:
        if subscription_id:
            cur = await db.execute(
                "UPDATE subscriptions SET active=0 WHERE id=? AND user_token=?",
                (subscription_id, user_token),
            )
        else:
            cur = await db.execute(
                "UPDATE subscriptions SET active=0 WHERE keyword=? AND user_token=?",
                (keyword, user_token),
            )
        await db.commit()
        return {
            "user_token": user_token,
            "deactivated_count": cur.rowcount,
            "subscription_id": subscription_id,
            "keyword": keyword,
        }
    finally:
        await db.close()


async def list_my_subscriptions(user_token: str = "default") -> dict:
    """내 활성 구독 목록 + 매칭 룰."""
    await init_db()
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT id, keyword, biz_type, inst_name, region, min_amount, max_amount,
                   notify_email, notify_kakao, created_at
            FROM subscriptions
            WHERE user_token=? AND active=1
            ORDER BY created_at DESC
            """,
            (user_token,),
        )
        rows = await cur.fetchall()
        items = [dict(r) for r in rows]
        return {
            "user_token": user_token,
            "subscription_count": len(items),
            "items": items,
        }
    finally:
        await db.close()


async def daily_bid_digest(
    user_token: str = "default",
    date_target: str | None = None,
) -> dict:
    """사용자 구독 룰에 매칭되는 오늘 신규 공고 다이제스트.

    각 구독별로 search_bid_notices 호출 → 매칭 결과 집계.
    실제 발송은 디스패처(이메일/카톡)에 위임 — 현재 placeholder.

    Args:
        user_token: 대상 사용자
        date_target: 조회 대상일 (YYYYMMDD, 기본 오늘)
    """
    from datetime import datetime
    target = date_target or datetime.now().strftime("%Y%m%d")

    await init_db()
    db = await get_db()
    try:
        cur = await db.execute(
            """SELECT id, keyword, biz_type, inst_name, region, min_amount, max_amount
               FROM subscriptions WHERE user_token=? AND active=1""",
            (user_token,),
        )
        subs = [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()

    if not subs:
        return {
            "user_token": user_token,
            "date": target,
            "subscription_count": 0,
            "matches": [],
            "note": "활성 구독 없음. subscribe_keyword_alerts 먼저 호출.",
        }

    results: list[dict[str, Any]] = []
    total_matches = 0

    for sub in subs:
        try:
            search_result = await bid_tools.search_bid_notices(
                keyword=sub["keyword"],
                biz_type=sub.get("biz_type"),
                region=sub.get("region"),
                inst_name=sub.get("inst_name"),
                date_from=target,
                date_to=target,
                limit=50,
            )
        except Exception as exc:
            results.append({
                "subscription_id": sub["id"],
                "keyword": sub["keyword"],
                "error": str(exc)[:200],
            })
            continue

        items = search_result.get("items", [])

        # 금액대 클라이언트 필터
        if sub.get("min_amount") or sub.get("max_amount"):
            mn = sub.get("min_amount") or 0
            mx = sub.get("max_amount") or 10**18
            items = [
                x for x in items
                if mn <= (x.get("estimated_price") or 0) <= mx
            ]

        results.append({
            "subscription_id": sub["id"],
            "keyword": sub["keyword"],
            "match_count": len(items),
            "items": items[:10],  # digest는 상위 10건만
        })
        total_matches += len(items)

    # 발송 이력 기록
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO digest_log (user_token, digest_date, digest_type, item_count)
               VALUES (?, ?, 'daily', ?)""",
            (user_token, target, total_matches),
        )
        await db.commit()
    finally:
        await db.close()

    return {
        "user_token": user_token,
        "date": target,
        "subscription_count": len(subs),
        "total_match_count": total_matches,
        "results": results,
        "dispatch_status": "logged_only — 실 발송(이메일/카톡)은 디스패처 인프라 필요",
    }


async def weekly_bid_digest(
    user_token: str = "default",
    date_to: str | None = None,
) -> dict:
    """지난 7일 신규 공고 다이제스트."""
    from datetime import datetime, timedelta
    end_date = datetime.strptime(date_to, "%Y%m%d") if date_to else datetime.now()
    start_date = end_date - timedelta(days=7)

    await init_db()
    db = await get_db()
    try:
        cur = await db.execute(
            """SELECT id, keyword, biz_type, inst_name, region, min_amount, max_amount
               FROM subscriptions WHERE user_token=? AND active=1""",
            (user_token,),
        )
        subs = [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()

    if not subs:
        return {
            "user_token": user_token,
            "date_from": start_date.strftime("%Y%m%d"),
            "date_to": end_date.strftime("%Y%m%d"),
            "subscription_count": 0,
            "matches": [],
        }

    results: list[dict[str, Any]] = []
    total = 0
    for sub in subs:
        try:
            r = await bid_tools.search_bid_notices(
                keyword=sub["keyword"],
                biz_type=sub.get("biz_type"),
                region=sub.get("region"),
                inst_name=sub.get("inst_name"),
                date_from=start_date.strftime("%Y%m%d"),
                date_to=end_date.strftime("%Y%m%d"),
                limit=100,
            )
            items = r.get("items", [])
            results.append({
                "subscription_id": sub["id"],
                "keyword": sub["keyword"],
                "match_count": len(items),
                "items": items[:20],
            })
            total += len(items)
        except Exception as exc:
            results.append({
                "subscription_id": sub["id"],
                "keyword": sub["keyword"],
                "error": str(exc)[:200],
            })

    return {
        "user_token": user_token,
        "date_from": start_date.strftime("%Y%m%d"),
        "date_to": end_date.strftime("%Y%m%d"),
        "subscription_count": len(subs),
        "total_match_count": total,
        "results": results,
    }
