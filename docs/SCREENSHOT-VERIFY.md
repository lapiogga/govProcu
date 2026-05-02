# 프론트 화면 mock 검증 가이드

> 사용자 32번 발화 "프론트 화면 전체 mock 데이터 기반 스크린 캡쳐 검증 필요" 대응.
> MCP 서버 없이도 전 페이지 렌더링 + Playwright 자동 캡쳐.

---

## 1. 동작 원리

```
[Page RSC] → callMcpTool() → MCP_MOCK_MODE=true ? buildMockResult() : fetch(MCP)
                                                       │
                                                       └─ src/lib/mocks.ts MOCK_FIXTURES
```

`MCP_MOCK_MODE=true` 환경변수가 `frontend` 프로세스에 설정되면, **모든 MCP 도구 호출이 fixture 응답으로 단락**된다. 페이지·컴포넌트 코드는 일절 변경되지 않는다 (production 안전).

운영 시에는 절대 설정하면 안 되며 — `.env.local` 가 아닌 일회성 shell 변수로만 활성화한다.

---

## 2. fixture 커버리지

`frontend/src/lib/mocks.ts` 의 `MOCK_FIXTURES` 가 다음 도구를 모킹:

| 영역 | 도구 |
|------|------|
| bid | search_bid_notices, get_bid_notice_detail |
| workflow | trace_bid_lifecycle (★ 6단계 전부), vendor_profile, agency_procurement_history |
| analytics | industry_trend, market_share, analyze_agency_price_pattern |
| lookup | lookup_by_bid_no, lookup_by_biz_no, lookup_by_inst_code |
| me | list_my_watchlist, list_my_subscriptions |
| qualification | calc_qualification_score |
| prediction | predict_bid_price, compare_bid_strategies |
| multi_agency | list_supported_agencies |

미정의 도구는 `{status: "mock_no_fixture", tool: <name>}` 응답 — 페이지가 그래도 렌더링되도록 graceful.

---

## 3. 실행 단계

### 3.1 의존성 설치 (1회)
```powershell
cd C:\Users\User\GovProcu\frontend
npm install
npx playwright install chromium webkit
```

### 3.2 dev 서버를 mock 모드로 실행
```powershell
$env:MCP_MOCK_MODE = "true"
npm run dev
# → http://localhost:3000
```

### 3.3 별도 터미널에서 캡쳐
```powershell
cd C:\Users\User\GovProcu\frontend
npm run test:screenshots
```

### 3.4 결과 확인
```
frontend/tests/e2e/screenshots/
  Desktop-Chromium/
    01-dashboard.png
    02-bids-trace.png
    ...
    13-console.png
  Tablet-(iPad-Pro-11)/
    01-dashboard.png
    ...
```

---

## 4. 캡쳐 페이지 목록 (13장 × 2 viewport = 26장)

| # | path | 검증 포인트 |
|---|------|----------|
| 01 | `/` | 대시보드 9 메뉴 카드 |
| 02 | `/bids/trace?no=...` | ★ 6단계 lifecycle (사전규격→공고→응찰→낙찰→NTS→계약) |
| 03 | `/search?keyword=AI` | 메인 검색 결과 |
| 04 | `/bids?keyword=AI` | 입찰 목록 |
| 05 | `/vendors/1234567890` | 업체 프로필 + Tremor 차트 |
| 06 | `/agencies?name=...` | 발주기관 분석 + 사정률 패턴 |
| 07 | `/analytics?type=용역` | 동향 + 시장점유 (Tremor 차트 2종) |
| 08 | `/lookup?mode=bid` | xyflow 4 키 그래프 (공고 기준) |
| 09 | `/lookup?mode=biz` | xyflow 4 키 그래프 (사업자 기준) |
| 10 | `/me` | 즐겨찾기 + 알림 구독 |
| 11 | `/qualification?...` | 적격심사 점수 표 |
| 12 | `/prediction?...` | 투찰가 예측 + 시나리오 |
| 13 | `/console` | AI 자연어 콘솔 (mock 어려움 — 빈 상태) |

---

## 5. 단일 페이지 캡쳐

특정 페이지만 다시 캡쳐:
```powershell
npm run test:screenshots -- --grep "02-bids-trace"
```

특정 viewport만:
```powershell
npm run test:screenshots -- --project="Desktop Chromium"
```

---

## 6. 트러블슈팅

### 6.1 페이지 빈 화면
- `npm run dev` 콘솔 확인 — TS 컴파일 오류 시 빨간 줄 표시
- `MCP_MOCK_MODE` 가 dev 서버 프로세스에 전달됐는지 확인 (`echo $env:MCP_MOCK_MODE`)

### 6.2 차트(Tremor) 미렌더
- Suspense 안에서 client component → 800ms 대기로도 부족할 수 있음. spec 의 `waitForTimeout(800)` 을 1500 으로 증가

### 6.3 xyflow 그래프 빈 캔버스
- `'use client'` 컴포넌트 import 시점 hydration 필요. spec 마지막에 `await page.waitForSelector(".react-flow__node")` 추가 시도

### 6.4 console 페이지가 ANTHROPIC_API_KEY 없어서 깨짐
- 정상. mock 검증의 의도는 페이지가 "오류 화면이라도 렌더링" 되는 것 — 빈 prompt 입력 폼만 캡쳐

### 6.5 hydration mismatch warning
- 시간 표시 등 Date.now() 의존 → fixtures 의 created_at 등이 고정값이라 안전
- 그래도 경고 발생 시 무해 — 캡쳐 결과만 확인

---

## 7. 운영 안전

- `MCP_MOCK_MODE` 는 코드에 하드코딩 절대 금지
- production build (`next build`) 시점에 환경변수 미설정이면 `MOCK_MODE=false` → fixture 코드는 dead-eliminate 안 되지만 호출 안 됨
- CI에서 mock 캡쳐를 자동 실행하려면 `.github/workflows/screenshots.yml` 별도 추가 (차기 세션)

작성: 2026-05-02 · 사용자 32번 발화 대응
