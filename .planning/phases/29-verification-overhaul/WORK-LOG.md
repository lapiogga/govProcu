# Phase 29 — WORK-LOG (시계열)

## 2026-05-04 (월)

| 시각 (KST) | 행위자 | 작업 | 결과 / 산출물 |
|-----------|--------|------|---------------|
| 00:32 | user | 발화 #31 (오류투성이 / 검증 부족) | 자동 진행 멈춤 트리거 |
| 00:35 | lead | Phase 29 신설 (PLAN.md + WORK-LOG.md) | 검증 절차 L1~L6 표준 정의. 단순 import OK는 통과 인정 안 함. v29.1 backend MCP 직접 호출 sprint 즉시 시작 |
| 00:38 | lead | F11 진단 결과 phase 28에 정리 | P0~P3 4종. P0 즉시 fix 가능 (workflow.py:206 키 불일치). 사용자에게 진행 승인 요청 (3 옵션) |
| 00:48 | cron `6cc910e8` | 자동 갱신 trigger fire #3 (1h 간격) | 점검: PROMPTS-LOG #21~#31(31건) / Phase 28 v28.1 + F11 도착 / Phase 29 신설 / background tasks (backend `bx4cbk05a` 8081, frontend `beonzk7mx` 3000) 모두 기록 정합. logs/WORK-LOG.md 외부 sync hook 미간섭. 다음 cron: 01:07 예상. **no-op (1~2줄 보충 후)** |
| 00:50 | user | 발화 #32 ("진행") | 옵션 A — v29.1.1 fix + L3/L4 검증 진행 |
| 00:52 | lead | v29.1.1 v1 fix | `workflow.py:206` `b_stt_cd`/`b_stt` → `status_code`/`status`/`raw.b_stt_cd` (3중 fallback). cache prefix `vendor_profile_v24` → `vendor_profile_v29` |
| 00:54 | lead | L1 import OK | backend stop(`bx4cbk05a`) → restart(`bo9uxr7h2`) |
| 00:56 | lead | **L3-T2 첫 시도 FAIL** | curl vendor_profile 7028600866 (7일) → HTTP 200, 19.94s, 3982 bytes. but `summary.nts_status_code=null`. sections.nts_status[0].status_code='01' (정상). **fix 무효** — agent F11 진단의 키 이름만으로는 부족 |
| 00:58 | lead | root cause v2 발견 | `_safe_get(d, *keys)`는 dict.get만 지원, list index 처리 안 됨. `_safe_get(..., "items", 0, "status_code")` 호출 시 items가 list라 즉시 default 반환 |
| 01:00 | lead | v29.1.1 v2 fix | nts_items 직접 추출 (`isinstance(nts_items, list) and nts_items` 체크). cache prefix `_v29` → `_v29a`. L2 unit test PASS |
| 01:02 | lead | backend 재기동 (`bo9uxr7h2` → `bsdlr2aiz`) | uvicorn 8081 |
| 01:04 | lead | **L3-T2 + L4-T1 PASS** | (T1) vendor_profile 7028600866: summary.nts_status_code='01' / sections.nts_status[0].status_code='01' / awards_count=0. (T2) vendor_profile 2391602024: 동일 PASS. **P0 fix 검증 완료** |
| 01:06 | lead | v29.1.1 commit (f4e7a8d) | atomic + raw 검증 데이터 commit message 포함 |
| 01:10 | user | 발화 #33 ("진행") | v29.1.2 (P2 V4 병렬화 + P1 has_more) 진행 |
| 01:12 | lead | v29.1.2 적용 | (1) `search_awards_by_vendor` chunks×biz_divs `asyncio.gather` 병렬화 (search_awards/search_bid_notices와 동일 패턴). (2) page loop은 단일 조합 내부 sequential 유지. (3) has_more = `(matches >= limit) or (scanned < total)`, `scan_coverage_pct` 응답 추가. (4) cache prefix `award_vendor_v28` → `award_vendor_v29`. L1 import OK |
| 01:14 | lead | backend 재기동 (`bsdlr2aiz` → `beqdtmz5n`) | uvicorn 8081 |
| 01:18 | lead | **L3 timing 비교 PASS** | (1개월) 32s, total=11801, scanned=9067, coverage=76.8%, matched=0, has_more=True. (1년) 36s, total=17019, scanned=99605, coverage=100%, matched=**1**, has_more=False. **사용자 보고 "낙찰 건수 있다" 검증 완료** — 7028600866 1년 100% 커버에서 1건. P2 1년 timeout 60s+ → 36s 효과. P1 has_more / scan_coverage_pct 노출 효과 |
| 01:25 | user | 발화 #34 ("진행") | v29.1.3 + v29.2 진행 |
| 01:28 | lead | v29.1.3 적용 (P3 cache) | `app/core/cache.py`: `cache_result(empty_ttl=...)` 옵션 + `_is_empty_result` 헬퍼. workflow vendor_profile + award search_awards_by_vendor에 `empty_ttl=cache_ttl_volatile=300` 적용. cache prefix v29a→v29b. L2 unit test 8/8 PASS |
| 01:30 | lead | v29.2 적용 (vendor default 1년) | `vendors/page.tsx` defaultDateFrom 30일→365일. `[bizNo]/page.tsx` from/to 미입력 시 1년 default 적용. 이전 30일 default가 false-negative 유발. 36초 timing은 cursor-wait spinner로 안내 (v22.4 패턴) |
| 01:32 | lead | backend 재기동 (`beqdtmz5n` → `bd4xlhyam`) | uvicorn 8081 |
| 01:34 | lead | **L3 cache TTL 검증 PASS** | `award_vendor_v29b: ttl=298s` (= empty_ttl=300 정상 적용). `vendor_profile_v29b: ttl=1798s` (NTS items 있어 non-empty 판정 — 정상). V4 빈응답은 5분 후 갱신 → 사용자 키발급/재시도 stale 회피 |
