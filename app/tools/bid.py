"""입찰공고 영역 MCP 도구."""
from __future__ import annotations
import asyncio
import structlog
from app.clients.g2b import G2BClient
from app.config import settings
from app.core.cache import cache_result
from app.core.daterange import chunk_date_range
from app.core.rate_limit import check_rate
from app.schemas.bid import BidNoticeSearchInput, BidNoticeSearchResult, BidNoticeSummary

log = structlog.get_logger(__name__)


_BIZ_DIV_MAP = {"공사": "1", "용역": "2", "물품": "3"}


def _infer_period_from_bid_no(bid_notice_no: str) -> tuple[str | None, str | None]:
    """공고번호 prefix 기반 기간 추정 — P31-R1 폐기 (항상 (None, None)).

    DOSSIER-OFFICIAL §3: G2B inqryBgnDt/inqryEndDt 범위는 최대 1개월 제한.
    기존 1년 통째(`{year}0101`-`{year}1231`) 반환 → 제약 위반으로 응답 결손 가능.
    POC #4 evidence: inqryDiv=2 + bidNtceNo만 전달 시 기간 unset에도 정상 매칭 →
    단건 모드는 기간 자체가 불필요. 함수는 award.py 호환을 위해 유지하되 동작은 no-op.
    """
    _ = bid_notice_no  # 인자 보존 (시그니처 호환)
    return None, None


def _resolve_bid_endpoints(biz_type: str | None) -> list[tuple[str, str]]:
    """biz_type별 단일조회 endpoint 목록 (단건 모드용). None이면 4종 병합.

    P31-R1 (F20): 외자(Frgcpt) endpoint 추가.
    DOSSIER-OFFICIAL §1.2: BidPublicInfoService 4분류 endpoint
    (Cnstwk/Servc/Thng/Frgcpt). 기타(Etc)는 PPSSrch에만 존재 → 단일조회는 4종.

    반환: [(biz_div_label, endpoint_path), ...]
    """
    if biz_type == "공사":
        return [("공사", "/BidPublicInfoService/getBidPblancListInfoCnstwk")]
    if biz_type == "물품":
        return [("물품", "/BidPublicInfoService/getBidPblancListInfoThng")]
    if biz_type == "용역":
        return [("용역", "/BidPublicInfoService/getBidPblancListInfoServc")]
    if biz_type == "외자":
        return [("외자", "/BidPublicInfoService/getBidPblancListInfoFrgcpt")]
    # 전체 (None 또는 잘못된 값) — 4종 병합 (외자 포함)
    return [
        ("용역", "/BidPublicInfoService/getBidPblancListInfoServc"),
        ("공사", "/BidPublicInfoService/getBidPblancListInfoCnstwk"),
        ("물품", "/BidPublicInfoService/getBidPblancListInfoThng"),
        ("외자", "/BidPublicInfoService/getBidPblancListInfoFrgcpt"),
    ]


# P31-R2 (F19): PPSSrch 검색 endpoint 5종 매핑.
# DOSSIER-OFFICIAL §4 + POC #1·#2·#3·#5·#7: PPSSrch는 LIKE 매칭(ntceInsttNm/dminsttNm/bidNtceNm)
# + indstrytyCd 서버측 필터 + Etc 포함 5분류. inqryDiv=1 = 공고게시일시 (단일조회 inqryDiv=1과 의미 다름).
_BID_ENDPOINTS_PPSSRCH = {
    "공사": "/BidPublicInfoService/getBidPblancListInfoCnstwkPPSSrch",
    "용역": "/BidPublicInfoService/getBidPblancListInfoServcPPSSrch",
    "물품": "/BidPublicInfoService/getBidPblancListInfoThngPPSSrch",
    "외자": "/BidPublicInfoService/getBidPblancListInfoFrgcptPPSSrch",
    "기타": "/BidPublicInfoService/getBidPblancListInfoEtcPPSSrch",
}


