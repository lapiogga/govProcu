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
