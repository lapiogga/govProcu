"""한국수자원공사(K-water) OpenAPI 어댑터 — 계약 결과 공개 API.

발급처: data.go.kr "한국수자원공사_전자조달 계약정보공개" (dataset 15101620)
환경변수: KWATER_API_KEY (G2B 통합 키와 동일 단일 인증키 재사용 OK)
endpoint: https://apis.data.go.kr/B500001/ebid/cntrct3/cntrwkList (공사 계약)

5/2 N23 — 사용자가 마이페이지 미리보기 URL 제공:
    GET https://apis.data.go.kr/B500001/ebid/cntrct3/cntrwkList
        ?serviceKey=...&pageNo=1&numOfRows=N&_type=xml&searchDt=YYYYMM
    응답: response > body > items > item (XML, JSON 둘 다 지원)

KWater는 data.go.kr에 입찰공고 OpenAPI 미공개. 계약 결과(cntrwkList)만 공개 →
search_bids 는 빈 결과 반환, search_contracts 가 핵심 메서드.
"""
from __future__ import annotations
import os
import re

from app.clients.external.base import (
    BaseAgencyAdapter,
    AdapterStatus,
    call_data_go_kr_standard,
)


def _to_int(s: str | int | None) -> int | None:
    if s is None:
        return None
    try:
        return int(re.sub(r"[^\d]", "", str(s)))
    except (ValueError, TypeError):
        return None


class KWaterAdapter(BaseAgencyAdapter):
    AGENCY_KEY = "kwater"
    AGENCY_NAME = "한국수자원공사"
    BASE_URL = "https://apis.data.go.kr/B500001"
    SERVICE_KEY_ENV = "KWATER_API_KEY"
    # 공사 계약 (다른 endpoint: 용역/물품은 마이페이지 추가 명세 필요)
    DEFAULT_ENDPOINT = "/ebid/cntrct3/cntrwkList"
    STATUS = AdapterStatus.ACTIVE  # 5/2 N23 검증 완료 (HTTP 200, totalCount 61)

    async def search_bids(
        self,
        keyword: str | None = None,
        biz_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 20,
    ) -> dict:
        # KWater 는 data.go.kr 에 입찰공고 미공개 — 계약만 (search_contracts 사용)
        return {
            "items": [],
            "total_count": 0,
            "agency": self.AGENCY_KEY,
            "status": self.current_status().value,
            "note": (
                "K-water 는 data.go.kr 에 입찰공고 OpenAPI 미제공. "
                "계약 결과는 search_contracts() 사용 (cntrwkList)."
            ),
        }

    async def search_contracts(
        self,
        search_dt: str | None = None,
        limit: int = 20,
    ) -> dict:
        """K-water 공사 계약 정보 검색.

        Args:
            search_dt: 검색 연월 YYYYMM (예: 202205). 미지정 시 최근 월 1건 호출.
            limit: 페이지당 row 수 (max 1000)
        """
        status = self.current_status()
        if status == AdapterStatus.PENDING_KEY:
            return {
                "items": [],
                "total_count": 0,
                "agency": self.AGENCY_KEY,
                "status": status.value,
                "note": f"{self.SERVICE_KEY_ENV} 환경변수 미설정.",
            }

        params: dict = {"numOfRows": limit, "pageNo": 1}
        if search_dt:
            params["searchDt"] = search_dt

        result = await call_data_go_kr_standard(
            base_url=self.BASE_URL,
            endpoint=self.DEFAULT_ENDPOINT,
            service_key=os.environ[self.SERVICE_KEY_ENV],
            params=params,
        )
        return {
            "items": [self.normalize_contract(it) for it in result.get("items", [])],
            "total_count": result.get("total_count", 0),
            "agency": self.AGENCY_KEY,
            "endpoint": result.get("endpoint", ""),
            "raw_count": len(result.get("items", [])),
            "status": status.value,
            "error": result.get("error"),
        }

    def normalize_contract(self, raw: dict) -> dict:
        """KWater 응답 → GovProcu 표준 contract row 매핑.

        K-water 응답 필드 (5/2 미리보기 검증):
          cntrctDe        계약일자 (YYYYMMDD, int)
          cntrctDeptNm    계약부서명 (예: 광주수도지사)
          cntrctDivNm     계약구분명 (공사/용역/물품)
          cntrctEntrpsNm  계약업체명
          ctrmthdNm       계약방법명 (일반경쟁/제한경쟁/소액전자/...)
          lastCtramt      최종계약금액 (예: '55,182,000')
          lmttMthNm       제한방법명 (지역제한 등)
          ordgNo          발주번호 (예: C5202205025)
          ordgTit         발주제목
          strwrkDe        시작/종료일자 (YYYYMMDD~YYYYMMDD)
        """
        period = str(raw.get("strwrkDe") or "")
        period_from, _, period_to = period.partition("~")

        return {
            "contract_no": raw.get("ordgNo"),
            "contract_date": str(raw.get("cntrctDe") or ""),
            "title": raw.get("ordgTit"),
            "inst_name": self.AGENCY_NAME,
            "dept_name": raw.get("cntrctDeptNm"),
            "biz_type": raw.get("cntrctDivNm"),
            "winner_name": raw.get("cntrctEntrpsNm"),
            "contract_method": raw.get("ctrmthdNm"),
            "limit_method": raw.get("lmttMthNm"),
            "contract_amount": _to_int(raw.get("lastCtramt")),
            "period_from": period_from.strip() or None,
            "period_to": period_to.strip() or None,
            "raw": raw,
        }

    def normalize_row(self, raw: dict) -> dict:
        # base 호환 (search_bids 미지원으로 사실상 미사용)
        return self.normalize_contract(raw)
