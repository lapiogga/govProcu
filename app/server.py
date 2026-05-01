"""FastMCP 서버 진입점 (HTTP/SSE 모드).

실행:
    uvicorn app.server:app --host 0.0.0.0 --port 8080
또는:
    python -m app.server
"""
from __future__ import annotations
import logging
import structlog
from fastmcp import FastMCP
from app.config import settings
from app.tools import bid as bid_tools
from app.tools import award as award_tools
from app.tools import contract as contract_tools
from app.tools import stats as stats_tools
from app.tools import user as user_tools
from app.tools import vendor as vendor_tools

# 구조화 로깅
logging.basicConfig(level=settings.log_level)
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)
log = structlog.get_logger()

# FastMCP 인스턴스
mcp = FastMCP(
    name="GovProcu",
    instructions=(
        "나라장터(G2B) OpenAPI를 LLM Tool로 노출하는 MCP 서버입니다. "
        "한국어 자연어 질의를 권장합니다. "
        "예: '최근 한 달 정보화 용역 공고 알려줘'"
    ),
)

# === 도구 등록 ===
# bid 영역
mcp.tool()(bid_tools.search_bid_notices)
mcp.tool()(bid_tools.get_bid_notice_detail)
mcp.tool()(bid_tools.list_pre_specifications)
# award 영역 (M5 단계 스텁)
mcp.tool()(award_tools.placeholder_award)
# contract 영역 (M5 단계 스텁)
mcp.tool()(contract_tools.get_contract_process)
mcp.tool()(contract_tools.search_contracts)
# stats 영역 (스텁)
mcp.tool()(stats_tools.placeholder_stats)
# user 영역 (스텁)
mcp.tool()(user_tools.placeholder_user)
# vendor 영역 (스텁)
mcp.tool()(vendor_tools.placeholder_vendor)


def _get_asgi_app():
    """FastMCP 버전별 ASGI app 추출 (호환성 처리)."""
    # FastMCP 2.x 신규 API
    if hasattr(mcp, "http_app"):
        return mcp.http_app()
    # FastMCP 1.x 구 API
    if hasattr(mcp, "streamable_http_app"):
        return mcp.streamable_http_app()
    # 더 오래된 fallback
    if hasattr(mcp, "sse_app"):
        return mcp.sse_app()
    raise RuntimeError(
        "FastMCP 버전 호환 안 됨. http_app/streamable_http_app/sse_app 메서드 모두 없음. "
        "fastmcp 패키지를 업데이트하세요: pip install -U fastmcp"
    )


def main():
    """CLI 엔트리포인트 — uvicorn 없이 직접 실행."""
    log.info("starting", host=settings.server_host, port=settings.server_port)
    # 최신 FastMCP는 transport="streamable-http" 또는 "http" 지원
    try:
        mcp.run(transport="http", host=settings.server_host, port=settings.server_port)
    except (TypeError, ValueError):
        # 구 버전: transport="streamable-http"
        mcp.run(transport="streamable-http", host=settings.server_host, port=settings.server_port)


# uvicorn에서 직접 import할 ASGI 앱
app = _get_asgi_app()


if __name__ == "__main__":
    main()
