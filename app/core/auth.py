"""사용자 Bearer 토큰 인증 + ContextVar로 user_token 전파.

NEXT4-5: alerts/watchlist 도구가 user_token 자동 추출 가능.

Bearer 추출 흐름:
1. ASGI 미들웨어가 Authorization 헤더 → ContextVar 주입
2. 각 도구는 get_current_user_token() 으로 조회
3. 미인증 호출은 'default' fallback (개발 모드)
"""
from __future__ import annotations
from contextvars import ContextVar

from app.config import settings


class AuthError(Exception):
    pass


# 현재 요청의 user_token (ContextVar로 비동기 안전)
current_user_token: ContextVar[str] = ContextVar("user_token", default="default")


def verify_token(token: str | None) -> None:
    """제공된 토큰이 허용 목록에 있는지 검증."""
    if not token:
        raise AuthError("missing_token")
    if not settings.allowed_tokens:
        # 토큰 미설정 시 개발모드: 통과
        return
    if token not in settings.allowed_tokens:
        raise AuthError("invalid_token")


def get_current_user_token() -> str:
    """현재 요청의 user_token 조회 (ContextVar)."""
    return current_user_token.get()


def parse_bearer(auth_header: str | None) -> str:
    """Authorization 헤더 → token. 'Bearer xxx' 또는 raw 토큰 모두 허용."""
    if not auth_header:
        return ""
    parts = auth_header.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    if len(parts) == 1:
        return parts[0]
    return ""


class AuthMiddleware:
    """ASGI 미들웨어 — Authorization 헤더 → ContextVar 주입.

    설치:
        from starlette.applications import Starlette
        app.add_middleware(AuthMiddleware)

    또는 FastMCP의 ASGI app 위에 wrap.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # 헤더에서 Authorization 추출
        token = "default"
        for k, v in scope.get("headers", []):
            if k == b"authorization":
                bearer = parse_bearer(v.decode("utf-8", errors="ignore"))
                if bearer:
                    try:
                        verify_token(bearer)
                        token = bearer
                    except AuthError:
                        # 무효 토큰 — 401 응답
                        if scope["type"] == "http":
                            await send({
                                "type": "http.response.start",
                                "status": 401,
                                "headers": [(b"content-type", b"application/json")],
                            })
                            await send({
                                "type": "http.response.body",
                                "body": b'{"error":"invalid_token"}',
                            })
                            return
                break

        # ContextVar에 주입 후 app 실행
        token_ref = current_user_token.set(token)
        try:
            await self.app(scope, receive, send)
        finally:
            current_user_token.reset(token_ref)
