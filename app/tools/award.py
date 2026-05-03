"""award 영역 MCP 도구 — 개찰/낙찰결과 조회.

G2B `ScsbidInfoService` (낙찰정보서비스) — base `/1230000/as/ScsbidInfoService`.
업종 분기 패턴: Thng(물품)/Cnstwk(공사)/Servc(용역)/Frgcpt(외자).

운영 컨벤션:
- 개찰결과 목록: getOpengResultListInfo{업종}PPSSrch
- 낙찰목록: getScsbidListSttus{업종}
- 응찰업체 단독 endpoint 없음 → 개찰결과 응답 row에서 추출
- 사업자번호 직접 필터 파라미터 없음 → 클라이언트측 필터링

도구 매트릭스 (REPLAN.md v2):
- list_bid_openings: 개찰결과 목록 (특정 입찰 단건 또는 기간 일괄)
- search_awards: 낙찰목록 (기간/기관/업종/키워드)
- get_award_detail: 낙찰 단건 (공고번호+차수)
- search_awards_by_vendor (V4): 업체 기준 낙찰 이력
- list_bid_participants: 응찰업체 목록 (개찰결과 row에서 추출)
"""
from __future__ import annotations
from app.clients.g2b import G2BClient
from app.config import settings
from app.core.cache import cache_result
from app.core.daterange import chunk_date_range
from app.core.rate_limit import check_rate


_BIZ_DIV_MAP = {"공사": "Cnstwk", "용역": "Servc", "물품": "Thng", "외자": "Frgcpt"}

_OPENING_BASE = "/ScsbidInfoService/getOpengResultListInfo"
_AWARD_BASE = "/ScsbidInfoService/getScsbidListSttus"

_OPENING_ENDPOINTS = {
    "Cnstwk": _OPENING_BASE + "CnstwkPPSSrch",
    "Servc": _OPENING_BASE + "ServcPPSSrch",
    "Thng": _OPENING_BASE + "ThngPPSSrch",
    "Frgcpt": _OPENING_BASE + "FrgcptPPSSrch",
}
_AWARD_ENDPOINTS = {
    "Cnstwk": _AWARD_BASE + "Cnstwk",
    "Servc": _AWARD_BASE + "Servc",
    "Thng": _AWARD_BASE + "Thng",
    "Frgcpt": _AWARD_BASE + "Frgcpt",
}


