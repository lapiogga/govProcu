---
status: testing
phase: 01-autonomous-v3-v8
source:
  - .planning/phases/01-autonomous-v3-v8/01-SUMMARY.md
  - .planning/phases/01-autonomous-v3-v8/02-FULL-TEST-PLAN.md
started: 2026-05-03T00:30:00+09:00
updated: 2026-05-03T02:50:00+09:00
fix_round: v10.2
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 2
name: shadcn Wave 2 — DropdownMenu 정렬 (mock)
expected: |
  /bids?q=AI 또는 mock 모드에서 hasQuery 영역 진입 시 우측 상단의 정렬 메뉴 trigger 버튼이 보인다.
  버튼 클릭 → 라디오 메뉴 5종(공고일↓/↑/마감 임박/추정가↓/↑) 표시.
  "마감 임박" 선택 → URL 에 ?sort=deadline 갱신.
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: |
  docker ps → govprocu-redis + govprocu-neo4j-poc 둘 다 Up.
  python -m app.server (SERVER_PORT=8081 FASTMCP_STATELESS_HTTP=true) 부팅 OK.
  frontend npm run start 부팅 OK.
  curl http://localhost:8081/mcp 405 또는 307 (정상), curl http://localhost:3020/ 200.
result: issue
reported: "localhost:8081 ERR_CONNECTION_REFUSED (err-01.png)"
severity: blocker
fix_action: "MCP/frontend 재가동 (직전 taskkill 후 미재시작) → 4 서비스 정상 확인 (MCP 405/frontend 200/Redis Up 8h/Neo4j Up 8h)"
fix_status: resolved
follow_up: "운영 가이드에 cold start 절차를 별도 스크립트 또는 docker-compose 통합으로 단순화 고려"

### 2. shadcn Wave 2 — DropdownMenu 정렬 (mock)
expected: |
  /bids?q=AI 또는 mock 모드에서 hasQuery 영역 진입 시 우측 상단의 정렬 메뉴 trigger 버튼이 보인다.
  버튼 클릭 → 라디오 메뉴 5종(공고일↓/↑/마감 임박/추정가↓/↑) 표시.
  "마감 임박" 선택 → URL 에 ?sort=deadline 갱신.
result: [pending]

### 3. shadcn Wave 2 — Dialog 즐겨찾기 추가 (mock)
expected: |
  /me 페이지 헤더의 "+ 추가" 버튼 클릭 → 모달 열림.
  유형 select(업체/공고/기관) + 키 + 라벨 + 메모 입력 필드 표시.
  ESC 또는 X 클릭 시 닫힘.
result: [pending]

### 4. cmdk Command Palette (Cmd+K)
expected: |
  헤더 우측의 "검색… ⌘K" 버튼 클릭 또는 Ctrl+K 단축키 → 모달 열림.
  "페이지" 그룹에 14개 항목(대시보드/빠른검색/입찰 검색/입찰 추적/업체/발주기관/분석/Lookup/AI 콘솔/Me/적격심사/투찰가/K-water 계약공개) 표시.
  10자리 숫자 입력 시 "업체 프로필 보기" 항목 노출.
  Esc 닫힘. 항목 선택 시 페이지 이동.
result: [pending]

### 5. KWater 라이브 — /external/kwater
expected: |
  /external/kwater?dt=202205&biz=용역 진입 시 약 3~5초 후 표 5건 표시.
  헤더에 "총 131건 (반환 5)" 형태.
  표시 데이터에 "광주시 노후 상수관로 교체공사 건설폐기물 처리용역(1차년도)" 행 보인다.
  apis.data.go.kr/B500001/ebid/cntrct3/servcList endpoint 우측 표시.
  업종 select 를 "공사" 로 변경하여 검색 시 다른 행(예: 보현산댐 부유물 적치장)으로 갱신.
result: [pending]

### 6. /bids 라이브 + cursor 페이징
expected: |
  /bids?q=정보화&type=용역&from=20260420&to=20260502 진입 시 약 3~5초 후 표 표시.
  "총 9124건 (반환 N, 페이지 1)" 형태.
  표시 데이터에 KTL 정보화전략계획 ISMP 또는 한의약정보화 AI 추진 기본계획 보인다.
  헤더 또는 footer 에 "1 / 10" 페이지 번호 + "다음 →" 버튼.
  "다음 →" 클릭 시 URL 에 page=2 반영, 새 페이지 결과 표시(0건 + "결과 없음" 정상).
