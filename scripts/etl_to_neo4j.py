"""GovProcu → Neo4j ETL (Phase R1 PoC).

사용자 5/2 22번 R&D 트랙. docs/GRAPH-FEASIBILITY.md Phase R1 검증 스크립트.

기능:
1. G2B 입찰공고 N일치 풀스캔 (search_bid_notices)
2. 각 공고별 낙찰·응찰업체 수집 (get_award_detail / list_bid_participants)
3. Neo4j에 idempotent ingest (UNWIND + MERGE)
4. 4개 relational key 정규화 (사업자번호 하이픈 제거 등)

사용법:
    pip install neo4j  # 또는 pyproject에 추가
    python scripts/etl_to_neo4j.py --days 7 --biz-type 용역

환경변수:
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=govprocu_poc
"""
from __future__ import annotations
import argparse
import asyncio
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트 import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools import bid as bid_tools
from app.tools import award as award_tools


def normalize_biz_no(s: str | None) -> str | None:
    """사업자번호 정규화 (하이픈·공백 제거, 10자리 숫자)."""
    if not s:
        return None
    digits = re.sub(r"\D", "", str(s))
    return digits if len(digits) == 10 else None


def normalize_bid_no(s: str | None) -> str | None:
    if not s:
        return None
    return str(s).strip() or None


async def collect_bids(days: int, biz_type: str | None) -> list[dict]:
    """최근 N일 입찰공고 + 낙찰 + 응찰 수집."""
    end = datetime.now()
    start = end - timedelta(days=days)
    date_from = start.strftime("%Y%m%d")
    date_to = end.strftime("%Y%m%d")

    print(f"[1/3] G2B 공고 수집: {date_from} ~ {date_to} (biz_type={biz_type or 'all'})")
    notices = await bid_tools.search_bid_notices(
        biz_type=biz_type,
        date_from=date_from,
        date_to=date_to,
        limit=100,  # PoC — 100건이면 충분
    )
    notice_items = notices.get("items", [])
    print(f"  → {len(notice_items)}건 수집")

    print("[2/3] 각 공고별 낙찰자·응찰업체 수집")
    enriched = []
    for i, notice in enumerate(notice_items[:50]):  # PoC: 상위 50건
        bid_no = notice.get("bid_no")
        bid_ord = notice.get("bid_ord") or "00"
        if not bid_no:
            continue

        award = None
        try:
            a = await award_tools.get_award_detail(bid_no, bid_ord)
            if a.get("found"):
                award = a.get("summary")
        except Exception:
            pass

        participants = []
        try:
            p = await award_tools.list_bid_participants(bid_no, bid_ord)
            if p.get("found"):
                participants = p.get("items", [])
        except Exception:
            pass

        enriched.append({
            "notice": notice,
            "award": award,
            "participants": participants,
        })

        if (i + 1) % 10 == 0:
            print(f"  진행: {i+1}/{len(notice_items[:50])}")

    return enriched


def ingest_to_neo4j(records: list[dict]) -> dict:
    """Neo4j idempotent ingest. UNWIND + MERGE 패턴.

    requires: pip install neo4j
    """
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("ERROR: neo4j Python driver 필요. pip install neo4j")
        sys.exit(1)

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "govprocu_poc")

    print(f"[3/3] Neo4j ingest: {uri}")
    driver = GraphDatabase.driver(uri, auth=(user, pwd))

    notice_count = 0
    award_count = 0
    participation_count = 0

    with driver.session() as session:
        for rec in records:
            notice = rec["notice"]
            bid_no = normalize_bid_no(notice.get("bid_no"))
            bid_ord = notice.get("bid_ord") or "00"
            if not bid_no:
                continue

            inst_name = notice.get("inst_name") or "Unknown"
            inst_code = notice.get("raw", {}).get("dminsttCd") if notice.get("raw") else None

            # Agency + BidNotice
            session.run(
                """
                MERGE (a:Agency {inst_code: coalesce($inst_code, $inst_name)})
                  ON CREATE SET a.inst_name = $inst_name
                MERGE (n:BidNotice {bid_notice_no: $bid_no, bid_ord: $bid_ord})
                  SET n.bid_title = $title,
                      n.notice_date = date($notice_date),
                      n.base_amount = $base_amount,
                      n.biz_type = $biz_type
                MERGE (n)-[:ISSUED_BY]->(a)
                """,
                bid_no=bid_no, bid_ord=bid_ord,
                inst_name=inst_name, inst_code=inst_code,
                title=notice.get("title"),
                notice_date=notice.get("publish_date", "")[:10] or "1970-01-01",
                base_amount=notice.get("estimated_price") or 0,
                biz_type=notice.get("biz_type"),
            )
            notice_count += 1

            # Award + Vendor
            if rec["award"]:
                a = rec["award"]
                v_biz = normalize_biz_no(a.get("winner_biz_no"))
                if v_biz:
                    session.run(
                        """
                        MERGE (v:Vendor {biz_no: $biz_no})
                          ON CREATE SET v.vendor_name = $name
                        MATCH (n:BidNotice {bid_notice_no: $bid_no, bid_ord: $bid_ord})
                        MERGE (n)-[r:AWARDED_TO]->(v)
                          SET r.amount = $amount,
                              r.event_at = date($event_at),
                              r.award_rate = $award_rate
                        """,
                        biz_no=v_biz,
                        name=a.get("winner_name"),
                        bid_no=bid_no, bid_ord=bid_ord,
                        amount=a.get("award_amount") or 0,
                        event_at=(a.get("open_date") or "")[:10] or "1970-01-01",
                        award_rate=a.get("award_rate"),
                    )
                    award_count += 1

            # Participations
            for p in rec["participants"]:
                p_biz = normalize_biz_no(p.get("participant_biz_no"))
                if p_biz:
                    session.run(
                        """
                        MERGE (v:Vendor {biz_no: $biz_no})
                          ON CREATE SET v.vendor_name = $name
                        MATCH (n:BidNotice {bid_notice_no: $bid_no, bid_ord: $bid_ord})
                        MERGE (v)-[r:PARTICIPATED_IN]->(n)
                          SET r.bid_amount = $amount,
                              r.bid_rank = $rank
                        """,
                        biz_no=p_biz,
                        name=p.get("participant_name"),
                        bid_no=bid_no, bid_ord=bid_ord,
                        amount=p.get("participant_bid_amount") or 0,
                        rank=p.get("opening_rank"),
                    )
                    participation_count += 1

    driver.close()

    return {
        "notice_count": notice_count,
        "award_count": award_count,
        "participation_count": participation_count,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="GovProcu → Neo4j PoC ETL")
    parser.add_argument("--days", type=int, default=7, help="최근 N일 (기본 7)")
    parser.add_argument("--biz-type", type=str, default=None, help="공사/용역/물품")
    args = parser.parse_args()

    records = await collect_bids(args.days, args.biz_type)
    print(f"\n수집 완료: {len(records)} records")

    if input("Neo4j ingest 진행? (y/N) ").lower() != "y":
        print("ingest 건너뜀.")
        return

    stats = ingest_to_neo4j(records)
    print(f"\n=== Ingest 완료 ===")
    print(f"BidNotice nodes: {stats['notice_count']}")
    print(f"Award rels: {stats['award_count']}")
    print(f"Participation rels: {stats['participation_count']}")
    print("\n검증: http://localhost:7474 → MATCH (n) RETURN count(n)")


if __name__ == "__main__":
    asyncio.run(main())
