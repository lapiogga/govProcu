"""graph 영역 MCP 도구 — Neo4j 그래프 쿼리.

NEXT6-4 (Phase R3): R1 PoC 검증 통과 후 MCP 도구로 노출.
NEO4J_URI 환경변수 설정 시만 동작 (없으면 status='neo4j_not_configured').

도구:
- graph_query_path: 4 키 사이의 최단 경로 (예: 발주기관 → 공고 → 낙찰자)
- find_collusion_clusters: 카르텔 의심 community detection (Louvain)
- agency_vendor_network: 발주기관-업체 거래 네트워크 weight
- vendor_supply_concentration: 업체의 발주기관 의존도 (HHI)
"""
from __future__ import annotations
import os


def _neo4j_available() -> tuple[bool, str]:
    """Neo4j 연결 가능 여부."""
    if not os.getenv("NEO4J_URI"):
        return False, "NEO4J_URI 미설정"
    try:
        import neo4j  # noqa: F401
        return True, ""
    except ImportError:
        return False, "neo4j Python driver 미설치 — pip install -e .[graph]"


def _get_driver():
    from neo4j import GraphDatabase
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "govprocu_poc"),
        ),
    )


async def graph_query_path(
    start_type: str,
    start_value: str,
    end_type: str,
    end_value: str,
    max_hops: int = 4,
) -> dict:
    """4 키 노드 사이 최단 경로 탐색.

    Args:
        start_type / end_type: 'bid' / 'vendor' / 'agency' / 'contract'
        start_value / end_value: 해당 키 값 (공고번호, 사업자번호 등)
        max_hops: 최대 홉 수
    """
    ok, err = _neo4j_available()
    if not ok:
        return {"status": "neo4j_not_configured", "note": err}

    label_map = {"bid": "BidNotice", "vendor": "Vendor", "agency": "Agency", "contract": "Contract"}
    key_map = {"bid": "bid_notice_no", "vendor": "biz_no", "agency": "inst_code", "contract": "contract_no"}

    if start_type not in label_map or end_type not in label_map:
        return {"status": "invalid_type", "supported": list(label_map.keys())}

    cypher = f"""
    MATCH p = shortestPath(
        (a:{label_map[start_type]} {{{key_map[start_type]}: $start}})
        -[*..{max_hops}]-
        (b:{label_map[end_type]} {{{key_map[end_type]}: $end}})
    )
    RETURN [n IN nodes(p) | {{
        labels: labels(n),
        props: properties(n)
    }}] AS path_nodes,
    [r IN relationships(p) | type(r)] AS rel_types,
    length(p) AS hops
    """

    try:
        driver = _get_driver()
        with driver.session() as session:
            r = session.run(cypher, start=start_value, end=end_value)
            row = r.single()
        driver.close()
        if not row:
            return {
                "status": "no_path",
                "start": [start_type, start_value],
                "end": [end_type, end_value],
                "max_hops": max_hops,
            }
        return {
            "status": "found",
            "hops": row["hops"],
            "rel_types": row["rel_types"],
            "path_nodes": row["path_nodes"],
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:200]}


