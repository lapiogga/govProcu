# DIAGNOSIS-G3 — vendor 화면 정합성 진단

> **점검 대상 (G3)**: 2 화면
>
> 1. `frontend/src/app/vendors/page.tsx` — 업체 인덱스 + 사업자번호 redirect + 업체명 LIKE 검색 + 즐겨찾기
> 2. `frontend/src/app/vendors/[bizNo]/page.tsx` — 업체 프로필 W2 (NTS 진위 + 입찰/응찰/개찰/낙찰 통계)
>
> **연관 backend**: `vendor_profile` (W2, Phase 29 v29.1.1 fix), `search_awards_by_vendor` (V4, v28.1 + v29.1.2 fix)
>
> **점검자**: G3 sub-agent (2026-05-04)
> **점검 기준**: PLAN.md 8 dimensions × OK / WARN / FAIL 분류

---

## 0. 핵심 요약

- **P0 (차단)**: 0건 — Phase 29 fix가 frontend 참조 키와 정확히 일치 (`summary.nts_status_code`, `sections.awards.items[].open_date|bid_title|inst_name|award_amount|award_rate` 모두 정합).
- **P1 (중요)**: 4건 — `has_more`/`scan_coverage_pct` UI 미노출 / `loading UX 미흡(36초 대기 대비 부족)` / `vendor 프로필 페이지 기간 변경 form 부재` / `vendor index has_more 표시 누락`.
- **P2 (권장)**: 3건 — `extractData` 중복 정의 (extractMcpData 미사용) / `summary.win_rate_pct.toFixed(2)` null-safe 누락 / `sections.awards?.items?.length > 0` JSX boolean coercion (TS lint 경고 가능).
- **P3 (보완)**: 2건 — `implementation_status` 표시 위치 중복 / 빈 상태에서 사용자 가이드 링크 부재.

**최우선 권장 fix**: **P1-1 has_more / scan_coverage_pct UI 노출** + **P1-2 loading UX 강화 (36초 대기 명시 + spinner)**.

---

## 1. 화면별 / 차원별 진단 매트릭스

### 화면 1: `/vendors` (page.tsx)

| Dim | 평가 | 근거 (line) | 분류 |
|-----|------|-------------|------|
| **D1 extract** | OK | line 131-146: `extractMcpData<{items?, total_count?, scanned?, returned_count?}>` 안전. `data?.items \|\| []` null 안전. | OK |
| **D2 key naming** | OK | backend `search_awards_by_vendor` 응답 (`items`, `total_count`, `scanned`, `returned_count`) 정합. winner_biz_no/winner_name/award_amount/open_date 모두 `_normalize_award_row` 키와 정확 일치. | OK |
| **D3 빈 상태** | OK | line 197-200: "매칭되는 후보 없음. 다른 키워드 또는 기간 확장." 안내. RecentVendors 빈 상태도 line 256-262 명시. | OK |
| **D4 loading UX** | OK | line 95, 104: Suspense + Skel 컴포넌트. NameSearchResults는 V4 병렬화 후 1년 36초 → fallback 표시. | OK (개선 여지: skeleton 너무 단순) |
| **D5 에러 경로** | OK | line 121-128: `if (!r.ok)` 분기 → `오류: {r.error}` 사용자 노출. | OK |
| **D6 기간 default + has_more** | **WARN** | defaultDateFrom 1년 (line 309-316) v29.2 적용 OK. **그러나 `has_more` / `scan_coverage_pct` 응답 키를 frontend가 사용하지 않음** — 사용자에게 "스캔 커버리지 X%, 추가 검색 권장" 안내 부재. | **P1** |
| **D7 포맷터** | OK | fmtWon (line 224), fmtDate (line 227) 일관 적용. tabular-nums 일관. | OK |
| **D8 페이지네이션** | **FAIL** | limit=30 고정 (line 120). `has_more=true` 시 다음 페이지 진입점 없음. `total_count` vs `returned_count` 차이 노출 안 됨 (line 194: `returned_count` 단독 표시). | **P1** |

**그룹화 로직 검증** (line 161-182):
- `winner_biz_no` 정규화 (`replace(/\D/g, "")`) OK — backend `_normalize_biz_no`도 하이픈 제거 → 양쪽 정합.
- `groups.set(key, ...)` Map 순회 정상.
- 정렬 기준 `total_amount` 내림차순 (line 184-186) 합리적.
- **WARN**: `latest_date` 비교 시 `(it.open_date || "") > cur.latest_date` — 빈 문자열 비교는 사실상 모든 값이 우선순위 가짐 (단, 사용자가 보는 결과에는 큰 영향 없음).

### 화면 2: `/vendors/[bizNo]` ([bizNo]/page.tsx)

