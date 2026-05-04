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

P32-R2 (F30): R-prefix 단건 폴백 raw evidence (poc_p32_v3.py 5건 검증):
- award: getScsbidListSttus{X}PPSSrch + inqryDiv=3 + bidNtceNo (non-PPSSrch + inqryDiv=4 미작동)
- 응찰: getOpengResultListInfo{X} + inqryDiv=4 + bidNtceNo (non-PPSSrch) — 1 row 단위 입찰 집계
  • prtcptCnum = 응찰 총 수, opengCorpInfo = 낙찰자 1건 caret(^) 인코딩 ("업체명^사업자번호^대표자^공고번호^낙찰률")
  • 응찰자 50건 raw row endpoint는 OpenAPI 미공개 — G2B 웹 UI 전용. carriage limit.
"""
from __future__ import annotations
import asyncio
import re
from app.clients.g2b import G2BClient
from app.config import settings
from app.core.cache import cache_result
from app.core.daterange import chunk_date_range
from app.core.rate_limit import check_rate


# v28.1: 업체명 LIKE 매칭 정규화 — 공백/(주)/주식회사/㈜ 등 제거 후 비교
_VENDOR_NORMALIZE_PATTERN = re.compile(
    r"\s+|\(주\)|\(유\)|\(사\)|㈜|주식회사|유한회사|사단법인|재단법인|협동조합|합자회사|합명회사"
)


def _normalize_vendor_name(name: str | None) -> str:
    """업체명 매칭용 정규화 — 변형 표기 통일.

    예시:
    - "아이웨이브" → "아이웨이브"
    - "(주)아이웨이브" → "아이웨이브"
    - "주식회사아이웨이브" → "아이웨이브"
    - "아이 웨이브 주식회사" → "아이웨이브"
    """
    if not name:
        return ""
    return _VENDOR_NORMALIZE_PATTERN.sub("", name).lower()


def _vendor_name_match(query: str, target: str) -> bool:
    """LIKE 매칭 — 정규화 후 부분일치 + 토큰 매칭.

    질의 토큰이 모두 정규화된 target에 포함되면 매칭.
    """
    if not query or not target:
        return False
    norm_target = _normalize_vendor_name(target)
    if not norm_target:
        return False
    # 질의 정규화 (공백 보존 — 토큰 분리용)
    query_clean = _VENDOR_NORMALIZE_PATTERN.sub(" ", query).strip().lower()
    tokens = [t for t in query_clean.split() if t]
    if not tokens:
        return False
    return all(t in norm_target for t in tokens)


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

# P32-R2 (F30): R-prefix 단건 폴백 전용 endpoint.
# poc_p32_v3.py 5건 raw evidence 기반:
# - 낙찰: getScsbidListSttus{X}PPSSrch + inqryDiv=3 (non-PPSSrch는 미작동)
# - 응찰: getOpengResultListInfo{X} (non-PPSSrch) + inqryDiv=4 (PPSSrch는 inqryDiv=3로도 가능하나
#   응답 형태 동일 — 1 row per 입찰 + opengCorpInfo caret 인코딩)
_AWARD_PPSSRCH_ENDPOINTS = {
    "Cnstwk": _AWARD_BASE + "CnstwkPPSSrch",
    "Servc": _AWARD_BASE + "ServcPPSSrch",
    "Thng": _AWARD_BASE + "ThngPPSSrch",
    "Frgcpt": _AWARD_BASE + "FrgcptPPSSrch",
}
_OPENING_NONPPS_ENDPOINTS = {
    "Cnstwk": _OPENING_BASE + "Cnstwk",
    "Servc": _OPENING_BASE + "Servc",
    "Thng": _OPENING_BASE + "Thng",
    "Frgcpt": _OPENING_BASE + "Frgcpt",
}

_R_PREFIX_PATTERN = re.compile(r"^R\d{2}[A-Z]{2}\d{8}$", re.IGNORECASE)


def _is_r_prefix(bid_no: str | None) -> bool:
    """차세대 나라장터 13자리 R-prefix 입찰번호 여부 (P32-R2).

    형식: R + 년도(2) + 단계구분(2) + 순번(8) = 13자리. (DOSSIER-OFFICIAL §5.1)
    `-차수` suffix가 붙은 경우 split 후 prefix 부분만 검사.
    """
    if not bid_no:
        return False
    head = bid_no.split("-")[0].strip()
    return bool(_R_PREFIX_PATTERN.match(head))


def _parse_openg_corp_info(s: str | None) -> list[dict]:
    """opengCorpInfo caret(^) 인코딩 파싱 — 낙찰자 1건만 인코딩되는 G2B 운영 관행 (P32-R2).

    raw 형식 (5건 raw evidence, R26BK01451151 case):
      "주식회사 서정이엔지^6468800556^이유정^260750100^90.593"
      = "{업체명}^{사업자번호}^{대표자}^{공고번호 추정}^{낙찰률}"

    반환: 응찰업체 정규화 row 리스트 (winner_only=True 1건). 50건 응찰자 raw list는
    OpenAPI 미공개 — prtcptCnum(응찰 총수)만 row 단위로 보고됨.
    """
    if not s or not isinstance(s, str):
        return []
    parts = s.split("^")
    if not parts or not parts[0].strip():
        return []
    name = parts[0].strip()
    biz_no = _normalize_biz_no(parts[1] if len(parts) > 1 else None)
    rep = (parts[2] or "").strip() if len(parts) > 2 else None
    rate_raw = (parts[4] or "").strip() if len(parts) > 4 else None
    return [{
        "participant_name": name,
        "participant_biz_no": biz_no,
        "representative_name": rep,
        "opening_rank": 1,
        "is_winner": True,
        "award_rate": rate_raw,
        "raw": {"opengCorpInfo": s},
    }]


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

@cache_result(ttl=settings.cache_ttl_short, prefix="award_list_v24")
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
    # v24.2: 매칭 0건 시 사용자 학습용 inst 표기 샘플 (필터 통과 무관)
    inst_sample_counts: dict[str, int] = {}

    client = G2BClient(base_url=settings.g2b_award_base_url)

    # v23.4: chunks × biz_divs 직렬 → asyncio.gather 병렬.
    # chunks=1 (30일) × biz_divs=4 (전체) = 4× 효과. 큰 범위는 더 큰 효과.
    async def _fetch(biz_div: str, chunk_from: str | None, chunk_to: str | None):
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
            return endpoint, int(body.get("totalCount", 0) or 0), list(_extract_items(body))
        except Exception:  # noqa: BLE001
            return endpoint, 0, []

    try:
        tasks = [
            _fetch(bd, cf, ct)
            for cf, ct in chunks
            for bd in biz_divs
        ]
        results = await asyncio.gather(*tasks)

        for endpoint, count, raw_items in results:
            if endpoint not in used_endpoints:
                used_endpoints.append(endpoint)
            total_count += count
            for raw in raw_items:
                # v24.2: inst 표기 샘플 (필터 통과 무관)
                sample_label = ((raw.get("dminsttNm") or "") + " " + (raw.get("ntceInsttNm") or "")).strip()
                if sample_label:
                    inst_sample_counts[sample_label] = inst_sample_counts.get(sample_label, 0) + 1

                if needs_client_filter:
                    if keyword:
                        title = raw.get("bidNtceNm") or ""
                        # v24.4: keyword 토큰 매칭 (어순 변경 매칭률 ↑)
                        keyword_tokens = [t for t in keyword.split() if t]
                        if not all(t in title for t in keyword_tokens):
                            continue
                    if inst_name:
                        inst = (raw.get("dminsttNm") or "") + " " + (raw.get("ntceInsttNm") or "")
                        # v24.1: 토큰 기반 매칭 — "경찰청 경찰대학" 토큰 ["경찰청","경찰대학"]이 모두 포함되면 매칭
                        inst_tokens = [t for t in inst_name.split() if t]
                        if not all(t in inst for t in inst_tokens):
                            continue
                key = (str(raw.get("bidNtceNo", "")), str(raw.get("bidNtceOrd", "")))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                matches.append(_normalize_award_row(raw))
                if len(matches) >= limit:
                    break
            if len(matches) >= limit:
                break
    finally:
        await client.aclose()

    # v24.2: 매칭 0건 시 사용자 학습용 inst 표기 샘플 상위 5개 (출현 빈도 순)
    sample_inst_names = [
        name for name, _ in sorted(inst_sample_counts.items(), key=lambda x: -x[1])[:5]
    ]

    return {
        "items": matches,
        "total_count": total_count,
        "returned_count": len(matches),
        "has_more": len(matches) >= limit,
        "endpoints_used": used_endpoints,
        "chunks_used": len(chunks),
        "sample_inst_names": sample_inst_names,
    }


# === 3. get_award_detail ===

@cache_result(ttl=settings.cache_ttl_short, prefix="award_detail_v32")
async def get_award_detail(bid_notice_no: str, bid_ord: str = "00") -> dict:
    """공고번호+차수로 낙찰 단건 상세 조회.

    5/3 N42: inqryDiv=4(단건) 미지원 케이스(R 형식 등)를 위해 inqryDiv=1 폴백 추가.
    P32-R2 (F30): R-prefix 단건 매칭은 ScsbidListSttus*PPSSrch + inqryDiv=3 + bidNtceNo
        라는 운영 관행 검증 (poc_p32_v3.py 5건 raw evidence). non-PPSSrch + inqryDiv=4는
        실제로는 미작동. 1차 우선순위로 PPSSrch fan-out 추가.
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
        # P32-R2 (F30) 1차 신설: R-prefix 단건이면 ScsbidListSttus*PPSSrch + inqryDiv=3 4종 fan-out 우선.
        # poc_p32_v3.py: R25BK00755515(Servc), R25BK00760571(Cnstwk), R26BK01451151(Cnstwk) 적중.
        if _is_r_prefix(bid_notice_no):
            async def _call_pps(biz_div: str, endpoint: str):
                params = {
                    "pageNo": 1,
                    "numOfRows": 5,
                    "inqryDiv": "3",  # PPSSrch 패턴: 3=입찰공고번호 (raw evidence)
                    "bidNtceNo": bid_notice_no,
                    "bidNtceOrd": bid_ord,
                }
                try:
                    body = await client.call(endpoint, settings.g2b_key_award, params)
                except Exception:  # noqa: BLE001
                    return biz_div, endpoint, []
                return biz_div, endpoint, _extract_items(body)

            results = await asyncio.gather(
                *(_call_pps(bd, ep) for bd, ep in _AWARD_PPSSRCH_ENDPOINTS.items())
            )
            for biz_div, endpoint, items in results:
                for raw in items:
                    if str(raw.get("bidNtceNo", "")) == bid_notice_no:
                        return {
                            "found": True,
                            "biz_div": biz_div,
                            "endpoint": endpoint,
                            "lookup_mode": "PPSSrch+inqryDiv=3+bidNtceNo",
                            "summary": _normalize_award_row(raw),
                            "raw": raw,
                        }

        # 1차 (기존): inqryDiv=4 단건 — 11자리 숫자 등 R-prefix 외에서 작동하는 케이스 보존
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

        # 2차 폴백: inqryDiv=1 + bidNtceNo + 추정 기간 (G2B inqryDiv=1은 기간 필수)
        from app.tools.bid import _infer_period_from_bid_no
        bgn_dt, end_dt = _infer_period_from_bid_no(bid_notice_no)
        for biz_div, endpoint in _AWARD_ENDPOINTS.items():
            params = {
                "pageNo": 1,
                "numOfRows": 50,
                "inqryDiv": "1",
                "bidNtceNo": bid_notice_no,
            }
            if bgn_dt and end_dt:
                params["inqryBgnDt"] = bgn_dt + "0000"
                params["inqryEndDt"] = end_dt + "2359"
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

