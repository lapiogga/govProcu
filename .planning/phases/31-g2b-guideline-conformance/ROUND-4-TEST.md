# ROUND 4 TEST REPORT (Phase 31)

> **라운드**: Phase 31 Round 4 — F25 (입찰공고 필수항목 노출) + F27 (qualification 라벨 정정) + F28 (trace 6단계 명칭 정정).
> **tester**: tester-p31-r4
> **검증 시각**: 2026-05-04 (KST)
> **검증 대상**:
> - Commit A `6beb1b2` — qualification/page.tsx (+7/-7)
> - Commit B `45f5287` — bids/trace/page.tsx (+112/-18)
> **base 비교**: `9e8693d` (R3 종료) → 현재 HEAD
> **입력**: ROUND-4-FIX.md, DOSSIER-LAW.md (§4.2 / §7.1 / §8.3), poc4_용역.json (R25BK00755515 raw payload)

---

## 종합 PASS/FAIL

**P31-R4: CONDITIONAL FAIL**

frontend 코드 변경 자체(commit A + commit B)는 모두 ROUND-4-FIX 명세대로 정확히 적용됨 (L1/L2 PASS). 그러나 L4 사용자 case retrieval 단계에서 **F25 NoticeRequiredFields가 실제 사용자 화면에 노출되지 않음** — 원인은 backend `get_bid_notice_detail` 폴백 chain이 운영 환경에서 `found=false`를 반환하여 frontend의 노출 조건 `data?.found && <NoticeRequiredFields>` 분기가 항상 false. 이는 R3.5에서 식별된 "G2B 단건 inqryDiv=3 R형식 미지원" 이슈의 재발. **본 R4 commit 자체는 frontend-only이므로 코드 변경에는 결함 없음**, 다만 R4 의도(시행령 제36조 12 필수항목 사용자 노출)는 backend 폴백 chain 정상 작동 전까지 실현 불가 — R5 또는 별도 backend phase로 인계 필요.

추가로 미세 결함 1건 (L2): SummarySkeleton 본문의 "요약 로딩 중 — **본 공고** 단건 조회 (cache hit 시 0.5초)" 텍스트가 F28 정정에서 누락 — `bids/trace/page.tsx:537`. 비표준어 "본 공고" 잔존.

---

## 검증 매트릭스

| 항목 | L1 정적 | L2 논리 | L3 backend raw | L4 user case | L5 frontend HTML | L6 법령 매핑 | 종합 |
|------|--------|---------|----------------|---------------|------------------|--------------|------|
| F27 qualification 라벨 | PASS | PASS | N/A | PASS | PASS | PASS | **PASS** |
| F28 trace 6단계 명칭 | PASS | PASS (1건 누락) | N/A | PASS | PASS | PASS | **CONDITIONAL PASS** |
| F25 입찰공고 필수항목 | PASS | PASS | **FAIL** | **FAIL** | **FAIL** | PASS | **FAIL (backend 의존)** |
| 회귀 (영향 받지 않는 화면) | PASS | — | — | PASS | PASS | — | **PASS** |
| 회귀 (TypeScript) | PASS | — | — | — | — | — | **PASS** |

---

## L1 정적

### 1.1 git diff stat

```
git diff 9e8693d..HEAD --stat
 frontend/src/app/bids/trace/page.tsx    | 130 +++++++++++++++++++++++++++-----
 frontend/src/app/qualification/page.tsx |  14 ++--
 2 files changed, 119 insertions(+), 25 deletions(-)
```

- **app/ 디렉터리 0 변경** (backend 격리 보전 ✅)
- **frontend qualification/page.tsx**: +7 / -7 (commit A 명세 일치)
- **frontend bids/trace/page.tsx**: +112 / -18 (commit B 명세 일치)
- 영향 받지 않는 frontend 영역 (vendors, agencies, lookup, external/kwater, analytics, lib/actions.ts) **0 변경 ✅**

### 1.2 TypeScript 컴파일

```
cd frontend && npx tsc --noEmit
EXIT=0
```

- **0 에러 ✅**
- commit A 후 + commit B 후 누적 컴파일 통과

### 1.3 변경 라인 정합성

