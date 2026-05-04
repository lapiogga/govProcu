# Phase 30 — CHECKLIST (통합 점검 매트릭스)

> 5개 sub-agent (G1~G5) 진단 결과 통합. 14 화면 × 8 dim. 우선순위별 fix 계획.
>
> **분류**: P0 (차단/크래시/잘못된 키) / P1 (false-negative·UX 혼란) / P2 (권장) / P3 (보완)
>
> 각 fix는 Phase 29 검증 절차 (L1 import / L2 unit / L3 MCP 직접 호출 / L4 사용자 case / L5 frontend 화면) 통과 후 commit.

---

## 0. 화면별 진단 OK/WARN/FAIL/N/A 합계

| 그룹 | 화면 수 | OK | WARN | FAIL | N/A | P0 | P1 | P2 | P3 |
|------|---------|----|------|------|-----|----|----|----|----|
| G1 (홈+검색) | 2 | 2 | 1 | 0 | 13 | 0 | 2 | 2 | 3 |
| G2 (입찰/추적/단건) | 3 | 14 | 7 | 1 | 2 | 1 (+1 격상) | 7 | 3 | 8 |
| G3 (업체) | 2 | 10 | 2 | 3 | 1 | 0 | 4 | 3 | 3 |
| G4 (분석/예측/자격) | 4 | 18 | 12 | 4 | 2 | 3 | 4 | 6 | 4 |
| G5 (운영/내정보/외부) | 4 | (22+) | (10+) | — | — | 0 | 6 | 12 | — |
| **합계** | **14** | — | — | — | — | **5** | **23** | **26** | **18+** |

> 자세한 매트릭스는 `DIAGNOSIS-G{1..5}.md` 참조.

---

## 1. P0 (즉시 fix — 5건)

| ID | 화면 | 결함 | Evidence | Fix 제안 |
|----|------|------|----------|----------|
| **P0-A** | `/bids/trace` Stage5 | NTS 응답 키 `b_stt_cd`(raw) 직접 참조. backend `check_business_status`는 `status_code`로 정규화 (vendor.py:111-112) → ntsLabel 항상 fallback "—" | `frontend/src/app/bids/trace/page.tsx:406` `const code = first.b_stt_cd;` | `first.status_code \|\| first.b_stt_cd` (3중 fallback). `first.status \|\| first.b_stt`도 동일 |
| **P0-B** | `/agencies` PriceCard | backend `summary_pct` 9-key 중 `p75` 누락. Stat 슬롯이 `mean/median/p10/p25/p90`만 5개 — 목표 낙찰확률 0.7 시나리오 핵심 분위 부재 | `frontend/src/app/agencies/page.tsx:183-189` | Stat 1개 추가 `<Stat label="p75" value={s.p75?.toFixed(2)+'%'} />`. grid-cols-5 → grid-cols-6 또는 lg:grid-cols-9 |
| **P0-C** | `/analytics` 시장점유 표 | `<VendorLink bizNo={v.biz_no} name={v.biz_no}>` — `name`에 raw 10자리 입력. fmtBizNo 미적용 → "1234567890" 그대로 표시 | `frontend/src/app/analytics/page.tsx:186-192` | `<VendorLink bizNo={v.biz_no} formatBizNo />` 또는 `name={v.name}` (이미 v.name 별도 컬럼이라 명확화) |
| **P0-D** | `/lookup` mode=biz/inst | backend `lookup_by_inst_code`는 keys={inst_code, inst_name}만, `lookup_by_biz_no`는 keys={vendor_biz_no}만 반환. frontend는 4-카드 그리드를 항상 그려 bid_notice_no/contract_no 카드 항상 "—" → cross-lookup 핵심 가치 손실 | `frontend/src/app/lookup/page.tsx` + `app/tools/lookup.py:156-160, 236` | **backend 표준화**: lookup_by_inst_code/biz_no가 keys에 4 키 항상 포함 (없는 키는 None). 또는 **frontend 분기**: mode별 다른 카드 레이아웃 |
| **P0-E** | `/agencies` `/analytics` 차트 | Tremor v3 + Tailwind v4 zero-config → `tremor-*` 토큰 미정의로 차트 검은색 사각형 (F10) | `frontend/tailwind.config` 부재, globals.css `@theme` tremor 토큰 없음 | **별도 Phase 31 권장** — Tremor v4 migration 또는 토큰 globals.css 주입. fix 범위 큼 |

