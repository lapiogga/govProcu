"""외부 발주기관 OpenAPI 어댑터 — 공통 베이스 클래스.

각 기관별 어댑터는 본 베이스를 상속하고 다음을 구현:
- AGENCY_KEY: 'lh', 'ex', 'kwater', 'korail' 등
- AGENCY_NAME: 한국어 표시명
- BASE_URL: API base URL
- SERVICE_KEY_ENV: 환경변수 이름
- async def search_bids(...): 표준 인터페이스
- async def normalize(...): 응답 → GovProcu 표준 형태로 정규화

운영 검증된 호출 패턴이 있을 때만 status='active'. 그 전엔 'pending_implementation'.
"""
from __future__ import annotations
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class AdapterStatus(str, Enum):
    ACTIVE = "active"
    PENDING_KEY = "pending_key"
    PENDING_IMPLEMENTATION = "pending_implementation"
    DEPRECATED = "deprecated"


async def call_data_go_kr_standard(
    base_url: str,
    endpoint: str,
    service_key: str,
    params: dict[str, Any] | None = None,
    timeout: float = 20.0,
) -> dict:
    """data.go.kr 표준 OpenAPI 호출 + 응답 정규화.

    표준 응답 형태 (JSON):
        { "response": { "header": {...}, "body": { "items": [...], "totalCount": N } } }

    Args:
        base_url: 예 'https://apis.data.go.kr/B552555'
        endpoint: 예 '/SrvcThngStocknflwInfoInqireSvc'
        service_key: 발급키 (URL 인코딩 안 된 평문)
        params: 추가 쿼리 파라미터
        timeout: 초 단위

    Returns:
        {"items": [...], "total_count": int, "raw": {...}, "endpoint": str}
        실패 시 {"items": [], "total_count": 0, "error": "..."}
    """
    try:
        import httpx
    except ImportError:
        return {"items": [], "total_count": 0, "error": "httpx not installed"}

    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    qs = {"serviceKey": service_key, "type": "json", "_type": "json"}
    if params:
        qs.update({k: v for k, v in params.items() if v is not None})

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url, params=qs)
        if r.status_code != 200:
            return {
                "items": [],
                "total_count": 0,
                "error": f"HTTP {r.status_code}",
                "endpoint": url,
            }

        try:
            data = r.json()
        except Exception:
            return {
                "items": [],
                "total_count": 0,
                "error": "non-JSON response",
                "raw_text": r.text[:500],
                "endpoint": url,
            }

        body = (data.get("response") or {}).get("body") or {}
        items_field = body.get("items")
        if isinstance(items_field, dict):
            items_field = items_field.get("item", [])
        if items_field is None:
            items_field = []
        if isinstance(items_field, dict):
            items_field = [items_field]

        return {
            "items": items_field,
            "total_count": int(body.get("totalCount", len(items_field) or 0)),
            "raw": data,
            "endpoint": url,
        }
    except Exception as exc:
        return {
            "items": [],
            "total_count": 0,
            "error": f"{type(exc).__name__}: {str(exc)[:200]}",
            "endpoint": url,
        }


class BaseAgencyAdapter(ABC):
    """발주기관 OpenAPI 어댑터 추상 클래스."""

    AGENCY_KEY: str = ""
    AGENCY_NAME: str = ""
    BASE_URL: str = ""
    SERVICE_KEY_ENV: str = ""
    STATUS: AdapterStatus = AdapterStatus.PENDING_IMPLEMENTATION

    @classmethod
    def has_key(cls) -> bool:
        """환경변수에 키가 설정되어 있나."""
        return bool(os.getenv(cls.SERVICE_KEY_ENV))

    @classmethod
    def current_status(cls) -> AdapterStatus:
        """런타임 상태. 키 없으면 PENDING_KEY로 강제."""
        if cls.STATUS == AdapterStatus.PENDING_IMPLEMENTATION:
            return AdapterStatus.PENDING_IMPLEMENTATION
        if not cls.has_key():
            return AdapterStatus.PENDING_KEY
        return cls.STATUS

    @classmethod
    def metadata(cls) -> dict:
        """기관 메타데이터."""
        return {
            "agency": cls.AGENCY_KEY,
            "name": cls.AGENCY_NAME,
            "base_url": cls.BASE_URL,
            "service_key_env": cls.SERVICE_KEY_ENV,
            "status": cls.current_status().value,
        }

    @abstractmethod
    async def search_bids(
        self,
        keyword: str | None = None,
        biz_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 20,
    ) -> dict:
        """표준 입찰 검색 인터페이스.

        Returns:
            {
                "items": [...],            # 정규화된 공고 row 리스트
                "total_count": int,
                "agency": str,             # AGENCY_KEY
                "endpoint": str,           # 호출한 endpoint
                "raw_count": int,          # 원본 응답 건수
            }
        """
        ...

    def normalize_row(self, raw: dict) -> dict:
        """API 응답 row를 GovProcu 표준으로 정규화. 어댑터별 override."""
        return {
            "bid_no": raw.get("bidNtceNo") or raw.get("bid_no"),
            "title": raw.get("bidNtceNm") or raw.get("title"),
            "inst_name": self.AGENCY_NAME,
            "raw": raw,
        }
