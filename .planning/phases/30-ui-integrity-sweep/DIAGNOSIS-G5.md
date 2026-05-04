# DIAGNOSIS-G5 — 운영/내활동/외부 화면 정합성 진단

> 점검 대상 4 화면, 8 차원 매트릭스 — Phase 30 (2026-05-04)
>
> 점검자 입장: PLAN.md §3 L1~L5 검증 정신, §4 P0~P3 분류 표준 적용. 코드 수정 금지 — 진단만.

---

## 0. 점검 대상

| # | Path | 역할 | 핵심 backend tool |
|---|------|------|--------------------|
| G5-1 | `/console` | AI 자연어 콘솔 (LLM 도구 호출) | (Anthropic API 직접 + MCP 5종 화이트리스트) |
| G5-2 | `/me` | 즐겨찾기 + 키워드 알림 구독 | `list_my_watchlist`, `list_my_subscriptions`, `add/remove`, `subscribe/unsubscribe_keyword_alerts` |
| G5-3 | `/external/kwater` | 한국수자원공사 계약공개 (월 단위) | `search_kwater_contracts` |
| G5-4 | `/external/kwater/contract` | KWater 계약 단건 상세 (query params) | (없음 — query params 만 사용) |

---

## 1. 결론 (1-line per 화면)

| 화면 | 결론 | 최고 심각도 |
|------|------|-------------|
| `/console` | 페이지 이름·하단 fooler가 시사하는 "60개 도구 + tool_health/cache 통계/clear_cache" 운영 콘솔 기능이 **전무** — 단순 Anthropic chat 5-tool 화이트리스트 데모. PLAN.md §1 #12 명시 backend(`tool_health`/`clear_cache`) 자체가 미구현 | **P1** |
| `/me` | watchlist/subscription 정합 OK. Suspense·빈 상태·서버 액션 모두 정상. 단 `add` Dialog가 `contract` 타입을 의도적으로 제외(P3), 구독 폼 amount 범위·region·kakao 필드 미노출(P3) | **P3** |
| `/external/kwater` | 핵심 데이터 흐름 정상 — 어댑터·정규화·검색 폼·테이블·상세 진입까지 정합. 단 `r.ok===false` 분기에서 `data.status` 미노출 (특히 `pending_key`) — KWATER_API_KEY 미설정 시 사용자에게 원인 안 보임 (P1). 5월 default 가 1년 전 동월 (P3 OK) | **P1** |
| `/external/kwater/contract` | query-param 기반 단건 표시 기능 OK. 단 query 손실/조작 시 fallback 부족, "이행기간 -" 표시 일관성 누락 (P3) | **P3** |

---

## 2. /console — 8 차원 매트릭스

| Dim | 항목 | 결과 | 근거 (file:line) |
|-----|------|------|------------------|
| D1 | extract — `extractData(raw)` 인라인 (`content[0].text` JSON.parse) — null 안전 OK | **OK** | `console/page.tsx:190-203` |
| D2 | key naming — 5 tool 화이트리스트 (`trace_bid_lifecycle`, `vendor_profile`, `search_bid_notices`, `agency_procurement_history`, `predict_bid_price`) — backend 도구명 일치 | **OK** | `api/chat/route.ts:36-105` vs `app/server.py` |
| D3 | 빈 상태 — `displayMessages.length === 0` 안내 + 데모 mode 토글 OK. tool 호출 후 결과 빈 dict 시 fallback JSON dump | **OK** | `console/page.tsx:81-92, 183-187` |
| D4 | loading UX — `isLoading` 시 "AI가 도구를 호출하는 중…" 한 줄 표기. tool result 도착 시 `BidLifecycleCard` 렌더 (Suspense 미사용 — streaming 채널) | **OK** | `console/page.tsx:123-127` |
| D5 | 에러 경로 — `useChat` 자체 error 노출 채널 없음. tool execute 내 `result.data ?? { error: result.error }` 만 (상위 표시 없음). ANTHROPIC_API_KEY 미설정 시 에러 메시지 표면화 안 됨 | **P1 WARN** | `api/chat/route.ts:48-50, 60-61, 76, 89-90, 103-104` |
| D6 | 기간 default — chat tool이 `date_from/to` 옵셔널, 자연어로 LLM 위임 — 명시 default 없음 (LLM이 추론). | **OK (의도)** | `api/chat/route.ts:55-56, 69-70` |
| D7 | 포맷터 — generative tool 결과 `BidLifecycleCard` 만 컴포넌트 매핑. 그 외는 raw JSON dump → fmtWon/fmtDate 미적용 | **P3 WARN** | `console/page.tsx:172-187` |
| D8 | 페이지네이션 — 자연어 콘솔이라 무관 | **N/A** | — |

