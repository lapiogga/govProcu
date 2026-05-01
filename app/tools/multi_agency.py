"""multi_agency 영역 MCP 도구 — G2B 외 발주기관 통합 검색.

사용자 5/2 22번 우선순위 P1 (중요, 시장 표준).
경쟁사(입찰나라·웰로비즈·아이건설넷) 표준 기능 — 다중 OpenAPI 통합.

대상 발주기관 (확장 가능):
- LH (한국토지주택공사) — lh.or.kr 자체 OpenAPI
- 한국도로공사 — ex.co.kr
- 한국수자원공사 — kwater.or.kr
- 한국철도공사(코레일) — korail.com
- 한국마사회 — kra.co.kr
- 국방조달본부 — dapa.go.kr

본 모듈은 통합 인터페이스 + G2B fallback 골격이다.
각 기관 키 발급 후 기관별 어댑터(adapters/) 추가하여 활성화.

도구:
- search_multi_agency_bids: 여러 기관 동시 검색 → 통합 결과
- list_supported_agencies: 지원 기관 목록 + 키 발급 상태
- search_agency_specific: 특정 기관 단독 검색 (어댑터 호출)
"""
from __future__ import annotations

from app.tools import bid as bid_tools


# === 지원 기관 카탈로그 ===
_SUPPORTED_AGENCIES = {
    "g2b": {
        "name": "나라장터(G2B)",
        "url": "apis.data.go.kr/1230000",
        "scope": "조달청 통합 (대부분 발주기관)",
        "api_key_env": "G2B_KEY_BID",
        "status": "active",  # G2B는 이미 통합됨
    },
    "lh": {
        "name": "한국토지주택공사(LH)",
        "url": "apis.data.go.kr (LH 별도 OpenAPI 필요)",
        "scope": "주거·도시개발 입찰",
        "api_key_env": "LH_API_KEY (미발급)",
        "status": "pending_key",
    },
    "ex": {
        "name": "한국도로공사",
        "url": "apis.data.go.kr (도로공사 OpenAPI)",
        "scope": "도로 건설·유지보수",
        "api_key_env": "EX_API_KEY (미발급)",
        "status": "pending_key",
    },
    "kwater": {
        "name": "한국수자원공사",
        "url": "data.kwater.or.kr OpenAPI",
        "scope": "수자원·댐 관련",
        "api_key_env": "KWATER_API_KEY (미발급)",
        "status": "pending_key",
    },
    "korail": {
        "name": "한국철도공사(코레일)",
        "url": "info.korail.com (별도)",
        "scope": "철도 건설·차량",
        "api_key_env": "KORAIL_API_KEY (미발급)",
        "status": "pending_key",
    },
    "kra": {
        "name": "한국마사회",
        "url": "별도",
        "scope": "마사회 자체 발주",
        "api_key_env": "KRA_API_KEY (미발급)",
        "status": "pending_key",
    },
    "dapa": {
        "name": "방위사업청",
        "url": "별도",
        "scope": "국방 조달",
        "api_key_env": "DAPA_API_KEY (미발급)",
        "status": "pending_key",
    },
}


async def list_supported_agencies() -> dict:
    """통합 검색 지원 기관 목록 + 키 발급 상태."""
    active = sum(1 for a in _SUPPORTED_AGENCIES.values() if a["status"] == "active")
    pending = sum(1 for a in _SUPPORTED_AGENCIES.values() if a["status"] == "pending_key")

    return {
        "total_agencies": len(_SUPPORTED_AGENCIES),
        "active": active,
        "pending_key": pending,
        "agencies": _SUPPORTED_AGENCIES,
        "note": "현재 G2B 통합만 활성화. 다른 기관은 별도 키 발급 필요. data.go.kr에서 'LH 입찰', '도로공사 발주' 등 검색.",
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

    Returns:
        agency별 결과 + 통합 합계.
    """
    target = agencies or [k for k, a in _SUPPORTED_AGENCIES.items() if a["status"] == "active"]

    results: dict = {}
    total_count = 0
    skipped: list[dict] = []

    for agency_key in target:
        agency_info = _SUPPORTED_AGENCIES.get(agency_key)
        if not agency_info:
            skipped.append({"agency": agency_key, "reason": "unknown"})
            continue

        if agency_info["status"] == "pending_key":
            skipped.append({
                "agency": agency_key,
                "name": agency_info["name"],
                "reason": "API 키 미발급",
                "api_key_env": agency_info["api_key_env"],
            })
            continue

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
                results[agency_key] = {
                    "name": agency_info["name"],
                    "match_count": len(r.get("items", [])),
                    "items": r.get("items", []),
                }
                total_count += len(r.get("items", []))
            except Exception as exc:
                results[agency_key] = {
                    "name": agency_info["name"],
                    "error": str(exc)[:200],
                }
        else:
            # 다른 기관은 어댑터 미구현 — 키 발급 + adapter 작성 후 활성화
            results[agency_key] = {
                "name": agency_info["name"],
                "status": "adapter_not_implemented",
                "items": [],
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
        "note": "G2B 외 기관은 별도 OpenAPI 키 발급 + 어댑터 구현 후 활성화 가능.",
    }


async def search_agency_specific(
    agency: str,
    keyword: str | None = None,
    biz_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict:
    """특정 기관 단독 검색.

    Args:
        agency: 'g2b', 'lh', 'ex', 'kwater', 'korail', 'kra', 'dapa'
    """
    info = _SUPPORTED_AGENCIES.get(agency)
    if not info:
        return {
            "status": "unknown_agency",
            "agency": agency,
            "supported": list(_SUPPORTED_AGENCIES.keys()),
        }
    if info["status"] != "active":
        return {
            "status": "pending_key",
            "agency": agency,
            "name": info["name"],
            "api_key_env": info["api_key_env"],
            "note": "키 발급 후 어댑터 구현 필요.",
        }
    if agency == "g2b":
        return await bid_tools.search_bid_notices(
            keyword=keyword,
            biz_type=biz_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
    return {
        "status": "adapter_not_implemented",
        "agency": agency,
        "items": [],
    }
