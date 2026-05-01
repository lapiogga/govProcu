# GovProcu Frontend Tech R&D — 2025~2026 최신 프론트엔드 접목 보고서

> 작성: 2026-05-02 01:13 KST
> Frontend Tech R&D Team (sub-agent)
> 사용자 5/2 01:08 KST 통찰 응답

---

## 결론 (먼저)

UI-PLAN v1의 Next.js 15 + shadcn/ui + Tailwind v4 스택은 시장 표준. **차별화 동력**은 4개 축 추가로 1~2년 앞선 콘솔이 됨:

1. **Cache Components + Streaming** (Next.js 15) — `trace_bid_lifecycle` 6단계 도착 즉시 표시
2. **Vercel AI SDK 5 Generative UI** — 자연어 검색 박스가 LLM으로 도구 자동 호출 (MCP 직결)
3. **xyflow(React Flow) + Tremor** — Cross-Lookup 4키 그래프, 대시보드 즉시 구축
4. **OKLCH 컬러 + View Transitions API** — 표 가독성·전환 부드러움

---

## A. 기술 매트릭스 (적용 우선순위)

| # | 기술 | 카테고리 | GovProcu 적용 화면 | 효과 | 비용 | 우선순위 |
|---|------|---------|------------------|------|---------|---------|
| 1 | RSC + Streaming + Suspense | Next.js | `trace_bid_lifecycle` 6단계 점진 로드 | 체감 3~5배, TTFB ↓ | 낮음 | ★★★★★ |
| 2 | Cache Components (`'use cache'`) | Next.js | 통계/분석, 발주기관 이력, 동향 | ms 단위 응답, API 호출 절감 | 낮음 | ★★★★★ |
| 3 | AI SDK 5 + `useChat` tool streaming | AI | 자연어 검색 콘솔(헤더 cmd+k, 홈) | LLM이 42 도구 자동 선택 | 중 (LLM 비용) | ★★★★★ |
| 4 | shadcn/ui v3.5 (data-table/command/sidebar/chart) | UI | 전 화면 공통 | 표준 UI 즉시 | 낮음 | ★★★★★ |
| 5 | Tailwind v4 + `@theme` + OKLCH | 디자인 토큰 | 전역, 표 가독성, 다크모드 | 명도 균일, 정부 데이터 표 가독 ↑ | 낮음 | ★★★★★ |
| 6 | Tremor 차트 (Recharts 기반) | 시각화 | 대시보드, industry_trend, market_share | 정부 통계 대시보드 즉시 완성 | 낮음 | ★★★★ |
| 7 | AI SDK `useObject` + `streamObject` | AI | trace_bid_lifecycle JSON 부분 응답 | 6단계 도착 즉시 타임라인 | 중 | ★★★★ |
| 8 | xyflow (React Flow) + Dagre | 시각화 | Cross-Lookup, 입찰 → 응찰업체 관계도 | 4 키 노드·엣지 직관 | 중 | ★★★★ |
| 9 | TanStack Query v5 + Suspense Mode | 데이터 | 클라이언트 캐싱·prefetch | 즐겨찾기 빠른 전환 | 낮음 | ★★★★ |
| 10 | Server Actions + revalidateTag/updateTag | Next.js | 즐겨찾기, 알림 룰 | 폼 핸들러 단순화 | 낮음 | ★★★★ |
| 11 | TanStack Table + Virtual | 데이터 표 | agency_procurement_history, 응찰업체 | 대용량 표 60fps | 낮음 | ★★★★ |
| 12 | View Transitions API (Next.js 15) | UX | 검색 → 상세 → 프로필 전환 | 시선 이탈 없음 | 낮음 | ★★★ |
| 13 | React Compiler (Next.js 15 stable) | 성능 | 전역 자동 메모 | 보일러플레이트 제거 | 낮음 | ★★★ |
| 14 | Partial Prerendering (PPR) | Next.js | 대시보드 (정적 헤더 + 동적 KPI) | 정적 셸 즉시 + streaming | 낮음~중 | ★★★ |
| 15 | Apache ECharts | 시각화 | Sankey(발주기관→낙찰), Heatmap(월별·업종) | Tremor·Recharts로 안 되는 차트 | 중 | ★★★ |
| 16 | Container Queries + CSS @scope | 반응형 | 사이드 패널 카드 | 컴포넌트 재사용 | 낮음 | ★★★ |
| 17 | cmdk (shadcn command) | UX | cmd+k: 공고/사업자/기관 통합 | 영업 매니저 결정적 | 낮음 | ★★★★ |
| 18 | Triplit/Replicache (Local-first) | 데이터 | 즐겨찾기·최근 본 항목 오프라인 | 출장 환경 | 중~높음 | ★★ |
| 19 | deck.gl + Mapbox | 지리 | 발주기관·낙찰업체 지역 분포 | 지역 패턴 | 높음 | ★★ |
| 20 | Edge Runtime / Vercel Edge | 성능 | NTS 짧은 라우트 | 한국 리전 100ms 미만 | 중 | ★★ |

---

## B. 화면별 추천 스택

