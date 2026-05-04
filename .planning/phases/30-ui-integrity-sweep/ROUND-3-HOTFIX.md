# ROUND 3.5 HOTFIX REPORT

> Phase 30 Round 3.5 — fixer-r3.5 backend-only hot-fix.
> 입력: ROUND-3-REPORT.md § 9 R3.5 HOTFIX 권고 + ROUND-3-TEST.md § 차단성 회귀.
> 산출: backend `search_awards_by_vendor` page 인자 추가 atomic commit.

## 회귀 정의

- R3 commit `2acc4ae` (frontend `lib/actions.ts:282`) `searchVendorsByName(..., page)` → `search_awards_by_vendor` 호출에 `page` 키 전달
- backend 시그니처(`app/tools/award.py:460-467` 변경 전)에 `page` 인자 미지원 → Pydantic `unexpected_keyword_argument` validation error
- 영향: `/vendors?name=*` 모든 LIKE 검색 항상 빈 응답 + "매칭되는 후보 없음" + 스캔 0 (차단성)
- fixer-r3 자체 sanity check 누락 항목: backend 도구 시그니처 cross-check 부재

## 적용 변경 (atomic backend-only)

| 항목 | before | after | line |
|------|--------|-------|------|
| 시그니처 | `(... limit: int = 20)` | `(... limit: int = 20, page: int = 1)` | award.py:467 |
| 변수 정규화 | (없음) | `page = max(1, int(page or 1)); offset = (page-1)*limit; needed = offset+limit` | award.py:483-487 |
| 내부 변수명 충돌 | `page = 1` (G2B pageNo loop) | `page_no = 1` — 외부 인자와 충돌 회피 | award.py:517, 520, 542 |
| break 조건 | `len(matches) >= limit` | `len(matches) >= needed` | award.py:573, 575 |
| matched slice | `matches` 전체 반환 | `matches[offset : offset + limit]` | award.py:585 |
| has_more 식 | `(len(matches) >= limit) or (scanned_total < total_count)` | `(matched_total > offset + len(page_items)) or (scanned_total < total_count)` | award.py:586 |
| 응답 키 추가 | `items, total_count, scanned, scan_coverage_pct, returned_count, has_more, endpoints_used, chunks_used, filter` | + `matched_total, page, limit` (페이지네이션 컨텍스트) | award.py:589-600 |
| cache prefix | `award_vendor_v29b` | `award_vendor_v30` | award.py:459 |

## 결정 메모

1. **page 슬라이싱 방식 — 사후 slice (선택)**:
   - 옵션 A: `needed = offset + limit`만큼 누적 matches 채운 뒤 `[offset:offset+limit]` slice (선택)
   - 옵션 B: G2B pageNo 자체에 page를 매핑 (불가 — backend 도구는 chunks × biz_divs × pageNo 다중 loop 후 클라이언트 필터로 매칭 후보 선별. G2B pageNo와 사용자 page는 의미 다름)
   - 옵션 A 선택 사유: 페이지네이션 본질은 "동일 검색 결과 set의 다른 페이지". 누적 matches가 이미 chunks×biz_divs scan 후 매칭된 동일 set이므로 slice가 가장 단순·정확. 옵션 B는 G2B pageNo가 매칭 전 raw row 페이지라 사용자 의미와 미정합.

2. **has_more 재계산 — 두 분기 OR 유지**:
   - matched_total 기준: `matched_total > offset + len(page_items)` — 다음 페이지에 매칭이 더 있음
   - 스캔 커버리지 기준: `scanned_total < total_count` — 모집단 미스캔으로 false-negative 가능 (기존 의미 유지)
   - OR 결합: 둘 중 하나라도 참이면 사용자에게 "더 보기" 노출 — 기존 의미 보존 + 페이지네이션 의미 추가

