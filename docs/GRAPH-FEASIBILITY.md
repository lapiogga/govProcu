# GovProcu 그래프DB / 온톨로지 적용 가능성 분석 보고서

> 작성: 2026-05-02 01:08 KST
> Graph DB Feasibility R&D Team (sub-agent)
> 사용자 5/2 01:04 KST 통찰 응답

---

## 결론 (요약)

**적용 가능성: ★★★★ (적극 권장).** 1순위 후보 = **Neo4j Community Edition**. 4개 relational key의 그래프 매핑 친화도가 매우 높고, 카르텔 탐지·공급망 분석·LLM 자연어 질의 같은 차세대 기능이 자연스럽게 따라온다. **PoC: 2주 내 단일 컨테이너 검증**, 본 도입 결정은 R1 결과 후. 시간성·키 정규화·NTS 캐싱 3개 난점 R2 선결 필수.

---

## 1. 그래프 데이터 모델

### 노드 (8종)

| 노드 | 1차 키 | 핵심 속성 |
|------|--------|----------|
| `BidNotice` | `bid_notice_no + bid_ord` | bid_title, notice_date, base_amt, region |
| `Contract` | `contract_no` | contract_amt, contract_date, contract_type |
| `Agency` | `inst_code` | inst_name, inst_type, region |
| `Vendor` | `vendor_biz_no` | vendor_name, biz_status, capital, region |
| `PreSpec` | `pre_spec_no` | spec_title, open_date, deadline |
| `Award` | `bid_notice_no + bid_ord` | award_amt, award_rate, awarded_date |
| `BidParticipation` | (notice, vendor) | bid_amt, bid_rate, bid_rank |
| `ContractChange` | (contract, change_seq) | change_type, change_amt, change_date |

### 관계

```
(Agency) ──ISSUED_PRESPEC──► (PreSpec) ──BECAME_NOTICE──► (BidNotice)
(BidNotice) ──ISSUED_BY──► (Agency)
(Vendor) ──PARTICIPATED_IN──► (BidNotice) [props: bid_amt, rank]
(BidNotice) ──HAS_AWARD──► (Award) ──AWARDED_TO──► (Vendor)
(BidNotice) ──CONTRACTED_AS──► (Contract) ──SIGNED_WITH──► (Vendor)
(Contract) ──MODIFIED_BY──► (ContractChange)
```

### 다이어그램

```
   ┌──────────┐  ISSUED_PRESPEC   ┌─────────┐  BECAME_NOTICE  ┌────────────┐
   │  Agency  │───────────────────►│ PreSpec │────────────────►│ BidNotice  │
   └──────────┘                    └─────────┘                 └─────┬──────┘
        ▲                                                            │
        │ ISSUED_BY                                                  │ HAS_AWARD
        └────────────────────────────────────────────────────────────┤
                                                                     ▼
   ┌──────────┐  PARTICIPATED_IN  ┌─────────┐  AWARDED_TO  ┌──────────────┐
   │  Vendor  │◄──────────────────│         │◄─────────────│    Award     │
   └────┬─────┘                   │BidNotice│              └──────────────┘
        │ SIGNED_WITH             └────┬────┘
        ▼                              │ CONTRACTED_AS
   ┌──────────┐                        ▼
   │ Contract │◄───────────────────────┘
   └────┬─────┘  MODIFIED_BY
        ▼
   ┌────────────────┐
   │ ContractChange │
   └────────────────┘
```

---

## 2. 그래프DB 후보 비교

| 후보 | 라이선스 | 특징 | 한국어 | Python | 적합도 |
|------|---------|------|-------|--------|--------|
| **Neo4j Community** ⭐ | GPLv3/상용 | Cypher, GDS 라이브러리, GraphRAG 지원 | OK (UTF-8) | neo4j-driver (공식) | ★★★★★ |
| **ArangoDB** | Apache 2.0 | 멀티모델 (graph+doc+kv) | OK | python-arango | ★★★★ |
| **Memgraph** | BSL | 인메모리, Cypher 호환, 실시간 | OK | mgclient/neo4j-driver | ★★★ |
| **NebulaGraph** | Apache 2.0 | 분산 처리, 수십억 엣지 | OK | nebula3-python | ★★★ |
| **AWS Neptune** | 상용 (관리형) | Gremlin/SPARQL, 운영 부담 적음 | OK | boto3 | ★★ (운영비) |
| **NetworkX** | BSD | Python in-memory | N/A | 기본 내장 | ★★ (PoC만) |

