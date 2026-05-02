"""한국토지주택공사(LH) OpenAPI 어댑터 — 정보화 영역 외, 보류.

5/2 사용자 #49: 정보화 업무영역(IT 용역)과 LH(건축/토목/주택) 거리 → 비-사용 결정.
스킬레톤은 유지 — 향후 건설/토목 분야 확장 시 활용 가능.

만약 활성화한다면:
- data.go.kr 에서 LH 입찰공고/사전규격/개찰/계약/발주계획 5종 활용신청 (자동승인)
- LH 자체 포털(http://openapi.ebid.lh.or.kr/...) 은 별도 키 활성화 필요
  (data.go.kr 통합 키와 별개. 마이페이지 → LH 별도 인증 절차)
- endpoint 패턴 (확인됨):
    /OpenBidInfoList.dev    (입찰공고)
    /OpenAdvcinfoReqList.dev (사전규격)
    EUC-KR XML 응답
"""
from __future__ import annotations
import os

from app.clients.external.base import (
    BaseAgencyAdapter,
    AdapterStatus,
    call_data_go_kr_standard,
)


class LHAdapter(BaseAgencyAdapter):
    AGENCY_KEY = "lh"
    AGENCY_NAME = "한국토지주택공사(LH)"
    BASE_URL = "https://apis.data.go.kr/1611000"
    SERVICE_KEY_ENV = "LH_API_KEY"
    DEFAULT_ENDPOINT = "/HfBidNoticeService/getHfBidNoticeListInfoInqire"
    STATUS = AdapterStatus.PENDING_IMPLEMENTATION  # 키 발급 + 검증 후 ACTIVE 로 갱신

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
                    "LH OpenAPI 키 발급 + endpoint 검증 필요. "
                    "data.go.kr 에서 'LH 입찰' 검색 → 활용신청 → LH_API_KEY 환경변수 설정 → "
                    "본 어댑터 STATUS=AdapterStatus.ACTIVE 로 갱신."
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

        # ACTIVE — data.go.kr 표준 호출
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
            "notice_date": raw.get("bidNtceDt") or raw.get("rgstDt"),
            "deadline": raw.get("bidNtceEndDt") or raw.get("opengDt"),
            "base_amount": raw.get("presmptPrce") or raw.get("asignBdgtAmt"),
            "raw": raw,
        }
