# Phase 26 — trace Suspense Streaming

> **이전 phase**: 25-port-ops-chore (v25.1 완료)
> **시작**: 2026-05-03 23:25 KST
> **목표**: 5초 SLA 마지막 잠재 효과 — trace 페이지 첫 stage 1~3초 도착으로 사용자 체감 ↑

## 1. 배경

- 현재 (v23.2 + v23.5): `trace_bid_lifecycle` 통합 호출
  - backend 1~4 stage `asyncio.gather` 병렬 → max(stage) ≈ 5~20초
  - 5단계 NTS는 4단계(award) winner_biz_no 의존 → 순차
  - frontend는 1 await → 모든 stage 끝나야 화면
  - cache hit 시 0.5초 (v23.5)
- 사용자 체감: cache miss 시 5~20초 동안 spinner

## 2. 분리 모드 (Streaming) 효과

- frontend 6 server actions으로 stage별 직접 호출
- 각 Suspense fallback이 stage별 도착 즉시 unsuspend
- 첫 stage(사전규격 또는 본 공고) 1~3초 후 화면 등장 → 체감 5초 SLA ✅
- backend 단건 도구 모두 cache 적용 (v23.5) → 두 번째 호출 0.5초

## 3. trade-off

- 통합 호출: 한 cache hit (`trace_lifecycle_v24`)으로 통합 응답 0.5초
- 분리 호출: 5 cache hits (`bid_detail`/`prespec_detail`/`participants`/`award_detail`/none for nts) — 5번 cache 조회 비용. 실제로는 미미함

## 4. 진행 단계

### v26.1 — actions.ts 5 stage actions 추가
- `getPreSpecDetail(bidNo, bidOrd)` → `get_pre_specification_detail`
- `getBidNoticeDetail(bidNo, bidOrd)` → `get_bid_notice_detail`
- `listBidParticipants(bidNo, bidOrd)` → `list_bid_participants`
- `getAwardDetail(bidNo, bidOrd)` → `get_award_detail`
- `checkBusinessStatus(bizNos)` → `check_business_status`
- 기존 `traceBidLifecycle` 그대로 보존 (호환)

### v26.2 — `bids/trace/page.tsx` 리팩토링
- 1 Timeline → 6 sub-component (각자 Suspense + 자체 server action)
- summary header는 stage2(bid_notice) 결과로 채움
- stage5 NTS는 stage4 await 후 winner_biz_no 추출하여 호출 (의존성 처리)
- 단계별 로딩 상태 명시 (각 Stage Skeleton)

### v26.3 (선택) — 의존성 stage 최적화
- stage5 NTS 의존 await chain → server-side 처리 (stage4 + stage5를 한 await로)

## 5. 검증

- frontend type-check 통과
- 사용자 rebuild 후 화면에서 stage별 도착 확인
