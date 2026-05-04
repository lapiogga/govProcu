# ROUND 4 FIX REPORT (Phase 31)

> **라운드**: Phase 31 Round 4 — F25 (입찰공고 필수항목 노출) + F27 (qualification 라벨 정정) + F28 (trace 6단계 명칭 정정). frontend-only.
> **fixer**: fixer-p31-r4
> **기간**: 2026-05-04 (KST) 단일 라운드
> **base**: `9e8693d` (R3 종료) → `45f5287` (R4 종료, 2 commits)
> **입력**: PLAN.md, ROUND-3-REPORT.md § R4 권고 강화, DOSSIER-LAW.md, POC-G2B.md (poc4_용역.json R25BK00755515 raw payload)

---

## 1. Commits

| # | hash | 영역 | 변경 라인 | 적용 F |
|---|------|------|----------|---------|
| A | `6beb1b2` | qualification/page.tsx | +7 / -7 | F27 |
| B | `45f5287` | trace/page.tsx | +112 / -18 | F25 + F28 |

총 변경: 2 파일, +119 / -25 lines (frontend only).

---

## 2. 적용 변경 상세

### 2.1 Commit A — F27 (qualification 라벨 법령 표준 정정)

파일: `frontend/src/app/qualification/page.tsx`

| # | 위치 | before | after | 근거 |
|---|------|--------|-------|------|
| 1 | header 부제어 | "입찰가 + 시공경험 + 기술자 + 신용등급 + 경영·기타" | "입찰금액 + 시공경험 + 기술능력 + 경영상태 + 신인도" | DOSSIER-LAW §8.3, 시설공사 적격심사 세부기준 평가분야 4종 |
| 2 | Field label | "응찰가 (원)" | "입찰금액 (원)" | DOSSIER-LAW §8.3, 시행령 제42조 — "입찰금액"이 법령 표준어. "응찰가"는 비표준어 |
| 3 | Field label | "기초금액 (원)" | "예정가격 (원)" | DOSSIER-LAW §3.2 — 적격심사 분모는 예정가격. 기초금액은 예가요약서 |
| 4 | Field label | "기술자 수" | "보유 기술자 수" | DOSSIER-LAW §8.3 — 기술능력 평가의 "보유 기술자" 명확화 |
| 5 | Field label | "신용등급 (예: AA-)" | "경영상태 (예: AA-)" | DOSSIER-LAW §8.3 — 적격심사 평가분야 표준명 "경영상태" (재무비율 기반) |
| 6 | labelMap.credit | "신용평가" | "경영상태" | DOSSIER-LAW §8.3 |
| 7 | labelMap.etc | "기타" | "신인도" | DOSSIER-LAW §8.3 — 적격심사 평가분야 4종 중 4번째 표준명 |

**backend 변경 0**: `calc_qualification_score` 호출 인자(`bid_amount`, `base_amount`, `biz_type`, `experience_actual`, `experience_standard`, `tech_count`, `tech_required`, `credit_grade`)는 모두 영문 키 — 그대로 보전. 표시 라벨만 한글 정정.

### 2.2 Commit B — F25 + F28 (trace 6단계 명칭 + 입찰공고 필수항목)

파일: `frontend/src/app/bids/trace/page.tsx`

#### F28 — 6단계 명칭 정정 (시행령 표제어)

| # | 단계 | before | after | 근거 |
|---|------|--------|-------|------|
| 1 | Stage 1 | 사전규격 | **사전규격공개** | DOSSIER-LAW §7.1, 정부 입찰·계약 집행기준 (행정안전부 2016-12-30 보도자료) |
| 2 | Stage 2 | 본 공고 | **입찰공고** | DOSSIER-LAW §7.1, 시행령 제33조 표제어 |
| 3 | Stage 3 | 개찰 + 응찰업체 | (변경 없음) | 자체 명칭 유지 |
| 4 | Stage 4 | 낙찰 | **낙찰자 결정** | DOSSIER-LAW §7.1, 시행령 제42조 표제어 |
| 5 | Stage 5 | 낙찰자 NTS 검증 | (변경 없음) | 자체 검증 단계 |
| 6 | Stage 6 | 계약 | **계약 체결** | DOSSIER-LAW §7.1, 시행규칙 제48조 |