@cache_result(ttl=settings.cache_ttl_short, empty_ttl=settings.cache_ttl_volatile, prefix="award_vendor_v30")
async def search_awards_by_vendor(
    vendor_name: str | None = None,
    vendor_biz_no: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 20,
    page: int = 1,
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

    # P30-R3.5: page 인자 도입 — 1-based. offset = (page-1)*limit.
    # 누적 matches에서 page slice 적용 (동일 검색 결과 set의 다른 페이지).
    page = max(1, int(page or 1))
    offset = (page - 1) * limit
    needed = offset + limit

    # 5/3 N40: G2B 낙찰정보서비스 numOfRows 최대 500 (999는 resultCode 07).
    # 5/3 N42: date range 1개월 초과 시 자동 chunking.
    # v28.1: 1000 → 3000 (1 chunk × 1 biz_div × 6페이지) — vendor 매칭률 ↑
    page_size = 500
    max_scan_per_call = 3000

    chunks = chunk_date_range(date_from, date_to, max_days=31)
    matches: list[dict] = []
    total_count = 0
    scanned_total = 0
    used_endpoints: list[str] = []
    seen_keys: set[tuple[str, str]] = set()

    client = G2BClient(base_url=settings.g2b_award_base_url)

    # v29.1.2 (F11 P2): chunks × biz_divs 직렬 → asyncio.gather 병렬.
    # 1년 12 chunks × 4 biz_div = 48 직렬 → 병렬 max(combo_time).
    # page loop는 단일 조합 내부 sequential (다음 page 호출은 직전 응답 의존).
    async def _fetch_v4_combo(
        chunk_from: str | None,
        chunk_to: str | None,
        biz_div: str,
    ):
        endpoint = _AWARD_ENDPOINTS[biz_div]
        local_total = 0
        local_scanned = 0
        local_raw: list = []
        scanned_in_call = 0
        page_no = 1  # P30-R3.5: 외부 인자 `page`와 충돌 회피 — G2B pageNo 변수 분리
        while scanned_in_call < max_scan_per_call:
            params: dict = {
                "pageNo": page_no,
                "numOfRows": page_size,
                "inqryDiv": "1",
            }
            if chunk_from:
                params["inqryBgnDt"] = chunk_from + "0000"
            if chunk_to:
                params["inqryEndDt"] = chunk_to + "2359"
            try:
                body = await client.call(endpoint, settings.g2b_key_award, params)
            except Exception:  # noqa: BLE001
                break
            local_total = max(local_total, int(body.get("totalCount", 0) or 0))
            items_raw = _extract_items(body)
            if not items_raw:
                break
            for raw in items_raw:
                scanned_in_call += 1
                local_scanned += 1
                local_raw.append(raw)
            if len(items_raw) < page_size:
                break
            page_no += 1
        return endpoint, local_total, local_scanned, local_raw

    try:
        tasks = [
            _fetch_v4_combo(cf, ct, bd)
            for cf, ct in chunks
            for bd in biz_divs
        ]
        results = await asyncio.gather(*tasks)

        for endpoint, lt, ls, raws in results:
            if endpoint not in used_endpoints:
                used_endpoints.append(endpoint)
            total_count = max(total_count, lt)
            scanned_total += ls
            for raw in raws:
                norm = _normalize_award_row(raw)
                matched = False
                if target_biz_no and norm.get("winner_biz_no") == target_biz_no:
                    matched = True
                elif vendor_name and _vendor_name_match(vendor_name, norm.get("winner_name") or ""):
                    # v28.1: 정규화(공백/(주)/주식회사 제거) + 토큰 매칭
                    matched = True
                if not matched:
                    continue
                key = (str(norm.get("bid_notice_no") or ""), str(norm.get("bid_ord") or ""))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                matches.append(norm)
                if len(matches) >= needed:
                    break
            if len(matches) >= needed:
                break
    finally:
        await client.aclose()

    # v29.1.2 (F11 P1): has_more 정확화 — 매칭 한도 또는 스캔 미커버리지 명시.
    # scanned_total < total_count면 false-negative 가능성 (모집단 미스캔).
    # frontend가 사용자에게 "추가 검색 권장" 안내 가능.
    # P30-R3.5: page slice 적용 — 누적 matches에서 [offset : offset+limit] 반환.
    matched_total = len(matches)
    page_items = matches[offset : offset + limit]
    has_more_flag = (matched_total > offset + len(page_items)) or (scanned_total < total_count)
    scan_coverage_pct = round(min(100.0, (scanned_total / total_count * 100.0) if total_count else 100.0), 1)

    return {
        "items": page_items,
        "total_count": total_count,
        "scanned": scanned_total,
        "scan_coverage_pct": scan_coverage_pct,
        "returned_count": len(page_items),
        "matched_total": matched_total,
        "page": page,
        "limit": limit,
        "has_more": has_more_flag,
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

@cache_result(ttl=settings.cache_ttl_short, prefix="participants_v32")
async def list_bid_participants(
    bid_notice_no: str,
    bid_ord: str = "00",
) -> dict:
    """입찰공고번호로 응찰업체 목록 조회.

    ScsbidInfoService에 응찰업체 단독 endpoint 없음 → 개찰결과(getOpengResultListInfo*) 응답 row를 사용.

    P32-R2 (F30) raw evidence 검증 (poc_p32_v3.py 5건):
    - R-prefix 단건은 getOpengResultListInfo{X} (non-PPSSrch) + inqryDiv=4 + bidNtceNo 에서 1 row 응답.
      기존 PPSSrch + inqryDiv=4는 미작동. PPSSrch + inqryDiv=3는 동일 1 row 가능.
    - 응답 row는 입찰 단위 1건이며 prtcptCnum=응찰 총수, opengCorpInfo=낙찰자 1건 caret 인코딩.
      응찰 50건 raw row endpoint는 OpenAPI 미공개 (G2B 웹 UI 전용).
    - 따라서 items는 opengCorpInfo 파싱 결과(낙찰자 1건) + participant_count는 prtcptCnum 사용.
    """
    allowed, remaining = await check_rate("g2b_participants", capacity=10, refill_per_sec=1.0)
    if not allowed:
        raise RuntimeError(f"rate_limit: g2b_participants 토큰 소진 (remaining={remaining})")

    if "-" in bid_notice_no and not bid_ord.strip("0"):
        parts = bid_notice_no.rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            bid_notice_no, bid_ord = parts[0], parts[1]

    client = G2BClient(base_url=settings.g2b_award_base_url)
    try:
        # P32-R2 (F30) 1차 신설: R-prefix 단건이면 non-PPSSrch + inqryDiv=4 fan-out 우선.
        if _is_r_prefix(bid_notice_no):
            async def _call_nonpps(biz_div: str, endpoint: str):
                params = {
                    "pageNo": 1,
                    "numOfRows": 100,
                    "inqryDiv": "4",  # ScsbidInfoService non-PPSSrch: 4=입찰공고번호 (raw evidence)
                    "bidNtceNo": bid_notice_no,
                    "bidNtceOrd": bid_ord,
                }
                try:
                    body = await client.call(endpoint, settings.g2b_key_award, params)
                except Exception:  # noqa: BLE001
                    return biz_div, endpoint, []
                return biz_div, endpoint, _extract_items(body)

            results = await asyncio.gather(
                *(_call_nonpps(bd, ep) for bd, ep in _OPENING_NONPPS_ENDPOINTS.items())
            )
            for biz_div, endpoint, items in results:
                for raw in items:
                    if str(raw.get("bidNtceNo", "")) != bid_notice_no:
                        continue
                    # opengCorpInfo caret 파싱 (낙찰자 1건). 미존재면 빈 list.
                    parsed = _parse_openg_corp_info(raw.get("opengCorpInfo"))
                    declared_count = _to_int(raw.get("prtcptCnum") or raw.get("opengCnt")) or len(parsed)
                    return {
                        "found": True,
                        "biz_div": biz_div,
                        "endpoint": endpoint,
                        "lookup_mode": "non-PPSSrch+inqryDiv=4+bidNtceNo",
                        "bid_notice_no": bid_notice_no,
                        "bid_ord": bid_ord,
                        "items": parsed,  # 낙찰자 1건 (or 빈 list)
                        "participant_count": declared_count,  # 응찰 총수 (prtcptCnum)
                        "winner_only": True,
                        "note": (
                            f"G2B OpenAPI 응답 1 row + opengCorpInfo 인코딩 1건. "
                            f"응찰 총수 prtcptCnum={declared_count}, items=낙찰자 1건. "
                            "전체 응찰자 raw list endpoint는 OpenAPI 미공개."
                        ),
                        "raw": raw,
                    }

        # 기존 fallback: PPSSrch + inqryDiv=4 (raw evidence상 R-prefix 미작동, 11자리 숫자형 호환)
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
                    "lookup_mode": "PPSSrch+inqryDiv=4",
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
