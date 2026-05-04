# DIAGNOSIS G1 — 홈 + 통합검색

> **점검 대상**: `/page.tsx` (홈 대시보드) + `/search/page.tsx` (빠른 검색 라우터)
> **점검 일시**: 2026-05-04
> **방법**: 정적 코드 분석 + backend 도구 응답 구조 대조 + redirect 흐름 추적

## 0. 사전 발견 (중요)

태스크 설명서가 명시한 전제 두 가지가 실제 코드와 어긋남.

### 0-1. `unified_search` (W6)는 backend에 존재하지 않음

| 검증 | 결과 |
|------|------|
| `app/tools/workflow.py` 정의 함수 | `trace_bid_lifecycle`, `vendor_profile`, `agency_bid_summary`, `competitor_analysis`, `agency_procurement_history` (W1~W5) |
| `unified_search` 또는 W6 grep | 일치 0건 (`.planning/phases/30-ui-integrity-sweep/PLAN.md` 1곳만) |
| frontend `TOOL_CATALOG` (`mcp-client.ts:83-159`) | `unified_search` 미등록 |

→ Phase 30 PLAN.md 표 #2(`unified_search`)는 **계획상 명세지 아직 미구현**. 본 진단은 "현재 동작" 기준이므로 W6 응답 키 정합 점검 항목(D2 등) 자체가 N/A.

### 0-2. `app/routers/me.py`는 존재하지 않음 (FastAPI router 구조 아님)

| 검증 | 결과 |
|------|------|
| `app/routers/` 디렉토리 | **존재하지 않음** (`ls`로 확인) |
| `app/` 하위 | `clients`, `core`, `dispatcher`, `ml`, `schemas`, `storage`, `tools`, `config.py`, `server.py` |
| 즐겨찾기/알림 도구 위치 | `app/tools/watchlist.py`, `app/tools/alerts.py` (MCP tool 직접 등록) |
| frontend 호출 경로 | `lib/actions.ts` → `callMcpTool("list_my_watchlist", ...)` 등 |

→ "홈에서 즐겨찾기·알림을 표시할 수 있다"는 가설은 **현 코드에서 전혀 적용되지 않음**. `page.tsx`는 정적 메뉴 카드 9개일 뿐, 어떤 backend 호출도 없음. (D1~D8 점검 시 자동 OK / N/A 처리)

---

## 1. `/page.tsx` (홈 대시보드)

### 1-1. 코드 본질

- 모든 콘텐츠가 **하드코딩된 정적 메뉴 카드**: `MENUS[]` 9개 (`page.tsx:49-119`)
- backend 호출 0건. server action 호출 0건. server component이지만 사실상 정적.
- 빠른 검색 폼: `<form action="/search" method="GET">` → `name="q"` 단일 필드 (`page.tsx:23-32`)
- footer: `process.env.GOVPROCU_MCP_URL || "localhost:8081"` 표시만 (`page.tsx:43`)

### 1-2. 8 차원 점검표

| Dim | 결과 | Evidence | Note |
|-----|------|----------|------|
| D1 extract | N/A | `page.tsx` 전체 | MCP 응답을 받지 않음 → `content[0].text` JSON.parse 코드 자체가 없음 |
| D2 key naming | N/A | `page.tsx` 전체 | backend 응답 참조 0건 |
| D3 빈 상태 안내 | N/A | `page.tsx:35-39` | 메뉴 카드가 항상 9개 정적이라 "빈 상태" 개념 없음 |
| D4 loading UX | N/A | `page.tsx:10-46` | Suspense boundary 없음. 정적이라 불필요 |
| D5 에러 경로 | N/A | `page.tsx` 전체 | 호출 자체가 없으므로 `result.ok === false` 분기 불필요 |
| D6 기간 default | N/A | — | 기간 필터 없음 |
| D7 포맷터 | N/A | — | 숫자/금액 표시 없음 |
| D8 페이지네이션 | N/A | — | 리스트 없음 |

### 1-3. 추가 정합성 관찰 (8 dim 외)