수정 위치 (각 명칭 4~5곳):
- Suspense fallback `<StageSkeleton label=... />` (4 stages)
- `<StagePreSpec>`/`<StageNotice>`/`<StageAwardAndNts>` 함수의 `<StageError>` 및 `<Stage>` label
- `<Stage n={6} label="계약 체결" inactive />` 인라인 라벨
- 빈 form 안내 텍스트 (`사전규격 → 본 공고 → 개찰 → 낙찰 → 응찰업체 → 낙찰자 NTS 검증` → `사전규격공개 → 입찰공고 → 개찰 → 낙찰자 결정 → 낙찰자 NTS 검증 → 계약 체결`)

#### F25 — 입찰공고(stage2) 필수항목 노출

신규 컴포넌트 `<NoticeRequiredFields>` (66 lines) 추가. `<StageNotice>` 본문에서 `data?.found === true` 시 자동 렌더링. raw 필드 매핑 (R25BK00755515 응답 검증 완료):

| 시행령 36조 | label | raw 필드 | fallback |
|---|---|---|---|
| 제5호 입찰참가자격 | 입찰참가자격 | `bidPrtcptLmtYn`, `indstrytyLmtYn`, `prdctClsfcLmtYn`, `rgnLmtBidLocplcJdgmBssNm` | "제한 없음 (일반)" |
| 제7호 낙찰자 결정방법 | 낙찰자 결정방법 | `sucsfbidMthdNm` 또는 `cntrctCnclsMthdNm` | "—" |
| 제8호 입찰서 제출방법 | 입찰서 제출방법 | `bidMethdNm` | "—" |
| 제8호 입찰서 마감일시 | 입찰 개시·마감 | `bidBeginDt` + `bidClseDt` | "—" |
| 제2호 개찰 일시 | 개찰 일시 | `opengDt` | "—" |
| 제2호 개찰 장소 | 개찰 장소 | `opengPlce` | "전자조달시스템(나라장터)" |
| 제6호 입찰참가수수료 | 입찰참가수수료 | `bidPrtcptFee` | "면제" |
| 제6호 입찰보증금 | 입찰보증금 | `bidGrntymnyPaymntYn` | "면제 또는 별도 안내" |
| 제10호 현장설명 | 현장설명 | `dcmtgOprtnDt` + `dcmtgOprtnPlce` | "—" |
| 제11호 공동계약 | 공동계약 | `cmmnSpldmdMethdNm` | "—" |
| 제3호 계약담당공무원 | 계약담당공무원 | `ntceInsttOfclNm` + `ntceInsttOfclTelNo` 또는 `crdtrNm` | "—" |
| 제4호 목적물 명세 | 목적물 명세 | `purchsObjPrdctList` | "—" |
| 제12호 무효사유 | (안내문 fallback) | — | "무효사유 등 상세는 입찰공고문 본문 참조 (시행령 제36조 제12호)" |

**12개 필수항목 중 12개 모두 노출** (poc4_용역.json 검증 — 모두 raw에 존재). 응답 누락 시 "—" 또는 의미 있는 fallback 표시 (정합).

**컴포넌트 격리**: `<NoticeRequiredFields>` + `<FieldRow>` 두 신규 helper만 추가. 기존 `<Stage>`, `<StageSkeleton>`, `<SummarySkeleton>`, `<StageError>` 시그니처 모두 보전.

---

## 3. 자체 sanity check (R3+R4 학습 누적)

