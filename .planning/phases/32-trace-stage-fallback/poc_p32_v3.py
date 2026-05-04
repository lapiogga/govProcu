"""P32-R2 v3 — 5건 입찰번호 × 단건 모드 polite probe.

발견 패턴 (v2):
- getScsbidListSttus{X}PPSSrch + inqryDiv=3 + bidNtceNo (낙찰)
- getOpengResultListInfo{X} + inqryDiv=4 + bidNtceNo (개찰결과 non-PPSSrch)
- getOpengResultListInfo{X}PPSSrch + inqryDiv=3 + bidNtceNo (개찰결과 PPSSrch)

5건 × 4종(Cnstwk/Servc/Thng/Frgcpt) × 위 3 모드 → 어디서 hit 하는지.
+ 사전규격 BidPublicInfoService getPrdctClsfcNoPblancListInfo* + inqryDiv 1/2/3
"""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "poc_p32_raw_v3"
RAW_DIR.mkdir(exist_ok=True)

ENV_FILE = Path(r"C:\Users\User\GovProcu\.env")
ENV: dict[str, str] = {}
for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip()
KEY_AWARD = ENV.get("G2B_KEY_AWARD")
KEY_BID = ENV.get("G2B_KEY_BID")
AWARD_BASE = "https://apis.data.go.kr/1230000/as"
BID_BASE = "https://apis.data.go.kr/1230000/ad"

BID_NOS = [
    "R25BK00755515",
    "R25BK00758431",
    "R25BK00760571",
    "R26BK01451151",
    "R26BK01501665",
]

BIZ_DIVS = ["Cnstwk", "Servc", "Thng", "Frgcpt"]

# Mode 1: 낙찰 — getScsbidListSttus{X}PPSSrch + inqryDiv=3
MODE_AWARD_SCS_PPSSRCH = "MODE_AWARD_SCS_PPSSRCH"  # /ScsbidInfoService/getScsbidListSttus{}PPSSrch, div=3
# Mode 2: 개찰결과 non-PPSSrch + inqryDiv=4
MODE_OPENG_NONPPS = "MODE_OPENG_NONPPS"  # /ScsbidInfoService/getOpengResultListInfo{}, div=4
# Mode 3: 개찰결과 PPSSrch + inqryDiv=3
MODE_OPENG_PPSSRCH = "MODE_OPENG_PPSSRCH"  # /ScsbidInfoService/getOpengResultListInfo{}PPSSrch, div=3


async def call(client: httpx.AsyncClient, base: str, path: str, key: str, params: dict) -> dict:
    p = {"ServiceKey": key, "type": "json", **params}
    try:
        resp = await client.get(f"{base}{path}", params=p, timeout=60.0)
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
            "totalCount": body.get("totalCount", 0),
            "n": len(items),
            "first": items[0] if items else None,
        }
    except Exception as e:
        return {"err": str(e)[:200]}


async def probe_award(client, bid_no, biz):
    # Mode 1: getScsbidListSttus{X}PPSSrch + inqryDiv=3 + bidNtceNo
    path = f"/ScsbidInfoService/getScsbidListSttus{biz}PPSSrch"
    return await call(client, AWARD_BASE, path, KEY_AWARD,
                      {"pageNo": 1, "numOfRows": 5, "inqryDiv": "3", "bidNtceNo": bid_no, "bidNtceOrd": "00"})


async def probe_openg_nonpps(client, bid_no, biz):
    path = f"/ScsbidInfoService/getOpengResultListInfo{biz}"
    return await call(client, AWARD_BASE, path, KEY_AWARD,
                      {"pageNo": 1, "numOfRows": 100, "inqryDiv": "4", "bidNtceNo": bid_no, "bidNtceOrd": "00"})


async def probe_openg_ppssrch(client, bid_no, biz):
    path = f"/ScsbidInfoService/getOpengResultListInfo{biz}PPSSrch"
    return await call(client, AWARD_BASE, path, KEY_AWARD,
                      {"pageNo": 1, "numOfRows": 100, "inqryDiv": "3", "bidNtceNo": bid_no, "bidNtceOrd": "00"})


async def probe_prespec(client, bid_no, biz):
    # 사전규격 — biz는 Cnstwk/Servc/Thng만 (외자 prespec 없음)
    if biz == "Frgcpt":
        return None
    path = f"/BidPublicInfoService/getPrdctClsfcNoPblancListInfo{biz}"
    # inqryDiv=2 + bidNtceNo (BidPublicInfoService 단일조회 패턴 A: 2=입찰공고번호)
    r2 = await call(client, BID_BASE, path, KEY_BID,
                    {"pageNo": 1, "numOfRows": 5, "inqryDiv": "2", "bidNtceNo": bid_no, "bidNtceOrd": "00"})
    return {"div=2": r2}


async def probe_one(client, bid_no):
    out = {"bid_no": bid_no, "award": {}, "openg_nonpps": {}, "openg_ppssrch": {}, "prespec": {}}
    for biz in BIZ_DIVS:
        out["award"][biz] = await probe_award(client, bid_no, biz)
        out["openg_nonpps"][biz] = await probe_openg_nonpps(client, bid_no, biz)
        out["openg_ppssrch"][biz] = await probe_openg_ppssrch(client, bid_no, biz)
        out["prespec"][biz] = await probe_prespec(client, bid_no, biz)
    return out


async def main():
    summary = {}
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*(probe_one(client, b) for b in BID_NOS))
    for r in results:
        bid = r["bid_no"]
        (RAW_DIR / f"{bid}.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        award_n = {b: (r["award"][b] or {}).get("n", 0) for b in BIZ_DIVS}
        openg_n_nonpps = {b: (r["openg_nonpps"][b] or {}).get("n", 0) for b in BIZ_DIVS}
        openg_n_ppssrch = {b: (r["openg_ppssrch"][b] or {}).get("n", 0) for b in BIZ_DIVS}
        prespec_n = {b: ((r["prespec"][b] or {}).get("div=2", {}) or {}).get("n", 0) for b in BIZ_DIVS}
        print(f"\n=== {bid} ===")
        print(f"  award (ScsbidListSttus*PPSSrch + div=3): {award_n}  sum={sum(award_n.values())}")
        print(f"  openg non-PPSSrch (div=4): {openg_n_nonpps}  sum={sum(openg_n_nonpps.values())}")
        print(f"  openg PPSSrch (div=3): {openg_n_ppssrch}  sum={sum(openg_n_ppssrch.values())}")
        print(f"  prespec (div=2): {prespec_n}  sum={sum(prespec_n.values())}")
        summary[bid] = {
            "award_total": sum(award_n.values()),
            "award_per_biz": award_n,
            "openg_nonpps_total": sum(openg_n_nonpps.values()),
            "openg_ppssrch_total": sum(openg_n_ppssrch.values()),
            "prespec_total": sum(prespec_n.values()),
        }
    (RAW_DIR / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