**1순위: Neo4j Community.** Cypher 패턴 매칭이 직관적, GDS의 Louvain/community detection 내장, GraphRAG Python 패키지로 LLM→Cypher 자동 변환.

---

## 3. 기술적 문제점

### (1) 데이터 동기화 (ETL)
G2B는 pull 모델 → 변경 감지 어려움. 일일 증분 + 주간 풀 리컨실리에이션 이중 배치. UNWIND+MERGE로 idempotent ingest. 응답 절단·인코딩(EUC-KR) 정규화 레이어 필수.

### (2) 키 정규화
사업자번호 하이픈/공백, 기관명 vs 기관코드 매핑 누락 다수. 해결: ingest layer zod 강제, 기관 alias 테이블, NULL 키는 `:Unresolved` 라벨.

### (3) 시간성 (Temporal Graph)
사전규격→공고→개찰→낙찰→계약 시간 흐름 핵심. Neo4j 네이티브 Date/DateTime 활용 + `valid_from`/`valid_to`/`event_at` 일관 부여. 시점 슬라이스 쿼리 패턴:

```python
session.run("""
  MERGE (v:Vendor {biz_no:$biz})
  MERGE (n:BidNotice {notice_no:$nno, ord:$ord})
  MERGE (v)-[r:PARTICIPATED_IN]->(n)
  SET r.bid_amt=$amt, r.event_at=$ts, r.valid_from=$ts
""", biz=biz, nno=nno, ord=ord, amt=amt, ts=DateTime.now())
```

### (4) 스케일
연 ~10만 공고 × 응찰 7개 = 100만 노드/700만 엣지/년. 5년 누적 5천만 엣지 → Neo4j Community 64GB RAM 단일 인스턴스 충분. 분산 필요시 Enterprise/NebulaGraph 재검토.

### (5) NTS 동기 호출 성능
쿼리 시 동기 호출하면 분 단위 지연. 해결: nightly batch로 `Vendor.biz_status`/`status_checked_at` 캐시, TTL 30일 만료 노드만 재조회.

### (6) 카르텔 탐지의 라벨링
패턴 발견은 가능하나 "담합" 판정은 공정위/감사원 영역. **시스템은 "의심 신호(suspicion score)"만 제공**, 최종 판단 사용자 위임 → 법적 책임 회피.

---

## 4. 응용 시나리오

- **거래 네트워크 시각화**: Agency-Vendor 양방향 + 거래 빈도/누적 금액 weight. Neo4j Bloom 또는 자체 D3.
- **카르텔 위험 탐지**: GDS `gds.louvain.stream` community detection + 같은 community 반복 응찰 패턴(`COUNT(*) >= θ`). 컨소시엄 화이트리스트.
- **입찰 추천 (GraphRAG hybrid)**: Vendor 낙찰 패턴 vector embedding → 신규 공고 cosine similarity. Neo4j 5.x vector index + traversal hybrid retrieval.
- **공급망 위험 평가**: 발주기관 단일 업체 50%+ 의존 (HHI), 업체 단일 기관 80%+ 매출 — "병목/특혜" 플래깅.
- **시간적 트렌드**: 월별 Agency-Vendor 엣지 weight 변화 → "특정 업체-기관 거래 6개월 급증" 자동 감지.

---

## 5. 단계별 추진

| Phase | 기간 | 내용 |
|-------|------|------|
| **R1 PoC** | 1~2주 | Neo4j Community Docker + 1주일치 데이터(~1000공고) 적재. Cypher 5종 검증. |
| **R2 ETL** | 2~3주 | 키 정규화 + 일일 증분 ETL (cron/Airflow). NULL 키, NTS 캐시. |
| **R3 MCP 통합** | 1~2주 | 신규 도구: `graph_query_path`, `find_collusion_clusters`, `agency_vendor_network`, `vendor_recommend_notices`. |
| **R4 GraphRAG** | Optional | Neo4j GraphRAG → LLM 자연어→Cypher. "○○건설이 최근 1년간 받은 계약을 발주기관별로 보여줘". |

---

## 6. 출처

- Neo4j Python Driver (context7: `/neo4j/neo4j-python-driver`)
- Neo4j GraphRAG for Python (context7: `/neo4j/neo4j-graphrag-python`)
- Neo4j 공식 (context7: `/websites/neo4j`) — GDS, vector hybrid retrieval
