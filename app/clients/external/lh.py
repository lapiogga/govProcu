"""한국토지주택공사(LH) OpenAPI 어댑터.

발급처: data.go.kr "LH 입찰" 검색 (또는 LH 공식 데이터포털 lh.or.kr)
환경변수: LH_API_KEY

키 발급 후 STATUS = AdapterStatus.ACTIVE 로 변경 + search_bids 본문 구현.
"""
from __future__ import annotations

from app.clients.external.base import BaseAgencyAdapter, AdapterStatus


class LHAdapter(BaseAgencyAdapter):
    AGENCY_KEY = "lh"
    AGENCY_NAME = "한국토지주택공사(LH)"
    BASE_URL = "https://apis.data.go.kr/B552555"  # placeholder
    SERVICE_KEY_ENV = "LH_API_KEY"
    STATUS = AdapterStatus.PENDING_IMPLEMENTATION  # 키 발급 + 운영 검증 후 ACTIVE

    async def search_bids(
        self,
        keyword: str | None = None,
        biz_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 20,
    ) -> dict:
        if self.current_status() != AdapterStatus.ACTIVE:
            return {
                "items": [],
                "total_count": 0,
                "agency": self.AGENCY_KEY,
                "status": self.current_status().value,
                "note": "LH OpenAPI 키 발급 + 어댑터 구현 필요. data.go.kr에서 'LH 입찰' 검색.",
            }
        # TODO: 키 발급 후 실 호출 구현
        return {
            "items": [],
            "total_count": 0,
            "agency": self.AGENCY_KEY,
            "status": "active_placeholder",
        }