### /console 추가 결함 (PLAN.md 명시 vs 실제 갭)

| 항목 | PLAN.md §1 #12 / §2 차원 | 실제 | 분류 |
|------|------------------------|------|------|
| `tool_health` 도구 호출 패널 | "tool_health / clear_cache" backend 도구로 명시 | backend `app/tools/` 전수 grep 결과 **`tool_health` 함수 자체가 없음** (`app/server.py` 등록 도구 목록에도 부재) | **P1** |
| `clear_cache` 버튼 | PLAN.md 명시 | 미구현 (backend·frontend 양쪽) | **P1** |
| Cache key 목록 + TTL 표시 | PLAN.md 명시 | 미구현. 현 console 은 chat-only | **P1** |
| `_v29b` prefix 잔존 (사용자 요구) | PHASE 29 v29.1.3 후 정리 필요 | `award.py:459` `award_vendor_v29b`, `workflow.py:119` `vendor_profile_v29b` 남아있음 (실코드 수준) | **P2** |
| `empty_ttl` 동작 (`cache.py:_is_empty_result`) 가시화 | PLAN.md 의도 | `core/cache.py:20-53` 동작 OK이나 console에 노출 채널 없음 | **P2** |
| 60개 도구 노출 (footer 문구) | "MCP 60개 도구 (5종 etc 노출)" | chat에 5개만 화이트리스트, 나머지 55개 자연어 호출 불가. footer가 사용자 오해 유발 | **P3** |

→ **/console 핵심 결론**: 페이지가 광고하는 운영 콘솔 가치(tool 진단·캐시 제어·도구 인벤토리)가 backend·frontend 양쪽에 **부재**. 현재는 사실상 "AI chat 데모"만. PLAN §1 #12 backend tool 신설이 선행되어야 함.

---

## 3. /me — 8 차원 매트릭스

| Dim | 항목 | 결과 | 근거 (file:line) |
|-----|------|------|------------------|
| D1 | extract — `extractMcpData<...>(r.data)` 적용 (genericized `items/total_count/by_type`, `items/subscription_count`) — null 안전 OK | **OK** | `me/page.tsx:43-52, 80-81`; `lib/extract.ts:5-22` |
| D2 | key naming — `list_my_watchlist` 응답 (`items/total_count/by_type/items[].id/item_type/item_key/item_label/note/created_at`) vs frontend 참조 — **완전 일치**. `list_my_subscriptions` 응답 (`subscription_count/items[].id/keyword/biz_type/inst_name/notify_email/created_at`) vs frontend — **일치**. amount_range는 backend rule.amount_range nest 인 반면 frontend는 `min_amount/max_amount`로 나뉜 row 표시 ➜ row level은 raw row 반환이라 OK | **OK** | `app/tools/watchlist.py:153-159` vs `me/page.tsx:43-52, 70-72`; `app/tools/alerts.py:138-142` vs `me/page.tsx:80-86, 124-141` |
| D3 | 빈 상태 — `items.length === 0` "저장된 즐겨찾기 없음. '추가' 버튼 또는 입찰 추적·업체 프로필 페이지에서 추가하세요." / "활성 구독 없음." — 명시적 안내 OK | **OK** | `me/page.tsx:66-72, 108-110` |
| D4 | loading UX — Watchlist/Subscriptions 각 Suspense + Skeleton (`Skel h={32}`) | **OK** | `me/page.tsx:30-35, 150-157` |
| D5 | 에러 경로 — `r.ok === false` 분기 **없음**. `r.data` 가 null/error면 `extractMcpData` 가 null 반환 → `data?.items || []` 로 빈 화면 표시. 실제 backend 5xx 시 사용자에게 "활성 구독 없음" 메시지로 표시되어 **에러 사일런트 흡수** | **P1 WARN** | `me/page.tsx:42-48, 79-81` (`.ok` 미사용) |
| D6 | 기간 default — N/A (즐겨찾기는 기간 무관) | **N/A** | — |
| D7 | 포맷터 — `created_at` raw 표시 (`text-xs tabular-nums`) — fmtDate 미적용. `notify_email` raw OK. 사업자번호(item_key) — `WatchlistTable` `KeyLink` 가 `<VendorLink bizNo={...} name={item.item_key}/>` 로 위임 (내부 fmtBizNo 적용 가정) — 화면 자체 직접 포맷터 호출 없음 | **P3 WARN (created_at)** | `me/page.tsx:131`; `me/watchlist-table.tsx:118-129` |
| D8 | 페이지네이션 — Watchlist는 `WatchlistTable pageSize={10}` (TanStack Table 자체) OK. Subscriptions는 raw `<table>` 페이지네이션 없음 — 다수 구독 시 스크롤만 (P3) | **WatchlistOK / SubsP3** | `me/watchlist-table.tsx:99`; `me/page.tsx:111-143` |

