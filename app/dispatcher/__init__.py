"""알림 디스패처 — email / slack / kakao 통합.

NEXT6-2: alerts.daily_bid_digest 결과를 외부 채널로 발송.
환경변수가 설정된 채널만 활성화.
"""
from __future__ import annotations
import os

from app.dispatcher.email import send_email
from app.dispatcher.slack import send_slack
from app.dispatcher.kakao import send_kakao


__all__ = ["dispatch_digest", "send_email", "send_slack", "send_kakao"]


async def dispatch_digest(
    user_token: str,
    digest: dict,
    notify_email: str | None = None,
    notify_slack: str | None = None,
    notify_kakao: str | None = None,
) -> dict:
    """다이제스트 결과 → 사용자 채널 발송. {channel: status}"""
    body = _format_digest(digest)
    subject = f"[GovProcu] 입찰 다이제스트 — {digest.get('date', '')}"
    results: dict[str, str] = {}

    if notify_email and os.getenv("SMTP_HOST"):
        try:
            await send_email(notify_email, subject, body)
            results["email"] = "sent"
        except Exception as exc:
            results["email"] = f"error: {str(exc)[:100]}"
    else:
        results["email"] = "skipped"

    if notify_slack or os.getenv("SLACK_WEBHOOK_URL"):
        try:
            await send_slack(notify_slack, body)
            results["slack"] = "sent"
        except Exception as exc:
            results["slack"] = f"error: {str(exc)[:100]}"
    else:
        results["slack"] = "skipped"

    if notify_kakao and os.getenv("KAKAO_API_KEY"):
        try:
            await send_kakao(notify_kakao, body)
            results["kakao"] = "sent"
        except Exception as exc:
            results["kakao"] = f"error: {str(exc)[:100]}"
    else:
        results["kakao"] = "skipped"

    return results


def _format_digest(digest: dict) -> str:
    date = digest.get("date", "")
    total = digest.get("total_match_count", 0)
    sub_count = digest.get("subscription_count", 0)
    results = digest.get("results", [])
    lines = [
        f"GovProcu 입찰 다이제스트 — {date}",
        f"활성 구독: {sub_count} · 매칭 공고: {total}건",
        "",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"[키워드: {r['keyword']}] 오류: {r['error']}")
            continue
        match_count = r.get("match_count", 0)
        if match_count == 0:
            continue
        lines.append(f"## {r['keyword']} ({match_count}건)")
        for item in r.get("items", [])[:5]:
            t = item.get("title", "")
            inst = item.get("inst_name", "")
            price = item.get("estimated_price") or 0
            lines.append(f"  - {t} / {inst} / {price:,}원")
        if match_count > 5:
            lines.append(f"  ... 외 {match_count - 5}건")
        lines.append("")
    return "\n".join(lines)
