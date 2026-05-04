# ROUND 4 FIX REPORT

> Phase 30 Round 4 — fixer-r4. P1 batch — default 기간 1년 확장 + r.ok 분기.
> 입력: ROUND-3-REPORT.md / ROUND-3-HOTFIX-TEST.md / DIAGNOSIS-G4.md.
> 산출: 3 atomic commits (영역별) + tester-r4 핸드오프.

## Commits

| # | hash | 영역 | 변경 라인 | 적용 P1 |
|---|------|------|----------|---------|
| 1 | `383a7e5` | agencies | +21 / -4 (1 file) | P1-10, P1-19 |
| 2 | `e5d4597` | analytics | +35 / -2 (1 file) | P1-11, P1-20 |
| 3 | `79bfc2c` | prediction | +10 / -0 (1 file) | P1-21 |

총 3 commit, 3 files, +66 / -6 라인 (frontend only).

---

## 적용 변경 상세

### Commit 1 (`383a7e5`) — `/agencies` default 1년 + r.ok 분기

**파일**: `frontend/src/app/agencies/page.tsx`

| 변경 | 위치 | 내용 |
|------|------|------|
| `defaultAgencyFrom` 30일 → 365일 | L19-26 | `d.setDate(d.getDate() - 30)` → `d.setDate(d.getDate() - 365)`. 주석 갱신 (v23.1 5초 SLA → P30-R4 P1-10). 큰 범위 경고(isLargeRange >365일)는 기존 그대로 — 1년 default는 경계, form 입력 시만 trigger |
| PriceCard `r.ok` 분기 | L150 위 | `if (!r.ok) return <ErrorBox>...{r.error}</ErrorBox>;` (border-danger + danger-bg 토큰) |
| HistoryTable `r.ok` 분기 | L211 위 | 동일 패턴 — "발주 이력 조회 오류" 라벨 |

**적용 P1**:
- **P1-10**: 30일 → 365일 default. F12 (재정관리단) / F13 (국방부) 큰 기관 30일 0건 false-negative 회피
- **P1-19**: PriceCard / HistoryTable 양쪽 r.ok 분기 — silent fail 회피

**시그니처 변경**: 0 (defaultAgencyFrom 내부 상수만 변경, 함수 시그니처 동일)

### Commit 2 (`e5d4597`) — `/analytics` default 1년 + r.ok 분기

**파일**: `frontend/src/app/analytics/page.tsx`

| 변경 | 위치 | 내용 |
|------|------|------|
| `todayYYYYMMDD` + `defaultAnalyticsFrom` 헬퍼 추가 | L12-30 | agencies와 동일 패턴 — 365일 default. 주석에 P1-11 사유 명시 (G2B inqryBgnDt 누락 → 0건/rate_limit) |
| `dateFrom` / `dateTo` 변수 도입 | L37-38 | `sp.from \|\| defaultAnalyticsFrom()` / `sp.to \|\| todayYYYYMMDD()` |
| Suspense 내부 `from={sp.from}` → `from={dateFrom}` | L60, L64 | TrendSection / MarketShareSection 양쪽 |
| TrendSection `r.ok` 분기 | L88 위 | "업종 동향 조회 오류" border-danger 분기 |
| MarketShareSection `r.ok` 분기 | L162 위 | "시장 점유 조회 오류" 분기 |

**적용 P1**:
- **P1-11**: from/to 미입력 시 365일 default — backend 무기간 호출 (G2B inqryBgnDt 누락 → chunk_date_range fallback today 1개월) 회피
- **P1-20**: TrendSection / MarketShareSection r.ok 분기 — "데이터 없음"과 통신 오류 구분

**시그니처 변경**: 0 (`getIndustryTrend(bizType, undefined, from, to)` / `getMarketShare(bizType, from, to, 20)` — caller 시그니처 그대로, dateFrom/dateTo는 내부 변수)

### Commit 3 (`79bfc2c`) — `/prediction` ScenarioTable r.ok 분기

**파일**: `frontend/src/app/prediction/page.tsx`

| 변경 | 위치 | 내용 |
|------|------|------|
| ScenarioTable `r.ok` 분기 | L171 위 | PredictResult와 동일 패턴 (Card border-danger + CardContent) — 일관성 유지 |

**적용 P1**:
- **P1-21**: ScenarioTable의 r.ok 체크 누락 회복

**시그니처 변경**: 0

---

## 결정 메모

1. **agencies default 1년 채택 사유**: F12/F13 사용자 보고 큰 기관 매칭 회복이 핵심. CHECKLIST §2 P1-10에서 "default 90일 또는 365일" 선택지 중 365일 채택 — 큰 기관(예: 재정관리단)이 90일 내 0건일 가능성 (sample_count 정밀도). 1년 default + form 입력 시 입력값 우선 (sp.from || defaultAgencyFrom).
2. **isLargeRange 경고는 그대로**: 기존 isLargeRange (>365일) 경고는 1년 default를 경계 미초과 — form에서 사용자가 더 큰 범위 입력한 케이스에만 trigger. default 1년에서는 경고 노출 0 (의도된 동작).
3. **r.ok 분기 패턴 일관**: ROUND-3 trace StageError 패턴 + PredictResult 기존 분기를 참고 — `border-danger` + `danger-bg` 또는 `<Card className="border-[var(--color-danger)]">` 두 형태 혼용 (각 영역의 기존 스타일 일관성 우선). agencies는 단일 컴포넌트가 아닌 div 박스 (TrendSection / MarketShareSection도 동일), prediction ScenarioTable은 Card 패턴 — PredictResult와 일관.
4. **analytics dateFrom/dateTo 변수 추가 이유**: 헬퍼 호출을 Suspense 자식 컴포넌트마다 반복하지 않기 위해 page 함수에서 1회 계산 후 prop 전달. backend 호출 시그니처 변경 0 (caller actions.ts 그대로).
5. **prediction ScenarioTable null 분기 유지**: 기존 `if (scenarios.length === 0) return null;` 분기는 보존 — sp.base + sp.inst 둘 다 입력된 경우에만 trigger (Suspense 부모 조건). r.ok 분기는 그 위에 추가.
6. **backend 미변경**: 본 R4는 frontend only — uvicorn 재기동 불필요. ROUND-3-HOTFIX 학습 (uvicorn `--reload` 미설정 → backend 변경 시 재기동 필요)을 sanity check 항목으로 명시.
7. **3 atomic commits**: 영역별 분리 (agencies / analytics / prediction). R3에서 4 commit (영역별) 패턴 계승 — round-over-round 일관성. 회귀 추적 시 영역별 hash bisect 가능.

