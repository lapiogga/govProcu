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
from app.tools import analytics as analytics_tools
from app.tools import workflow as workflow_tools
from app.tools import lookup as lookup_tools

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
# bid 영역 (입찰공고 + 사전규격)
mcp.tool()(bid_tools.search_bid_notices)
mcp.tool()(bid_tools.get_bid_notice_detail)
mcp.tool()(bid_tools.list_pre_specifications)
mcp.tool()(bid_tools.get_pre_specification_detail)
# award 영역 (개찰/낙찰/응찰업체)
mcp.tool()(award_tools.list_bid_openings)
mcp.tool()(award_tools.search_awards)
mcp.tool()(award_tools.get_award_detail)
mcp.tool()(award_tools.search_awards_by_vendor)
mcp.tool()(award_tools.list_bid_participants)
mcp.tool()(award_tools.placeholder_award)
# contract 영역 (계약과정통합공개)
mcp.tool()(contract_tools.get_contract_process)
mcp.tool()(contract_tools.search_contracts)
mcp.tool()(contract_tools.list_contract_changes)
mcp.tool()(contract_tools.get_contract_detail)
# stats 영역 (공공조달통계)
mcp.tool()(stats_tools.get_procurement_stats)
mcp.tool()(stats_tools.list_top_vendors_by_period)
mcp.tool()(stats_tools.agency_procurement_volume)
mcp.tool()(stats_tools.industry_procurement_stats)
mcp.tool()(stats_tools.placeholder_stats)
# user 영역 (스텁)
mcp.tool()(user_tools.placeholder_user)
# vendor 영역 (응찰업체 + NTS + V1~V3 vendor-by-vendor)
mcp.tool()(vendor_tools.search_bid_participants)
mcp.tool()(vendor_tools.get_evaluation_scores)
mcp.tool()(vendor_tools.check_business_status)
mcp.tool()(vendor_tools.verify_business_info)
mcp.tool()(vendor_tools.search_bids_by_vendor)
mcp.tool()(vendor_tools.search_participations_by_vendor)
mcp.tool()(vendor_tools.search_openings_by_vendor)
mcp.tool()(vendor_tools.placeholder_vendor)
# analytics 영역 (Tier 2.5 — 동종업체·경쟁사·유사사업·업종 동향)
mcp.tool()(analytics_tools.find_similar_vendors)
mcp.tool()(analytics_tools.find_similar_bids)
mcp.tool()(analytics_tools.industry_trend)
mcp.tool()(analytics_tools.peer_analysis)
mcp.tool()(analytics_tools.market_share)
# workflow 영역 (Tier 2 — 통합 워크플로우)
mcp.tool()(workflow_tools.trace_bid_lifecycle)
mcp.tool()(workflow_tools.vendor_profile)
mcp.tool()(workflow_tools.agency_bid_summary)
mcp.tool()(workflow_tools.competitor_analysis)
mcp.tool()(workflow_tools.agency_procurement_history)
# lookup 영역 (Relational Key 기반 cross-lookup — 사용자 5/2 통찰)
mcp.tool()(lookup_tools.lookup_by_bid_no)
mcp.tool()(lookup_tools.lookup_by_inst_code)
mcp.tool()(lookup_tools.lookup_by_biz_no)
mcp.tool()(lookup_tools.lookup_by_contract_no)


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


# uvicorn에서 ASGI app 노출
app = _get_asgi_app()


if __name__ == "__main__":
    main()
