# Phase 27 — cache warmup ETL

> **이전 phase**: 26-trace-streaming (v26.1+v26.2 완료)
> **시작**: 2026-05-03 23:50 KST
> **목표**: 사용자 첫 호출 = cache hit (0.5초). 5초 SLA 마지막 단계

## 1. 배경 (cache 인프라 현황)

- `app/core/cache.py`: 이미 Redis 사용 (`redis.asyncio`). cache_result decorator는 Redis SET/GET. TTL 적용. cache 장애 시 우회.
- v23.5/v23.7에서 11개 도구 cache 적용 (search_bid_notices, search_awards, trace_lifecycle 등)
- v23.3에서 cache_ttl_short = 1800 (30분)
- v23 누적: cache miss 시 5~20초, cache hit 시 0.5초

## 2. 미해결 — 첫 사용자 = 항상 cache miss

cache는 사용자 호출 시 채워짐. 첫 호출자 또는 30분 미사용 후 첫 호출은 cache miss → 5~20초.

**해결**: scheduled background warmup이 인기 검색을 미리 호출 → Redis 채움 → 사용자 첫 호출 cache hit.

## 3. v27.1 변경 (single commit)

### scripts/etl_warmup.py (신규)
- 인기 keyword × biz_type 조합 search_bid_notices 호출
- 인기 inst_name × biz_type 조합 search_awards 호출
- 인기 inst_name agency_procurement_history (W5) 호출
- Redis cache 자동 채움 (cache_result decorator 자동)

### POPULAR 데이터 (script 내부)
- POPULAR_KEYWORDS = ["정보화", "구축사업", "유지보수", "용역"]
- POPULAR_AGENCIES = ["국방부", "경찰청", "조달청", "한국수자원공사"]
- POPULAR_BIZ_TYPES = [None, "용역", "공사", "물품"]

### 사용자 등록 (manual)
- Windows Task Scheduler: 30분 간격
- Linux cron: `*/30 * * * *`
- macOS launchd: 30분 간격

## 4. 후속 (별도)

- POPULAR_* 자동 학습 (사용자 검색 빈도 통계 기반)
- 사용자별 personal warmup
