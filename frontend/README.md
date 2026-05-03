# GovProcu Frontend (UI Phase A)

> 데스크톱·태블릿 웹앱 (사용자 5/2 23번 모바일 제외 정정).
> Next.js 15 + AI SDK 5 + shadcn/Tailwind v4 + MCP 60 tools.

## 빠른 시작

```bash
cd frontend
npm install
cp .env.example .env.local  # ANTHROPIC_API_KEY, GOVPROCU_MCP_URL 입력
npm run dev
```

http://localhost:3000

## 페이지

| 경로 | 설명 |
|------|------|
| `/` | 대시보드 — 9개 메뉴 카드 + 빠른 검색 |
| `/console` | **AI 자연어 콘솔** (R&D-B) — Claude가 도구 자동 호출 |
| `/bids` | 입찰 검색 (TODO: Phase B) |
| `/bids/trace` | 입찰 상세 추적 — `trace_bid_lifecycle` (TODO: Phase B Streaming Timeline) |
| `/vendors/[bizNo]` | 업체 프로필 (TODO: Phase B) |
| `/agencies/[code]` | 발주기관 분석 (TODO) |
| `/analytics` | 분석/통계 (TODO: Phase C) |
| `/lookup` | Cross-Lookup (TODO: Phase D) |
| `/me` | 알림 + 즐겨찾기 (TODO) |
| `/prediction` | 투찰가 예측 (TODO) |
| `/qualification` | 적격심사 계산기 (TODO) |

## 환경변수 (`.env.local`)

```env
ANTHROPIC_API_KEY=sk-ant-...
GOVPROCU_MCP_URL=http://localhost:8081
```

## 기술 스택

FRONTEND-TECH.md Wave 1 + Wave 2 일부:
- Next.js 15 (App Router + Turbopack)
- React 19
- Tailwind v4 (`@theme` + OKLCH)
- AI SDK 5 (`@ai-sdk/anthropic` + tool streaming)
- TanStack Query/Table
- TypeScript strict

## 다음 단계

| Phase | 기간 | 내용 |
|-------|------|------|
| **A (현재)** | - | 부트스트랩 + 자연어 콘솔 |
| **B** | 2주 | 입찰 상세 추적 Streaming Timeline + 업체 프로필 + 입찰 검색 |
| **C** | 2주 | 발주기관 분석 + 분석/통계 (Tremor 차트 통합) |
| **D** | 1주 | Cross-Lookup (xyflow 그래프) + 즐겨찾기 |
| **E** | 1주 | 알림·다이제스트·적격심사·투찰가 화면 + Playwright E2E |
