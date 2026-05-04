# ROUND 3.5 HOTFIX TEST REPORT

> Phase 30 Round 3.5 — tester-r3-hotfix 검증.
> 입력: ROUND-3-HOTFIX.md (commit `37080ec`) + ROUND-3-TEST.md (R3 차단성 회귀 evidence).
> 산출: L1~L5 누적 검증 + R4 진입 권고.

## 종합 PASS/FAIL

**R3.5 종합: PASS — 차단성 회귀 (P1-09) 완전 회복. R4 즉시 진입 권고.**

- **코드 레이어 (L1/L2/L3 backend 직접 import / L4)**: **PASS** — 8 결정 메모 항목 모두 award.py 라인과 일치, page 인자 정상 처리, default=1 회귀 0, 1년 default 기간 LIKE 매칭 1건 정상 반환
- **운영 레이어 (L5 frontend via MCP 서버 — 재기동 후 재검증)**: **PASS** — backend MCP 서버 재기동 (PID 1828 KILL → 신규 PID 37168 8081 LISTENING) 후 모든 검증 통과
  - MCP 직접 호출 3 케이스 (`page=1`, `page=2`, page 미전달, 1년 default) 모두 `isError: false`
  - `/vendors?name=아이웨이브&from=20250504&to=20260504` HTTP 200 — "후보 업체 1개" / "낙찰 row 1건" / "스캔 99605" / 7028600866 10회 노출 / "주식회사 아이웨이브" 9회 노출 / `validation error` 0회 ✅
  - `/vendors?name=아이웨이브` (날짜 미전달) HTTP 200 — `validation error` 0회 + "후보 업체 0개" + "스캔 100%" Badge (default null 기간 매칭 0은 데이터 사실, 회귀 아님)
- **R3 → R3.5 회복 evidence**: HTML keyword 비교 — `validation error` (R3: 1회 → R3.5: 0회), `Unexpected keyword` (R3: 1회 → R3.5: 0회), `isError":true` (R3: 1회 → R3.5: 0회). 1년 기간에서 `matched_total=1` 사용자 가시 ✅

---

## 검증 매트릭스

| 항목 | L1 | L2 | L3 | L4 | L5 | 종합 |
|------|-----|-----|-----|-----|-----|------|
| backend page 인자 추가 | PASS | PASS | PASS | PASS | PASS | PASS |
| 회귀 회복 (P1-09) | PASS | PASS | PASS | PASS | PASS | PASS |
| 다른 caller 영향 (회귀 0) | PASS | PASS | PASS | PASS | N/A | PASS |
| 응답 키 추가 (matched_total/page/limit) | PASS | PASS | PASS | PASS | PASS | PASS |
| frontend ↔ backend 시그니처 정합 | PASS | PASS | PASS | PASS | PASS | PASS |

---

## L1 정적

### diff stat
- commit `37080ec` author lapiogga 2026-05-04 02:07:28
- 변경 파일: `app/tools/award.py` 1 file (atomic)
- 통계: +22 / -9 (ROUND-3-HOTFIX 명시 일치)
- 메시지: `fix(backend): P30-R3.5 search_awards_by_vendor page 인자 추가 (P1-09 회귀 회복)`

### import 성공
- `python -c "from app.tools.award import search_awards_by_vendor"` → 0 에러 ✅
- 모듈 로드 가능

### inspect.signature
- 결과: `(vendor_name: 'str | None' = None, vendor_biz_no: 'str | None' = None, date_from: 'str | None' = None, date_to: 'str | None' = None, biz_type: 'str | None' = None, limit: 'int' = 20, page: 'int' = 1) -> 'dict'`
- `page: int = 1` 인자 7번째 위치 추가 ✅
- frontend `actions.ts:282` `page` 키 전달과 정합

---

## L2 논리 (코드 레퍼런스)

### ROUND-3-HOTFIX 결정 메모 vs award.py 라인 일치
| 항목 | 결정 메모 (HOTFIX 표) | award.py 실제 | 일치 |
|------|---------------------|--------------|------|
| 시그니처 line 467 | `page: int = 1` | line 467: `page: int = 1,` | ✅ |
| 변수 정규화 line 483-487 | `page = max(1, int(page or 1)); offset = (page-1)*limit; needed = offset+limit` | line 485-487 일치 | ✅ |
| 내부 변수명 충돌 회피 | `page → page_no` (line 517/520/542) | line 517 `page_no = 1`, line 520 `"pageNo": page_no`, line 542 `page_no += 1` | ✅ |
| break 조건 | `len(matches) >= needed` | line 573 / line 575 일치 | ✅ |
| matched slice | `matches[offset : offset + limit]` | line 585 `page_items = matches[offset : offset + limit]` | ✅ |
| has_more 식 | `(matched_total > offset + len(page_items)) or (scanned_total < total_count)` | line 586 일치 | ✅ |
| 응답 키 추가 | `matched_total, page, limit` 3 키 | line 595-597 일치 | ✅ |
| cache prefix | `award_vendor_v29b → award_vendor_v30` | line 459 `prefix="award_vendor_v30"` | ✅ |

