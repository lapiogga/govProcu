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