ROUND-4-FIX.md § 2.1 (commit A)의 7개 라벨 매핑 모두 git diff에서 확인:
- header 부제어: "입찰가 + 시공경험 + 기술자 + 신용등급 + 경영·기타" → "입찰금액 + 시공경험 + 기술능력 + 경영상태 + 신인도" ✅
- "응찰가 (원)" → "입찰금액 (원)" ✅
- "기초금액 (원)" → "예정가격 (원)" ✅
- "기술자 수" → "보유 기술자 수" ✅
- "신용등급 (예: AA-)" → "경영상태 (예: AA-)" ✅
- labelMap.credit "신용평가" → "경영상태" ✅
- labelMap.etc "기타" → "신인도" ✅

ROUND-4-FIX.md § 2.2 (commit B) 모두 확인:
- 빈 form 안내 텍스트 (line 62) "사전규격 → 본 공고 → 개찰 → 낙찰 → 응찰업체 → 낙찰자 NTS 검증" → "사전규격공개 → 입찰공고 → 개찰 → 낙찰자 결정 → 낙찰자 NTS 검증 → 계약 체결" ✅
- StageSkeleton fallback 4종 (n=1/2/4 + n=6 inline) 라벨 정정 ✅
- StagePreSpec/StageNotice/StageAwardAndNts 함수 내부 StageError + Stage label 4종 정정 ✅
- 신규 컴포넌트 NoticeRequiredFields (66 lines) + FieldRow 추가 ✅

---

## L2 논리

### 2.1 F27 qualification — 8개 라벨 매핑 (PASS)

| # | before | after | DOSSIER-LAW 근거 | 정합 |
|---|--------|-------|------------------|------|
| 1 | header "입찰가+시공경험+기술자+신용등급+경영·기타" | "입찰금액+시공경험+기술능력+경영상태+신인도" | §8.3 적격심사 평가분야 4종 | ✅ |
| 2 | "응찰가 (원)" | "입찰금액 (원)" | §8.3 + 시행령 제42조 표준어 | ✅ |
| 3 | "기초금액 (원)" | "예정가격 (원)" | §3.2 적격심사 분모는 예정가격 | ✅ |
| 4 | "기술자 수" | "보유 기술자 수" | §8.3 기술능력 평가 | ✅ |
| 5 | "신용등급 (예: AA-)" | "경영상태 (예: AA-)" | §8.3 평가분야 표준명 | ✅ |
| 6 | labelMap.credit "신용평가" | "경영상태" | §8.3 | ✅ |
| 7 | labelMap.etc "기타" | "신인도" | §8.3 | ✅ |

backend 인자 (`bid_amount`, `base_amount`, `biz_type`, `experience_actual`, `experience_standard`, `tech_count`, `tech_required`, `credit_grade`)는 모두 영문 키로 보전. **backend signature 변경 0 ✅**.

### 2.2 F28 trace 6단계 명칭 (CONDITIONAL PASS — 1건 누락)

| Stage | before | after | DOSSIER-LAW 근거 | 정합 |
|-------|--------|-------|------------------|------|
| 1 | 사전규격 | 사전규격공개 | §7.1 정부입찰계약 집행기준 | ✅ |
| 2 | 본 공고 | 입찰공고 | §7.1 시행령 제33조 표제어 | ✅ |
| 3 | 개찰 + 응찰업체 | (변경 없음, 자체 명칭) | — | ✅ |
| 4 | 낙찰 | 낙찰자 결정 | §7.1 시행령 제42조 표제어 | ✅ |
| 5 | 낙찰자 NTS 검증 | (변경 없음, 자체 검증) | — | ✅ |
| 6 | 계약 | 계약 체결 | §7.1 시행규칙 제48조 | ✅ |

**미세 결함 — 누락 1건**: `bids/trace/page.tsx:537` SummarySkeleton 본문 텍스트 "요약 로딩 중 — **본 공고** 단건 조회 (cache hit 시 0.5초)"에서 비표준어 "본 공고" 잔존. F28 의도 ("본 공고" 사용 0)에 부합하기 위해 "입찰공고 단건 조회"로 정정 필요. 단 사용자 시각 노출은 stage 라벨보다 짧은 fallback 시점(0.5초~5초) 한정 — 우선순위 낮음.

### 2.3 F25 NoticeRequiredFields — 12 시행령 제36조 항목 매핑 (코드 PASS, 노출 FAIL → L3/L4/L5)