### /me 추가 결함

| 항목 | 결함 | 분류 |
|------|------|------|
| `add-watchlist-dialog` 의 `<select>` 가 `vendor/bid/agency` 만 — backend `ItemType` 에는 `contract` 도 정의 (`app/tools/watchlist.py:20`) | UI에서 `contract` 타입 추가 차단 → 외부 KWater 계약 row를 즐겨찾기 못함 | **P3** |
| `subscribeKeywordAction` form 이 `region`, `min_amount`, `max_amount`, `notify_kakao` 미노출 | backend `subscribe_keyword_alerts` 가 5개 추가 필드 지원하나 frontend 폼은 4개만 — 기능 절반 노출 | **P3** |
| `WatchlistItem.created_at: string` 그대로 표시 (`text-xs tabular-nums`) | ISO 또는 SQLite 형식이 그대로 노출, fmtDate 미적용 | **P3** |
| `SELECT_CLASS` 가 `me/page.tsx` 와 `add-watchlist-dialog.tsx` 양쪽 중복 정의 | 일관성 OK이나 DRY 위반 (정합성 결함은 아님) | **N/A** |

---

## 4. /external/kwater — 8 차원 매트릭스

| Dim | 항목 | 결과 | 근거 (file:line) |
|-----|------|------|------------------|
| D1 | extract — `extractMcpData<{items,total_count,raw_count,status,endpoint}>(r.data)` 적용 OK | **OK** | `external/kwater/page.tsx:140-147` |
| D2 | key naming — `KWaterAdapter.search_contracts` 반환 키 (`items, total_count, agency, biz_type, endpoint, raw_count, status, error`) vs frontend 참조 (`items, total_count, raw_count, status, endpoint`) — **일치** (`agency, biz_type, error` 미참조 — 정상). `normalize_contract` row 키 (`contract_no, contract_date, title, inst_name, dept_name, biz_type, winner_name, contract_method, limit_method, contract_amount, period_from, period_to, raw`) vs `interface ContractRow` (raw 제외 12개) — **완전 일치** | **OK** | `app/clients/external/kwater.py:104-147` vs `external/kwater/page.tsx:36-49` |
| D3 | 빈 상태 — `items.length === 0` 시 "결과 없음 (N건). status: …" 표시 — `status` 노출 OK이나 `pending_key`/`active`/`error` 사용자 친화 변환 없음. raw value 그대로 표시 | **WARN** | `external/kwater/page.tsx:149-155` |
| D4 | loading UX — `Suspense + TableSkeleton` (5 row skeleton) | **OK** | `external/kwater/page.tsx:116-118, 269-280` |
| D5 | 에러 경로 — `r.ok` false 분기 → `오류: {r.error}` 빨간 박스 OK. 단 backend `result.error` 가 `data.error` 로 들어올 때 (e.g. `KWATER_API_KEY` 미설정 시 backend 가 `{items:[], status:'pending_key', note:'...'}` 반환 → `r.ok === true` → 빈 상태 분기로 빠짐) **사용자에게 키 미설정 원인 비표시**. KWater adapter의 `note` 필드도 frontend 미참조 | **P1 WARN** | `external/kwater/page.tsx:133-139, 149-155`; `app/clients/external/kwater.py:82-89` |
| D6 | 기간 default — `defaultMonth()` = 1년 전 동월 — 사용자 보고 검증 데이터(2022-05) 와는 다름. 월 단위라 default 가 false-negative 유발 가능. `현재: {searchDt} · {bizType} · 행 {limit}` 라벨 노출 OK | **OK (의도된 default)** | `external/kwater/page.tsx:51-58, 67-69, 109-111` |
| D7 | 포맷터 — `fmtDate(contract_date / period_from / period_to)`, `fmtWon(contract_amount)` — 일관 적용 OK. tabular-nums 적용 | **OK** | `external/kwater/page.tsx:191, 254-258` |
| D8 | 페이지네이션 — `limit` 입력 (1~1000) 만 존재. `pageNo` 전달 없음 → backend 도 `pageNo: 1` 고정 (`kwater.py:94`). `total_count` 가 `limit` 보다 크면 다음 페이지 진입점 부재 → 표시 위 헤더에 "총 N건 (반환 M)"는 노출되나 페이지 이동 불가 | **P1 WARN** | `external/kwater/page.tsx:69, 159-167`; `kwater.py:94` |

