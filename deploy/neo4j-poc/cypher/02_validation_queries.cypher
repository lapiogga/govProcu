// Phase R1 검증 쿼리 5종 (docs/GRAPH-FEASIBILITY.md 권장)
// PoC 성공 기준: 5개 쿼리가 모두 1초 이내 응답
//
// 사용법:
//   docker exec -it govprocu-neo4j-poc cypher-shell -u neo4j -p govprocu_poc -f /var/lib/neo4j/import/02_validation_queries.cypher

// ─────────────────────────────────────────────────────────────
// Q1: 거래 네트워크 시각화
// "한 발주기관과 거래 빈도 상위 10개 업체"
// ─────────────────────────────────────────────────────────────
MATCH (a:Agency {inst_name: $inst_name})<-[:ISSUED_BY]-(n:BidNotice)
      -[r:AWARDED_TO]->(v:Vendor)
RETURN v.biz_no AS vendor_biz_no,
       v.vendor_name AS vendor_name,
       count(n) AS award_count,
       sum(r.amount) AS total_amount
ORDER BY total_amount DESC LIMIT 10;

// ─────────────────────────────────────────────────────────────
// Q2: 카르텔 의심 클러스터 (community detection)
// 같은 입찰들에 반복 응찰한 업체 community
// ─────────────────────────────────────────────────────────────
CALL gds.graph.project.cypher(
  'collusion-graph',
  'MATCH (v:Vendor) RETURN id(v) AS id',
  'MATCH (v1:Vendor)-[:PARTICIPATED_IN]->(n)<-[:PARTICIPATED_IN]-(v2:Vendor)
   WHERE id(v1) < id(v2)
   RETURN id(v1) AS source, id(v2) AS target, count(n) AS weight'
)
YIELD graphName;

CALL gds.louvain.stream('collusion-graph')
YIELD nodeId, communityId
WITH communityId, collect(gds.util.asNode(nodeId).biz_no) AS members
WHERE size(members) >= 3
RETURN communityId, size(members) AS member_count, members
ORDER BY member_count DESC LIMIT 5;

CALL gds.graph.drop('collusion-graph') YIELD graphName;

// ─────────────────────────────────────────────────────────────
// Q3: 시점 슬라이스 — 2026년 1월 시점의 거래 네트워크
// ─────────────────────────────────────────────────────────────
MATCH (v:Vendor)-[r:AWARDED_TO]-(n:BidNotice)
WHERE r.event_at <= date('2026-01-31')
  AND (r.valid_to IS NULL OR r.valid_to > date('2026-01-31'))
RETURN v.biz_no, v.vendor_name, count(n) AS awards_until_jan
ORDER BY awards_until_jan DESC LIMIT 20;

// ─────────────────────────────────────────────────────────────
// Q4: 공급망 의존도 — 한 업체의 발주기관 분포 HHI
// ─────────────────────────────────────────────────────────────
MATCH (v:Vendor {biz_no: $biz_no})-[:AWARDED_TO]-(n:BidNotice)-[:ISSUED_BY]->(a:Agency)
WITH v, a, count(n) AS deal_count, sum(n.award_amount) AS deal_amount
WITH v, collect({inst: a.inst_name, count: deal_count, amount: deal_amount}) AS deals,
     sum(deal_amount) AS total
RETURN v.biz_no,
       v.vendor_name,
       size(deals) AS unique_agencies,
       total,
       [d IN deals | {
         inst: d.inst,
         share_pct: round(d.amount * 100.0 / total, 2)
       }] AS agency_shares
ORDER BY agency_shares[0].share_pct DESC;

// ─────────────────────────────────────────────────────────────
// Q5: 추천 — 유사한 낙찰 패턴의 업체가 수주한 신규 공고
// ─────────────────────────────────────────────────────────────
MATCH (v:Vendor {biz_no: $biz_no})-[:AWARDED_TO]-(past:BidNotice)
MATCH (past)-[:ISSUED_BY]->(a:Agency)<-[:ISSUED_BY]-(new:BidNotice)
WHERE new.notice_date >= date() - duration('P30D')
  AND NOT (v)-[:PARTICIPATED_IN]->(new)
RETURN DISTINCT new.bid_notice_no AS bid_notice_no,
       new.bid_title AS title,
       a.inst_name AS agency,
       new.base_amount AS base_amount
LIMIT 20;
