"""카카오톡 알림톡 (placeholder).

운영 시 카카오 비즈니스 채널 + 발송 대행사(NHN Cloud / Aligo / Bizppurio 등) 키 필요.
환경변수:
    KAKAO_API_KEY, KAKAO_SENDER_ID, KAKAO_TEMPLATE_CODE
"""
from __future__ import annotations
import os


async def send_kakao(channel_id: str, text: str) -> None:
    """카카오톡 발송 (현재 placeholder)."""
    api_key = os.getenv("KAKAO_API_KEY")
    if not api_key:
        raise RuntimeError("KAKAO_API_KEY 미설정 — 알림톡 발송 대행사 연동 필요")

    # TODO: NHN Cloud Notification 또는 Aligo API 호출
    # 현재는 noop (인증·템플릿 등록 단계 필요)
    raise NotImplementedError(
        "카카오톡 알림톡 발송은 비즈니스 채널 + 템플릿 등록 + 대행사 키 필요. "
        "당분간 SLACK_WEBHOOK_URL 또는 SMTP 사용 권장."
    )