3. **응답 키 추가 (`matched_total`, `page`, `limit`)**:
   - frontend가 페이지네이션 nav 정확히 표시하려면 현재 page + 누적 매칭 수 필요
   - 기존 키(`items`, `returned_count`, `has_more` 등) 의미 보존 — 회귀 0
   - frontend `vendors/page.tsx` `NameSearchResults`가 본 키들을 사용 시 추가 정확도 향상 (선택적, 기존 동작도 정상)

4. **상위호환성 — page default=1 + 신규 키는 추가만**:
   - 기존 caller 3개 (`analytics.py:63`, `lookup.py:234`, `workflow.py:147`) 모두 page 인자 미전달 → default=1 정상 동작
   - 신규 응답 키(`matched_total`, `page`, `limit`)는 추가 키이므로 기존 frontend가 무시해도 회귀 0

5. **cache prefix 갱신 — `_v29b` → `_v30`**:
   - page 도입으로 응답 본질 변경 (기존 캐시는 page 미반영). prefix 변경으로 캐시 키 분리 필수
   - empty_ttl 동작 변화도 page=N 별로 분리

6. **내부 변수 충돌 회피 — `page → page_no`**:
   - `_fetch_v4_combo` 내부 `page = 1` 변수가 외부 함수 인자 `page`와 동명 (closure 아님이므로 동작 자체는 정상)
   - 가독성·향후 수정 안전성 위해 G2B pageNo loop 변수를 `page_no`로 변경
   - line 517 (선언) + line 520 (params 사용) + line 542 (증가) 3곳 동시 변경

7. **backend 재기동 필요 여부**:
   - 본 hot-fix는 함수 시그니처 + 내부 로직 변경 → 서버 import 시 재로드 필요
   - 운영 backend 프로세스 hot-reload 가능 여부는 운영 설정 의존 (uvicorn `--reload` 등). tester-r3.5는 backend 재기동 또는 hot-reload 후 검증 필수

## Commit

- hash: **37080ec**
- 변경 파일: `app/tools/award.py` 1 file (atomic)
- 통계: +22 / -9
- 메시지: `fix(backend): P30-R3.5 search_awards_by_vendor page 인자 추가 (P1-09 회귀 회복)`

## 자체 sanity check

- [x] **Read → Edit 페어링**: award.py line 1-50, 450-700 정독 후 수정 (3 region edits)
- [x] **시그니처 hint 검증**: `python -c "from app.tools.award import search_awards_by_vendor; import inspect; print(inspect.signature(search_awards_by_vendor))"` 결과 → `(vendor_name: 'str | None' = None, vendor_biz_no: 'str | None' = None, date_from: 'str | None' = None, date_to: 'str | None' = None, biz_type: 'str | None' = None, limit: 'int' = 20, page: 'int' = 1) -> 'dict'` ✅
- [x] **page=1 호출 회귀 0**: `await search_awards_by_vendor(vendor_name='아이웨이브', limit=30, page=1)` → validation error 없음 + items=[] + returned_count=0 + page=1 + matched_total=0 (default 30일 기간 매칭 0건은 데이터 사실)
- [x] **page=2 호출 정상 동작**: `await search_awards_by_vendor(vendor_name='아이웨이브', limit=30, page=2)` → validation error 없음 + items=[] + page=2 + has_more=false (정상)
- [x] **회귀 0 검증 — 기존 caller 패턴**: `await search_awards_by_vendor(vendor_biz_no='7028600866', limit=20)` (page 미전달) → validation error 없음 + page=1 default 정상 동작
- [x] **응답 키 추가 검증**: 응답 키 set에 `matched_total`, `page`, `limit` 추가 노출 확인 (`['chunks_used', 'endpoints_used', 'filter', 'has_more', 'items', 'limit', 'matched_total', 'page', 'returned_count', 'scan_coverage_pct', 'scanned', 'total_count']`)
- [x] **frontend caller 시그니처 정합 (cross-layer cross-check, R4 강화 권고 반영)**:
  - actions.ts:282 `searchVendorsByName(...).callMcpTool("search_awards_by_vendor", { vendor_name, date_from, date_to, limit, page })` ↔ backend `search_awards_by_vendor(vendor_name, vendor_biz_no, date_from, date_to, biz_type, limit, page)` — frontend 전달 5개 인자(`vendor_name, date_from, date_to, limit, page`) 모두 backend 시그니처 키워드와 매칭 ✅
  - frontend가 미전달하는 backend 인자(`vendor_biz_no, biz_type`) — backend default=None이라 정상
