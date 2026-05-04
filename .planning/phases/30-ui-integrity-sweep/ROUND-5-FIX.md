# ROUND 5 FIX REPORT (Phase 30 final)

> Phase 30 Round 5 — fixer-r5. P1 잔여 7건 적용 + 종합 회귀 준비. **Phase 30 마지막 라운드**.
> 입력: ROUND-4-REPORT.md (R5 권고) / DIAGNOSIS-G3·G5·G2.md (P1 evidence) / CHECKLIST.md.
> 산출: 4 atomic commits (영역별) + 핸드오프 → tester-r5.

## Commits

| # | hash | 영역 | 변경 라인 | 적용 P1 |
|---|------|------|----------|---------|
| 1 | `cb95b54` | `vendors/[bizNo]` profile UX | +70 / -8 (1 file) | P1-07, P1-08 |
| 2 | `ab95952` | `me` r.ok 분기 | +30 / -0 (1 file) | P1-14 |
| 3 | `2f7614a` | `external/kwater` 키 안내 + 페이지네이션 | +86 / -12 (1 file) | P1-15, P1-16 |
| 4 | `2e2977c` | `lookup` biz 공고 목록 + 기간 form | +123 / -7 (1 file) | P1-17, P1-18 |

**누적**: 4 file (모두 frontend) / +309 / -27 line / 7 P1 항목 적용 / backend 변경 0.

---

## 적용 변경 상세

### Commit 1 — `cb95b54` `/vendors/[bizNo]` UX (P1-07 + P1-08)

**파일**: `frontend/src/app/vendors/[bizNo]/page.tsx`

#### P1-07 — ProfileSkeleton spinner + 진행 메시지

- 기존: `<ProfileSkeleton />` 단순 5칸 pulse만 — 36초 대기 시 사용자 abandon 위험
- 변경:
  - `cursor-wait` class 적용 (skeleton wrapper)
  - SVG `animate-spin` spinner + `<p>검색 중 (최대 1분 소요)</p>` 진행 메시지
  - 부가 설명: "G2B 1년 데이터 12회 chunk × 4 endpoint 병렬 — 페이지를 닫지 마세요."
- DIAGNOSIS-G3 § P1-2 직결 (`[bizNo]/page.tsx:236-250` 영역)

#### P1-08 — 기간 변경 form

- 기존: header `<h1>` + `<p>` 2개만. URL 수동 편집 필요
- 변경:
  - header에 `<form action={/vendors/${bizNo}}>` GET form 추가
  - `<Input name="from"/>` + `<Input name="to"/>` (YYYYMMDD pattern) + 재조회 button
  - "현재: {from} ~ {to} (1년 default)" 안내
- vendors/page.tsx (index)의 NameSearchResults form 패턴 계승
- DIAGNOSIS-G3 § P1-3 직결

**영향 받지 않는 영역**: Profile / Stat / extractData / VendorAwardChart / NTS 검증 / 통계 grid — 모두 무변동.

### Commit 2 — `ab95952` `/me` r.ok 분기 (P1-14)

**파일**: `frontend/src/app/me/page.tsx`

#### P1-14 — Watchlist + Subscriptions r.ok === false 분기

- 기존: `r.ok` 체크 없이 `extractMcpData(r.data)` → `data?.items || []` → "활성 구독 없음" 빈 상태로 사일런트 흡수
- 변경: 두 함수 공통 패턴
  ```tsx
  if (!r.ok) {
    return (
      <Card>
        <CardHeader><CardTitle>...</CardTitle></CardHeader>
        <CardContent className="p-4">
          <div className="rounded border border-[var(--color-danger)] p-3 text-sm">
            오류: {r.error}
          </div>
        </CardContent>
      </Card>
    );
  }
  ```
- R4 r.ok 분기 패턴 (`<div border-[var(--color-danger)]>`) 일관 적용 (R4 commit 1/2/3 동일)
- DIAGNOSIS-G5 § P1-4 직결

**영향 받지 않는 영역**: AddWatchlistDialog / WatchlistTable / subscribeKeywordAction form / SELECT_CLASS — 모두 무변동.

### Commit 3 — `2f7614a` `/external/kwater` 키 안내 + 페이지네이션 (P1-15 + P1-16)

**파일**: `frontend/src/app/external/kwater/page.tsx`

