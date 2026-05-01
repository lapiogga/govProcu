"""multi_agency 영역 MCP 도구 — G2B 외 발주기관 통합 검색.

사용자 5/2 22번 우선순위 P1 (중요, 시장 표준).
경쟁사(입찰나라·웰로비즈·아이건설넷) 표준 기능 — 다중 OpenAPI 통합.

본 모듈은 **adapter dispatch 패턴**을 사용한다:
- app/clients/external/ 의 BaseAgencyAdapter 상속 클래스들이 기관별 어댑터
- ADAPTER_REGISTRY로 dispatch (lh / ex / kwater / korail)
- 환경변수에 키 설정 + 어댑터 ACTIVE 상태이면 자동 활성화

도구:
- search_multi_agency_bids: 여러 기관 동시 검색 → 통합 결과
- list_supported_agencies: 지원 기관 + 키 발급 상태
- search_agency_specific: 특정 기관 단독 검색
"""
from __future__ import annotations

from app.tools import bid as bid_tools
from app.clients.external import ADAPTER_REGISTRY, AdapterStatus


# G2B는 이미 통합되어 있어 별도 어댑터 없이 bid_tools로 호출
_G2B_META = {
    "agency": "g2b",
    "name": "나라장터(G2B)",
    "base_url": "apis.data.go.kr/1230000",
    "service_key_env": "G2B_KEY_BID",
    "status": "active",
}


async def list_supported_agencies() -> dict:
    """통합 검색 지원 기관 + 키 발급 상태."""
    agencies = [_G2B_META]
    for adapter_cls in ADAPTER_REGISTRY.values():
        agencies.append(adapter_cls.metadata())

    active = sum(1 for a in agencies if a["status"] == "active")
    pending_key = sum(1 for a in agencies if a["status"] == "pending_key")
    pending_impl = sum(1 for a in agencies if a["status"] == "pending_implementation")

    return {
        "total_agencies": len(agencies),
        "active": active,
        "pending_key": pending_key,
        "pending_implementation": pending_impl,
        "agencies": agencies,
        "note": "환경변수 키 설정 + 어댑터 STATUS=ACTIVE 시 즉시 활성화. data.go.kr에서 'LH 입찰', '도로공사 발주' 등 검색.",
    }


async def search_multi_agency_bids(
    keyword: str | None = None,
    biz_type: str | None = None,
    region: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    agencies: list[str] | None = None,
    limit_per_agency: int = 30,
) -> dict:
    """여러 발주기관 OpenAPI 동시 검색 → 통합 결과.

    Args:
        keyword, biz_type, region, date_from, date_to: 공통 검색 조건
        agencies: 검색 대상 기관 키 목록 (None=모든 active)
        limit_per_agency: 기관별 최대 반환 건수
    """
    target = agencies or ["g2b"] + list(ADAPTER_REGISTRY.keys())

    results: dict = {}
    total_count = 0
    skipped: list[dict] = []

    for agency_key in target:
        if agency_key == "g2b":
            try:
                r = await bid_tools.search_bid_notices(
                    keyword=keyword,
                    biz_type=biz_type,
                    region=region,
                    date_from=date_from,
                    date_to=date_to,
                    limit=limit_per_agency,
                )
                results["g2b"] = {
                    "name": _G2B_META["name"],
                    "match_count": len(r.get("items", [])),
                    "items": r.get("items", []),
                }
                total_count += len(r.get("items", []))
            except Exception as exc:
                results["g2b"] = {"name": _G2B_META["name"], "error": str(exc)[:200]}
            continue

        adapter_cls = ADAPTER_REGISTRY.get(agency_key)
        if not adapter_cls:
            skipped.append({"agency": agency_key, "reason": "unknown"})
            continue

        status = adapter_cls.current_status()
        if status != AdapterStatus.ACTIVE:
            skipped.append({
                "agency": agency_key,
                "name": adapter_cls.AGENCY_NAME,
                "status": status.value,
                "service_key_env": adapter_cls.SERVICE_KEY_ENV,
            })
            continue

        try:
            adapter = adapter_cls()
            r = await adapter.search_bids(
                keyword=keyword,
                biz_type=biz_type,
                date_from=date_from,
                date_to=date_to,
                limit=limit_per_agency,
            )
            results[agency_key] = {
                "name": adapter_cls.AGENCY_NAME,
                "match_count": len(r.get("items", [])),
                "items": r.get("items", []),
            }
            total_count += len(r.get("items", []))
        except Exception as exc:
            results[agency_key] = {
                "name": adapter_cls.AGENCY_NAME,
                "error": str(exc)[:200],
            }

    return {
        "search_criteria": {
            "keyword": keyword,
            "biz_type": biz_type,
            "region": region,
            "date_range": [date_from, date_to],
        },
        "agencies_searched": target,
        "agencies_skipped": skipped,
        "total_match_count": total_count,
        "results_by_agency": results,
        "note": "비활성 기관은 키 발급(SERVICE_KEY_ENV) 또는 어댑터 구현 후 활성화.",
    }


async def search_agency_specific(
    agency: str,
    keyword: str | None = None,
    biz_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict:
    """특정 기관 단독 검색."""
    if agency == "g2b":
        return await bid_tools.search_bid_notices(
            keyword=keyword,
            biz_type=biz_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

    adapter_cls = ADAPTER_REGISTRY.get(agency)
    if not adapter_cls:
        return {
            "status": "unknown_agency",
            "agency": agency,
            "supported": ["g2b"] + list(ADAPTER_REGISTRY.keys()),
        }

    status = adapter_cls.current_status()
    if status != AdapterStatus.ACTIVE:
        return {
            "status": status.value,
            "agency": agency,
            "name": adapter_cls.AGENCY_NAME,
            "service_key_env": adapter_cls.SERVICE_KEY_ENV,
            "note": "키 발급 + 어댑터 ACTIVE 처리 후 사용 가능.",
        }

    adapter = adapter_cls()
    return await adapter.search_bids(
        keyword=keyword,
        biz_type=biz_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
