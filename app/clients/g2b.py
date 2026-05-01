"""나라장터 OpenAPI 비동기 HTTP 클라이언트."""
from __future__ import annotations
from typing import Any
import httpx
from tenacity import (
    AsyncRetrying, stop_after_attempt, wait_exponential,
    retry_if_exception_type
)
from app.config import settings
from app.core.errors import map_g2b_response


class G2BClient:
    """G2B API 호출용 비동기 클라이언트.

    - 재시도: 지수 백오프 (1s → 2s → 4s, 최대 3회)
    - 자동 type=json 부여
    - 에러 코드 정규화
    """

    def __init__(self, timeout: float = 10.0):
        self._client = httpx.AsyncClient(
            base_url=settings.g2b_base_url,
            timeout=timeout,
            headers={"Accept": "application/json"},
        )

    async def call(
        self,
        endpoint: str,
        service_key: str,
        params: dict[str, Any],
    ) -> dict:
        """G2B 엔드포인트 호출. 정규화된 dict 반환."""
        if not service_key:
            raise RuntimeError(f"service_key 미설정 (endpoint={endpoint})")

        full_params = {
            "ServiceKey": service_key,
            "type": "json",
            **{k: v for k, v in params.items() if v is not None},
        }

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=4),
            retry=retry_if_exception_type((httpx.HTTPError,)),
            reraise=True,
        ):
            with attempt:
                resp = await self._client.get(endpoint, params=full_params)
                resp.raise_for_status()
                data = resp.json()

        # G2B 응답 표준 검증
        body_root = data.get("response", data)
        header = body_root.get("header", {})
        map_g2b_response(header)
        return body_root.get("body", {})

    async def aclose(self):
        await self._client.aclose()