---

## 2. P1 (중요 — 사용자 보고 사례 직결)

| ID | 화면 | 결함 | 사용자 사례 매핑 | Fix 제안 |
|----|------|------|------------------|----------|
| P1-01 | `/bids` | `scan_coverage_pct`/`chunks_used`/`endpoints_used` 미노출 — false-negative 인지 불가 | F16 "정보체계" 0건 | 결과 헤더에 `<Badge>스캔 X% (Y개월 × Z endpoint)</Badge>` 추가 |
| P1-02 | `/bids` | `buildHref`에 `deep`/`sort` 보존 누락 — 페이지 이동 시 deep 풀림 | F16 깊은 검색 1페이지만 동작 | `buildHref({page, deep, sort})`에 deep/sort 포함 |
| P1-03 | `/bids/trace` | 5 Stage 모두 `r.ok === false` 분기 누락 — 통신 오류와 데이터 미발견 동일 표시 | F2 trace 빈 결과 | 각 Stage 컴포넌트 시작에 `if (!r.ok) return <ErrorBox>`  |
| P1-04 | `/bids/trace` | backend `note` 필드(미발견 사유) 무시 — 6단계 비어있어도 "왜"를 알 수 없음 | F2 잔존 | `<StageNote>{data?.note}</StageNote>` 추가 |
| P1-05 | `/search` → `/bids` redirect | `deep` 파라미터 미전달 — 30일 default + scan_pages=1 → 0건 위양성 | F16 "정보체계", "아이웨이브" 0건 | `redirect(/bids?q=${q}&deep=1)` (또는 longer default 기간) |
| P1-06 | `/vendors` `/vendors/[bizNo]` | `has_more`/`scan_coverage_pct` UI 미노출 — v29.1.2 backend fix가 사용자에게 도달 안 함 | (Phase 29 효과 무력) | header/section에 `<Badge>` 추가 |
| P1-07 | `/vendors/[bizNo]` | 36초 대기 loading UX 미흡 — skeleton만, "최대 1분 소요" 안내 없음 | (사용자 abandon 위험) | ProfileSkeleton에 spinner + 진행 메시지 추가 |
| P1-08 | `/vendors/[bizNo]` | 기간 변경 form 부재 — URL 수동 편집 필요 | (UX) | header에 from/to + 재조회 form 추가 (vendors/page.tsx 패턴) |
| P1-09 | `/vendors` | 페이지네이션 부재 — limit=30 고정 | (truncation) | page param + has_more + "더 보기" 링크 |
| P1-10 | `/agencies` | sp.name 시 30일 default — 큰 기관(재정관리단/국방부) 30일 내 0건 가능성 | F12, F13 | default 90일 또는 365일. 큰 기관 휴리스틱 안내 |
| P1-11 | `/analytics` | sp.from/to 미입력 시 backend `undefined` 호출 — G2B inqryBgnDt 누락 → 0건/rate_limit | (운영 위험) | default 1년 또는 365일. defaultDateFrom/To 헬퍼 |
| P1-12 | `/qualification` | 점검 의도(search_bid_notices+filter)와 실제(calc_qualification_score) 불일치 | (의도 확인 필요) | 화면 의도 정정 또는 별도 매칭 화면 신설 |
| P1-13 | `/console` | PLAN §1 #12 `tool_health`/`clear_cache` backend 미구현 | (운영 콘솔 가치 절반) | backend 도구 신설 — 별도 phase |
| P1-14 | `/me` | 에러 사일런트 흡수 | (관측성) | `r.ok` 분기 + 토스트/배너 |
| P1-15 | `/external/kwater` | KWATER_API_KEY 미설정 시 사용자 무인지 | (외부 통합 옵셔널) | 명시적 안내 |
| P1-16 | `/external/kwater` | 페이지네이션 부재 | — | page param + has_more |
| P1-17 | `/lookup` mode=biz | `summary.bid_notice_no_list` 미노출 | "이 업체가 받은 공고" 직접 표시 안 함 | bid_notice_no_list 표 추가 |
| P1-18 | `/lookup` mode=biz/inst | 기간 입력 form 부재 → backend 무기간 호출 (G2B 1개월 chunk 자동) | (timeout 위험) | from/to input 추가 |
| P1-19 | `/agencies` | `r.ok === false` 분기 부재 → silent fail | (관측성) | error box 추가 |
| P1-20 | `/analytics` | `r.ok` 미체크 → "데이터 없음"만 표시 | (관측성) | error box 추가 |
| P1-21 | `/prediction` | ScenarioTable r.ok 체크 누락 | (관측성) | 동일 |
| P1-22 | `/agencies` | `agency_procurement_history` backend has_more 키 미반환 | (truncation 인지 불가) | backend 추가 + frontend 노출 |
| P1-23 | `/analytics` | trend/share has_more/scan_coverage 미노출 | (truncation) | backend 추가 + frontend 노출 |

