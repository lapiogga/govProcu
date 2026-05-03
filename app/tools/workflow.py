"""workflow 영역 MCP 도구 — Tier 2 통합 워크플로우.

핵심 가치: "한 입찰 또는 한 업체에 대해 흩어진 정보를 한 번에 추적·통합"

도구 목록 (REPLAN.md v2):
- trace_bid_lifecycle (W1): 한 입찰의 사전규격→공고→개찰→낙찰→응찰업체 전 생애
- vendor_profile (W2): 한 업체의 NTS 진위 + 기간 내 입찰/응찰/개찰/낙찰 통계
- agency_bid_summary (W3): 발주기관별 사전규격→공고→낙찰 요약
- competitor_analysis (W4): 동일 업종 경쟁사 비교 (analytics.peer_analysis 래퍼)
- agency_procurement_history (W5): 사용자 5/2 추가 — 발주기관 발주이력 + 낙찰업체 매칭
"""
from __future__ import annotations
import asyncio
from typing import Any

from app.config import settings
from app.core.cache import cache_result
from app.tools import bid as bid_tools
from app.tools import award as award_tools
from app.tools import vendor as vendor_tools
from app.tools import analytics as analytics_tools


async def _safe(coro):
    """예외 발생 시 {"error": ...} 반환. asyncio.gather에서 stage 손실 방지."""
    try:
        return await coro
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)[:200]}


