# DIAGNOSIS-G4 — UI 정합성 진단 (G4 그룹)

> **그룹**: G4 — 분석/예측/적격 (4 화면)
> **대상**:
> - `/agencies` (발주기관 분석 W5)
> - `/analytics` (통계 분석)
> - `/prediction` (가격 예측 V4)
> - `/qualification` (적격심사 점수 계산기)
> **점검 차원**: 8 (D1 extract / D2 key naming / D3 빈 상태 / D4 loading UX / D5 에러 경로 / D6 기간 default + has_more / D7 포맷터 / D8 페이지네이션)
> **분류**: OK · WARN · FAIL (P0 차단 / P1 중요 / P2 권장 / P3 보완)

---

## 0. 그룹 헤드라인

| 우선 | 결함 (요약) | 영향 화면 | 핵심 evidence |
|------|------------|----------|--------------|
| **P0** | Tremor v3 차트 토큰 미설치 → **차트 검은색 사각형/색 누락** (F10) | /agencies (price pattern bar), /analytics (trend bar + share donut), /prediction(없음), /vendors(scope 외 AreaChart) | globals.css 가 Tailwind v4 `@theme` 만 정의. `tremor-*` 토큰 부재. tailwind.config 파일 없음. tremor `@tremor/react@^3.18.7` 는 tremor-token 의존 |
| **P0** | `/agencies` `PriceCard` — backend `analyze_agency_price_pattern` 응답에 **`p75` 필드 있음**에도 `Stat`은 `p10/p25/p90`만 표시 → 5개 슬롯 중 1개(`p25`) 중복 가능성 없음. **단, `summary_pct.p75` 누락 표시** | /agencies | agencies/page.tsx 183~189: p10/p25/median/p25(아닌 p75 누락)/p90... 실 코드는 mean/median/p10/p25/p90 5개. backend 는 mean/median/std/min/max/p10/p25/**p75**/p90 9개 제공. p75 미표시 (사용자 추천 분위 누락) |
| **P0** | `/analytics` 시장점유 표 — **사업자번호 컬럼이 `<VendorLink ... name={biz_no}>`**로 잘못 표기 → 사업자번호 자리에도 업체명 링크가 아닌 사업자번호가 들어가지만 fmtBizNo 미적용 (XXX-XX-XXXXX 포맷 아님) 그리고 의미적 중복 | /analytics | analytics/page.tsx L186~192: 두번째 `<VendorLink>` `name={v.biz_no}` — `formatBizNo` 누락. `fmtBizNo()` 안 거치고 raw 10자리 표시 |
| **P0** | `/qualification` — backend `calc_qualification_score` 응답의 `scores.management/etc` **에는 `detail` 필드가 없음**. frontend `summarizeDetail` 은 detail null일 때 `""` 반환 (OK) → **빈 셀 정상**. 그러나 `Object.entries(scores).map(... v: any)` 의 `v.detail` 이 undefined일 때 `JSON.stringify(undefined)` 는 `undefined` 반환 후 `.slice` 호출 가능성 → 안전 처리 OK. 다만 P0가 아닌 P3 | /qualification | qualification/page.tsx L133-139, qualification.py 256-260 |
| **P1** | `/prediction` — `predict_bid_price` 응답이 `status="missing_base_amount"` 일 때 화면은 안내 표시 OK이지만, backend가 `pattern_count < 5` fallback 으로 `model: "default_lower_rate"` 반환할 때 `data.agency_pattern` 이 **없음** (코드 162~178) → frontend L155 `data.agency_pattern?.sample_count ?? "n/a"` 는 OK이지만 `data.agency_pattern?.interpretation || data.note` 분기 → `data.note` 사용 OK | /prediction | prediction.py L162~178 vs prediction/page.tsx L154-157 |
| **P1** | `/agencies` 기간 default — sp.name 입력 시 30일 (v23.1 SLA 기준). 사용자 제공 사례 `재정관리단`/`국방부` 같은 큰 기관은 **30일 내 0건 가능성 매우 높음** → 사용자 학습 안내 (sample_inst_names 카드)가 출력되지만 "기간 30일 → 더 길게" 안내가 부족 | /agencies | agencies/page.tsx L24-26 (defaultAgencyFrom=30일), L156-172 빈 상태에서 "기간 확장 권장" 만 단 한 줄 |
| **P1** | `/analytics` 기간 default **없음** — sp.from/sp.to 미입력 시 `undefined` 그대로 backend 호출. backend `industry_trend / market_share` 가 무기간 호출되면 G2B `inqryBgnDt` 누락으로 **rate_limit 또는 0건** 가능 | /analytics | analytics/page.tsx L78, L151 (from=sp.from undefined) |
| **P1** | `/qualification` — 이 화면은 **`search_bid_notices` 와 무관**. 점검 요청서의 "search_bid_notices + filter (참가자격, 지역, 업종)" 설명과 실제 코드 불일치. 실제는 `calc_qualification_score` 만 호출하는 점수 계산기 | /qualification | qualification/page.tsx L4-5, L56-65 |
| **P2** | `/agencies` PriceCard — `s.mean?.toFixed(2)` 등 `toFixed(2)` 직접 호출. backend는 이미 `round(... , 3)` 으로 반환 → 표시는 2자리. 그러나 fmtRate 헬퍼 미사용 (일관성 깨짐) | /agencies | agencies/page.tsx L184-188 vs analytics.py L465-473 |
| **P2** | `/agencies` HistoryTable — has_more / scan_coverage 표시 **없음**. backend `agency_procurement_history` 는 `chunks_used`/`endpoints_used` 만 노출하고 has_more 키 자체가 미반환 (L376-389 workflow.py) → 한도 30건 초과 시 사용자 인지 불가 | /agencies | workflow.py L376-389, agencies/page.tsx L215-269 |
| **P2** | `/analytics` Trend/MarketShare — has_more / scan_coverage / endpoints_used 표시 없음. backend `industry_trend`/`market_share` 는 limit=500/1000 풀스캔이지만 G2B totalCount > limit 케이스에 대한 한계 안내 없음 | /analytics | analytics.py L237, L335 vs analytics/page.tsx 전체 |
| **P2** | `/prediction` — 검색 form `target` 분류 라벨 (0.7=p10 근처, 0.9=p10 근처) 가 **둘 다 p10 근처**로 표기 됨 → backend `predict_bid_price` 매핑 (>= 0.85 → p10, 0.65 ≤ x < 0.85 → p25) 와 **불일치** | /prediction | prediction/page.tsx L87-90 vs prediction.py L112-127 |
| **P2** | `/qualification` — Field input 모두 `type="text"` (Input 기본). `bid_amount`/`base_amount`/`tech_count` 등 숫자 필드에 `inputMode="numeric"` 또는 `type="number"` 미적용 → 모바일/태블릿에서 키패드 노출 X. 문자 입력 시 `parseInt` 가 NaN | /qualification | qualification/page.tsx L142-166 (Field 컴포넌트) |
| **P2** | `/qualification` — `parseInt(params.bid_amount!)` 결과 NaN 일 때 backend 가 nan 으로 호출되어 응답 비정상. **input type 검증 부재** (D5 시스템 경계 검증 누락) | /qualification | qualification/page.tsx L57-58 |
| **P3** | `/agencies` PriceCard — `data.summary_pct?.p75` 표시 누락 (위 P0 항목과 별개로 UX 보완 차원에서) | /agencies | analytics.py L470 |
| **P3** | `/analytics` `bizType` default=`"용역"` 하드코딩 — 사용자 직전 검색 컨텍스트 무시. localStorage/searchParams persist 미적용 | /analytics | analytics/page.tsx L16 |
| **P3** | `/prediction` ScenarioTable — `scenarios.length === 0` 일 때 `return null` (silent). 빈 상태 안내 부재 | /prediction | prediction/page.tsx L173 |