---

## 3. P2 (권장 — 26건, 묶어서 batch fix)

대표 항목:
- P2-01: `extractMcpData` 헬퍼 미사용 (bids/trace/[bizNo] inline 중복)
- P2-02: `summary.bidNtceNm` raw camelCase fallback chain (죽은 분기)
- P2-03: cache prefix `_v29b` 잔존 (award.py:459, workflow.py:119)
- P2-04: fmtRate / fmtWon 일관성 부족 (직접 toFixed 호출)
- P2-05: `add-watchlist-dialog` `contract` 타입 누락
- P2-06: 구독 폼 4/5 필드만 노출
- P2-07: `target` 라벨 vs backend 매핑 — G4 진단에서 OK 정정됨

---

## 4. P3 (보완 — 18+건)

- 메뉴 카드 라벨 의미 명확화
- 7-digit input 묵시적 fallback 주석
- `slice(0, 10)` 하드코딩 → "더 보기" 토글
- TableSkeleton cursor-wait 일관성
- footer 환경변수 production 비표시
- 빈 응답 사유 구분 (LIKE 0건 / 입력 누락 / 백엔드 0건)

---

## 5. 자동 Fix 진행 계획

### Round 1 — P0 small fixes (atomic commit)

- P0-A (trace NTS 키)
- P0-B (agencies p75)
- P0-C (analytics fmtBizNo)
- → 1 commit `fix(frontend): P0 small — trace NTS / p75 / fmtBizNo 정합 (Phase 30)`

### Round 2 — P0-D backend keys 표준화

- backend `lookup_by_inst_code`/`lookup_by_biz_no` keys 4-key 표준화 (없는 키는 None)
- frontend 분기 제거
- → 1 commit `fix(backend): lookup keys 4-key 표준화 — cross-lookup 정합 (Phase 30)`

### Round 3 — P1 batch (사용자 보고 사례 직결)

- P1-01 + P1-02: bids scan_coverage 노출 + buildHref deep 보존
- P1-03 + P1-04: trace Stage r.ok 분기 + note 노출
- P1-05: /search redirect deep=1
- P1-06 + P1-09: vendors has_more / 페이지네이션
- → 2~3 commits (영역별)

### Round 4 — P1 default 기간 + 에러 분기 batch

- P1-10 + P1-11: agencies/analytics default 기간 1년
- P1-19 + P1-20 + P1-21: r.ok 체크 추가
- → 1 commit

### Deferred (별도 phase)

- P0-E (F10 차트, Tremor v4)
- P1-12 (qualification 의도 정정 — 사용자 확인 필요)
- P1-13 (console backend 도구 신설)
- P1-22 + P1-23 (backend has_more 추가 + frontend 노출)
- P2 26건 (batch — 가독성/일관성 개선)

---

## 6. 검증 절차 (각 commit 별)

| 단계 | 검증 |
|------|------|
| L1 | backend/frontend 재기동 후 import error 없음 |
| L2 | 영향 함수 단위 테스트 (해당 시) |
| L3 | curl로 backend 응답 raw 검증 (key 정합) |
| L4 | 사용자 case retrieval (7028600866 / 2391602024 / "정보체계" / "아이웨이브" / "재정관리단") |
| L5 | localhost:3000 화면 렌더링 확인 (해당 시) |

---

## 7. 종료 조건

- P0 5건 모두 fix (P0-E는 deferred 사유 명시)
- P1 23건 중 사용자 보고 사례 직결 항목 (F2/F12/F13/F16) 100% fix
- 14 화면 사용자 화면 검증 1라운드 완료
- 사용자 "정합성 OK" 확인
