"""Neo4j Phase R1 PoC 자동 검증 스크립트.

사용자 5/2 24번 [NEXT-3]. docs/GRAPH-FEASIBILITY.md 성공 기준 검증.

자동화 단계:
1. Docker compose 가동 상태 확인
2. Neo4j 연결 + 스키마 적용
3. ETL 1주치 (이미 ingest 됐으면 skip)
4. 5개 검증 쿼리 실행 + 응답시간 측정
5. 성공 기준: 모든 쿼리 1초 이내

사용:
    pip install neo4j
    cd deploy/neo4j-poc && docker compose up -d
    python scripts/verify_neo4j_poc.py
"""
from __future__ import annotations
import os
import sys
import time
from pathlib import Path


def check_neo4j_connection() -> bool:
    """Neo4j 연결 가능한지 확인."""
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("ERROR: pip install neo4j")
        return False

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "govprocu_poc")

    try:
        driver = GraphDatabase.driver(uri, auth=(user, pwd))
        driver.verify_connectivity()
        driver.close()
        print(f"OK Neo4j 연결 ({uri})")
        return True
    except Exception as exc:
        print(f"FAIL Neo4j 연결 실패: {exc}")
        print("  → docker compose up -d 가동 확인")
        return False


def apply_schema() -> bool:
    """01_schema.cypher 적용."""
    from neo4j import GraphDatabase
    schema_path = Path(__file__).resolve().parent.parent / "deploy/neo4j-poc/cypher/01_schema.cypher"
    if not schema_path.exists():
        print(f"FAIL 스키마 파일 없음: {schema_path}")
        return False

    cypher = schema_path.read_text(encoding="utf-8")
    # 주석 제거 + 빈 줄 제거 + ; 단위 분리
    statements = []
    for stmt in cypher.split(";"):
        cleaned = "\n".join(
            line for line in stmt.splitlines()
            if line.strip() and not line.strip().startswith("//")
        ).strip()
        if cleaned:
            statements.append(cleaned)

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "govprocu_poc")

    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    applied = 0
    with driver.session() as session:
        for stmt in statements:
            try:
                session.run(stmt)
                applied += 1
            except Exception as exc:
                print(f"  SKIP (이미 존재 가능): {stmt[:50]}... → {str(exc)[:80]}")
    driver.close()
    print(f"OK 스키마 적용: {applied}/{len(statements)} statement")
    return True


def count_nodes() -> dict:
    """현재 노드/엣지 수."""
    from neo4j import GraphDatabase
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "govprocu_poc")

    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    counts = {}
    with driver.session() as session:
        for label in ["BidNotice", "Agency", "Vendor", "Award", "Contract"]:
            r = session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
            counts[label] = r.single()["c"]
        r = session.run("MATCH ()-[r]->() RETURN count(r) AS c")
        counts["_total_rels"] = r.single()["c"]
    driver.close()
    return counts


def run_validation_queries() -> dict:
    """5개 검증 쿼리 실행 + 응답시간 측정.

    docs/GRAPH-FEASIBILITY.md 성공 기준: 모든 쿼리 1초 이내.
    """
    from neo4j import GraphDatabase
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "govprocu_poc")

    queries = {
        "Q1_거래네트워크": (
            """MATCH (a:Agency)<-[:ISSUED_BY]-(n:BidNotice)-[:AWARDED_TO]->(v:Vendor)
               RETURN a.inst_name AS agency, v.vendor_name AS vendor,
                      count(n) AS deals
               ORDER BY deals DESC LIMIT 10""",
            {},
        ),
        "Q2_업체별_입찰빈도": (
            """MATCH (v:Vendor)-[:PARTICIPATED_IN]->(n:BidNotice)
               RETURN v.biz_no, v.vendor_name, count(n) AS bid_count
               ORDER BY bid_count DESC LIMIT 10""",
            {},
        ),
        "Q3_시점슬라이스": (
            """MATCH (v:Vendor)-[r:AWARDED_TO]-(n:BidNotice)
               WHERE r.event_at <= date('2026-01-31')
               RETURN count(*) AS awards_until_jan""",
            {},
        ),
        "Q4_공급망_의존도_샘플": (
            """MATCH (v:Vendor)-[:AWARDED_TO]-(n:BidNotice)-[:ISSUED_BY]->(a:Agency)
               WITH v, count(DISTINCT a) AS unique_agencies, count(n) AS total_deals
               WHERE total_deals >= 2
               RETURN v.biz_no, v.vendor_name, unique_agencies, total_deals
               ORDER BY total_deals DESC LIMIT 10""",
            {},
        ),
        "Q5_최근30일_공고": (
            """MATCH (n:BidNotice)
               WHERE n.notice_date >= date() - duration('P30D')
               RETURN count(n) AS recent_notices""",
            {},
        ),
    }

    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    results = {}

    with driver.session() as session:
        for name, (cypher, params) in queries.items():
            start = time.time()
            try:
                r = session.run(cypher, **params)
                rows = r.data()
                elapsed = time.time() - start
                results[name] = {
                    "elapsed_ms": round(elapsed * 1000, 2),
                    "row_count": len(rows),
                    "pass": elapsed < 1.0,
                    "sample_row": rows[0] if rows else None,
                }
            except Exception as exc:
                results[name] = {
                    "error": str(exc)[:200],
                    "pass": False,
                }

    driver.close()
    return results


def main() -> int:
    print("=" * 60)
    print("Neo4j Phase R1 PoC 자동 검증")
    print("=" * 60)

    # 1. 연결
    if not check_neo4j_connection():
        return 1

    # 2. 스키마
    if not apply_schema():
        return 1

    # 3. 데이터 카운트
    counts = count_nodes()
    print(f"\nOK 현재 데이터:")
    for label, c in counts.items():
        print(f"  {label}: {c}")

    if counts.get("BidNotice", 0) == 0:
        print("\nWARN 데이터 없음. ETL 먼저 실행:")
        print("  python scripts/etl_to_neo4j.py --days 7")
        return 2

    # 4. 검증 쿼리
    print("\n검증 쿼리 5종 실행…")
    results = run_validation_queries()

    pass_count = 0
    fail_count = 0
    print("\n=" * 60)
    print(f"{'쿼리':<30} {'시간(ms)':>10} {'행수':>6} {'결과':>6}")
    print("-" * 60)
    for name, r in results.items():
        if "error" in r:
            print(f"{name:<30} {'ERROR':>10} {'-':>6} {'FAIL':>6}")
            print(f"  → {r['error'][:100]}")
            fail_count += 1
        else:
            status = "PASS" if r["pass"] else "SLOW"
            print(f"{name:<30} {r['elapsed_ms']:>10.2f} {r['row_count']:>6} {status:>6}")
            if r["pass"]:
                pass_count += 1
            else:
                fail_count += 1

    print("=" * 60)
    print(f"\n결과: {pass_count} PASS / {fail_count} FAIL/SLOW")

    if fail_count == 0:
        print("\nOK Phase R1 PoC 성공 — R2 동기화 ETL 단계로 진행 권장.")
        return 0
    else:
        print("\nWARN 일부 쿼리 1초 초과 또는 실패. 인덱스 추가 또는 쿼리 최적화 필요.")
        return 3


if __name__ == "__main__":
    sys.exit(main())
