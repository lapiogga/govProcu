"""한국도로공사 OpenAPI 어댑터.

발급처: data.go.kr "도로공사 입찰" 또는 ex.co.kr 데이터센터(data.ex.co.kr)
환경변수: EX_API_KEY
endpoint 후보:
    /openapi/safeBidNotice (도로공사 자체 데이터센터)
    또는 /1320000/ExBidPublicInfoService (data.go.kr 게시 시)
"""
from __future__ import annotations
import os

from app.clients.external.base import (
    BaseAgencyAdapter,
    AdapterStatus,
    call_data_go_kr_standard,
)


class ExAdapter(BaseAgencyAdapter):
    AGENCY_KEY = "ex"
    AGENCY_NAME = "한국도로공사"
    BASE_URL = "https://apis.data.go.kr/1320000"
    SERVICE_KEY_ENV = "EX_API_KEY"
    DEFAULT_ENDPOINT = "/ExBidPublicInfoService/getBidPblancListInfoInqire"
    STATUS = AdapterStatus.PENDING_IMPLEMENTATION

    async def search_bids(
        self,
        keyword: str | None = None,
        biz_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 20,
    ) -> dict:
        status = self.current_status()
        if status == AdapterStatus.PENDING_IMPLEMENTATION:
            return {
                "items": [],
                "total_count": 0,
                "agency": self.AGENCY_KEY,
                "status": status.value,
                "note": (
                    "도로공사 OpenAPI 키 발급 + endpoint 검증 필요. "
                    "data.go.kr 에서 '도로공사 입찰' 검색 또는 data.ex.co.kr 직접 발급."
                ),
            }
        if status == AdapterStatus.PENDING_KEY:
            return {
                "items": [],
                "total_count": 0,
                "agency": self.AGENCY_KEY,
                "status": status.value,
                "note": f"{self.SERVICE_KEY_ENV} 환경변수 미설정.",
            }

        params = {"numOfRows": limit, "pageNo": 1}
        if keyword:
            params["bidNtceNm"] = keyword
        if date_from:
            params["bidNtceBgnDt"] = date_from
        if date_to:
            params["bidNtceEndDt"] = date_to

        result = await call_data_go_kr_standard(
            base_url=self.BASE_URL,
            endpoint=self.DEFAULT_ENDPOINT,
            service_key=os.environ[self.SERVICE_KEY_ENV],
            params=params,
        )
        return {
            "items": [self.normalize_row(it) for it in result.get("items", [])],
            "total_count": result.get("total_count", 0),
            "agency": self.AGENCY_KEY,
            "endpoint": result.get("endpoint", ""),
            "raw_count": len(result.get("items", [])),
            "status": status.value,
            "error": result.get("error"),
        }

    def normalize_row(self, raw: dict) -> dict:
        return {
            "bid_no": raw.get("bidNtceNo"),
            "bid_ord": raw.get("bidNtceOrd"),
            "title": raw.get("bidNtceNm"),
            "inst_name": self.AGENCY_NAME,
            "notice_date": raw.get("bidNtceDt"),
            "deadline": raw.get("bidNtceEndDt") or raw.get("opengDt"),
            "base_amount": raw.get("presmptPrce") or raw.get("asignBdgtAmt"),
            "raw": raw,
        }
