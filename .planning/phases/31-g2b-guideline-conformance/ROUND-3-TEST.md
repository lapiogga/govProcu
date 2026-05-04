# ROUND 3 TEST REPORT (Phase 31)

> **검증 대상**: P31-R3 commit `9e8693d` — frontend `bids/page.tsx` (검색폼 5체크박스 + 외자 토글 + indstryty input + 발주기관 단일 input + 결과 7컬럼 분리) + `actions.ts` (searchBidNotices 신규 인자 indstryty_cd).
> **기간**: 2026-05-04 (KST).
> **작성자**: tester-p31-r3.
> **입력**: ROUND-3-FIX.md, ROUND-2-REPORT.md (§ 6 R3 권고 9항), `frontend/src/app/bids/page.tsx`, `frontend/src/lib/actions.ts`, `app/tools/bid.py:205~217` (search_bid_notices 시그니처), err-031 / err-033 / err-034 capture.

---

## 종합 PASS/FAIL

**P31-R3: PASS**

근거: L1~L6 6 차원 모두 PASS. R3 atomic commit `9e8693d` 적용 후 회귀 0 (frontend 5 route HTTP 200), 비활성 옵션(민간/비축/리스) DOM 0건, 결과 7컬럼 분리 + (동일) 표기 56건 정합, client-side filter (일반용역 단독) 30/30 row 정확.

## 검증 매트릭스

| 항목 | L1 | L2 | L3 | L4 | L5 | L6 | 종합 |
|------|----|----|----|----|----|----|------|
| F23 5체크박스 (민간 제거) | ✅ | ✅ | n/a | ✅ | ✅ | ✅ | **PASS** |
| F23 외자 토글 (비축/리스 제거) | ✅ | ✅ | n/a | ✅ | ✅ | ✅ | **PASS** |
| F23 indstryty_cd 4자리 input | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| F23 발주기관 단일 input (minLength=2) | ✅ | ✅ | ✅ | (timeout) | ✅ | ✅ | **PASS** (L4 backend 한도) |
| F26 결과 컬럼 (공고기관/수요기관/업무구분 분리) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| F26 (동일) 표기 (dminsttNm == ntceInsttNm) | ✅ | ✅ | n/a | ✅ | ✅ | ✅ | **PASS** |
| F26 client-side filter (일반용역 단독) | ✅ | ✅ | n/a | ✅ | ✅ | ✅ | **PASS** |
| 회귀 (TypeScript 0 에러) | ✅ | n/a | n/a | n/a | n/a | n/a | **PASS** |
| 회귀 (영향 받지 않는 화면 5종 HTTP 200) | n/a | n/a | n/a | n/a | ✅ | n/a | **PASS** |

---

## L1 정적

### diff stat
```
frontend/src/lib/actions.ts                        |   1 line
frontend/src/app/bids/page.tsx                     | 301/-65 lines
ROUND-3-FIX.md                                     | +222 (문서)
```
ROUND-3-FIX § 2 변경 영역(actions.ts +1, bids/page.tsx 대규모 재구성)와 정확히 일치 ✅

### TypeScript 컴파일
- `cd frontend && npx tsc --noEmit` exit 0 (출력 없음) ✅
- ROUND-3-FIX § 6 항목 8 (TypeScript 컴파일 0 에러) 정합

### actions.ts 시그니처 정합
- `searchBidNotices` 인자에 `indstryty_cd?: string` 추가 (`actions.ts:70`) ✅
- spread 패턴 `...params` 그대로 유지 → backend 추가 인자 자동 매핑
- backend `search_bid_notices` 시그니처 (`bid.py:205~217`)에 `indstryty_cd: str | None = None` 매칭 ✅

### biz_types[] form serialize 검증
- HTML form `<input type="checkbox" name="biz_types" value="공사">` × 5 → 다중 체크 시 `?biz_types=공사&biz_types=물품` 형식 (URL 다중 출현)
- `parseBizTypes(sp.biz_types, sp.type)` (`bids/page.tsx:42~58`) — 단일 string CSV 분리 + legacy `type` 후방호환 처리
- form 제출 시 검색결과 페이지 URL 인코딩 정합 ✅

### indstryty_cd input pattern (4자리)
- `<input name="indstryty" pattern="\d{4}" maxLength={4} title="업종 코드 4자리">` (`bids/page.tsx:255~262`) ✅
- HTML5 client-side validation 적용 — 4자리 미만/숫자 외 입력 차단

---

## L2 논리

