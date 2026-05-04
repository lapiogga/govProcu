# RETROSPECTIVE — 2026-05-04 (Phase 22~32 종합 자기반성)

> 사용자 발화 #62 트리거 — "자기반성 + 시점 관리 + 원인 분석 + 다시 시작할 때까지 대기"

## 1. 시점 (체크포인트)

| 일시 | 이벤트 |
|------|--------|
| 2026-05-03 20:42 | 세션 시작 — 발화 #1 운영 프레임워크 (오케스트레이터/GSD/시계열) |
| 2026-05-03 21:18 | 발화 #4 — err-*.png 5건 + 결함 보고 시작 |
| 2026-05-04 00:32 | 발화 #31 (강한 비판 #1) — "오류투성이, 데이터 형식 고려 안 함" → Phase 29 verification-overhaul |
| 2026-05-04 00:53 | 발화 #35 — "처음부터 다시 14화면 정합성" → Phase 30 |
| 2026-05-04 01:18 | 발화 #36 — 3팀 5회 반복 → quality-loop 정착 |
| 2026-05-04 09:38 | 발화 #39 (강한 비판 #2) — "지침 보기라도 한건지" → Phase 31 G2B 지침 정합 |
| 2026-05-04 11:15 | 발화 #48 (강한 비판 #3) — "이젠 못 믿겠어" → 5 DOSSIER + POC 7건 raw evidence |
| 2026-05-04 14:50 | 발화 #54 (강한 비판 #4) — "좀 잘하자" → P31-R4.6 hot-fix |
| 2026-05-04 15:45 | 발화 #59 (강한 비판 #5) — "헤매는 이유? 처음부터 다시? 포기?" → P32-R2 일괄 fix |
| 2026-05-04 17:05 | **본 RETROSPECTIVE 작성 시점** |

총 진행 시간 약 20시간. 사용자 강한 비판 5회. 누적 commits 12+ atomic.

## 2. 누적 진행 (성과)

### Phase 22~32 산출

| Phase | 핵심 fix | 회복 결함 |
|-------|---------|----------|
| 22 errors-triage | F1 포트, F2 trace, F4 페이징, F6 UX, F7 vendor profile, F8 키워드 | 8건 |
| 23 perf-sla-5s | 6 stage 병렬화, default 단축, R 폴백, cache TTL | F9 회피 |
| 24 vendor-matching | 토큰 매칭 (keyword + inst_name) | F4/F8 정합 |
| 25 port-ops | 인프라 docker-compose 정합 | F1 보강 |
| 26 trace-streaming | 1 Timeline → 6 Suspense | UX 강화 |
| 27 cache-warmup | etl_warmup.py | 사전 캐싱 |
| 28 validation-debug | Phase 29 트리거 진단 | F11 P0~P3 |
| 29 verification-overhaul | L1~L6 검증 표준화, F11 4건 fix | nts_status_code 등 |
| 30 ui-integrity-sweep | 14 화면 진단, 5 round, 11 commits | P0 5→1, P1 23→5 |
| 31 g2b-guideline | 5 DOSSIER + POC raw 7건, F18~F28 | 11 결함 → 10 회복 |
| 32 trace-stage-fallback | 5 stage actions R-prefix 일괄, F32 hydration | F18/F25/F30 등 |

**baseline 진척**:
- P0 (차단): 5 → 0 (100%)
- P1 (중요): 23 → 5 (R-prefix 영역 거의 회복)

**누적 commits (저장된 핵심)**:
- v22~v29 (Phase 22~29): 30+ atomic
- Phase 30: 11 (R1~R5 + R3.5)
- Phase 31: 9 (R1~R5 + R4.5)
- Phase 32: 4 (R4.6, P32-R1, P32-R2, P32-R2.5, F32)

총 50+ atomic commits.

## 3. 잘못된 점 (자기반성)

### 3.1 검증 시뮬레이션 근본 결함 ★ 최대 원인