---

## 1. /agencies (발주기관 분석 W5)

**호출 도구**: `agency_procurement_history` (W5) + `analyze_agency_price_pattern` (A6)

| Dim | 결과 | Evidence |
|-----|------|----------|
| D1 extract | OK | extractMcpData 사용, null guard `if (!data) return null` (L150, L210) |
| D2 key naming | **WARN-P0** | summary_pct: backend는 `mean/median/std/min/max/p10/p25/p75/p90` (9개) → frontend는 `mean/median/p10/p25/p90` (5개) 표시. `p75/std/min/max` 누락. summary_pct.p75 (목표 낙찰확률 0.7 시나리오용 핵심) 누락. + `data.summary_pct` 와 destructure `s.mean?.toFixed(2)` — `?.` 가드는 OK |
| D2 key naming (HistoryTable) | OK | `summary.notice_count` / `summary.award_matched_count` / `summary.award_match_rate_pct` / `summary.award_total_won` 모두 backend (workflow.py L383-389) 와 일치. `it.bid_notice_no` / `it.winner.winner_biz_no` / `it.winner.award_amount` 일치 (workflow.py L365-374) |
| D3 빈 상태 | **OK (WARN-P3)** | sample_count==0 시 sample_inst_names 카드 표시 (UX 우수). 다만 HistoryTable items=[] 일 때 빈 tbody 표시 (안내 메시지 없음). 헤더의 `notice_count` 가 0일 때 표 자체가 비어 사용자가 "왜?" 인지 못함 |
| D4 loading UX | OK | 2개 Suspense (PriceCard / HistoryTable) 분리. cursor-wait + 명확 spinner + label (v22.4 F6) |
| D5 에러 경로 | **WARN-P1** | `r.ok === false` 분기 부재. `extractMcpData` 결과 null일 때 `return null` 만 (silent fail). 사용자가 backend 오류 인지 불가 |
| D6 기간 default | **WARN-P1** | sp.name 시 30일 default. 큰 기관 (재정관리단/국방부)은 30일 내 0건 비번 발생. isLargeRange (>1년) 안내만 있고 isSmallRange 안내는 없음 |
| D6 has_more | **WARN-P2** | agency_procurement_history backend는 has_more 키 미반환. 30건 cap 초과 인지 불가 |
| D7 포맷터 | **WARN-P2** | fmtWon/fmtDate 적용 OK. summary_pct는 `?.toFixed(2)%` 직접 → fmtRate 미사용 |
| D8 페이지네이션 | FAIL | limit=30 hardcoded, page param 없음 |

