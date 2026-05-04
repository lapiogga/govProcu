# ROUND 3 TEST REPORT

> Phase 30 Round 3 — tester-r3 종합 검증.
> 입력: ROUND-3-FIX.md (4 commits) + ROUND-2-REPORT.md § R3 권고.
> 산출: L1~L5 누적 검증 + commit별 PASS/FAIL.

## 종합 PASS/FAIL

**R3 종합: FAIL (조건부) — 차단성 회귀 1건 발견**

- 4 commits 중 3건 (`b0621eb` /bids · `703e629` /trace · `49e65fe` /search) PASS
- 1건 FAIL: `2acc4ae` /vendors P1-09 페이지네이션 — actions.ts `searchVendorsByName(..., page)` 가 backend 미지원 인자 `page`를 전달 → backend Pydantic validation error → 모든 LIKE 검색 결과 빈 응답
- TypeScript 누적 컴파일 0 에러 ✅, 영향 받지 않는 화면 회귀 0 ✅
- 이 회귀는 fixer-r3 자체 sanity check ("기존 기능 회귀 없음")가 backend 시그니처 미검증으로 누락한 결함

---

## 검증 매트릭스 (commit 별)

| Commit | 영역 | L1 | L2 | L3 | L4 | L5 | 종합 |
|--------|------|-----|-----|-----|-----|-----|------|
| `b0621eb` | /bids | PASS | PASS | PARTIAL | PASS | PARTIAL | PARTIAL PASS |
| `703e629` | /bids/trace | PASS | PASS | PASS | PASS | PASS | PASS |
| `49e65fe` | /search | PASS | PASS | N/A | PASS | PASS | PASS |
| `2acc4ae` | /vendors | PASS | FAIL | FAIL | FAIL | FAIL | **FAIL (차단성)** |

---

## L1 정적

### 변경 파일/라인 ROUND-3-FIX 표 일치
- `b0621eb`: `frontend/src/app/bids/page.tsx` 1 file / +46 / -3 ✅
- `703e629`: `frontend/src/app/bids/trace/page.tsx` 1 file / +84 / -8 ✅
- `49e65fe`: `frontend/src/app/search/page.tsx` 1 file / +4 / -2 ✅
- `2acc4ae`: 3 files / +97 / -9 (`vendors/[bizNo]/page.tsx` +21/-2, `vendors/page.tsx` +73/-7, `lib/actions.ts` +3/-0) ✅

### TypeScript 누적 컴파일
- `cd frontend; npx tsc --noEmit` → **0 에러** ✅ (4 commits 적용 후 누적)

---

## L2 논리 (코드 레퍼런스)

### Commit `b0621eb` — /bids
- P1-01 scan_coverage 추출 (`bids/page.tsx:243-247`):
  - `data?.scan_coverage_pct`, `data?.chunks_used`, `data?.endpoints_used`, `data?.scanned`, `data?.total_count` 5개 모두 추출 ✅
  - `renderCoverageBadge()` 헬퍼 (line 266-285) — `typeof scan_coverage_pct !== "number"` 시 null 반환 (graceful fallback)
  - 결과 헤더 (line 343-348) + 빈 결과 분기 (line 296-298) 모두 노출 ✅
- P1-02 buildHref deep 보존 (`bids/page.tsx:255-257`):
  - `if (sort) qs.set("sort", sort);` 기존 보존 (line 255)
  - `if (sp.deep) qs.set("deep", sp.deep);` 신규 추가 (line 257) ✅

### Commit `703e629` — /bids/trace
- P1-03 5 Stage 모두 `r.ok` 분기 ✅:
  - `StagePreSpec` line 191-193 → `<StageError n={1} label="사전규격" .../>`
  - `StageNotice` line 209-211 → `<StageError n={2} label="본 공고" .../>`
  - `StageParticipants` line 227-229 → `<StageError n={3} label="개찰 + 응찰업체" .../>`
  - `StageAwardAndNts` line 278-280 → `<StageError n={4} label="낙찰" .../>`
  - `StageNts` line 310-312 → `<StageError n={5} label="낙찰자 NTS 검증" .../>`