**우리 검증 절차 L1~L6**:
- L1 정적 (TS 컴파일 / Python import)
- L2 논리 (코드 분석)
- L3 backend MCP raw (curl)
- L4 사용자 case (입찰번호 1~2건)
- L5 frontend HTML (curl 정적 SSR)
- L6 G2B vs 나라장터 UI 매핑

**갭**:
- **L5는 curl HTML — 정적 SSR만**. 사용자가 form submit → 다중 체크박스 → searchParams string[] 같은 동적 인터랙션 시뮬 부재.
- → P31-R3 commit 후 사용자 화면 검증 → err-91 Runtime TypeError 발견 (`raw.split is not a function`)
- L7 (Runtime + 인터랙션 시뮬) 부재가 헤매는 패턴의 근본.

### 3.2 단편 fix 패턴 (사용자 보고마다 한 도구씩 fix)

- F18 R-prefix 발견 → search_bid_notices만 fix (R1)
- F25 발견 → get_bid_notice_detail만 fix (R4.5)
- F30 발견 → list_bid_participants + get_award_detail + get_pre_specification_detail 일괄 fix (P32-R2)

→ 매 사용자 발견마다 부분 fix → 다음 발견 → 또 부분 fix 무한 반복 패턴. **bid_notice_no 받는 모든 backend 도구를 처음부터 일괄 점검했어야**.

### 3.3 사용자 시나리오 우선 검증 부재

- 우리 순서: 코드 → tester → quality-monitor → 사용자 마지막
- 올바른 순서: **사용자 보고 정확한 입찰번호로 14 화면 + 6 stage 자동화 시나리오 검증을 첫 차원**으로
- L4를 L1·L2·L3 위에 위치시켜야

### 3.4 dev server hot-reload 신뢰 결함

- err-71 — F31 commit `73f12be` 미적용 evidence
- frontend dev server에 새 코드 적용됐는지 자동 검증 안 함
- 사용자가 새로고침해도 hot-reload 미작동 가능

### 3.5 Backend 응답 파싱 한계 미인지

- G2B `getOpengResultListInfo*`는 비공개 API (P32-R2에서 발견)
- 응답 row 1건 + `prtcptCnum`(개수) + `opengCorpInfo`(낙찰자 caret 인코딩)만
- 50건 응찰업체 raw row는 OpenAPI 미공개
- → **G2B API 한계를 처음부터 인지했어야 — DOSSIER에서 swagger 명세만 추출하고 실제 응답 형식 PoC 부족**

### 3.6 사용자 신뢰 회복 5회 반복

| 비판 | 트리거 | 우리 반응 |
|------|-------|----------|
| #1 (#31 "오류투성이") | F11 누적 | Phase 29 verification |
| #2 (#39 "지침 보기라도") | err-021~026 | Phase 31 5 DOSSIER |
| #3 (#48 "못 믿겠어") | DOSSIER 인용만 | POC raw 7건 |
| #4 (#54 "좀 잘하자") | err-91 Runtime | P31-R4.6 |
| #5 (#59 "헤매는 이유") | err-71/72/73 | P32-R2 일괄 fix |

**패턴**: 매 비판 → 검증 강화 약속 → 다음 commit에서 다른 결함 발견 → 비판 반복.
검증 강화가 매번 **이전 비판에만 대응** — 새로운 영역 사전 검증 부재.

## 4. 원인 분석 (4 카테고리)

### 4.1 인지적 원인
- **사용자 시나리오 사후 검증** — 완벽한 코드를 만들고 사용자가 검증 → 결함 발견 → fix 반복
- 사용자가 우리 "QA"를 대신함

### 4.2 도구적 원인
- Playwright/브라우저 자동화 부재
- 우리는 sub-agent + curl + python에 한정
- 동적 인터랙션 시뮬 도구 부재

### 4.3 절차적 원인
- 5-round quality-loop는 **이미 정의된 결함**에는 강함
- 그러나 **신규 결함 발견 능력**은 사용자에게 의존
- 자체 결함 발견 메커니즘 부재 (Playwright + 사용자 시나리오 fixture)

