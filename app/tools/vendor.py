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

