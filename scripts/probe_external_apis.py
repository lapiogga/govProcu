"""외부 발주기관 OpenAPI 어댑터 endpoint 검증 스크립트.

사용자 #43 자율 v3 라운드 N21 — LH/EX/KWater/Korail 어댑터의 추정 endpoint가
실제 data.go.kr 또는 자체 포털 명세와 일치하는지 점검.

사용:
    python scripts/probe_external_apis.py

판정:
- ACTIVE: HTTP 200 + body.items 또는 valid response
- KEY_ERR: HTTP 200 + resultCode=30 (서비스키 등록 안 됨)
- ENDPOINT_ERR: HTTP 404/500 또는 fault 응답
- NO_KEY: 환경변수 미설정

성공 어댑터는 코드의 STATUS=PENDING_IMPLEMENTATION → ACTIVE 로 변경 가능.
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
from pathlib import Path

# .env 로드 (있으면)
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


async def probe_lh(key: str) -> dict:
    """LH 입찰공고 — apis.data.go.kr 표준 + 자체 포털 둘 다 시도."""
    import httpx

    candidates = [
        # data.go.kr 표준 추정
        {
            "url": "https://apis.data.go.kr/1611000/HfBidNoticeService/getHfBidNoticeListInfoInqire",
            "params": {"serviceKey": key, "type": "json", "numOfRows": 1, "pageNo": 1},
        },
        # LH 자체 포털 (검색 결과 1번에서 본 URL)
        {
            "url": "http://openapi.ebid.lh.or.kr/ebid.com.openapi.service.OpenBidInfoList.dev",
            "params": {"serviceKey": key, "numOfRows": 1, "pageNo": 1},
        },
    ]
    return await _probe_candidates("LH", candidates)


async def probe_ex(key: str) -> dict:
    candidates = [
        {
            "url": "https://apis.data.go.kr/1320000/ExBidPublicInfoService/getBidPblancListInfoInqire",
            "params": {"serviceKey": key, "type": "json", "numOfRows": 1, "pageNo": 1},
        },
    ]
    return await _probe_candidates("EX", candidates)


async def probe_kwater(key: str) -> dict:
    candidates = [
        {
            "url": "https://apis.data.go.kr/1480000/KwaterBidPublicInfoService/getBidPblancListInfoInqire",
            "params": {"serviceKey": key, "type": "json", "numOfRows": 1, "pageNo": 1},
        },
    ]
    return await _probe_candidates("KWater", candidates)


async def _probe_candidates(name: str, candidates: list[dict]) -> dict:
    import httpx

    for c in candidates:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(c["url"], params=c["params"])
            status_code = r.status_code
            body_preview = r.text[:300]

            # 명백한 등록키 오류
            if "SERVICE_KEY_IS_NOT_REGISTERED_ERROR" in body_preview:
                return {
                    "name": name,
                    "verdict": "KEY_ERR",
                    "url": c["url"],
                    "http": status_code,
                    "preview": body_preview,
                    "hint": "활용신청 미승인 또는 키 미일치. 마이페이지 → 활용신청 현황 확인.",
                }

            if status_code == 200 and ("response" in body_preview or "items" in body_preview):
                return {
                    "name": name,
                    "verdict": "ACTIVE",
                    "url": c["url"],
                    "http": status_code,
                    "preview": body_preview,
                }

            if status_code == 200 and "fault" in body_preview.lower():
                return {
                    "name": name,
                    "verdict": "FAULT",
                    "url": c["url"],
                    "http": status_code,
                    "preview": body_preview,
                }

            # 다음 candidate 시도
            last_result = {
                "name": name,
                "verdict": "ENDPOINT_ERR",
                "url": c["url"],
                "http": status_code,
                "preview": body_preview,
            }
        except Exception as exc:
            last_result = {
                "name": name,
                "verdict": "EXC",
                "url": c["url"],
                "error": f"{type(exc).__name__}: {str(exc)[:200]}",
            }

    return last_result


async def main():
    results = []

    for env_name, name, fn in [
        ("LH_API_KEY", "LH", probe_lh),
        ("EX_API_KEY", "EX", probe_ex),
        ("KWATER_API_KEY", "KWater", probe_kwater),
    ]:
        key = os.getenv(env_name, "")
        if not key:
            results.append({"name": name, "verdict": "NO_KEY", "env": env_name})
            continue
        r = await fn(key)
        results.append(r)

    print(json.dumps(results, ensure_ascii=False, indent=2))

    # 요약
    print("\n=== 요약 ===")
    for r in results:
        v = r["verdict"]
        marker = {
            "ACTIVE": "OK",
            "KEY_ERR": "WAIT",
            "FAULT": "ERR",
            "ENDPOINT_ERR": "ERR",
            "EXC": "ERR",
            "NO_KEY": "SKIP",
        }.get(v, "?")
        print(f"  [{marker}] {r['name']:8s} {v}")


if __name__ == "__main__":
    asyncio.run(main())
