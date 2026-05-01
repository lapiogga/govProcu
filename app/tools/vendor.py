"""vendor 영역 MCP 도구.

응찰업체별 정보 / 입찰참가 이력 / 평가점수 조회용. 현재 단계는 골격(스텁)이며,
조달데이터허브 또는 추가 OpenAPI 신청 후 endpoint 정보가 확정되면 실 구현으로 교체한다.

연동 예정 API 후보:
  - 조달데이터허브: 응찰업체 상세/평가정보 (G2B_KEY_EVAL 키 사용 예정)
  - 입찰참가자격등록정보 (data.go.kr 신청 검토)
"""
from __future__ import annotations


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


async def placeholder_vendor() -> dict:
    """vendor 영역 도구 자리표시자. M5 단계에서 실제 도구로 교체."""
    return {"status": "not_implemented", "domain": "vendor"}