| 시행령 36조 호 | label | raw 필드 매핑 | fallback | 코드 정합 |
|---|---|---|---|---|
| 5호 | 입찰참가자격 | `bidPrtcptLmtYn` Y → "참가제한" / `indstrytyLmtYn` Y → "업종제한" / `prdctClsfcLmtYn` Y → "물품분류제한" / `rgnLmtBidLocplcJdgmBssNm` → "지역제한(...)" 누적 | "제한 없음 (일반)" | ✅ |
| 7호 | 낙찰자 결정방법 | `sucsfbidMthdNm` 또는 `cntrctCnclsMthdNm` | "—" | ✅ |
| 8호 | 입찰서 제출방법 | `bidMethdNm` | "—" | ✅ |
| 8호 | 입찰 개시·마감 | `bidBeginDt` + `bidClseDt` (또는 `summary.deadline_date` 폴백) | "—" | ✅ |
| 2호 | 개찰 일시 | `opengDt` | "—" | ✅ |
| 2호 | 개찰 장소 | `opengPlce` | "전자조달시스템(나라장터)" | ✅ |
| 6호 | 입찰참가수수료 | `bidPrtcptFee` (>0 시 fmtWon, 0 시 "면제") | "면제" | ✅ |
| 6호 | 입찰보증금 | `bidGrntymnyPaymntYn` Y → "납부 필요", N → "면제 또는 별도 안내" | — | ✅ |
| 10호 | 현장설명 | `dcmtgOprtnDt` + `dcmtgOprtnPlce` | "—" | ✅ |
| 11호 | 공동계약 | `cmmnSpldmdMethdNm` | "—" | ✅ |
| 3호 | 계약담당공무원 | `ntceInsttOfclNm` (+ `ntceInsttOfclTelNo` optional) 또는 `crdtrNm` | "—" | ✅ |
| 4호 | 목적물 명세 | `purchsObjPrdctList` | "—" | ✅ |
| 12호 | 무효사유 fallback | (코드 hardcoded) | "무효사유 등 상세는 입찰공고문 본문 참조 (시행령 제36조 제12호)" | ✅ |

**코드 매핑 12종 모두 정합** — fixer가 선언한 ROUND-4-FIX § 2.2 표 준수. 단, 노출 조건 `data?.found && <NoticeRequiredFields>` 의 `data.found`가 backend 의존성에 의해 false 고정 (L3 참조).

---

## L3 backend raw (F25 필드 도착)

### 3.1 backend 가동 확인

- `POST http://localhost:8081/mcp` HTTP 405 (GET 405, POST 정상) — 가동 ✅

### 3.2 fixer 선언 raw payload 검증 (`poc4_용역.json` R25BK00755515)

| 필드 | poc4_용역.json 값 | 존재 |
|------|-------------------|------|
| bidNtceNo | "R25BK00755515" | ✅ |
| bidNtceOrd | "000" | ✅ |
| bidPrtcptLmtYn | "N" | ✅ |
| indstrytyLmtYn | "Y" | ✅ |
| prdctClsfcLmtYn | "N" | ✅ |
| sucsfbidMthdNm | "수의시담-일반경쟁->수의" | ✅ |
| cntrctCnclsMthdNm | "수의계약" | ✅ |
| bidMethdNm | "전자시담" | ✅ |
| bidBeginDt | "2025-04-03 09:30:00" | ✅ |
| bidClseDt | "2025-04-03 11:30:00" | ✅ |
| opengDt | "2025-04-03 11:35:00" | ✅ |
| opengPlce | "" (fallback "전자조달시스템(나라장터)") | ✅ (fallback) |
| bidPrtcptFee | "928960" | ✅ |
| bidGrntymnyPaymntYn | "" (fallback "면제 또는 별도 안내") | ✅ (fallback) |
| dcmtgOprtnDt | "" (fallback "—") | ✅ (fallback) |
| dcmtgOprtnPlce | "" | ✅ (fallback) |
| cmmnSpldmdMethdNm | "(전자)공동이행" | ✅ |
| ntceInsttOfclNm | "이상정" | ✅ |
| ntceInsttOfclTelNo | "02-590-8890" | ✅ |
| crdtrNm | "대한민국정부서울지방조달청장" | ✅ |
| purchsObjPrdctList | "[1^8115169901^공간정보DB구축서비스]" | ✅ |

**fixer가 선언한 12 필드 모두 inqryDiv=2 응답에서 존재 확인 ✅** (`.planning/phases/31-g2b-guideline-conformance/poc_raw/poc4_용역.json:13~120`).