| 화면 | 핵심 스택 | 차별화 |
|-----|---------|-------|
| **대시보드** | Tremor + RSC + Cache Components(KPI) + cmdk + sidebar | 정적 셸 즉시 + KPI streaming |
| **입찰 검색** | shadcn data-table + Suspense + Server Actions | 페이지 이동 없는 부분 streaming |
| **입찰 상세 추적** ⭐ | RSC + 6 Suspense + AI SDK useObject + xyflow 미니 그래프 | **Streaming Timeline** (v1엔 없는 차별화) |
| **업체 프로필** | Tremor BarChart/DonutChart + Cache(`'use cache: remote'` NTS 1h) + tabs | NTS 실시간 + 통계 캐시 혼합 |
| **발주기관 분석** | TanStack Virtual Table + Tremor + Cache(분기 단위 expire) | 수천 건 가상화 |
| **분석/통계** | Tremor + ECharts(Sankey/Heatmap) + Cache(`cacheLife('hours')`) | 흐름·열지도 ECharts 보강 |
| **Cross-Lookup** | xyflow + Dagre 자동 레이아웃 + AI SDK Generative UI | **4키 노드·엣지 시각화** (그래프DB 친화) |
| **공통** | shadcn(sidebar/command/dialog/sheet) + Tailwind v4 + View Transitions | 화면 전환 부드러움 |

---

## C. 도입 단계

### Wave 1 (필수, 즉시) — 효과 大, 비용 小
- RSC + Streaming + Suspense (Next.js 15 기본)
- shadcn/ui (data-table, command, sidebar, chart)
- Tailwind v4 + OKLCH + `@theme`
- Tremor 차트
- TanStack Query v5 + Suspense Mode
- React Compiler

### Wave 2 (중요, PoC 후) — 차별화 가치
- Cache Components (`'use cache'`/`'use cache: remote'`/`'use cache: private'`)
- AI SDK 5 + `useObject` (Streaming Timeline, 자연어 콘솔)
- xyflow + Dagre (Cross-Lookup 그래프)
- Server Actions + `updateTag`
- Apache ECharts (Sankey·Heatmap)

### Wave 3 (실험적, 검증 필요)
- Local-first (Triplit/Replicache) — 출장 환경 PoC
- deck.gl 지도 시각화
- Edge Runtime — NTS 라우트 한정
- Partial Prerendering (PPR) — 대시보드 한정

---

## D. 차별화 신규 기능 (UI-PLAN v1엔 없는 5개)

1. **AI 자연어 콘솔 (Generative UI)**: "이 공고 어떻게 됐어?" → AI SDK가 trace_bid_lifecycle 자동 호출 → 부분 응답 도착 즉시 타임라인 렌더
2. **Streaming Timeline (`trace_bid_lifecycle`)**: 6단계 도착 즉시 노드 표시. 사전규격(빠름) 먼저, NTS 검증(느림) 나중
3. **Relational Graph (Cross-Lookup)**: 공고번호 → 발주기관/계약/낙찰업체 4 노드를 xyflow + Dagre 자동 레이아웃
4. **Live Command Palette (cmd+k)**: shadcn command — 공고/사업자/기관/계약 통합 빠른검색. LLM이 패턴 인식 (10자리 숫자 → 사업자번호 추정)
5. **OKLCH 다크모드 + 표 가독성**: Tailwind v4 기본. 입찰액(억) 낙찰률(%) 표 명도 균일. WCAG 2.2 자동 통과

---

## E. 우려·위험

| 위험 | 영향 | 완화 |
|-----|------|-----|
| AI SDK LLM 비용 | 자연어 콘솔 사용량 비례 | 사내 캐시, Anthropic prompt caching, 짧은 라우트만 Edge, `cacheTag('lifecycle-{bidNo}')` |
| Cache Components 안정성 | Next.js 15 신기능 — 무효화 디버깅 어려움 | Wave 2 PoC: 통계 화면 1개부터, `cacheTag` 명명 표준화 |
| xyflow 대용량 노드 | 1000+ 노드 끊김 | Cross-Lookup은 4키 중심 — 보통 20개 이내 |
| RSC/Client 경계 | "use client" 설계 필요 | 화면당 RSC 80% / Client 20% 가이드 |
| Tremor의 Recharts 의존 | 매우 큰 데이터 시 느림 | 5만+ 포인트는 ECharts/Visx 대체 |
| Local-first(Triplit) 학습 | 동기화 충돌 정책 | Wave 3 즐겨찾기 한정 PoC |

---

## F. UI-PLAN v2 갱신 권장

- `trace_bid_lifecycle` 화면 — Streaming Timeline (6 Suspense 경계) 명시
- 헤더에 cmd+k 검색 팔레트 + AI 자연어 콘솔 토글
- Cross-Lookup 화면 — xyflow 그래프 표시
- 디자인 토큰 — Tailwind v4 `@theme` + OKLCH 컬러 정의
- 캐시 정책 표 — `'use cache'`/`'use cache: remote'`/`'use cache: private'` 배분 매트릭스

---

## 출처 (context7 MCP query-docs 6개 라이브러리 직접 조회)

- Next.js Cache Components: https://nextjs.org/docs/app/api-reference/directives/use-cache
- Vercel AI SDK 5: https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage
- Tailwind v4: https://tailwindcss.com/blog/tailwindcss-v4
- shadcn/ui: https://ui.shadcn.com/docs/components/data-table
- React Flow (xyflow) + Dagre: https://reactflow.dev/examples/layout/dagre
- Tremor: https://www.tremor.so/docs/visualizations/area-chart
