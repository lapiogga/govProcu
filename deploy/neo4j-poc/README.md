# Neo4j Phase R1 PoC

> 사용자 5/2 22번 R&D 트랙. docs/GRAPH-FEASIBILITY.md 기반 2주 검증.

## 가동

```powershell
# Windows
cd deploy/neo4j-poc
docker compose up -d
```

- Browser: http://localhost:7474
- Bolt: bolt://localhost:7687
- 계정: `neo4j` / `govprocu_poc`

## 스키마 적용

브라우저(7474)에서 `cypher/01_schema.cypher` 내용 붙여넣기 실행.
또는:

```powershell
docker exec -i govprocu-neo4j-poc cypher-shell -u neo4j -p govprocu_poc < cypher/01_schema.cypher
```

## ETL 실행 (G2B → Neo4j)

```powershell
# 의존성 추가
pip install neo4j

# 최근 7일 용역 입찰 ingest
python ../../scripts/etl_to_neo4j.py --days 7 --biz-type 용역
```

## 검증 쿼리

`cypher/02_validation_queries.cypher` 5종.
- Q1: 거래 네트워크 (발주기관 → 상위 거래 업체)
- Q2: 카르텔 의심 클러스터 (Louvain community detection)
- Q3: 시점 슬라이스 (2026-01-31 시점 기준)
- Q4: 공급망 의존도 (HHI 분포)
- Q5: 추천 (유사 패턴 신규 공고)

성공 기준: 모든 쿼리 1초 이내 응답.

## R2/R3 진행 권고

R1 검증 통과 시:
- R2: 일일 증분 ETL (cron + Apache Airflow)
- R3: MCP 도구 (`graph_query_path`, `find_collusion_clusters`)
- R4: GraphRAG (LLM 자연어 → Cypher)
