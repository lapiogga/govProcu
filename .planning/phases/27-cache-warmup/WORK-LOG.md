# Phase 27 — WORK-LOG (시계열)

## 2026-05-03 (일)

| 시각 (KST) | 행위자 | 작업 | 결과 / 산출물 |
|-----------|--------|------|---------------|
| 23:50 | lead | Phase 27 신설 | `PLAN.md` + `WORK-LOG.md` |
| 23:53 | lead | cache.py read | 이미 Redis (`redis.asyncio`) 사용 — backend 변경 불필요 |
| 23:55 | lead | v27.1 적용 | `scripts/etl_warmup.py` 신규 (130줄). POPULAR_KEYWORDS × biz_type → search_bid_notices, POPULAR_AGENCIES × biz_type → search_awards, POPULAR_AGENCIES → agency_procurement_history. 30일 range. import sanity check OK. 사용자 등록은 manual (Windows Task Scheduler / cron) |