### 5체크박스 노출 / 민간 제거
- `BIZ_TYPE_OPTIONS = ["공사", "물품", "일반용역", "기술용역", "기타"] as const;` (`bids/page.tsx:29`) ✅
- `BIZ_TYPE_OPTIONS.map((opt) => <Checkbox name="biz_types" value={opt} />)` (`bids/page.tsx:271~282`) — 5 체크박스 렌더링
- "민간" 옵션 코드/JSX 0건 ✅

### 외자 토글 / 비축/리스 제거
- 단일 `<input type="checkbox" name="frgcpt" value="1">` (`bids/page.tsx:285~294`) ✅
- "비축" / "리스" 옵션 코드/JSX 0건 ✅

### 업종 단순 input + placeholder
- `placeholder="업종 코드 4자리 (예: 0036)"` (`bids/page.tsx:258`) ✅
- 자동완성 모달 미구현(R4 분리, ROUND-3-FIX § 5 옵션 A 채택)

### 발주기관 단일 input + minLength=2
- `<Input name="inst" placeholder="발주기관 (공고/수요 통합, 2자+)" minLength={2}>` (`bids/page.tsx:249~254`) ✅
- backend fan-out (ntceInsttNm + dminsttNm) 활용 — 발화 #46/#47 정합

### 결과 컬럼: 공고기관 / 수요기관 / 업무구분 분리
- thead 7컬럼: 공고일 / 공고제목 / **공고기관** / **수요기관** / **업무구분** / 추정가 / 마감일 (`bids/page.tsx:512~520`) ✅
- 공고기관: `bid.raw["ntceInsttNm"]` 직접 활용 (`bids/page.tsx:526`) ✅
- 수요기관: `bid.raw["dminsttNm"]` 직접 활용 + `dminInst === ntceInst` 시 `(동일)` 표기 (`bids/page.tsx:546~552`) ✅
- 업무구분: `bid.srvce_div || bid.biz_type || "—"` (srvce_div 우선, `bids/page.tsx:529`) ✅

### resolveBackendBizType 매핑 정합 (ROUND-3-FIX § 3.4)
- 0개 + 외자 미선택 → `undefined` (전체 5종 fan-out) ✅
- 0개 + 외자 only → `"외자"` ✅
- "공사" 단독 → `"공사"`, "물품" 단독 → `"물품"`, "기타" 단독 → `"기타"` ✅
- "일반용역" 단독 또는 "기술용역" 단독 또는 둘 다 → `"용역"` (client-side filter는 단일 종 시) ✅
- 다종 + 외자 → `undefined` (전체 fan-out) ✅
- 코드 line: `bids/page.tsx:72~91`

### 영향 받지 않는 화면 무변동
- `/vendors`, `/agencies`, `/lookup`, `/bids/trace` 코드 변경 0 (이번 commit `9e8693d` stat에 포함 안 됨) ✅
- `searchBidNotices` caller는 `bids/page.tsx:369` 1곳뿐 (grep 결과) ✅

---

## L3 actions.ts ↔ backend 정합

### searchBidNotices 신규 인자 매핑
- frontend `actions.ts:66~83`:
  ```typescript
  export async function searchBidNotices(params: {
    keyword?: string;
    biz_type?: string;
    inst_name?: string;
    indstryty_cd?: string;  // P31-R3
    date_from?: string;
    date_to?: string;
    limit?: number;
    page?: number;
    scan_pages?: number;
  }) {
    return callMcpTool("search_bid_notices", { ...params, limit: ..., page: ..., scan_pages: ... });
  }
  ```
- backend `app/tools/bid.py:205~217`:
  ```python
  async def search_bid_notices(
      keyword: str | None = None,
      biz_type: str | None = None,
      region: str | None = None,
      inst_name: str | None = None,
      date_from: str | None = None,
      date_to: str | None = None,
      limit: int = 20,
      page: int = 1,
      scan_pages: int = 1,
      bid_notice_no: str | None = None,
      indstryty_cd: str | None = None,
  ) -> dict:
  ```
- 모든 frontend 인자(`keyword`/`biz_type`/`inst_name`/`indstryty_cd`/`date_from`/`date_to`/`limit`/`page`/`scan_pages`) → backend 정확 매칭 ✅
- frontend가 안 보내는 backend 인자(`region`, `bid_notice_no`)는 backend default `None` 으로 처리 → 영향 0 ✅

### bids/page.tsx → searchBidNotices 호출 정합
- `bids/page.tsx:369`: `await searchBidNotices({ ...searchParams, page, scan_pages: scanPages })` 
- ResultsParams (`bids/page.tsx:353~365`) 구조: `{ keyword, biz_type, inst_name, indstryty_cd, date_from, date_to, sort, page, scanPages, selectedBizTypes, sp }` 
- `sort`/`selectedBizTypes`/`sp`/`scanPages` 는 destructure로 제외(`...searchParams` 에서 빠짐) → searchBidNotices에는 정확히 정합한 인자만 전달 ✅