### /external/kwater 추가 결함

| 항목 | 결함 | 분류 |
|------|------|------|
| `<form action="/external/kwater">` GET form — 필드 hydration OK이나 `pageNo` URL 파라미터 schema에 부재. `searchParams: {dt, biz, limit}` 만. 페이지네이션 추가 시 `page` 파라미터 신설 필요 | **P1** (D8과 연결) | `external/kwater/page.tsx:64, 83` |
| 결과 row 클릭 시 `/external/kwater/contract?` 로 query string 전체 직렬화. 긴 title 다수 row 시 URL 길이 폭발 가능 | **P3** | `external/kwater/page.tsx:20-34` |
| `winner_name` LIKE 검색 링크 `/vendors?name=...` 으로 우회 OK. 사업자번호(`bizNo`) 직접 링크는 KWater raw 미제공 → vendors LIKE로 매칭하는 흐름 의도된 우회 OK | **OK** | `external/kwater/page.tsx:233-244` |
| 사용자 보고 `kwater-01.png` — raw XML 응답 화면 (`data.go.kr` API 직접 URL 호출 결과). frontend 결함 아님. 정규화 후 frontend 표시 흐름은 정상 | **N/A** | — |

---

## 5. /external/kwater/contract — 8 차원 매트릭스

| Dim | 항목 | 결과 | 근거 (file:line) |
|-----|------|------|------------------|
| D1 | extract — query params 만 사용. backend 호출 없음 → extract 자체 무관 | **N/A** | `external/kwater/contract/page.tsx:13-26` |
| D2 | key naming — query param 키 (`no, dt, title, dept, biz, winner, method, limit, amount, p_from, p_to`) vs `buildContractHref` 직렬화 키 — **완전 일치** | **OK** | `external/kwater/page.tsx:20-34` vs `external/kwater/contract/page.tsx:13-26` |
| D3 | 빈 상태 — `!no` 시 "계약번호 미지정. /external/kwater 에서 row 를 클릭하세요." 명시 OK | **OK** | `external/kwater/contract/page.tsx:32-44` |
| D4 | loading UX — query params 동기 표시. 비동기 fetch 없어 Suspense 무관 | **N/A** | — |
| D5 | 에러 경로 — query 파라미터 손실/잘못된 amount(NaN) 시 fallback 부족: `parseInt(sp.amount, 10)` NaN 시 `fmtWon(NaN)` → `"NaN"` 표시 가능 (fmtWon이 `>= 100_000_000` 비교 시 NaN false → `>= 10_000` false → `(NaN).toLocaleString()` = `"NaN"`) | **P3 WARN** | `external/kwater/contract/page.tsx:118`; `lib/format.ts:5-15` |
| D6 | 기간 default — N/A (단건) | **N/A** | — |
| D7 | 포맷터 — `fmtDate(sp.dt / sp.p_from / sp.p_to)`, `fmtWon(parseInt(sp.amount, 10))` — 적용 OK. `이행기간` Field 의 `p_from || p_to` 모두 falsy 시 `—` 표시 — **WARN**: 한쪽만 있을 때 `fmtDate(undefined) ~ fmtDate(p_to)` = `— ~ 2026-...` 비대칭 표시. period 라벨에서는 OK이나 시인성 떨어짐 | **P3 WARN** | `external/kwater/contract/page.tsx:65-134` |
| D8 | 페이지네이션 — N/A (단건) | **N/A** | — |