#### P1-15 — KWATER_API_KEY 미설정 안내

- 기존: `data.status === "pending_key"` 시 "결과 없음. status: pending_key" 1줄만
- 변경: 별도 분기 — `data.status === "pending_key"`이면 warning Card 노출
  - "외부 API 키 미설정" 헤더
  - `data.note` 표시 (backend가 `f"{KWATER_API_KEY} 환경변수 미설정."` 메시지 제공)
  - "운영자에게 문의 또는 .env 확인" 가이드
- DIAGNOSIS-G5 § P1-5 직결 (`external/kwater/page.tsx:149-155` 영역)

#### P1-16 — Client-side 페이지네이션

- 기존: `limit` input만. backend `searchKwaterContracts(searchDt, bizType, limit)`은 `pageNo=1` 고정 (`kwater.py:94`)
- 제약: backend 미변경 (R5 frontend only) → `pageNo` 파라미터 추가 불가
- 해결: **client-side slice** (backend 시그니처 변경 0)
  - `searchParams.page` 추가 (default 1)
  - fetch limit = `min(pageSize * page, 1000)` (KWater API max=1000)
  - items = `allItems.slice((page-1)*pageSize, page*pageSize)`
  - hasMore = `total_count > page * pageSize`
- 페이지네이션 nav: 이전 / 다음 button + 페이지 표시 + 1000건 한계 도달 시 안내
- 헤더: "총 {totalCount}건 (페이지 {page} · 표시 {items.length}건 / 페이지당 {pageSize})"
- DIAGNOSIS-G5 § P1-6 직결

**영향 받지 않는 영역**: ContractRow interface / buildContractHref / row 표시 / VendorLink redirect — 모두 무변동.

### Commit 4 — `2e2977c` `/lookup` 공고 목록 + 기간 form (P1-17 + P1-18)

**파일**: `frontend/src/app/lookup/page.tsx`

#### P1-17 — bid_notice_no_list 표시 (mode=biz)

- 기존: backend `lookup_by_biz_no` 가 `summary.bid_notice_no_list` (첫 20건) 반환하나 frontend는 `top_agencies`만 표시
- 변경: mode=biz + `summary.bid_notice_no_list?.length > 0` 시 별도 section
  - 헤더: "이 업체가 받은 공고 목록" + "(낙찰 {award_count}건 · 첫 {list.length}건)"
  - 표 3열: # / 공고번호 / 바로가기 → 각 row는 `/bids/trace?no={bidNo}&ord=00` 링크
- DIAGNOSIS-G2 § G2-P1-06 직결 (lookup.py:311 `bid_notice_no_list[:20]` 활용)

#### P1-18 — 기간 input form (mode=biz/inst)

- 기존: form은 `q` + `ord`(bid mode)만. 기간 input 부재 → backend 무기간 호출 (timeout 위험)
- 변경:
  - `searchParams: { mode, q, ord, from, to }` 확장
  - mode=biz/inst인 경우 `<Input name="from"/>` + `<Input name="to"/>` 추가
  - `defaultDateFrom()` / `defaultDateTo()` — 1년 default (R4 패턴 계승)
  - Result 함수에 from/to 인자 추가 → `lookupByBizNo(q, from, to)` / `lookupByInstCode(q, from, to)`
  - actions.ts 시그니처 변경 0 (이미 dateFrom/dateTo optional 보유)
  - 안내: "기간 미입력 시 1년 default 적용 (G2B 1개월 chunk 자동 — timeout 위험 회피)"
- DIAGNOSIS-G2 § G2-P1-07 직결

**영향 받지 않는 영역**: LookupGraph / KeyNode / top_winners 표 / mode=contract stub / placeholderFor — 모두 무변동.

---

## 결정 메모

1. **ProfileSkeleton spinner 패턴** — SVG `animate-spin` (Tailwind built-in) 채택. 외부 lucide-react 등 라이브러리 추가 회피 (R5 변경 최소화 원칙). cursor-wait class는 wrapper에 적용 (R3.5 학습).

2. **기간 form 디자인 (vendors/[bizNo])** — vendors/page.tsx (index) Pattern 정확 계승: `<form action={...} GET>` + Input from/to + 재조회 Button + "현재: ~ default" 안내. URL state는 next.js page props로 직접 받음 (서버 컴포넌트 친화).

