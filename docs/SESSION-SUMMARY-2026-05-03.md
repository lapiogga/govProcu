# SESSION SUMMARY — 2026-05-03 (자율 v9~v15.1 + UAT 라운드)

> 5/2 자율 v3~v8 종결(`.planning/phases/01-autonomous-v3-v8/01-SUMMARY.md`) 다음 진행.
> 5/3 자율 v9 (사용자 후속 결함 3건) → /gsd-verify-work → 결함 6건 라운드 → fix v10/v10.2/v11/v12/v15.1.

---

## 1. 본 세션 개요

| 라운드 | 주제 | 산출 |
|---|---|---|
| **v9** | 사용자 후속 결함 3건 (vendor LIKE / bids deep / KWater detail) | commit 5d0097c |
| **v10 UAT** | /gsd-verify-work skill — 결함 6건 발견 + Full Test Plan v2 + chunking 도입 | commit e9c8387 |
| **v10.2** | 단건 폴백 강화 + agencies 6개월 default | commit 2863528 |
| **v11 docs** | PROMPTS-LOG #58~#69 + UAT.md 6 결함 매핑 | commit 5913601 |
| **v12** | bid_notice_no 인자 + 큰범위 timeout 안내 | commit f0fef7f |
| **v14 e2e** | standalone CSS 정적자산 fix (env) → 36/36 PASS 회복 | env fix (no commit) |
| **v15.1** | trace 폴백 추정기간 1년 → 30일 단축 | commit c18d63b |

**총 5 commits + 1 환경 fix** (origin 5 commits ahead).

---

## 2. UAT 결함 6건 (사용자 N42 보고 → 일괄 fix)

| # | 보고 내용 | 상태 | 검증 |
|---|---|---|---|
| #1 | 4개월 범위 조회 안됨 (G2B 1개월 제약) | ✅ resolved | 라이브 67초, 1월/4월 데이터 merge |
| #2 | 업종 '전체' 검색 안됨 | ✅ resolved | 3종 endpoint merge + dedup |
| #3 | 마감 임박 정렬 안됨 | ✅ resolved | e2e Wave2 PASS |
| #4 | R26BK01435763-000 입찰추적 안됨 (err-02) | ✅ resolved | trace 라이브 found=True (44초) |
| #5 | 발주기관 분석 안됨 (5년 timeout, err-03) | ✅ resolved + 안내 | default 6개월 + 큰범위 경고 박스 |
| #6 | 결과 없음 25966건 페이지 표시 (err-04) | ✅ resolved | "키워드 매칭 0건 + deep 권장" |

---

## 3. 측정 기반 default 결정 (사용자 N42-2 지시)

라이브 cold 측정 (`tests/measure_cold.log`) 후 페이지별 default:

| 페이지 | default | Cold P99 | 측정 케이스 |
|---|---|---|---|
| /bids | 30일 | 4.2초 | q=정보화 D30 → 4.12초 |
| /vendors LIKE | 30일 (90→30 단축) | 20초 | broad 키워드 19.7초 우려 |
| /vendors/{biz} | 365일 | 4초 | chunk 12회 자동 |
| /agencies | 180일 (365→180 단축) | 30초 | 1년 60초 → 6개월 |
| /external/kwater | 직전월 | 3.5초 | 단일 월 API 특성 |

**큰 범위 입력 안내**: /bids 1개월+ / /agencies 1년+ → 노란 경고 박스 + 예상 시간.

---

## 4. Full Test Plan v2 (200 케이스)

`.planning/phases/01-autonomous-v3-v8/02-FULL-TEST-PLAN.md` + `tests/full-test-cases.json`:

- 시나리오 20 × 케이스 10 = 200건 (P0 110 / P1 60 / P2 30)
- 키워드 풀 20 / 발주기관 풀 15 / 사업자 풀 10 / 업체명 풀 16 / 공고번호 풀 10 / KWater 월 풀 10
- 날짜 매트릭스 11종 (D1, D1*, D3, D3*, W1, W1*, W2*, M1, M1A*, M1B*, M3, Y1)
- 클릭 검증 18건 (BidLink/AgencyLink/VendorLink 곳곳 분산)