### /external/kwater/contract 추가 결함

| 항목 | 결함 | 분류 |
|------|------|------|
| 외부 ebid.kwater.or.kr 링크는 단순 메인 — `ordgNo` 직접 검색 URL 깊은 링크 미지원 (KWater 시스템 한계) | **P3** (외부 한계) | `external/kwater/contract/page.tsx:144-153` |
| `inst_name = "한국수자원공사"` 항상 동일이라 화면 헤더 미노출 (의도) — 사용자 인지 부족 가능 | **P3** | `external/kwater/contract/page.tsx:48-61` |
| 즐겨찾기 추가 버튼 부재 — `/me` AddWatchlistDialog 도 `contract` 타입 미노출이라 KWater 계약 즐겨찾기 경로 부재 (G5-2의 P3와 연쇄) | **P3 (cross-page)** | — |

---

## 6. P0~P3 우선순위 종합

### P0 (차단 — 화면 빈 표시 / 크래시 / 잘못된 키)

**없음.** 4 화면 모두 기본 렌더 + 데이터 흐름 정상.

### P1 (중요 — false-negative / UX 혼란 / 페이지 가치 미달)

| # | 화면 | 결함 | Fix 권장 |
|---|------|------|----------|
| P1-1 | `/console` | `tool_health` / `clear_cache` backend 도구 부재 (PLAN §1 #12 명시) | backend `app/tools/health.py` 또는 `app/tools/admin.py` 신설 — `tool_health` (등록 도구 목록 + import 상태), `clear_cache` (Redis prefix별 flush), `cache_stats` (key 카운트 + TTL 분포) |
| P1-2 | `/console` | Cache key 목록·TTL·`_v29b` prefix 가시화 채널 부재 | Cache 통계 패널 + cache_stats tool 호출 → `award_vendor_v29b`, `vendor_profile_v29b` 등 prefix별 hits/keys 표 |
| P1-3 | `/console` | `useChat` API 에러 표면화 없음 (ANTHROPIC_API_KEY 미설정 시 사용자 무인지) | `useChat({onError})` 또는 `error` 채널 노출 |
| P1-4 | `/me` | `r.ok === false` 분기 부재 — backend 5xx 시 빈 상태로 사일런트 fallback | `me/page.tsx` Watchlist/Subscriptions 양쪽에 `if (!r.ok) return <ErrorBanner error={r.error}/>` |
| P1-5 | `/external/kwater` | `data.status === 'pending_key'` (KWATER_API_KEY 미설정) 시 사용자에게 원인 미표시 | 빈 상태 분기에 `status==='pending_key'` 시 "환경변수 KWATER_API_KEY 미설정 — 운영자에게 문의" 명시. `data.note` 도 표시 |
| P1-6 | `/external/kwater` | 페이지네이션 부재 — `total_count > limit` 시 다음 페이지 진입점 없음 | `searchParams.page` 추가 + backend `KWaterAdapter.search_contracts(page_no=...)` 매개변수 신설 + frontend prev/next 버튼 |

### P2 (권장 — 성능 / 일관성)

| # | 화면 | 결함 |
|---|------|------|
| P2-1 | `/console` | `_v29b` prefix 코드 잔존 (`award.py:459`, `workflow.py:119`) — Phase 29 v29.1.3 정리 누락 |
| P2-2 | `/console` | `empty_ttl` 동작이 backend 에서 작동(`core/cache.py:20-85`) 하나 console에 노출 채널 없음 |

### P3 (보완 — 미세 UX / 코드 품질)

| # | 화면 | 결함 |
|---|------|------|
| P3-1 | `/console` | Generative Render fallback (JSON dump) 가 `vendor_profile`, `agency_procurement_history`, `predict_bid_price`, `search_bid_notices` 4 도구에 컴포넌트 매핑 부재 |
| P3-2 | `/console` | footer "MCP 60개 도구 (5종 etc 노출)" 와 실제 5 화이트리스트 갭 — 사용자 오해 |
| P3-3 | `/me` | `add-watchlist-dialog` `<select>` 가 `contract` 타입 누락 |
| P3-4 | `/me` | `subscribe` 폼이 `region`/`min_amount`/`max_amount`/`notify_kakao` 미노출 — backend 지원 5필드 중 4개만 (절반 노출) |
| P3-5 | `/me` | Subscriptions raw `<table>` 페이지네이션 부재 (다수 구독 시 스크롤) |
| P3-6 | `/me` | `created_at` raw 표시 — fmtDate 미적용 |
| P3-7 | `/external/kwater` | row 클릭 시 query string 전체 직렬화 — URL 길이 폭발 가능 (단건은 backend `lookup_by_contract_no` 신설 권장이나 backend 미지원) |
| P3-8 | `/external/kwater/contract` | `parseInt(sp.amount, 10)` NaN fallback 미처리 → `fmtWon(NaN)` → `"NaN"` |
| P3-9 | `/external/kwater/contract` | `이행기간` 한쪽만 있을 때 비대칭 표시 (`— ~ 2026-...`) |
| P3-10 | cross-page | KWater 계약 → 즐겨찾기 추가 경로 부재 (`contract` 타입 미노출과 연쇄) |

---

## 7. Fix 매트릭스 (참고용 — 코드 수정 금지 원칙 준수)

| 우선순위 | 변경 영역 | 추정 변경 line |
|---------|----------|----------------|
| P1 | backend `app/tools/health.py` 신설 + `app/server.py` 등록 | +80 ~ +120 lines (3 도구) |
| P1 | `console/page.tsx` Cache 통계 패널 + 에러 노출 | +60 ~ +100 lines |
| P1 | `me/page.tsx` `r.ok` 분기 추가 | +20 lines |
| P1 | `external/kwater/page.tsx` `pending_key` 안내 + 페이지네이션 | +30 ~ +50 lines |
| P1 | `app/clients/external/kwater.py` `pageNo` 매개변수 | +5 lines |
| P2/P3 | prefix `_v29b` rename | 2 file × ~2 line |
| P3 | `add-watchlist-dialog.tsx` `contract` 옵션 + 구독 폼 확장 | +20 lines |

---

## 8. L1~L5 검증 권장 (Fix 후)

- **L1 (import)**: backend 재기동, `app.tools.health` import 확인
- **L2 (unit)**: `tool_health()` / `clear_cache(prefix)` / `cache_stats()` 단위 테스트
- **L3 (MCP curl)**: `curl -X POST .../mcp` 로 3 신규 도구 raw 응답 검증
- **L4 (사용자 case)**: KWater 2022-05 계약 14건 (kwater-01.png 사용자 검증 데이터) — 페이지네이션 동작 확인
- **L5 (frontend)**: localhost:3000/console DOM 텍스트 검증 — 신규 Cache 패널 노출. localhost:3000/me 5xx 모킹 시 ErrorBanner 노출. localhost:3000/external/kwater?dt=999999 → pending_key 안내 표시

---

## 9. 종합 평가

| 화면 | 정합성 점수 (8 dim 중 OK) | 핵심 갭 |
|------|---------------------------|---------|
| `/console` | 4/8 (D1, D2, D3, D4) — D5/D7 WARN, D8 N/A, D6 LLM 위임. **+ PLAN.md 명시 backend 미구현 (P1×3)** | "운영 콘솔" 가치 자체 부재 |
| `/me` | 6/8 (D1, D2, D3, D4 + D7 부분 OK + D8 watchlist OK) — D5 WARN, D6 N/A | 에러 사일런트 흡수 |
| `/external/kwater` | 5/8 (D1, D2, D4, D6, D7) — D3/D5/D8 WARN | pending_key 안내 + 페이지네이션 |
| `/external/kwater/contract` | 4/4 (D2, D3, D7) — D1/D4/D5/D6/D8 N/A 또는 의도된 부재 | NaN fallback + 비대칭 기간 |

**G5 그룹 총평**: 즐겨찾기/외부 KWater는 **MVP 수준 정합성 통과**. `/console`은 "AI 콘솔" 데모로는 동작하지만 PLAN.md 가 약속한 운영 콘솔 backend 도구가 부재해 핵심 가치 대비 절반 미달. P0 결함 없음 → 즉시 차단 사례는 없으나, P1 6건이 사용자 신뢰도/디버그 용이성에 직결.