def _resolve_ppssrch_endpoints(biz_type: str | None) -> list[tuple[str, str]]:
    """biz_type별 PPSSrch endpoint 목록 (검색 모드용). None이면 5종 병합."""
    if biz_type and biz_type in _BID_ENDPOINTS_PPSSRCH:
        return [(biz_type, _BID_ENDPOINTS_PPSSRCH[biz_type])]
    return [(label, ep) for label, ep in _BID_ENDPOINTS_PPSSRCH.items()]


# P31-R1: bid_notice_no 단건 매칭 모드용 5종 단일조회 endpoint
# DOSSIER-OFFICIAL §1.2 + POC #4: 외부 호출자는 사업 분류 미지 → 5종 fan-out
# inqryDiv=2 + bidNtceNo 직접 → 기간 unset OK
_BID_DETAIL_ENDPOINTS = [
    ("공사", "/BidPublicInfoService/getBidPblancListInfoCnstwk"),
    ("용역", "/BidPublicInfoService/getBidPblancListInfoServc"),
    ("물품", "/BidPublicInfoService/getBidPblancListInfoThng"),
    ("외자", "/BidPublicInfoService/getBidPblancListInfoFrgcpt"),
    ("기타", "/BidPublicInfoService/getBidPblancListInfoEtc"),
]


