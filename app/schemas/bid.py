"""입찰공고 도메인 스키마."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class BidNoticeSearchInput(BaseModel):
    """search_bid_notices 입력."""
    keyword: str | None = Field(None, description="제목/내용 키워드 (예: '정보화 용역')")
    bid_notice_no: str | None = Field(None, description="공고번호 정확 매칭 (단건 조회 폴백용)")
    biz_type: Literal["공사", "용역", "물품", "외자", "기타", None] = Field(None, description="업종 구분 (P31-R2: 기타 추가)")
    region: str | None = Field(None, description="지역 (시도명)")
    inst_name: str | None = Field(None, description="발주기관명 부분일치")
    indstryty_cd: str | None = Field(None, description="업종코드 (G2B indstrytyCd 서버측 필터 — P31-R2)")
    date_from: str | None = Field(None, description="공고일 시작 (YYYYMMDD)")
    date_to: str | None = Field(None, description="공고일 종료 (YYYYMMDD)")
    limit: int = Field(20, ge=1, le=100, description="최대 반환 건수")
    page: int = Field(1, ge=1, le=100, description="페이지 번호 (cursor 페이징)")
    scan_pages: int = Field(1, ge=1, le=10, description="스캔 페이지 수 (LIKE 매칭률 향상, 응답 시간 trade-off)")


class BidNoticeSummary(BaseModel):
    """공고 요약 (목록용)."""
    bid_no: str
    bid_ord: str | None = None
    title: str
    inst_name: str | None = None
    biz_type: str | None = None
    srvce_div: str | None = None       # P31-R2 (F21): "일반용역" / "기술용역"
    ppsw_gnrl_yn: str | None = None    # P31-R2 (F21): Y/N (PPS 일반용역 여부)
    region: str | None = None
    estimated_price: int | None = None
    publish_date: str | None = None
    deadline_date: str | None = None
    raw: dict | None = None  # 원본 보존


class BidNoticeSearchResult(BaseModel):
    """search_bid_notices 출력."""
    items: list[BidNoticeSummary]
    total_count: int
    returned_count: int
    has_more: bool
    page: int = 1
