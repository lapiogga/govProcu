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


async def check_business_status(biz_nos: list[str] | str) -> dict:
    """국세청 사업자등록 상태조회 (계속/휴업/폐업).

    Args:
        biz_nos: 사업자번호 단건(문자열) 또는 다건(리스트). 하이픈은 자동 제거.
                  한 호출당 최대 100건.

    Returns:
        items: [
            {
                "biz_no": "1058705373",
                "status_code": "01",         # 01=계속, 02=휴업, 03=폐업
                "status": "계속사업자",
                "tax_type": "...",
                "end_date": None,            # 폐업일자 (폐업자만)
                "raw": {...}
            }, ...
        ],
        requested_count, returned_count
    """
    if isinstance(biz_nos, str):
        biz_nos = [biz_nos]
    if not biz_nos:
        raise ValueError("biz_nos는 1건 이상 필요합니다.")
    if len(biz_nos) > 100:
        raise ValueError("한 호출당 최대 100건. 분할 호출 필요.")

    normalized = [_normalize_biz_no(b) for b in biz_nos]
    bad = [b for b, n in zip(biz_nos, normalized) if len(n) != 10]
    if bad:
        raise ValueError(f"유효하지 않은 사업자번호(10자리 아님): {bad}")

    client = NTSClient()
    try:
        body = await client.post("/status", {"b_no": normalized})
    finally:
        await client.aclose()

    raw_items = body.get("data") or []
    items = []
    for raw in raw_items:
        cd = raw.get("b_stt_cd") or ""
        items.append({
            "biz_no": raw.get("b_no"),
            "status_code": cd,
            "status": _NTS_STATUS_CD.get(cd) or raw.get("b_stt") or "알수없음",
            "tax_type": raw.get("tax_type"),
            "end_date": raw.get("end_dt") or None,
            "raw": raw,
        })

    return {
        "items": items,
        "requested_count": len(normalized),
        "returned_count": len(items),
    }


def _normalize_yyyymmdd(s: str) -> str:
    """YYYY-MM-DD / YYYY.MM.DD / YYYYMMDD 등을 YYYYMMDD 8자리로 정규화."""
    digits = "".join(c for c in (s or "") if c.isdigit())
    return digits


async def verify_business_info(
    biz_no: str,
    start_dt: str,
    p_nm: str,
    b_nm: str | None = None,
    corp_no: str | None = None,
    p_nm2: str | None = None,
    b_sector: str | None = None,
    b_type: str | None = None,
    b_adr: str | None = None,
) -> dict:
    """국세청 사업자등록 진위확인.

    필수 3개(사업자번호 + 개업일자 + 대표자명)가 모두 일치해야 valid='01' 반환.
    선택 필드를 추가하면 그 항목까지 일치 여부 확인 가능.

    Args:
        biz_no: 사업자번호 10자리 (하이픈 허용, 자동 제거)
        start_dt: 개업일자 (YYYYMMDD / YYYY-MM-DD 모두 허용)
        p_nm: 대표자 성명
        b_nm: 상호 (선택)
        corp_no: 법인등록번호 13자리 (선택, 하이픈 자동 제거)
        p_nm2: 외국인 대표자 영문성명 (선택)
        b_sector: 주업태명 (선택)
        b_type: 주종목명 (선택)
        b_adr: 사업장 주소 (선택)

    Returns:
        valid: '01' (일치) | '02' (불일치)
        valid_message: 진위확인 사유 텍스트
        request_param: 서버에 전달된 정규화된 파라미터
        raw: 원본 응답 1건
    """
    biz_n = _normalize_biz_no(biz_no)
    if len(biz_n) != 10:
        raise ValueError(f"biz_no가 10자리가 아닙니다: {biz_no}")
    sd = _normalize_yyyymmdd(start_dt)
    if len(sd) != 8:
        raise ValueError(f"start_dt가 YYYYMMDD 8자리가 아닙니다: {start_dt}")
    if not p_nm:
        raise ValueError("p_nm(대표자 성명)은 필수입니다.")

    payload = {
        "b_no": biz_n,
        "start_dt": sd,
        "p_nm": p_nm,
    }
    if p_nm2:
        payload["p_nm2"] = p_nm2
    if b_nm:
        payload["b_nm"] = b_nm
    if corp_no:
        payload["corp_no"] = _normalize_biz_no(corp_no)  # 13자리 숫자만
    if b_sector:
        payload["b_sector"] = b_sector
    if b_type:
        payload["b_type"] = b_type
    if b_adr:
        payload["b_adr"] = b_adr

    client = NTSClient()
    try:
        body = await client.post("/validate", {"businesses": [payload]})
    finally:
        await client.aclose()

    raw_items = body.get("data") or []
    if not raw_items:
        return {
            "valid": None,
            "valid_message": body.get("status_code") or "응답 없음",
            "request_param": payload,
            "raw": body,
        }
    raw = raw_items[0]
    return {
        "valid": raw.get("valid"),  # '01' 일치 / '02' 불일치
        "valid_message": raw.get("valid_msg"),
        "request_param": raw.get("request_param") or payload,
        "raw": raw,
    }


async def placeholder_vendor() -> dict:
    """vendor 영역 도구 자리표시자. M5 단계에서 실제 도구로 교체."""
    return {"status": "not_implemented", "domain": "vendor"}


# === V1~V3: vendor-by-vendor 검색 (사용자 5/2 추가 지시) ===
# V4 search_awards_by_vendor는 award.py에 위치.

async def search_bids_by_vendor(
    vendor_biz_no: str | None = None,
    vendor_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 20,
) -> dict:
    """업체 기준 기간 내 응찰한 입찰공고 목록 조회 (V1, 스텁).

    BidPublicInfoService 풀 페이지 스캔 + 응찰업체 필드(prtcptCnum 등) 클라이언트 필터.
    또는 list_bid_participants를 역인덱싱하는 우회 경로.
    """
    return {
        "status": "not_implemented",
        "domain": "vendor",
        "tool": "search_bids_by_vendor",
        "items": [],
        "total_count": 0,
        "note": "V1 — 응찰업체 매핑 endpoint 확정 후 구현",
    }


async def search_participations_by_vendor(
    vendor_biz_no: str | None = None,
    vendor_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict:
    """업체 기준 기간 내 응찰 이력(응찰가 포함) 조회 (V2, 스텁).

    조달데이터허브 EVAL API(G2B_KEY_EVAL) 발급 후 본문 교체 예정.
    """
    return {
        "status": "not_implemented",
        "domain": "vendor",
        "tool": "search_participations_by_vendor",
        "items": [],
        "total_count": 0,
        "note": "V2 — G2B_KEY_EVAL 키 발급 + EVAL endpoint 매핑 후 구현",
    }


async def search_openings_by_vendor(
    vendor_biz_no: str | None = None,
    vendor_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict:
    """업체가 참여한 입찰의 개찰 결과 이력 조회 (V3, 스텁).

    ScsbidInfoService 개찰목록 + 응찰업체 필터.
    """
    return {
        "status": "not_implemented",
        "domain": "vendor",
        "tool": "search_openings_by_vendor",
        "items": [],
        "total_count": 0,
        "note": "V3 — ScsbidInfoService 개찰 endpoint 확정 후 구현",
    }
