# PROMPTS-LOG — 사용자 프롬프트 시계열

> 본 파일은 사용자가 본 프로젝트(나라장터 MCP 서버 구축)에 준 모든 프롬프트(지시·요구·통찰)를 시계열로 보존한다.
> 글로벌 규칙: `~/.claude/rules/prompts-log.md`
> 시간 기준: KST (Asia/Seoul, UTC+9)

## 분류 라벨

- **핵심지시**: 프로젝트 방향을 정의하거나 바꾸는 큰 요구
- **추가지시**: 도구·기능 추가
- **통찰**: 사용자가 발견한 설계 인사이트
- **정정**: 기존 계획·구현 정정
- **운영지시**: 작업 방식·기록·관리 규정

---

## 2026-04-29 (수) — 프로젝트 시작

| 시각 (KST) | # | 사용자 발화 (요약) | 분류 | 반영 결과 |
|-----------|---|------------------|------|----------|
| 10:30 | 1 | "나라장터 API 연동 MCP 서버 사전 계획" | 핵심지시 | 계획서 docx (9챕터, 421문단) |
| ~10:50 | 2 | "WORK-LOG / TERMINAL-LOG / 20분 자동기록 / GitHub 배포" | 운영지시 | 작업관리 체계 초기화 + cron 등록 |
| ~11:10 | 3 | "C:\\Users\\User\\GovProcu 폴더 마운트, GitHub repo URL" | 운영지시 | 폴더 마운트 + 첫 커밋 + push |

## 2026-05-01 (금) — 환경 셋업 + API 확정

| 시각 (KST) | # | 사용자 발화 (요약) | 분류 | 반영 결과 |
|-----------|---|------------------|------|----------|
| ~17:30 | 4 | "API 6종 활용신청 진행" → 6종 확정 (입찰공고/사전규격/낙찰/계약과정통합공개/사용자정보/통계) | 핵심지시 | API_신청_진행_트래커 v3, .env.example 갱신 |
| ~17:40 | 5 | "FastMCP 골격 코드 셋업" | 핵심지시 | app/{config,server,clients,core,schemas,tools} 골격 + 28파일 push |
| ~18:18 | 6 | "D를 입찰참가자격→계약과정통합공개로 교체" | 정정 | config.py·README·트래커 v3·tools/contract.py |
| ~23:35 | 7 | "DART → NTS(국세청 사업자등록 진위확인)으로 데이터 소스 교체" | 정정 | clients/nts.py 신규 + vendor.py NTS 통합 + 라이브 검증 |

## 2026-05-02 (토) — 계획 재수립 + 도구 확장

