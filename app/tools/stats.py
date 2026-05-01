"""통계 영역 MCP 도구 — 공공조달통계서비스.

G2B_KEY_STATS 사용. 발주기관·업종·기간 기준 조달 통계 조회.

도구 매트릭스 (REPLAN.md v2):
- get_procurement_stats: 기간별 조달 통계 (총건·총액)
- list_top_vendors_by_period: 상위 낙찰업체
- agency_procurement_volume: 발주기관별 조달 규모
"""
from __future__ import annotations


async def get_procurement_stats(
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    inst_code: str | None = None,
) -> dict:
    """기간/업종/기관 기준 조달 통계 조회 (스텁)."""
    return {
        "status": "not_implemented",
        "domain": "stats",
        "tool": "get_procurement_stats",
        "note": "공공조달통계서비스 매핑 진행 중",
    }


async def list_top_vendors_by_period(
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 20,
) -> dict:
    """기간 내 낙찰 합계 기준 상위 업체 목록 (스텁)."""
    return {
        "status": "not_implemented",
        "domain": "stats",
        "tool": "list_top_vendors_by_period",
        "items": [],
        "note": "공공조달통계서비스 매핑 진행 중",
    }


async def agency_procurement_volume(
    inst_code: str | None = None,
    inst_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """발주기관별 조달 규모(입찰·계약 합계) 조회 (스텁)."""
    return {
        "status": "not_implemented",
        "domain": "stats",
        "tool": "agency_procurement_volume",
        "note": "공공조달통계서비스 매핑 진행 중",
    }


async def placeholder_stats() -> dict:
    """stats 영역 도구 자리표시자. 호환성을 위해 유지."""
    return {"status": "not_implemented", "domain": "stats"}
