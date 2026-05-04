"""P32-R2 v4 — 응찰업체 50건 raw list 발신 endpoint 탐색.

PPSSrch / non-PPSSrch 모두 1건 단위 입찰 row만 반환 (prtcptCnum=50 카운트만).
실제 50건 row를 받는 endpoint 찾기:

후보:
- getOpengResultListInfo{X}OpengCompt
- getOpengResultListInfo{X}Failing
- getOpengResultListInfo{X}Rebid
- BidPrcbdrPLInfo (입찰 PL 정보)
- 검색 모드 inqryDiv=1/2/3 + bidNtceNo (PPSSrch 내부 검색)
"""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parent
ENV_FILE = Path(r"C:\Users\User\GovProcu\.env")
ENV: dict[str, str] = {}
for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip()
KEY = ENV.get("G2B_KEY_AWARD")
AWARD_BASE = "https://apis.data.go.kr/1230000/as"

TARGET = "R26BK01451151"  # 응찰 50건

CANDIDATES = [
    # 추가 endpoint 추정
    "/ScsbidInfoService/getOpengResultListInfoCnstwkOpengCompt",
    "/ScsbidInfoService/getOpengResultListInfoCnstwkFailing",
    "/ScsbidInfoService/getOpengResultListInfoCnstwkRebid",
    "/ScsbidInfoService/getOpengResultListInfoCnstwkPreparPcDetail",
    "/ScsbidInfoService/getBidPrcbdrPLInfoCnstwkPPSSrch",
    "/ScsbidInfoService/getBidPrcbdrPLInfoCnstwk",
    # PPSSrch 페이징 — numOfRows 100, items=50건 도착 가능성
    "/ScsbidInfoService/getOpengResultListInfoCnstwkPPSSrch",
]


async def call(client, path, params):
    p = {"ServiceKey": KEY, "type": "json", **params}
    try:
        resp = await client.get(f"{AWARD_BASE}{path}", params=p, timeout=60.0)
        try:
            data = json.loads(resp.text)
        except Exception:
            return {"status": resp.status_code, "raw": resp.text[:300]}
        body = (data.get("response", {}) or {}).get("body", {}) or {}
        header = (data.get("response", {}) or {}).get("header", {}) or {}
        items = body.get("items", [])
        if isinstance(items, dict):
            items = items.get("item", [])
        if not isinstance(items, list):
            items = [items] if items else []
        return {
            "rc": header.get("resultCode"),
            "msg": header.get("resultMsg"),
            "totalCount": body.get("totalCount", 0),
            "n": len(items),
            "first_keys": list(items[0].keys()) if items else [],
            "first": items[0] if items else None,
        }
    except Exception as e:
        return {"err": str(e)[:200]}


async def main():
    async with httpx.AsyncClient() as client:
        for path in CANDIDATES:
            print(f"\n--- {path} ---")
            for params in [
                {"pageNo": 1, "numOfRows": 100, "inqryDiv": "1", "bidNtceNo": TARGET, "bidNtceOrd": "00"},
                {"pageNo": 1, "numOfRows": 100, "inqryDiv": "2", "bidNtceNo": TARGET, "bidNtceOrd": "00"},
                {"pageNo": 1, "numOfRows": 100, "inqryDiv": "3", "bidNtceNo": TARGET, "bidNtceOrd": "00"},
                {"pageNo": 1, "numOfRows": 100, "inqryDiv": "4", "bidNtceNo": TARGET, "bidNtceOrd": "00"},
            ]:
                r = await call(client, path, params)
                print(f"  div={params['inqryDiv']}: rc={r.get('rc')} tc={r.get('totalCount')} n={r.get('n')} msg={(r.get('msg') or '')[:60]}")
                if r.get("n", 0) > 1:
                    print(f"    *** MULTI-ITEM RESULT: keys={r.get('first_keys')}")


if __name__ == "__main__":
    asyncio.run(main())
