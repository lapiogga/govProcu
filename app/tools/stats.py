"""통계 영역 MCP 도구 — 공공조달통계정보서비스.

서비스: 조달청_공공조달통계정보서비스 (data.go.kr 15129412)
Base URL: https://apis.data.go.kr/1230000/PubPrcrmntStatInfoService
인증: G2B_KEY_STATS (Encoding 키)

특이사항 (Delta Research 5/2):
- base path는 /ad나 /ao가 아닌 직접 /1230000/PubPrcrmntStatInfoService
- 13개 operation 식별 (전체조달실적/기관구분/기업구분/계약방법/지역제한 등)
- 시간 필터는 bsisYy(기준연도) 또는 bsisYm(기준연월) 추정 (운영 검증 후 확정)

도구:
- get_procurement_stats: 전체 조달 실적 (getTotlPubPrcrmntSttus)
- list_top_vendors_by_period: 조달기업×계약방법별 실적 (클라이언트 정렬로 Top-N)
- agency_procurement_volume: 수요기관×기업구분별 실적
- industry_procurement_stats: 업무대상별(물품/공사/용역/외자) 현황
"""
from __future__ import annotations
from app.clients.g2b import G2BClient
from app.config import settings
from app.core.cache import cache_result
from app.core.rate_limit import check_rate


_STATS_ENDPOINTS = {
    "total": "/PubPrcrmntStatInfoService/getTotlPubPrcrmntSttus",
    "inst_div": "/PubPrcrmntStatInfoService/getInsttDivAccotPrcrmntSttus",
    "entrprs_div": "/PubPrcrmntStatInfoService/getEntrprsDivAccotPrcrmntSttus",
    "cntrct_method": "/PubPrcrmntStatInfoService/getCntrctMthdAccotSttus",
    "rgn_lmt": "/PubPrcrmntStatInfoService/getRgnLmtSttus",
    "rgn_duty_cmmn": "/PubPrcrmntStatInfoService/getRgnDutyCmmnCntrctSttus",
    "object_bsns_obj": "/PubPrcrmntStatInfoService/getPrcrmntObjectBsnsObjAccotSttus",
    "dminstt_entrprs_div": "/PubPrcrmntStatInfoService/getDminsttAccotEntrprsDivAccotArslt",
    "dminstt_bsns_obj": "/PubPrcrmntStatInfoService/getDminsttAccotBsnsObjAccotArslt",
    "dminstt_cntrct_method": "/PubPrcrmntStatInfoService/getDminsttAccotCntrctMthdAccotArslt",
    "dminstt_systm_ty": "/PubPrcrmntStatInfoService/getDminsttAccotSystmTyAccotArslt",
    "entrprs_bsns_obj": "/PubPrcrmntStatInfoService/getPrcrmntEntrprsAccotBsnsObjAccotArslt",
    "entrprs_cntrct_method": "/PubPrcrmntStatInfoService/getPrcrmntEntrprsAccotCntrctMthdAccotArslt",
}


def _extract_items(body: dict) -> list[dict]:
    items = body.get("items", [])
    if isinstance(items, dict):
        items = items.get("item", [])
    if not isinstance(items, list):
        items = [items] if items else []
    return items


def _build_period_params(year: str | None, ym: str | None) -> dict:
    """통계 시간 필터. year(YYYY) 또는 ym(YYYYMM) 사용 (Delta Research 추정)."""
    p: dict = {}
    if year:
        p["bsisYy"] = year
    if ym:
        p["bsisYm"] = ym
    return p


@cache_result(ttl=settings.cache_ttl_long, prefix="stats_total")
async def get_procurement_stats(
    year: str | None = None,
    ym: str | None = None,
    biz_type: str | None = None,
) -> dict:
    """기간 내 전체 공공조달 실적 통계.

    Args:
        year: 기준연도 YYYY (예: "2024")
        ym: 기준연월 YYYYMM (예: "202404") — year보다 우선
        biz_type: 업무대상 (물품/공사/용역/외자) — 클라이언트측 필터
    """
    allowed, remaining = await check_rate("g2b_stats", capacity=5, refill_per_sec=0.5)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_stats 토큰 소진 (remaining={remaining})")

    client = G2BClient(base_url=settings.g2b_stats_base_url)
    try:
        params = {
            "pageNo": 1,
            "numOfRows": 100,
            **_build_period_params(year, ym),
        }
        try:
            body = await client.call(_STATS_ENDPOINTS["total"], settings.g2b_key_stats, params)
        except Exception as exc:
            return {
                "status": "endpoint_error",
                "endpoint": _STATS_ENDPOINTS["total"],
                "error": str(exc)[:200],
                "note": "통계 endpoint 추정 — 운영 IP에서 검증 필요. bsisYy/bsisYm 키명 확인.",
                "items": [],
            }
        items = _extract_items(body)
        if biz_type:
            items = [x for x in items if biz_type in (x.get("bsnsObjNm") or "")]
        return {
            "year": year,
            "ym": ym,
            "biz_type": biz_type,
            "items": items,
            "count": len(items),
            "endpoint": _STATS_ENDPOINTS["total"],
        }
    finally:
        await client.aclose()


