"""한국수자원공사(K-water) OpenAPI 어댑터.

발급처: data.kwater.or.kr OpenAPI 또는 data.go.kr "수자원공사 입찰"
환경변수: KWATER_API_KEY
"""
from __future__ import annotations

from app.clients.external.base import BaseAgencyAdapter, AdapterStatus


class KWaterAdapter(BaseAgencyAdapter):
    AGENCY_KEY = "kwater"
    AGENCY_NAME = "한국수자원공사"
    BASE_URL = "https://opendata.kwater.or.kr"  # placeholder
    SERVICE_KEY_ENV = "KWATER_API_KEY"
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
                "note": "K-water OpenAPI 키 발급 필요.",
            }
        return {
            "items": [],
            "total_count": 0,
            "agency": self.AGENCY_KEY,
            "status": "active_placeholder",
        }
