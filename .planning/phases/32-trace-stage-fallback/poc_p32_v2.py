"""P32-R2 v2 — ScsbidInfoService inqryDiv 매핑 탐색.

DOSSIER §6.3: "(또는 일부 endpoint는 1=공고일시, 2=개찰일시, 3=입찰공고번호)"
inqryDiv=4가 미작동 → 1/2/3/4 모두 시도. + non-PPSSrch endpoint도 시도.
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

# 사용자 보고 적중 케이스 (Cnstwk + R25BK00760571 + inqryDiv=4 = 1건 hit)
TARGET = "R25BK00760571"

# 4종 endpoint × inqryDiv 1/2/3/4 × PPSSrch 유무
ENDPOINTS = {
    "scsbid_Cnstwk": "/ScsbidInfoService/getScsbidListSttusCnstwk",
    "scsbid_Servc": "/ScsbidInfoService/getScsbidListSttusServc",
    "scsbid_CnstwkPPSSrch": "/ScsbidInfoService/getScsbidListSttusCnstwkPPSSrch",
    "scsbid_ServcPPSSrch": "/ScsbidInfoService/getScsbidListSttusServcPPSSrch",
    "openg_Cnstwk": "/ScsbidInfoService/getOpengResultListInfoCnstwk",
    "openg_Servc": "/ScsbidInfoService/getOpengResultListInfoServc",
    "openg_CnstwkPPSSrch": "/ScsbidInfoService/getOpengResultListInfoCnstwkPPSSrch",
    "openg_ServcPPSSrch": "/ScsbidInfoService/getOpengResultListInfoServcPPSSrch",
}


async def call(client: httpx.AsyncClient, path: str, params: dict) -> dict:
    p = {"ServiceKey": KEY, "type": "json", **params}
    try:
        resp = await client.get(f"{AWARD_BASE}{path}", params=p, timeout=60.0)
        text = resp.text
        try:
            data = json.loads(text)
        except Exception:
            return {"status": resp.status_code, "raw": text[:300]}
        body = (data.get("response", {}) or {}).get("body", {}) or {}
        header = (data.get("response", {}) or {}).get("header", {}) or {}
        items = body.get("items", [])
        if isinstance(items, dict):
            items = items.get("item", [])
        if not isinstance(items, list):
            items = [items] if items else []
        return {
            "rc": header.get("resultCode"),
            "totalCount": body.get("totalCount", 0),
            "items_n": len(items),
            "first_item_keys": list(items[0].keys())[:8] if items else [],
        }
    except Exception as e:
        return {"err": str(e)[:200]}


async def main():
    async with httpx.AsyncClient() as client:
        print(f"target bid_no = {TARGET}")
        for label, ep in ENDPOINTS.items():
            print(f"\n--- {label} ({ep}) ---")
            for div in ["1", "2", "3", "4"]:
                params = {"pageNo": 1, "numOfRows": 5, "inqryDiv": div, "bidNtceNo": TARGET, "bidNtceOrd": "00"}
                r = await call(client, ep, params)
                # 기간 unset 모드
                rc = r.get("rc")
                tc = r.get("totalCount")
                n = r.get("items_n")
                print(f"  inqryDiv={div} unset_period: rc={rc} totalCount={tc} items_n={n}")

            # inqryDiv=4 + 추정 기간 (R25 → 2025년)
            params_with_period = {
                "pageNo": 1, "numOfRows": 5, "inqryDiv": "4",
                "bidNtceNo": TARGET, "bidNtceOrd": "00",
                "inqryBgnDt": "202501010000", "inqryEndDt": "202501312359",
            }
            r2 = await call(client, ep, params_with_period)
            print(f"  inqryDiv=4 + period 2025-01: rc={r2.get('rc')} tc={r2.get('totalCount')} n={r2.get('items_n')}")


if __name__ == "__main__":
    asyncio.run(main())