result: [pending]

### 7. /vendors/{bizNo} 라이브 — NTS 진위확인
expected: |
  /vendors/1058705373 진입 시 약 10~15초 후 페이지 표시.
  NTS 검증 섹션에 "계속사업자" 또는 "01" 코드 + 부가가치세 일반과세자 표시.
  awards/participations/openings/bids 5종 통계 라벨 보인다 (수치는 0 또는 실값).
result: [pending]

### 8. Gmail SMTP — 수신 확인
expected: |
  N24 단계에서 send_email() 가 lapiogga@gmail.com 으로 자기 발송했음.
  메일 제목: "[GovProcu] SMTP dispatcher 검증 메일".
  본문 첫 줄: "GovProcu 알림 dispatcher 검증 메일입니다."
  Gmail 수신함(또는 스팸함) 에서 도착 확인.
result: [pending]

### 9. Neo4j Browser — 데이터 점검
expected: |
  http://localhost:7474 접속 후 neo4j / govprocu_poc 로그인.
  쿼리 입력: MATCH (n:BidNotice) RETURN count(n) AS c
  결과: 50 (ETL 1주치 ingest 결과).
  쿼리 입력: MATCH (n) RETURN labels(n) AS l, count(*) AS c
  BidNotice 50, 다른 라벨은 0 또는 일부.
result: [pending]

### 10. e2e 회귀 (mock)
expected: |
  cd frontend && MCP_MOCK_MODE=true PORT=3025 npm run start
  npx playwright test --project="Desktop Chromium" --reporter=line
  결과: 36/36 PASS.
  (또는 마지막 commit 4d3de8e 시점에서 실행한 결과: 36 passed)
result: [pending]

## Summary

total: 10
passed: 0
issues: 10  # Test1 + 후속 3건 (v9) + 6건 (v10): chunk/업종/정렬/R-form/발주기관/0건 메시지
pending: 9
skipped: 0
blocked: 0
fix_round: v10.2  # G2B 1개월 chunking + 업종 전체 merge + 단건 폴백 + agencies 6개월 default
commits:
  - 5d0097c  # 자율 v9 — vendor LIKE + bids deep + kwater detail
  - e9c8387  # 자율 v10 — chunking + 3종 merge + R 폴백 + 측정 기반 default
  - 2863528  # 자율 v10.2 — _infer_period 헬퍼 + 999 매칭 + agencies 180일

## Gaps

- truth: "MCP 서버 cold start 후 localhost:8081/mcp 정상 응답 + frontend localhost:3020 HTTP 200"
  status: failed_then_resolved
  reason: "User reported: ERR_CONNECTION_REFUSED (err-01.png) — MCP/frontend 미가동 상태에서 검증 시도"
  severity: blocker
  test: 1
  root_cause: "직전 라이브 검증 후 내가 taskkill로 종료했고 새 세션 cold start 절차가 사용자에게 명시 안 됨"
  artifacts: []
  missing:
    - "운영 가이드(docs/OPERATIONS.md 또는 README)에 cold start one-liner 또는 docker-compose 통합"
  fix_action: "MCP 8081 + frontend 3020 재가동 → 4 서비스 정상 확인"
  follow_up_phase: "future-track"

- truth: "업체 분석에서 업체명으로 검색이 가능해야 함"
  status: failed_then_resolved
  reason: "User reported: '/vendors 페이지가 사업자번호 10자리 직접 입력만 받음. 업체명 LIKE 검색 미지원'"
  severity: major
  test: implicit
  root_cause: "/vendors 인덱스 페이지가 사업자번호 redirect만 처리, 업체명 검색 form/MCP 도구 호출 없음"
  artifacts:
    - path: "frontend/src/app/vendors/page.tsx"
    - path: "frontend/src/lib/actions.ts"
    - path: "app/tools/award.py"
  fix_action: |
    1. searchVendorsByName(name, dateFrom, dateTo) action 추가
    2. /vendors 페이지에 업체명 input + 결과 리스트(NameSearchResults)
    3. search_awards_by_vendor 라이브 fix:
       - G2B award base URL /ad → /as (settings.g2b_award_base_url 신규)
       - numOfRows 999 → 500 (G2B resultCode 07 입력범위초과 방지)
       - date range 1개월 제한 (default 30일)
       - max_scan_per_biz 10000 → 1000 (응답 ~7초 목표)
    4. 라이브 검증: name=디지털 → 19초 → 후보 1개(부산디지털대학교산학협력단)

