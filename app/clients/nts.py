"""국세청 사업자등록 진위확인/상태조회 비동기 HTTP 클라이언트.

G2B와 달리 POST + JSON body 기반. serviceKey는 쿼리 파라미터로 부여한다.
"""
from __future__ import annotations
from typing import Any
import httpx
from tenacity import (
    AsyncRetrying, stop_after_attempt, wait_exponential,
    retry_if_exception_type,
)
from app.config import settings


class NTSClient:
    """NTS odcloud API 호출용 비동기 클라이언트.

    - POST + JSON body
    - serviceKey 자동 부여
    - 재시도: 지수 백오프 (1s → 2s → 4s, 최대 3회)
    """

    def __init__(self, timeout: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=settings.nts_base_url,
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    async def post(self, endpoint: str, body: dict[str, Any]) -> dict:
        """NTS endpoint POST 호출. 정규화된 dict 반환."""
        if not settings.nts_api_key:
            raise RuntimeError("NTS_API_KEY 미설정 — .env에 NTS_API_KEY=... 등록 필요")

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=4),
            retry=retry_if_exception_type((httpx.HTTPError,)),
            reraise=True,
        ):
            with attempt:
                resp = await self._client.post(
                    endpoint,
                    params={"serviceKey": settings.nts_api_key},
                    json=body,
                )
                resp.raise_for_status()
                return resp.json()

        raise RuntimeError("unreachable")  # pragma: no cover

    async def aclose(self):
        await self._client.aclose()