| 항목 | 결과 | Evidence | 비고 |
|------|------|----------|------|
| MCP URL 기본값 일치 | OK | `page.tsx:43` `localhost:8081` vs `mcp-client.ts:9` `http://localhost:8081` | 최근 commit 74501a8 fix 반영됨 |
| 메뉴 항목 수와 점검 대상 14화면 일치 | WARN | `MENUS[]` 9개. PLAN.md 14화면 중 `/bids/trace`, `/bids` 같은 핵심 라우트가 메뉴에 없음 | "입찰 검색"(`/bids`), "입찰 상세 추적"(`/bids/trace`)는 있음. 빠진 것: `/lookup` 표시되나 단건 조회와 menu 텍스트("Cross-Lookup ... 4키 자동 관계 추적") 일치 모호. `/console`, `/analytics`는 표시되거나 별도. — 표시 누락은 없음. WARN 사유는 메뉴 카드의 `tag` 라벨 (P0/P1/신규/외부) 가 **PLAN.md priority 기준이 아니라 프로젝트 자체 라벨링**이라 점검 매트릭스와 직결되지 않는 점. |
| 빠른 검색 입력 → /search 라우팅 | OK | `page.tsx:23` form action="/search" method="GET" → `/search?q=...` | redirect 로직 `/search/page.tsx`로 위임 |
| 접근성 — autoFocus | OK | `page.tsx:28` Input에 `autoFocus` | 첫 진입 시 키보드 검색 가능 |
| 카드 링크 패턴 일관 | OK | `MenuCard` (`page.tsx:130-148`) `<Link href={href}>` 통일 |
| 키보드/포커스 hover state | OK | `hover:bg-[var(--color-bg-muted)]` (`page.tsx:134`) |

### 1-4. /page.tsx 결론

**기능적 결함 없음.** 정적 메뉴 + 검색 폼만 가지므로 진단 8 dim은 모두 N/A. 다만 PLAN.md가 "홈에서 즐겨찾기·알림 표시 가능" 가설을 세웠다면 해당 기능은 **현재 미구현** → 향후 phase에서 server action(`listMyWatchlist`, `listMySubscriptions`) 호출을 홈에 추가할지 정책 결정 필요.

---

## 2. `/search/page.tsx` (빠른 검색 라우터)

### 2-1. 코드 본질

- **redirect-only stub** (29줄, `redirect()` 외 어떤 UI 렌더링도 없음)
- 입력 패턴 분기:
  - `q` 비어있음 → `/`로 리다이렉트 (`search/page.tsx:14`)
  - `^\d{10}$` (10자리 숫자) → `/vendors/{cleaned}` (`:18-20`)
  - `^\d{8,15}$` (8~15자리 숫자) → `/bids/trace?no={cleaned}` (`:22-25`)
  - 그 외 → `/bids?q={q}` (`:28`)
- backend 호출 0건. 자체 데이터 표시 0건.

### 2-2. 8 차원 점검표

| Dim | 결과 | Evidence | Note |
|-----|------|----------|------|
| D1 extract | N/A | `search/page.tsx` 전체 | MCP 응답 받지 않음 |
| D2 key naming | N/A | — | 동일 |
| D3 빈 상태 안내 | OK | `search/page.tsx:14` `if (!q) redirect("/")` | 빈 입력 → 홈으로 회귀 (직관적) |
| D4 loading UX | N/A | — | redirect만 발생. fallback UI 노출 시점 없음 |
| D5 에러 경로 | WARN | `search/page.tsx` 전체 | 정규식 매칭이 모호한 경우(예: 8자리 숫자 = vendor 아니라 `/bids/trace?no=`로 분기) 사용자에게 알림 없이 강제 라우팅. 잘못된 destination에서 0건이 나오면 사용자는 "왜 이 페이지인지" 모름 |
| D6 기간 default | N/A | — | redirect-only |
| D7 포맷터 | N/A | — | 숫자 표시 없음 |
| D8 페이지네이션 | N/A | — | 리스트 없음 |