**Evidence 코드**:
- `agencies/page.tsx` L183-189 — `Stat label="평균" v={s.mean?.toFixed(2)+'%'}` 5개 — p75 누락
- `agencies/page.tsx` L150 — `if (!data) return null;` (에러 메시지 부재)
- `app/tools/analytics.py` L464-473 — `summary_pct` 9-key 정의
- `app/tools/workflow.py` L376-389 — `agency_procurement_history` summary 정의

**사용자 사례 (F12 재정관리단 / F13 국방부)**:
- 30일 default → 큰 기관도 데이터 부재 우려. backend는 "기간 확장" 단문만 노출. 사용자가 검색 form `from/to` 직접 입력해야 발견 가능 → **P1 권장: default 90일 또는 365일 + 큰 기관 휴리스틱 안내**

---

## 2. /analytics (통계 분석)

**호출 도구**: `industry_trend` (A3) + `market_share` (A5)

| Dim | 결과 | Evidence |
|-----|------|----------|
| D1 extract | OK | extractMcpData 사용. `data?.monthly` `data?.top_vendors` optional chain |
| D2 key naming | **OK (1 P0)** | trend: `data.monthly`/`data.total_count`/`data.total_amt` ✓ (analytics.py L262-269). market_share: `data.top_vendors`/`data.grand_total_won`/`data.vendor_count_total` ✓ (L362-369). top_vendors 항목: `v.biz_no`/`v.name`/`v.award_total`/`v.award_count`/`v.market_share_pct` ✓. **단 사업자번호 컬럼 `<VendorLink name={v.biz_no}>` 는 `name`에 raw 10자리 입력 → fmtBizNo 미적용** (P0) |
| D3 빈 상태 | OK | trend monthly.length===0 → "데이터 없음" 행. market_share top.length===0 → "데이터 없음" 행 |
| D4 loading UX | **WARN-P3** | Suspense fallback `<Skel h={20}/>` `<Skel h={32}/>` 만. 진행 메시지 없음 (agencies 의 v22.4 적용 안됨) |
| D5 에러 경로 | **FAIL-P1** | `r.ok` 미체크. `data?.monthly` optional 으로만 처리 — backend 오류 시 사용자에게 표시 없이 "데이터 없음"만 → 진단 곤란 |
| D6 기간 default | **FAIL-P1** | sp.from/sp.to 미입력 시 둘 다 `undefined` → backend 호출 (analytics.py L232-237 search_awards 호출). G2B 는 inqryBgnDt 필수 → fallback 으로 chunk_date_range 가 today만 1개월 처리. **무기간 검색은 0건 또는 부분 결과** |
| D6 has_more | **FAIL-P2** | trend/share 모두 limit=500/1000 풀스캔이지만 hint UI 없음 |
| D7 포맷터 | OK | fmtWon 적용 (L88, L115, L118, L161, L194). market_share_pct?.toFixed(2)% 직접 (fmtRate 미사용 — 일관성 P3) |
| D8 페이지네이션 | OK (애초 미해당) | trend는 월별 집계. share는 top_n=20 |

