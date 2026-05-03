# GovProcu — 나라장터 입찰 통합 콘솔

> 한국 정부·공공기관 입찰의 **전 생애주기**(사전규격 → 공고 → 개찰 → 낙찰 → 응찰업체 → NTS 검증 → 계약)를
> 공고번호·사업자번호·발주기관·계약번호 4개 키 1개로 한 화면에서 추적하는 MCP 서버 + Next.js 15 콘솔.

[![CI](https://github.com/lapiogga/govProcu/actions/workflows/ci.yml/badge.svg)](https://github.com/lapiogga/govProcu/actions/workflows/ci.yml)

---

## 핵심 가치

1. **★ trace_bid_lifecycle** — 공고번호 1개 → 6단계 통합 응답 (사전규격·공고·응찰업체·낙찰·NTS·계약)
2. **vendor_profile** — 사업자번호 1개 → NTS 진위 + 기간 내 입찰/응찰/개찰/낙찰 통계 + 동종업체 비교
3. **agency_procurement_history** — 발주기관 1개 → 발주 이력 + 각 공고별 낙찰업체 + 사정률 패턴
4. **Cross-Lookup (xyflow)** — 4개 키(공고/사업자/기관/계약) 자동 관계 그래프 시각화
5. **GraphRAG (Neo4j R4)** — 자연어 → Cypher → 그래프 응답 (`graph_natural_query`)

---

## 빠른 시작

### 옵션 A — Mock 모드 (UI 데모, MCP 서버 불필요)

```powershell
cd frontend
npm install
$env:MCP_MOCK_MODE = "true"
npm run dev
# http://localhost:3000 → 13 페이지 fixture 데이터로 즉시 확인
```

테마 토글 (헤더): **🎨 아이보리** / ☀ 라이트 / 🌙 다크 — `localStorage.govprocu.theme` 저장.

### 옵션 B — 실 MCP 서버

```powershell
# 1. 환경변수 (.env)
cp .env.example .env
# G2B 6 키 + NTS 키 + (선택) NEO4J/SMTP/SLACK 입력

# 2. MCP 서버 (65 도구)
pip install -e .
uvicorn app.server:app --port 8081

# 3. Frontend
cd frontend
cp .env.example .env.local
# ANTHROPIC_API_KEY (자연어 콘솔용) + MCP_BASE_URL=http://localhost:8081
npm install
npm run dev
```

### 옵션 C — Docker compose 통합 (MCP + Frontend + Redis + Neo4j)

```powershell
docker compose -f deploy/docker-compose.full.yml up -d
```

---

## 프론트 페이지 13종

| # | path | 도구 |
|---|------|------|
| 01 | `/` | 대시보드 (9 메뉴 카드 + 빠른 검색) |
| 02 | `/bids/trace?no=...` ★ | trace_bid_lifecycle 6단계 + 응찰업체 |
| 03 | `/search?q=...` | 자동 redirect (사업자번호/공고번호 패턴 인식) |
| 04 | `/bids?keyword=...` | search_bid_notices |
| 05 | `/vendors/{biz_no}` | vendor_profile + Tremor 차트 |
| 06 | `/agencies?name=...` | agency_procurement_history + 사정률 패턴 |
| 07 | `/analytics?type=용역` | industry_trend + market_share (Tremor) |
| 08 | `/lookup?mode=bid\|biz\|inst\|contract` | xyflow 4 키 그래프 |
| 09 | `/me` | 즐겨찾기 + 키워드 알림 구독 |
| 10 | `/qualification?...` | calc_qualification_score (조달청 표준) |
| 11 | `/prediction?...` | predict_bid_price + compare_bid_strategies |
| 12 | `/console` | AI SDK 자연어 콘솔 (Generative UI) |

### 링크 일관 정책

모든 페이지의 모든 컬럼에서 (`components/EntityLink.tsx` 일관 사용):
- 업체명·사업자번호 → `/vendors/{biz_no}` (`<VendorLink>`)
- 발주기관명 → `/agencies?name=...` (`<AgencyLink>`)
- 공고제목·공고번호 → `/bids/trace?no=...&ord=...` (`<BidLink>`)

---

## 65 MCP 도구 영역

| 영역 | 도구 수 | 대표 |
|------|--------|------|
| bid | 4 | search_bid_notices, get_bid_notice_detail, list_pre_specifications |
| award | 5 | search_awards, list_bid_openings, list_bid_participants |
| contract | 4 | get_contract_process, search_contracts |
| stats | 4 | get_procurement_stats, agency_procurement_volume |
| user | 1 | lookup_user_info |
| vendor | 7 | check_business_status (NTS), search_bids_by_vendor, V1~V4 |
| analytics | 6 | industry_trend, market_share, analyze_agency_price_pattern |
| workflow | 5 | **trace_bid_lifecycle ★**, vendor_profile, agency_procurement_history |
| lookup | 4 | lookup_by_bid_no, lookup_by_biz_no, lookup_by_inst_code |
| alerts | 5 | subscribe_keyword_alerts, daily_bid_digest |
| watchlist | 3 | add_to_watchlist, list_my_watchlist |
| qualification | 3 | calc_qualification_score |
| prediction | 3 | predict_bid_price, compare_bid_strategies |
| multi_agency | 3 | search_multi_agency_bids (G2B + LH/EX/KWater/Korail 어댑터) |
| graph | 4 | graph_query_path, find_collusion_clusters (Neo4j R3) |
| graphrag | 1 | graph_natural_query (LLM → Cypher, R4) |

상세 카탈로그: [docs/TOOLS-CATALOG.md](docs/TOOLS-CATALOG.md)

---

## Claude Desktop 연결

`claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "govprocu": {
      "url": "http://your-server:8081/mcp",
      "transport": "http",
      "headers": { "Authorization": "Bearer <MCP_API_TOKEN>" }
    }
  }
}
```

---

## 문서 인덱스

| 분류 | 문서 |
|------|------|
| 계획 | [REPLAN.md](docs/REPLAN.md) v3 도구 매트릭스 / [UI-PLAN.md](docs/UI-PLAN.md) v1.1 |
| 운영 | [DEPLOY.md](docs/DEPLOY.md) / [OPERATIONS.md](docs/OPERATIONS.md) / [NOTIFICATIONS.md](docs/NOTIFICATIONS.md) |
| 검증 | [SCREENSHOT-VERIFY.md](docs/SCREENSHOT-VERIFY.md) / [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| 카탈로그 | [TOOLS-CATALOG.md](docs/TOOLS-CATALOG.md) / [USER-GUIDE.md](docs/USER-GUIDE.md) |
| 캐시 | [CACHE-STRATEGY.md](docs/CACHE-STRATEGY.md) |
| 보안 | [AI-SDK-V6-MIGRATION.md](docs/AI-SDK-V6-MIGRATION.md) (보류 트랙) |
| R&D | [GRAPH-FEASIBILITY.md](docs/GRAPH-FEASIBILITY.md) / [AI-TREND-RESEARCH.md](docs/AI-TREND-RESEARCH.md) / [FRONTEND-TECH.md](docs/FRONTEND-TECH.md) / [MARKET-RESEARCH.md](docs/MARKET-RESEARCH.md) |
| 시계열 | [logs/WORK-LOG.md](logs/WORK-LOG.md) / [docs/PROMPTS-LOG.md](docs/PROMPTS-LOG.md) |

---

## 작업 관리 규칙

1. **WORK-LOG**: 모든 작업은 `logs/WORK-LOG.md` 시계열 기록
2. **PROMPTS-LOG**: 사용자 발화는 `docs/PROMPTS-LOG.md` 시계열 기록 (글로벌 규칙)
3. **자동 동기화**: 20분 주기 Cowork 스케줄이 push
4. **분기별 archive**: `python scripts/archive_logs.py --days 90` (90일+ 로그·audit 자동 압축)

---

## 라이선스

사내 사용 한정. 외부 배포 시 별도 협의.