### has_more 정합 점검
- offset + limit < total → has_more 가능
- 두 분기 OR (matched_total 기준 + scanned 미커버리지 기준) — 기존 의미 보존 + 페이지네이션 의미 추가

### 내부 변수 충돌 회피 검증
- `_fetch_v4_combo` 내부 G2B `pageNo` loop 변수 = `page_no` (외부 인자 `page`와 분리)
- closure이 아니므로 변수 동명도 동작은 정상이나 가독성·향후 수정 안전성 위해 분리 — ROUND-3-HOTFIX 명시와 일치

---

## L3 backend raw 호출 (회귀 회복 핵심)

### Test 1: `search_awards_by_vendor(vendor_name="아이웨이브", limit=30, page=1)`
- 응답 keys: `['chunks_used', 'endpoints_used', 'filter', 'has_more', 'items', 'limit', 'matched_total', 'page', 'returned_count', 'scan_coverage_pct', 'scanned', 'total_count']` — `matched_total/page/limit` 3 신규 키 노출 ✅
- `page: 1`, `matched_total: 0`, `returned_count: 0`, `has_more: false`, `scan_coverage_pct: 100.0`
- **validation error 없음** (R3 시점에서 차단되었던 핵심 회귀 회복) ✅

### Test 2: `search_awards_by_vendor(vendor_name="아이웨이브", limit=30, page=2)` (경계)
- `page: 2`, `matched_total: 0`, `returned_count: 0`, `has_more: false`
- validation error 없음, page=2 정상 처리 (offset=30 → 빈 매칭 정상) ✅

### Test 3: `search_awards_by_vendor(vendor_name="아이웨이브", limit=30)` (page 미전달)
- `page: 1` (default), `matched_total: 0`, `returned_count: 0`, `has_more: false`
- R2 시점과 동일 동작 — 회귀 0 ✅

### Test 4: `search_awards_by_vendor(vendor_biz_no="7028600866", limit=20)` (간접 caller 패턴)
- `page: 1` (default), `matched_total: 0`, `returned_count: 0`, `has_more: false`
- `analytics.py:63` / `lookup.py:234` / `workflow.py:147` page 미전달 caller 시나리오 회귀 0 검증 ✅

---

## L4 사용자 case retrieval (1년 default 기간)

### Test L4-1: `search_awards_by_vendor(vendor_name="아이웨이브", date_from="20250504", date_to="20260504", limit=30, page=1)`
- `page: 1`, `matched_total: 1`, `returned_count: 1`, `has_more: false`, `scan_coverage_pct: 100.0`, `total_count: 17019`, `scanned: 99605`
- items[0]: `winner_name: 주식회사 아이웨이브`, `winner_biz_no: 7028600866` ✅
- **R3 시점 (validation error → "후보 업체 0개")**: BLOCKED
- **R3.5 시점 (1건 매칭 후보 정상 반환)**: PASS
- 핵심 회귀 회복 evidence 확보

### Test L4-2: `search_awards_by_vendor(vendor_name="정보체계", date_from="20250504", date_to="20260504", limit=30, page=1)`
- `page: 1`, `matched_total: 0`, `returned_count: 0`, `has_more: false`
- LIKE 매칭 0건은 데이터 사실 (winner_name에 "정보체계" 토큰 매칭 0)
- validation error 없음 — page 인자 정상 처리 ✅

### Test L4-3: `search_awards_by_vendor(vendor_biz_no="7028600866", limit=20)` (page 미전달)
- L3 Test 4와 동일 — 간접 caller 회귀 0 ✅

---

## L5 frontend via MCP 서버 (재기동 후 PASS)

