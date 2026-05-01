"""입찰공고 영역 MCP 도구."""
from __future__ import annotations
from app.clients.g2b import G2BClient
from app.config import settings
from app.core.cache import cache_result
from app.core.rate_limit import check_rate
from app.schemas.bid import BidNoticeSearchInput, BidNoticeSearchResult, BidNoticeSummary


_BIZ_DIV_MAP = {"공사": "1", "용역": "2", "물품": "3"}


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
) -> dict:
    """나라장터 입찰공고를 키워드/업종/지역/기관/기간으로 검색합니다.

    Args:
        keyword: 공고 제목 부분일치 키워드 (예: '정보화', '용역', 'AI')
        biz_type: '공사' | '용역' | '물품' 중 하나
        region: 지역 제한 (시도명)
        inst_name: 발주기관명 부분일치
        date_from: 공고일 시작 (YYYYMMDD)
        date_to: 공고일 종료 (YYYYMMDD)
        limit: 최대 반환 건수 (1~100)

    Returns:
        items, total_count, returned_count, has_more를 포함한 dict.
    """
    # Rate limit 체크
    allowed, remaining = await check_rate("g2b_bid", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_bid 토큰 소진 (remaining={remaining})")

    inp = BidNoticeSearchInput(
        keyword=keyword, biz_type=biz_type, region=region,
        inst_name=inst_name, date_from=date_from, date_to=date_to, limit=limit,
    )

    biz_div = _BIZ_DIV_MAP.get(inp.biz_type) if inp.biz_type else None

    # 업종별 엔드포인트 (운영 검증된 경로: /ad/BidPublicInfoService 시리즈)
    if biz_div == "1":
        endpoint = "/BidPublicInfoService/getBidPblancListInfoCnstwk"
    elif biz_div == "3":
        endpoint = "/BidPublicInfoService/getBidPblancListInfoThng"
    else:
        endpoint = "/BidPublicInfoService/getBidPblancListInfoServc"

    # 서버측 keyword/inst_name/region 필터가 무시되는 이슈 → 클라이언트측 필터링
    needs_client_filter = bool(inp.keyword or inp.inst_name or inp.region)
    page_size = 999 if needs_client_filter else inp.limit
    max_scan = 50000  # 안전 상한 (대형 결과셋 방어)

    matches: list[dict] = []
    page = 1
    scanned = 0
    total_count = 0

    client = G2BClient()
    try:
        while len(matches) < inp.limit and scanned < max_scan:
            params: dict = {
                "pageNo": page,
                "numOfRows": page_size,
                "inqryDiv": "1",  # 등록일 기준
            }
            if inp.date_from:
                params["inqryBgnDt"] = inp.date_from + "0000"
            if inp.date_to:
                params["inqryEndDt"] = inp.date_to + "2359"

            body = await client.call(endpoint, settings.g2b_key_bid, params)
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
                    title = raw.get("bidNtceNm") or ""
                    inst = (raw.get("dminsttNm") or "") + " " + (raw.get("ntceInsttNm") or "")
                    region_v = raw.get("rgnLmtBidLocplcNm") or ""
                    if inp.keyword and inp.keyword not in title:
                        continue
                    if inp.inst_name and inp.inst_name not in inst:
                        continue
                    if inp.region and inp.region not in region_v:
                        continue
                matches.append(_normalize_notice(raw).model_dump())
                if len(matches) >= inp.limit:
                    break

            # 다음 페이지 진행 조건: 마지막 페이지면 종료
            if len(items_raw) < page_size:
                break
            page += 1
    finally:
        await client.aclose()

    return BidNoticeSearchResult(
        items=matches,
        total_count=total_count,
        returned_count=len(matches),
        has_more=(total_count > scanned) and (len(matches) >= inp.limit),
    ).model_dump()


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

    BidPublicInfoService `inqryDiv=3` + `bidNtceNo`+`bidNtceOrd` 단건 패턴.
    업종(공사/용역/물품)을 모르므로 용역 → 공사 → 물품 순으로 시도.

    Args:
        bid_notice_no: 입찰공고번호 (예: '20240101234')
        bid_ord: 공고차수 (기본 "00")

    Returns:
        공고 상세 dict (raw 포함). 미발견 시 status=not_found.
    """
    allowed, remaining = await check_rate("g2b_bid_detail", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_bid_detail 토큰 소진 (remaining={remaining})")

    client = G2BClient()
    try:
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
            except Exception as exc:  # noqa: BLE001
                # 다음 업종 endpoint 시도
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
            "note": "공사/용역/물품 3개 endpoint 모두 미발견. 공고번호·차수 확인 또는 사전규격(get_pre_specification_detail) 시도.",
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