| Dim | 평가 | 근거 (line) | 분류 |
|-----|------|-------------|------|
| **D1 extract** | **WARN** | line 252-269: `extractData()` 인라인 정의. `extractMcpData` 헬퍼 미사용 (lib/extract.ts에 동일 로직 존재). 동작은 정상이나 중복. | **P2** |
| **D2 key naming** | OK | Phase 29 fix 키 (`summary.nts_status_code`) frontend line 92, 121 정확 참조. `sections.{awards,participations,openings,bids}.items` 정합. `a.bid_notice_no/bid_ord/bid_title/inst_name/award_amount/award_rate/open_date` 모두 `_normalize_award_row` 출력 키와 1:1 매칭. | OK |
| **D3 빈 상태** | OK | line 86-115: `hasAnyData` 검증 + 4개 가능 원인 + `implementation_status` 노출. F7 v22.5 패턴 유지. | OK |
| **D4 loading UX** | **FAIL** | line 44: Suspense fallback `<ProfileSkeleton />` 적용. **그러나 1년 default = 36초 대기인데 skeleton 5칸만 표시 — "검색 중 (최대 1분 소요)" 명시적 안내 없음**. 사용자가 멈춘 줄 알고 페이지를 닫을 가능성. line 12 주석 "cursor-wait + spinner로 안내" 의도와 실 구현 불일치. | **P1** |
| **D5 에러 경로** | OK | line 62-68: `result.ok === false` 처리. line 70-81: `extractData` null 시 별도 안내 ("응답 파싱 실패"). | OK |
| **D6 기간 default + has_more** | **FAIL** | defaultFromY 1년 (line 11-16) v29.2 적용 OK. **그러나 `searchParams`만 받음 — 사용자가 기간 변경하려면 URL 수동 편집 필요. <form>이 없음**. 또한 `sections.awards.has_more`, `sections.awards.scan_coverage_pct` 어디에도 노출 안 됨. | **P1** |
| **D7 포맷터** | OK | fmtWon (line 139, 198), fmtRate (line 201), fmtDate (line 185), fmtBizNo (line 37) 일관. tabular-nums 일관 (line 184, 197, 200). | OK |
| **D8 페이지네이션** | N/A | 단건 vendor 프로필 — 페이지네이션 적용 대상 아님. 단, `최근 낙찰 X건` 표시 후 `slice(0, 10)` 하드코딩 (line 182). limit=50 호출 (actions.ts 미지정 → 기본값) vs UI 10건만 표시 — 사용자가 11~50번 row 못 봄. | **P3** |

**추가 발견**:
- **P2**: line 144-155 `summary.win_rate_pct.toFixed(2)` — backend는 `round(win_rate, 2)` number 반환 (workflow.py line 224). `null` 가드 (`!= null`) 있어 안전. 그러나 만약 backend가 `"NaN"` 등 string으로 우회 반환 시 런타임 에러 — 방어 약함.
- **P3**: line 211 `구현 상태` 표시가 line 110 빈 상태 패널과 중복 출력 — 데이터 있는 케이스에선 불필요하게 노출.
- **P2**: line 158 `sections.awards?.items?.length > 0` — `length`가 `undefined`면 `undefined > 0 === false` 동작은 OK이나 TypeScript strict 모드에서 lint 경고 (`(0 | undefined) > 0`). 이미 line 88-91에서 `?? 0` 패턴 사용 → 일관성 결여.

---

## 2. Phase 29 fix 노출 검증 (가장 우선)

| Phase 29 fix | backend 키 | frontend 참조 | 노출 여부 |
|--------------|-----------|---------------|-----------|
| v29.1.1 nts_status_code (status_code/status/raw.b_stt_cd 3중 fallback) | `result.summary.nts_status_code` | `[bizNo]/page.tsx:92, 121-126` | **PASS** — 정확 일치, "✅ 계속사업자" 표시 동작. |
| v29.1.2 V4 chunks×biz_divs 병렬화 | (성능만 영향) | — | **PASS** — frontend는 시간만 단축됨, 코드 변경 무관. |
| v29.1.2 has_more = (matches >= limit) or (scanned < total) | `sections.awards.has_more` | **참조 없음** | **FAIL** — backend 신호가 사용자에게 전달 안 됨. |
| v29.1.2 scan_coverage_pct | `sections.awards.scan_coverage_pct` | **참조 없음** | **FAIL** — 동일. |
| v29.2 frontend default 1년 | (frontend 변경) | `page.tsx:309-316`, `[bizNo]/page.tsx:11-16` | **PASS** — 두 화면 모두 1년 적용. |

**결론**: backend nts_status_code key fallback과 default 기간 변경은 frontend에 **정확히** 도달하지만, **has_more/scan_coverage_pct 사용자 시각화는 미실현**. v29.1.2 P1 fix가 화면에 반영 안 된 상태.

---

## 3. 사용자 보고 사례 회귀 검증

