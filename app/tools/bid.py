"""입찰공고 영역 MCP 도구."""
from __future__ import annotations
from app.clients.g2b import G2BClient
from app.config import settings
from app.core.cache import cache_result
from app.core.daterange import chunk_date_range
from app.core.rate_limit import check_rate
from app.schemas.bid import BidNoticeSearchInput, BidNoticeSearchResult, BidNoticeSummary


_BIZ_DIV_MAP = {"공사": "1", "용역": "2", "물품": "3"}


def _infer_period_from_bid_no(bid_notice_no: str) -> tuple[str | None, str | None]:
    """공고번호 prefix에서 연도 추정해 inqryBgnDt/inqryEndDt 자동 생성.

    G2B 단건 조회 inqryDiv=1 폴백에서 기간 필수 → 공고번호 자체에 인코딩된 연도 사용.
    - 'R26...' / 'R25...' → 2026 / 2025년
    - '20240101234' (숫자 11자리) → 첫 4자리 연도
    추정 불가 시 (None, None).
    """
    s = (bid_notice_no or "").strip().upper()
    # R 형식 (R + 2자리 연도)
    if len(s) >= 3 and s.startswith("R") and s[1:3].isdigit():
        yy = int(s[1:3])
        year = 2000 + yy if yy < 80 else 1900 + yy
        return f"{year}0101", f"{year}1231"
    # 숫자 11자리 (예: 20240101234)
    if len(s) >= 4 and s[:4].isdigit():
        year = int(s[:4])
        if 2000 <= year <= 2100:
            return f"{year}0101", f"{year}1231"
    return None, None


def _resolve_bid_endpoints(biz_type: str | None) -> list[tuple[str, str]]:
    """biz_type별 endpoint 목록. None이면 3종 모두 (공사/용역/물품).

    반환: [(biz_div_label, endpoint_path), ...]
    """
    if biz_type == "공사":
        return [("공사", "/BidPublicInfoService/getBidPblancListInfoCnstwk")]
    if biz_type == "물품":
        return [("물품", "/BidPublicInfoService/getBidPblancListInfoThng")]
    if biz_type == "용역":
        return [("용역", "/BidPublicInfoService/getBidPblancListInfoServc")]
    # 전체 (None 또는 잘못된 값)
    return [
        ("용역", "/BidPublicInfoService/getBidPblancListInfoServc"),
        ("공사", "/BidPublicInfoService/getBidPblancListInfoCnstwk"),
        ("물품", "/BidPublicInfoService/getBidPblancListInfoThng"),
    ]