def _to_int(v) -> int | None:
    try:
        return int(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _normalize_biz_no(s) -> str | None:
    """사업자번호 정규화: 하이픈 제거."""
    if not s:
        return None
    return str(s).replace("-", "").replace(" ", "").strip() or None


def _extract_items(body: dict) -> list[dict]:
    """G2B body에서 items 배열 안전 추출."""
    items = body.get("items", [])
    if isinstance(items, dict):
        items = items.get("item", [])
    if not isinstance(items, list):
        items = [items] if items else []
    return items


def _normalize_award_row(raw: dict) -> dict:
    """낙찰결과 row 정규화."""
    return {
        "bid_notice_no": raw.get("bidNtceNo"),
        "bid_ord": raw.get("bidNtceOrd"),
        "bid_title": raw.get("bidNtceNm"),
        "inst_name": raw.get("ntceInsttNm") or raw.get("dminsttNm"),
        "biz_type": raw.get("bsnsDivNm"),
        "winner_name": raw.get("bidwinnrNm") or raw.get("opengCorpNm") or raw.get("prcbdrNm"),
        "winner_biz_no": _normalize_biz_no(
            raw.get("bidwinnrBizno") or raw.get("opengCorpBizrno") or raw.get("prcbdrBizno")
        ),
        "award_amount": _to_int(raw.get("sucsfbidAmt") or raw.get("plnprc") or raw.get("sucsfbidPrce")),
        "award_rate": raw.get("sucsfbidRate") or raw.get("opengRslcfRate"),
        "open_date": raw.get("opengDt") or raw.get("rlOpengDt"),
        "raw": raw,
    }


def _normalize_opening_row(raw: dict) -> dict:
    """개찰결과 row 정규화 — 응찰자 단위 포함."""
    return {
        "bid_notice_no": raw.get("bidNtceNo"),
        "bid_ord": raw.get("bidNtceOrd"),
        "bid_title": raw.get("bidNtceNm"),
        "inst_name": raw.get("ntceInsttNm") or raw.get("dminsttNm"),
        "open_date": raw.get("opengDt") or raw.get("rlOpengDt"),
        "participant_count": _to_int(raw.get("prtcptCnum") or raw.get("opengCnt")),
        "lower_limit_rate": raw.get("dcsnRsrvtnPrceRt") or raw.get("rsrvtnPrceRngBgnRate"),
        "participant_name": raw.get("opengCorpNm") or raw.get("prtcptCorpNm") or raw.get("prcbdrNm"),
        "participant_biz_no": _normalize_biz_no(
            raw.get("opengCorpBizrno") or raw.get("prtcptCorpBizrno") or raw.get("prcbdrBizno")
        ),
        "participant_bid_amount": _to_int(raw.get("opengAmt") or raw.get("prtcptPrce") or raw.get("plnprc")),
        "opening_rank": _to_int(raw.get("opengRank") or raw.get("rank")),
        "is_winner": raw.get("sucsfbidYn") == "Y" or raw.get("bidwinnrYn") == "Y",
        "raw": raw,
    }


def _resolve_biz_divs(biz_type: str | None) -> list[str]:
    """biz_type에 해당하는 endpoint key 목록. None이면 전체 4종."""
    if biz_type is None:
        return ["Servc", "Cnstwk", "Thng", "Frgcpt"]  # 가장 흔한 순
    key = _BIZ_DIV_MAP.get(biz_type)
    if key:
        return [key]
    return ["Servc", "Cnstwk", "Thng", "Frgcpt"]


# === 1. list_bid_openings ===

@cache_result(ttl=settings.cache_ttl_short, prefix="award_open")
async def list_bid_openings(
    bid_notice_no: str | None = None,
    bid_ord: str | None = None,
    inst_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 20,
) -> dict:
    """개찰결과 목록 조회 — 특정 입찰 단건 또는 기간 일괄.

    Args:
        bid_notice_no: 입찰공고번호 (단건 추적 시)
        bid_ord: 차수 (선택)
        inst_name: 발주기관명 (클라이언트측 필터)
        date_from / date_to: 개찰일 (YYYYMMDD)
        biz_type: '공사' | '용역' | '물품' | '외자'
        limit: 최대 반환 건수

    Returns:
        items: 개찰결과 row 목록 (응찰업체별).
    """
    allowed, remaining = await check_rate("g2b_open", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_open 토큰 소진 (remaining={remaining})")

    biz_divs = _resolve_biz_divs(biz_type)
    needs_client_filter = bool(inst_name)

    matches: list[dict] = []
    total_count = 0
    used_endpoints: list[str] = []

    client = G2BClient(base_url=settings.g2b_award_base_url)
    try:
        for biz_div in biz_divs:
            if len(matches) >= limit:
                break
            endpoint = _OPENING_ENDPOINTS[biz_div]
            params: dict = {
                "pageNo": 1,
                "numOfRows": 999 if needs_client_filter else max(limit, 50),
                "inqryDiv": "1",  # 등록일 (일자 미지정 시 사용)
            }
            if bid_notice_no:
                params["inqryDiv"] = "4"  # 공고번호 단건
                params["bidNtceNo"] = bid_notice_no
                if bid_ord:
                    params["bidNtceOrd"] = bid_ord
            else:
                if date_from:
                    params["inqryBgnDt"] = date_from + "0000"
                if date_to:
                    params["inqryEndDt"] = date_to + "2359"

            try:
                body = await client.call(endpoint, settings.g2b_key_award, params)
            except Exception as exc:  # noqa: BLE001
                continue

            used_endpoints.append(endpoint)
            total_count += int(body.get("totalCount", 0) or 0)

            for raw in _extract_items(body):
                if needs_client_filter and inst_name:
                    inst = (raw.get("dminsttNm") or "") + " " + (raw.get("ntceInsttNm") or "")
                    if inst_name not in inst:
                        continue
                matches.append(_normalize_opening_row(raw))
                if len(matches) >= limit:
                    break
    finally:
        await client.aclose()

    return {
        "items": matches,
        "total_count": total_count,
        "returned_count": len(matches),
        "has_more": len(matches) >= limit,
        "endpoints_used": used_endpoints,
    }


# === 2. search_awards ===

@cache_result(ttl=settings.cache_ttl_short, prefix="award_list")
async def search_awards(
    inst_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    keyword: str | None = None,
    limit: int = 20,
) -> dict:
    """기간/기관/업종/키워드로 낙찰 목록 조회.

    5/3 N42: G2B 1개월 제약 자동 chunking. biz_type=None면 4종 endpoint 병합.
    """
    allowed, remaining = await check_rate("g2b_award", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_award 토큰 소진 (remaining={remaining})")

    biz_divs = _resolve_biz_divs(biz_type)
    chunks = chunk_date_range(date_from, date_to, max_days=31)
    needs_client_filter = bool(inst_name or keyword)
    page_size = 500 if needs_client_filter else max(limit, 50)

    seen_keys: set[tuple[str, str]] = set()
    matches: list[dict] = []
    total_count = 0
    used_endpoints: list[str] = []

    client = G2BClient(base_url=settings.g2b_award_base_url)
    try:
        for chunk_from, chunk_to in chunks:
            if len(matches) >= limit:
                break
            for biz_div in biz_divs:
                if len(matches) >= limit:
                    break
                endpoint = _AWARD_ENDPOINTS[biz_div]
                params: dict = {
                    "pageNo": 1,
                    "numOfRows": page_size,
                    "inqryDiv": "1",
                }
                if chunk_from:
                    params["inqryBgnDt"] = chunk_from + "0000"
                if chunk_to:
                    params["inqryEndDt"] = chunk_to + "2359"

                try:
                    body = await client.call(endpoint, settings.g2b_key_award, params)
                except Exception:
                    continue

                if endpoint not in used_endpoints:
                    used_endpoints.append(endpoint)
                total_count += int(body.get("totalCount", 0) or 0)

                for raw in _extract_items(body):
                    if needs_client_filter:
                        if keyword:
                            title = raw.get("bidNtceNm") or ""
                            if keyword not in title:
                                continue
                        if inst_name:
                            inst = (raw.get("dminsttNm") or "") + " " + (raw.get("ntceInsttNm") or "")
                            if inst_name not in inst:
                                continue
                    key = (str(raw.get("bidNtceNo", "")), str(raw.get("bidNtceOrd", "")))
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    matches.append(_normalize_award_row(raw))
                    if len(matches) >= limit:
                        break
    finally:
        await client.aclose()

    return {
        "items": matches,
        "total_count": total_count,
        "returned_count": len(matches),
        "has_more": len(matches) >= limit,
        "endpoints_used": used_endpoints,
        "chunks_used": len(chunks),
    }


# === 3. get_award_detail ===

async def get_award_detail(bid_notice_no: str, bid_ord: str = "00") -> dict:
    """공고번호+차수로 낙찰 단건 상세 조회.

    5/3 N42: inqryDiv=4(단건) 미지원 케이스(R 형식 등)를 위해 inqryDiv=1 폴백 추가.
    """
    allowed, remaining = await check_rate("g2b_award_detail", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_award_detail 토큰 소진 (remaining={remaining})")

    # `-` suffix 통합 형태 자동 split
    if "-" in bid_notice_no and not bid_ord.strip("0"):
        parts = bid_notice_no.rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            bid_notice_no, bid_ord = parts[0], parts[1]

    norm_ord = bid_ord.lstrip("0") or "0"

    client = G2BClient(base_url=settings.g2b_award_base_url)
    try:
        # 1차: inqryDiv=4 단건
        for biz_div, endpoint in _AWARD_ENDPOINTS.items():
            params = {
                "pageNo": 1,
                "numOfRows": 1,
                "inqryDiv": "4",
                "bidNtceNo": bid_notice_no,
                "bidNtceOrd": bid_ord,
            }
            try:
                body = await client.call(endpoint, settings.g2b_key_award, params)
            except Exception:
                continue
            items = _extract_items(body)
            if items:
                return {
                    "found": True,
                    "biz_div": biz_div,
                    "endpoint": endpoint,
                    "lookup_mode": "inqryDiv=4",
                    "summary": _normalize_award_row(items[0]),
                    "raw": items[0],
                }

        # 2차 폴백: inqryDiv=1 + bidNtceNo (차수 무관 → 클라이언트측 매칭)
        for biz_div, endpoint in _AWARD_ENDPOINTS.items():
            params = {
                "pageNo": 1,
                "numOfRows": 50,
                "inqryDiv": "1",
                "bidNtceNo": bid_notice_no,
            }
            try:
                body = await client.call(endpoint, settings.g2b_key_award, params)
            except Exception:
                continue
            items = _extract_items(body)
            if not items:
                continue
            for raw in items:
                raw_ord = str(raw.get("bidNtceOrd", ""))
                raw_ord_norm = raw_ord.lstrip("0") or "0"
                if raw_ord_norm == norm_ord or raw_ord == bid_ord:
                    return {
                        "found": True,
                        "biz_div": biz_div,
                        "endpoint": endpoint,
                        "lookup_mode": "inqryDiv=1+ord_match",
                        "summary": _normalize_award_row(raw),
                        "raw": raw,
                    }
            # 차수 매칭 실패 시 첫 항목
            first = items[0]
            return {
                "found": True,
                "biz_div": biz_div,
                "endpoint": endpoint,
                "lookup_mode": "inqryDiv=1+first_only",
                "ord_mismatch_warning": f"요청 ord={bid_ord} 미발견. 첫 항목(ord={first.get('bidNtceOrd')}) 반환.",
                "summary": _normalize_award_row(first),
                "raw": first,
            }

        return {
            "found": False,
            "bid_notice_no": bid_notice_no,
            "bid_ord": bid_ord,
            "note": "낙찰 inqryDiv=4 + inqryDiv=1 폴백 모두 미발견. 공고번호·차수 확인 또는 개찰결과(list_bid_openings) 시도.",
        }
    finally:
        await client.aclose()


# === 4. search_awards_by_vendor (V4) ===

@cache_result(ttl=settings.cache_ttl_short, prefix="award_vendor")
async def search_awards_by_vendor(
    vendor_name: str | None = None,
    vendor_biz_no: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 20,
) -> dict:
    """업체명/사업자번호로 기간 내 낙찰 내역 조회.

    ScsbidInfoService에 사업자번호 직접 필터 없음 → 풀 페이지 스캔 + 클라이언트 필터.
    """
    if not (vendor_name or vendor_biz_no):
        raise ValueError("vendor_name 또는 vendor_biz_no 중 하나는 필수")

    allowed, remaining = await check_rate("g2b_award_vendor", capacity=5, refill_per_sec=0.5)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_award_vendor 토큰 소진 (remaining={remaining})")

    target_biz_no = _normalize_biz_no(vendor_biz_no)
    biz_divs = _resolve_biz_divs(biz_type)

    # 5/3 N40: G2B 낙찰정보서비스 numOfRows 최대 500 (999는 resultCode 07).
    # 5/3 N42: date range 1개월 초과 시 자동 chunking.
    page_size = 500
    max_scan_per_call = 1000  # 1 chunk * 1 biz_div 당 2페이지

    chunks = chunk_date_range(date_from, date_to, max_days=31)
    matches: list[dict] = []
    total_count = 0
    scanned_total = 0
    used_endpoints: list[str] = []
    seen_keys: set[tuple[str, str]] = set()

    client = G2BClient(base_url=settings.g2b_award_base_url)
    try:
        for chunk_from, chunk_to in chunks:
            if len(matches) >= limit:
                break
            for biz_div in biz_divs:
                if len(matches) >= limit:
                    break
                endpoint = _AWARD_ENDPOINTS[biz_div]
                scanned_in_call = 0
                page = 1
                while scanned_in_call < max_scan_per_call and len(matches) < limit:
                    params: dict = {
                        "pageNo": page,
                        "numOfRows": page_size,
                        "inqryDiv": "1",
                    }
                    if chunk_from:
                        params["inqryBgnDt"] = chunk_from + "0000"
                    if chunk_to:
                        params["inqryEndDt"] = chunk_to + "2359"

                    try:
                        body = await client.call(endpoint, settings.g2b_key_award, params)
                    except Exception:
                        break

                    if endpoint not in used_endpoints:
                        used_endpoints.append(endpoint)
                    total_count = max(total_count, int(body.get("totalCount", 0) or 0))
                    items_raw = _extract_items(body)
                    if not items_raw:
                        break

                    for raw in items_raw:
                        scanned_in_call += 1
                        scanned_total += 1
                        norm = _normalize_award_row(raw)
                        matched = False
                        if target_biz_no and norm.get("winner_biz_no") == target_biz_no:
                            matched = True
                        elif vendor_name and vendor_name in (norm.get("winner_name") or ""):
                            matched = True
                        if not matched:
                            continue
                        key = (str(norm.get("bid_notice_no") or ""), str(norm.get("bid_ord") or ""))
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        matches.append(norm)
                        if len(matches) >= limit:
                            break

                    if len(items_raw) < page_size:
                        break
                    page += 1
    finally:
        await client.aclose()

    return {
        "items": matches,
        "total_count": total_count,
        "scanned": scanned_total,
        "returned_count": len(matches),
        "has_more": len(matches) >= limit,
        "endpoints_used": used_endpoints,
        "chunks_used": len(chunks),
        "filter": {
            "vendor_biz_no": target_biz_no,
            "vendor_name": vendor_name,
            "date_range": [date_from, date_to],
            "biz_type": biz_type,
        },
    }


# === 5. list_bid_participants ===

async def list_bid_participants(
    bid_notice_no: str,
    bid_ord: str = "00",
) -> dict:
    """입찰공고번호로 응찰업체 목록 조회.

    ScsbidInfoService에 응찰업체 단독 endpoint 없음 → 개찰결과(getOpengResultListInfo*) 응답 row를 사용.
    각 row가 응찰업체 1건이라는 가정 (Bravo Research 결과 confidence: medium-low).
    실 응답 검증 후 필드명 조정 가능.
    """
    allowed, remaining = await check_rate("g2b_participants", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_participants 토큰 소진 (remaining={remaining})")

    client = G2BClient(base_url=settings.g2b_award_base_url)
    try:
        for biz_div, endpoint in _OPENING_ENDPOINTS.items():
            params = {
                "pageNo": 1,
                "numOfRows": 100,
                "inqryDiv": "4",
                "bidNtceNo": bid_notice_no,
                "bidNtceOrd": bid_ord,
            }
            try:
                body = await client.call(endpoint, settings.g2b_key_award, params)
            except Exception:
                continue
            items_raw = _extract_items(body)
            if items_raw:
                rows = [_normalize_opening_row(r) for r in items_raw]
                return {
                    "found": True,
                    "biz_div": biz_div,
                    "endpoint": endpoint,
                    "bid_notice_no": bid_notice_no,
                    "bid_ord": bid_ord,
                    "items": rows,
                    "participant_count": len(rows),
                }
        return {
            "found": False,
            "bid_notice_no": bid_notice_no,
            "bid_ord": bid_ord,
            "items": [],
            "note": "개찰결과 4종 endpoint 모두 미발견. 공고번호·차수 확인 또는 입찰이 아직 개찰되지 않음.",
        }
    finally:
        await client.aclose()


# === 호환성 ===

async def placeholder_award() -> dict:
    """award 영역 도구 자리표시자. 호환성을 위해 유지."""
    return {"status": "not_implemented", "domain": "award"}
