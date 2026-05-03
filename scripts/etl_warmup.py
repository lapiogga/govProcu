"""ETL warmup — 인기 검색 키워드/발주기관을 미리 호출하여 Redis cache 채움.

자율 v27.1: 사용자 첫 호출 = cache hit (0.5초) 보장.

cache 인프라 (자율 v23.3 + v23.5):
- app/core/cache.py — Redis 기반 (redis.asyncio)
- cache_result decorator: 11개 도구에 30분 TTL 적용
- 첫 호출은 cache miss (5~20초) → warmup이 미리 채워두면 사용자 hit

Windows Task Scheduler 등록 (PowerShell 관리자):
    schtasks /create /tn "GovProcu Cache Warmup" /tr "python C:/path/to/scripts/etl_warmup.py" /sc minute /mo 30

Linux cron:
    */30 * * * * cd /path/to/GovProcu && python scripts/etl_warmup.py >> logs/warmup.log 2>&1

조정:
- POPULAR_KEYWORDS / POPULAR_AGENCIES를 운영 환경에 맞게 수정
- 사용자 발화 학습 후 자동 갱신은 후속 sprint
"""
from __future__ import annotations
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools import bid as bid_tools
from app.tools import award as award_tools
from app.tools import workflow as workflow_tools


# 운영 환경에 맞게 조정. 사용자 검색 빈도 통계로 자동 학습은 후속 sprint.
POPULAR_KEYWORDS = ["정보화", "구축사업", "유지보수", "용역"]
POPULAR_AGENCIES = ["국방부", "경찰청", "조달청", "한국수자원공사"]
POPULAR_BIZ_TYPES_ALL: list[str | None] = [None, "용역", "공사", "물품"]
POPULAR_BIZ_TYPES_AWARD: list[str | None] = [None, "용역", "공사"]


async def warmup_bids(date_from: str, date_to: str) -> int:
    """인기 keyword × biz_type 조합 search_bid_notices."""
    count = 0
    for kw in POPULAR_KEYWORDS:
        for biz in POPULAR_BIZ_TYPES_ALL:
            try:
                await bid_tools.search_bid_notices(
                    keyword=kw,
                    biz_type=biz,
                    date_from=date_from,
                    date_to=date_to,
                    limit=30,
                )
                count += 1
                print(f"  bids: kw={kw!r} biz={biz!r}")
            except Exception as exc:  # noqa: BLE001
                print(f"  fail bids kw={kw!r} biz={biz!r}: {str(exc)[:120]}")
    return count


async def warmup_awards(date_from: str, date_to: str) -> int:
    """인기 inst_name × biz_type 조합 search_awards."""
    count = 0
    for inst in POPULAR_AGENCIES:
        for biz in POPULAR_BIZ_TYPES_AWARD:
            try:
                await award_tools.search_awards(
                    inst_name=inst,
                    biz_type=biz,
                    date_from=date_from,
                    date_to=date_to,
                    limit=100,
                )
                count += 1
                print(f"  awards: inst={inst!r} biz={biz!r}")
            except Exception as exc:  # noqa: BLE001
                print(f"  fail awards inst={inst!r} biz={biz!r}: {str(exc)[:120]}")
    return count


async def warmup_agency_history(date_from: str, date_to: str) -> int:
    """인기 inst_name agency_procurement_history (W5)."""
    count = 0
    for inst in POPULAR_AGENCIES:
        try:
            await workflow_tools.agency_procurement_history(
                inst_name=inst,
                date_from=date_from,
                date_to=date_to,
                limit=30,
            )
            count += 1
            print(f"  history: inst={inst!r}")
        except Exception as exc:  # noqa: BLE001
            print(f"  fail history inst={inst!r}: {str(exc)[:120]}")
    return count


async def main() -> int:
    started = datetime.now()
    print(f"=== ETL warmup start: {started.isoformat()} ===")

    today = datetime.now()
    date_from = (today - timedelta(days=30)).strftime("%Y%m%d")
    date_to = today.strftime("%Y%m%d")
    print(f"  range: {date_from}~{date_to} (30일)")

    bids_count = await warmup_bids(date_from, date_to)
    awards_count = await warmup_awards(date_from, date_to)
    history_count = await warmup_agency_history(date_from, date_to)

    elapsed = (datetime.now() - started).total_seconds()
    print(
        f"OK warmup 완료: bids={bids_count}, awards={awards_count}, "
        f"history={history_count} / elapsed={elapsed:.1f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