def _to_int(v) -> int | None:
    try:
        return int(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _normalize_notice(raw: dict) -> BidNoticeSummary:
    """G2B 응답 한 건을 정규화."""
    return BidNoticeSummary(
        bid_no=str(raw.get("bidNtceNo", "")),
        bid_ord=str(raw.get("bidNtceOrd", "")) or None,
        title=str(raw.get("bidNtceNm", "")),
        inst_name=raw.get("ntceInsttNm") or raw.get("dminsttNm"),
        biz_type=raw.get("bsnsDivNm"),
        region=raw.get("rgnLmtBidLocplcNm"),
        estimated_price=_to_int(raw.get("presmptPrce") or raw.get("asignBdgtAmt")),
        publish_date=raw.get("bidNtceDt"),
        deadline_date=raw.get("bidClseDt"),
        raw=raw,
    )


@cache_result(ttl=settings.cache_ttl_short, prefix="bid")
async def search_bid_notices(
    keyword: str | None = None,
    biz_type: str | None = None,
    region: str | None = None,
    inst_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
    page: int = 1,
    scan_pages: int = 1,
    bid_notice_no: str | None = None,
) -> dict:
    """나라장터 입찰공고를 키워드/업종/지역/기관/기간으로 검색합니다.

    5/3 N42 update:
    - biz_type=None 또는 ''면 공사+용역+물품 3종 endpoint 병합
    - date 범위 1개월 초과 시 자동 chunking (G2B 1개월 제약 대응)

    Args:
        keyword: 공고 제목 부분일치 키워드 (예: '정보화', '용역', 'AI')
        biz_type: '공사' | '용역' | '물품' (None/'' = 전체 3종 병합)
        region: 지역 제한 (시도명)
        inst_name: 발주기관명 부분일치
        date_from: 공고일 시작 (YYYYMMDD)
        date_to: 공고일 종료 (YYYYMMDD)
        limit: 최대 반환 건수 (1~100)
        page: 시작 페이지 번호 (default 1). cursor 페이징.
        scan_pages: 스캔할 페이지 수 (default 1, max 10).

    Returns:
        items, total_count, returned_count, has_more, page, endpoints_used, chunks_used 포함 dict.
    """
    allowed, remaining = await check_rate("g2b_bid", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_bid 토큰 소진 (remaining={remaining})")

    inp = BidNoticeSearchInput(
        keyword=keyword, biz_type=biz_type, region=region,
        inst_name=inst_name, date_from=date_from, date_to=date_to, limit=limit,
        page=page, bid_notice_no=bid_notice_no,
    )
    max_scan_pages = max(1, min(int(scan_pages), 10))

    # 5/3 N42 v12: bid_notice_no 정확 매칭 모드 — 추정 기간 자동 + 매칭 시 즉시 반환
    if inp.bid_notice_no and not inp.date_from and not inp.date_to:
        bgn, end = _infer_period_from_bid_no(inp.bid_notice_no)
        if bgn and end:
            inp.date_from = bgn
            inp.date_to = end

    # 업종 endpoint (None → 3종 병합)
    endpoints = _resolve_bid_endpoints(inp.biz_type)
    # 1개월 초과 시 chunk 자동 분할 (G2B 1개월 제약)
    chunks = chunk_date_range(inp.date_from, inp.date_to, max_days=31)

    needs_client_filter = bool(inp.keyword or inp.inst_name or inp.region or inp.bid_notice_no)
    page_size = 999 if needs_client_filter else inp.limit
    max_scan_per_call = page_size * max_scan_pages

    seen_keys: set[tuple[str, str]] = set()  # (bid_no, bid_ord) dedup
    matches: list[dict] = []
    total_count = 0
    scanned_total = 0
    endpoints_used: list[str] = []

    client = G2BClient()
    try:
        for chunk_from, chunk_to in chunks:
            if len(matches) >= inp.limit:
                break
            for biz_label, endpoint in endpoints:
                if len(matches) >= inp.limit:
                    break
                cur_page = inp.page
                scanned_in_call = 0
                while scanned_in_call < max_scan_per_call and len(matches) < inp.limit:
                    params: dict = {
                        "pageNo": cur_page,
                        "numOfRows": page_size,
                        "inqryDiv": "1",  # 등록일 기준
                    }
                    if chunk_from:
                        params["inqryBgnDt"] = chunk_from + "0000"
                    if chunk_to:
                        params["inqryEndDt"] = chunk_to + "2359"

                    try:
                        body = await client.call(endpoint, settings.g2b_key_bid, params)
                    except Exception:  # noqa: BLE001
                        break

                    if endpoint not in endpoints_used:
                        endpoints_used.append(endpoint)
                    total_count += int(body.get("totalCount", 0) or 0)

                    items_raw = body.get("items", [])
                    if isinstance(items_raw, dict):
                        items_raw = items_raw.get("item", [])
                    if not isinstance(items_raw, list):
                        items_raw = [items_raw] if items_raw else []
                    if not items_raw:
                        break

                    for raw in items_raw:
                        scanned_in_call += 1
                        scanned_total += 1
                        if needs_client_filter:
                            title = raw.get("bidNtceNm") or ""
                            inst = (raw.get("dminsttNm") or "") + " " + (raw.get("ntceInsttNm") or "")
                            region_v = raw.get("rgnLmtBidLocplcNm") or ""
                            if inp.bid_notice_no and str(raw.get("bidNtceNo", "")) != inp.bid_notice_no:
                                continue
                            if inp.keyword and inp.keyword not in title:
                                continue
                            if inp.inst_name and inp.inst_name not in inst:
                                continue
                            if inp.region and inp.region not in region_v:
                                continue
                        key = (str(raw.get("bidNtceNo", "")), str(raw.get("bidNtceOrd", "")))
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        matches.append(_normalize_notice(raw).model_dump())
                        if len(matches) >= inp.limit:
                            break

                    if len(items_raw) < page_size:
                        break
                    cur_page += 1
    finally:
        await client.aclose()

    has_more = (
        (total_count > inp.page * page_size * len(endpoints))
        if (max_scan_pages == 1 and len(chunks) == 1)
        else (total_count > scanned_total and len(matches) >= inp.limit)
    )

    return {
        **BidNoticeSearchResult(
            items=matches,
            total_count=total_count,
            returned_count=len(matches),
            has_more=has_more,
            page=inp.page,
        ).model_dump(),
        "endpoints_used": endpoints_used,
        "chunks_used": len(chunks),
        "scanned": scanned_total,
    }


# === Phase 3: 사전규격 + 입찰공고 단건 상세 ===

# 사전규격 업종별 endpoint (BidPublicInfoService 산하 — Research Team Alpha confidence: medium)
_PRESPEC_ENDPOINTS = {
    "1": "/BidPublicInfoService/getPrdctClsfcNoPblancListInfoCnstwk",  # 공사
    "2": "/BidPublicInfoService/getPrdctClsfcNoPblancListInfoServc",  # 용역
    "3": "/BidPublicInfoService/getPrdctClsfcNoPblancListInfoThng",  # 물품
}

# 입찰공고 업종별 endpoint (운영 검증됨)
_BID_ENDPOINTS = {
    "1": "/BidPublicInfoService/getBidPblancListInfoCnstwk",
    "2": "/BidPublicInfoService/getBidPblancListInfoServc",
    "3": "/BidPublicInfoService/getBidPblancListInfoThng",
}


def _pick_first_item(body: dict) -> dict | None:
    """G2B body에서 items 배열 첫 항목 안전 추출."""
    items = body.get("items", [])
    if isinstance(items, dict):
        items = items.get("item", [])
    if not isinstance(items, list):
        items = [items] if items else []
    return items[0] if items else None


async def get_bid_notice_detail(bid_notice_no: str, bid_ord: str = "00") -> dict:
    """공고번호+차수로 입찰공고 단건 상세를 조회합니다.

    5/3 N42: 단건 inqryDiv=3 미지원 endpoint 케이스(R 형식 등)를 위해 inqryDiv=1 폴백 추가.
    1차: inqryDiv=3 + bidNtceNo + bidNtceOrd
    2차 폴백: inqryDiv=1 + bidNtceNo (차수 무관) → 클라이언트측 차수 매칭

    Args:
        bid_notice_no: 입찰공고번호 (예: '20240101234' 또는 'R26BK01435763')
        bid_ord: 공고차수 (기본 "00", "000"/"01" 등 가능)

    Returns:
        공고 상세 dict (raw 포함). 미발견 시 found=False.
    """
    allowed, remaining = await check_rate("g2b_bid_detail", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_bid_detail 토큰 소진 (remaining={remaining})")

    # `-` suffix 통합 형태("R26BK01435763-000") 자동 split
    if "-" in bid_notice_no and not bid_ord.strip("0"):
        parts = bid_notice_no.rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            bid_notice_no, bid_ord = parts[0], parts[1]

    norm_ord = bid_ord.lstrip("0") or "0"  # "000" → "0", "01" → "1"

    client = G2BClient()
    try:
        # 1차: inqryDiv=3 (단건 직접)
        for biz_div, endpoint in _BID_ENDPOINTS.items():
            params = {
                "pageNo": 1,
                "numOfRows": 1,
                "inqryDiv": "3",
                "bidNtceNo": bid_notice_no,
                "bidNtceOrd": bid_ord,
            }
            try:
                body = await client.call(endpoint, settings.g2b_key_bid, params)
            except Exception:  # noqa: BLE001
                continue
            item = _pick_first_item(body)
            if item:
                return {
                    "found": True,
                    "biz_div": biz_div,
                    "endpoint": endpoint,
                    "lookup_mode": "inqryDiv=3",
                    "summary": _normalize_notice(item).model_dump(),
                    "raw": item,
                }

        # 2차 폴백: inqryDiv=1 + bidNtceNo (차수 무관 검색).
        # G2B는 inqryDiv=1에 inqryBgnDt/inqryEndDt 기간 필수 → 공고번호 prefix로 추정 기간 자동 설정.
        # R26... = 2026년, 20240101234 = 2024년 등 prefix 기반.
        bgn_dt, end_dt = _infer_period_from_bid_no(bid_notice_no)

        for biz_div, endpoint in _BID_ENDPOINTS.items():
            params = {
                "pageNo": 1,
                "numOfRows": 999,
                "inqryDiv": "1",
                "bidNtceNo": bid_notice_no,
            }
            if bgn_dt and end_dt:
                params["inqryBgnDt"] = bgn_dt + "0000"
                params["inqryEndDt"] = end_dt + "2359"
            try:
                body = await client.call(endpoint, settings.g2b_key_bid, params)
            except Exception:  # noqa: BLE001
                continue

            items_raw = body.get("items", [])
            if isinstance(items_raw, dict):
                items_raw = items_raw.get("item", [])
            if not isinstance(items_raw, list):
                items_raw = [items_raw] if items_raw else []
            if not items_raw:
                continue

            # bidNtceNo + bidNtceOrd 매칭 (G2B inqryDiv=1은 bidNtceNo 파라미터 무시 → 999개 중 클라이언트 필터)
            for raw in items_raw:
                raw_no = str(raw.get("bidNtceNo", ""))
                if raw_no != bid_notice_no:
                    continue
                raw_ord = str(raw.get("bidNtceOrd", ""))
                raw_ord_norm = raw_ord.lstrip("0") or "0"
                if raw_ord_norm == norm_ord or raw_ord == bid_ord:
                    return {
                        "found": True,
                        "biz_div": biz_div,
                        "endpoint": endpoint,
                        "lookup_mode": "inqryDiv=1+no_ord_match",
                        "summary": _normalize_notice(raw).model_dump(),
                        "raw": raw,
                    }

        # bid_no 동일 + 다른 ord 라도 있으면 첫 항목 반환 (참고용)
        for biz_div, endpoint in _BID_ENDPOINTS.items():
            params = {
                "pageNo": 1,
                "numOfRows": 999,
                "inqryDiv": "1",
                "bidNtceNo": bid_notice_no,
            }
            if bgn_dt and end_dt:
                params["inqryBgnDt"] = bgn_dt + "0000"
                params["inqryEndDt"] = end_dt + "2359"
            try:
                body = await client.call(endpoint, settings.g2b_key_bid, params)
            except Exception:  # noqa: BLE001
                continue
            items_raw = body.get("items", [])
            if isinstance(items_raw, dict):
                items_raw = items_raw.get("item", [])
            if not isinstance(items_raw, list):
                items_raw = [items_raw] if items_raw else []
            for raw in items_raw:
                if str(raw.get("bidNtceNo", "")) == bid_notice_no:
                    return {
                        "found": True,
                        "biz_div": biz_div,
                        "endpoint": endpoint,
                        "lookup_mode": "inqryDiv=1+no_only_ord_diff",
                        "ord_mismatch_warning": f"요청 ord={bid_ord} 미발견. 다른 차수(ord={raw.get('bidNtceOrd')}) 반환.",
                        "summary": _normalize_notice(raw).model_dump(),
                        "raw": raw,
                    }

        # 3차 폴백: search_bid_notices(bid_notice_no=...) — 최근 30일 우선 시도
        # 1년 chunks 12 × 3 endpoints = 비효율 → 최근 30일로 우선, 추후 라운드에서 확장
        from datetime import datetime, timedelta
        today = datetime.now()
        recent_from = (today - timedelta(days=30)).strftime("%Y%m%d")
        recent_to = today.strftime("%Y%m%d")
        try:
            search_result = await search_bid_notices(
                bid_notice_no=bid_notice_no,
                limit=3,
                scan_pages=2,
                date_from=recent_from,
                date_to=recent_to,
            )
            for item in search_result.get("items", []):
                if str(item.get("bid_no", "")) == bid_notice_no:
                    item_ord = str(item.get("bid_ord") or "")
                    item_ord_norm = item_ord.lstrip("0") or "0"
                    if item_ord_norm == norm_ord or item_ord == bid_ord:
                        return {
                            "found": True,
                            "lookup_mode": "search_bid_notices+ord_match",
                            "summary": item,
                            "raw": item.get("raw", item),
                        }
            # ord 다른 차수라도 first match
            first_match = next(
                (it for it in search_result.get("items", []) if str(it.get("bid_no", "")) == bid_notice_no),
                None,
            )
            if first_match:
                return {
                    "found": True,
                    "lookup_mode": "search_bid_notices+no_only",
                    "ord_mismatch_warning": f"요청 ord={bid_ord} 미발견. 다른 차수(ord={first_match.get('bid_ord')}) 반환.",
                    "summary": first_match,
                    "raw": first_match.get("raw", first_match),
                }
        except Exception:  # noqa: BLE001
            pass

        return {
            "found": False,
            "bid_notice_no": bid_notice_no,
            "bid_ord": bid_ord,
            "note": "inqryDiv=3 단건 + inqryDiv=1 폴백 + search_bid_notices 매칭 모두 미발견. 공고번호·차수 확인 또는 사전규격(get_pre_specification_detail) 시도.",
        }
    finally:
        await client.aclose()


@cache_result(ttl=settings.cache_ttl_short, prefix="bid_prespec")
async def list_pre_specifications(
    keyword: str | None = None,
    biz_type: str | None = None,
    inst_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict:
    """사전규격공개 목록을 조회합니다.

    BidPublicInfoService `getPrdctClsfcNoPblancList...` 시리즈 사용.
    `G2B_KEY_PRESPEC` 우선, 없으면 `G2B_KEY_BID`로 fallback.

    Args:
        keyword: 사전규격명 부분일치
        biz_type: '공사' | '용역' | '물품'
        inst_name: 발주기관명 부분일치
        date_from / date_to: 등록일 (YYYYMMDD)
        limit: 최대 반환 건수
    """
    allowed, remaining = await check_rate("g2b_prespec", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_prespec 토큰 소진 (remaining={remaining})")

    biz_div = _BIZ_DIV_MAP.get(biz_type) if biz_type else None
    endpoint = _PRESPEC_ENDPOINTS.get(biz_div, _PRESPEC_ENDPOINTS["2"])  # default: 용역
    service_key = settings.g2b_key_prespec or settings.g2b_key_bid

    needs_client_filter = bool(keyword or inst_name)
    page_size = 999 if needs_client_filter else max(limit, 20)
    max_scan = 30000

    matches: list[dict] = []
    page = 1
    scanned = 0
    total_count = 0

    client = G2BClient()
    try:
        while len(matches) < limit and scanned < max_scan:
            params: dict = {
                "pageNo": page,
                "numOfRows": page_size,
                "inqryDiv": "1",  # 등록일
            }
            if date_from:
                params["inqryBgnDt"] = date_from + "0000"
            if date_to:
                params["inqryEndDt"] = date_to + "2359"

            try:
                body = await client.call(endpoint, service_key, params)
            except Exception as exc:  # noqa: BLE001
                return {
                    "status": "endpoint_error",
                    "endpoint": endpoint,
                    "error": str(exc)[:200],
                    "note": "사전규격 endpoint 추정 — 운영 IP에서 검증 후 메서드명 조정 필요",
                    "items": [],
                    "total_count": 0,
                    "returned_count": 0,
                    "has_more": False,
                }

            total_count = int(body.get("totalCount", 0))
            items_raw = body.get("items", [])
            if isinstance(items_raw, dict):
                items_raw = items_raw.get("item", [])
            if not isinstance(items_raw, list):
                items_raw = [items_raw] if items_raw else []
            if not items_raw:
                break

            for raw in items_raw:
                scanned += 1
                if needs_client_filter:
                    title = raw.get("bidNtceNm") or raw.get("prdctClsfcNoNm") or ""
                    inst = (raw.get("dminsttNm") or "") + " " + (raw.get("ntceInsttNm") or "")
                    if keyword and keyword not in title:
                        continue
                    if inst_name and inst_name not in inst:
                        continue
                matches.append(_normalize_notice(raw).model_dump())
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
        "returned_count": len(matches),
        "has_more": (total_count > scanned) and (len(matches) >= limit),
        "endpoint": endpoint,
    }


async def get_pre_specification_detail(bid_notice_no: str, bid_ord: str = "00") -> dict:
    """공고번호+차수로 사전규격 단건 상세를 조회합니다.

    `getPrdctClsfcNoPblancList...` 시리즈에 `inqryDiv=3` + `bidNtceNo`+`bidNtceOrd` 단건 패턴.
    """
    allowed, remaining = await check_rate("g2b_prespec_detail", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_prespec_detail 토큰 소진 (remaining={remaining})")

    service_key = settings.g2b_key_prespec or settings.g2b_key_bid
    client = G2BClient()
    try:
        for biz_div, endpoint in _PRESPEC_ENDPOINTS.items():
            params = {
                "pageNo": 1,
                "numOfRows": 1,
                "inqryDiv": "3",
                "bidNtceNo": bid_notice_no,
                "bidNtceOrd": bid_ord,
            }
            try:
                body = await client.call(endpoint, service_key, params)
            except Exception:
                continue
            item = _pick_first_item(body)
            if item:
                return {
                    "found": True,
                    "biz_div": biz_div,
                    "endpoint": endpoint,
                    "summary": _normalize_notice(item).model_dump(),
                    "raw": item,
                }
        return {
            "found": False,
            "bid_notice_no": bid_notice_no,
            "bid_ord": bid_ord,
            "note": "사전규격 endpoint 3종 모두 미발견. 사전규격이 아니라 본 입찰공고일 수 있음 — get_bid_notice_detail 시도 권장.",
        }
    finally:
        await client.aclose()