### 4.4 구조적 원인
- backend 도구가 분산 (`bid.py` / `award.py` / `workflow.py` / `vendor.py`)
- bid_notice_no 받는 모든 도구의 R-prefix 폴백을 일관 적용하는 메커니즘 부재
- → "한 도구 fix → 다음 발견 → 다른 도구 fix" 무한 패턴

## 5. 다음 시작 시 적용할 변경 사항

### 5.1 검증 패러다임 전환 (Phase 33+)

**L7 신규 차원 의무**:
- Playwright 또는 Puppeteer로 브라우저 자동화
- 사용자 보고 입찰번호 5건 (R25BK00755515 / R25BK00758431 / R25BK00760571 / R26BK01451151 / R26BK01501665)을 표준 fixture
- 14 화면 자동 순회 + 모든 form 인터랙션 + Runtime 에러 모니터링
- L1~L7 7 차원 검증

### 5.2 사용자 시나리오 우선 (Top-Down)

- L4 (사용자 case retrieval)을 **첫 검증 차원**으로 격상
- 매 commit 후 첫 검증: "사용자가 직접 화면 켜고 5 입찰번호 검색 시 모든 stage 정상 표시?"
- 통과 후에만 L1~L3 검증 진행

### 5.3 Backend 도구 일관성 의무

- bid_notice_no 받는 **모든 backend 도구**의 R-prefix 폴백을 한 번에 일괄 점검
- 신규 도구 추가 시 R-prefix 폴백 의무 (lint 또는 검증 hook)

### 5.4 사용자 비판 패턴 인식

- 비판 #1~#5 모두 **유사한 패턴** (검증 시뮬 한계 / 단편 fix / 사용자 시나리오 부재)
- 같은 패턴 비판 6회째는 **상위 메타 변경** 필요 — 단순 추가 fix 아님
- Phase 33부터 메타 변경 적용

## 6. 성과 (자기 인정)

자기 비판만 하는 것도 부적절. 명확 성과:
- **Phase 22~32 누적 50+ atomic commits**
- **P0 결함 5 → 0** (100% 해소)
- **POC raw evidence 7건 + 5 DOSSIER** (사용자 발화 #48 신뢰 회복)
- **F18 R-prefix 매칭 회복** (R25BK00755515 → 역사지리정보DB raw 검증)
- **F19 발주기관 fan-out** (국방부 국군재정관리단 매칭)
- **F25 시행령 제36조 12 필수항목 노출**
- **F30 5 stage actions 일괄 R-prefix 폴백**

## 7. 다시 시작할 때 권고

### 7.1 즉시 (Phase 33 가동 시)
- F32 hydration `ee85fc2` 적용 확인
- F33 (vendor 0건) — search_awards_by_vendor scan 한계 fix 또는 G2B 서버측 vendor 필터 활용
- F29 (유찰 라벨) — getOpengResultListInfoFailing 활용

### 7.2 메타 (장기)
- Playwright 환경 구축
- 사용자 시나리오 fixture 표준화 (5 입찰번호 + 14 화면)
- L7 검증 차원 의무화

### 7.3 사용자 협업
- 사용자가 새 결함 보고 시 **즉시 fix 대신 일관성 점검 우선**
- "이 결함과 동일 패턴이 다른 도구에 있는가?" 자체 질문
- 5건 입찰번호 fixture로 자체 검증 → 다른 결함 발견 → 일괄 fix

## 8. 잠시 대기

사용자 다음 지시까지 작업 멈춤. 본 RETROSPECTIVE 검토 후 다음 단계 결정 부탁.

권고 다음 단계:
- **(A) Phase 33 신설** — 검증 패러다임 전환 (Playwright + 사용자 시나리오 우선)
- **(B) F33/F29 즉시 fix** — vendor 0건 + 유찰 라벨 (작은 스코프)
- **(C) 휴식 후 재개** — 사용자가 직접 화면 사용 후 결함 일괄 수집

기다림.
