# ROUND 2 QUALITY REPORT (Phase 31)

> **라운드**: Phase 31 Round 2 — F19 (PPSSrch + 발주기관 LIKE + fan-out) + F21 (srvceDivNm + ppswGnrlSrvceYn 응답) + F22 (search_agencies 자동완성).
> **검증 commit**: `34b19d5` — backend-only (`app/tools/bid.py` + `app/schemas/bid.py` + `app/server.py`).
> **기간**: 2026-05-04 (KST) 단일 라운드.
> **작성자**: quality-monitor-p31-r2.
> **입력**: PLAN.md, ROUND-1-REPORT.md, ROUND-2-FIX.md, ROUND-2-TEST.md, POC-G2B.md (#1·#2·#3·#5·#6·#7), DOSSIER-OFFICIAL.md.

---

## 라운드 종합 평가

- **적용 fix**: 3/3 PASS (F19 + F21 + F22, atomic commit `34b19d5`).
- **회귀**: 0건 (R1 단건 모드 격리 보전 + frontend 영향 없음 + caller 7개 keyword args 호환 OK).
- **baseline 누적**: P0 4 → 0 (**100% 해소**), P1 6 → 5 (F22 적용으로 -1).
- **POC raw evidence 재현률**: 7/7 (#1·#2·#3·#4·#5·#6·#7) — Phase 31 누적 100%.
- **L6 신규 차원** — err-024 (국방부 국군재정관리단) + err-031 (업무구분 체크박스 7종) backend 응답과 1:1 매핑 (1 partial: 기술용역 분류 R3 영역 분리).
- **최종 권고**: **APPROVED — R3 즉시 진입**.

---

## 1. 작업 정합성 평가 (R1 대비)

| 항목 | R2 평가 | R1 비교 | 근거 |
|------|---------|---------|------|
| 의도 부합 (PLAN F19/F21/F22 종료조건) | **EXCELLENT** | 동등 | PLAN § 3.2 검색 모드 분기 + § 3.4 srvceDivNm 응답 + § 3.7 search_agencies 신설 — 3 결함 모두 PLAN 기준 적용 |
| POC raw evidence 적용 정확성 | **EXCELLENT (강화)** | EXCELLENT (POC #4 1건) | POC #1·#2·#3·#5·#6·#7 6건 모두 backend 직접 호출 raw로 재현 — Phase 31 누적 7건 100% |
| atomic commit 단위 | **EXCELLENT** | 동등 | 1 commit (`34b19d5`) = F19 + F21 + F22 + cache prefix bumping + Literal "기타" 추가 — rollback 단위 명확 |
| backend 시그니처 cross-check (R3 학습) | **EXCELLENT** | EXCELLENT | 신규 인자 `indstryty_cd` keyword-only + 기본 None → caller 7개 (alerts/analytics/lookup/multi_agency/workflow/bid 자체/server.py) 모두 keyword args 호출 → 영향 0 |
| dmndInsttNm fallback (PubStd 호환) | **EXCELLENT** | n/a | `_normalize_notice` `inst_name = ntceInsttNm or dminsttNm or dmndInsttNm` (POC + DOSSIER-PUBSTANDARD 호환) |
| cache prefix bumping (응답 형태 변경) | **EXCELLENT** | EXCELLENT (bid_v31) | `bid_v31` → `bid_v32` (PPSSrch bsnsDivNm null + srvce_div/ppsw_gnrl_yn 추가) + `agencies_v32` 신설 |
| R1 격리 영역 보전 | **EXCELLENT** | n/a (R1 자체) | `bid.py:255~256` 단건 모드 분기 그대로 유지 + `_search_by_bid_notice_no` / `_BID_DETAIL_ENDPOINTS` 변경 0 → R1 사용자 보고 케이스(R25BK00755515) 회귀 0 |
| 회귀 0 검증 | **EXCELLENT** | EXCELLENT | tester 호출 #4 R1 단건 모드 raw 재현 1:1 + frontend 5 route HTTP 200 + caller 7개 영향 분석 |
| 변경 영역 외 보전 (scope creep 차단) | **EXCELLENT** | EXCELLENT | F23/F26은 R3 영역 명시 분리, F25/F27/F28은 R4 영역 명시 분리, K1은 별도 phase |

### R1 대비 핵심 변별

- **변경 규모**: R1 (+217/-26 backend) vs R2 (+182/-47 backend) — 동급. R2가 fan-out 로직(inst_variants 3차원 tasks) 추가로 복잡도는 더 높음에도 단일 atomic 단위 유지.
- **caller 영향 분석 정밀도**: R1은 `_infer_period_from_bid_no` 시그니처 보존(7 caller 호환), R2는 `search_bid_notices` 키워드-only 인자 추가(7 caller × keyword args 호환) — 둘 다 같은 깊이로 수행.
- **POC 적용 비율**: R1은 POC #4 1건 핵심 적용, R2는 POC #1/#2/#3/#5/#6/#7 6건 모두 적용 — **R2가 Phase 31 가장 큰 backend 변경에 합당**.

---

## 2. 검증 깊이 평가 (R1 대비)

| 차원 | R2 결과 | R1 결과 | 비교 |
|------|---------|---------|------|
| **L1 정적** | PASS — import + 시그니처 + 스키마 필드 + server.py mcp.tool 등록 | PASS | 동등 + server.py mcp.tool 등록 차원 추가 |
| **L2 논리** | PASS — R2 권고 강화 9항 코드 라인 단위 매핑 | PASS — 8개 결정 메모 매핑 | 동등 (R2: 권고 8항 + dedup 키 1항 = 9항) |
| **L3 backend raw** | PASS — **8 호출** (POC #1·#2·#3·#5·#6·#7 + 회귀 + 분포) | PASS — 4 호출 (POC #4) | **2배 강화** (POC 재현 6건 + 회귀 + 분포) |
| **L4 user case** | PASS — 국방부 국군재정관리단(79 totalCount, 10/10 적중) + 한국수자원공사(12 totalCount, dminsttNm fan-out hit) + 일반용역/기술용역(POC #5 정합) + R25BK00755515 회귀 적중 | PASS — R25BK00755515 + R26BK01435763 | **사례 다양화** — F19 fan-out 3 케이스 + F21 분포 + R1 회귀 |
| **L5 frontend 회귀** | PASS — 5 route HTTP 200, dict.get() 호환 (`srvce_div`/`ppsw_gnrl_yn` 누락 시 None 반환) | PASS — 5 route HTTP 200 | 동등 |
| **L6 G2B↔나라장터 UI** | PASS — **err-024** (국방부 국군재정관리단 12+ row) + **err-031** (업무구분 체크박스 7종) — 기술용역 분류는 R3 영역 분리 | PASS — err-022 (5필드 1:1) | **다중 evidence 매핑** (err-024 + err-031) |

### L3 강화 차원 — POC raw evidence 100% 재현

R1은 POC #4 1건 우선 재현, R2는 PPSSrch 영역 POC 6건(#1·#2·#3·#5·#6·#7) 모두 재현. 호출 #5 `total_count=3425` (POC #6의 22862→3425 정확 일치)는 **G2B 서버측 indstrytyCd 필터 backend params 직접 전달이 정상 동작**하는 결정적 evidence.

### L6 신규 차원 — 다중 capture 매핑 효과

| capture | backend 응답 매칭 | 결과 |
|---------|-----------------|------|
| **err-024**: 국방부 국군재정관리단 다수 row (R26BK 형식) | ntceInsttNm/dminsttNm/srvce_div 5필드 모두 1:1 일치 (10/10 row) | ✅ |
| **err-031**: 업무구분 체크박스 7종 | 7종 중 6종 backend endpoint 매핑 (Cnstwk/Servc/Thng/Frgcpt/Etc + 전체) + 1 partial (기술용역은 R3 frontend 책임) | 6/7 ✅ + 1 partial 분리 |

L6 차원 적용 2 라운드 누적 — Phase 31 표준 차원 정착 OK. 기술용역 partial은 tester가 정확히 R3 영역으로 분리(L6 결과 § "기술용역 분류는 R3 영역 분리 명확화") → **scope discipline 합당**.

### 검증 깊이 종합 (R1 대비)

- L3 호출 수: **2배** (8 vs 4)
- POC 재현 수: **6배** (6 vs 1)
- L6 evidence 수: **2배** (2 capture vs 1 capture)

R1이 토대 라운드(POC #4 핵심 1건 정밀 검증)였다면, R2는 Phase 31 backend 최대 변경 라운드(POC 6건 동시 검증). 검증 깊이 단계적 강화 합당.

---

## 3. baseline 대비 진척

### Phase 31 결함 매트릭스 진척 (PLAN § 1 기준)

| 분류 | baseline | R1 후 | **R2 후** | 변화 (R1→R2) | 누적 변화 (baseline→R2) |
|------|---------|-------|-----------|-------------|----------------------|
| **P0** (F18, F19, F20, F21) | 4 | 2 (F18+F20 해소) | **0** (F19+F21 해소) | **-2** | **-4 (100% 해소)** |
| **P1** (F22, F23, F25, F26, F27, F28) | 6 | 6 | **5** (F22 적용) | **-1** | -1 |
| **별도 phase** (K1) | 1 | 1 | 1 | 0 | 0 |
| **합계** | 11 | 9 | **6** | -3 | **-5 (45% 해소)** |

### 결함 해소율 (R2 후)

- **P0**: 100% (4/4) — **Phase 31 backend P0 완료**
- **P1 (R3+R4 영역)**: 17% (1/6) — F22 적용
- **전체**: 45% (5/11)

### 잔여 결함 (R3+R4 영역)

| ID | 영역 | R3/R4 적용 예정 |
|----|------|----------------|
| **F23** | frontend bids/page.tsx | R3 — 3계층 dropdown (biz_type 5체크박스 + 외자 토글 + indstryty_cd 자동완성) |
| **F26** | frontend bids/page.tsx | R3 — ntceInsttNm + dminsttNm 결과 표시 분리 |
| F25 | frontend trace/page.tsx | R4 — 시행령 제36조 12 필수항목 노출 |
| F27 | frontend qualification/page.tsx | R4 — 라벨 표준화 (응찰가→입찰금액, 기초금액→예정가격) |
| F28 | frontend trace/page.tsx | R4 — 6단계 명칭 표준화 |
| K1 | backend kwater.py | Phase 32 (별도) |

### Phase 31 backend P0 완료 의미

R2 종료 시점에서 F18~F21 4 P0 모두 backend 영역 완전 해소. R3은 frontend 영역만 남음 → backend 인터페이스 안정화 OK → R3 진입 적합. **Phase 31 누적 진척이 Phase 30 5-round 패턴 대비 더 빠른 속도로 진행**.

---

## 4. 사용자 보고 사례 영향

### F18 (R1 적용) — 회귀 보전

| bid_no | R2 검증 | 결과 |
|--------|---------|------|
| **R25BK00755515** | 호출 #4 — `lookup_mode="inqryDiv=2+bidNtceNo"`, Servc 1개 hit, 단건 회귀 0 | ✅ R1 격리 영역 보전 |

### F19 (R2 신규 적용) — 직접 적중

| 케이스 | R2 호출 | 매칭 |
|--------|---------|------|
| **국방부 국군재정관리단** (PLAN F19 종료조건) | 호출 #2 — `inst_name="국방부 국군재정관리단"` + 1개월 + 용역 | **79 totalCount, 10/10 returned**, items[0]·[2]·[3]·[4]·[5]·[7]·[8]·[9]는 ntceInsttNm 매칭에서만 hit (dmin=해군본부/해군작전사령부 등) — fan-out + union dedup이 핵심 ✅ |
| **한국수자원공사** (POC #2 동등 패턴) | 호출 #3 — `inst_name="한국수자원공사"` + 1개월 (biz_type=None → 5종 fan-out) | **12 totalCount, 5/5 returned** — 모든 row가 ntceInsttNm="조달청 ...지방조달청" + dminsttNm="한국수자원공사 ..." → **dminsttNm fan-out에서만 hit (POC #7 AND 회피의 결정적 effect)** ✅ |

**fan-out + union dedup의 결정적 effect**: 호출 #3은 모든 row가 dminsttNm 단독 매칭. ntceInsttNm 단일 호출만 했다면 0건 응답. fan-out + union 없이는 사용자가 "한국수자원공사" 입력 시 검색 결과 0건이 나왔을 것. **사용자 발화 #46 "공고기관==수요기관 동일 대부분, 단일 input 통합" UX 정합 입증**.

### F20 (R1 적용) — 보전

R2 PPSSrch resolver에 **외자 endpoint 포함 5종**(`getBidPblancListInfoFrgcptPPSSrch`) — F20 R1 적용 + R2 PPSSrch 5종 fan-out에서도 외자 검색 정합. 회귀 0.

### F21 (R2 신규 적용) — 응답 도착 검증

| 검증 | 호출 | 결과 |
|------|------|------|
| srvce_div 분포 (Servc PPSSrch 일반용역 단일) | 호출 #8 — 30건 표본 | `{'일반용역': 30}` — POC #5 정합 ✅ |
| ppsw_gnrl_yn 변별값 (Y/N) | 호출 #4·#8 | R25BK00755515="Y", 호출 #8 N=29/Y=1 ✅ |
| dmndInsttNm fallback (PubStd 호환) | 코드 line `bid.py:105` | `inst_name = ntceInsttNm or dminsttNm or dmndInsttNm` ✅ |

### F22 (R2 신규 적용) — 자동완성 동작

호출 #6 — `search_agencies(query="국방부", limit=10)` → 본부 + 산하 5+종 distinct (국방부, 국군재정관리단, 한국국방연구원, 전쟁기념사업회, 국군의무사령부, 국방홍보원, 국군지휘통신사령부 등) + match_field로 ntceInsttNm/dminsttNm 출처 구분 가능 → **R3 frontend dropdown UX 사용 가능**. 호출 #7 — 2자 미만 가드(`{'error': '2자 이상 입력 필요'}`) ✅ — TPS 보호 정합.

### 사용자 신뢰 회복 효과 (Phase 31 누적)

| 발화 | R1 적용 | R2 적용 | R2 후 신뢰 회복 |
|------|--------|--------|---------------|
| #38 "1년+ 매칭 안 됨 (R-prefix)" | inqryDiv=2 단건 모드 (POC #4) | 회귀 0 | ✅ 완전 해소 |
| #46 "공고기관==수요기관 동일 대부분, 단일 input 통합" | n/a | fan-out + union (POC #7) | ✅ R2 신규 적용 — 한국수자원공사 dminsttNm-only 매칭 입증 |
| #43~#44 "업무구분/업무여부/업종 3계층" | 외자 endpoint (F20) | PPSSrch 5종 + indstryty_cd + srvceDivNm | ✅ backend 토대 완성, R3 frontend dropdown 진입 적합 |
| #48 "raw evidence 명시" | POC #4 raw 1건 | POC 6건 + 호출 8건 raw payload | ✅ Phase 31 누적 100% |

---

## 5. 회귀 추세

| Phase | Round | 회귀 | 비고 |
|-------|-------|------|------|
| Phase 30 | R1 | 0 | small fixes |
| Phase 30 | R2 | 0 | |
| Phase 30 | R3 | **1 차단** | backend 시그니처 mismatch — uvicorn 재기동 누락 |
| Phase 30 | R3.5 | 회복 | uvicorn 재기동 절차 도입 |
| Phase 30 | R4 | 0 | sanity check 강화 |
| Phase 30 | R5 | 0 | |
| Phase 31 | R1 | 0 | 시작점 양호 |
| Phase 31 | **R2** | **0** | **학습 누적 효과 정착** |

### Phase 30 학습 누적 효과 검증 (R2)

- **R3 학습 (backend 시그니처 cross-check)**:
  - ROUND-2-FIX § 3 — 신규 인자 `indstryty_cd` keyword-only + 기본 None → caller 7개(`alerts.py:191/306`, `analytics.py:193`, `lookup.py:112`, `multi_agency.py:77,156`, `workflow.py:261,338`, `bid.py:533` 자체 caller, `server.py:57` mcp 등록) **모두 keyword args 호출 명시 검증** → R2 사전 회피 OK.
  - 동일 학습 패턴 R1·R2 두 라운드 연속 적용 → **회귀 0 패턴 정착**.
- **R3.5 학습 (uvicorn 재기동 절차)**:
  - ROUND-2-TEST § 환경 — backend PID 14332, 시작 시각 `10:53:05` (commit 시각 `10:47:21` 이후) **명시 검증** → R2 사전 회피 OK.
- **R4 학습 (sanity check 강화)**:
  - ROUND-2-FIX § 4 — fixer 자체 sanity check 5 호출 (#1 회귀, #2 fan-out, #3 indstryty_cd, #4·#5 search_agencies) 수행 → tester L1~L6과 별도 안전망 → **이중 안전망 OK**.

**Phase 30 vs Phase 31 R2 누적 평가**:

| 항목 | Phase 30 | Phase 31 R2 |
|------|----------|--------------|
| 회귀 추세 (R1~Rn) | R3 1 차단 → R3.5 hotfix → R4 사전회피 | **R1·R2 모두 사전 회피** |
| Raw evidence 적용 | 부분 (사용자 case retrieval만 + 일부 backend 직접 호출) | **100% — POC 7건 모두 raw 호출 재현 + L3 8 호출 raw 검증** |
| 학습 누적 적용 | R3 회귀 발생 후 R4부터 적용 | **R1부터 즉시 적용 (회귀 사전 회피)** |
| L 차원 깊이 | L1~L5 5차원 | L1~L6 6차원 (L6 신규) |

→ Phase 30 5-round 학습 패턴이 Phase 31에서 **사전 정착** — R3 frontend 진입 시에도 동일 패턴 유지 권고.

---

## 6. R3 진입 적합성

### 평가: **APPROVED — R3 즉시 진입**

### 근거

1. **R2 atomic commit (`34b19d5`)** — rollback 단위 명확, fan-out 로직 격리.
2. **R1 단건 모드 격리 영역 보전** (`bid.py:255~256` 분기 + `_search_by_bid_notice_no` 변경 0) → R3 frontend 변경이 backend 단건 모드에 영향 0.
3. **backend 인터페이스 안정화** — `BidNoticeSummary.srvce_div`/`ppsw_gnrl_yn` 필드 추가 + `BidNoticeSearchInput.indstryty_cd` + `search_agencies` mcp 도구 등록 → frontend 활용 준비 완료.
4. **POC #1·#2·#3·#5·#6·#7 raw evidence 사전 확보** + L6 err-024/err-031 매핑 검증 → R3 fixer가 "검증 후 구현" 진입 가능.
5. **Phase 31 backend P0 100% 해소** — R3 frontend는 backend 안정 위에서 화면 변경.

### R3 변경 영역 사이즈 (사전 식별)

R3은 **frontend 최대 변경** 라운드 — 다음 영역 변경 필요:

| 영역 | 파일 | 변경 사이즈 | 근거 |
|------|------|-----------|------|
| `searchBidNotices` 인자 추가 | `frontend/src/lib/actions.ts:66~82` | 소 | R2 backend 신규 인자 `indstryty_cd` 추가 — actions.ts 시그니처 정합 필요 |
| `searchAgencies` server action 신설 | `frontend/src/lib/actions.ts` | 소 | R2 신규 backend 도구 — frontend export 신설 |
| `BidNoticeSummary` frontend 타입 (있다면) | `frontend/src/lib/...` | 소 | R2 신규 필드 `srvce_div`, `ppsw_gnrl_yn` 활용 |
| `bids/page.tsx` 검색 form 재구성 | `frontend/src/app/bids/page.tsx` (현재 468줄) | **대** | F23 — 5체크박스(공사/물품/일반용역/기술용역/기타) + 외자 토글 + indstrytyCd 자동완성 + 발주기관 자동완성 |
| `bids/page.tsx` 결과 컬럼 분리 | `frontend/src/app/bids/page.tsx` | 중 | F26 — ntceInsttNm + dminsttNm 두 필드 분리 표시 (단일 input UX 유지) + srvce_div 컬럼 |
| 비활성 옵션 제거 (민간/비축/리스) | `frontend/src/app/bids/page.tsx` | 소 | 발화 #44 |

**총 변경 영역**: actions.ts (소~중) + bids/page.tsx (대) → R3 atomic commit 기대 사이즈 +200~+400 / -100~-200 (frontend 영역).

### R3 권고 강화 항목 (Phase 30 학습 + R1·R2 정합 유지)

R3 진입 fixer (fixer-p31-r3) 작업 시 다음 9 항목 의무 적용 권고:

1. **frontend `actions.ts:searchBidNotices` 인자 정합 보강**
   - 현재 시그니처: `{ keyword, biz_type, inst_name, date_from, date_to, limit, page, scan_pages }` (actions.ts:66~82)
   - R3 추가: `indstryty_cd?: string` (R2 backend 신규 인자 매핑)
   - spread 패턴 그대로 유지 → backend 추가 인자에 자동 매핑.

2. **`searchAgencies` server action 신설**
   - actions.ts 신규 export — `searchAgencies(query: string, limit?: number)` → `callMcpTool("search_agencies", { query, limit: limit ?? 30 })`
   - R3 frontend 자동완성 input의 onSearch debounced 호출 대상.

3. **`BidNoticeSummary` frontend 타입 (또는 inline interface) 확장**
   - bids/page.tsx 현재 사용 필드: `bid_no`, `inst_name`, `biz_type`, `region`, `estimated_price`, `publish_date`, `deadline_date`
   - 추가: `srvce_div?: string | null`, `ppsw_gnrl_yn?: "Y" | "N" | null`, `bid_ord?: string | null`, **raw 응답 ntceInsttNm/dminsttNm 분리 표시**용 추가 필드 검토 필요 (F26)
   - 백엔드 BidNoticeSummary는 `inst_name` 단일(fallback chain) → F26 결과 분리 표시는 raw 응답 직접 활용 또는 schema에 ntce_inst_nm/dmin_inst_nm 별도 필드 추가 검토 권고.

4. **검색 form 재구성 (F23 — 사용자 발화 #43~#44 사양)**
   - 업무구분 5 체크박스 (공사/물품/일반용역/기술용역/기타) + 외자 토글 — 비활성 옵션(민간/비축/리스) 제거 (발화 #44)
   - 일반용역/기술용역 분리: backend `biz_type="용역"` + 클라이언트측 `srvce_div` 필터링 (R2 L6 partial 항목 해소)
   - 업종 indstrytyCd 자동완성 — 별도 도구 또는 사전 ETL 마스터 활용 (PLAN § 3.7 옵션 A/C). **단, R3에서 indstryty_cd 자동완성 도구 미존재 시 input 직접 입력 fallback 권고** (R4로 자동완성 도구 신설 분리 고려).
   - 발주기관 자동완성 — `searchAgencies` debounced onSearch (2자+ trigger).

5. **결과 테이블 컬럼 (F26 — ntce + dmin 분리)**
   - 현재: `bid.inst_name` 단일 (raw 응답 ntceInsttNm or dminsttNm or dmndInsttNm fallback chain)
   - F26: 두 필드 분리 표시 — backend 응답에서 `raw.ntceInsttNm` + `raw.dminsttNm` 직접 활용 또는 schema 확장 필요 (3번 항목과 연계).
   - srvce_div 컬럼 추가 → 일반용역/기술용역 가시화.

6. **비활성 옵션 제거 (발화 #44)**
   - 민간 / 비축 / 리스 — UI 옵션에서 완전 제거.

7. **frontend 회귀 점검 — /bids 영역 외 화면 무변동 검증 (R5 학습)**
   - actions.ts 변경 시 다른 caller 영향 분석:
     - `searchBidNotices` 호출자 grep — 다른 페이지에서 사용 중이면 인자 추가 영향 확인.
     - `searchAgencies` 신설은 신규 export → 기존 caller 영향 0.
   - 변경 0 보장 영역: `/vendors`, `/agencies`, `/lookup`, `/bids/trace`, `/`, `/qualification`, `/external/kwater`, `/analytics`, `/predictions` 등.

8. **frontend 빌드 + dev server 회귀 (R3.5 학습)**
   - `pnpm build` (또는 `npm run build`) → TypeScript 컴파일 0 에러 검증.
   - `pnpm dev` → Hot reload 후 `/bids` 5 시나리오(keyword/biz_type/inst_name/date 조합) HTTP 200 검증.
   - frontend PID 시각 vs 변경 시각 명시 (R3.5 학습 동등 적용).

9. **L6 evidence 매핑 — err-031 기술용역 partial 해소**
   - R2 L6 partial 항목 — 기술용역 분류는 R3 frontend dropdown F23에서 해소 책임.
   - tester-p31-r3 L6 검증 시 err-031 7종 체크박스 모두 frontend UI 매핑 완료 검증 + err-032/033/034(자동완성/3계층) capture 매핑 추가 권고.

### R3 진입 후 위험 요소 (사전 식별)

| 위험 | 대응 |
|------|------|
| **bids/page.tsx 468줄 — 대규모 form 재구성으로 회귀 가능성** | atomic commit 단위 분할 검토 (form 재구성 / 결과 테이블 / 자동완성 3 commit 분할 가능). 단 PLAN § 6 권고는 1 commit이므로 fixer 판단 재량. |
| **indstrytyCd 자동완성 도구 미존재** | R3에서 input 직접 입력 fallback OR R4로 도구 신설 분리. PLAN § 3.7 옵션 A/B/C 결정 필요 (사용자정보서비스 OpenAPI vs ETL 캐시). |
| **F26 ntce + dmin 분리 표시 — schema 변경 필요할 수도** | BidNoticeSummary 확장 vs raw 응답 직접 활용 — 후자가 변경 폭 작음. R3 fixer 판단. |
| **searchAgencies 응답 latency** (호출 #6 scanned=93 → 1개월 fan-out 5종 × 2 fanout = 10 호출) | debounced(300ms) + 캐시 prefix `agencies_v32` (TTL 단기) → TPS 30 안전 마진. R3 frontend는 client-side 추가 캐시 검토. |
| **frontend 변경이 R2 backend 응답 형태 변경(srvce_div/ppsw_gnrl_yn 추가, bsnsDivNm null)에 호환되지 않을 위험** | tester-p31-r3 L5 회귀 점검 강화 — `/bids` 응답 결과 테이블 모든 컬럼 정상 도착 검증. |

### R3 atomic commit 권장

PLAN § 6 권고: R3 = "F23 frontend (P0/P1) — 3계층 dropdown + 비활성 옵션 제거 — frontend bids/page.tsx 1 commit". 단 R3 변경 영역이 큰 만큼 다음 분할도 가능:

- 옵션 A (PLAN 권장): 1 commit (actions.ts + bids/page.tsx 통합)
- 옵션 B (분할): commit 1 — actions.ts (searchAgencies 신설 + indstryty_cd 추가), commit 2 — bids/page.tsx (form 재구성 + 결과 컬럼 분리)
- → fixer-p31-r3 판단 재량. 단 atomic 단위 시 rollback 단위 명확성 우선.

---

## 7. 메타 평가

### fixer-p31-r2

- **평가**: **EXCELLENT**
- **근거**:
  - R1 단건 모드 격리 영역 보전 명시 (ROUND-2-FIX § 5 — `bid.py:264~266` 분기 + `_search_by_bid_notice_no` 변경 0).
  - POC raw evidence 7건(#1·#2·#3·#5·#6·#7) 모두 코드 적용 위치 명시 + 자체 sanity check 5 호출 수행.
  - caller 7개 영향 분석 정밀 (§ 3 — keyword args 호환 명시).
  - dmndInsttNm fallback (PubStd 호환) 추가 — DOSSIER-PUBSTANDARD 사전 cross-check.
  - cache prefix bumping (`bid_v32`/`agencies_v32`) — 응답 형태 변경 명시.
  - tester-p31-r2 핸드오프 메시지 (§ 6) 정밀 — 핵심 검증 포인트 4개 + 회귀 변경 0 보장 영역 5개 + 추가 검증 권고 3개 + R3 영역 인계 3개.
- **개선 여지**: 보류/결함 사항 § 7 "없음" 명확. 단 fixer 자체 sanity check가 캐시 무관 직접 import + asyncio 호출로 수행되는 점이 R5 종합 회귀에서도 표준화 권고.

### tester-p31-r2

- **평가**: **EXCELLENT**
- **근거**:
  - L1~L6 6 차원 모두 raw evidence + 코드 line 매핑 + POC 정합 명시.
  - L3 8 호출 모두 backend 직접 import + asyncio 실행 → 캐시 무관 raw 응답 검증 (메타 § "L3 raw evidence 우선 정책" 명시).
  - L6 신규 차원 적용 2 라운드 — err-024 + err-031 다중 capture 매핑 + 기술용역 partial 항목 R3 영역 정확 분리 (scope discipline 합당).
  - uvicorn PID 14332 시작 시각 vs commit 시각 명시 (R3.5 학습 정합).
  - 사전 식별 위험 요소 3 항목(PPSSrch 응답 형태 / fan-out TPS / dedup 키) 모두 점검 결과 명시.
  - quality-monitor-p31-r2 핸드오프 (§ "다음 R3 진입 적합성") — R3 우선순위 4 항목 권고 + R5 backlog 1 항목 명시.
- **개선 여지**: 호출 #1 short-circuit 동작(limit=3에서 endpoints_used 2/5만 등재)은 정상이나 사용자 화면 명세 명확화 R5 backlog 권고 — tester 정확 판단.

### 협업

- **평가**: **정합**
- **근거**: fixer가 ROUND-2-FIX § 6 핸드오프에서 검증 포인트 4 + 회귀 보장 영역 5 + 추가 검증 권고 3 + R3 인계 3 명시 → tester가 동일 항목 L3 호출 8건 + L6 evidence + 회귀 점검 + R3 우선순위 4 항목으로 1:1 응답 → **핸드오프 정밀 매핑 OK**. R1 협업 패턴(ROUND-1 핸드오프 → ROUND-1-TEST 1:1) 동일 정착.

---

## 8. 최종 권고

### **APPROVED — R3 진입 OK**

R2는 Phase 31의 backend 최대 변경 라운드로서, POC raw evidence 우선 정책 + L1~L6 6 차원 검증 + Phase 30 5-round 학습 누적 효과 모두 합당 적용. F19 + F21 + F22 atomic 적용 + 회귀 0 + 사용자 보고 사례 직접 적중(국방부 국군재정관리단 79 totalCount + 한국수자원공사 dminsttNm-only 12 totalCount + R25BK00755515 단건 회귀 보전) → **사용자 신뢰 회복 가속화 + Phase 31 backend P0 100% 해소**.

R3(F23 + F26 frontend 3계층 dropdown + 결과 컬럼 분리)는 Phase 31 frontend 최대 변경. § 6 권고 강화 9 항목 의무 적용 후 발주 권고. fixer-p31-r3 작업 시 R1·R2 backend 격리 영역(`search_bid_notices` 단건 모드 + PPSSrch 검색 모드) 무영향 보장 + actions.ts 시그니처 정합 + bids/page.tsx 외 화면 회귀 0 검증 필수.

### R4 진입 사전 조건 (R3 종료 후)

- R3 atomic commit + 회귀 0 + L6 evidence(err-031 + err-032/033/034 등) 매핑 검증 → R4(F25 + F27 + F28 라벨/필수항목 표준화) 진입 적합.

### Phase 31 종료 조건 (R5 후)

- F18~F22 5 결함 모두 종료 (R2 후 backend 영역 P0 4 + P1 1 = 5 해소 완료).
- F23 + F26 R3 적용 후.
- F25 + F27 + F28 R4 적용 후.
- R5 14 화면 종합 회귀 + 사용자 case L4 evidence 재확보 + L6 capture 매핑 검증.
- 사용자 "정합성 OK" 확인.