- [x] **다른 backend caller 회귀 점검**: `grep search_awards_by_vendor app/` 결과 3개 caller 확인 — `analytics.py:63`, `lookup.py:234`, `workflow.py:147` 모두 page 인자 미전달 → default=1 정상 동작 (검증 1건 vendor_biz_no='7028600866' 호출로 회귀 0 확인)
- [x] **atomic commit 검증**: `git diff` 결과 `app/tools/award.py` 단일 파일 +22/-9 — frontend 미변경 ✅

## 핸드오프 메시지 (tester-r3-hotfix 앞)

backend page 인자 추가 hot-fix 완료. commit `37080ec`.

### L3 raw payload 검증 (우선)

1. `search_awards_by_vendor(vendor_name="아이웨이브", limit=30, page=1)` → MCP 호출
   - 기대: `result.isError`가 false (또는 미존재) + `content[0].text`가 JSON 문자열 + parse 후 `items[]`, `returned_count: 0`, `page: 1`, `matched_total: 0` 등 정상 응답
2. `search_awards_by_vendor(vendor_name="아이웨이브", limit=30, page=2)` → MCP 호출
   - 기대: validation error 없음 + `page: 2`, `has_more: false` (default 30일 매칭 0이므로)
3. (선택) 매칭이 풍부한 키워드 (예: `vendor_name="삼성"`)로 page=1, page=2 모두 호출 → 다른 items 반환 + page slice 동작 확인

### L4 사용자 case 검증

- `vendor_name="아이웨이브"` + 1년 기간 (`date_from`, `date_to`)으로 매칭이 1건이라도 발생하는 케이스 사전 확보 권고
- 또는 frontend `/vendors?name=아이웨이브` 페이지가 backend에 1년 default 기간 전달하는지 actions.ts 통과 검증

### L5 frontend 회귀 회복 검증

- `/vendors?name=아이웨이브` HTTP 200 + HTML 검증
  - "후보 업체 0개" → 매칭이 0이어도 backend validation error 사라짐 → "후보 업체 N개" 또는 정상 빈 결과 표시 정합
  - `scan_coverage_pct` Badge 노출 (응답에 키 존재)
  - 페이지네이션 nav: `has_more=true` 케이스에서 "더 보기" 링크 노출 (line 278-299 분기 진입)
- frontend가 backend `matched_total`/`page`/`limit` 응답 키 사용 여부 점검 — 미사용도 정상 (회귀 0)

### 회귀 점검

- backend 다른 caller (`/agencies/...`, `/vendors/[bizNo]`, `/lookup`, `/workflow`) HTTP 200 회귀 0 확인
  - 특히 `/vendors/[bizNo]` (vendor_profile → search_awards_by_vendor caller) 정상 동작 검증
- TypeScript 누적 컴파일 0 에러 (frontend 미변경이라 불변)

## quality-monitor-r3.5 또는 R4 진입 권고

- R3.5 hot-fix 완료 시 R4 진입 (CHECKLIST.md §5.4 P1-10/11/19/20/21)
- R4 fixer-r4 sanity check 강화 항목 — backend 도구 시그니처 cross-check 의무 (R3 패턴 회귀 회피)
- R4 tester-r4 — L4 winner 있는 trace + F12/F13 365일 default 케이스 사전 확보 + cross-layer 시그니처 cross-check 권고

## 제약 준수 검증

- [x] backend-only 변경 (frontend 미변경)
- [x] 1 atomic commit (`37080ec`)
- [x] 다른 도구 미변경 (award.py 단일 파일)
- [x] ROUND-3-HOTFIX.md 외 신규 파일 생성 없음
- [x] R4 작업 미진행 (P1-09 회귀 회복만)