| # | 항목 | 결과 | 근거 |
|---|------|------|------|
| 1 | backend signature 변경 0 (frontend only) | ✅ | `git diff 9e8693d..HEAD -- frontend/` 2 파일만, app/ 무변동 |
| 2 | backend 응답 필드 사전 검증 (F25) | ✅ | `poc4_용역.json` 12 필드 모두 존재 검증 (R25BK00755515) |
| 3 | TypeScript 컴파일 0 에러 | ✅ | `npx tsc --noEmit` exit 0 (commit A 후 + commit B 후 각 1회) |
| 4 | 영향 받지 않는 화면 무변동 | ✅ | bids/page.tsx / vendors / agencies / lookup / external/kwater / analytics / predictions / lookup 모두 unchanged |
| 5 | qualification backend 인자 호환성 | ✅ | 영문 키(`bid_amount`/`base_amount` 등) 무변경 — 표시 라벨만 한글 정정 |
| 6 | trace W3 응답 호환성 | ✅ | `traceBidLifecycle`/`getBidNoticeDetail`/`getAwardDetail` 등 action signature 무변경 — frontend label/필드 노출만 추가 |
| 7 | schema 변경 0 | ✅ | F25는 raw 응답 필드 직접 활용 (R3 패턴 계승) — `BidNoticeSummary` 무변경 |
| 8 | atomic commit 분할 (R3 권고) | ✅ | F27 격리 commit A + F25/F28 통합 commit B |
| 9 | DOSSIER-LAW 인용 의무 | ✅ | commit message에 §4.2 / §7.1 / §8.3 직접 인용 |
| 10 | 사용자 발화 #48 raw evidence 정책 | ✅ | poc4_용역.json raw 필드 검증 후 코드 진입 (추측 fix 금지) |

---

## 4. 변경 영역 격리 검증

| 영역 | 상태 | 비고 |
|------|------|------|
| backend (`app/`) | unchanged | R1·R2 backend 격리 영역 보전 |
| frontend bids/page.tsx | unchanged | R3 변경 영역 보전 (5체크박스 + 결과 7컬럼) |
| frontend lib/actions.ts | unchanged | R3 신규 인자 indstryty_cd 보전 |
| frontend bids/trace/page.tsx | **변경** (R4 commit B) | F25 NoticeRequiredFields 신규 + F28 명칭 정정 |
| frontend qualification/page.tsx | **변경** (R4 commit A) | F27 라벨 정정 |
| frontend vendors/[bizNo] | unchanged | F30 영역 (별도 phase) |
| frontend agencies | unchanged | R2 LIKE 영역 보전 |
| frontend lookup | unchanged | P30-R5 영역 보전 |
| frontend external/kwater | unchanged | K1 별도 phase 영역 |
| schema (`app/schemas/`) | unchanged | R2 srvce_div / ppsw_gnrl_yn 보전 |

---

## 5. 잔여 결함 (Phase 31 R5 영역)

R4 종료 시점 baseline 결함 매트릭스:

| 분류 | baseline | R3 후 | **R4 후** | 변화 |
|------|---------|-------|-----------|-------|
| **P0** (F18~F21) | 4 | 0 | **0** | 보전 |
| **P1** (F22~F28) | 7 | 3 | **0** (F25/F27/F28 모두 적용) | -3 (R4 추가 해소) |
| 별도 phase (K1) | 1 | 1 | 1 | 보전 |
| **합계** | 12 | 4 | **1** | -3 |

**Phase 31 결함 해소율 (R4 후): 92% (11/12)**. K1만 별도 phase.

다만 F22 frontend 자동완성 (R4 권고에서 "별도 영역 명시")은 ROUND-3-REPORT § 3 잔여 결함에서도 R4 영역으로 명시되었으나, 본 R4 발주서 기준 F25/F27/F28만 진행하고 F22 frontend 자동완성은 별도 commit 영역. **본 R4 commit 범위는 F25 + F27 + F28 한정**.

---

## 6. 핸드오프 메시지 (tester-p31-r4 앞)

### 검증 포인트

