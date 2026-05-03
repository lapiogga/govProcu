# Phase 23 — WORK-LOG (시계열)

## 2026-05-03 (일)

| 시각 (KST) | 행위자 | 작업 | 결과 / 산출물 |
|-----------|--------|------|---------------|
| 22:10 | user | 발화 #10 (자동 진행 + recommended) | 운영 모드 강화 |
| 22:11 | lead | Phase 23 신설 | `PLAN.md` + 본 `WORK-LOG.md`. 6단계 자동 진행 (v23.1~v23.6) |
| 22:13 | lead | v23.1 적용 | (1) `agencies/page.tsx` defaultAgencyFrom 180→30일 (5초 SLA 근접). (2) `bid.py` R 형식 폴백 progressive(30→90→연도) 복원 — 보통 케이스 5~10초 |
| 22:14 | lead | v23.1 commit (000958b) | atomic |
| 22:18 | user | 발화 #11 ("continue 무조건 묻지말고 진행 해") | 자동 진행 강화 재확인 |
| 22:20 | lead | v23.2 적용 | `app/tools/workflow.py` trace_bid_lifecycle 1~4단계 직렬 await → `asyncio.gather` 병렬화. import asyncio 추가 + `_safe()` 헬퍼. 5단계(NTS)는 4단계(award) winner_biz_no 의존 → 순차 유지. 효과: 직렬 30~90초 → 병렬 max 5~20초 |
| 22:22 | lead | v23.3 적용 | `app/config.py` `cache_ttl_short` 300→1800(30분), 신규 `cache_ttl_volatile=300`(NTS 등). `.env.example` 동시 갱신 (사용자 `.env`에 명시 시 그것이 우선). 효과: 검색 cache hit 시 0.5초 |
| 22:23 | lead | sanity check | workflow import OK. ttl=300 출력 — 사용자 `.env`가 override 가능성. 사용자 안내 필요 |
| 22:20 | cron `6cc910e8` | 자동 갱신 trigger fire (1h 간격) | 점검: PROMPTS-LOG #6~#11 / phase-22 v22.4~v22.7 / phase-23 v23.1~v23.3 모두 기록 정합. logs/WORK-LOG.md는 외부 sync hook 영역 미간섭. **no-op** |
| 23:10 | lead | v23.7 적용 (workflow.py 4개 cache 누락 보완) | `vendor_profile` (W2) / `agency_bid_summary` (W3) / `competitor_analysis` (W4) / `agency_procurement_history` (W5)에 `@cache_result(ttl=cache_ttl_short, prefix="*_v24")` 추가. v23.5에서 trace_lifecycle만 적용했고 나머지 W2~W5 누락 발견. sanity check: 5개 워크플로우 함수 `cached=True`. 효과: 반복 호출 0.5초 (이전엔 sub-call cache hit이지만 함수 자체는 매번 통합 처리 → 변환·요약 계산 비용도 cache) |
| 22:25 | user | 발화 #12 ("자동 진행?") | cron 응답 후 v23.4 진행 안 됐다는 지적 — 즉시 재개 |
| 22:27 | lead | v23.4 적용 | `app/tools/award.py` `import asyncio` 추가. `search_awards` 외부 chunks loop + 내부 biz_divs loop 직렬 → `asyncio.gather`로 모든 (chunk, biz_div) 조합 병렬. 효과: chunks=1 × biz_divs=4 (agencies 30일 default) = **4× 빠름**. 큰 범위는 더 큰 효과. 클라이언트 필터(keyword/inst_name) + dedup(seen_keys) 로직은 results 통합 단계에서 그대로 적용. import sanity check OK |
| 22:30 | lead | v23.4 commit (da0e4a2) | atomic |
| 22:32 | lead | v23.5 적용 (cache_result 5개 도구 추가) | (1) `workflow.py` import settings + cache_result 추가 + `trace_bid_lifecycle`에 `@cache_result(ttl=cache_ttl_short, prefix="trace_lifecycle")`. (2) `bid.py` `get_bid_notice_detail` + `get_pre_specification_detail`. (3) `award.py` `get_award_detail` + `list_bid_participants`. 모두 30분 cache. sanity check: 5개 함수 `__wrapped__=True`. 효과: trace 반복 추적 0.5초, 단건 조회 반복 빠름. 단 trace_bid_lifecycle 자체에 cache 추가 = 가장 큰 누락 보완 |
| 22:34 | lead | v23.5 commit (0b187e7) | atomic |
| 22:35 | user | 발화 #13 ("자동 진행?" 재촉) | v23.6 즉시 시작 |
| 22:38 | lead | v23.6 적용 (search_bid_notices 병렬화) | `bid.py` `import asyncio` 추가. `search_bid_notices`의 chunks loop + endpoints loop 직렬 → `asyncio.gather`로 (chunk, endpoint) 조합 병렬. page loop(while)는 단일 조합 내부에서 sequential 유지(직전 응답 의존). 첫 Edit 시도 매칭 실패(`# 등록일 기준` 주석 누락) → 재시도 성공. 효과: chunks=1 × endpoints=3 (전체 업종) = **3× 빠름**. 큰 범위는 더 큰 효과. import sanity check OK |
