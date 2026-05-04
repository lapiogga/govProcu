"""P32-R2 raw evidence — 5 입찰번호 ScsbidInfoService inqryDiv=4 단건 호출 검증.

목적: trace 5 stage actions (get_award_detail / list_bid_participants /
get_pre_specification_detail) R-prefix 단건 폴백 fix 적용 전후 raw 응답 비교 근거 마련.

호출 모드:
- ScsbidInfoService getScsbidListSttus{Cnstwk,Servc,Thng,Frgcpt}: inqryDiv=4 + bidNtceNo
- ScsbidInfoService getOpengResultListInfo{Cnstwk,Servc,Thng,Frgcpt}: inqryDiv=4 + bidNtceNo
  (기존 코드 PPSSrch 사용 — 단순 단건은 PPSSrch 미접미사 buildable 또는 PPSSrch+inqryDiv=2)

DOSSIER §6.3: ScsbidInfoService inqryDiv 1=등록일시 2=공고일시 3=개찰일시 4=입찰공고번호.

산출물: poc_p32_raw/{bid_no}_{endpoint}.json
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "poc_p32_raw"
RAW_DIR.mkdir(exist_ok=True)

# .env 직접 파싱 (settings 우회 — backend 미기동 상태에서 호출 가능)
ENV_FILE = Path(r"C:\Users\User\GovProcu\.env")
ENV: dict[str, str] = {}
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            ENV[k.strip()] = v.strip()

KEY = ENV.get("G2B_KEY_AWARD") or ENV.get("G2B_KEY_BID")
AWARD_BASE = "https://apis.data.go.kr/1230000/as"
BID_BASE = "https://apis.data.go.kr/1230000/ad"

BID_NOS = [
    "R25BK00755515",
    "R25BK00758431",
    "R25BK00760571",
    "R26BK01451151",
    "R26BK01501665",
]

# Award 단건/응찰업체 endpoint
SCS_ENDPOINTS = {
    "Cnstwk": "/ScsbidInfoService/getScsbidListSttusCnstwk",
    "Servc": "/ScsbidInfoService/getScsbidListSttusServc",
    "Thng": "/ScsbidInfoService/getScsbidListSttusThng",
    "Frgcpt": "/ScsbidInfoService/getScsbidListSttusFrgcpt",
}
OPENG_ENDPOINTS = {
    "Cnstwk": "/ScsbidInfoService/getOpengResultListInfoCnstwkPPSSrch",
    "Servc": "/ScsbidInfoService/getOpengResultListInfoServcPPSSrch",
    "Thng": "/ScsbidInfoService/getOpengResultListInfoThngPPSSrch",
    "Frgcpt": "/ScsbidInfoService/getOpengResultListInfoFrgcptPPSSrch",
}
# 사전규격 endpoint
PRESPEC_ENDPOINTS = {
    "Cnstwk": "/BidPublicInfoService/getPrdctClsfcNoPblancListInfoCnstwk",
    "Servc": "/BidPublicInfoService/getPrdctClsfcNoPblancListInfoServc",
    "Thng": "/BidPublicInfoService/getPrdctClsfcNoPblancListInfoThng",
}


async def call(client: httpx.AsyncClient, base: str, path: str, params: dict) -> dict:
    p = {"ServiceKey": KEY, "type": "json", **params}
    url = f"{base}{path}"
    try:
        resp = await client.get(url, params=p, timeout=60.0)
        text = resp.text
        try:
            data = json.loads(text)
        except Exception:
            return {"_status": resp.status_code, "_text": text[:500], "_url": str(resp.url)}
        body = (data.get("response", {}) or {}).get("body", {}) or {}
        header = (data.get("response", {}) or {}).get("header", {}) or {}
        items = body.get("items", [])
        if isinstance(items, dict):
            items = items.get("item", [])
        if not isinstance(items, list):
            items = [items] if items else []
        return {
            "_status": resp.status_code,
            "resultCode": header.get("resultCode"),
            "totalCount": body.get("totalCount", 0),
            "item_count": len(items),
            "items": items[:5],  # 첫 5건만 dump (용량)
        }
    except Exception as e:
        return {"_error": str(e)[:300]}


async def probe_one(client: httpx.AsyncClient, bid_no: str) -> dict:
    out: dict = {"bid_no": bid_no, "scs_award": {}, "openg_participants": {}, "prespec": {}}

    # 1. Award (낙찰): ScsbidInfoService inqryDiv=4 + bidNtceNo, 4종 fan-out
    for label, ep in SCS_ENDPOINTS.items():
        out["scs_award"][label] = await call(
            client, AWARD_BASE, ep,
            {"pageNo": 1, "numOfRows": 5, "inqryDiv": "4", "bidNtceNo": bid_no, "bidNtceOrd": "00"},
        )

    # 2. 응찰업체 (개찰결과): getOpengResultListInfo*PPSSrch + inqryDiv=4 + bidNtceNo, 4종 fan-out
    for label, ep in OPENG_ENDPOINTS.items():
        out["openg_participants"][label] = await call(
            client, AWARD_BASE, ep,
            {"pageNo": 1, "numOfRows": 100, "inqryDiv": "4", "bidNtceNo": bid_no, "bidNtceOrd": "00"},
        )

    # 3. 사전규격: BidPublicInfoService getPrdctClsfcNoPblancListInfo* + inqryDiv=2 + bidNtceNo
    for label, ep in PRESPEC_ENDPOINTS.items():
        out["prespec"][label] = await call(
            client, BID_BASE, ep,
            {"pageNo": 1, "numOfRows": 5, "inqryDiv": "2", "bidNtceNo": bid_no, "bidNtceOrd": "00"},
        )

    return out


async def main():
    if not KEY:
        print("ERROR: G2B_KEY_AWARD not in .env", file=sys.stderr)
        sys.exit(1)
    summary = {}
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*(probe_one(client, b) for b in BID_NOS))
    for r in results:
        bid = r["bid_no"]
        out_path = RAW_DIR / f"{bid}.json"
        out_path.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")

        # summary line
        award_hits = {l: v.get("item_count", 0) for l, v in r["scs_award"].items()}
        openg_hits = {l: v.get("item_count", 0) for l, v in r["openg_participants"].items()}
        prespec_hits = {l: v.get("item_count", 0) for l, v in r["prespec"].items()}
        summary[bid] = {
            "award_inqryDiv=4": award_hits,
            "openg_PPSSrch_inqryDiv=4": openg_hits,
            "prespec_inqryDiv=2": prespec_hits,
        }
        print(f"\n=== {bid} ===")
        print(f"  award (inqryDiv=4): {award_hits} totalSum={sum(award_hits.values())}")
        print(f"  openg PPSSrch (inqryDiv=4): {openg_hits} totalSum={sum(openg_hits.values())}")
        print(f"  prespec (inqryDiv=2): {prespec_hits} totalSum={sum(prespec_hits.values())}")
    (RAW_DIR / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nraw dumps → {RAW_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