**Evidence 코드**:
- `analytics/page.tsx` L78 `getIndustryTrend(bizType, undefined, from, to)` — from/to 모두 undefined 가능
- `analytics/page.tsx` L186-192 — `<VendorLink bizNo={v.biz_no} name={v.biz_no}/>` 사업자번호 자리에도 raw biz_no
- 기대값: `<VendorLink bizNo={v.biz_no} formatBizNo />` 또는 `<VendorLink ... name={fmtBizNo(v.biz_no)} />`
- `app/tools/analytics.py` L262-270 (industry_trend), L362-369 (market_share)

---

## 3. /prediction (가격 예측 V4)

**호출 도구**: `predict_bid_price` + `compare_bid_strategies`

| Dim | 결과 | Evidence |
|-----|------|----------|
| D1 extract | OK | extractMcpData 사용. data null guard + status==="missing_base_amount" 분기 (L132) |
| D2 key naming | **WARN-P1** | `data.recommended_amount` ✓ / `data.recommended_rate_pct` ✓ / `data.ci_95?.low_amount/high_amount` ✓ / `data.model` ✓ / `data.agency_pattern?.sample_count/interpretation` ✓ (prediction.py L139-152). pattern 부족 fallback (L162-178) 시 `agency_pattern` 키 없음 → `?.` 안전. `data.note` fallback OK |
| D2 key naming (Scenario) | OK | `data.scenarios[]`/`data.agency_sample_count`/`s.bid_rate_pct/bid_amount/estimated_win_prob` ✓ (prediction.py L274-279) |
| D3 빈 상태 | **WARN-P3** | scenarios.length===0 시 silent return null (L173). "발주기관 데이터 부족 — 시나리오 산출 불가" 안내 부재 |
| D4 loading UX | OK | 2 Suspense (PredictResult / ScenarioTable) 분리 |
| D5 에러 경로 | **OK (PartialFail)** | r.ok===false 분기 OK (L124-129). 다만 ScenarioTable 은 r.ok 체크 누락 (L170 `data?.scenarios` 만) |
| D6 기간 default | (해당 없음) | predict는 기간 파라미터 없음 (분위수만 사용) |
| D7 포맷터 | OK | fmtWon 적용 (L149, L151, L152, L194). recommended_rate_pct는 `${data.recommended_rate_pct}%` 직접 (이미 round(_,3) 처리 by backend) |
| D8 페이지네이션 | (해당 없음) | |
| D form UX | **WARN-P2** | target 분류 라벨 — `0.9 = p10 근처` `0.7 = p25 근처` `0.5 = median` `0.3 = p75`. backend 매핑 (prediction.py L112-127): `>=0.85 → p10` / `>=0.65 → p25` / `>=0.45 → median` / `else → p75`. 일치 — 정정. **그러나 page L87 텍스트 "0.9 매우 높음 (0.9 — p10 근처)" 와 "0.7 높음 (0.7 — p25 근처)" 자체는 OK** → 본 항목 OK 정정 |

