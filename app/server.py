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

# 구조화 로깅 셋업
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
        "예: '최근 한 달 정보화 용역 공고 알려줘', '2026년 1월 ~ 4월 인공지능 키워드 공고 추세'"
    ),
)

# === 도구 등록 ===
# M3 (PoC) 단계: 핵심 1개 도구만 등록
mcp.tool()(bid_tools.search_bid_notices)

# M5 (MVP) 단계에서 추가 등록 예정:
# mcp.tool()(bid_tools.get_bid_notice_detail)
# mcp.tool()(bid_tools.list_pre_specifications)
# mcp.tool()(award_tools.get_award_result)
# ...


def main():
    """CLI 엔트리포인트."""
    log.info("starting", host=settings.server_host, port=settings.server_port)
    mcp.run(transport="http", host=settings.server_host, port=settings.server_port)


# uvicorn에서 직접 import할 ASGI 앱
app = mcp.streamable_http_app()


if __name__ == "__main__":
    main()
