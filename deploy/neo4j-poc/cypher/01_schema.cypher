// GovProcu Graph Schema (Phase R1 PoC)
// Reference: docs/GRAPH-FEASIBILITY.md
//
// 노드 (8): BidNotice, Contract, Agency, Vendor, PreSpec, Award, BidParticipation, ContractChange
// 4 핵심 키:
//   - bid_notice_no + bid_ord (BidNotice)
//   - contract_no              (Contract)
//   - inst_code                (Agency)
//   - vendor_biz_no            (Vendor)

// === Constraints (1차 키 유일성) ===
CREATE CONSTRAINT bid_notice_id IF NOT EXISTS
  FOR (n:BidNotice) REQUIRE (n.bid_notice_no, n.bid_ord) IS UNIQUE;

CREATE CONSTRAINT contract_id IF NOT EXISTS
  FOR (c:Contract) REQUIRE c.contract_no IS UNIQUE;

CREATE CONSTRAINT agency_id IF NOT EXISTS
  FOR (a:Agency) REQUIRE a.inst_code IS UNIQUE;

CREATE CONSTRAINT vendor_id IF NOT EXISTS
  FOR (v:Vendor) REQUIRE v.biz_no IS UNIQUE;

CREATE CONSTRAINT prespec_id IF NOT EXISTS
  FOR (p:PreSpec) REQUIRE (p.bid_notice_no, p.bid_ord) IS UNIQUE;

// === 보조 인덱스 ===
CREATE INDEX bid_notice_inst IF NOT EXISTS
  FOR (n:BidNotice) ON (n.inst_code);

CREATE INDEX bid_notice_date IF NOT EXISTS
  FOR (n:BidNotice) ON (n.notice_date);

CREATE INDEX agency_name IF NOT EXISTS
  FOR (a:Agency) ON (a.inst_name);

CREATE INDEX vendor_name IF NOT EXISTS
  FOR (v:Vendor) ON (v.vendor_name);

// === Vector index (향후 GraphRAG 용) ===
// 공고 제목 + 사양 임베딩 — embedding dim은 모델에 맞춰 조정 (예: 1024 = BGE-M3)
// CREATE VECTOR INDEX bid_notice_embedding IF NOT EXISTS
//   FOR (n:BidNotice) ON (n.embedding)
//   OPTIONS { indexConfig: {
//     `vector.dimensions`: 1024,
//     `vector.similarity_function`: 'cosine'
//   }};