**Evidence 코드**:
- `prediction/page.tsx` L116-130 (PredictResult)
- `prediction/page.tsx` L163-211 (ScenarioTable)
- `app/tools/prediction.py` L57-178 (predict_bid_price), L222-289 (compare_bid_strategies)

**개정 결과**: prediction 화면 D form UX 는 OK (페이지 라벨이 backend 매핑과 일치). 위 헤드라인 P2 "target 라벨 불일치" **취소**.

---

## 4. /qualification (적격심사 점수 계산기)

**호출 도구**: `calc_qualification_score` (qualification.py L198)

> **점검 요청 vs 실제 차이**: 요청서는 "search_bid_notices + filter (참가자격, 지역, 업종)" 으로 기술되어 있으나 실제 화면은 `calc_qualification_score` 호출 점수 계산기. **다른 화면 의도와 혼동 가능 — P1 정정 필요**.

| Dim | 결과 | Evidence |
|-----|------|----------|
| D1 extract | OK | extractMcpData. data null → "결과 없음" 표시 (L74) |
| D2 key naming | OK | `data.scores`/`data.total`/`data.max_total`/`data.ratio_pct`/`data.note` ✓ (qualification.py L249-265). scores 항목: `bid_price/experience/tech_capability/credit/management/etc` ✓. labelMap (L124-131) 6 key 일치 |
| D3 빈 상태 | **WARN-P3** | hasInput=false 시 화면에 form만 노출 (가이드 메시지 없음 — 첫 방문 사용자 학습 곤란) |
| D4 loading UX | **FAIL-P2** | Suspense 부재. Result 가 await 동기 호출되어 form submit 후 전체 화면 blank → 결과 한 번에 출력. cursor-wait 표시 없음 |
| D5 에러 경로 | **WARN-P1** | r.ok===false 분기 OK (L66-72). 그러나 input parseInt(NaN) 시 backend가 0/NaN 으로 호출 → 응답 silent 정상 (시스템 경계 검증 부재) |
| D6 기간 default | (해당 없음) | |
| D7 포맷터 | **WARN-P3** | bid_amount/base_amount input 후 결과 표시는 score (정수) 이므로 fmtWon 미사용 OK. ratio_pct 는 `${data.ratio_pct}%` 직접 (fmtRate 미사용) |
| D8 페이지네이션 | (해당 없음) | |
| D 입력 검증 | **FAIL-P2** | Field 모두 type="text". `bid_amount` input 에 "abc" 입력 후 submit 시 `parseInt("abc") = NaN` → backend 에 NaN 전달. inputMode="numeric" 또는 type="number" + min validation 미적용 |
| D 표시 | OK | passVariant 분기 (success/warning/danger) — 시각적 피드백 OK |

**Evidence 코드**:
- `qualification/page.tsx` L57-58 — `parseInt(params.bid_amount!)` (NaN 위험)
- `qualification/page.tsx` L142-166 — Field 컴포넌트 type 미지정
- `qualification/page.tsx` L102-114 — Object.entries(scores).map — management/etc는 detail 키 없음 → summarizeDetail(undefined) → "" (안전)
- `app/tools/qualification.py` L249-265 — scores 응답 schema

---

## 5. F10 차트 검은색 사각형 진단 (P0 우선)

**증상**: kwater-01.png / err-04~05.png 등에서 차트 영역이 검은색 사각형으로 표시.

