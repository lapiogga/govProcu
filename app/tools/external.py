"""외부 발주기관 OpenAPI MCP 도구.

5/2 N25 — KWater 어댑터를 자연어 도구로 노출. 향후 다른 외부 어댑터(EX/LH/Korail)도
같은 모듈에서 등록.

도구 목록:
    search_kwater_contracts(search_dt, limit) -> 한국수자원공사 공사 계약 검색
    list_external_adapters() -> 등록된 외부 어댑터 메타데이터
"""
from __future__ import annotations
from typing import Any

from app.clients.external.kwater import KWaterAdapter
from app.clients.external.lh import LHAdapter
from app.clients.external.ex import ExAdapter
from app.clients.external.korail import KorailAdapter


_KWATER = KWaterAdapter()


async def search_kwater_contracts(
    search_dt: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """한국수자원공사(K-water) 전자조달 공사 계약 정보 검색.

    K-water 는 data.go.kr 에 입찰공고 미공개, 계약 결과만 공개.
    월 단위 (searchDt YYYYMM) 검색만 지원. 키워드/기관 필터 미지원.

    Args:
        search_dt: 검색 연월 YYYYMM (예: '202205'). 미지정 시 어댑터 default.
        limit: 페이지당 row 수 (default 20, max 1000)

    Returns:
        items: [{contract_no, contract_date, title, inst_name, dept_name,
                 biz_type, winner_name, contract_method, limit_method,
                 contract_amount, period_from, period_to}, ...]
        total_count: 해당 월 전체 건수
        agency: 'kwater'
        endpoint: 호출 URL
        status: 'active' / 'pending_key' / 'pending_implementation'
    """
    return await _KWATER.search_contracts(search_dt=search_dt, limit=limit)


def list_external_adapters() -> dict[str, Any]:
    """등록된 외부 발주기관 어댑터 메타데이터.

    각 어댑터의 발주기관, base URL, 상태(active/pending_key/pending_implementation),
    환경변수 이름을 반환.
    """
    adapters = [
        KWaterAdapter,
        LHAdapter,
        ExAdapter,
        KorailAdapter,
    ]
    return {
        "items": [a.metadata() for a in adapters],
        "active_count": sum(1 for a in adapters if a.metadata()["status"] == "active"),
        "total": len(adapters),
    }