def _safe_amt(v: Any) -> int:
    if v is None:
        return 0
    try:
        return int(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0


def _safe_get(d: dict, *keys, default=None):
    """안전한 중첩 dict 접근."""
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


# === W1: trace_bid_lifecycle ===

@cache_result(ttl=settings.cache_ttl_short, prefix="trace_lifecycle")
async def trace_bid_lifecycle(bid_notice_no: str, bid_ord: str = "00") -> dict:
    """한 입찰의 전 생애주기 통합 추적.

    사용자 핵심 가치 도구. 사전규격 → 공고 → 개찰 → 낙찰 → 응찰업체 → 낙찰업체 NTS 검증
    6개 섹션을 한 번의 호출로 통합 반환.

    Args:
        bid_notice_no: 입찰공고번호 (예: '20240101234')
        bid_ord: 차수 (기본 "00")
    """
    result: dict[str, Any] = {
        "bid_notice_no": bid_notice_no,
        "bid_ord": bid_ord,
        "stages": {},
        "summary": {},
    }

    # v23.2: 1~4단계 병렬화 (직렬 30~90초 → 병렬 max 단계 ≈ 5~20초).
    # 5단계(NTS 검증)는 4단계(award)의 winner_biz_no 의존 → 순차 유지.
    prespec, notice, participants, award = await asyncio.gather(
        _safe(bid_tools.get_pre_specification_detail(bid_notice_no, bid_ord)),
        _safe(bid_tools.get_bid_notice_detail(bid_notice_no, bid_ord)),
        _safe(award_tools.list_bid_participants(bid_notice_no, bid_ord)),
        _safe(award_tools.get_award_detail(bid_notice_no, bid_ord)),
    )
    result["stages"]["pre_specification"] = prespec
    result["stages"]["bid_notice"] = notice
    result["stages"]["participants"] = participants
    result["stages"]["award"] = award

    # 5. 낙찰업체 NTS 검증 (낙찰자 사업자번호가 있을 때)
    winner_biz_no = _safe_get(result, "stages", "award", "summary", "winner_biz_no")
    if winner_biz_no:
        try:
            nts = await vendor_tools.check_business_status([winner_biz_no])
            result["stages"]["winner_nts_status"] = nts
        except Exception as exc:
            result["stages"]["winner_nts_status"] = {"error": str(exc)[:200]}

    # 6. 요약
    notice_summary = _safe_get(result, "stages", "bid_notice", "summary", default={})
    award_summary = _safe_get(result, "stages", "award", "summary", default={})
    participants_count = len(_safe_get(result, "stages", "participants", "items", default=[]))
    result["summary"] = {
        "title": notice_summary.get("title"),
        "inst_name": notice_summary.get("inst_name"),
        "biz_type": notice_summary.get("biz_type"),
        "estimated_price": notice_summary.get("estimated_price"),
        "publish_date": notice_summary.get("publish_date"),
        "deadline_date": notice_summary.get("deadline_date"),
        "participant_count": participants_count,
        "winner_name": award_summary.get("winner_name"),
        "winner_biz_no": award_summary.get("winner_biz_no"),
        "award_amount": award_summary.get("award_amount"),
        "award_rate": award_summary.get("award_rate"),
        "open_date": award_summary.get("open_date"),
        "stages_found": [k for k, v in result["stages"].items() if v.get("found") or v.get("items")],
    }
    return result


# === W2: vendor_profile ===

@cache_result(ttl=settings.cache_ttl_short, prefix="vendor_profile_v24")

async def vendor_profile(
    vendor_biz_no: str,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
) -> dict:
    """한 업체의 통합 프로필 — NTS 진위 + 기간 내 입찰/응찰/개찰/낙찰 통계.

    사용자 5/2 지시: 특정 업체의 기간 내 입찰/응찰/개찰/낙찰 정보 검색.
    """
    result: dict[str, Any] = {
        "vendor_biz_no": vendor_biz_no,
        "date_range": [date_from, date_to],
        "sections": {},
        "summary": {},
    }

    # 1. NTS 진위/상태
    try:
        nts = await vendor_tools.check_business_status([vendor_biz_no])
        result["sections"]["nts_status"] = nts
    except Exception as exc:
        result["sections"]["nts_status"] = {"error": str(exc)[:200]}

    # 2. 낙찰 이력 (V4)
    try:
        awards = await award_tools.search_awards_by_vendor(
            vendor_biz_no=vendor_biz_no,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
        result["sections"]["awards"] = awards
    except Exception as exc:
        result["sections"]["awards"] = {"error": str(exc)[:200]}

    # 3. 응찰 이력 (V2)
    try:
        participations = await vendor_tools.search_participations_by_vendor(
            vendor_biz_no=vendor_biz_no,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
        result["sections"]["participations"] = participations
    except Exception as exc:
        result["sections"]["participations"] = {"error": str(exc)[:200]}

    # 4. 개찰 이력 (V3)
    try:
        openings = await vendor_tools.search_openings_by_vendor(
            vendor_biz_no=vendor_biz_no,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
        result["sections"]["openings"] = openings
    except Exception as exc:
        result["sections"]["openings"] = {"error": str(exc)[:200]}

    # 5. 입찰 이력 (V1)
    try:
        bids = await vendor_tools.search_bids_by_vendor(
            vendor_biz_no=vendor_biz_no,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
        result["sections"]["bids"] = bids
    except Exception as exc:
        result["sections"]["bids"] = {"error": str(exc)[:200]}

    # 6. 요약 통계
    awards_items = _safe_get(result, "sections", "awards", "items", default=[])
    parts_items = _safe_get(result, "sections", "participations", "items", default=[])
    open_items = _safe_get(result, "sections", "openings", "items", default=[])
    bids_items = _safe_get(result, "sections", "bids", "items", default=[])

    award_total_amt = sum(_safe_amt(x.get("award_amount")) for x in awards_items)
    awards_count = len(awards_items)
    parts_count = len(parts_items)
    win_rate = (awards_count / parts_count * 100) if parts_count else None

    result["summary"] = {
        "vendor_biz_no": vendor_biz_no,
        "nts_status_code": _safe_get(result, "sections", "nts_status", "items", 0, "b_stt_cd")
            or _safe_get(result, "sections", "nts_status", "items", 0, "b_stt"),
        "awards_count": awards_count,
        "awards_total_won": award_total_amt,
        "awards_avg_won": (award_total_amt // awards_count) if awards_count else 0,
        "participations_count": parts_count,
        "openings_count": len(open_items),
        "bids_count": len(bids_items),
        "win_rate_pct": round(win_rate, 2) if win_rate is not None else None,
        "implementation_status": "awards 영역 = 실 구현, V1·V2·V3 = 스텁(EVAL 키 발급 후 활성화)",
    }
    return result


# === W3: agency_bid_summary ===

@cache_result(ttl=settings.cache_ttl_short, prefix="agency_summary_v24")
async def agency_bid_summary(
    inst_name: str,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 50,
) -> dict:
    """발주기관 단위 사전규격 → 공고 → 낙찰 요약."""
    result: dict[str, Any] = {
        "inst_name": inst_name,
        "date_range": [date_from, date_to],
        "biz_type": biz_type,
        "sections": {},
    }

    try:
        prespec = await bid_tools.list_pre_specifications(
            inst_name=inst_name,
            biz_type=biz_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
        result["sections"]["pre_specifications"] = prespec
    except Exception as exc:
        result["sections"]["pre_specifications"] = {"error": str(exc)[:200]}

    try:
        notices = await bid_tools.search_bid_notices(
            inst_name=inst_name,
            biz_type=biz_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
        result["sections"]["bid_notices"] = notices
    except Exception as exc:
        result["sections"]["bid_notices"] = {"error": str(exc)[:200]}

    try:
        awards = await award_tools.search_awards(
            inst_name=inst_name,
            biz_type=biz_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
        result["sections"]["awards"] = awards
    except Exception as exc:
        result["sections"]["awards"] = {"error": str(exc)[:200]}

    prespec_count = _safe_get(result, "sections", "pre_specifications", "returned_count", default=0)
    notices_count = _safe_get(result, "sections", "bid_notices", "returned_count", default=0)
    awards_items = _safe_get(result, "sections", "awards", "items", default=[])
    awards_count = len(awards_items)
    awards_total = sum(_safe_amt(x.get("award_amount")) for x in awards_items)

    result["summary"] = {
        "inst_name": inst_name,
        "pre_spec_count": prespec_count,
        "notice_count": notices_count,
        "award_count": awards_count,
        "award_total_won": awards_total,
        "biz_type": biz_type,
    }
    return result


# === W4: competitor_analysis ===

@cache_result(ttl=settings.cache_ttl_short, prefix="competitor_v24")
async def competitor_analysis(
    vendor_biz_no: str,
    peer_count: int = 5,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """동일 규모 경쟁사 비교 분석 (analytics.peer_analysis 래퍼)."""
    return await analytics_tools.peer_analysis(
        vendor_biz_no=vendor_biz_no,
        peer_count=peer_count,
        date_from=date_from,
        date_to=date_to,
    )


# === W5: agency_procurement_history (사용자 5/2 추가) ===

@cache_result(ttl=settings.cache_ttl_short, prefix="agency_history_v24")
async def agency_procurement_history(
    inst_name: str,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 30,
) -> dict:
    """특정 기간·발주기관의 발주 목록 + 각 발주별 낙찰업체 정보 통합 조회.

    사용자 5/2 지시: "특정기간, 특정 발주기관의 발주 목록 및 낙찰업체 정보 조회".

    절차:
    1. search_bid_notices(inst_name, period, biz_type) — 발주 목록
    2. 각 공고별 get_award_detail — 낙찰자 매칭
    3. 통합 표 + 발주기관 통계 요약
    """
    notices = await bid_tools.search_bid_notices(
        inst_name=inst_name,
        biz_type=biz_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    notice_items = notices.get("items", [])

    enriched: list[dict] = []
    award_total = 0
    matched_count = 0

    for notice in notice_items:
        bid_no = notice.get("bid_no")
        bid_ord = notice.get("bid_ord") or "00"
        award_data: dict | None = None
        if bid_no:
            try:
                award = await award_tools.get_award_detail(bid_no, bid_ord)
                if award.get("found"):
                    award_data = award.get("summary")
                    matched_count += 1
                    award_total += _safe_amt(award_data.get("award_amount"))
            except Exception:
                award_data = None

        enriched.append({
            "bid_notice_no": bid_no,
            "bid_ord": bid_ord,
            "title": notice.get("title"),
            "biz_type": notice.get("biz_type"),
            "estimated_price": notice.get("estimated_price"),
            "publish_date": notice.get("publish_date"),
            "deadline_date": notice.get("deadline_date"),
            "winner": award_data,
        })

    return {
        "inst_name": inst_name,
        "date_range": [date_from, date_to],
        "biz_type": biz_type,
        "items": enriched,
        "endpoints_used": notices.get("endpoints_used", []),
        "chunks_used": notices.get("chunks_used", 1),
        "summary": {
            "notice_count": len(enriched),
            "award_matched_count": matched_count,
            "award_match_rate_pct": round(matched_count / len(enriched) * 100, 2) if enriched else 0,
            "award_total_won": award_total,
            "match_note": "낙찰 매칭은 공고번호 기준. 미매칭은 미낙찰/유찰 또는 응답 미발견.",
        },
    }
