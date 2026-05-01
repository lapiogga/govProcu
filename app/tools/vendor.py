"""vendor 영역 MCP 도구.

응찰업체별 정보 / 입찰참가 이력 / 평가점수 / 사업자 상태 조회용.
- 조달데이터허브 EVAL API: 응찰자/평가점수 (스텁 — 키 발급 대기)
- 국세청 NTS API: 사업자등록 상태조회 (구현 — NTS_API_KEY 필요)
"""
from __future__ import annotations
from app.clients.nts import NTSClient


async def search_bid_participants(
    bid_notice_no: str | None = None,
    vendor_biz_no: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict:
    """입찰공고에 참가한 응찰업체 목록 조회 (스텁).

    조달데이터허브 응찰업체 상세 API 연동 후 실 구현으로 교체.
    파라미터:
      - bid_notice_no: 입찰공고번호 (예: '20240101234-00')
      - vendor_biz_no: 응찰업체 사업자등록번호
      - date_from / date_to: YYYY-MM-DD
      - limit: 최대 건수 (기본 20)
    """
    return {
        "status": "not_implemented",
        "domain": "vendor",
        "tool": "search_bid_participants",
        "note": "조달데이터허브 EVAL API 키 발급 후 구현 예정",
    }


async def get_evaluation_scores(
    bid_notice_no: str,
    vendor_biz_no: str | None = None,
) -> dict:
    """입찰공고별 응찰업체 평가점수 조회 (스텁).

    조달데이터허브 평가정보 API 연동 후 실 구현으로 교체.
    파라미터:
      - bid_notice_no: 입찰공고번호 (필수)
      - vendor_biz_no: 특정 업체로 필터 (선택)
    """
    return {
        "status": "not_implemented",
        "domain": "vendor",
        "tool": "get_evaluation_scores",
        "note": "조달데이터허브 EVAL API 키 발급 후 구현 예정",
    }


_NTS_STATUS_CD = {
    "01": "계속사업자",
    "02": "휴업자",
    "03": "폐업자",
}


def _normalize_biz_no(b: str) -> str:
    """사업자번호에서 하이픈/공백 제거하고 10자리 숫자만 반환."""
    digits = "".join(c for c in (b or "") if c.isdigit())
    return digits


async def check_business_status(
    biz_no_list: list[str] | str,
) -> dict:
    """국세청 사업자등록 상태조회 (휴업/폐업 여부).

    NTS odcloud `/status` 엔드포인트 호출. 1회 최대 100건.
    파라미터:
      - biz_no_list: 사업자등록번호 리스트 또는 콤마 구분 문자열 (10자리, 하이픈 무관)
    반환:
      - status: ok | error
      - count: 조회 건수
      - results: [{biz_no, b_stt_cd, b_stt, tax_type_cd, tax_type, end_dt, ...}]
    """
    # 입력 정규화: 문자열이면 콤마 분리, 리스트면 그대로
    if isinstance(biz_no_list, str):
        raw = [x for x in biz_no_list.replace(" ", "").split(",") if x]
    else:
        raw = list(biz_no_list or [])
    nums = [_normalize_biz_no(b) for b in raw]
    nums = [n for n in nums if len(n) == 10]
    if not nums:
        return {"status": "error", "error": "유효한 10자리 사업자번호 0건", "count": 0, "results": []}
    if len(nums) > 100:
        return {"status": "error", "error": "1회 최대 100건 (입력 %d건)" % len(nums), "count": len(nums), "results": []}

    client = NTSClient()
    try:
        raw_resp = await client.post("/status", {"b_no": nums})
    except Exception as e:
        return {"status": "error", "error": str(e), "count": len(nums), "results": []}
    finally:
        await client.aclose()

    items = raw_resp.get("data", []) or []
    # b_stt_cd 한글명 보강
    for it in items:
        cd = it.get("b_stt_cd")
        if cd and not it.get("b_stt"):
            it["b_stt"] = _NTS_STATUS_CD.get(cd, "알수없음")
    return {"status": "ok", "count": len(items), "results": items}


async def verify_business_info(
    items: list[dict],
) -> dict:
    """국세청 사업자등록 진위확인 (대표자명 + 개업일자 일치 검증).

    NTS odcloud `/validate` 엔드포인트 호출. 1회 최대 100건.
    파라미터:
      - items: [{b_no, start_dt, p_nm, p_nm2?, b_nm?, corp_no?, b_sector?, b_type?}]
        * b_no: 사업자번호 (10자리)
        * start_dt: 개업일자 (YYYYMMDD)
        * p_nm: 대표자명
    반환:
      - status: ok | error
      - count: 조회 건수
      - results: [{b_no, valid, status, request_param, ...}]
    """
    if not items:
        return {"status": "error", "error": "items 비어있음", "count": 0, "results": []}
    if len(items) > 100:
        return {"status": "error", "error": "1회 최대 100건 (입력 %d건)" % len(items), "count": len(items), "results": []}

    # b_no 정규화
    norm = []
    for it in items:
        if not isinstance(it, dict):
            continue
        bn = _normalize_biz_no(it.get("b_no", ""))
        if len(bn) != 10:
            continue
        cp = dict(it)
        cp["b_no"] = bn
        norm.append(cp)
    if not norm:
        return {"status": "error", "error": "유효 b_no 0건", "count": 0, "results": []}

    client = NTSClient()
    try:
        raw_resp = await client.post("/validate", {"businesses": norm})
    except Exception as e:
        return {"status": "error", "error": str(e), "count": len(norm), "results": []}
    finally:
        await client.aclose()

    return {
        "status": "ok",
        "count": len(norm),
        "results": raw_resp.get("data", []) or [],
        "match_cnt": raw_resp.get("match_cnt"),
    }


async def placeholder_vendor() -> dict:
    """vendor 영역 도구 자리표시자 (조달데이터허브 EVAL 키 발급 후 교체)."""
    return {"status": "not_implemented", "domain": "vendor"}