---

## 자체 sanity check (R4 강화 의무 항목)

| 항목 | 결과 | 비고 |
|------|------|------|
| backend 호출 시그니처 변경 여부 | NO — frontend only | 3 commit 모두 frontend `app/*/page.tsx`만 수정 |
| backend 도구 호출 인자 cross-check | OK | actions.ts caller 5개 (`agency_procurement_history`, `analyze_agency_price_pattern`, `industry_trend`, `market_share`, `compare_bid_strategies`) — 시그니처 변경 0. 본 R4는 `dateFrom`/`dateTo` 변수 도입(analytics) + `defaultAgencyFrom` 내부 상수 변경(agencies) + r.ok 분기 추가만 — actions.ts 변경 0 |
| TypeScript 컴파일 0 에러 | PASS | 각 commit 후 `cd frontend && npx tsc --noEmit` 0 에러 (3회 모두) |
| import 누락 점검 | OK | 신규 import 0 (agencies/analytics/prediction 모두 기존 import 활용 — extractMcpData, fmtWon, Card, CardContent, getIndustryTrend, getMarketShare 등 모두 기존 import) |
| 의도 외 라인 수정 | NO | diff stat: agencies +21/-4, analytics +35/-2, prediction +10/-0 — 모두 P1-10/11/19/20/21 범위 내 |
| 기존 functionality 회귀 위험 | OK | sp.from/sp.to 입력 시 입력값 우선 (`sp.from \|\| default`) — 기존 form 동작 보존. r.ok 분기는 기존 silent return을 대체하지 않고 추가 (data null 분기는 그대로). isLargeRange / sample_inst_names / Suspense fallback 등 기존 UX 100% 보존 |
| 영향 받지 않는 화면 무변동 | OK | vendors / bids / lookup / qualification / search / trace / me / console / external — 변경 0 (frontend 3 파일 외 0) |
| backend 미변경 → uvicorn 재기동 | 불필요 | R4 frontend only — 재기동 절차 불필요. 단 절차 명시 (R3 학습) |

---

## 핸드오프 메시지 (tester-r4 앞)

- 3 commit 누적 검증 부탁: `383a7e5` (agencies) → `e5d4597` (analytics) → `79bfc2c` (prediction)
- backend 미변경 — uvicorn 재기동 불필요
- L4 핵심 case (사용자 보고 사례 직결):
  1. `/agencies?name=재정관리단` (default 1년) → R4 효과 확인 (R3 30일 default 0건 → R4 1년 default N건)
  2. `/agencies?name=국방부` (default 1년) → 동일 패턴
  3. `/agencies?name=조달청` (default 1년) → 큰 기관 매칭
  4. `/agencies?name=재정관리단&type=용역` (1년 + bizType) → 1차 필터링
  5. `/analytics` (sp.from / sp.to 미입력 → default 1년 자동 적용) → industry_trend / market_share 무기간 호출 회피 evidence
- L5 시각 검증:
  1. `/agencies?name=재정관리단` HTTP 200 + sample_count > 0 또는 sample_inst_names 노출 (default 1년 효과)
  2. `/analytics` (날짜 미입력) HTTP 200 + monthly.length > 0 (default 1년 효과)
  3. `/prediction?bid_no=...` 또는 `?base=...&inst=...` (정상 케이스) — ScenarioTable 정상 렌더링 (회귀 0)
  4. backend 통신 오류 시뮬 (있는 경우) → "backend 통신 실패" 메시지 노출 (3 영역 모두)
- 회귀 점검 강화 (R3 학습): backend caller 시그니처 cross-check 의무
  - actions.ts 5개 caller 시그니처 변경 0 (본 R4 frontend only)
  - inspect 의무 항목 — 본 R4에서 변경 없음 확인용 1회 검증 권장
- L1 정적: `cd frontend && npx tsc --noEmit` 0 에러 (3 commit 누적 PASS)
- 회귀 위험 영역: agencies (defaultAgencyFrom 30일 → 365일) — 기존 5초 SLA 약속이 1년 chunk 12회 ≈ 60초로 늘어남. estimatedSec 표시는 있으나 default 1년에서 isLargeRange는 trigger 안 됨 (경계). `/agencies?name=조달청` (큰 기관 + 1년 + 매칭多) 응답 시간 측정 권고 — SLA 회귀 평가
- 산출물: 본 ROUND-4-FIX.md 1 파일

---

## 제약 준수 검증

- [x] backend 미변경 (frontend only)
- [x] 3 atomic commits (영역별)
- [x] ROUND-4-FIX.md 외 신규 파일 생성 0
- [x] 다음 round (R5) 작업 0
- [x] R3.5 학습 반영 (backend 시그니처 cross-check 명시 항목, uvicorn 재기동 절차 명시)
- [x] R3 commit 패턴 계승 (영역별 atomic)