async def find_collusion_clusters(
    min_community_size: int = 3,
    min_shared_bids: int = 2,
) -> dict:
    """카르텔 의심 community detection (Louvain).

    같은 입찰에 반복 응찰한 업체 그룹을 community로 식별.
    """
    ok, err = _neo4j_available()
    if not ok:
        return {"status": "neo4j_not_configured", "note": err}

    cypher = """
    CALL gds.graph.project.cypher(
      'collusion-' + toString(timestamp()),
      'MATCH (v:Vendor) RETURN id(v) AS id',
      'MATCH (v1:Vendor)-[:PARTICIPATED_IN]->(n)<-[:PARTICIPATED_IN]-(v2:Vendor)
       WHERE id(v1) < id(v2)
       WITH v1, v2, count(n) AS shared
       WHERE shared >= $min_shared
       RETURN id(v1) AS source, id(v2) AS target, shared AS weight',
      {parameters: {min_shared: $min_shared}}
    )
    YIELD graphName
    CALL gds.louvain.stream(graphName)
    YIELD nodeId, communityId
    WITH graphName, communityId, collect({
        biz_no: gds.util.asNode(nodeId).biz_no,
        name: gds.util.asNode(nodeId).vendor_name
    }) AS members
    WHERE size(members) >= $min_size
    CALL gds.graph.drop(graphName) YIELD graphName AS dropped
    RETURN communityId, size(members) AS member_count, members
    ORDER BY member_count DESC LIMIT 10
    """

    try:
        driver = _get_driver()
        with driver.session() as session:
            rows = session.run(
                cypher,
                min_shared=min_shared_bids,
                min_size=min_community_size,
            ).data()
        driver.close()
        return {
            "status": "ok",
            "min_community_size": min_community_size,
            "min_shared_bids": min_shared_bids,
            "communities": rows,
            "note": "의심 신호일 뿐 — 컨소시엄·정상 패턴 가능. 도메인 전문가 검토 필요.",
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:200]}


async def agency_vendor_network(
    inst_name: str,
    top_n: int = 20,
) -> dict:
    """발주기관-업체 거래 네트워크 weight."""
    ok, err = _neo4j_available()
    if not ok:
        return {"status": "neo4j_not_configured", "note": err}

    cypher = """
    MATCH (a:Agency {inst_name: $inst_name})<-[:ISSUED_BY]-(n:BidNotice)
          -[r:AWARDED_TO]->(v:Vendor)
    RETURN v.biz_no AS biz_no,
           v.vendor_name AS vendor_name,
           count(n) AS deal_count,
           sum(coalesce(r.amount, 0)) AS total_amount
    ORDER BY total_amount DESC LIMIT $top_n
    """

    try:
        driver = _get_driver()
        with driver.session() as session:
            rows = session.run(cypher, inst_name=inst_name, top_n=top_n).data()
        driver.close()
        return {
            "inst_name": inst_name,
            "top_vendors": rows,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:200]}


async def vendor_supply_concentration(biz_no: str) -> dict:
    """한 업체의 발주기관 의존도 (HHI 지수).

    HHI = sum(share_pct ** 2). 0~10000 범위. 5000+ = 단일 의존 위험.
    """
    ok, err = _neo4j_available()
    if not ok:
        return {"status": "neo4j_not_configured", "note": err}

    cypher = """
    MATCH (v:Vendor {biz_no: $biz_no})<-[:AWARDED_TO]-(n:BidNotice)-[:ISSUED_BY]->(a:Agency)
    WITH v, a, count(n) AS deal_count, sum(coalesce(n.base_amount, 0)) AS deal_amount
    WITH v, collect({
        inst_name: a.inst_name,
        deal_count: deal_count,
        deal_amount: deal_amount
    }) AS deals,
    sum(deal_amount) AS total
    WHERE total > 0
    RETURN v.biz_no AS biz_no,
           v.vendor_name AS vendor_name,
           total,
           [d IN deals | {
             inst: d.inst_name,
             share_pct: round(d.deal_amount * 100.0 / total, 2),
             deal_count: d.deal_count
           }] AS distribution
    """

    try:
        driver = _get_driver()
        with driver.session() as session:
            row = session.run(cypher, biz_no=biz_no).single()
        driver.close()
        if not row:
            return {"status": "no_data", "biz_no": biz_no}

        dist = row["distribution"]
        hhi = sum(d["share_pct"] ** 2 for d in dist)
        risk_level = (
            "매우 높음 (단일 기관 의존)" if hhi >= 5000
            else "높음" if hhi >= 2500
            else "중간" if hhi >= 1500
            else "분산 양호"
        )
        return {
            "biz_no": row["biz_no"],
            "vendor_name": row["vendor_name"],
            "total_amount": row["total"],
            "distribution": dist,
            "hhi": round(hhi, 2),
            "risk_level": risk_level,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:200]}
