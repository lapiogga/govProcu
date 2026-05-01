"""일일 증분 ETL — search_awards 누적 + Neo4j 동기화 (선택).

NEXT2-3 R2 파이프라인. last_synced_at 이후 신규 낙찰만 처리.

Windows Task Scheduler 등록 (예시):
    schtasks /create /tn "GovProcuETL" /tr "python C:\\Users\\User\\GovProcu\\scripts\\etl_daily.py" /sc DAILY /st 03:00

Linux cron:
    0 3 * * * cd /path/to/GovProcu && python scripts/etl_daily.py >> logs/etl.log 2>&1

산출:
- runtime/ml/dataset_YYYYMMDD.csv (신규 추가분 또는 누적 갱신)
- etl_state 갱신
- (선택) Neo4j 증분 ingest
"""
from __future__ import annotations
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools import award as award_tools
from app.storage.etl_state import get_last_synced_at, mark_success, mark_error


JOB_NAME = "daily_award_etl"


async def main() -> int:
    print(f"=== ETL daily start: {datetime.now().isoformat()} ===")

    last = await get_last_synced_at(JOB_NAME)
    if last:
        date_from = last.strftime("%Y%m%d")
        print(f"증분 동기화: {date_from} ~ today")
    else:
        # 첫 실행: 최근 7일
        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        print(f"첫 실행: 최근 7일 ({date_from} ~ today)")

    date_to = datetime.now().strftime("%Y%m%d")

    try:
        # 4개 업종 모두 수집 (None=전체이지만 안정성 위해 분리)
        all_items = []
        for biz_type in ["용역", "공사", "물품"]:
            r = await award_tools.search_awards(
                date_from=date_from,
                date_to=date_to,
                biz_type=biz_type,
                limit=500,
            )
            items = r.get("items", [])
            all_items.extend(items)
            print(f"  {biz_type}: {len(items)}건")

        # ML dataset 갱신
        from app.ml.dataset import row_to_features, DATASET_DIR
        import csv

        rows = [f for f in (row_to_features(it) for it in all_items) if f]
        out_path = DATASET_DIR / f"dataset_{date_to}.csv"
        if rows:
            keys = list(rows[0].keys())
            mode = "a" if out_path.exists() else "w"
            with open(out_path, mode, encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                if mode == "w":
                    w.writeheader()
                w.writerows(rows)
            print(f"  → {len(rows)}건 저장: {out_path}")

        await mark_success(
            JOB_NAME,
            metadata=f"date_range={date_from}..{date_to}, items={len(all_items)}, ml_rows={len(rows)}",
        )
        print(f"OK ETL 성공: {len(all_items)}건 수집, {len(rows)}건 학습 데이터")
        return 0

    except Exception as exc:
        await mark_error(JOB_NAME, str(exc))
        print(f"FAIL ETL 실패: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
