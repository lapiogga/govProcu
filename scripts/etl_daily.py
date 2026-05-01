"""일일 증분 ETL — search_awards 누적 + ML dataset + Neo4j (선택).

NEXT2-3 + NEXT3-5 통합. last_synced_at 이후 신규 낙찰만 처리.

Windows Task Scheduler 등록:
    deploy/scheduler/setup-windows-task.ps1 (PowerShell 관리자)

Linux cron:
    0 3 * * * cd /path/to/GovProcu && python scripts/etl_daily.py >> logs/etl.log 2>&1

산출:
- runtime/ml/dataset_YYYYMMDD.csv (신규 추가분 또는 누적 갱신)
- runtime/govprocu.db (etl_state 갱신)
- (선택) Neo4j 증분 ingest — NEO4J_URI 환경변수 있을 때만

환경변수 (선택):
- NEO4J_URI: bolt://localhost:7687
- NEO4J_USER: neo4j
- NEO4J_PASSWORD: govprocu_poc
"""
from __future__ import annotations
import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools import award as award_tools
from app.tools import bid as bid_tools
from app.storage.etl_state import get_last_synced_at, mark_success, mark_error


JOB_NAME = "daily_award_etl"
NEO4J_JOB_NAME = "daily_neo4j_etl"


async def collect_awards(date_from: str, date_to: str) -> list[dict]:
    """4개 업종(용역/공사/물품/외자) 낙찰 데이터 수집."""
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
    return all_items


async def update_ml_dataset(items: list[dict], date_to: str) -> int:
    """row_to_features → CSV append. 반환: 추가 행수."""
    from app.ml.dataset import row_to_features, DATASET_DIR
    import csv

    rows = [f for f in (row_to_features(it) for it in items) if f]
    out_path = DATASET_DIR / f"dataset_{date_to}.csv"
    if rows:
        keys = list(rows[0].keys())
        mode = "a" if out_path.exists() else "w"
        with open(out_path, mode, encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            if mode == "w":
                w.writeheader()
            w.writerows(rows)
        print(f"  ML dataset → {len(rows)}건: {out_path}")
    return len(rows)


async def ingest_to_neo4j(items: list[dict]) -> dict:
    """Neo4j 증분 ingest (NEO4J_URI 설정 시만).

    각 낙찰에 대해:
    - Agency / Vendor / BidNotice MERGE
    - AWARDED_TO 관계 (idempotent)
    """
    if not os.getenv("NEO4J_URI"):
        return {"skipped": "NEO4J_URI not set"}

    try:
        from neo4j import GraphDatabase
    except ImportError:
        return {"error": "neo4j driver missing — pip install -e .[graph]"}

    import re

    def normalize_biz(s: str | None) -> str | None:
        if not s:
            return None
        d = re.sub(r"\D", "", str(s))
        return d if len(d) == 10 else None

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "govprocu_poc")

    notice_count = 0
    award_count = 0

    try:
        driver = GraphDatabase.driver(uri, auth=(user, pwd))
        with driver.session() as session:
            for it in items:
                bid_no = it.get("bid_notice_no")
                if not bid_no:
                    continue
                bid_ord = it.get("bid_ord") or "00"
                inst_name = it.get("inst_name") or "Unknown"

                # MERGE Agency + BidNotice
                session.run(
                    """
                    MERGE (a:Agency {inst_code: $inst_name})
                      ON CREATE SET a.inst_name = $inst_name
                    MERGE (n:BidNotice {bid_notice_no: $bid_no, bid_ord: $bid_ord})
                      SET n.bid_title = $title,
                          n.biz_type = $biz_type
                    MERGE (n)-[:ISSUED_BY]->(a)
                    """,
                    bid_no=bid_no, bid_ord=bid_ord,
                    inst_name=inst_name,
                    title=it.get("bid_title"),
                    biz_type=it.get("biz_type"),
                )
                notice_count += 1

                # MERGE Vendor + AWARDED_TO
                v_biz = normalize_biz(it.get("winner_biz_no"))
                if v_biz:
                    open_date = (it.get("open_date") or "")[:8]
                    event_at = "1970-01-01"
                    if len(open_date) == 8:
                        event_at = f"{open_date[:4]}-{open_date[4:6]}-{open_date[6:8]}"
                    session.run(
                        """
                        MERGE (v:Vendor {biz_no: $biz_no})
                          ON CREATE SET v.vendor_name = $name
                        MATCH (n:BidNotice {bid_notice_no: $bid_no, bid_ord: $bid_ord})
                        MERGE (n)-[r:AWARDED_TO]->(v)
                          SET r.amount = $amount,
                              r.event_at = date($event_at)
                        """,
                        biz_no=v_biz,
                        name=it.get("winner_name"),
                        bid_no=bid_no, bid_ord=bid_ord,
                        amount=int(str(it.get("award_amount", 0)).replace(",", "")) if it.get("award_amount") else 0,
                        event_at=event_at,
                    )
                    award_count += 1

        driver.close()
        print(f"  Neo4j → notices={notice_count}, awards={award_count}")
        return {"notice_count": notice_count, "award_count": award_count}
    except Exception as exc:
        return {"error": str(exc)[:200]}


async def main() -> int:
    print(f"=== ETL daily start: {datetime.now().isoformat()} ===")

    last = await get_last_synced_at(JOB_NAME)
    if last:
        date_from = last.strftime("%Y%m%d")
        print(f"증분 동기화: {date_from} ~ today")
    else:
        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        print(f"첫 실행: 최근 7일 ({date_from} ~ today)")

    date_to = datetime.now().strftime("%Y%m%d")

    try:
        # 1. 낙찰 데이터 수집
        all_items = await collect_awards(date_from, date_to)

        # 2. ML dataset 갱신
        ml_rows = await update_ml_dataset(all_items, date_to)

        # 3. Neo4j 증분 ingest (선택)
        neo4j_result = await ingest_to_neo4j(all_items)

        await mark_success(
            JOB_NAME,
            metadata=(
                f"date_range={date_from}..{date_to}, items={len(all_items)}, "
                f"ml_rows={ml_rows}, neo4j={neo4j_result}"
            ),
        )

        # Neo4j 별도 job 상태도 기록
        if "error" not in neo4j_result and "skipped" not in neo4j_result:
            await mark_success(
                NEO4J_JOB_NAME,
                metadata=f"awards={neo4j_result.get('award_count', 0)}",
            )
        elif "error" in neo4j_result:
            await mark_error(NEO4J_JOB_NAME, neo4j_result["error"])

        print(f"OK ETL 성공: {len(all_items)}건 수집, {ml_rows}건 학습 데이터")
        return 0

    except Exception as exc:
        await mark_error(JOB_NAME, str(exc))
        print(f"FAIL ETL 실패: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