- `StageError` 컴포넌트 (line 400-424) — red border + warning icon + 통신 오류 라벨 + error 메시지 ✅
- P1-04 5 Stage 모두 `note={data?.note}` ✅:
  - line 202, 220, 239, 295, 321
- `Stage` 컴포넌트 (line 361-397) — `note?` prop + `<p className="...">{note}</p>` (회색, mt-1 ml-9) ✅

### Commit `49e65fe` — /search
- P1-05 redirect deep=1 (`search/page.tsx:30`):
  - `redirect(\`/bids?q=${encodeURIComponent(q)}&deep=1\`);` ✅

### Commit `2acc4ae` — /vendors
- P1-06 has_more / scan_coverage_pct UI:
  - NameSearchResults (`vendors/page.tsx:222-239`) — Badge + warning + "추가 검색 권장" ✅
  - bizNo (`vendors/[bizNo]/page.tsx:170-188`) — Badge + warning + "추가 검색 권장" ✅
- P1-09 페이지네이션 코드 구조:
  - searchParams `page?` 추가 (line 23, 25-26) ✅
  - NameSearchResults `page` prop 받음 (line 117, 122) ✅
  - `buildPageHref(newPage)` (line 158-165) ✅
  - nav 영역 (line 278-299) — 이전 / 페이지 N / 더 보기 ✅
- **FAIL**: actions.ts `searchVendorsByName` (line 270-284) — backend `search_awards_by_vendor`에 `page` 키 전달 (line 282), 그러나 backend 도구 시그니처는 page 미지원

---

## L3 backend 응답 키 정합

### `search_bid_notices(keyword="정보체계", date_from="20260104", date_to="20260504", scan_pages=5)`
- `total_count`: 321445 ✅
- `chunks_used`: 4 ✅
- `endpoints_used`: ["/BidPublicInfoService/getBidPblancListInfoServc", ...] ✅
- `scanned`: 19980 ✅
- `has_more`: 존재 ✅
- **`scan_coverage_pct`: 부재 ⚠**

응답 시간: 37.2초 (deep scan_pages=5).

> **부분 결함 (PARTIAL)**: backend `search_bid_notices`의 deep 응답에 `scan_coverage_pct` 키가 없음. frontend는 `typeof === "number"` 가드로 graceful fallback (Badge 미노출). ROUND-3-FIX § 결정 메모 7번에서 사전 명시한 fallback 동작 — 비차단성. 그러나 P1-01 사용자 임팩트 (F16 false-negative 인지)는 부분만 도달 (`chunks_used` / `scanned` / `total_count` Badge가 nested 표시이므로 함께 미노출).

### `search_awards_by_vendor(vendor_name="아이웨이브", limit=30)` (page 미포함)
- `items`: [] (default 30일 매칭 0)
- `total_count`: 0 ✅
- `scanned`: 0 ✅
- `scan_coverage_pct`: 100.0 ✅
- `returned_count`: 0 ✅
- `has_more`: false ✅

응답 시간: 0.22초.

### `search_awards_by_vendor(vendor_name="아이웨이브", limit=30, page=1)` (page=1 추가)
```
{"jsonrpc":"2.0","id":5,"result":{"content":[{"type":"text","text":
"1 validation error for call[search_awards_by_vendor]\npage\n
Unexpected keyword argument [type=unexpected_keyword_argument, input_value=1, input_type=int]
For further information visit https://errors.pydantic.dev/2.12/v/unexpected_keyword_argument"
}],"isError":true}}
```