@cache_result(ttl=settings.cache_ttl_long, prefix="stats_top")
async def list_top_vendors_by_period(
    year: str | None = None,
    ym: str | None = None,
    biz_type: str | None = None,
    top_n: int = 20,
) -> dict:
    """기간 내 낙찰 합계 기준 상위 업체 목록.

    조달기업×계약방법별 실적 endpoint를 호출하여 클라이언트측에서 합계 정렬.
    """
    allowed, remaining = await check_rate("g2b_stats_top", capacity=5, refill_per_sec=0.5)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_stats_top 토큰 소진 (remaining={remaining})")

    client = G2BClient(base_url=settings.g2b_stats_base_url)
    try:
        params = {
            "pageNo": 1,
            "numOfRows": 1000,
            **_build_period_params(year, ym),
        }
        try:
            body = await client.call(
                _STATS_ENDPOINTS["entrprs_cntrct_method"],
                settings.g2b_key_stats,
                params,
            )
        except Exception as exc:
            return {
                "status": "endpoint_error",
                "error": str(exc)[:200],
                "items": [],
            }

        items = _extract_items(body)

        # 업체별 합계
        agg: dict[str, dict] = {}
        for row in items:
            biz_no = row.get("bizrno") or row.get("entrprsBizrno")
            if not biz_no:
                continue
            try:
                amt = int(str(row.get("arsltAmt", 0)).replace(",", "")) if row.get("arsltAmt") else 0
            except (ValueError, TypeError):
                amt = 0
            try:
                cnt = int(str(row.get("arsltNum", 0)).replace(",", "")) if row.get("arsltNum") else 0
            except (ValueError, TypeError):
                cnt = 0
            entry = agg.setdefault(biz_no, {
                "biz_no": biz_no,
                "name": row.get("entrprsNm") or row.get("corpNm"),
                "total_amt": 0,
                "total_count": 0,
            })
            entry["total_amt"] += amt
            entry["total_count"] += cnt

        ranked = sorted(agg.values(), key=lambda x: x["total_amt"], reverse=True)[:top_n]
        return {
            "year": year,
            "ym": ym,
            "biz_type": biz_type,
            "top_vendors": ranked,
            "vendor_count_total": len(agg),
            "endpoint": _STATS_ENDPOINTS["entrprs_cntrct_method"],
        }
    finally:
        await client.aclose()


@cache_result(ttl=settings.cache_ttl_long, prefix="stats_agency")
async def agency_procurement_volume(
    inst_code: str | None = None,
    inst_name: str | None = None,
    year: str | None = None,
    ym: str | None = None,
) -> dict:
    """수요(발주)기관별 조달 규모 — 기업구분별 실적."""
    allowed, remaining = await check_rate("g2b_stats_agency", capacity=5, refill_per_sec=0.5)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_stats_agency 토큰 소진 (remaining={remaining})")

    client = G2BClient(base_url=settings.g2b_stats_base_url)
    try:
        params: dict = {
            "pageNo": 1,
            "numOfRows": 500,
            **_build_period_params(year, ym),
        }
        if inst_code:
            params["dminsttCd"] = inst_code

        try:
            body = await client.call(
                _STATS_ENDPOINTS["dminstt_entrprs_div"],
                settings.g2b_key_stats,
                params,
            )
        except Exception as exc:
            return {
                "status": "endpoint_error",
                "error": str(exc)[:200],
                "items": [],
            }
        items = _extract_items(body)

        if inst_name:
            items = [x for x in items if inst_name in (x.get("dminsttNm") or "")]

        return {
            "inst_code": inst_code,
            "inst_name": inst_name,
            "year": year,
            "ym": ym,
            "items": items,
            "count": len(items),
            "endpoint": _STATS_ENDPOINTS["dminstt_entrprs_div"],
        }
    finally:
        await client.aclose()


async def industry_procurement_stats(
    year: str | None = None,
    ym: str | None = None,
) -> dict:
    """업무대상별(물품/공사/용역/외자) 조달 현황."""
    client = G2BClient(base_url=settings.g2b_stats_base_url)
    try:
        params = {
            "pageNo": 1,
            "numOfRows": 100,
            **_build_period_params(year, ym),
        }
        try:
            body = await client.call(
                _STATS_ENDPOINTS["object_bsns_obj"],
                settings.g2b_key_stats,
                params,
            )
        except Exception as exc:
            return {"status": "endpoint_error", "error": str(exc)[:200], "items": []}
        return {
            "year": year,
            "ym": ym,
            "items": _extract_items(body),
            "endpoint": _STATS_ENDPOINTS["object_bsns_obj"],
        }
    finally:
        await client.aclose()


async def placeholder_stats() -> dict:
    """stats 영역 도구 자리표시자. 호환성을 위해 유지."""
    return {"status": "not_implemented", "domain": "stats"}
