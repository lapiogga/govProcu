"""한국도로공사 OpenAPI 어댑터.

발급처: data.go.kr "도로공사 입찰" 또는 ex.co.kr 데이터센터
환경변수: EX_API_KEY
"""
from __future__ import annotations

from app.clients.external.base import BaseAgencyAdapter, AdapterStatus


class ExAdapter(BaseAgencyAdapter):
    AGENCY_KEY = "ex"
    AGENCY_NAME = "한국도로공사"
    BASE_URL = "https://data.ex.co.kr/openapi"  # placeholder
    SERVICE_KEY_ENV = "EX_API_KEY"
    STATUS = AdapterStatus.PENDING_IMPLEMENTATION

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
                "note": "도로공사 OpenAPI 키 발급 필요.",
            }
        return {
            "items": [],
            "total_count": 0,
            "agency": self.AGENCY_KEY,
            "status": "active_placeholder",
        }