> **차단성 회귀 (FAIL)**: backend `search_awards_by_vendor` 시그니처는 `page` 인자를 지원하지 않음 (`app/tools/award.py:460-467`):
>
> ```python
> async def search_awards_by_vendor(
>     vendor_name: str | None = None,
>     vendor_biz_no: str | None = None,
>     date_from: str | None = None,
>     date_to: str | None = None,
>     biz_type: str | None = None,
>     limit: int = 20,
> ) -> dict:
> ```
>
> `actions.ts:282` `page` 인자 전달이 항상 validation error 유발 → MCP `result.isError=true` + `content[0].text`에 에러 메시지(JSON 아님) → frontend `extractMcpData`가 `JSON.parse` 실패로 null 반환 → `data?.items=undefined` → "후보 업체 0개" / "매칭되는 후보 없음" 항상 표시.

### `vendor_profile(vendor_biz_no="7028600866")`
- `sections.awards`: 존재 ✅
  - `items`: [] (default null 기간)
  - `total_count`: 0 ✅
  - `scan_coverage_pct`: 100.0 ✅
  - `has_more`: false ✅
  - `endpoints_used`: 4개 endpoint ✅

응답 시간: 1.08초.

> bids/[bizNo] 화면은 `sections.awards?.items?.length > 0` 조건에서만 awards 섹션 렌더 (`vendors/[bizNo]/page.tsx:166`). items=[]인 상태로는 Badge 노출 분기 진입 자체가 불가. P1-06 코드는 정상이나 backend 빈 결과 케이스에서는 사용자 가시 효과 없음.

---

## L4 사용자 case retrieval

### F16 직결 — /search redirect
- `curl -I http://localhost:3000/search?q=정보체계` → **HTTP/1.1 307** + `location: /bids?q=%EC%A0%95%EB%B3%B4%EC%B2%B4%EA%B3%84&deep=1` ✅
- (P1-05 100% PASS)

### F16 직결 — /bids deep=1 화면
- `curl /bids?q=정보체계&deep=1` (HTTP 200, 89578 bytes, 응답 ~37초)
- HTML 검증:
  - `name="deep"` checkbox 존재 ✅
  - `defaultChecked` + `checked` 속성 존재 (deep=1 보존) ✅
  - `정보체계` 키워드 form value 보존 ✅
  - 페이지 이동 링크 (PageNav) `deep=1` 보존 — 응답이 1페이지뿐이라 hasMore=false → PageNav 미노출 (코드 line 328 `(page > 1 || hasMore)` 조건 미충족) — 코드 자체는 P1-02 통과. 더 큰 결과셋이 있는 키워드로는 사후 검증 권고
- "스캔 X%" Badge: **미노출** — backend `scan_coverage_pct` 키 부재 (graceful fallback)

### F2 직결 — /bids/trace 미낙찰
- `curl /bids/trace?no=R26BK01435763&ord=000` (HTTP 200, 112482 bytes, ~49초)
- HTML 검증:
  - "사전규격" / "본 공고" / "개찰 + 응찰업체" / "낙찰" / "NTS" 5 stage 라벨 모두 노출 ✅
  - "미낙찰/유찰" 텍스트 3회 노출 (Stage 4 미낙찰 분기) ✅
  - "통신 오류" 텍스트 0회 — 모든 backend 응답 r.ok=true (StageError 미진입, 정상)
  - `data?.note` 노출은 backend가 note를 보낸 stage에서만 가시 — 본 케이스에서 note 텍스트 직접 검출 안 됨 (backend가 note 미반환). 코드는 P1-04 PASS이나 데이터 사례 부재로 시각 효과 검증은 코드 분석 의존.

### vendors `[bizNo]` — /vendors/7028600866
- `curl /vendors/7028600866` (HTTP 200, 85671 bytes, ~25초)
- HTML 검증:
  - "최근 낙찰 N건" 헤더 **미노출** — `sections.awards.items.length === 0` (default null 기간 빈 결과) → 섹션 자체 미렌더
  - P1-06 has_more/scan_coverage_pct Badge 코드는 PASS이나 데이터 부재로 시각 효과 사용자 도달 0

