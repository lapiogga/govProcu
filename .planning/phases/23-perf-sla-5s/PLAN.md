# Phase 23 — 성능 SLA 5초 (perf-sla-5s)

> **사용자 SLA (발화 #6)**: "통상 5초 이내에 조회가 되어야 함"
> **운영 모드 (발화 #10)**: 모든 단계 자동 진행, recommended 자동 선택
> **시작**: 2026-05-03 22:10 KST
> **이전 phase**: 22-errors-triage (자율 v22.1~v22.7 commit 완료)

## 1. 현재 측정 (체감) vs 목표

| 화면 | 현재 | 목표 | 격차 |
|------|------|------|------|
| trace (R 형식 채번) | 30~90초 | 5초 | 6~18× |
| agencies 6개월 default | 30~60초 | 5초 | 6~12× |
| bids deep | 20~50초 | 5초 | 4~10× |
| trace (보통 채번) | 5~15초 | 5초 | 1~3× |
| agencies 1개월 명시 | 8~15초 | 5초 | 1.6~3× |

## 2. 자동 진행 순서 (recommended)

| 버전 | 작업 | 효과 | 비용 |
|------|------|------|------|
| **v23.1** | agencies default 180→30일 + trace R 폴백 progressive 복원 | 보통 케이스 5~15초 | 小 |
| **v23.2** | R 형식 폴백 endpoint 단일화 (사용자 입력 biz_type 우선) | trace R 케이스 5~10초 | 小 |
| **v23.3** | trace Suspense Streaming (6단계 → 6 Suspense) | 첫 데이터 1~2초 (체감 5초 ✅) | 中 |
| **v23.4** | G2B chunk 병렬화 (asyncio.gather) — rate-limit 검증 | 1.5~3× | 中 |
| **v23.5** | cache TTL 강화 + Redis 검증 | cache hit 0.5초 | 小 |
| **v23.6** | (별도 sprint) 사전 ETL background fetch | 거의 모든 케이스 cache hit | 大 |

## 3. SLA 달성 시나리오

- **v23.1 + v23.2**: 보통 케이스 5초 SLA 부분 달성 (R 형식 + 짧은 기간)
- **+ v23.3 (Streaming)**: 사용자 체감 5초 SLA 본격 달성
- **+ v23.4**: 모든 케이스 5~10초
- **+ v23.5**: 반복 검색 0.5초 (cache hit)
- **+ v23.6**: 사실상 모든 케이스 < 5초

## 4. atomic commit 단위

각 v23.N마다 atomic commit. PROMPTS-LOG/WORK-LOG 동시 갱신.
관리 Agent cron은 1시간마다 trigger (session-only로 등록됨).
