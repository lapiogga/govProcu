# Phase 24 — 발주기관·업체명 매칭 강화 (vendor-matching)

> **이전 phase**: 23-perf-sla-5s (v23.1~v23.6 완료)
> **시작**: 2026-05-03 22:42 KST
> **목표**: F3 (발주기관 분석 데이터 부재) 정정 + 매칭률 향상

## 1. 배경 (F3 진단 — Phase 22 ROOT-CAUSE)

`/agencies?name=경찰청 경찰대학` → "데이터 없음 (낙찰률 데이터 없음)".

**원인**: `app/tools/award.py:269-272`
```python
if inst_name:
    inst = (raw.get("dminsttNm") or "") + " " + (raw.get("ntceInsttNm") or "")
    if inst_name not in inst:
        continue
```
- 부분일치(`in`) 단일 검사 → 변형 표기 미매칭
- "경찰청 경찰대학" vs G2B `dminsttNm="경찰청"` + `ntceInsttNm="경찰대학"` → 결합 "경찰청 경찰대학" 정확. but `dminsttNm=""` + `ntceInsttNm="경찰대학"` → " 경찰대학" → "경찰청" 토큰 빠져 fail.

## 2. 자동 진행 단위

### v24.1 — 토큰 기반 매칭 (작은 변경)
`inst_name`을 공백 분리한 모든 토큰이 결합 inst에 포함되면 매칭:
```python
inst_tokens = [t for t in inst_name.split() if t]
if not all(t in inst for t in inst_tokens):
    continue
```
- "경찰청 경찰대학" → 토큰 ["경찰청", "경찰대학"] → 둘 다 inst에 있어야
- 단일 토큰 ("경찰청") 입력 시 모든 경찰청 산하 매칭 (의도)

같은 패턴을 `app/tools/bid.py:196` 의 `inst_name` 필터에도 적용 (정합).

### v24.2 — 응답 샘플 안내 (사용자 학습)
매칭 0건 시 `analytics.py` `analyze_agency_price_pattern`이 G2B 응답에서 본 inst 표기 상위 3개를 `note`에 첨부.

### v24.3 — cache invalidate 신호
v24.1 매칭 로직 변경 → 기존 `award_list` cache는 (args 동일 시) stale하지 않으나 결과 다를 수 있음. prefix를 `award_list_v24`로 bump.

## 3. 후속 (별도)

- Levenshtein/Jaro-Winkler 유사도 기반 매칭 (의존성 추가, 큰 변경)
- 발주기관 자동완성 UI (frontend, 별도 sprint)