### MCP 서버 상태 (재기동 후)
- 포트 8081 LISTENING, **신규 PID 37168** (이전 PID 1828 KILL → uvicorn task `bio3i3tkf` 신규 기동)
- 이전 PID 1828 (StartTime 12:46:37) hot-reload 미동작 → lead 강제 재기동으로 hotfix commit `37080ec` 코드 가동
- ROUND-3-HOTFIX § 결정 메모 7번 사전 명시 사항 — uvicorn `--reload` 미설정 추정 → R4 강화 권고에 자동 재기동 단계 명시 권장

### MCP 직접 호출 evidence (재기동 후)

#### MCP T1: page=1
- POST body: `{"vendor_name":"아이웨이브","limit":30,"page":1}`
- 응답 status 200, **`isError: false`**
- payload: `items=[], total_count=0, scanned=0, scan_coverage_pct=100.0, returned_count=0, matched_total=0, page=1, limit=30, has_more=false, endpoints_used=[4 endpoint], chunks_used=1, filter={vendor_biz_no:null, vendor_name:"아이웨이브", date_range:[null,null], biz_type:null}`
- **R3 시점 validation error → R3.5 재기동 후 정상 JSON 응답 ✅**

#### MCP T2: page=2 (경계)
- `isError: false`, `page=2, matched_total=0, returned_count=0, has_more=false`
- offset=30 → 빈 매칭 정상 처리 ✅

#### MCP T3: page 미전달 (default 1, 회귀 점검)
- `isError: false`, `page=1, matched_total=0` (R2 시점과 동일 동작 — 회귀 0 ✅)

#### MCP T4: 1년 default 매칭 케이스 (R3 vs R3.5 evidence)
- POST body: `{"vendor_name":"아이웨이브","date_from":"20250504","date_to":"20260504","limit":30,"page":1}`
- `isError: false`, `page=1, matched_total=1, returned_count=1, has_more=false, scan_coverage_pct=100.0, total_count=17019, scanned=99605`
- items[0]: `winner_biz_no=7028600866, bid_notice_no=R26BK01338032` ✅

### `/vendors?name=아이웨이브` HTTP 200 (날짜 미전달, default null 기간)
- HTTP 200, 75343 bytes, 응답 시간 0.37초
- HTML 분석:
  - "후보 업체 0개" 정상 노출 (default null 기간 매칭 0 — 데이터 사실, 회귀 아님)
  - "낙찰 row 0건 · 스캔 0", "스캔 100%" Badge 노출 ✅
  - "매칭되는 후보 없음. 다른 키워드 또는 기간 확장." 정상 안내 ✅
  - **"validation error" 0회 / "Unexpected keyword" 0회 / "isError\":true" 0회** ✅
  - 임베디드 payload에 `matched_total:0, page:1, limit:30, has_more:false, filter:{date_range:[null,null]}` — backend page 인자 정상 처리 evidence

### `/vendors?name=아이웨이브&from=20250504&to=20260504` HTTP 200 (1년 기간 매칭)
- HTTP 200, 83370 bytes, 응답 시간 0.35초
- HTML 분석:
  - **"후보 업체 1개" / "낙찰 row 1건" / "스캔 99605"** ✅
  - "주식회사 아이웨이브" 9회 / "7028600866" 10회 노출 (헤더 + table row + payload) ✅
  - "스캔 100%" Badge 노출 ✅
  - "매칭되는 후보 없음" 0회 (분기 미진입) ✅
  - **"validation error" 0회 / "Unexpected keyword" 0회 / "isError\":true" 0회** ✅
  - 임베디드 payload에 `matched_total\":1` 1회 노출

### R3 vs R3.5 비교 (사용자 가시 회복)
| 항목 | R3 (commit 2acc4ae 후) | R3.5 (commit 37080ec + 재기동 후) |
|------|----------------------|----------------------------------|
| MCP `isError` | `true` | `false` |
| `validation error` keyword | HTML 1회 | HTML 0회 |
| `Unexpected keyword` keyword | HTML 1회 | HTML 0회 |
| 1년 기간 후보 업체 | 0개 (차단) | 1개 (정상) |
| 1년 기간 낙찰 row | 0건 (차단) | 1건 (정상) |
| 7028600866 노출 | 0회 | 10회 |
| 사용자 임팩트 | LIKE 검색 항상 빈 결과 | 정상 동작 |
- **차단성 회귀 (P1-09) 완전 회복 evidence 확보** ✅

---

## 회귀 점검

