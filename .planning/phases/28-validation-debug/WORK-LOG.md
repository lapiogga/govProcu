# Phase 28 — WORK-LOG (시계열)

## 2026-05-04 (월)

| 시각 (KST) | 행위자 | 작업 | 결과 / 산출물 |
|-----------|--------|------|---------------|
| 00:05 | user | 발화 #21 (err-011~018 + 702-86-00866) | 8장 결함 + vendor profile 보고 |
| 00:07 | user | 발화 #22 ("여전히 속도가 느림") | F15 — Phase 23 23 commits 후 SLA 미달 |
| 00:08 | user | 발화 #23 (239-16-02024 NTS) | F11 두 번째 사업자번호 동일 결함 |
| 00:10 | lead | 8장 시각 분석 종합 | F5 closure 확인 (err-017 정상) / F10·F11·F12·F13·F14 신규 / F15 재요구 |
| 00:12 | lead | Phase 28 신설 | `PLAN.md` + `WORK-LOG.md`. F11 + F15 우선 |
| 00:18 | user | 발화 #26 ("B") | F17 = /vendors LIKE 화면 |
| 00:22 | user | 발화 #27 (업체명 LIKE 강화) | search_awards_by_vendor 정규화 + 토큰 매칭 |
| 00:26 | lead | v28.1 적용 | (1) `_normalize_vendor_name` 정규화 함수 (공백/(주)/주식회사/㈜/유한회사/사단법인/재단법인/협동조합 등 제거 + lowercase). (2) `_vendor_name_match(query, target)` — 정규화 후 토큰 매칭. (3) `search_awards_by_vendor` 매칭 변경 + cache prefix `award_vendor` → `award_vendor_v28`. (4) `max_scan_per_call` 1000 → 3000 (vendor 매칭률 ↑). 검증 10/10: "(주)아이웨이브"·"㈜아이웨이브"·"아이 웨이브 주식회사"·"아이웨이브주식회사" 모두 매칭, "다른업체"/"한국주식회사" 미매칭 |
| 00:28 | lead | v28.1 commit (c7a3c58) | atomic |
| 00:38 | Agent F11 (`af1cd8da`) | 진단 보고 도착 | **P0 (즉시 fix)**: `workflow.py:206` `b_stt_cd`/`b_stt` → `status_code`/`status` 키 불일치 — frontend `hasAnyData=False` 강제 → "데이터 없음" panel. **P1**: V4 풀스캔 ~150k 모집단 중 ~4k만 스캔 (false-negative). **P2**: V4 직렬 loop (v23.4 병렬화 미적용) → 1년 호출 60s timeout. **P3**: 빈 응답도 30분 cache → 사용자 stale. T1·T2 NTS 정상(status_code=01) 검증 — 사용자 보고와 일치 |