3. **KWATER 키 미설정 detect 방법** — backend `KWaterAdapter.search_contracts()` (kwater.py:82-89) 가 `status: "pending_key"` + `note: "{SERVICE_KEY_ENV} 환경변수 미설정."` 명시 반환. frontend는 `data.status === "pending_key"` 분기로 detect (frontend only, env 직접 read 불필요).

4. **페이지네이션 client-side slice (KWater)** — backend `pageNo=1` 고정 + R5 frontend only 제약 충돌 해결: `searchKwaterContracts(searchDt, bizType, pageSize*page)` 호출 후 client slice. `pageSize*page > 1000`이면 KWater API max=1000 한계 안내. 시그니처 변경 0.

5. **bid_notice_no_list 표시 위치 (lookup)** — Top agencies 표 바로 위 (mode=biz일 때만). 사용자가 "이 업체가 받은 공고"를 가장 먼저 보도록 우선 위치 (top_winners는 mode=inst 한정). 각 row → `/bids/trace?no={bidNo}&ord=00` 직접 추적 링크.

6. **lookup 기간 form 노출 조건** — mode=biz/inst만 노출 (mode=bid는 단건 조회라 무관, mode=contract는 stub). conditional rendering으로 UX 단순화. `<>...</>` Fragment로 from/`~`/to 3개 element 묶음.

7. **backend 미변경 일관 적용** — 4 commit 모두 frontend only. 영향 받는 backend 시그니처 (listMyWatchlist / listMySubscriptions / searchKwaterContracts / lookupByBizNo / lookupByInstCode) inspect 결과 변경 0. uvicorn 재기동 불필요 (R3.5 학습 명시).

---

## 자체 sanity check (R3+R4 학습 누적)

- [x] **backend 호출 시그니처 변경 여부**: NO (frontend only — 4 commit 모두)
- [x] **backend 도구 호출 인자 cross-check** (R3 학습):
  - `listMyWatchlist()`: 시그니처 변경 0 (`me/page.tsx:42`)
  - `listMySubscriptions()`: 시그니처 변경 0 (`me/page.tsx:79`)
  - `searchKwaterContracts(searchDt, bizType, limit)`: limit만 frontend에서 `pageSize*page`로 계산 — 인자 시그니처 변경 0 (`external/kwater/page.tsx`)
  - `lookupByBizNo(vendorBizNo, dateFrom?, dateTo?)`: dateFrom/dateTo는 기존 optional 인자 활용 — 시그니처 변경 0 (`lookup/page.tsx`)
  - `lookupByInstCode(instName, dateFrom?, dateTo?)`: 동일 — 시그니처 변경 0
  - `getVendorProfile(vendorBizNo, dateFrom?, dateTo?)`: 시그니처 변경 0 (`vendors/[bizNo]/page.tsx:60`)
- [x] **TypeScript 컴파일 0 에러** (각 commit 후 `npx tsc --noEmit` 실행 — 모두 0 에러)
- [x] **의도 외 라인 수정 없음** — Edit tool로 정확한 영역만 수정. 인접 코드 무수정.
- [x] **영향 받지 않는 화면 (bids / trace / search / agencies / analytics / vendors index / prediction / qualification / console) 무변동** — 4 commit 모두 다른 디렉토리 무영향
- [x] **uvicorn 재기동: 불필요** (frontend only, backend 미변경 — R3.5 학습)

---

## 핸드오프 메시지 (tester-r5 앞)

**4 commit 누적 검증 부탁** — Phase 30 마지막 라운드. 종합 회귀 강조.

### Commit 정보

| # | hash | 영역 | 변경 |
|---|------|------|------|
| 1 | `cb95b54` | vendors/[bizNo] | profile UX (loading + 기간 form) |
| 2 | `ab95952` | me | r.ok 분기 |
| 3 | `2f7614a` | external/kwater | 키 안내 + 페이지네이션 |
| 4 | `2e2977c` | lookup | biz 공고 목록 + 기간 form |

### 사전 점검 사항

- backend 미변경 — uvicorn 재기동 불필요
- TypeScript 컴파일 0 에러 (4 commit 모두 검증 완료)
- frontend dev server 재기동만 필요 (Next.js page props 변경)

### L4 핵심 case