**JSON fixture**는 자동화 친화적 schema — 향후 Playwright runner 또는 Python 호출 가능.

---

## 5. 핵심 코드 변경

### 5.1 `app/core/daterange.py` (신규)
- `chunk_date_range(date_from, date_to, max_days=31)` — G2B 1개월 제약 자동 분할

### 5.2 `app/tools/bid.py`
- `_resolve_bid_endpoints(biz_type)` — None이면 3종 endpoint 반환
- `_infer_period_from_bid_no(bid_no)` — R26→2026, 20240101234→2024 prefix 파싱
- `search_bid_notices` — chunking + 3종 merge + (no, ord) dedup + `bid_notice_no` 정확 매칭 인자
- `get_bid_notice_detail` — 3-tier 폴백 (inqryDiv=3 → inqryDiv=1 → search_bid_notices 30일)

### 5.3 `app/tools/award.py`
- `search_awards` / `search_awards_by_vendor` — chunking + 4종 endpoint 병합
- `get_award_detail` — 동일 폴백 패턴

### 5.4 Frontend
- `/bids/page.tsx` — sortItems 3-tier deadline (미래/과거/null) + LIKE 0건 명확 메시지 + 큰범위 안내
- `/bids/trace/page.tsx` — `-` suffix 자동 split (R26BK01435763-000 → no=R26BK01435763, ord=000)
- `/agencies/page.tsx` — default 180일 + 큰범위 안내 박스
- `/vendors/page.tsx` — default 30일

### 5.5 환경 fix (회귀 36/36 PASS 회복)
- standalone build 후 `cp -r .next/static .next/standalone/.next/` 1회 명령 — Dockerfile.frontend 또는 build script 보강 권장

---

## 6. 본 라운드 발견사항

1. **G2B 단건 조회 패턴 한계** — `inqryDiv=3` + `bidNtceNo` + `bidNtceOrd` 가 일부 endpoint(R 형식)에서 0건 반환. `inqryDiv=1` 폴백도 `bidNtceNo` 무시 → 999개 중 클라이언트 필터 필요.
2. **G2B 1개월 제약** — `inqryBgnDt~inqryEndDt` 초과 시 resultCode 07 또는 silent 0건. chunking 필수.
3. **추정 기간 1년 풀스캔의 비용** — chunks 12 × 3 endpoints = 36 호출 = ~60초. 폴백은 최근 30일 우선 + progressive expansion 패턴 필요 (별도 라운드).
4. **/vendors LIKE 응답 시간 편차** — broad 키워드(디지털) D30 19.7초 vs narrow(솔루션) D60 1.7초. 매칭률 dominated.
5. **Next.js standalone build CSS 누락** — `next build` 만으로는 정적자산 자동 복사 안 됨 → Radix portal positioning 실패 → cmdk/Wave2 e2e fail. 환경 fix 필수.
6. **frontend dev mode (turbopack) RSC manifest 에러** — production build로 우회.
7. **R26BK01435763 자체 G2B 미존재** — 사용자 보고 케이스. 사용자 클릭 출처 불명 (오래된 공고 삭제 또는 다른 시스템 공고번호 가능성). R26BK01439997 (실존)로 fix 검증.

---

## 7. 알려진 한계 (별도 라운드 follow-up)

| 항목 | 우선순위 | 메모 |
|---|---|---|
| /agencies 5년 입력 timeout | 중 | 안내 메시지만 추가 — asyncio.gather 병렬화 또는 max_chunks 인자 필요 |
| trace 폴백 30일 한계 | 중 | 30일 초과 등록 R 형식 미커버 — progressive expansion (30→90→180) |
| standalone build 정적자산 | 낮 | Dockerfile.frontend 또는 npm script post-build 자동 cp |
| /vendors LIKE broad 키워드 | 낮 | 사용자 안내 추가 ("키워드 더 구체적") |

---

## 8. 다음 세션 진입점

