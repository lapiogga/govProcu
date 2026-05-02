"""카카오톡 알림톡 — NHN Cloud Notification 우선 어댑터.

발송 대행사 비교: docs/NOTIFICATIONS.md §4 참조.
환경변수 (NHN Cloud 기준):
    KAKAO_API_KEY     — NHN Cloud appKey
    KAKAO_SECRET_KEY  — NHN Cloud secretKey (헤더 X-Secret-Key)
    KAKAO_SENDER_ID   — 발신 프로필 키 (예: '@govprocu')
    KAKAO_TEMPLATE_CODE — 카카오 검수 통과한 템플릿 코드
    KAKAO_PROVIDER    — 'nhn'(default) | 'aligo' | 'bizppurio'

비즈니스 채널 + 템플릿 등록 + 대행사 키 모두 갖춘 후 동작. 미설정 시 RuntimeError.
"""
from __future__ import annotations
import os
import re
from typing import Any


_VAR_PATTERN = re.compile(r"#\{([^}]+)\}")


def render_template(template_text: str, variables: dict[str, Any]) -> str:
    """카카오 알림톡 변수 치환 헬퍼.

    템플릿 형식: '안녕하세요 #{name}님, #{count}건 매칭됐습니다.'
    """
    def _sub(m: re.Match) -> str:
        key = m.group(1).strip()
        return str(variables.get(key, m.group(0)))
    return _VAR_PATTERN.sub(_sub, template_text)


async def send_kakao(
    recipient_phone: str,
    text: str,
    variables: dict[str, Any] | None = None,
) -> None:
    """카카오톡 알림톡 발송.

    Args:
        recipient_phone: 수신자 휴대폰 번호 (010xxxxxxxx 형태)
        text: 발송 본문 (템플릿 변수가 이미 치환된 최종 문자열) 또는 템플릿 변수 미치환 원문
        variables: text가 템플릿 원문일 때 치환에 쓸 dict
    """
    api_key = os.getenv("KAKAO_API_KEY")
    if not api_key:
        raise RuntimeError(
            "KAKAO_API_KEY 미설정 — 알림톡 발송 대행사 연동 필요. "
            "docs/NOTIFICATIONS.md §4 참조."
        )

    sender = os.getenv("KAKAO_SENDER_ID")
    template_code = os.getenv("KAKAO_TEMPLATE_CODE")
    if not sender or not template_code:
        raise RuntimeError(
            "KAKAO_SENDER_ID + KAKAO_TEMPLATE_CODE 환경변수 모두 필요."
        )

    final_text = render_template(text, variables) if variables else text
    provider = os.getenv("KAKAO_PROVIDER", "nhn").lower()

    if provider == "nhn":
        await _send_nhn_cloud(
            api_key=api_key,
            secret_key=os.getenv("KAKAO_SECRET_KEY", ""),
            sender_id=sender,
            template_code=template_code,
            recipient_phone=recipient_phone,
            text=final_text,
        )
    else:
        raise NotImplementedError(
            f"KAKAO_PROVIDER={provider} 미구현. NHN Cloud(nhn) 우선 지원. "
            "Aligo/Bizppurio 추가 시 본 함수 분기 추가."
        )


async def _send_nhn_cloud(
    *,
    api_key: str,
    secret_key: str,
    sender_id: str,
    template_code: str,
    recipient_phone: str,
    text: str,
) -> None:
    """NHN Cloud Notification — 알림톡 발송 API.

    참조 (운영 시 검증):
        POST https://api-alimtalk.cloud.toast.com/alimtalk/v2.3/appkeys/{appkey}/messages
        Header: X-Secret-Key: {secretKey}
        Body: { senderKey, templateCode, recipientList: [{recipientNo, content}] }
    """
    try:
        import httpx
    except ImportError:
        raise RuntimeError("httpx 미설치 — pip install httpx")

    base = "https://api-alimtalk.cloud.toast.com/alimtalk/v2.3"
    url = f"{base}/appkeys/{api_key}/messages"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
    }
    if secret_key:
        headers["X-Secret-Key"] = secret_key

    payload = {
        "senderKey": sender_id,
        "templateCode": template_code,
        "recipientList": [
            {
                "recipientNo": recipient_phone.replace("-", ""),
                "content": text[:1000],  # 알림톡 본문 1000자 한도
            }
        ],
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, headers=headers, json=payload)

    if resp.status_code >= 400:
        raise RuntimeError(
            f"NHN Cloud 알림톡 발송 실패 — HTTP {resp.status_code}: {resp.text[:300]}"
        )

    body = resp.json() if resp.content else {}
    header = body.get("header", {})
    if not header.get("isSuccessful", False):
        raise RuntimeError(
            f"NHN Cloud 알림톡 응답 실패 — code={header.get('resultCode')}: "
            f"{header.get('resultMessage')}"
        )