- truth: "입찰 검색에서 LIKE 부분일치 검색이 가능해야 함"
  status: failed_then_resolved
  reason: "User reported: '/bids 의 키워드가 단일 페이지(999건) 클라이언트 필터로 매칭률 낮음'"
  severity: major
  test: implicit
  root_cause: "search_bid_notices max_scan_pages=1 hardcode. caller가 더 깊은 검색을 요청할 수단 없음"
  artifacts:
    - path: "app/tools/bid.py"
    - path: "app/schemas/bid.py"
    - path: "frontend/src/app/bids/page.tsx"
    - path: "frontend/src/lib/mcp-client.ts"
  fix_action: |
    1. BidNoticeSearchInput.scan_pages 필드 추가 (Field(1, ge=1, le=10))
    2. search_bid_notices(scan_pages) caller-controlled (1=빠름 / 5=LIKE 매칭률↑)
    3. /bids 페이지: ?deep=1 체크박스 → scan_pages=5
    4. mcp-client.ts SSE 파싱 강화: keepalive `: ping` line 무시 (22초+ 응답 대응)
    5. 라이브 검증: deep=1 → 9124/13건 (KTL/한의약/디지털/이지에스 등 매칭)

- truth: "K-water 계약공개의 계약번호/계약제목/계약업체 클릭 시 해당 정보로 이동해야 함"
  status: failed_then_resolved
  reason: "User reported: '/external/kwater 표 컬럼이 plain text. 클릭 라우팅 없음'"
  severity: major
  test: implicit
  root_cause: "/external/kwater page의 row 셀이 단순 text. KWater 계약 단건 상세 페이지 부재"
  artifacts:
    - path: "frontend/src/app/external/kwater/page.tsx"
    - path: "frontend/src/app/external/kwater/contract/page.tsx (NEW)"
  fix_action: |
    1. /external/kwater/contract/page.tsx 신규 (URL searchParams 기반 single row 상세)
    2. /external/kwater 표:
       - 계약번호/계약제목 → /external/kwater/contract?no=...&dt=...&title=...&winner=...&...
       - 계약업체 → /vendors?name={winner_name} (LIKE 검색 활용)
    3. 외부 KWater 시스템 링크 (ebid.kwater.or.kr) detail page footer에 추가
    4. 라이브 검증: 5 row 모든 컬럼에 정상 href 생성 (contract / vendors LIKE)

# === 사용자 N42 (5/3 01:10) 라운드 추가 보고 결함 6건 ===

- truth: "/bids 4개월 범위 (20260101~20260503) 조회 시 데이터 표시되어야 함"
  status: resolved
  reason: "User reported: '4개월로 하면 조회가 안됨. 최장 범위 규정 + 기본값 셋팅'"
  severity: blocker
  test: implicit
  root_cause: "G2B inqryDiv=1은 inqryBgnDt~inqryEndDt 최대 1개월 제약. 초과 시 resultCode 07 또는 silent 0건"
  artifacts:
    - path: "app/core/daterange.py (NEW)"
    - path: "app/tools/bid.py"
    - path: "app/tools/award.py"
  fix_action: |
    1. chunk_date_range() 유틸 추가 (max_days=31)
    2. search_bid_notices/search_awards/search_awards_by_vendor 자동 chunking
    3. (bid_no, bid_ord) dedup 적용
    라이브 검증: 4개월 q=정보화 → chunks=4, 1월/4월 데이터 정상 merge 표시 (67초)
  scenario_cases: ["S01-C10", "S03-C5", "S03-C6"]
  fix_commits: [e9c8387]

- truth: "/bids '업종 전체' 선택 시 공사+용역+물품 모두 검색되어야 함"
  status: resolved
  reason: "User reported: '업종을 전체로 하면 검색이 안됨'"
  severity: major
  test: implicit
  root_cause: "biz_type=None일 때 default로 용역 endpoint 1종만 호출 — 공사/물품 누락"
  artifacts:
    - path: "app/tools/bid.py (_resolve_bid_endpoints 추가)"
  fix_action: |
    biz_type=None 또는 ''면 3종 endpoint 모두 순회 + dedup. limit 도달 전 모든 endpoint 호출.
  scenario_cases: ["S02-C4", "S09-C7"]
  fix_commits: [e9c8387]

