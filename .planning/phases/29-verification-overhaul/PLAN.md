# Phase 29 — Verification Overhaul

> **트리거**: 사용자 발화 #31 — "오류투성이 / 데이터 성격·형식 고려 안 함 / gsd-verify 강화"
> **시작**: 2026-05-04 00:35 KST
> **이전 phase**: 28-validation-debug (v28.1 commit)
> **모드**: 자동 진행 일시 정지 → 검증 우선

## 1. 사용자 비판 — 정당한 지적

지금까지 27 commits (v22.1~v28.1). 우리가 부른 "테스트"는:
- ✅ Python import sanity check (`from app.tools import bid; print('OK')`)
- ✅ 단위 토큰 매칭 함수 호출 (`_vendor_name_match` 10/10)

부재한 것:
- ❌ **실제 G2B API 응답 검증** (cache miss 시 raw 응답 형식·content·예외)
- ❌ **사용자 시나리오 e2e 테스트** (브라우저 → frontend → backend → G2B)
- ❌ **데이터 형식 다양성** — 빈 응답 / null / 한글 인코딩 / 특수문자 / 변형 표기
- ❌ **timeout / rate-limit / 부분 실패** 시 동작
- ❌ **사용자 보고 결함 retrieval** (702-86-00866, 239-16-02024, "정보체계", "아이웨이브" 같은 실제 case가 fix 후 작동하는지)

결과: 27 commits 후에도 사용자 화면 결함 8건 (F10~F17) + "여전히 속도 느림".

## 2. 검증 절차 표준 (앞으로 모든 fix에 의무)

### 검증 단계 (각 fix마다 의무)

| 단계 | 도구 | 통과 기준 |
|------|------|----------|
| L1 | import sanity | `python -c "from X import Y"` 무오류 |
| L2 | 단위 테스트 (수정 함수) | 정상/edge/empty/null 케이스 ≥ 5 |
| L3 | **MCP 직접 호출** (실 backend) | curl POST → 응답 OK + 데이터 형식 |
| L4 | **사용자 보고 case retrieval** | 보고된 키워드/사업자번호로 매칭 |
| L5 | **frontend e2e** | Playwright 시나리오 (해당 화면) |
| L6 | **응답 시간 측정** | cache miss/hit 각각 ≤ SLA |

L3·L4·L5 실패 시 commit 금지. 단순 import OK는 통과로 인정 안 함.

### 데이터 형식 케이스 (L2/L3에서 검증 필수)

- 빈 응답 (`items=[]`, `totalCount=0`)
- null 필드 (`bidNtceNm=null`, `dminsttNm=""`)
- 한글 인코딩 (UTF-8 vs CP949 vs URL-encoded)
- 특수문자 (괄호 `()`·`㈜`·하이픈·점)
- 변형 표기 (회사명·발주기관 분산 표기)
- 길이 (long string·empty string)
- 숫자 vs 문자열 (`bidNtceOrd: "00"` vs `0`)

## 3. v29 진행 단위 (검증 우선 순서)

### v29.1 — backend MCP 직접 호출 검증 sprint
- 사용자 보고 4 case 직접 호출 (vendor_profile 2 / search_bid_notices 1 / search_awards_by_vendor 1)
- raw 응답 + 매칭 결과 + 응답 시간 기록
- 결함 발견 시 즉시 fix → 재검증 → commit

### v29.2 — frontend Playwright e2e 시나리오
- F1~F8 + F10~F17 시나리오 자동 재현
- 각 화면 스크린샷 + console error 캡처
- regression 방지

### v29.3 — gsd-verify 강화 가이드
- `.claude/CLAUDE.md` 또는 docs/VERIFICATION.md에 L1~L6 표준 명문화
- 모든 fix는 commit 전 L3·L4 통과 의무
- 검증 실패 시 fix 재작업

### v29.4 — 누적 fix 효과 통합 검증
- v22.1~v28.1까지 적용된 27 commits 효과를 case 단위로 재검증
- 효과 미달 fix는 root cause 재진단

## 4. F11 agent 결과 통합

진단 중 (background `af1cd8da02b0c023d`). 도착 시 v29.1 첫 case로 활용.

## 5. 자동 진행 정책 갱신

- ❌ 단순 "import OK" / "단위 토큰 매칭 N/N OK"만으로 commit 금지
- ✅ L3 MCP 직접 호출 + L4 사용자 보고 case retrieval 통과 후만 commit
- ✅ commit message에 검증 결과 raw 데이터 포함

## 6. 사용자 액션

본 phase는 **사용자 결함 보고 + 검증 결과 공유**가 핵심 입력. 자동 진행 모드는 검증 절차가 갖춰진 후 재개.
