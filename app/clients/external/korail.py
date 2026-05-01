"""한국철도공사(코레일) OpenAPI 어댑터.

발급처: info.korail.com 또는 data.go.kr
환경변수: KORAIL_API_KEY
"""
from __future__ import annotations

from app.clients.external.base import BaseAgencyAdapter, AdapterStatus


class KorailAdapter(BaseAgencyAdapter):
    AGENCY_KEY = "korail"
    AGENCY_NAME = "한국철도공사(코레일)"
    BASE_URL = "https://info.korail.com/openapi"  # placeholder
    SERVICE_KEY_ENV = "KORAIL_API_KEY"
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
                "note": "코레일 OpenAPI 키 발급 필요.",
            }
        return {
            "items": [],
            "total_count": 0,
            "agency": self.AGENCY_KEY,
            "status": "active_placeholder",
        }