### vendors LIKE — /vendors?name=아이웨이브
- `curl /vendors?name=아이웨이브` (HTTP 200, 73995 bytes, ~1초)
- HTML 검증:
  - "후보 업체 0개" / "매칭되는 후보 없음" 표시 ❌
  - "(낙찰 row 0건 · 스캔 0)" — backend 응답이 validation error여서 항상 0
  - "스캔 100%" Badge 미노출 — `scan_coverage_pct=undefined` (응답이 error라 키 자체 부재)
  - 페이지네이션 nav 미노출 — has_more=false + page=1이라 분기 진입 불가
- **FAIL — P1-09 backend page 미지원으로 모든 LIKE 검색 망가짐**

---

## L5 frontend 화면

| URL | HTTP | 응답 시간 | 핵심 검증 | 결과 |
|-----|------|----------|----------|------|
| `/search?q=정보체계` | 307 | <1s | Location: `/bids?q=...&deep=1` | ✅ PASS |
| `/bids?q=정보체계&deep=1` | 200 | ~37s | deep checkbox checked + 키워드 보존 | ✅ PASS |
| `/bids?q=정보체계&deep=1` | 200 | ~37s | "스캔 X%" Badge 노출 | ⚠ 미노출 (backend scan_coverage_pct 키 부재 — graceful fallback) |
| `/bids/trace?no=R26BK01435763&ord=000` | 200 | ~49s | 5 stage 라벨 + 미낙찰/유찰 표시 | ✅ PASS |
| `/bids/trace?no=R26BK01435763&ord=000` | 200 | ~49s | data?.note 노출 (있을 때) | ⚠ 코드 PASS, backend 본 케이스 note 미반환 |
| `/vendors/7028600866` | 200 | ~25s | has_more/scan_coverage_pct Badge | ⚠ 코드 PASS, awards 빈 결과로 섹션 미렌더 |
| `/vendors?name=아이웨이브` | 200 | <1s | 페이지네이션 + Badge | ❌ FAIL — 모든 호출 backend validation error |

---

## 다중 commit 누적 회귀 추적

### TypeScript 누적 컴파일
- 4 commits 모두 적용 후 `npx tsc --noEmit` **0 에러** ✅

### 영향 받지 않는 화면 (HTTP 200 회귀 0)
- `/agencies?name=조달청` → 200 ✅
- `/lookup?mode=notice&bid_notice_no=R26BK01435763` → 200 ✅
- `/analytics` → 200 ✅
- `/qualification` → 200 ✅
- `/prediction` (해당 시) — 본 라운드 변경 없음

### actions.ts 변경 회귀 검증
- `searchVendorsByName` caller grep — `vendors/page.tsx:124` 1개만 사용 (호출부 동시 수정으로 직접 회귀는 없음)
- 그러나 backend가 `page` 인자 미지원이라 **호출 자체가 항상 실패** — caller가 1개라도 차단성

---

## 회귀/결함 발견

### 차단성 회귀 1건
1. **P1-09 / commit `2acc4ae`** — `searchVendorsByName(vendorName, dateFrom, dateTo, 30, page)` 가 backend `search_awards_by_vendor`에 `page` 인자 전달, 그러나 backend 시그니처(`app/tools/award.py:460-467`)는 page 미지원
   - 영향: `/vendors?name=*` 모든 LIKE 검색 결과 빈 응답 (validation error)
   - 가시: "매칭되는 후보 없음" 항상 표시 + 스캔 0
   - 회피 양식 1: backend `search_awards_by_vendor`에 `page: int = 1` 인자 추가 + 내부 페이지네이션 로직 구현
   - 회피 양식 2: frontend actions.ts에서 page=1일 때만 backend 호출 + page=2 이상은 별도 호출 분기 (현재 backend는 단일 페이지로만 동작이라 의미 없음)
   - 회피 양식 3: 즉시 hot-fix — actions.ts에서 page 인자 제거 (P1-09 페이지네이션 기능 일시 보류) + R4에서 backend page 지원 추가 후 재도입