**위치 추적**:
1. `frontend/src/components/charts/AgencyPricePatternChart.tsx` — Tremor `<BarChart>` 5 분위 (L26-37). `colors={["indigo"]}`
2. `frontend/src/components/charts/IndustryTrendChart.tsx` — Tremor `<BarChart>` × 2 (L29-46). `colors={["blue"]}`, `colors={["emerald"]}`
3. `frontend/src/components/charts/MarketShareChart.tsx` — Tremor `<DonutChart>` (L29-38). `colors={["blue", "cyan", "indigo", "violet", "fuchsia", "slate"]}`
4. `frontend/src/components/charts/VendorAwardChart.tsx` — Tremor `<AreaChart>` (L36-45). `colors={["blue", "emerald"]}` (G4 외 — /vendors)

**근본 원인 (강력 의심)**:
- `frontend/package.json` L25: `"@tremor/react": "^3.18.7"`
- Tremor v3 는 자체 색상 토큰 (`tremor-brand-*`, `tremor-content-*`, `tremor-background` 등) 을 Tailwind config 의 `theme.extend.colors` 에서 정의해야 함
- 본 프로젝트는 Tailwind v4 zero-config (`tailwind.config.{js,ts}` 파일 부재 — 위 ls 결과 next.config.ts 만 존재). `globals.css` 의 `@theme` 블록은 GovProcu 자체 토큰 (`--color-bg/fg/...`) 만 정의하고 **`tremor-*` 토큰 미설정**
- → Tremor 컴포넌트가 `bg-tremor-background` `text-tremor-content` `fill-tremor-brand-*` 클래스를 적용해도 Tailwind v4 가 이를 인식 못함 → 클래스 처리 누락 → 차트 SVG 가 transparent 또는 fallback color (브라우저 default = currentColor 검정 또는 미스타일링)
- BarChart/DonutChart 의 막대/도넛 fill 이 검은색 사각형으로 표시되는 정확한 시그니처

**검증 방법** (수정 단계에서):
1. 브라우저 devtools → 차트 SVG element inspect → fill 속성 확인 (`fill: currentcolor` 또는 빈 값이면 확정)
2. `bg-tremor-background` 등 클래스가 computed style 에서 적용되었는지 확인
3. Tremor migration guide (Tremor v3 → Tailwind v4) 또는 `npx @tremor/cli init` 으로 토큰 주입 필요

**픽스 권장** (별도 phase):
- Option A: `@tremor/react` 를 `recharts` 직접 사용 또는 Tremor v4 (Geist) 로 마이그레이션
- Option B: `globals.css @theme` 블록에 tremor-* 토큰 alias 추가
- Option C: tailwind.config.ts (v3 호환) 추가 + tremor preset 등록

→ **본 phase 30 범위 초과**. Diagnose 만 보고. CHECKLIST 에 P0 별도 항목 등록 권장.

---

## 6. 사용자 사례 검증 (F12 / F13)

| 사례 | 발화 | 화면 | 진단 |
|------|------|------|------|
| F12 "재정관리단" | 사용자가 발주기관명 검색 시 어떤 표기로 검색해야 하는지 학습 곤란 | /agencies?name=재정관리단 | sp.name 30일 default → 0건 가능성 높음. `sample_inst_names` 카드 (v24.2/v24.3) 가 출력되어 "국방재정관리단", "전북재정관리단" 등 실 표기 학습 가능 — UX는 적절. 단 30일 → 90일 또는 longer default 검토 |
| F13 "국방부" | 큰 기관 검색 → 기간 부족 가능 | /agencies?name=국방부 | inst_name 토큰 매칭 (award.py L324-328) — "국방부" 토큰 1개로 매칭 광범위. 30일 default 로도 다수 결과 예상. 다만 "국방부 본부" vs "국방부 산하" 구분 어려움 — 하위 조직 sample_inst_names 학습 필요. backend `agency_procurement_history` 가 W5 search_bid_notices 만 사용 → 부분 hit 우려 |

**결론**: sample_inst_names 학습 카드는 잘 동작. 그러나 **분석 대상 발주기관이 실 G2B 표기와 다를 때 사용자에게 "재검색 권장" 안내가 빈 상태에서만 표시** → has_more 적은 경우(예: notice_count=2)에도 비슷한 학습 카드를 노출하면 정확도 향상 (P3 enhancement).

