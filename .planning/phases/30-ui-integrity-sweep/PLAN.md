# Phase 30 — UI Integrity Sweep (전수 화면 정합성 점검)

> **트리거**: 발화 #35 (2026-05-04 00:53 KST) — "처음부터 다시 각 화면의 정합성을 체크하고, 문제점을 분석하여 체크리스트를 만든 다음, 수정절차를 진행해 줘"
>
> **목표**: 14개 frontend page.tsx 전수 점검 → 결함 분류 → 우선순위별 자동 fix.
>
> **컨텍스트**: Phase 22~29 누적 fix가 부분 영역만 다뤘고, 사용자가 "처음부터 다시" 전수 검증을 요구. Phase 29 L1~L6 검증 표준 + 단순 import OK 통과 인정 안 함 정신을 그대로 계승.

## 1. 점검 대상 화면 (14)

| # | Path | 역할 | backend tool |
|---|------|------|--------------|
| 1 | `/` | 대시보드 홈 (메뉴 카드) | — |
| 2 | `/search` | 통합 검색 (W6 unified_search) | unified_search |
| 3 | `/bids` | 입찰 검색 (W1) | search_bid_notices |
| 4 | `/bids/trace` | 입찰 추적 6단계 (W3) | trace_bid_lifecycle / 5 stage actions |
| 5 | `/vendors` | 업체 인덱스 + LIKE 검색 | search_awards_by_vendor + listMyWatchlist |
| 6 | `/vendors/[bizNo]` | 업체 프로필 (W2) | vendor_profile |
| 7 | `/agencies` | 발주기관 분석 (W5) | agency_profile |
| 8 | `/lookup` | 단건 조회 (개찰결과 등) | get_bid_notice_detail / search_openings_results |
| 9 | `/prediction` | 가격 예측 (V4) | predict_award |
| 10 | `/qualification` | 입찰참가자격 매칭 | search_bid_notices + filter |
| 11 | `/analytics` | 통계 분석 | search_awards 집계 |
| 12 | `/console` | 운영 콘솔 (cache 등) | tool_health / clear_cache |
| 13 | `/me` | 내 즐겨찾기 + 알림 | listMyWatchlist / listAlertRules |
| 14 | `/external/kwater(/contract)` | 외부 (수자원공사) | external API |

## 2. 점검 차원 (8 dimensions)

각 화면을 다음 8 차원으로 진단:

| Dim | 항목 | 검사 방법 |
|-----|------|----------|
| D1 | extract 함수 (extractMcpData 또는 inline) — `content[0].text` JSON.parse 정상? null/undefined 안전? | grep + 코드 리뷰 |
| D2 | summary/sections key naming — backend 실제 응답 키와 frontend 참조 키 일치? | backend tool 응답 schema vs frontend 참조 |
| D3 | 빈 상태 안내 (no data, key missing, error) — 명시적 메시지 노출? "왜 비었는지" 알림? | 코드 검색 (hasAnyData 패턴) |
| D4 | loading UX — Suspense fallback / skeleton / cursor wait? | Suspense / skeleton 컴포넌트 유무 |
| D5 | 에러 경로 — `result.ok === false` 분기 + 사용자 친화 메시지? | result.error 노출 여부 |
| D6 | 기간 default — 너무 짧아 false-negative 유발? scan_coverage 노출? | defaultDateFrom 길이 + has_more/coverage UI |
| D7 | 포맷터 — fmtWon/fmtRate/fmtDate/fmtBizNo 적용 일관성. tabular-nums? | 직접 표시 vs 헬퍼 함수 |
| D8 | 페이지네이션 / has_more — 다음 페이지 진입점, scan 한계 명시? | scan_pages, page param, has_more UI |

## 3. 검증 절차 표준 (Phase 29 계승)

각 fix는 다음 5단계 검증 통과 후 commit:

- **L1 (import)**: backend 재기동 후 import error 없음
- **L2 (unit)**: 영향 함수 단위 테스트 (해당 시)
- **L3 (MCP 직접 호출)**: curl로 backend 응답 raw 검증 (key 존재 + 값 정확)
- **L4 (사용자 case)**: 사용자 보고 사례 (7028600866 / 2391602024 / "정보체계" / "아이웨이브") 데이터 retrieval
- **L5 (frontend)**: localhost:3000 화면 렌더링 + DOM 텍스트 검증 (해당 시)

## 4. 분류 기준

| 우선순위 | 정의 | 예시 |
|---------|------|------|
| P0 | 차단 — 화면 빈 표시 / 크래시 / 잘못된 키 | F11 P0 (vendor_profile nts_status_code null) |
| P1 | 중요 — false-negative / false-positive / UX 혼란 | 짧은 default 기간, has_more 부정확 |
| P2 | 권장 — 성능 / 일관성 | 직렬화된 fetch, 포맷 불일치 |
| P3 | 보완 — 미세 UX / 코드 품질 | 빈 상태 메시지 부재, 포맷터 누락 |

## 5. 수정 절차

1. **CHECKLIST.md 산출** — 14 화면 × 8 dim = 112 cell 매트릭스. 각 셀 OK / WARN / FAIL.
2. **P0 즉시 fix** — atomic commit, L1~L5 검증 후 다음 P0
3. **P1 batch fix** — 관련 항목 묶어서 commit (예: 전 화면 default 기간)
4. **P2/P3는 별도 phase로 deferred** 가능 (사용자 결정)

## 6. 산출물

- `.planning/phases/30-ui-integrity-sweep/PLAN.md` (본 문서)
- `.planning/phases/30-ui-integrity-sweep/WORK-LOG.md` (시계열)
- `.planning/phases/30-ui-integrity-sweep/CHECKLIST.md` (점검 매트릭스)
- `.planning/phases/30-ui-integrity-sweep/DIAGNOSIS-G{1..5}.md` (sub-agent 진단 결과 5개)

## 7. 비-목표

- 신규 기능 추가 (현 점검 범위 외)
- 리팩토링 (정합성 외 코드 품질)
- 백엔드 도구 신설 (응답 키 정합 외)

## 8. 종료 조건

- P0 모두 fix + 검증 통과
- P1 80% 이상 fix
- 14 화면 사용자 화면 검증 (L5) 1라운드 완료
- 사용자 "정합성 OK" 확인