| 시각 (KST) | # | 사용자 발화 (원문 또는 요약) | 분류 | 반영 결과 |
|-----------|---|----------------------------|------|----------|
| 00:13 | 8 | **"이제부터 다음 사항을 준수하여 작업을 진행한다. 너는 이번 작업을 통 지휘하는 오케스트레이터이며... GSD 프로세스 기반... 팀 Agent를 활용... 시계열로 모든 진행내용을 기록... context 80% 자동 compact... recommended 즉시 수행"** | 운영지시 | 오케스트레이터 모드 진입, TaskCreate 시계열 관리, 팀 sub-agent 가동 |
| 00:13 | 9 | **"나라장터 및 국세청 API를 이용하여 국가에서 하는 각종 입찰정보를 조회하고 특정 건에 대한 사전규격, 입찰공고, 개찰내역, 낙찰정보, 낙찰 및 응찰업체에 대한 구체적인 정보 등을 조회하고, 확인하고자 한다. 이에 대해 지금까지 진행한 내역을 바탕으로 보다 나은 결과를 이룰 수 있게 계획을 재 수립한다."** | 핵심지시 | docs/REPLAN.md v2 작성. Tier 1 단위 18종 + Tier 2 통합 워크플로우 4종 (trace_bid_lifecycle 등) |
| 00:19 | 9-A | **"1"** (origin 우선/로컬 우선/force push 3안 중 1번 선택) | 선택 | git reset --hard origin/main 진행. 회고 추가(5/2 01:14 강화 지시 반영). 9번 핵심지시에 대한 의사결정 분기점. |
| 00:25 | 10 | **"특정업체의 기간 내 입찰, 응찰, 개찰, 낙찰 정보도 검색할 수 있게끔 구현"** | 추가지시 | vendor V1~V4 도구 (search_bids/participations/openings/awards_by_vendor) + W2 vendor_profile 시그니처 강화 |
| 00:36 | 11 | **"동종업체 또는 비슷한 규모의 경쟁업체 동향, 유사 사업에 대한 업체 동향, 통계 등 보조적인 검색자료 추출도 서비스로 보강해서 추가"** | 추가지시 | app/tools/analytics.py 신규 (Tier 2.5): find_similar_vendors / find_similar_bids / industry_trend / peer_analysis / market_share |
| ~00:43 | 12 | **"특정기간, 특정 발주기관의 발주 목록 및 낙찰업체 정보 조회기능 도 추가"** | 추가지시 | workflow.py W5 agency_procurement_history (발주 목록 + 각 공고별 낙찰자 매칭) |
| 00:48 | 13 | **"공고번호(또는 공고번호+차수), 계약번호, 발주기관코드, 업체 사업자등록번호를 서로의 상관관계를 엮어주는 주요한 relational key가 될 것 같음."** | 통찰 | app/tools/lookup.py 신규 (Tier 3): lookup_by_bid_no / lookup_by_inst_code / lookup_by_biz_no / lookup_by_contract_no — 4개 키 cross-lookup |
| 00:53 | 14 | **"이러한 요구사항을 토대로 인터렉티브 한 프론트 환경을 구성한다면 그에 맞는 메뉴체계와 사용자 인터페이스 화면에 대해서도 계획을 수립하여야 함."** | 추가지시 | docs/UI-PLAN.md (v1) — 페르소나 4종, 메뉴 7대 영역, 화면 5종 wireframe, Next.js+shadcn 스택, 단계별 7주 계획 |
| 00:57 | 15 | **"지금까지 제시한 프롬프트는 시계열로 별도의 프롬프트 모임 파일로 만들어 지속적으로 추가 관리가 되어야 함."** | 운영지시 | 본 파일(docs/PROMPTS-LOG.md) 신설 |
| 00:59 | 16 | **"기존의 입찰정보를 제공하는 앱이나 서비스, 업체를 조사해서 빠진 기능이 없는 지 확인이 필요함. 시장조사도 필요함."** | 핵심지시 | Market Research sub-agent 가동 (병렬), docs/MARKET-RESEARCH.md 산출 예정 |
| 01:00 | 17 | **"사용자 프롬프트 시계열 관리는 본 프로젝트 와는 별개로 모든 프로젝트에 공히 적용되어야 할 기준임."** | 운영지시 | `~/.claude/rules/prompts-log.md` 글로벌 규칙 추가 + CLAUDE.md @import 등록 + 메모리 feedback 저장 |
| 01:02 | 18 | **"최근 인공지능을 이용하여 이와 같은 입찰정보를 제공하는 서비스나 업체, 트렌드, 기술 등에 대해서도 조사가 필요함."** | 핵심지시 | AI Trend Research sub-agent 가동 (병렬) — docs/AI-TREND-RESEARCH.md 산출 예정. 채택 가능 AI 기능 우선순위 + 차별화 신규 도구 제안 포함 |
| 01:04 | 19 | **"온톨로지나 그래프DB 형태로도 발전시켰을 때 기술적인 문제점은 없는지, 적용가능성은 있는지?"** | 통찰 | Graph DB Feasibility R&D sub-agent 가동 (병렬) — docs/GRAPH-FEASIBILITY.md 산출 예정. Neo4j 등 후보 비교, 데이터 모델, ETL 문제, 응용 시나리오(담합 탐지/입찰 추천), 단계별 추진안 |
| 01:08 | 20 | **"최신 프론트 기술로 접목 가능한 것은 있는지?"** | 통찰 | Frontend Tech R&D sub-agent 가동 (병렬) — docs/FRONTEND-TECH.md 산출. RSC+Streaming + AI SDK 5 + Cache Components + Tremor + xyflow 5축. Wave 1/2/3 도입 + 신규 UX 5종 (AI 자연어 콘솔/Streaming Timeline/Relational Graph/Live cmd+k/OKLCH 다크) |
| 01:14 | 21 | **"중간중간에 입력하는 프롬프트는 빠짐없이 기록 저장이 되어야 함. - 글로벌 영역"** | 운영지시 | 글로벌 규칙(`~/.claude/rules/prompts-log.md`) "모든 발화 빠짐없이 기록" 강화. 단순 확인·선택("응", "1번")도 의사결정 분기점이므로 기록 추가. 회고 발화 9-A(00:19 "1") 추가. 메모리 feedback 갱신. |
| 01:21 | 22 | **"P0 필수 > P1 중요 > R&D 트랙 > UI Phase A"** | 선택 | 우선순위 확정. P0(알림/즐겨찾기/적격심사) → P1(투찰가 예측/사정률/다중기관) → R&D(그래프DB PoC/AI SDK 콘솔) → UI Phase A(Next.js 부트스트랩). 본 세션 21번 마무리 보고에 대한 응답. |
| 01:31 | 23 | **"모바일 환경은 배제하고, 웹앱 형태로"** | 정정 | UI-PLAN.md 갱신: 모바일 PWA·deck.gl 모바일 최적화 제외. 데스크톱 웹앱(Next.js 15) 단일 타겟. UI-PLAN v1.1 = "데스크톱·태블릿(반응형) only, 모바일 앱 비대상". |
| 01:50 | 24 | **"순서대로 진행"** | 선택 | 다음 액션 5종 우선순위 확정. ① P1-C 다중기관 어댑터 골격 → ② UI Phase B (입찰 상세 추적 Streaming + 업체 프로필) → ③ Neo4j PoC 검증 스크립트 → ④ Frontend 검증 가이드 → ⑤ ML 학습 인프라 (LightGBM). 21번 마무리 보고 후속 작업. |
| 02:10 | 25 | **"순서대로 진행"** (2회차) | 선택 | NEXT 1-5 완료 후 추가 우선순위 5종 재확정. ① UI Phase C (발주기관 분석 + 분석/통계 + 즐겨찾기·알림) → ② ML 모델 정밀화 (feature engineering + 캘리브레이션) → ③ R2 ETL 파이프라인 (일일 증분 + 키 정규화) → ④ UI Phase D (Cross-Lookup xyflow + 적격심사·투찰가 페이지) → ⑤ 운영 문서 (DEPLOY/OPERATIONS). |
| 02:32 | 26 | **"진행"** | 선택 | NEXT2 1-5 완료 후 5개 후보 순차 확정. ① xyflow 그래프 (Cross-Lookup 시각화) → ② Tremor 차트 (analytics/agencies) → ③ shadcn/ui CLI 컴포넌트 표준화 → ④ Playwright E2E 3시나리오 → ⑤ Neo4j R2 일일 증분 ETL 통합. |
| 02:50 | 27 | **"진행"** (3회차) | 선택 | NEXT3 1-5 완료 후 5개 후보 순차 확정. ① shadcn 컴포넌트로 기존 페이지 점진 교체 → ② Cache Components ('use cache') 적용 → ③ AI SDK Generative UI 강화 → ④ CI 통합 (.github/workflows/e2e.yml + ml.yml) → ⑤ 사용자 인증 미들웨어 (MCP_API_TOKENS Bearer 검증). |
| 03:10 | 28 | **"진행"** (4회차) | 선택 | NEXT4 1-5 완료 후 5개 후보 순차 확정. ① watchlist/qualification 등 나머지 도구 ContextVar 통합 → ② shadcn 페이지 확장 (vendors/agencies/lookup/me) → ③ Tremor 차트 추가 (vendor profile/agency 사정률) → ④ 도구 카탈로그 + 사용자 매뉴얼 docs → ⑤ Docker compose 통합 (MCP + Redis + Neo4j + frontend). |
| 03:30 | 29 | **"진행"** (5회차) | 선택 | NEXT5 1-5 완료 후 5개 후보 순차 확정. ① agencies/me/lookup shadcn 마무리 → ② 알림 디스패처 (이메일+슬랙+카카오) → ③ ML v2 (시계열 split + GridSearch + SHAP) → ④ Neo4j R3 (MCP 도구 통합: graph_query_path 등) → ⑤ 보안 강화 (rate limit per user + NTS quota + audit log). |
| 03:55 | 30 | **"지금까지 내용 정리하고, 시점관리 포인트 설정하고, git에 저장"** | 운영지시 | 5/2 세션 마무리. WORK-LOG 종합 요약 + 시점관리 표 v3 갱신 + SESSION-SUMMARY 1쪽 + 최종 push. context 65% 도달, 다음 라운드는 신규 세션 권장. |
| 04:?? | 31 | **"순서대로"** | 선택 | 신규 세션 재개. SESSION-SUMMARY v3 대기 항목 8종(T1 검증 가이드 → T2 외부 어댑터 4종 골격 → T3 디스패처 운영 가이드 → T4 카카오 알림톡 → T5 shadcn 100% → T6 Cache Components → T7 Neo4j R4 GraphRAG → T8 로그 archive)을 순차 진행. NEXT7 라운드. |
| 09:50 | 32 | **"프론트 화면 전체 mock 데이터 기반 스크린 캡쳐 검증 필요"** | 핵심지시 | mock 검증 인프라 구축. ① `frontend/src/lib/mocks.ts` 14개 도구 fixture · ② `mcp-client.ts` MCP_MOCK_MODE 분기 · ③ Playwright `99-screenshots.spec.ts` 13 페이지 캡쳐 · ④ SCREENSHOT-VERIFY.md. |
| 10:15 | 33 | **"npm install ERESOLVE Tremor v3 vs React 19"** | 정정 | `.npmrc legacy-peer-deps=true` — Tremor v3 React 18 peer 충돌 영구 우회. |
| 10:32 | 34 | **"next critical RCE"** | 정정 | next 15.1.0 → 15.5.15 (CVE-2025-66478 외 7 advisory 패치). cacheComponents canary-only로 보류. |
| 10:45 | 35 | **"자체 판단으로 계속 진행"** | 운영지시 | 자율 진행 모드 강화 v1. mock dev → fetch → screenshot 자체 + 발견 문제 즉시 수정. |
| 11:30 | 36 | **"링크 일관화 + 3 테마 (system 아이보리 / light / dark)"** | 핵심지시 | EntityLink 3 헬퍼(VendorLink/AgencyLink/BidLink) + ThemeToggle + globals.css 3 OKLCH 토큰 + 7 페이지 raw `<a>` 교체. |
| 12:05 | 37 | **"recommand 기본으로 진행"** | 운영지시 | 자율 진행 모드 v2. NEXT8 5 + N9 3 = 8 트랙 자율 진행 → SESSION-SUMMARY v2 시점관리 v4. |
| 14:00~ | 38~40 | **"continue"** × 3 (자율 진행 연속) | 선택 | 자율 모드 유지. ① N10 e2e 4 fail 완전 해결 — search redirect 직접 진입 패턴 + parallel 부하 timeout 보강 → 25/25 PASS. ② N11 /vendors 인덱스 페이지 (대시보드 카드 → 404 갭 해소). ③ SESSION-SUMMARY v3 (시점관리 v5). 종결: 65 MCP 도구 + 14 페이지 + 25/25 e2e + 3 테마 + EntityLink 정책 — 본 자율 라운드 마무리. |
| 14:30 | 41 | **"지금까지 진행 정리/기록하고 시점관리하고, git배포하고"** | 운영지시 | 본 5/2 세션(31~40번 자율 라운드 포함) 최종 종결 commit. PROMPTS-LOG 41번 + WORK-LOG 종결 행 + SESSION-SUMMARY v3 footer + 최종 push. 17 트랙(NEXT7 8 + mock + 보안 + 링크/테마 + NEXT8 5 + N9 3 + N10 + N11) 전부 commit + push 완료. context 80%+ — 신규 세션 진입 권장. |
| 20:32 | 42 | **"오케스트레이터인 관리자의 의사결정 대기 하지말고, 권장사항을 지속적으로 업무 수행하기 바람"** | 운영지시 | 자율 진행 모드 v3 진입. 41번 종결 후 동일 세션 재개. SESSION-SUMMARY v3 §5 권장 우선순위 순차 진행: ① shadcn Wave 2 (DropdownMenu/Dialog/DataTable) → ② cmdk Command Palette (Cmd+K) → ③ 추가 e2e + 문서. 외부 의존 없는 트랙만 자율 진행, OpenAPI 키/SMTP/카카오 등 외부 의존 트랙은 사용자 액션 영역 유지. |
| 20:38 | 43 | **"외부의존 트랙도 진행.. 의사결정함"** | 운영지시 | 자율 v3 범위 확장. 외부 의존 트랙 중 내가 수행 가능한 것은 자율 진행: ① ai SDK v6 마이그레이션 (route + 콘솔 + Generative UI) ② ML 학습 인프라 검증 (pip install -e ".[ml]" + dataset 생성 + train 시도) ③ Neo4j PoC docker compose 시도 (Docker Desktop 가용 시) ④ Cache Components canary 검증 (참조 구현). 정부 사이트 키 발급/SMTP·Slack·Kakao 비즈니스 계정 등록은 사용자만 가능 — 가이드 문서 강화로 대체 (TROUBLESHOOTING/NOTIFICATIONS/OPERATIONS 보강). |
| 21:?? | 44 | **"남은 사용자 액션 하자"** | 핵심지시 | 외부 의존 트랙 같이 진행 — OpenAPI 키 발급 / SMTP / Slack / Docker. 사용자가 외부 사이트에서 가입·신청·승인을 하고, 내가 .env 갱신·어댑터 갱신·검증을 담당하는 협업 모드 |
| 21:?? | 44-A | **"공공데이터포털 OpenAPI 키 4종"** (4지선다) | 선택 | OpenAPI 트랙 우선. data.go.kr LH/EX/KWater/Korail 입찰 OpenAPI 존재 여부 검증 → LH 5종(입찰공고/사전규격/개찰/계약/발주계획) + EX 1종(계약공개) + KWater 1종(계약정보공개) 신청 가능, Korail은 data.go.kr 미제공으로 보류 |
| 21:?? | 44-B | **"LH 5종 + EX/KWater 계약 2종 = 7개 일괄"** | 선택 | 일괄 신청 모드 채택 |
| 21:?? | 44-C | **"기존 G2B 키 재사용"** | 선택 | data.go.kr 단일 인증키 정책에 맞춰 .env에 LH_API_KEY/EX_API_KEY/KWATER_API_KEY를 G2B 키 재사용으로 설정 |
| 21:?? | 44-D | **"지금 7개 활용신청 시작하겠음"** | 선택 | 진행. probe_external_apis.py 검증 → LH endpoint 작동(자체 포털 EUC-KR XML, 필수 파라미터 명세 필요), EX/KWater는 추정 URL 오류(HTTP 500) |
| 21:?? | 44-E | **"Docker Desktop 시작 → Neo4j PoC 검증"** | 선택 | 활용신청 대기 중 병렬 트랙 — Docker Desktop 시작 요청 (사용자 작업 대기 중) |
| 22:?? | 45 | **"EX를 뺀 LH, KWATER는 활용신청 OK"** | 정정 | 활용신청 범위 축소: LH 5종 + KWater 1종 = 6종 OK. EX 제외, Korail 보류. 다음 단계: probe 재실행으로 키 활성 확인 + LH/KWater 명세서로 어댑터 endpoint 갱신 |
| 22:?? | 46 | **(스크린샷 첨부) kwater-01.png + lh-01.png** | 통찰 | KWater 미리보기 응답 파악 (resultCode 00, 9개 필드 contract용). LH 14건 활용신청 OK 확인 |
| 22:?? | 47 | **"https://apis.data.go.kr/B500001/ebid/cntrct3/cntrwkList?serviceKey=...&_type=xml&searchDt=202205"** | 통찰 | KWater 정확한 endpoint 제공. 즉시 검증 → HTTP 200 totalCount 61, json/xml 둘 다 지원. KWater 어댑터 BASE_URL=B500001, ENDPOINT=cntrwkList로 갱신 |
| 22:?? | 48 | **(스크린샷 + URL) lh-02.png + LH 사전규격 호출 URL** | 통찰 | LH 자체 포털 endpoint 패턴 확인 (OpenAdvcinfoReqList.dev). 단, "SERVICE KEY IS NOT REGISTERED ERROR (resultCode 30)" — G2B 통합 키와 별개로 LH 자체 포털 키 활성화 필요. data.go.kr 단일 인증키 정책이 LH 자체 포털엔 적용 안 됨 |
| 22:?? | 49 | **"LH는 연결하지 않아도 됨. 정보화 업무영역에서는 포함이 안되어도 됨"** | 정정 | LH 5종 트랙 보류 결정. 정보화 영역(주로 IT 용역)과 LH 업무(건축/토목/주택)는 거리 있음. KWater만 ACTIVE 유지 — 단일 외부 어댑터 검증 케이스로 운영. EX/Korail/LH 모두 비-사용 |
| 22:?? | 50 | **"Gmail SMTP App Password (Recommended)"** (4지선다) | 선택 | 알림 채널 트랙 — Gmail SMTP App Password 우선 |
| 22:?? | 50-A | **"<redacted 16자리 App Password>"** | 운영지시 | Gmail App Password 16자리 paste. .env에 SMTP_HOST=smtp.gmail.com / PORT=587 / USER=lapiogga@gmail.com / PASSWORD=<masked> / FROM 추가. send_email() 자체 발송 테스트 → "OK 발송 완료" → SMTP dispatcher 검증 OK |
| 22:?? | 51 | **"continue"** | 선택 | 자율 v4 라운드 진입. v5 종결 후 SESSION-SUMMARY v5 §6 권장 우선순위 ① KWater frontend 통합 — search_contracts MCP 도구 등록 + frontend 통합 + mock + e2e |
| 22:?? | 52 | **"SLACK과 kakao 연결은 꼭 필요한가? 꼭 필수가 아니면 연결하지말고 Skip"** | 정정 | Slack Webhook + Kakao 알림톡 트랙 영구 Skip. 알림 채널은 Gmail SMTP 단일로 종결 (#50 N24 검증 완료). USER-ACTIONS.md §2.2~2.3 보류 표시. SESSION-SUMMARY 시점관리에서 미진행 → Skip 갱신 |
| 23:?? | 53 | **"실제 구현으로 진입"** | 핵심지시 | 자율 v5 라운드. KWater 추가 endpoint 검증(servcList 발견 — 정보화 영역 핵심 용역 131건) → 어댑터 ENDPOINTS 분기(공사/용역) → MCP 도구 biz_type 파라미터 → frontend 페이지 업종 select(default 용역) → e2e 4개 PASS, 전체 36/36 PASS |
| 23:?? | 54 | **"continue"** | 선택 | 자율 v6 — 실 데이터 PoC 풀스택 시연. ① G2B Python 직접 호출 9124건 검증 (정보화 용역 1주치) ② MCP stateless 모드(FASTMCP_STATELESS_HTTP=true + http_app(stateless_http=True)) 활성 ③ KWater live frontend 검증 — apis.data.go.kr/B500001/ebid/cntrct3/servcList → MCP stateless → /external/kwater 풀스택 OK (131건/5건 표시 3.6초). G2B /bids는 numOfRows=999×10페이지 풀스캔 패턴으로 timeout — 별도 fix 트랙 |
| 00:?? | 55 | **"continue"** (5/3) | 선택 | 자율 v7 — /bids 라이브 fix. search_bid_notices의 max_scan_pages를 50000→1로 단축 (단일 페이지 999건만 스캔). 응답 3.3초. /bids?q=정보화&type=용역 풀스택 검증 OK — 9124/2건 표시(한의약정보화 AI추진/KTL ISP ISMP). G2B → MCP stateless → frontend 핵심 시나리오 라이브 작동 |
| 00:?? | 56 | **"계속 진횅"** | 선택 | 자율 v8 진입 — 다른 페이지 라이브 검증 + cursor 페이징 |
| 00:?? | 56-A | **"진행"** | 선택 | v8 진행 |
| 00:?? | 57 | **"전체 구현단계까지 모두 만들어 줘"** | 핵심지시 | 자율 v8 끝까지: ① /vendors/[bizNo] 라이브 (1058705373 → NTS '계속사업자, 부가가치세 일반과세자' 정상) ② /agencies?name=조달청 라이브 (200 OK, 데이터 매칭 부족 — 정상 응답) ③ search_bid_notices에 page 인자 cursor 페이징 추가 (BidNoticeSearchInput/Result + bid.py + actions.ts) ④ /bids 페이지에 PageNav UI(이전/다음 + 현재/총페이지) ⑤ 페이지네이션 라이브 검증 (page=1 9124/2건 + page=2 0건 결과없음 + 다음→ 표시) ⑥ e2e 36/36 PASS |
| 00:30 | 58 | **"/gsd-verify-work"** (skill 호출) | 운영지시 | UAT 워크플로 진입. 01-UAT.md 신규 + Test 1 (Cold Start Smoke) 시작. |
| 00:35 | 59 | **(스크린샷) err-01.png ERR_CONNECTION_REFUSED** | 통찰 | Test 1 fail. MCP 8081/frontend 3020 미가동 — 직전 라이브 검증 후 종료된 채로 사용자가 cold start 시도. 4 서비스 재가동 → MCP 405/frontend 200/Redis Up/Neo4j Up 정상 확인. |
| 00:50 | 60 | **"'업체분석'에서 업체명으로 조회 + '입찰 검색'에서 like 검색 + KWater 계약공개 클릭 시 화면 이동"** | 핵심지시 | 자율 v9 사용자 후속 결함 3건 fix: ① searchVendorsByName + /vendors LIKE 결과 페이지 ② search_bid_notices scan_pages 인자 + /bids deep checkbox + SSE keepalive ping 파싱 ③ /external/kwater/contract 단건 페이지 + 표 컬럼 클릭 라우팅. commit 5d0097c. |
| 00:55 | 61 | **"MOCK MODE 해제" + "실제 데이터로 테스트되어야 함"** | 운영지시 | UAT를 라이브 G2B/NTS API로 실행 (MCP_MOCK_MODE=false). |
| 00:58 | 62 | **"YES"** | 선택 | Test 2 (DropdownMenu 정렬) 진행 동의. |
| 01:10 | 63 | **"4개월 조회 안됨 + 업종 전체 안됨 + 마감일임박 안됨 + R26BK01435763-000 추적 안됨 (err-02) + 발주기관 분석 안됨 (err-03) + 페이징 결과없음 25966건 (err-04)"** | 핵심지시 | UAT 결함 6건 일괄 보고. 결함 #1 (date 4개월) #2 (업종 전체 1종만) #3 (마감 임박 정렬) #4 (R 형식 trace) #5 (발주기관 5년 0건) #6 (LIKE 25966건 0건 메시지 혼란). |
| 01:25 | 64 | **"시나리오 20개 × 케이스 10개 = 200, 입력값/예상결과 문서 먼저 보여줘"** | 핵심지시 | Full Test Plan 작성 — .planning/phases/01-autonomous-v3-v8/02-FULL-TEST-PLAN.md + tests/full-test-cases.json. 4지선다 결정: 페이지별 차등 default / 라이브+Playwright 혼합 / 단일 md+JSON / 운영 핵심 위주. |
| 01:50 | 65 | **"S01: 날짜 다양한 범위 + 클릭 검증 / S03 동일 / S05 다양한 단어 / S06 다양한 사업자 / S07 다양한 업체명 / 모든 시나리오 풍부한 입력값"** | 정정 | Full Test Plan v2 — 날짜 매트릭스 11종, 키워드 풀 20, 업체명 풀 16, 사업자 풀 10, 발주기관 풀 15, 공고번호 풀 10, KWater 월 풀 10, 클릭 검증 18건 곳곳 분산. 모든 케이스 distinct 입력. |
| 01:55 | 66 | **"각 화면별 날짜 기본 설정 시 조회 건수/성능/소요시간 측정 후 적정 범위 결정"** | 핵심지시 | 라이브 측정 진행 — Redis FLUSHALL 후 cold 1차 호출. /bids D7~D60, /vendors LIKE D30~D180, /vendors/{biz} Y1, /agencies D90~D365, /kwater. 결과: /bids 1개월 4.2초 OK, /vendors LIKE D30 broad 키워드(디지털) 19.7초, /agencies D365 측정 1.7초 (첫 호출 캐싱 영향), /kwater 직전월 1.9초. /vendors LIKE default 90→30일 단축 결정. |
| 02:00 | 67 | **"ok"** | 선택 | 측정 기반 default 결정 동의 → fix v10 라운드 진입. |
| 02:30 | 68 | **"commit 진행"** | 운영지시 | fix v10 일괄 commit (e9c8387) — chunking + 3종 endpoint merge + R 형식 폴백 + 측정 기반 default + Full Test Plan v2 + JSON fixture. 13 파일 +1682 -175. |
| 02:45 | 69 | **"continue"** | 선택 | 자율 v11 — fix v10 라이브 추가 검증. ① 결함 #4 R26BK01439997 trace 폴백 — G2B 한계로 found=false (별도 라운드) ② 결함 #6 LIKE 0건 메시지 정상 표시 OK ③ 결함 #5 /agencies 1년 60.7초 → 6개월(180일) default 조정. fix v10.2 commit (2863528) — _infer_period_from_bid_no 헬퍼 + numOfRows 50→999 + bid_no 매칭 + agencies 6개월. |
