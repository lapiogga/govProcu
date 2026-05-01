"""award 영역 MCP 도구 — 개찰/낙찰결과 조회.

G2B `ScsbidInfoService` (낙찰정보서비스)를 기반으로 개찰·낙찰·응찰업체 정보를 조회한다.
업종 분기는 BidPublicInfoService와 동일 패턴(공사/용역/물품).

도구 매트릭스 (REPLAN.md v2):
- list_bid_openings: 개찰목록 (특정 입찰의 응찰결과)
- search_awards: 낙찰목록 (기간/기관/업종)
- get_award_detail: 낙찰 단건 상세
- search_awards_by_vendor: 업체 기준 낙찰 이력 (V4)
- list_bid_participants: 응찰업체 목록 (특정 입찰의 응찰자 + 응찰가)
"""
from __future__ import annotations
from app.config import settings


# === V4: 업체 기준 낙찰 이력 ===

async def search_awards_by_vendor(
    vendor_name: str | None = None,
    vendor_biz_no: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 20,
) -> dict:
    """업체명/사업자번호로 기간 내 낙찰 내역을 조회합니다 (스텁).

    Args:
        vendor_name: 낙찰자명(상호) 부분일치
        vendor_biz_no: 사업자등록번호 (10자리, 하이픈 제외)
        date_from / date_to: 개찰일 시작·종료 (YYYYMMDD)
        biz_type: '공사' | '용역' | '물품'
        limit: 최대 반환 건수 (1~100)

    Returns:
        items, total_count, returned_count, has_more를 포함한 dict.
    """
    return {
        "status": "not_implemented",
        "domain": "award",
        "tool": "search_awards_by_vendor",
        "note": "ScsbidInfoService 매핑 진행 중 — Phase 3에서 구현",
        "items": [],
        "total_count": 0,
        "returned_count": 0,
        "has_more": False,
    }


# === 단위 도구 ===

async def list_bid_openings(
    bid_notice_no: str | None = None,
    inst_code: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 20,
) -> dict:
    """개찰목록을 조회합니다 — 특정 입찰의 개찰 결과 또는 기간 내 개찰 일괄 (스텁).

    Args:
        bid_notice_no: 입찰공고번호 (단건 추적 시)
        inst_code: 발주기관 코드
        date_from / date_to: 개찰일 시작·종료 (YYYYMMDD)
        biz_type: '공사' | '용역' | '물품'
        limit: 최대 반환 건수

    Returns:
        items: 응찰자수·낙찰하한가·개찰일시 등 포함.
    """
    return {
        "status": "not_implemented",
        "domain": "award",
        "tool": "list_bid_openings",
        "note": "ScsbidInfoService 매핑 진행 중",
        "items": [],
        "total_count": 0,
        "returned_count": 0,
        "has_more": False,
    }


async def search_awards(
    inst_code: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    keyword: str | None = None,
    limit: int = 20,
) -> dict:
    """기간/기관/업종/키워드로 낙찰 목록을 조회합니다 (스텁)."""
    return {
        "status": "not_implemented",
        "domain": "award",
        "tool": "search_awards",
        "note": "ScsbidInfoService 매핑 진행 중",
        "items": [],
        "total_count": 0,
        "returned_count": 0,
        "has_more": False,
    }


async def get_award_detail(bid_notice_no: str, bid_ord: str = "00") -> dict:
    """공고번호+차수로 낙찰 단건 상세를 조회합니다 (스텁)."""
    return {
        "status": "not_implemented",
        "domain": "award",
        "tool": "get_award_detail",
        "bid_notice_no": bid_notice_no,
        "bid_ord": bid_ord,
        "note": "ScsbidInfoService 매핑 진행 중",
    }


async def list_bid_participants(
    bid_notice_no: str,
    bid_ord: str = "00",
) -> dict:
    """입찰공고번호로 응찰업체 목록을 조회합니다 (사용자 핵심 요구 — 스텁).

    각 응찰업체의 사업자번호·상호·응찰가·낙찰여부 포함.
    """
    return {
        "status": "not_implemented",
        "domain": "award",
        "tool": "list_bid_participants",
        "bid_notice_no": bid_notice_no,
        "bid_ord": bid_ord,
        "note": "ScsbidInfoService 또는 조달데이터허브 EVAL 매핑 진행 중",
        "items": [],
        "total_count": 0,
    }


# === 호환성 ===

async def placeholder_award() -> dict:
    """award 영역 도구 자리표시자. 호환성을 위해 유지."""
    return {"status": "not_implemented", "domain": "award"}