### 3.3 frontend 호출 흐름 검증 (CRITICAL FAIL)

frontend `bids/trace/page.tsx:208`은 `getBidNoticeDetail(bidNo, bidOrd)` server action 호출 → backend `get_bid_notice_detail(bid_notice_no, bid_ord)` 호출. backend는 다음 3차 폴백 chain 순서 수행:

1. inqryDiv=3 단건 직접
2. inqryDiv=1 + bidNtceNo (차수 매칭)
3. search_bid_notices(bid_notice_no=...) (progressive 30/90일 + 추정 연도)

**현재 운영 환경 검증 결과** (3건 시도):

| bid_notice_no | bid_ord | found | lookup_mode |
|---------------|---------|-------|-------------|
| R25BK00755515 | 000 | **false** | (폴백 모두 미매칭) |
| R26BK01501298 | 000 | **false** | (폴백 모두 미매칭) |
| 20240315678 | 00 | **false** | (폴백 모두 미매칭) |

backend `get_bid_notice_detail` 응답 note: "inqryDiv=3 단건 + inqryDiv=1 폴백 + search_bid_notices 매칭 모두 미발견."

대조 — `search_bid_notices(bid_notice_no="R26BK01501298", limit=3)` 직접 호출 시 1건 hit. 즉, search_bid_notices 단독은 동작하나 `get_bid_notice_detail` 내부의 3차 폴백 chain에서 매칭 로직이 실패. R3.5에서 식별된 issue의 재발 가능성.

→ **L3 FAIL**: backend `get_bid_notice_detail`이 R 형식·8자리 형식 모든 입력에 대해 found=false 반환 → frontend의 `data?.found` 분기 항상 false → NoticeRequiredFields 렌더링 0건.

**다만 본 R4 범위(frontend only)에서는 코드 결함 없음.** backend 폴백 chain 정합성 결함은 별도 phase 영역.

---

## L4 사용자 case retrieval

### 4.1 F27 qualification (PASS)

- URL: `/qualification?bid_amount=900000000&base_amount=1000000000&biz_type=공사`
- HTTP 200
- 4 라벨 + 비표준어 부재 검증 (L5 § 5.1 참조)
- backend `calc_qualification_score` 정상 호출 (영문 인자 키 보전)

### 4.2 F28 trace 6단계 명칭 (PASS)

- URL: `/bids/trace?no=R26BK01501298&ord=000`
- HTTP 200
- Stage 1~6 라벨 모두 법령 표준어 사용 (L5 § 5.2 참조)
- Stage 6 inactive 상태 ("계약 체결 · 체결 후 추적 가능") — 정합

### 4.3 F25 NoticeRequiredFields 노출 (FAIL)

- URL: `/bids/trace?no=R26BK01501298&ord=000` (실 G2B 검색 hit 공고)
- HTTP 200
- Stage 2 입찰공고 라벨 노출 ✅
- **NoticeRequiredFields 헤더 "입찰공고 필수항목 (시행령 제36조)" 0건** ❌
- **12 항목 라벨(입찰참가자격/낙찰자 결정방법/...) 0건** ❌

원인: L3 § 3.3 — backend `get_bid_notice_detail` 폴백 chain 미작동으로 `data.found=false` 고정. frontend 노출 조건 `{data?.found && <NoticeRequiredFields ...>}` 절단.

---

## L5 frontend HTML (curl 시각 검증)

### 5.1 `/qualification` (PASS)

```
curl http://localhost:3000/qualification → HTTP 200, 80174 bytes
```

라벨 매칭 카운트:

| 라벨 | hit | 정합 |
|------|-----|------|
| 입찰금액 | 6 | ✅ |
| 응찰가 | **0** | ✅ (비표준어 부재) |
| 예정가격 | 4 | ✅ |
| 기초금액 | **0** | ✅ (비표준어 부재) |
| 경영상태 | 6 | ✅ |
| 신용등급 | **0** | ✅ (비표준어 부재) |
| 신인도 | 2 | ✅ |
| 보유 기술자 | 4 | ✅ |
| 기술자 수 | 4 | (정합 — "보유 기술자 수" + "요구 기술자 수"의 부분 매칭) |

**F27 4 라벨 모두 노출 + 비표준어 4종 모두 부재 ✅**

### 5.2 `/bids/trace?no=R26BK01501298&ord=000` (CONDITIONAL PASS)

