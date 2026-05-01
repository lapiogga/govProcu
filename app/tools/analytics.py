"""analytics 영역 MCP 도구 — 동종업체·경쟁사·유사사업·업종 동향 분석.

Tier 2.5 보조 분석 계층. Tier 1 단위 도구(award/bid/stats)를 내부 호출하여
가치 있는 인사이트를 산출한다. 사용자 5/2 지시: 보조 검색·통계 자료 강화.

도구 목록 (REPLAN.md v2 — Tier 2.5):
- find_similar_vendors (A1): 동일 업종/규모 동종업체 목록
- find_similar_bids (A2): 유사 사업(같은 발주기관·키워드·금액대) 입찰 목록
- industry_trend (A3): 업종별 월별 입찰수·낙찰가 추이
- peer_analysis (A4): 같은 규모 경쟁사 비교
- market_share (A5): 업종 내 시장점유 상위 업체

대부분 도구는 Tier 1이 실 응답을 반환할 때 결과가 의미 있어진다.
키 활성화 + 운영 IP에서의 응답 검증 후 내부 집계 로직 정밀화 가능.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from typing import Any

from app.tools import award as award_tools
from app.tools import bid as bid_tools


def _safe_amt(v: Any) -> int:
    if v is None:
        return 0
    try:
        return int(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0


def _bucket_amt(amt: int) -> str:
    """낙찰가 규모 버킷 (소액/중소/중견/대형)."""
    if amt < 100_000_000:  # 1억
        return "소액(1억 미만)"
    if amt < 1_000_000_000:  # 10억
        return "중소(1억~10억)"
    if amt < 10_000_000_000:  # 100억
        return "중견(10억~100억)"
    return "대형(100억 이상)"


# === A1: 동종 업체 찾기 ===

async def find_similar_vendors(
    vendor_biz_no: str,
    biz_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict:
    """기준 업체와 동종/유사 규모의 경쟁업체 목록 조회.

    절차:
    1. 기준 업체의 낙찰 이력에서 주력 업종·평균 낙찰가 산출
    2. 같은 업종에서 낙찰 합계가 ±50% 범위에 있는 업체를 동종으로 분류
    3. 낙찰 합계 내림차순으로 상위 N개 반환

    사용자 5/2 지시: 동종업체 동향 분석.
    """
    # 1. 기준 업체 낙찰 이력
    base = await award_tools.search_awards_by_vendor(
        vendor_biz_no=vendor_biz_no,
        date_from=date_from,
        date_to=date_to,
        biz_type=biz_type,
        limit=100,
    )
    base_items = base.get("items", [])
    if not base_items:
        return {
            "status": "no_base_data",
            "vendor_biz_no": vendor_biz_no,
            "note": "기준 업체의 낙찰 이력이 없습니다 (또는 award API 미응답).",
            "similar_vendors": [],
        }

    base_amounts = [_safe_amt(x.get("award_amount")) for x in base_items]
    base_total = sum(base_amounts)
    base_avg = base_total / len(base_amounts) if base_amounts else 0
    base_biz_types = Counter(x.get("biz_type") for x in base_items if x.get("biz_type"))
    main_biz_type = base_biz_types.most_common(1)[0][0] if base_biz_types else biz_type

    # 2. 같은 업종에서 낙찰 목록 풀스캔
    candidates = await award_tools.search_awards(
        date_from=date_from,
        date_to=date_to,
        biz_type=main_biz_type,
        limit=500,
    )

    # 3. 업체별 합계 집계
    vendor_stats: dict[str, dict] = defaultdict(lambda: {"total_amt": 0, "count": 0, "name": ""})
    for row in candidates.get("items", []):
        vbn = row.get("winner_biz_no")
        if not vbn or vbn == vendor_biz_no:
            continue
        amt = _safe_amt(row.get("award_amount"))
        vendor_stats[vbn]["total_amt"] += amt
        vendor_stats[vbn]["count"] += 1
        vendor_stats[vbn]["name"] = row.get("winner_name") or vendor_stats[vbn]["name"]

    # 4. 유사 규모(±50% 범위) 필터 + 정렬
    lower = max(0, int(base_total * 0.5))
    upper = int(base_total * 1.5) if base_total > 0 else 10**12
    similar = [
        {
            "biz_no": vbn,
            "name": data["name"],
            "award_total": data["total_amt"],
            "award_count": data["count"],
            "vs_base_ratio": (data["total_amt"] / base_total) if base_total else None,
        }
        for vbn, data in vendor_stats.items()
        if lower <= data["total_amt"] <= upper
    ]
    similar.sort(key=lambda x: x["award_total"], reverse=True)

    return {
        "base_vendor": {
            "biz_no": vendor_biz_no,
            "award_total": base_total,
            "award_avg": int(base_avg),
            "award_count": len(base_items),
            "main_biz_type": main_biz_type,
            "size_bucket": _bucket_amt(int(base_avg)),
        },
        "similar_vendors": similar[:limit],
        "criteria": {
            "biz_type": main_biz_type,
            "size_range_won": [lower, upper],
            "date_range": [date_from, date_to],
        },
        "candidates_scanned": len(vendor_stats),
        "note": "Tier 1 award API 응답 검증 후 size_bucket 임계값·필드명 조정 가능",
    }


# === A2: 유사 사업 찾기 ===

async def find_similar_bids(
    bid_notice_no: str,
    bid_ord: str = "00",
    similarity_factors: list[str] | None = None,
    limit: int = 20,
) -> dict:
    """기준 입찰과 유사한 사업 입찰 목록 조회.

    유사도 인자 (기본 모두 적용):
    - same_agency: 같은 발주기관
    - title_keyword: 제목 핵심 키워드(첫 단어 기준)
    - amount_bucket: 같은 규모 버킷(소/중소/중견/대형)
    - same_biz_type: 같은 업종
    """
    if similarity_factors is None:
        similarity_factors = ["same_agency", "title_keyword", "amount_bucket", "same_biz_type"]

    # 1. 기준 공고 상세
    base = await bid_tools.get_bid_notice_detail(bid_notice_no=bid_notice_no, bid_ord=bid_ord)
    if not base.get("found"):
        return {
            "status": "base_not_found",
            "bid_notice_no": bid_notice_no,
            "bid_ord": bid_ord,
            "note": "기준 입찰공고를 찾을 수 없습니다.",
            "similar_bids": [],
        }

    summary = base.get("summary", {})
    raw = base.get("raw", {})
    base_inst = summary.get("inst_name") or raw.get("ntceInsttNm")
    base_title = summary.get("title") or raw.get("bidNtceNm") or ""
    base_biz_type = summary.get("biz_type") or raw.get("bsnsDivNm")
    base_amt = _safe_amt(summary.get("estimated_price"))
    base_bucket = _bucket_amt(base_amt) if base_amt else None

    # 2. 첫 핵심 키워드 추출 (제목에서 첫 한글 단어)
    keyword = None
    if "title_keyword" in similarity_factors and base_title:
        tokens = [t for t in base_title.split() if len(t) >= 2]
        keyword = tokens[0] if tokens else None

    # 3. 검색
    search_kwargs: dict = {"limit": 100}
    if "same_biz_type" in similarity_factors and base_biz_type:
        search_kwargs["biz_type"] = base_biz_type
    if "same_agency" in similarity_factors and base_inst:
        search_kwargs["inst_name"] = base_inst
    if keyword:
        search_kwargs["keyword"] = keyword

    results = await bid_tools.search_bid_notices(**search_kwargs)

    # 4. amount_bucket 클라이언트 필터
    items = results.get("items", [])
    if "amount_bucket" in similarity_factors and base_bucket:
        items = [
            x for x in items
            if _bucket_amt(_safe_amt(x.get("estimated_price"))) == base_bucket
        ]

    # 자기 자신 제외
    items = [x for x in items if x.get("bid_no") != bid_notice_no]

    return {
        "base_bid": {
            "bid_notice_no": bid_notice_no,
            "bid_ord": bid_ord,
            "title": base_title,
            "inst_name": base_inst,
            "biz_type": base_biz_type,
            "estimated_price": base_amt,
            "size_bucket": base_bucket,
            "keyword_used": keyword,
        },
        "applied_factors": similarity_factors,
        "similar_bids": items[:limit],
        "candidates_scanned": len(results.get("items", [])),
    }


# === A3: 업종별 동향 ===

async def industry_trend(
    biz_type: str,
    inst_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """업종별 입찰·낙찰 동향 (월별 집계)."""
    awards = await award_tools.search_awards(
        inst_name=inst_name,
        date_from=date_from,
        date_to=date_to,
        biz_type=biz_type,
        limit=500,
    )

    monthly: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_amt": 0, "amounts": []})
    for row in awards.get("items", []):
        d = row.get("open_date") or ""
        ym = d[:6] if len(d) >= 6 else "unknown"
        amt = _safe_amt(row.get("award_amount"))
        monthly[ym]["count"] += 1
        monthly[ym]["total_amt"] += amt
        if amt > 0:
            monthly[ym]["amounts"].append(amt)

    series = []
    for ym in sorted(monthly.keys()):
        data = monthly[ym]
        amts = data["amounts"]
        avg = sum(amts) // len(amts) if amts else 0
        series.append({
            "yyyymm": ym,
            "count": data["count"],
            "total_amt": data["total_amt"],
            "avg_amt": avg,
        })

    return {
        "biz_type": biz_type,
        "inst_name": inst_name,
        "date_range": [date_from, date_to],
        "monthly": series,
        "total_count": sum(s["count"] for s in series),
        "total_amt": sum(s["total_amt"] for s in series),
        "note": "낙찰목록 응답 풀스캔 기반 집계. 키 활성화 + 응답 필드 검증 후 정확도 향상.",
    }


# === A4: 동일 규모 경쟁사 비교 ===

async def peer_analysis(
    vendor_biz_no: str,
    peer_count: int = 5,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """기준 업체와 같은 규모의 경쟁사 N개를 비교 분석."""
    similar = await find_similar_vendors(
        vendor_biz_no=vendor_biz_no,
        date_from=date_from,
        date_to=date_to,
        limit=peer_count,
    )
    base_data = similar.get("base_vendor", {})
    peers = similar.get("similar_vendors", [])
    base_total = base_data.get("award_total", 0)

    comparison = []
    for peer in peers[:peer_count]:
        peer_total = peer["award_total"]
        comparison.append({
            "biz_no": peer["biz_no"],
            "name": peer["name"],
            "award_total": peer_total,
            "award_count": peer["award_count"],
            "avg_amt": peer_total // peer["award_count"] if peer["award_count"] else 0,
            "vs_base_pct": (peer_total / base_total * 100) if base_total else None,
        })

    base_avg = base_data.get("award_avg", 0)
    peer_avg_total = sum(p["award_total"] for p in peers[:peer_count]) // max(len(peers[:peer_count]), 1)
    peer_avg_count = sum(p["award_count"] for p in peers[:peer_count]) // max(len(peers[:peer_count]), 1)

    return {
        "base_vendor": base_data,
        "peers": comparison,
        "summary": {
            "peer_count": len(comparison),
            "peer_avg_award_total": peer_avg_total,
            "peer_avg_award_count": peer_avg_count,
            "base_vs_peers_total_pct": (base_total / peer_avg_total * 100) if peer_avg_total else None,
            "base_avg_won": base_avg,
        },
        "criteria": similar.get("criteria"),
    }


# === A5: 시장 점유 ===

async def market_share(
    biz_type: str,
    date_from: str | None = None,
    date_to: str | None = None,
    top_n: int = 10,
) -> dict:
    """업종별 낙찰 시장 점유 상위 업체."""
    awards = await award_tools.search_awards(
        date_from=date_from,
        date_to=date_to,
        biz_type=biz_type,
        limit=1000,
    )

    vendor_total: dict[str, dict] = defaultdict(lambda: {"total_amt": 0, "count": 0, "name": ""})
    grand_total = 0
    for row in awards.get("items", []):
        vbn = row.get("winner_biz_no")
        if not vbn:
            continue
        amt = _safe_amt(row.get("award_amount"))
        vendor_total[vbn]["total_amt"] += amt
        vendor_total[vbn]["count"] += 1
        vendor_total[vbn]["name"] = row.get("winner_name") or vendor_total[vbn]["name"]
        grand_total += amt

    ranked = sorted(vendor_total.items(), key=lambda kv: kv[1]["total_amt"], reverse=True)[:top_n]
    top_list = []
    for vbn, data in ranked:
        share_pct = (data["total_amt"] / grand_total * 100) if grand_total else 0
        top_list.append({
            "biz_no": vbn,
            "name": data["name"],
            "award_total": data["total_amt"],
            "award_count": data["count"],
            "market_share_pct": round(share_pct, 2),
        })

    return {
        "biz_type": biz_type,
        "date_range": [date_from, date_to],
        "grand_total_won": grand_total,
        "top_vendors": top_list,
        "vendor_count_total": len(vendor_total),
        "note": "낙찰목록 풀스캔 기반 단순 집계. 정확한 시장 규모는 PubPrcrmntStatInfoService 통합 필요.",
    }


# === A6: 발주기관 사정률 패턴 (P1, 사용자 5/2 22번) ===

async def analyze_agency_price_pattern(
    inst_name: str,
    biz_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 200,
) -> dict:
    """발주기관별 낙찰가/예정가 비율 패턴 분석.

    경쟁사(인포21C·비드큐) 인기 1위 기능. 입찰가격 산정의 핵심 인사이트.

    절차:
    1. 발주기관의 낙찰 이력 풀스캔 (search_awards)
    2. 각 낙찰 row의 award_rate (낙찰률) 추출 — 보통 응답에 직접 포함
    3. 낙찰률 분포 통계 (평균/표준편차/분위수)
    4. 업종별·금액대별 분포 분리

    Args:
        inst_name: 발주기관명
        biz_type: 업종 필터
        date_from / date_to: 기간 (YYYYMMDD)
        limit: 분석 대상 최대 건수
    """
    awards = await award_tools.search_awards(
        inst_name=inst_name,
        date_from=date_from,
        date_to=date_to,
        biz_type=biz_type,
        limit=limit,
    )
    items = awards.get("items", [])

    rates: list[float] = []
    rate_buckets: dict[str, list[float]] = defaultdict(list)
    amount_buckets: dict[str, list[float]] = defaultdict(list)

    for row in items:
        rate_str = row.get("award_rate")
        if not rate_str:
            continue
        try:
            r = float(str(rate_str).replace("%", "").strip())
            # 0~100 범위 정규화
            if r > 1 and r < 200:
                r = r / 100.0
            elif r >= 200:
                continue  # 이상치 제외
        except (ValueError, TypeError):
            continue

        rates.append(r)
        rate_buckets[row.get("biz_type") or "unknown"].append(r)
        amt = _safe_amt(row.get("award_amount"))
        amount_buckets[_bucket_amt(amt)].append(r)

    if not rates:
        return {
            "inst_name": inst_name,
            "biz_type": biz_type,
            "date_range": [date_from, date_to],
            "sample_count": 0,
            "note": "낙찰률 데이터 없음. 발주기관명 확인 또는 기간 확장.",
        }

    rates_sorted = sorted(rates)
    n = len(rates)
    mean = sum(rates) / n
    median = rates_sorted[n // 2]
    p25 = rates_sorted[n // 4]
    p75 = rates_sorted[3 * n // 4]
    p10 = rates_sorted[n // 10] if n >= 10 else rates_sorted[0]
    p90 = rates_sorted[9 * n // 10] if n >= 10 else rates_sorted[-1]

    # 표준편차
    var = sum((r - mean) ** 2 for r in rates) / n
    std = var ** 0.5

    return {
        "inst_name": inst_name,
        "biz_type": biz_type,
        "date_range": [date_from, date_to],
        "sample_count": n,
        "summary_pct": {
            "mean": round(mean * 100, 3),
            "median": round(median * 100, 3),
            "std": round(std * 100, 3),
            "min": round(rates_sorted[0] * 100, 3),
            "max": round(rates_sorted[-1] * 100, 3),
            "p10": round(p10 * 100, 3),
            "p25": round(p25 * 100, 3),
            "p75": round(p75 * 100, 3),
            "p90": round(p90 * 100, 3),
        },
        "by_biz_type": {
            bt: {
                "count": len(rs),
                "mean_pct": round(sum(rs) / len(rs) * 100, 3) if rs else 0,
            }
            for bt, rs in rate_buckets.items()
        },
        "by_amount_bucket": {
            bk: {
                "count": len(rs),
                "mean_pct": round(sum(rs) / len(rs) * 100, 3) if rs else 0,
            }
            for bk, rs in amount_buckets.items()
        },
        "interpretation": _interpret_pattern(mean, std),
    }


def _interpret_pattern(mean_rate: float, std: float) -> str:
    """낙찰률 패턴 해석 텍스트."""
    if std < 0.02:
        consistency = "매우 일관됨 (낙찰률 변동 적음)"
    elif std < 0.05:
        consistency = "일관됨"
    else:
        consistency = "변동 큼 (입찰별 사정률 편차 큼)"

    if mean_rate > 0.95:
        level = "고낙찰률 (응찰가 90%+ 권장)"
    elif mean_rate > 0.88:
        level = "중낙찰률 (응찰가 88~92% 범위 권장)"
    elif mean_rate > 0.82:
        level = "중저낙찰률 (응찰가 84~88% 범위 권장)"
    else:
        level = "저낙찰률 (응찰가 80~85% 범위 권장)"

    return f"{level} | {consistency}"