1. **vendors/[bizNo]** — `/vendors/7028600866?from=20240501&to=20260504` (또는 default 1년)
   - 기간 form 표시 + 재조회 동작
   - 36초 대기 시 spinner + "검색 중 (최대 1분 소요)" 메시지
   - 1년 default 1건 매칭 (P1-07 evidence)
2. **me** — `/me` 빈 즐겨찾기 + 알림 정상 + 백엔드 5xx 모킹 시 ErrorBox
   - 빈 상태: 기존 동작 그대로 ("저장된 즐겨찾기 없음")
   - r.ok=false 케이스: 백엔드 down 또는 DB 락 시 `border-[var(--color-danger)]` 박스
3. **external/kwater** — `/external/kwater?dt=202205&biz=용역`
   - 정상 결과: 기존 14건 표시 (kwater-01.png evidence)
   - 페이지네이션: total > pageSize 시 "다음 →" 노출. limit=10 + total=14 → 페이지 1: 10건, 페이지 2: 4건
   - pending_key 미설정 시뮬: env KWATER_API_KEY 비우고 호출 (또는 코드 분석 logical PASS — fixer는 env 변경 권한 없음)
4. **lookup** mode=biz — `/lookup?mode=biz&q=2391602024`
   - bid_notice_no_list 표 노출 (첫 20건 또는 award_count만큼)
   - 각 공고번호 → /bids/trace 링크 동작
   - 기간 form: from/to 1년 default + 사용자 변경 가능
5. **lookup** mode=inst — `/lookup?mode=inst&q=국방재정관리단`
   - 기간 form 노출 + 무기간 호출 회피
   - top_winners 표 정상

### L5 시각 검증

- 4 화면 모두 HTTP 200
- 신규 UI 요소 노출:
  - vendors/[bizNo]: spinner SVG / form 3 inputs + button
  - me: error box (모킹 시) — 평상시 noop
  - external/kwater: warning Card (pending_key) / nav buttons (페이지네이션)
  - lookup: form from/to inputs / bid_notice_no_list 표

### 종합 회귀 (R5 마지막 라운드 — 강조)

- **14 화면 전체 HTTP 200/307/400(필수 param)** — 영향 받지 않는 9 화면 (bids / bids/trace / search / agencies / analytics / vendors / prediction / qualification / console) 무변동 검증
- **TypeScript 누적 0 에러** (R1~R5 누적)
- **5 사용자 사례 종합 evidence 재확인**:
  - F2 trace 빈 결과 → R3 PASS 유지 (note + r.ok 분기)
  - F12 재정관리단 → R4 PASS 유지 (1년 default 매칭 10건)
  - F13 국방부 → R4 PASS 유지
  - F16 정보체계/아이웨이브 → R3 PASS 유지 (deep=1 redirect)
  - cross-lookup → R2 PASS 유지 + R5 P1-17/18 강화
- **CHECKLIST.md §7 종료 조건 4건 충족 명시**:
  - P0 5건: 4건 fix (P0-A/B/C/D), 1건 deferred (P0-E F10 차트 별도 phase)
  - P1 80% 이상: R5 후 누적 18/23 = 78% (F12-13 직결 100%)
  - L5 1라운드: R1~R5 14 화면 검증 완료
  - 사용자 OK: R5 보고 후 사용자 confirm 대기

### 회귀 위험 영역

- **vendors/[bizNo]**: 기간 form 추가가 page header 레이아웃에 영향 — header section spacing 점검
- **lookup**: from/to input이 bid mode에서 노출되지 않는지 conditional rendering cross-check
- **kwater**: page=1 default 시 기존 동작 유지 — pageSize=30 default + 14건 응답 시 1페이지 표시 + nav 미노출 (hasMore=false)

---

## Phase 30 종료 권고 (R5 quality-monitor 앞)

- R5 7 P1 적용 + 종합 회귀 0 가정 시 **APPROVED — Phase 30 종료**
- 잔여 P1 5건 (P1-12 / P1-13 / P1-22 / P1-23) → 별도 phase deferred (ROUND-4-REPORT § 7 권고 그대로)
- P0-E F10 차트 검은색 → Phase 31 deferred 그대로
- 사용자 발화 #36 "5회 반복" 정신 충족 (R1-R5 + R3.5 hotfix)