```
curl "http://localhost:3000/bids/trace?no=R26BK01501298&ord=000" → HTTP 200, 108514 bytes
```

Stage 라벨 정밀 매칭:

| 라벨 | exact 매칭 hit | 컨텍스트 검증 |
|------|---------------|----------------|
| 사전규격공개 | 2 | Stage 1 라벨 + skeleton fallback 정합 ✅ |
| 사전규격 (단독, "공개" 미포함) | 0 의미적 hit | 모두 backend `note` 메시지 안의 안내 텍스트 ("사전규격 endpoint", "get_pre_specification_detail")로, Stage 라벨 아님 ✅ |
| 입찰공고 | 2 | Stage 2 + Stage 1 note 안 "본 입찰공고일 수 있음" ✅ |
| 본 공고 | 1 | **`bids/trace/page.tsx:537` SummarySkeleton 본문** ("요약 로딩 중 — 본 공고 단건 조회") — F28 정정에서 누락된 비표준어 ⚠ |
| 낙찰자 결정 | 2 | Stage 4 라벨 ✅ |
| 낙찰 (단독) | 3 | 모두 "미낙찰/유찰" 패턴 — Stage 라벨 아님 ✅ |
| 계약 체결 | 1 | Stage 6 라벨 ✅ |
| 계약 (단독) | 0 | ✅ |

**F28 6단계 명칭 4종 모두 노출 + 비표준어 (사전규격 단독, 낙찰 단독, 계약 단독) Stage 영역 부재 ✅**, 단 SummarySkeleton 한 줄 잔존 ⚠.

### 5.3 `/bids/trace?no=R26BK01501298&ord=000` NoticeRequiredFields (FAIL)

| 라벨 | hit |
|------|-----|
| 입찰공고 필수항목 (헤더) | **0** ❌ |
| 입찰참가자격 | 0 ❌ |
| 낙찰자 결정방법 | 0 ❌ |
| 입찰서 제출방법 | 0 ❌ |
| 입찰 개시·마감 | 0 ❌ |
| 개찰 일시 | 0 ❌ |
| 개찰 장소 | 0 ❌ |
| 입찰참가수수료 | 0 ❌ |
| 입찰보증금 | 0 ❌ |
| 현장설명 | 0 ❌ |
| 공동계약 | 0 ❌ |
| 계약담당공무원 | 0 ❌ |
| 목적물 명세 | 0 ❌ |

**12 항목 모두 미노출 ❌** — backend 의존성 (L3/L4 § 3.3·4.3 참조).

### 5.4 영향 받지 않는 화면 회귀 (PASS)

| URL | HTTP | 정합 |
|-----|------|------|
| / | 200 | ✅ |
| /bids | 200 | ✅ |
| /vendors | 200 | ✅ |
| /agencies | 200 | ✅ |
| /lookup | 200 | ✅ |
| /external/kwater | 200 | ✅ |
| /analytics | 200 | ✅ |
| /predictions | 404 | (R3 시점에도 동일 — 라우트 미존재. R4 회귀 아님) |

frontend 영향 받지 않는 화면 모두 **HTTP 200 보전 ✅**.

---

## L6 G2B vs 법령 표준 일치 (DOSSIER-LAW 인용)

### 6.1 F27 qualification 라벨 ↔ 법령 표준 매핑 (PASS)

DOSSIER-LAW.md §8.3 — "공사 적격심사 세부기준" 평가분야 4종:

| 평가분야 | 시행령/세부기준 표준명 | R4 frontend 라벨 (after) | 정합 |
|---|---|---|---|
| 입찰가격 | 입찰금액 (시행령 제42조) / 입찰금액 비율 평가 | "입찰금액 (원)" | ✅ |
| 해당공사 수행능력 (시공경험) | 시공경험 (실적/기준) | "시공경험 실적" / "시공경험 기준" | ✅ |
| 해당공사 수행능력 (기술능력) | 기술능력 — 보유 기술자 + 기술자격 | "보유 기술자 수" / "요구 기술자 수" | ✅ |
| 경영상태 | 경영상태 (재무비율 + 기업경영분석) | "경영상태 (예: AA-)" + labelMap.credit "경영상태" | ✅ |
| 신인도 | 신인도 (가산점) | labelMap.etc "신인도" | ✅ |
| 분모 | 예정가격 (시행령 제8조 + DOSSIER-LAW §3.2) | "예정가격 (원)" | ✅ |