| 사례 | 화면 | 예상 동작 | 코드 검증 결과 |
|------|------|-----------|----------------|
| 7028600866 1년 1건 매칭 | `/vendors/7028600866` | 1년 default → vendor_profile 조회 → 낙찰 1건 표시 | OK — defaultFromY 1년 + summary.awards_count 표시 + sections.awards.items[0] 표 노출 경로 정상. |
| 2391602024 NTS 진위 | `/vendors/2391602024` | summary.nts_status_code "01" → "✅ 계속사업자" | OK — line 121-124 정확 매칭. |
| "정보체계" LIKE | `/vendors?name=정보체계` | search_awards_by_vendor 호출 → 후보 N개 그룹 | OK — line 120 호출, 그룹화 정상. 단, 1년 36초 대기 시 사용자 ABANDON 위험 (D4 P1). |
| "아이웨이브" LIKE | `/vendors?name=아이웨이브` | _vendor_name_match 정규화 매칭 → "(주)아이웨이브" 등 표기 차이 흡수 | OK (backend) — frontend는 결과만 표시. UI 정합 OK. |

---

## 4. Sub-component import 정합

| import | 실 사용 | 정합 |
|--------|---------|------|
| `VendorAwardChart` from `@/components/charts/VendorAwardChart` | line 161 `<VendorAwardChart items={sections.awards.items} />` | OK — 컴포넌트의 `items: AwardItem[]` interface (`open_date`, `award_amount`)와 backend `_normalize_award_row` 키 일치. |
| `AgencyLink, BidLink` from `@/components/EntityLink` | line 188-195 | OK — `BidLink`의 `bidNo/ord/title` props와 `a.bid_notice_no/a.bid_ord/a.bid_title` 매칭. `AgencyLink`의 `name` props와 `a.inst_name` 매칭. |
| `VendorLink` (vendors/page.tsx line 20) | line 219, 284 | OK — `bizNo/name` props 정합. line 284 `formatBizNo` flag로 사업자번호 하이픈 표시. |
| `extractMcpData, fmtWon, fmtDate` (vendors/page.tsx line 15-16) | line 145, 224, 227 | OK. |

**모든 sub-component import 정합 OK**. 빠진 import 없음.

---

## 5. 우선순위별 fix 권장

### P1 (중요 — 즉시 fix 권장)

| ID | 항목 | 화면 | 위치 | fix 제안 |
|----|------|------|------|----------|
| P1-1 | has_more / scan_coverage_pct 미노출 | 두 화면 | NameSearchResults header / Profile awards section | `data.has_more && <Badge>스캔 {scan_coverage_pct}% — 추가 검색 권장</Badge>` 형태로 노출. |
| P1-2 | 36초 대기 loading UX 미흡 | `/vendors/[bizNo]` | line 236-250 ProfileSkeleton | "검색 중 (최대 1분 소요)" 텍스트 + animated spinner. cursor-wait class 적용. |
| P1-3 | vendor 프로필 기간 변경 form 부재 | `/vendors/[bizNo]` | line 33-48 header | from/to input + "재조회" 버튼 추가 (vendors/page.tsx line 68-86 동일 패턴). |
| P1-4 | vendor index 페이지네이션 부재 | `/vendors` | NameSearchResults | limit=30 고정 → page param + has_more 체크 + "더 보기" 링크. |

### P2 (권장)

| ID | 항목 | 화면 | 위치 | fix 제안 |
|----|------|------|------|----------|
| P2-1 | extractData 중복 정의 | `/vendors/[bizNo]` | line 252-269 | `import { extractMcpData } from "@/lib/extract"` 사용. |
| P2-2 | win_rate_pct.toFixed null-safe | `/vendors/[bizNo]` | line 149 | `typeof summary.win_rate_pct === 'number' && summary.win_rate_pct.toFixed(2)`. |
| P2-3 | sections.awards?.items?.length > 0 일관성 | `/vendors/[bizNo]` | line 158, 166 | `(sections.awards?.items?.length ?? 0) > 0`로 통일 (line 88-91 패턴). |

### P3 (보완)

| ID | 항목 | 화면 | 위치 | fix 제안 |
|----|------|------|------|----------|
| P3-1 | implementation_status 중복 노출 | `/vendors/[bizNo]` | line 110, 211 | 데이터 있을 때 line 211 노출 생략 (또는 collapsible). |
| P3-2 | sections.awards.items.slice(0, 10) 하드코딩 | `/vendors/[bizNo]` | line 182 | "더 보기" 토글 또는 limit 인자화 (50건 호출인데 10건만 표시). |
| P3-3 | latest_date 빈 문자열 비교 | `/vendors` | line 170-172 | `if (it.open_date && it.open_date > cur.latest_date)` 명시. |

---

## 6. 최종 OK / WARN / FAIL 카운트

| 화면 | OK | WARN | FAIL | N/A |
|------|----|------|------|-----|
| `/vendors` | 6 | 1 (D6) | 1 (D8) | 0 |
| `/vendors/[bizNo]` | 4 | 1 (D1) | 2 (D4, D6) | 1 (D8) |
| **합계** | **10** | **2** | **3** | **1** |

**Phase 29 P0 fix는 frontend에 정확히 도달**. P1 fix 4건 적용 시 사용자 체감 정합성 100% 달성 예상.
