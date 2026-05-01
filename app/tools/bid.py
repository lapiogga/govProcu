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

    params: dict = {
        "pageNo": 1,
        "numOfRows": inp.limit,
        "inqryDiv": "1",  # 등록일 기준
    }
    if inp.date_from:
        params["inqryBgnDt"] = inp.date_from + "0000"
    if inp.date_to:
        params["inqryEndDt"] = inp.date_to + "2359"
    if inp.keyword:
        params["bidNtceNm"] = inp.keyword
    if inp.inst_name:
        params["dminsttNm"] = inp.inst_name

    biz_div = _BIZ_DIV_MAP.get(inp.biz_type) if inp.biz_type else None

    # 업종별 엔드포인트 (G2B API 특성)
    if biz_div == "1":
        endpoint = "/BidPublicInfoService05/getBidPblancListInfoCnstwk"
    elif biz_div == "2":
        endpoint = "/BidPublicInfoService05/getBidPblancListInfoServc"
    elif biz_div == "3":
        endpoint = "/BidPublicInfoService05/getBidPblancListInfoThng"
    else:
        endpoint = "/BidPublicInfoService05/getBidPblancListInfoServc"

    client = G2BClient()
    try:
        body = await client.call(endpoint, settings.g2b_key_bid, params)
    finally:
        await client.aclose()

    items_raw = body.get("items", [])
    if isinstance(items_raw, dict):
        items_raw = items_raw.get("item", [])
    if not isinstance(items_raw, list):
        items_raw = [items_raw] if items_raw else []

    items = [_normalize_notice(r).model_dump() for r in items_raw]
    total = int(body.get("totalCount", len(items)))

    return BidNoticeSearchResult(
        items=items,
        total_count=total,
        returned_count=len(items),
        has_more=total > len(items),
    ).model_dump()


# === Stub: 추후 구현 ===
async def get_bid_notice_detail(bid_no: str, bid_ord: str = "00") -> dict:
    """공고번호 기준 입찰공고 상세 정보를 조회합니다. (stub)"""
    raise NotImplementedError("M5 단계 구현 예정")


async def list_pre_specifications(
    keyword: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict:
    """사전규격공개 목록을 조회합니다. (stub — G2B_KEY_PRESPEC 사용)"""
    raise NotImplementedError("M5 단계 구현 예정")