- truth: "/bids 정렬 '마감일임박' 선택 시 미래 마감 가까운 순으로 정렬되어야 함"
  status: resolved
  reason: "User reported: '마감일임박은 안됨'"
  severity: major
  test: 2
  root_cause: "단순 localeCompare → 빈 마감일과 과거 마감을 동등 처리"
  artifacts:
    - path: "frontend/src/app/bids/page.tsx (sortItems 3-tier)"
  fix_action: |
    tier(d) 함수: 미래(0) → 과거(1) → null(2). tier 0 asc, tier 1 desc, tier 2 끝.
    today YYYYMMDD 기준 정확 비교 (앞 8자리만).
  scenario_cases: ["S04-C3"]
  fix_commits: [e9c8387]

- truth: "공고번호 R26BK01435763-000 입찰추적 시 데이터 표시되어야 함"
  status: partially_resolved
  reason: "User reported: 'R26BK01435763-000 입찰추적이 안됨 (err-02.png)'"
  severity: major
  test: implicit
  root_cause: |
    1. URL "R26BK01435763-000"이 -000 suffix 통합 형태인데 split 안 됨
    2. G2B inqryDiv=3 단건 조회가 R 형식 일부 endpoint에서 0건 반환
    3. 폴백 inqryDiv=1은 bidNtceNo 파라미터를 무시 → 999개 중 매칭 필요
  artifacts:
    - path: "app/tools/bid.py (_infer_period_from_bid_no, get_bid_notice_detail 폴백)"
    - path: "app/tools/award.py (get_award_detail 폴백)"
    - path: "frontend/src/app/bids/trace/page.tsx (suffix split)"
  fix_action: |
    v10: inqryDiv=1 폴백 + 차수 매칭 + 첫 항목 fallback
    v10.2: _infer_period_from_bid_no (R26→2026, 20240101234→2024) + numOfRows 999 + bid_no 동일 매칭
    검증: R26BK01435763 자체 G2B 미존재 (사용자 클릭 출처 불명).
          R26BK01439997 (실존)도 단건 0건 — G2B 단건 조회 패턴 자체 한계.
          폴백 inqryDiv=1+추정기간 1년 안의 999건 중 매칭 — 30000+건 환경에서 부족.
  follow_up: "search_bid_notices(bid_notice_no=...) 인자 추가 + 페이징 다회 또는 sortby 패턴 — v11 별도 라운드"
  scenario_cases: ["S12-C1", "S12-C2", "S12-C3"]
  fix_commits: [e9c8387, 2863528]

- truth: "발주기관 분석은 1년 default + 합리적 응답시간으로 동작해야 함"
  status: resolved
  reason: "User reported: '발주기관 분석 안됨 (err-03) - 날짜를 기본 1년으로 할 것'"
  severity: major
  test: implicit
  root_cause: "기존 default 무 → 사용자가 5년 (2020~2026) 직접 입력 시 G2B 1개월 제약 위반으로 0건"
  artifacts:
    - path: "frontend/src/app/agencies/page.tsx"
    - path: "app/core/daterange.py"
  fix_action: |
    v10: default 365일 + chunking 12회 자동
    v10.2: 측정 1.7초 vs 실사용 60.7초 차이 발견 → 180일(6개월)로 단축. chunk 6 × 4 endpoint = ~30초.
    5년 명시 입력 시는 60+ chunks → timeout. 별도 라운드에서 안내 메시지 또는 병렬화.
  scenario_cases: ["S09-C5", "S09-C6", "S09-C8", "S10-C8"]
  fix_commits: [e9c8387, 2863528]

- truth: "/bids 결과 0건 메시지 — '결과 없음 (25966건)' 사용자 혼란 해소"
  status: resolved
  reason: "User reported: '결과없음(25966건)인데, 표시가 안됨. 결과없음으로 나옴. 페이징처리가 작동됨 (err-04.png)'"
  severity: major
  test: implicit
  root_cause: "키워드 LIKE 매칭이 페이지 1에서 0건이지만 total_count는 G2B 전체 25966건 → 사용자에게 '왜 표시 안 됨?' 의문"
  artifacts:
    - path: "frontend/src/app/bids/page.tsx (Results 0건 분기)"
  fix_action: |
    "이 페이지에서 키워드 'X' 매칭 0건 — 기간 내 총 N건 공고가 있지만 본 페이지는 매칭 없음.
     '깊은 검색' 체크박스를 켜면 5배 깊이 스캔 (응답 시간 ~22초). 또는 다음 페이지 시도."
  scenario_cases: ["S05-C10"]
  fix_commits: [e9c8387]
