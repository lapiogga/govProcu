"""P32-R2 fix 적용 후 backend 함수 직접 호출 검증.

5 입찰번호 × {get_award_detail, list_bid_participants, get_pre_specification_detail}
각 응답의 found / participant_count / lookup_mode / winner_name 등 핵심 필드 dump.
"""
from __future__ import annotations
import asyncio
import json
from pathlib import Path

# bypass cache (force fresh) — 테스트 격리
import os
os.environ.setdefault("CACHE_DISABLED", "1")  # 무시될 수도; 캐시 prefix가 v32라 첫 호출은 항상 fresh

from app.tools import award as award_tools
from app.tools import bid as bid_tools


BID_NOS = [
    "R25BK00755515",
    "R25BK00758431",
    "R25BK00760571",
    "R26BK01451151",
    "R26BK01501665",
]

OUT = Path(__file__).resolve().parent / "verify_p32_fix_raw"
OUT.mkdir(exist_ok=True)


async def main():
    summary = {}
    for bid_no in BID_NOS:
        print(f"\n=== {bid_no} ===")
        award_r, parts_r, prespec_r = await asyncio.gather(
            award_tools.get_award_detail(bid_no, "00"),
            award_tools.list_bid_participants(bid_no, "00"),
            bid_tools.get_pre_specification_detail(bid_no, "00"),
        )
        # award
        a_found = award_r.get("found")
        a_lm = award_r.get("lookup_mode")
        a_biz = award_r.get("biz_div")
        a_winner = (award_r.get("summary") or {}).get("winner_name")
        a_amt = (award_r.get("summary") or {}).get("award_amount")
        print(f"  award: found={a_found} biz={a_biz} lookup={a_lm} winner={a_winner} amt={a_amt}")
        # participants
        p_found = parts_r.get("found")
        p_lm = parts_r.get("lookup_mode")
        p_count = parts_r.get("participant_count")
        p_items = len(parts_r.get("items") or [])
        p_biz = parts_r.get("biz_div")
        winner_in_items = next(iter(parts_r.get("items") or [{}]), {}).get("participant_name") if p_items else None
        print(f"  participants: found={p_found} biz={p_biz} lookup={p_lm} count={p_count} items={p_items} winner_item={winner_in_items}")
        # prespec
        s_found = prespec_r.get("found")
        s_lm = prespec_r.get("lookup_mode")
        print(f"  prespec: found={s_found} lookup={s_lm}")

        summary[bid_no] = {
            "award": {"found": a_found, "biz": a_biz, "lookup_mode": a_lm, "winner_name": a_winner, "award_amount": a_amt},
            "participants": {"found": p_found, "biz": p_biz, "lookup_mode": p_lm, "participant_count": p_count, "items_n": p_items, "first_winner": winner_in_items},
            "prespec": {"found": s_found, "lookup_mode": s_lm},
        }
        # full raw dump
        (OUT / f"{bid_no}.json").write_text(
            json.dumps({"award": award_r, "participants": parts_r, "prespec": prespec_r}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    (OUT / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nfull raws → {OUT}/")


if __name__ == "__main__":
    asyncio.run(main())