### 2-3. 추가 정합성 관찰 — 사용자 보고 사례 ("정보체계", "아이웨이브" 0건) 추적

`/search?q=정보체계` → 정규식 `\d{10}`/`\d{8,15}` 모두 fail → `redirect("/bids?q=정보체계")`.
사용자가 보는 "0건" 화면은 **`/bids/page.tsx`의 Results 컴포넌트** 출력. 본 G1 점검 범위 외이지만 redirect 종착지이므로 핵심 흐름 문제를 1차 식별:

| 관찰 | 결과 | Evidence | 영향 |
|------|------|----------|------|
| `/search` → `/bids?q=...` 이행 시 사용자 의도 보존 | WARN | `search/page.tsx:28` | 사용자는 "통합 검색"을 기대했지만 `/bids` (입찰 공고 한정)로 이동. 업체명·발주기관 키워드와 입찰 공고 키워드가 같이 검색되는 W6 unified_search가 backend에 없으므로 어쩔 수 없는 fallback이지만, **/bids로 이동했다는 사실 자체가 사용자에게 표시되지 않음** → "왜 0건"의 1차 원인 |
| `/bids` default 기간 30일 적용 | INFO | `bids/page.tsx:76-81, 119-121` | 사용자가 from/to 미입력 시 자동 30일 적용. "정보체계"가 30일 내 부재면 0건 표시. P1 매트릭스의 "기간 default 길이" 문제와 직결 |
| LIKE 매칭률 | INFO | `bids/page.tsx:117-118` | `deep=1` 미체크 시 `scan_pages=1`. 5/3 N40 fix로 "깊은 검색" 옵션 추가됐지만 `/search`에서 `/bids`로 redirect 시 deep 파라미터 전달 없음 → 사용자 "정보체계"·"아이웨이브" 0건 위양성 가능성 ↑ |
| 한글 키워드 URL 인코딩 | OK | `search/page.tsx:28` `encodeURIComponent(q)` | "정보체계"→ `%EC%A0%95%EB%B3%B4%EC%B2%B4%EA%B3%84` 정상 |
| 사업자번호 패턴 우선순위 | OK | `:18-20` 10자리 → vendor → 그 후 8~15자리 trace | 10자리 사업자번호가 trace로 빨려가는 사고 방지됨 |
| 7-digit input 처리 | WARN | `search/page.tsx:18-25` | `^\d{7}$`는 어떤 정규식에도 안 잡힘 → `/bids?q=...`로 fallback. 의도일 수 있으나 명시 주석 없음 |
| 숫자+하이픈 패턴 (예: `123-45-67890` 사업자번호) | OK | `:15` `replace(/[-\s]/g, "")` | 사용자가 하이픈 입력해도 정규화 후 매칭 |

### 2-4. /search/page.tsx 결론

**redirect-only 스텁**이라 8 dim 자체는 거의 N/A. 다만 사용자 보고 사례(0건)의 흐름 시작점이므로 다음 결함이 P1·P2로 누적됨:

- **모호 분기 안내 부재** (D5): 입력 패턴이 정규식에 부합하지 않을 때 어떤 페이지로 이동하는지 사전 안내 없음
- **deep search 옵션 미연결** (D8): redirect 시 `deep=1` 자동 부여 없음 → 짧은 default 기간과 결합되면 0건 위양성

---

## 3. 결함 요약 (P0/P1/P2/P3)

### P0 — 차단/크래시
- 없음 (홈·검색 둘 다 정적·redirect-only로 크래시 경로 자체 부재)

### P1 — 중요 (false-negative / 사용자 혼란)
- **[P1-1]** `/search` → `/bids` redirect 시 `deep` 파라미터 미전달. 사용자가 "정보체계", "아이웨이브" 같은 키워드로 빠른 검색하면 default 30일 + `scan_pages=1`로 0건 위양성 발생.
  - **Evidence**: `frontend/src/app/search/page.tsx:28` (`redirect(/bids?q=${encodeURIComponent(q)})`)
  - **제안**: redirect URL에 `&deep=1` 자동 부여 (단, 응답 22초 위험 동반 → UX 트레이드오프 사전 결정 필요)