def _to_int(v) -> int | None:
    try:
        return int(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _normalize_notice(raw: dict) -> BidNoticeSummary:
    """G2B 응답 한 건을 정규화.

    P31-R2:
    - F21: srvce_div + ppsw_gnrl_yn 신규 필드 (POC #5 raw evidence)
    - PubStd 호환: inst_name fallback 순서 ntceInsttNm > dminsttNm > dmndInsttNm
    """
    return BidNoticeSummary(
        bid_no=str(raw.get("bidNtceNo", "")),
        bid_ord=str(raw.get("bidNtceOrd", "")) or None,
        title=str(raw.get("bidNtceNm", "")),
        inst_name=raw.get("ntceInsttNm") or raw.get("dminsttNm") or raw.get("dmndInsttNm"),
        biz_type=raw.get("bsnsDivNm"),  # PPSSrch 응답에선 null (POC #5)
        srvce_div=raw.get("srvceDivNm"),  # "일반용역" / "기술용역"
        ppsw_gnrl_yn=raw.get("ppswGnrlSrvceYn"),  # Y/N
        region=raw.get("rgnLmtBidLocplcNm"),
        estimated_price=_to_int(raw.get("presmptPrce") or raw.get("asignBdgtAmt")),
        publish_date=raw.get("bidNtceDt"),
        deadline_date=raw.get("bidClseDt"),
        raw=raw,
    )


async def _search_by_bid_notice_no(inp: BidNoticeSearchInput) -> dict:
    """P31-R1 (F18): bid_notice_no 단건 매칭 모드.

    inqryDiv=2 + bidNtceNo 직접 → 기간 unset, 5종 단일조회 endpoint 병렬 fan-out.
    매칭 row 발견 즉시 반환 (POC #4 raw evidence: R25BK00755515 → Servc 1개에서만 hit).

    DOSSIER-OFFICIAL §3.1 + POC #4 결론:
    - 1개월 제한 회피 (기간 자체 미전달)
    - _infer_period_from_bid_no 1년 통째 폴백 불필요
    - 외부 호출자는 사업 분류 미지 → 5종 fan-out 필수
    """
    target_no = (inp.bid_notice_no or "").strip()
    target_ord_norm: str | None = None
    if "-" in target_no:
        parts = target_no.rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            target_no = parts[0]
            target_ord_norm = parts[1].lstrip("0") or "0"

    async def _call_one(label: str, endpoint: str):
        params = {
            "pageNo": 1,
            "numOfRows": 10,
            "inqryDiv": "2",  # 입찰공고번호 직접조회 (단건)
            "bidNtceNo": target_no,
        }
        try:
            body = await client.call(endpoint, settings.g2b_key_bid, params)
        except Exception:  # noqa: BLE001
            return label, endpoint, 0, []
        items_raw = body.get("items", [])
        if isinstance(items_raw, dict):
            items_raw = items_raw.get("item", [])
        if not isinstance(items_raw, list):
            items_raw = [items_raw] if items_raw else []
        return label, endpoint, int(body.get("totalCount", 0) or 0), items_raw

    matches: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()
    endpoints_used: list[str] = []
    total_count = 0
    scanned_total = 0

    client = G2BClient()
    try:
        results = await asyncio.gather(
            *(_call_one(label, ep) for label, ep in _BID_DETAIL_ENDPOINTS)
        )
        for _label, endpoint, local_total, items_raw in results:
            if items_raw and endpoint not in endpoints_used:
                endpoints_used.append(endpoint)
            total_count += local_total
            for raw in items_raw:
                scanned_total += 1
                if str(raw.get("bidNtceNo", "")) != target_no:
                    continue
                if target_ord_norm is not None:
                    raw_ord_norm = str(raw.get("bidNtceOrd", "")).lstrip("0") or "0"
                    if raw_ord_norm != target_ord_norm:
                        continue
                key = (str(raw.get("bidNtceNo", "")), str(raw.get("bidNtceOrd", "")))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                matches.append(_normalize_notice(raw).model_dump())
                if len(matches) >= inp.limit:
                    break
            if len(matches) >= inp.limit:
                break
    finally:
        await client.aclose()

    return {
        **BidNoticeSearchResult(
            items=matches,
            total_count=total_count,
            returned_count=len(matches),
            has_more=False,  # 단건 모드는 페이지 개념 없음
            page=inp.page,
        ).model_dump(),
        "endpoints_used": endpoints_used,
        "chunks_used": 0,  # 단건 모드는 기간 unset → chunk 없음
        "scanned": scanned_total,
        "lookup_mode": "inqryDiv=2+bidNtceNo",
    }


@cache_result(ttl=settings.cache_ttl_short, prefix="bid_v32")
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
    indstryty_cd: str | None = None,
) -> dict:
    """나라장터 입찰공고를 키워드/업종/지역/기관/기간으로 검색합니다.

    P31-R2 (F19+F21):
    - 검색 모드는 PPSSrch endpoint 5종 (Cnstwk/Servc/Thng/Frgcpt/Etc) 사용 — LIKE 매칭 직접 지원
    - inst_name 입력 시 ntceInsttNm + dminsttNm 두 호출 fan-out + union dedup (POC #7 AND 회피)
    - keyword → bidNtceNm, indstryty_cd → indstrytyCd 서버측 필터
    - 단건 모드(bid_notice_no, R1)는 격리 보전 — 단일조회 endpoint inqryDiv=2 그대로

    Args:
        keyword: 공고명 부분일치 (PPSSrch bidNtceNm 직접 전달)
        biz_type: '공사' | '용역' | '물품' | '외자' | '기타' (None = 5종 병합)
        region: 지역 제한 (시도명, client-side filter)
        inst_name: 발주기관명 부분일치 (ntceInsttNm + dminsttNm fan-out)
        indstryty_cd: 업종코드 (G2B indstrytyCd 서버측 필터)
        date_from / date_to: 공고일 (YYYYMMDD)
        limit: 최대 반환 건수 (1~100)
        page: 시작 페이지 번호
        scan_pages: 스캔 페이지 수 (max 10)
        bid_notice_no: 단건 모드 진입 (date 미명시 + 본 인자 → inqryDiv=2)

    Returns:
        items, total_count, returned_count, has_more, page, endpoints_used, chunks_used 포함 dict.
    """
    allowed, remaining = await check_rate("g2b_bid", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_bid 토큰 소진 (remaining={remaining})")

    inp = BidNoticeSearchInput(
        keyword=keyword, biz_type=biz_type, region=region,
        inst_name=inst_name, indstryty_cd=indstryty_cd,
        date_from=date_from, date_to=date_to, limit=limit,
        page=page, bid_notice_no=bid_notice_no,
    )
    max_scan_pages = max(1, min(int(scan_pages), 10))

    # P31-R1 (F18): bid_notice_no 단건 매칭 모드 — inqryDiv=2 + bidNtceNo 직접
    # 단건 모드는 격리 보전 (R1 회귀 0).
    if inp.bid_notice_no and not inp.date_from and not inp.date_to:
        return await _search_by_bid_notice_no(inp)

    # P31-R2 (F19): PPSSrch endpoint 5종 (None → 5종 병합).
    endpoints = _resolve_ppssrch_endpoints(inp.biz_type)
    # 1개월 초과 시 chunk 자동 분할 (G2B 1개월 제약)
    chunks = chunk_date_range(inp.date_from, inp.date_to, max_days=31)

    # PPSSrch는 keyword/inst_name/indstryty_cd를 서버측 LIKE/필터로 처리.
    # region/bid_notice_no 만 client-side 필터 필요.
    needs_client_filter = bool(inp.region or inp.bid_notice_no)
    page_size = 100 if needs_client_filter else min(inp.limit, 100)
    max_scan_per_call = page_size * max_scan_pages

    # F19 fan-out: inst_name 있으면 ntceInsttNm + dminsttNm 두 호출 (POC #7 AND 회피).
    inst_variants: list[tuple[str, str | None]]
    if inp.inst_name:
        inst_variants = [("ntceInsttNm", inp.inst_name), ("dminsttNm", inp.inst_name)]
    else:
        inst_variants = [("none", None)]

    seen_keys: set[tuple[str, str]] = set()  # (bid_no, bid_ord) union dedup
    matches: list[dict] = []
    total_count = 0
    scanned_total = 0
    endpoints_used: list[str] = []

    client = G2BClient()

    async def _fetch_combo(
        chunk_from: str | None,
        chunk_to: str | None,
        endpoint: str,
        inst_field: str,
        inst_value: str | None,
    ):
        local_total = 0
        local_scanned = 0
        local_raw_items: list = []
        cur_page = inp.page
        scanned_in_call = 0
        while scanned_in_call < max_scan_per_call:
            params: dict = {
                "pageNo": cur_page,
                "numOfRows": page_size,
                "inqryDiv": "1",  # PPSSrch: 1=공고게시일시
                "type": "json",
            }
            if chunk_from:
                params["inqryBgnDt"] = chunk_from + "0000"
            if chunk_to:
                params["inqryEndDt"] = chunk_to + "2359"
            # F19: PPSSrch 서버측 LIKE 직접 전달
            if inp.keyword:
                params["bidNtceNm"] = inp.keyword
            if inp.indstryty_cd:
                params["indstrytyCd"] = inp.indstryty_cd
            if inst_value:
                params[inst_field] = inst_value
            try:
                body = await client.call(endpoint, settings.g2b_key_bid, params)
            except Exception:  # noqa: BLE001
                break
            local_total += int(body.get("totalCount", 0) or 0)
            items_raw = body.get("items", [])
            if isinstance(items_raw, dict):
                items_raw = items_raw.get("item", [])
            if not isinstance(items_raw, list):
                items_raw = [items_raw] if items_raw else []
            if not items_raw:
                break
            for raw in items_raw:
                scanned_in_call += 1
                local_scanned += 1
                local_raw_items.append(raw)
            if len(items_raw) < page_size:
                break
            cur_page += 1
        return endpoint, local_total, local_scanned, local_raw_items

    try:
        # tasks = chunks × endpoints × inst_variants (fan-out 차원).
        tasks = [
            _fetch_combo(cf, ct, ep, field, value)
            for cf, ct in chunks
            for _, ep in endpoints
            for field, value in inst_variants
        ]
        results = await asyncio.gather(*tasks)

        for endpoint, local_total, local_scanned, raw_items in results:
            if endpoint not in endpoints_used:
                endpoints_used.append(endpoint)
            # fan-out으로 중복 카운트되는 부분이 있으나 totalCount는 endpoint별 통계용 sum
            total_count += local_total
            scanned_total += local_scanned
            for raw in raw_items:
                if needs_client_filter:
                    region_v = raw.get("rgnLmtBidLocplcNm") or ""
                    if inp.bid_notice_no and str(raw.get("bidNtceNo", "")) != inp.bid_notice_no:
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
            if len(matches) >= inp.limit:
                break
    finally:
        await client.aclose()

    has_more = (
        (total_count > inp.page * page_size * len(endpoints))
        if (max_scan_pages == 1 and len(chunks) == 1)
        else (total_count > scanned_total and len(matches) >= inp.limit)
    )
    if scanned_total == 0:
        has_more = False

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
        "lookup_mode": "PPSSrch+inst_fanout" if inp.inst_name else "PPSSrch",
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


async def _get_detail_by_bid_no(bid_notice_no: str, bid_ord: str, norm_ord: str) -> dict | None:
    """P31-R4.5 (F25 hotfix): inqryDiv=2 + bidNtceNo 직접 + 5종 단일조회 endpoint 병렬.

    R-prefix 단건 매칭이 inqryDiv=3/inqryDiv=1 폴백 chain에서 미작동하는 케이스 대응.
    PoC #4 evidence (R25BK00755515 → Servc endpoint 적중) 패턴 재사용.
    R1 `_search_by_bid_notice_no` 와 동일 호출 구조 — 단 detail 형식(found/biz_div/endpoint/lookup_mode/summary/raw)으로 정규화.

    매칭 1건 발견 즉시 반환. 미매칭 시 None.
    """
    target_no = bid_notice_no.strip()

    async def _call_one(label: str, endpoint: str):
        params = {
            "pageNo": 1,
            "numOfRows": 10,
            "inqryDiv": "2",
            "bidNtceNo": target_no,
        }
        try:
            body = await client.call(endpoint, settings.g2b_key_bid, params)
        except Exception:  # noqa: BLE001
            return label, endpoint, []
        items_raw = body.get("items", [])
        if isinstance(items_raw, dict):
            items_raw = items_raw.get("item", [])
        if not isinstance(items_raw, list):
            items_raw = [items_raw] if items_raw else []
        return label, endpoint, items_raw

    client = G2BClient()
    try:
        results = await asyncio.gather(
            *(_call_one(label, ep) for label, ep in _BID_DETAIL_ENDPOINTS)
        )
        # 1순위: bidNtceNo + bidNtceOrd 정합 매칭
        for label, endpoint, items_raw in results:
            for raw in items_raw:
                if str(raw.get("bidNtceNo", "")) != target_no:
                    continue
                raw_ord = str(raw.get("bidNtceOrd", ""))
                raw_ord_norm = raw_ord.lstrip("0") or "0"
                if raw_ord_norm == norm_ord or raw_ord == bid_ord:
                    return {
                        "found": True,
                        "biz_div": label,
                        "endpoint": endpoint,
                        "lookup_mode": "inqryDiv=2+bidNtceNo+ord_match",
                        "summary": _normalize_notice(raw).model_dump(),
                        "raw": raw,
                    }
        # 2순위: bidNtceNo 일치하나 ord 다른 차수 (참고용 first match)
        for label, endpoint, items_raw in results:
            for raw in items_raw:
                if str(raw.get("bidNtceNo", "")) == target_no:
                    return {
                        "found": True,
                        "biz_div": label,
                        "endpoint": endpoint,
                        "lookup_mode": "inqryDiv=2+bidNtceNo+ord_diff",
                        "ord_mismatch_warning": f"요청 ord={bid_ord} 미발견. 다른 차수(ord={raw.get('bidNtceOrd')}) 반환.",
                        "summary": _normalize_notice(raw).model_dump(),
                        "raw": raw,
                    }
    finally:
        await client.aclose()
    return None


@cache_result(ttl=settings.cache_ttl_short, prefix="bid_detail_v33")
async def get_bid_notice_detail(bid_notice_no: str, bid_ord: str = "00") -> dict:
    """공고번호+차수로 입찰공고 단건 상세를 조회합니다.

    5/3 N42: 단건 inqryDiv=3 미지원 endpoint 케이스(R 형식 등)를 위해 inqryDiv=1 폴백 추가.
    P31-R4.5 (F25 hotfix): R-prefix 단건 매칭이 inqryDiv=3/inqryDiv=1 폴백 모두 미작동
        케이스 대응 — inqryDiv=2 + bidNtceNo + 5종 단일조회 endpoint 병렬 폴백 신규(PoC #4 패턴).
    1차: inqryDiv=3 + bidNtceNo + bidNtceOrd
    2차 폴백: inqryDiv=1 + bidNtceNo (차수 무관) → 클라이언트측 차수 매칭
    3차 폴백: inqryDiv=2 + bidNtceNo (P31-R4.5 신규, 5종 단일조회 endpoint 병렬)
    4차 폴백: search_bid_notices(bid_notice_no=...) (progressive 30/90일 + 추정 연도)

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

        # 3차 폴백: P31-R4.5 (F25 hotfix) — inqryDiv=2 + bidNtceNo + 5종 단일조회 endpoint 병렬.
        # PoC #4 evidence (R25BK00755515 → Servc 적중) 패턴 재사용.
        # R-prefix 단건이 inqryDiv=3/inqryDiv=1 폴백 모두 미작동 시 hit 가능 (운영 환경 검증 결함 회복).
        detail_via_div2 = await _get_detail_by_bid_no(bid_notice_no, bid_ord, norm_ord)
        if detail_via_div2 is not None:
            return detail_via_div2

        # 4차 폴백: search_bid_notices — v22.3 + v23.1 (F2 + F9):
        # R26.../20260101... 형식이라도 progressive(30→90→연도)로 보통 케이스 우선 빠르게.
        # 30일에 hit이면 5~10초 (5초 SLA 근접). 못 찾으면 90일, 그래도 못 찾으면 연도 전체.
        from datetime import datetime, timedelta
        today = datetime.now()
        inferred_from, inferred_to = _infer_period_from_bid_no(bid_notice_no)
        fallback_ranges = [
            ((today - timedelta(days=30)).strftime("%Y%m%d"), today.strftime("%Y%m%d")),
            ((today - timedelta(days=90)).strftime("%Y%m%d"), today.strftime("%Y%m%d")),
        ]
        if inferred_from and inferred_to:
            # R/숫자 형식: 마지막 fallback으로 추정 연도 (비용 ↑, 정확)
            fallback_ranges.append((inferred_from, inferred_to))

        for fb_from, fb_to in fallback_ranges:
            try:
                search_result = await search_bid_notices(
                    bid_notice_no=bid_notice_no,
                    limit=3,
                    scan_pages=2,
                    date_from=fb_from,
                    date_to=fb_to,
                )
                for item in search_result.get("items", []):
                    if str(item.get("bid_no", "")) == bid_notice_no:
                        item_ord = str(item.get("bid_ord") or "")
                        item_ord_norm = item_ord.lstrip("0") or "0"
                        if item_ord_norm == norm_ord or item_ord == bid_ord:
                            return {
                                "found": True,
                                "lookup_mode": "search_bid_notices+ord_match",
                                "fallback_range": f"{fb_from}~{fb_to}",
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
                        "fallback_range": f"{fb_from}~{fb_to}",
                        "ord_mismatch_warning": f"요청 ord={bid_ord} 미발견. 다른 차수(ord={first_match.get('bid_ord')}) 반환.",
                        "summary": first_match,
                        "raw": first_match.get("raw", first_match),
                    }
            except Exception as exc:  # noqa: BLE001
                # v22.3: 기존 silent pass → 가시화 (root cause 추적)
                log.warning(
                    "trace_search_fallback_failed",
                    bid_notice_no=bid_notice_no,
                    date_from=fb_from,
                    date_to=fb_to,
                    error=str(exc)[:200],
                )
                continue

        return {
            "found": False,
            "bid_notice_no": bid_notice_no,
            "bid_ord": bid_ord,
            "note": "inqryDiv=3 단건 + inqryDiv=1 폴백 + inqryDiv=2 5종 fan-out + search_bid_notices 매칭 모두 미발견. 공고번호·차수 확인 또는 사전규격(get_pre_specification_detail) 시도.",
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


@cache_result(ttl=settings.cache_ttl_short, prefix="prespec_detail")
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


@cache_result(ttl=settings.cache_ttl_short, prefix="agencies_v32")
async def search_agencies(query: str, limit: int = 30) -> dict:
    """발주/수요기관 LIKE 검색 (자동완성용, 2자 이상).

    P31-R2 (F22): err-035 사양 — 2자+ trigger 발주기관 자동완성.

    구현: Servc PPSSrch (POC #5 evidence — totalCount=22862 가장 많음) 1개월 호출 + 응답
    ntceInsttNm/dminsttNm 두 호출 fan-out → distinct (코드, 이름, match_field) 추출.

    Args:
        query: 기관명 부분일치 키워드 (2자 이상 필수)
        limit: 최대 반환 건수 (default 30)

    Returns:
        items: [{inst_code, inst_name, match_field}, ...] (distinct)
        total_count: scanned 응답 수
        error: 2자 미만 시 "2자 이상 입력 필요"
    """
    q = (query or "").strip()
    if len(q) < 2:
        return {"items": [], "total_count": 0, "error": "2자 이상 입력 필요"}

    allowed, remaining = await check_rate("g2b_agencies", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_agencies 토큰 소진 (remaining={remaining})")

    from datetime import datetime, timedelta
    today = datetime.now()
    # G2B 1개월 제약 안전 마진 — 30일 (31일은 일부 endpoint에서 에러)
    bgn = (today - timedelta(days=30)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")

    endpoint = _BID_ENDPOINTS_PPSSRCH["용역"]  # POC #5: 일반용역 PPSSrch가 데이터 가장 많음

    async def _call_one(field: str):
        params = {
            "pageNo": 1,
            "numOfRows": 100,
            "inqryDiv": "1",
            "inqryBgnDt": bgn + "0000",
            "inqryEndDt": end + "2359",
            "type": "json",
            field: q,
        }
        try:
            body = await client.call(endpoint, settings.g2b_key_bid, params)
        except Exception:  # noqa: BLE001
            return field, []
        items_raw = body.get("items", [])
        if isinstance(items_raw, dict):
            items_raw = items_raw.get("item", [])
        if not isinstance(items_raw, list):
            items_raw = [items_raw] if items_raw else []
        return field, items_raw

    client = G2BClient()
    seen: set[tuple[str, str, str]] = set()  # (code, name, match_field)
    items_out: list[dict] = []
    scanned = 0
    try:
        results = await asyncio.gather(
            _call_one("ntceInsttNm"),
            _call_one("dminsttNm"),
        )
        for field, raws in results:
            for raw in raws:
                scanned += 1
                if field == "ntceInsttNm":
                    code = str(raw.get("ntceInsttCd") or "")
                    name = str(raw.get("ntceInsttNm") or "")
                else:
                    code = str(raw.get("dminsttCd") or "")
                    name = str(raw.get("dminsttNm") or "")
                if not name or q not in name:
                    continue
                key = (code, name, field)
                if key in seen:
                    continue
                seen.add(key)
                items_out.append({
                    "inst_code": code or None,
                    "inst_name": name,
                    "match_field": field,
                })
                if len(items_out) >= limit:
                    break
            if len(items_out) >= limit:
                break
    finally:
        await client.aclose()

    return {
        "items": items_out,
        "total_count": len(items_out),
        "scanned": scanned,
    }