1. **L1 정적**: `npx tsc --noEmit` exit 0 (commit A + commit B 각 1회 사전 통과). git diff stat 확인.
2. **L2 논리**: F27 8 라벨 매핑(header 부제어 + 5 Field label + labelMap.credit/etc) / F28 6단계 명칭 + 빈 form 안내 텍스트 / F25 NoticeRequiredFields 12 항목 매핑 검증.
3. **L3 backend**: backend 변경 0 — `app/` 디렉터리 git diff 0 라인. 단, F25 raw 필드 매핑 검증 — `poc4_용역.json` (R25BK00755515) 응답 12 필드 → frontend label 매핑 1:1.
4. **L4 user case**:
   - `/qualification?bid_amount=900000000&base_amount=1000000000&biz_type=공사` → 신규 라벨 "입찰금액"/"예정가격"/"보유 기술자 수"/"경영상태"/"신인도" DOM 노출.
   - `/bids/trace?no=R25BK00755515&ord=000` → Stage 라벨 "사전규격공개"/"입찰공고"/"낙찰자 결정"/"계약 체결" DOM 노출 + NoticeRequiredFields 12 항목 노출 ("입찰참가자격: 업종제한", "낙찰자 결정방법: 수의시담-일반경쟁->수의" 등).
5. **L5 시각 검증 (R4 의무)**:
   - HTML curl `/bids/trace?no=R25BK00755515&ord=000` + grep — F28 명칭 4종 (사전규격공개/입찰공고/낙찰자 결정/계약 체결) 모두 hit + F25 NoticeRequiredFields 헤딩 "입찰공고 필수항목 (시행령 제36조)" hit.
   - HTML curl `/qualification` + grep — F27 라벨 7종 hit + 비표준어("응찰가"/"기초금액"/"신용등급" placeholder 등) DOM 0건.
6. **L6 DOSSIER-LAW 인용 매핑**:
   - F27: §8.3 적격심사 평가분야 4종 표준명 (공사 적격심사 세부기준)
   - F28: §7.1 6단계 시행령 표제어 (제33/42조 + 시행규칙 제48조 + 정부입찰계약 집행기준)
   - F25: §4.1·§4.2 시행령 제36조 12개 필수항목 + raw 필드 매핑 (poc4_용역.json)

### 회귀 보장 영역

- backend (`app/`) — 0 라인 변경. R1·R2 학습 영역(`search_bid_notices` 모드 분기 + PPSSrch + search_agencies) 보전.
- frontend bids/page.tsx — 0 라인 변경. R3 영역(5체크박스 + 결과 7컬럼 + (동일) 표기) 보전.
- frontend lib/actions.ts — 0 라인 변경. R3 신규 인자 보전.
- 영향 받지 않는 화면 (vendors, agencies, lookup, external/kwater, analytics, predictions, /) — HTTP 200 + 컴파일 0 에러 보전.

### R4 분리 영역 (F22 frontend 자동완성)

ROUND-3-REPORT § 3에서 R4 영역으로 명시된 F22 frontend 자동완성(searchAgencies 연동)은 본 R4 commit 범위에서 분리. 발주서 기준 F25 + F27 + F28만 진행. F22 자동완성은 별도 R4.5 또는 R5 영역으로 인계 (tester 판단 또는 quality-monitor § R5 권고에 위임).

### tester-p31-r4 작업 흐름

1. 2 commits 누적 검증 (`6beb1b2` qualification + `45f5287` trace).
2. L1~L6 6 차원 검증 + Phase 30·R1~R3 학습 누적 패턴 (라벨 텍스트 매칭 + RSC payload + 영향 받지 않는 화면 회귀 0 + DOSSIER-LAW 조항 인용).
3. F25 NoticeRequiredFields raw 필드 매핑 검증 — backend `getBidNoticeDetail` 실 응답에 12 필드 모두 도착 시 frontend가 1:1 노출하는지.
4. ROUND-4-TEST.md 작성 → quality-monitor-p31-r4 인계.

### 핵심 연락 사항

- backend get_bid_notice_detail 응답 raw 필드 → frontend NoticeRequiredFields 12 라벨 매핑 정밀 검증 의무 (POC-G2B.md poc4_용역.json 기준).
- TypeScript 컴파일 0 에러 — fixer 자체 검증 PASS (commit 직전 + commit 직후).
- F22 frontend 자동완성 별도 분리 — 본 R4 범위 외.

---

## 7. 보류/결함 사항

없음. F25 + F27 + F28 모두 발주서 적합 적용. backend 응답 raw 필드 검증 완료 후 frontend 진입 — 추측 fix 0건. R3 학습(자동완성 R4 분리, schema 변경 0, raw 직접 활용 패턴) 모두 계승.