### 부분 결함 (비차단성)
2. **P1-01 / commit `b0621eb`** — backend `search_bid_notices` deep 응답에 `scan_coverage_pct` 키 부재 (deep scan 케이스). frontend graceful fallback (`typeof === "number"` 가드)으로 회귀 0이나 사용자 임팩트 (F16 false-negative 인지) 부분만 도달.
   - ROUND-3-FIX § 결정 메모 7번에서 사전 명시한 fallback 동작 — 사전 인지된 결함
   - 회피: backend `search_bid_notices`에 `scan_coverage_pct = (scanned / total_count) * 100` 추가 (별도 backend small fix — R4 batch 또는 별도 hot-fix)

### 데이터 의존 검증 SKIP
3. **P1-04 note 노출** — backend가 note를 반환하지 않은 케이스(R26BK01435763)에서는 시각 효과 미확인. 코드 자체는 PASS이나 데이터 케이스 부재. R4에서 default 기간 1년 확장 후 다른 trace 케이스로 재검증 권고.
4. **P1-06 has_more Badge for vendors/[bizNo]** — `sections.awards.items=[]` 케이스에서는 awards 섹션 자체 미렌더 (line 166 조건). 코드 PASS이나 시각 효과는 풍부 awards 케이스에서만 검증 가능 — R4 1년 default 후 재검증 권고.

---

## quality-monitor-r3 핸드오프

- **R3 종합: FAIL (조건부)** — 4 commits 중 1건 차단성 회귀 (`2acc4ae` P1-09 페이지네이션 backend 미지원)
- **F16 사용자 사례 영향**:
  - P1-05 (/search redirect deep=1) **PASS** — 100% 적용
  - P1-02 (/bids buildHref deep 보존) **PASS** — 코드 정합 (실 검증은 hasMore 케이스 후속)
  - P1-01 (/bids scan_coverage 노출) **PARTIAL** — frontend 코드 PASS, backend deep scan 케이스 `scan_coverage_pct` 키 부재 (사전 인지 fallback)
- **F2 사용자 사례 영향**:
  - P1-03 (Stage r.ok 분기) **PASS** — 5 stage 모두 적용 + StageError 컴포넌트 정합
  - P1-04 (note 노출) **PASS (코드)** — 데이터 케이스 부재로 시각 효과 후속 검증 권고
- **vendors / Phase 29 효과**:
  - P1-06 has_more/scan_coverage Badge **PASS (코드)** — `/vendors?name=*` 차단 회귀로 LIKE 검색에서 가시 효과 0, `/vendors/[bizNo]`는 빈 awards로 섹션 미렌더
  - P1-09 페이지네이션 **FAIL** — backend page 미지원으로 모든 LIKE 검색 항상 빈 응답
- **회귀 점검**:
  - TypeScript 누적 컴파일 0 에러 ✅
  - 영향 받지 않는 화면 (agencies/lookup/analytics/qualification) HTTP 200 ✅
  - 사용자 가시 임팩트 회귀: **/vendors LIKE 검색 차단** — 사전 R2 시점에는 정상 동작했을 가능성 (page 인자 부재) 검증 필요
- **R4 진입 적합성**: **CONDITIONAL** — P1-09 차단 회귀를 R4 진입 전 별도 hot-fix commit (또는 R3 보강 commit)으로 해소 권고:
  - 옵션 A: backend `search_awards_by_vendor`에 page 인자 추가 + 페이지네이션 로직 (선호 — 명세 P1-09 완전 충족)
  - 옵션 B: frontend actions.ts page 인자 임시 제거 (P1-09 일시 보류, R4에서 backend 강화 후 재도입)
  - 옵션 C: frontend page>1만 client-side slicing으로 처리 (현실성 낮음 — backend가 limit=30 단일 호출)
- **CHECKLIST.md 갱신 권고**: P1-09 명세 강화 — "frontend `page` 파라미터 + **backend `search_awards_by_vendor` 시그니처에 page 인자 추가**" 양 방향 수정 명시 필요