**5 평가분야 + 분모 모두 법령 표준어 정합 ✅.**

### 6.2 F28 trace 6단계 ↔ 시행령 표준 절차 매핑 (PASS)

DOSSIER-LAW.md §7.1:

| Stage | DOSSIER-LAW §7.1 표준 | R4 frontend 라벨 (after) | 시행령 근거 | 정합 |
|---|---|---|---|---|
| 1 | 사전규격공개 | "사전규격공개" | 정부입찰·계약 집행기준 (행안부 2016-12-30) | ✅ |
| 2 | 입찰공고 | "입찰공고" | 시행령 제33조 표제어 | ✅ |
| 3 | 개찰 + 입찰참가자 | "개찰 + 응찰업체" (자체 명칭 유지) | 시행령 제40조 | ⚠ ("응찰업체"는 구어 — DOSSIER-LAW §8.2에서 일관성 위해 유지 가능 명시) |
| 4 | 낙찰자 결정 | "낙찰자 결정" | 시행령 제42조 표제어 | ✅ |
| 5 | (법령 외 자체 검증) | "낙찰자 NTS 검증" | 부가가치세법 제8조 | ✅ |
| 6 | 계약 체결 | "계약 체결" | 시행규칙 제48조 | ✅ |

**6단계 중 4단계 시행령 표준어 정정 ✅, 자체 명칭 2건(3·5단계) 유지 — DOSSIER-LAW 인정.**

### 6.3 F25 입찰공고 필수항목 ↔ 시행령 제36조 매핑 (코드 PASS)

DOSSIER-LAW.md §4.1·§4.2 — 시행령 제36조 12개 명시 의무 항목 ↔ frontend NoticeRequiredFields 매핑:

| 시행령 36조 호 | 의무 항목 | R4 NoticeRequiredFields label | raw 필드 | 코드 정합 |
|---|---|---|---|---|
| 1호 | 입찰에 부치는 사항 (=공고제목) | (Summary 헤더에서 표시) | summary.title | ✅ (기존 표시) |
| 2호 | 입찰·개찰의 장소 및 일시 | "개찰 일시" + "개찰 장소" | `opengDt` + `opengPlce` | ✅ |
| 3호 | 공고기관·수요기관·계약담당공무원 | "계약담당공무원" | `ntceInsttOfclNm` + `ntceInsttOfclTelNo` 또는 `crdtrNm` | ✅ |
| 4호 | 계약 목적물 명세 및 수량 | "목적물 명세" | `purchsObjPrdctList` | ✅ |
| 5호 | 입찰참가자격 | "입찰참가자격" | `bidPrtcptLmtYn` + `indstrytyLmtYn` + `prdctClsfcLmtYn` + `rgnLmtBidLocplcJdgmBssNm` | ✅ |
| 6호 | 입찰보증금·계약보증금·하자보수보증금 | "입찰참가수수료" + "입찰보증금" | `bidPrtcptFee` + `bidGrntymnyPaymntYn` | ✅ |
| 7호 | 낙찰자 결정방법 | "낙찰자 결정방법" | `sucsfbidMthdNm` 또는 `cntrctCnclsMthdNm` | ✅ |
| 8호 | 입찰서 제출방법 + 마감일시 | "입찰서 제출방법" + "입찰 개시·마감" | `bidMethdNm` + `bidBeginDt` + `bidClseDt` | ✅ |
| 9호 | 추정가격 | (Stage 2 desc에 표시) | `presmptPrce` | ✅ (기존 표시) |
| 10호 | 현장설명 | "현장설명" | `dcmtgOprtnDt` + `dcmtgOprtnPlce` | ✅ |
| 11호 | 공동계약 | "공동계약" | `cmmnSpldmdMethdNm` | ✅ |
| 12호 | 입찰의 무효사유 | (fallback 안내) | "무효사유 등 상세는 입찰공고문 본문 참조 (시행령 제36조 제12호)" | ✅ |

**시행령 제36조 12 항목 모두 코드에서 매핑·노출 분기 정합 ✅** (단, 노출은 backend `data.found` 의존 — L3/L4/L5 § 3.3·4.3·5.3).