- **[P1-2]** PLAN.md가 명세한 `unified_search` (W6) backend 도구 자체 미구현. `/search` 페이지가 통합 검색이 아니라 **입찰 공고 검색**으로만 fallback됨.
  - **Evidence**: `app/tools/workflow.py` 전체 (W1~W5만 존재) + `frontend/src/lib/mcp-client.ts:127-131` (TOOL_CATALOG에 unified_search 없음)
  - **제안**: 본 진단 범위 외. Phase 30이 W6 구현을 포함할지 별도 결정 필요. 미구현이라면 PLAN.md 명세 정정.

### P2 — 권장 (UX 일관성)
- **[P2-1]** `/search`에서 redirect 분기 시 사용자에게 "어떤 페이지로 이동했는지" 표시 없음. `/vendors/[bizNo]`나 `/bids/trace?no=`에서 결과 0건이 뜨면 "내가 입력한 게 사업자번호로 인식됐는지" 알기 어려움.
  - **Evidence**: `search/page.tsx:14-28` redirect 직전 어떤 UI도 노출되지 않음
  - **제안**: `/bids`나 `/vendors/[bizNo]` 페이지 상단에 "입력 X가 사업자번호로 인식되어 이 페이지로 이동했습니다" 헤더 배너 추가 (별도 phase)
- **[P2-2]** 홈 페이지 `MENUS` 메뉴 9개 정적이며 사용자별 즐겨찾기·최근 본 입찰·신규 알림 카운트 등 동적 데이터 없음. PLAN.md 가정과 불일치.
  - **Evidence**: `page.tsx:10-46` server action 호출 0건
  - **제안**: 홈에 `listMyWatchlist({limit:5})` + `listMySubscriptions()` 결과 카드 추가하는 별도 phase 검토

### P3 — 보완 (미세)
- **[P3-1]** `/page.tsx` footer가 환경변수 직접 노출 (`localhost:8081`). 운영 환경에서 의도적이지 않다면 정보 노출.
  - **Evidence**: `page.tsx:42-44`
  - **제안**: production build 시 `process.env.NODE_ENV === "production"` 분기로 비표시
- **[P3-2]** `/search/page.tsx` 정규식 분기 로직에 7자리 숫자 케이스가 묵시적으로 fallback됨. 의도라면 주석 추가, 아니라면 별도 처리.
  - **Evidence**: `search/page.tsx:17-28`
- **[P3-3]** 홈 메뉴 카드 `tag` 라벨 (P0/P1/신규/외부)이 PLAN.md priority 매트릭스와 매핑되지 않아 사용자 입장에서 의미 불명확.
  - **Evidence**: `page.tsx:50-118`
  - **제안**: 라벨 의미 footer/tooltip로 명시

---

## 4. 검증 방법 (재현용)

```powershell
# /search → /bids redirect 흐름
# (frontend 실행 중일 때)
# 브라우저 또는 curl 로 http://localhost:3000/search?q=정보체계
# Location 헤더가 /bids?q=%EC%A0%95%EB%B3%B4%EC%B2%B4%EA%B3%84 로 떨어지는지 확인

# unified_search 부재 검증
Select-String -Path C:\Users\User\GovProcu\app\tools\*.py -Pattern "unified_search"
# (출력 없음 = 미구현)
```

---

## 5. 메모 — 8 dimension 적용성 한계

`/page.tsx`(정적) + `/search/page.tsx`(redirect-only) 둘 다 **데이터 fetch가 없는 화면**이라 8 dim 매트릭스의 D1·D2·D4·D6·D7·D8이 N/A로 채워짐. 매트릭스 점검은 G2 이후(`/bids`, `/bids/trace`, `/vendors/[bizNo]`, `/agencies` 등 데이터 페이지)에서 본격 의미를 가질 것으로 예상. G1은 **흐름의 시작점에서 redirect 정합성과 정적 컨텐츠 일관성**만 확인.
