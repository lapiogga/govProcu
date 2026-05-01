"""사용자 Bearer 토큰 인증."""
from __future__ import annotations
from app.config import settings


class AuthError(Exception):
    pass


def verify_token(token: str | None) -> None:
    """제공된 토큰이 허용 목록에 있는지 검증."""
    if not token:
        raise AuthError("missing_token")
    if not settings.allowed_tokens:
        # 토큰 미설정 시 개발모드: 통과 (운영에서는 반드시 설정)
        return
    if token not in settings.allowed_tokens:
        raise AuthError("invalid_token")