DOSSIER-LAW.md § 4.2 결론 ("우리 frontend는 시행령 제36조 명시사항 12개 중 4~5개만 표시 (33~42%)")는 본 R4 코드 적용 후 **코드 측면 12/12 (100%) 매핑** — 단, **운영 노출 측면**은 backend 의존성 차단으로 **0/12 (0%)** 상태.

---

## quality-monitor-p31-r4 핸드오프

### R4 PASS/FAIL 종합

- **commit A `6beb1b2` (F27 qualification)**: **PASS** (L1~L6 모두 정합)
- **commit B `45f5287` (F25+F28 trace)**:
  - F28 6단계 명칭 정정: **CONDITIONAL PASS** (1건 누락 — `bids/trace/page.tsx:537` SummarySkeleton "본 공고" 잔존)
  - F25 NoticeRequiredFields 노출: **CONDITIONAL FAIL** (코드 정합 ✅, 운영 노출 ❌ — backend 폴백 chain 의존성)

- **frontend 코드 변경 자체**: 모두 ROUND-4-FIX 명세 일치, TS 컴파일 0 에러, 회귀 0건.
- **사용자 시각 검증 (R4 의무)**: F27 PASS, F28 PASS (1건 minor 누락), F25 **FAIL** (backend 의존성).
- **회귀**: 영향 받지 않는 frontend 화면 7종 모두 HTTP 200 보전. backend `app/` 0 변경.

### 다음 R5 (종합 회귀) 진입 적합성

**부적합 — R4.5 또는 R5 backend 영역 신규 fix 필요**:

1. **Critical (R5 진입 차단)**: backend `get_bid_notice_detail` 폴백 chain 운영 환경 작동 검증 + 수정. 현재 R/숫자 형식 모든 공고에 대해 `found=false` 반환 — F25 NoticeRequiredFields 사용자 노출 차단. fixer가 검증한 raw payload(inqryDiv=2 응답)는 정합이지만 frontend가 호출하는 단건 endpoint 폴백 chain 미동작. R3.5에서 식별된 동일 issue의 재발 가능성.
   - 권고: `app/tools/bid.py:550~608` (search_bid_notices 폴백 chain) 디버깅. `bid_notice_no` 인자 매칭 로직 + progressive date range 파라미터 검증.
   - 또는 frontend NoticeRequiredFields 노출 조건 완화 (`data?.found` → `data?.raw && Object.keys(data.raw).length > 0`) — 단 backend 폴백 chain 정상화가 우선.

2. **Minor (R5 진입 가능, R5에서 일괄 정정 권고)**: `bids/trace/page.tsx:537` SummarySkeleton 본문 텍스트 "본 공고" → "입찰공고" 정정. F28 의도("본 공고" 사용 0)에 부합. 1라인 수정.

3. **R5 진입 후 회귀 검증 권고**:
   - L1~L6 누적 + Phase 30·R1·R2·R3 학습 영역 (5체크박스 + 결과 7컬럼 + (동일) 표기 + searchAgencies LIKE + indstryty_cd dropdown + ppsw_gnrl_yn 분리) 회귀 무결성.
   - F22 frontend 자동완성 (R4에서 분리) 별도 영역으로 R5 또는 별도 phase 진입.

### 핵심 연락 사항

- **fixer ROUND-4-FIX § 6 핸드오프 vs 검증 결과 차이**: fixer는 "F25 NoticeRequiredFields raw 필드 매핑 검증 — backend `getBidNoticeDetail` 실 응답에 12 필드 모두 도착 시 frontend가 1:1 노출하는지"를 의무로 명시했고, 매핑 자체는 ✅. 다만 **"12 필드 모두 도착" 전제조건이 backend 운영 환경에서 미충족** — found=false 반환. fixer의 raw payload 검증은 inqryDiv=2 응답 (poc4_용역.json 캡처) 한정으로, frontend 호출 흐름(inqryDiv=3 + 폴백)에서의 도착 여부는 별도 검증 필요했음. R5 backend 작업으로 인계.

- **R3.5 학습의 재발**: P30-R3.5에서 식별된 "G2B 단건 inqryDiv=3 R형식 미지원" 이슈가 R4 commit B 디플로이 후 재차 노출. backend 폴백 chain의 운영 환경 적합성 점검 필요.

- **DOSSIER-LAW 인용 의무**: R4 commit message + 본 리포트 모두 §4.2 / §7.1 / §8.3 직접 인용 ✅.

---

**작성 완료 — 2026-05-04 (KST)**