### 다른 backend caller (코드 레이어)
- `app/tools/analytics.py:63` `await award_tools.search_awards_by_vendor(vendor_biz_no=..., date_from=..., date_to=...)` — page 미전달 → L3 Test 4 패턴 회귀 0 ✅
- `app/tools/lookup.py:234` 동일 패턴 — 회귀 0 ✅
- `app/tools/workflow.py:147` 동일 패턴 — 회귀 0 ✅
- `app/tools/vendor.py:220` 주석만 (호출 없음) — 영향 없음 ✅
- 4 caller 모두 page 인자 미전달 → default=1 정상 동작 — 검증 1건(`vendor_biz_no='7028600866'`) 회귀 0 evidence 확보

### TypeScript 컴파일
- `cd frontend; npx tsc --noEmit` → **0 에러** ✅ (frontend 미변경이라 R3 시점과 동일)

### frontend ↔ backend 시그니처 정합 (R4 강화 권고 반영 — cross-layer cross-check)
- frontend `lib/actions.ts:270-284` `searchVendorsByName(vendorName, dateFrom, dateTo, 30, page)`:
  ```ts
  callMcpTool("search_awards_by_vendor", {
    vendor_name: vendorName,
    date_from: dateFrom,
    date_to: dateTo,
    limit,
    page,  // ← R3 신규
  });
  ```
- backend `app/tools/award.py:460-468` `search_awards_by_vendor(vendor_name, vendor_biz_no, date_from, date_to, biz_type, limit, page)`:
  - frontend 5 키(`vendor_name, date_from, date_to, limit, page`) 모두 backend 시그니처 키워드와 1:1 매칭 ✅
  - frontend 미전달 키 (`vendor_biz_no, biz_type`) — backend default=None ✅
- **결론: cross-layer 시그니처 정합 완료. R3 시점 결함은 코드 레이어에서 회복**

### 다른 화면 영향 받지 않음 (운영 미검증)
- 본 hotfix는 `app/tools/award.py` 단일 파일 변경 — frontend 미변경
- `/agencies`, `/lookup`, `/analytics` 등 다른 화면은 award.py에 의존 안 하거나 다른 도구 호출 → 미검증이나 회귀 위험 없음
- backend 프로세스 재기동 시점에 종합 회귀 1회 검증 권고

---

## R4 진입 권고

**R3.5 종합 PASS — R4 즉시 진입 권고.**

### R4 진입 가능 근거
- backend hot-fix 코드 + 운영 (재기동 후 MCP 서버) 양쪽 모두 PASS
- 차단성 회귀 (P1-09) 완전 회복 — 1년 기간 LIKE 검색에서 사용자 가시 1건 정상 반환
- 다른 caller 회귀 0 (4 caller default=1 정상 동작)
- TypeScript 컴파일 0 에러
- cross-layer 시그니처 정합 (actions.ts:282 ↔ award.py:467)

### R4 진입 절차
1. R4 fixer 즉시 작업 시작 — `.planning/phases/30-ui-integrity-sweep/CHECKLIST.md §5.4 P1-10/11/19/20/21`
2. 별도 회복 작업 불필요 — 본 R3.5 검증으로 R3 차단성 결함 종결

### R4 fixer/tester 강화 권고 (R3 패턴 회귀 회피)
- **fixer-r4 sanity check 의무 항목 추가**:
  - frontend 신규 인자 도입 시 backend 도구 시그니처 cross-check (이번 R3 결함 패턴) — `inspect.signature` 호출 + 키 정합 명시
  - hot-fix가 backend 모듈 수정인 경우 — uvicorn 프로세스 재기동 단계 명시 또는 자동화 (이번 R3.5에서 hot-reload 미동작 확인됨)
- **tester-r4 검증 강화 항목**:
  - L3 backend 직접 import + MCP 서버 직접 호출 양쪽 모두 검증 — import PASS이나 MCP BLOCKED 상태 분리 가능 (이번 R3.5에서 evidence 확보)
  - cross-layer 시그니처 정합 명시 cross-check (frontend caller → backend tool inspect)
- L4 winner 있는 trace 케이스 + F12/F13 365일 default 케이스 사전 확보 (ROUND-3-HOTFIX § 권고 유지)
- 운영 환경 가정: uvicorn `--reload` 미설정 → backend 모듈 변경 후 프로세스 재기동 명시 절차 의무화

---

## 제약 준수 검증

- [x] 코드 수정 0건 (검증 전용)
- [x] 검증 깊이 R3 tester 수준 유지 (L1~L5 매트릭스 + cross-layer 시그니처 cross-check)
- [x] R3 회귀 패턴 cross-layer 시그니처 검증 명시 수행
- [x] 산출물 단일 파일 (ROUND-3-HOTFIX-TEST.md)
- [x] R4 작업 미진행