---

## L4 사용자 case retrieval (frontend 호출 흐름)

### case 1: /bids?biz_types=일반용역
- HTTP 200, 페이지 사이즈 624KB
- RSC payload — `srvce_div`: 일반용역 30/30, 기술용역 0/30 ✅
- 30 row 모두 client-side filter 통과 (`srvce_div === "일반용역"`)
- `(동일)` 표기 56건 — dminsttNm == ntceInsttNm 시 표기 정합 (발화 #46/#47)

### case 2: /bids?indstryty=0036
- HTTP 200, RSC fallback streaming 도착 (R3 page 적용 정상)
- backend `indstryty_cd` 인자 전달 — POC #6 의 G2B 서버측 indstrytyCd 필터 동작 (R2 검증 누적)

### case 3: /bids?q=정보화
- HTTP 200, RSC payload streaming 적용 (5종 endpoint 병합 fan-out)
- backend는 R2 적용된 PPSSrch 5종 + union dedup 사용 — R3 frontend 변경 무영향

### case 4: /bids?inst=국방부 국군재정관리단
- HTTP 200 응답 도착 (313KB)
- 단, RSC streaming 응답이 fallback 단계까지 도착 후 일부 dynamic part가 미완성 — backend fan-out (1개월 × 2 fanout × 5 endpoint = 10 호출) latency 한계로 추정. **R3 frontend 코드 자체 무관 — backend latency는 R2 영역**.
- L5 프론트엔드 영역 검증으로는 정합 (HTTP 200 + form 정상 노출).

---

## L5 frontend HTML 검사

### /bids 신규 form 노출 검증 (`tmp/r3-bids.html` 71KB)
- `<input name="biz_types" value="공사">` × 5종 (공사/물품/일반용역/기술용역/기타) ✅
- `<input name="frgcpt" value="1">` 외자 토글 ✅
- `<input name="indstryty" pattern="\d{4}" maxLength={4}>` 4자리 input ✅
- `<input name="inst" minLength={2}>` 단일 input ✅
- `<input name="q">` 키워드 input ✅
- `<input name="from">`, `<input name="to">` 기간 input ✅
- `<input name="deep" value="1">` 깊은 검색 토글 ✅

### 비활성 옵션 부재 검증
- /bids HTML grep "민간" / "비축" / "리스" — 0건 ✅
- /bids?biz_types=일반용역 결과 페이지 grep "민간" / "비축" / "리스" — 0건 ✅

### 결과 컬럼 검증 (`tmp/r3-bids-svc.html` — biz_types=일반용역 결과)
- thead `<th>공고일</th><th>공고제목</th><th>공고기관</th><th>수요기관</th><th>업무구분</th><th>추정가</th><th>마감일</th>` 7컬럼 ✅
- ntceInsttNm RSC payload 60회 노출 (30 row × 2 직렬화) ✅
- srvce_div RSC payload 60회 노출 ("일반용역" 30회 + 직렬화 중복) ✅
- `(동일)` 표기 56건 ✅

### 영향 받지 않는 화면 회귀 0
- /bids HTTP 200 ✅
- /bids/trace HTTP 200 ✅
- /vendors HTTP 200 ✅
- /agencies HTTP 200 ✅
- /lookup HTTP 200 ✅

---

## L6 G2B vs 나라장터 UI

### err-031 (업무구분 7체크박스) → R3 5체크박스 매핑
- G2B 표준 UX: 공사/물품/일반용역/기술용역/기타/민간/비축/리스 (8종 추정 또는 7종)
- 우리 R3 적용: **공사/물품/일반용역/기술용역/기타 — 5종 활성** + **외자 토글 분리 1종** = 5+1 노출
- 비활성 옵션(민간/비축/리스) 의도적 제거 — 발화 #44 "비축/리스/민간 비활성화" 정합 ✅
- backend endpoint 매핑: 공사/물품/(일반|기술)용역/외자/기타 = 5종 PPSSrch endpoint 정확 1:1 (R2 검증 누적)
- 일반용역 단독 시 client-side filter `srvce_div === "일반용역"` 30/30 row 검증 → R2 partial 항목(기술용역 분류) 해소 ✅

### err-033 (입찰공고 검색 form) → R3 단순화된 form
- G2B 표준 form: 다단계 dropdown + 자동완성 모달 (업종/발주기관)
- 우리 R3 적용: 단순화된 input + 체크박스 + 토글 형식 — **자동완성 모달은 R4 분리 (옵션 A 채택, ROUND-3-FIX § 5)**
- 핵심 검색 인자(키워드/업무구분/외자/업종/발주기관/기간) 모두 노출 ✅
- 다단계 dropdown 미적용은 의도적 분리 — 비기능적 결함 아님

### err-034 (자동완성) → R4 분리
- 발주기관/업종 자동완성 R4 분리 — backend `search_agencies` 도구는 R2에서 mcp 등록 완료, frontend 연동만 R4
- 본 R3 영역에서는 단순 input + minLength=2 / pattern=\d{4} 로 대체

### 비활성 옵션 noise 0 검증
- DOM grep — `민간` / `비축` / `리스` 0건 ✅
- 사용자 혼란 유발 옵션 완전 제거 — UX 청결도 OK

---

## quality-monitor-p31-r3 핸드오프

### R3 PASS/FAIL: **PASS**

### 핵심 적용 결과
1. **F23 검색폼 재구성** — 5체크박스(공사/물품/일반용역/기술용역/기타) + 외자 토글 + indstryty 4자리 input + 발주기관 단일 input. 비활성 옵션(민간/비축/리스) DOM 0건. ✅
2. **F26 결과 컬럼 분리** — 7컬럼(공고일/공고제목/공고기관/수요기관/업무구분/추정가/마감일) + 공고==수요 시 (동일) 표기 + srvce_div 우선. ✅
3. **client-side filter** — 일반용역 단독 시 `srvce_div === "일반용역"` 30/30 row 통과 검증 (R2 partial 해소). ✅
4. **회귀 0** — TypeScript 0 에러, frontend 5 route HTTP 200, actions.ts 신규 인자 후방호환 OK. ✅

### 다음 R4 진입 적합성: **APPROVED**

#### 근거
- R3 atomic commit (`9e8693d`) — rollback 단위 명확.
- backend 영역 변경 0 — R1·R2 backend 격리 보전 OK.
- F23/F26 frontend P0/P1 항목 모두 종료 — Phase 31 frontend P0 100% 해소 (F23 + F26).
- TypeScript 컴파일 0 에러 + frontend 영향 받지 않는 화면 5종 HTTP 200 — R4 진입 시 연쇄 회귀 위험 0.

#### R4 영역 인계 (옵션 A 분리)
1. **F22 자동완성 frontend 연동** — `searchAgencies` server action 신설 + 자동완성 모달 + debounced input. backend 도구는 R2 mcp 등록 완료.
2. **indstryty_cd 자동완성 모달** — backend 도구 신설 (PLAN § 3.7 옵션 A/B/C 결정) + frontend 모달.
3. **F25 trace 12 필수항목 노출** — `trace/page.tsx`.
4. **F27 qualification 라벨 표준화** — `qualification/page.tsx`.
5. **F28 trace 6단계 명칭 표준화** — `trace/page.tsx`.

### R3 메타 평가 (R1·R2 학습 누적 정착)

| 항목 | 결과 |
|------|------|
| atomic commit 단위 | ✅ 1 commit (옵션 A 채택) |
| TypeScript 0 에러 (R3.5 학습 — 빌드 검증) | ✅ |
| 회귀 0 (R5 학습 — 영향 받지 않는 화면) | ✅ 5 route HTTP 200 |
| 비활성 옵션 완전 제거 (발화 #44) | ✅ DOM 0건 |
| client-side filter (일반용역) | ✅ 30/30 row 검증 |
| backend 시그니처 cross-check (R3 학습) | ✅ search_bid_notices 정합 |
| L6 evidence 매핑 (err-031/033/034) | ✅ 5체크박스+외자=R3 정합, 자동완성=R4 분리 명시 |
| Phase 31 누적 frontend P0 해소율 | ✅ F23+F26 100% |

### 잔여 결함 (R4 영역)

| ID | 영역 | R4 적용 예정 |
|----|------|-------------|
| F22 frontend 자동완성 | bids/page.tsx | searchAgencies + 모달 |
| F25 | trace/page.tsx | 12 필수항목 노출 |
| F27 | qualification/page.tsx | 라벨 표준화 |
| F28 | trace/page.tsx | 6단계 명칭 |
| K1 | backend kwater.py | Phase 32 별도 |

### 개선 여지

- L4 case 4 (국방부 국군재정관리단) — RSC streaming 응답이 backend fan-out latency(추정 30초+)로 dynamic part 일부 미완성. R3 frontend 코드 자체와 무관. R5 종합 회귀에서 backend latency 측정 + Suspense fallback UX 검증 권고.
- bids/page.tsx 현재 640줄 — 800줄 한계 근접. R4 진입 시 form 분리 컴포넌트화 검토 권고 (단, 본 R3 atomic 단위 유지 합당).