---

## 7. 종합 매트릭스 (8 dim × 4 화면 = 32 cell)

| Dim | /agencies | /analytics | /prediction | /qualification |
|-----|-----------|------------|-------------|----------------|
| D1 extract | OK | OK | OK | OK |
| D2 key naming | **WARN P0** (p75 누락) | **WARN P0** (fmtBizNo 누락) | OK | OK |
| D3 빈 상태 | OK / WARN P3 (history) | OK | WARN P3 (scenarios silent) | WARN P3 (가이드 부재) |
| D4 loading UX | OK | WARN P3 (label 부재) | OK | **FAIL P2** (Suspense 부재) |
| D5 에러 경로 | WARN P1 (r.ok 미체크) | **FAIL P1** | OK (Predict) / WARN P1 (Scenario) | WARN P1 (input NaN) |
| D6 기간 default | WARN P1 (30일 짧음) | **FAIL P1** (default 부재) | N/A | N/A |
| D6 has_more | WARN P2 (history) | FAIL P2 | N/A | N/A |
| D7 포맷터 | WARN P2 (fmtRate 미사용) | OK / WARN P3 | OK | WARN P3 (fmtRate) |
| D8 페이지네이션 | FAIL (cap 30, page 없음) | N/A | N/A | N/A |
| **차트 (별도)** | **FAIL P0** (검은색 가능) | **FAIL P0** (검은색 가능) | N/A | N/A |
| **입력 검증** | OK | OK | OK | **FAIL P2** (NaN) |

---

## 8. 우선순위별 권장 fix 순서

**P0 (차단)** — 즉시 별도 phase 또는 spike:
1. **F10 차트 검은색**: Tremor v3 + Tailwind v4 호환성 문제 분석 후 마이그레이션 또는 토큰 주입. /agencies, /analytics, /vendors 모두 영향.
2. **/agencies summary_pct.p75 누락 표시**: agencies/page.tsx Stat 1줄 추가 (간단 fix).
3. **/analytics 사업자번호 fmtBizNo**: `formatBizNo` prop 또는 `name={fmtBizNo(v.biz_no)}` 1줄 fix.

**P1 (중요)**:
4. /analytics 기간 default — sp.from/sp.to undefined 시 30일 default 추가.
5. /agencies 30일 → 90/180일 default 또는 큰 기관 안내 강화.
6. r.ok 미체크 분기 추가 (analytics, prediction-Scenario).
7. /qualification — 점검 요청서 의도 (search_bid_notices+filter) vs 실제 점수계산기. 화면 의도 결정 필요.

**P2 (권장)**:
8. /qualification Field 에 inputMode="numeric" + min validation.
9. /qualification Suspense + skeleton 추가.
10. has_more / scan_coverage UI (agencies, analytics).
11. /prediction target 라벨 OK (취소).

**P3 (보완)**:
12. fmtRate 일관 적용.
13. ScenarioTable / 빈 monthly 안내 메시지.
14. analytics bizType persist.

---

## 9. 산출물 위치 + 핵심 요약 (1~3줄)

**파일**: `C:\Users\User\GovProcu\.planning\phases\30-ui-integrity-sweep\DIAGNOSIS-G4.md`

**3줄 요약**:
1. **차트 검은색 사각형 (F10) — P0**: `@tremor/react@^3.18.7` + Tailwind v4 zero-config 조합으로 `tremor-*` 토큰 부재 → /agencies BarChart, /analytics BarChart+DonutChart, /vendors AreaChart 4개 컴포넌트 영향. 별도 phase 필요.
2. **/agencies summary_pct.p75 누락 표시 + /analytics VendorLink 사업자번호 fmtBizNo 미적용 — P0** 2건은 단순 fix.
3. **/analytics 기간 default 부재 + /agencies 30일 too short — P1**: 큰 발주기관 (재정관리단/국방부 사용자 사례) false-negative 우려. /qualification 은 점검 요청 의도(search_bid_notices+filter)와 실제 코드(score 계산기) 불일치 — 화면 의도 사용자 확인 필요.
