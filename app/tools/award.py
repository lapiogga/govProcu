"""award 영역 MCP 도구 — 낙찰/개찰결과 조회.

G2B `ScsbidInfoService` (낙찰정보서비스)의 `getOpengResultListInfoXxxPPSSrch` 시리즈를 사용한다.
서버측 업체명 필터 미지원으로 추정 → 풀 페이지 스캔 + 클라이언트 측 필터링.
응답의 `bidwinnrNm`(낙찰자명) 또는 `prcbdrBizno`(낙찰자사업자등록번호)를 키로 매칭.

NOTE (2026-05-01): 본 모듈은 사용자가 mount에서 실 구현 작성 도중 절단되었다.
스케줄 task가 자동 복원하면서 search_awards_by_vendor를 스텁으로 유지한다.
실제 G2B 호출 로직은 다음 사용자 편집 사이클에서 채워진다.
"""
from __future__ import annotations


async def search_awards_by_vendor(
    vendor_name: str | None = None,
    vendor_biz_no: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    biz_type: str | None = None,
    limit: int = 20,
) -> dict:
    """업체명 또는 사업자번호로 최근 낙찰내역을 조회합니다 (M5 단계 스텁).

    Args:
        vendor_name: 낙찰자명(상호) 부분일치
        vendor_biz_no: 사업자등록번호 (10자리, 하이픈 제외)
        date_from: 개찰일 시작 (YYYYMMDD)
        date_to: 개찰일 종료 (YYYYMMDD)
        biz_type: '공사' | '용역' | '물품'
        limit: 최대 반환 건수 (1~100)

    Returns:
        items, total_count, returned_count, has_more를 포함한 dict.
        현재는 스텁 — 실제 구현은 사용자 편집 사이클에서 추가 예정.
    """
    return {
        "status": "not_implemented",
        "domain": "award",
        "tool": "search_awards_by_vendor",
        "note": "ScsbidInfoService 통합 예정 — 현재 등록만 활성화된 스텁",
        "items": [],
        "total_count": 0,
        "returned_count": 0,
        "has_more": False,
    }


async def placeholder_award() -> dict:
    """award 영역 도구 자리표시자. 호환성을 위해 유지."""
    return {"status": "not_implemented", "domain": "award"}