```bash
# 1. 동기화
git log --oneline -10  # c18d63b 또는 그 이후

# 2. 인프라 가동
docker start govprocu-redis govprocu-neo4j-poc
cd frontend && (MCP_MOCK_MODE=true PORT=3025 node .next/standalone/server.js)
# (라이브 mode: cd .. && SERVER_PORT=8081 FASTMCP_STATELESS_HTTP=true python -m app.server)
# frontend 라이브: cd frontend && (GOVPROCU_MCP_URL=http://localhost:8081 PORT=3020 npm run dev)

# 3. 사용자 spot-check 우선순위
#   A. /bids?q=AI&from=20260101&to=20260503  ← 4개월 chunking + 큰범위 경고 박스
#   B. /bids?q=AI 정렬 메뉴 → "마감 임박" 클릭  ← URL ?sort=deadline 갱신
#   C. /bids/trace?no=R26BK01439997-000  ← suffix split + bid_notice stage found=True
#   D. /agencies?name=한국수자원공사  ← default 6개월 + 사정률 패턴

# 4. 다음 라운드 우선순위
#   ① 시나리오 P0 110건 자동 실행 인프라 (tests/full-test-cases.json runner)
#   ② trace 폴백 progressive expansion (30→90→180)
#   ③ /agencies 병렬화 (asyncio.gather)
#   ④ Dockerfile.frontend 정적자산 자동 cp (standalone build)
#   ⑤ search_bid_notices에 max_chunks 인자 (대범위 timeout 방지)
```

---

## 9. Commit chain (origin 동기화 완료)

```
?      v22 (다음)  err-05 fix rebuild + 검증 (다음 세션 진입 시)
?      v21 (보류)  세션 정리 commit (mcp-client default 8081 + docs)
05b89f2  v20    P1+P2 100% PASS (41/41) + analyze_price endpoints 노출
db6478f  v19    P0 100% PASS (73/73) + workflow.py endpoints 노출
65569a2  v18    lookup_by_* 4종 시그니처 mapping (94.5%)
e64a2ba  v17    fixture 정밀화 — case-level tool / date_matrix (86%)
2034345  v16    P0 runner 작성 + 시점관리 v6 (71%)
c18d63b  v15.1  trace 폴백 추정기간 1년 → 30일 단축
f0fef7f  v12    bid_notice_no 정확 매칭 인자 + 큰범위 timeout 안내
5913601  v11    PROMPTS-LOG/UAT docs (#58~#69)
2863528  v10.2  G2B 단건조회 폴백 강화 + agencies 6개월 default
e9c8387  v10    G2B 1개월 chunking + 업종 전체 merge + R 형식 폴백 + 측정 default
```

## 10. 자동 검증 누적 (자율 v16~v20)

| 우선순위 | API PASS | API FAIL | UI SKIP | 합계 |
|---|---|---|---|---|
| P0 | 73 | 0 | 47 | 120 |
| P1+P2 | 41 | 0 | 39 | 80 |
| **합계** | **114** | **0** | **86** | **200** |

- API 자동 검증: 114/114 = 100%
- e2e Playwright: 36/36 = 100%
- 유효 합계: 150/150 = 100%
- 라이브 실행 시간: P0 15분 + P1+P2 7분 = 22분

## 11. err-05 (사용자 spot-check 발견)

`/bids?q=구축사업&type=용역&from=20260301&to=20260320&deep=1` → "오류: HTTP 500"

**진단**: 8080 포트에 다른 서버(PID 7948) 가 HTTP 500 응답. frontend `mcp-client.ts` default URL이 8080 (build time inject) → 운영 표준 8081 미사용.

**fix (commit pending)**:
- `frontend/src/lib/mcp-client.ts`: default `http://localhost:8080` → `http://localhost:8081`
- `frontend/next.config.ts`: 동일 변경 (build time env inject)

**다음 세션 진입 시 필수**:
```bash
cd frontend && npm run build
cp -r .next/static .next/standalone/.next/
# standalone 재시작
GOVPROCU_MCP_URL=http://localhost:8081 PORT=3020 node .next/standalone/server.js
```

---

작성: 2026-05-03 (자율 v9~v20 종합 + err-05 fix 보류)
