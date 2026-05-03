# Phase 22 — ROOT-CAUSE 통합

> 5개 결함의 근원 진단 통합. F2/F3/F4·F5는 sub-agent 분석 결과 요약.

## F1 — 포트 미스매치 (확정·완료)

**Root cause**: 자율 v21(74501a8)에서 frontend default URL을 8080→8081로 변경했으나 backend 정합 누락 (`app/config.py`, `app/server.py` docstring, `.env.example`, `frontend/.env.example`, `page.tsx` footer가 8080 잔존).

**환경적 정황**: 사용자 PC에서 포트 8080을 외부 프로세스 PID 7948 + 37424가 LISTEN 중. v21 commit message에 "8080 충돌 회피, 운영 표준 8081" 명시.

**수정**: 6 파일 8081 통일 (이미 적용). 사용자 액션: `.env`의 `SERVER_PORT=8080` → 삭제 또는 8081, 백엔드를 `--port 8081`로 재기동.

**잔재 정합 (chore v22.5)**: README, DEPLOY, USER-GUIDE, OPERATIONS, TROUBLESHOOTING, frontend/README, frontend/tests/e2e/README, docs/API_신청, docker-compose 2종, e2e.yml.

---

## F2 — `trace_bid_lifecycle` R26BK01435763-000 빈 결과

### 호출 경로
- `frontend/src/app/bids/trace/page.tsx:16-26` URL `?no=R26BK01435763-000` → bidNo `R26BK01435763` + bidOrd `00`
- `frontend/src/lib/actions.ts:9-14` Server Action → `callMcpTool("trace_bid_lifecycle")`
- `app/tools/workflow.py:44-117` 6단계 병렬 (사전규격→공고→응찰→낙찰→NTS→summary)

### 핵심 흐름
- `app/tools/bid.py:14-33` `_infer_period_from_bid_no` — R 형식 인식: `R26` → 2026-01-01~2026-12-31
- `app/tools/bid.py:286-385` 단건 1차(inqryDiv=3) + 2차(inqryDiv=1 + 연도) 폴백
- `app/tools/bid.py:387-400` 3차 폴백 — **자율 v15.1(c18d63b)이 1년 → 30일로 단축**
- workflow는 모든 단계가 `found=False` 시 summary 모든 필드 `None` → frontend `"—"` 렌더

### Root Cause (우선순위)
| # | 가설 | 확신 | 근거 |
|---|------|------|------|
| **P1** | **v15.1의 30일 폴백 trade-off** — R 형식 공고가 30일 이전 등록되면 폴백 미커버 | **85%** | git log c18d63b 트레이드오프 코멘트 |
| P2 | 2차 inqryDiv=1 폴백 예외 조용히 삼킴 (`bid.py:297, 327`) | 60% | `try: ... except Exception: continue` 로깅 없음 |
| P3 | bid_no 정규화 미스매칭 (G2B raw vs 요청) | 40% | `bid.py:376` `str(raw.get("bidNtceNo"))` 직접 비교 |

### 수정 방향 (v22.3)
1. **3차 폴백을 R/숫자 형식이면 추정 연도 범위로 우선 시도, 그렇지 않으면 30→90일 progressive**
2. 2차 폴백 예외에 `log.warning` 추가 (silent fail 가시화)
3. (선택) R 형식 KWater 어댑터 라우팅은 추후 phase

---

## F3 — 발주기관 분석 데이터 부재

### 호출 경로
- `frontend/src/app/agencies/page.tsx:135` `getAgencyPricePattern(instName, bizType, dateFrom, dateTo)`
- `frontend/src/lib/actions.ts:61-74` → `callMcpTool("analyze_agency_price_pattern")`
- `app/tools/analytics.py:374-485` `analyze_agency_price_pattern`
- → `app/tools/award.py:209` `search_awards(inst_name=...)`

### 핵심 흐름
- `award.py:226` `chunk_date_range(date_from, date_to, max_days=31)` — 5년 4개월 = **52 chunks** × 4 biz × 1 endpoint ≈ 200+ G2B 호출
- `award.py:269-272` 발주기관 필터:
  ```python
  inst = (raw.get("dminsttNm") or "") + " " + (raw.get("ntceInsttNm") or "")
  if inst_name not in inst:
      continue
  ```
- `analytics.py:411-422` `award_rate` 추출 → 빈 리스트면 `sample_count=0` + note 반환

### Root Cause (우선순위)
| # | 가설 | 확신 | 근거 |
|---|------|------|------|
| **P1** | **`award.py:270` 부분일치(`inst_name not in inst`) — 변형 표기/공백/축약과 미매칭** | **80%** | "경찰청 경찰대학" vs G2B 응답 (`ntceInsttNm="경찰대학"`, `dminsttNm="경찰청"` 등 분산) |
| P2 | `award_rate` G2B에서 NULL → continue → 0건 (`analytics.py:410-422`) | 15% | `sucsfbidRate` / `opengRslcfRate` 둘 다 NULL 시 |
| P3 | 5년/52 chunk 타임아웃 (rate_limit) | 5% | `award.py:221-223` |

### 수정 방향 (v22.4 — 별도 phase 권장, 영향 큼)
1. 매칭 알고리즘 강화: 정확 일치 OR `dminsttNm` 단독 OR `ntceInsttNm` 단독 OR Jaro-Winkler 유사도 ≥ 임계
2. 매칭 0건 시 `note`에 실제 응답된 표기 샘플 3개 첨부 (사용자가 정확 표기 학습)
3. `analytics.py`에 첫 매칭 발주기관명 `log.info` 추가

---

## F4 — 페이징 빈 페이지 (25966건/페이지2 공란)

### 핵심 코드
- `app/tools/bid.py:211-215`:
  ```python
  has_more = (
      (total_count > inp.page * page_size * len(endpoints))
      if (max_scan_pages == 1 and len(chunks) == 1)
      else (total_count > scanned_total and len(matches) >= inp.limit)
  )
  ```
- `app/tools/bid.py:205-206` 빈 응답 시 `break` (안쪽 루프)
- `frontend/src/app/bids/page.tsx:255-289`:
  ```tsx
  const isLikeZero = !!params.keyword && totalCount > 0;
  if (isLikeZero) "키워드 매칭 0건"
  else "결과 없음 (총 X건). 페이지 N. 다음 페이지를 시도하세요."
  ```

### Root Cause (우선순위)
| # | 가설 | 확신 | 근거 |
|---|------|------|------|
| **P1** | **`has_more`가 `total_count > page*page_size*len(endpoints)` 단순 비교 — `len(items_raw)<page_size`로 break했어도 True 유지** | **75%** | 빈 page에서도 `has_more=True` 반환 |
| P2 | `total_count` 3 endpoint 누적 → `len(endpoints)=3`로 곱셈 보정해도 endpoint별 분포 차이로 부정확 | 40% | `bid.py:172` |
| P3 | frontend 분기에서 `params.keyword` 누락 가능성 (=`isLikeZero=false`로 잘못된 메시지 출력) | 25% | URL params 파싱 line 102-111 추가 검증 필요 |

### 수정 방향 (v22.2)
1. `has_more` 계산 직후 `if not matches: has_more = False` 보수적 정정
2. (선택) frontend 메시지: items 비었고 totalCount > 0이면 무조건 "키워드/조건 매칭 0건 (페이지 N / 총 N건)"

---

## F5 — 깊은 검색 HTTP 500 (구축사업 + 5x LIKE)

### 핵심 코드
- `frontend/src/app/bids/page.tsx:118` `deep` 체크박스 → `scanPages=5` URL 인자
- `app/tools/bid.py:88, 120, 135-136` `max_scan_pages = max(1, min(int(scan_pages), 10))` → 5
- v9(5d0097c) "업체명 LIKE + 입찰 deep 검색" 추가
- v21(74501a8) frontend default 8080 → 8081 변경

### Root Cause (우선순위)
| # | 가설 | 확신 | 근거 |
|---|------|------|------|
| **P1** | **v21 fix가 이미 해결한 결함** — frontend가 8080 외부 서버(PID 7948)에 POST → 외부 500 응답. v21 commit msg에 명시 | **70%** | v21 이전 환경 한정 |
| P2 | deep 5 페이지 × 3 endpoint × 1 chunk = 최대 15 G2B 호출 → timeout 또는 rate-limit → MCP 예외 → 500 매핑 | 25% | `bid.py:154-207` |
| P3 | v9 SSE 파싱 강화 이전 long-response 불완전 파싱 | 5% | `mcp-client.ts:55-68` (이미 강화됨) |

### 수정 방향 (v22.6 — 검증 우선)
1. **사용자 환경에서 frontend rebuild + 8081 재기동 후 deep 검색 재시도**
2. 재현 시: deep 분기에서 timeout/rate-limit 명시적 핸들링 + 사용자 친화적 에러 메시지
3. 재현 안 되면: F5는 v21 fix로 해결 처리, ROOT-CAUSE에 closure 기록

---

## 종합 Fix 순서 (확정)

```
v22.1  fix(port): 운영 표준 8081 정합 (코드 6 파일)            ← 이미 적용, commit 대기
v22.2  fix(bid): 페이징 has_more 빈 응답 시 False 정정         ← F4
v22.3  fix(bid): trace 3차 폴백 R형식 연도 범위 + progressive  ← F2
v22.4  fix(award): 발주기관 매칭 정합 (별도 phase 권장)        ← F3
v22.5  chore(port): docs/docker/CI 8081 정합                   ← F1 잔재
v22.6  verify(deep): F5 v21 fix 효과 검증 (사용자 화면)        ← F5
```

## 사용자 액션 대기 항목

- [ ] `.env`의 `SERVER_PORT=8080` → 8081 또는 라인 삭제
- [ ] 백엔드 8081 재기동: `uvicorn app.server:app --port 8081`
- [ ] frontend rebuild & 재기동 (v21 변경 반영): `cd frontend && npm run build && npm run start`
- [ ] err-01 화면 (localhost:8081) 정상 접속 확인
- [ ] err-05 (구축사업 + deep) 재시도 → 500 재현 여부 확인

---

## 사용자 화면 검증 결과 — 신규 결함 4건 (발화 #4·#5)

### F6 — UX loading 안내 부재 (입찰추적·발주기관 공통)

**증상**: G2B chunking으로 응답 10~90초 소요. 사용자가 "응답 멎었나" 인지 어려움. err-02에 "MCP 호출 중..." 텍스트는 있으나 작고 색이 약함.

**Root cause**: TimelineSkeleton/Skel이 `animate-pulse + ⏳`만 표시. cursor 변화 없음. 진행 메시지 없음.

**수정 (v22.4 코드 적용 — commit 대기)**:
- `bids/trace/page.tsx` TimelineSkeleton: `cursor-wait` + 큰 spinner + 명시 메시지("R 형식 채번은 30~90초 소요 가능")
- `agencies/page.tsx` Skel: `cursor-wait` + spinner + 청크 수·예상 초 안내

---

### F7 — 업체 프로필 페이지 전체 미표시 (Agent F7)

**Root Cause** (1순위, 90%):
- `app/tools/workflow.py:122-218` `vendor_profile`이 정상 작동하지만 **V1·V2·V3 도구가 스텁** (EVAL 키 미발급) + NTS 키 미설정 → 모든 section 빈 배열
- frontend `/vendors/[bizNo]/page.tsx`가 모든 sub-section을 조건부 렌더링 (`sections.awards?.items?.length > 0`) → **전부 스킵 → 빈 화면 인식**
- p0 자동테스트 S08-C1~C10이 `items=0`로 PASS = 도구는 OK이나 응답이 비어있음을 의미

**수정 (v22.5)**:
- frontend가 빈 응답 시 명시적 안내 표시: "NTS 진위확인 키 미설정 / V1·V2·V3 EVAL 키 발급 후 활성화 — 현재는 awards만 작동"
- backend `vendor_profile`에 `implementation_status` 필드는 이미 있음 → frontend가 이걸 노출

---

### F8 — 입찰검색 매칭 실패 (Agent F8)

**Root Cause** (1순위, HIGH):
- G2B `getBidPblancListInfo*` API는 **keyword 파라미터 미지원** → 클라이언트 1개월 999건 받아 로컬 `if keyword not in title: continue` 필터
- `scan_pages=1` (기본) → **첫 999건만 스캔**. 1개월에 더 많은 공고가 있으면 키워드 매칭 누락
- **v22.2 fix 부작용**: `if not matches: has_more = False`가 정상 케이스(=다음 페이지 시도 가능)에서도 차단. err-04에서 page 2 빈 응답이지만 페이지 3에 매칭 있을 가능성 차단

**수정 (v22.6)**:
- v22.2 정정: `if scanned_total == 0: has_more = False` (G2B 빈 응답 한정)
- 매칭 0건이지만 G2B는 데이터 줌 → has_more 유지 (frontend 권유 가능)
- `bids/page.tsx`의 isLikeZero 분기 검증 (사용자 화면에 "결과 없음 (25966건)" 표시된 = isLikeZero=False였음 → 분기 버그 추가 진단)

---

### F9 — 전체 응답 속도 느림 (사용자 발화 #5)

**증상**: 입찰추적·발주기관·검색 모든 화면이 느림 (기본 30~60초).

**누적 비용 분석**:
- trace: 6단계 `asyncio.gather` 모았지만 frontend는 1 await로 다 기다림 (Streaming 미활용)
- v22.3 R 형식 폴백: 추정 연도(12 chunks) × 3 endpoints × scan_pages=2 = 최대 72 G2B 호출
- agencies: 1개월 × 4 biz × 6 chunks (180일 default) ≈ 24+ 호출
- bids deep: 5 pages × 3 endpoints × 1 chunk = 15 호출
- cache hit률 미측정 — 동일 요청 반복 시 cache_result decorator 효과는 있을 듯

**SLA (사용자 발화 #6)**: **통상 5초 이내**.
현재 측정치 (체감):
- trace 단일 채번 (R 형식): 30~90초 (12 chunks × 3 endpoints 폴백)
- agencies 6개월 default: 30~60초 (6 chunks × 4 biz)
- bids deep: 20~50초 (5 pages × 3 endpoints)

**Phase 23 design proposal (5초 SLA 달성 — 사용자 승인 후 가동)**:

A) **Streaming 1st-byte (가장 큰 효과)**
   - trace: backend가 6단계 `asyncio.gather`를 한꺼번에 await → JSON으로 한 번에 반환. frontend는 한 번에 다 기다림
   - 변경: 6단계를 SSE 스트림으로 분리 (또는 frontend 6 Suspense로 단계별 호출). 첫 단계 1-2초 내 화면 도착 → 사용자 체감 5초 이내

B) **default 기간 대폭 단축**
   - agencies: 180일 → 30일 (사용자가 명시 시 확장 알림)
   - bids: 30일 그대로 OK
   - trace 폴백: R 형식이지만 첫 시도는 30일 → 못 찾으면 90 → 365 progressive (현재 v22.3은 R이면 처음부터 12 chunks)

C) **R 형식 폴백 lighter**
   - v22.3: 추정 연도(12 chunks) × 3 endpoints × scan=2 = 72 G2B 호출
   - 정정: 사용자 입력 biz_type 우선 endpoint 1개 + 30일/90일 progressive → 못 찾으면 그제서야 연도 범위. 보통 케이스는 1-2초 OK

D) **G2B 호출 병렬화 극단**
   - 현재 chunk 직렬 → asyncio.gather로 chunk 모두 동시
   - rate-limit 주의 (`app/core/rate_limit.py`)

E) **사전 ETL 캐싱 (별도 sprint)**
   - 인기 키워드/발주기관/최근 30일 데이터를 background job이 미리 G2B에서 fetch → Redis 캐싱
   - 사용자 검색 = 거의 cache hit → 0.5초 이내

F) **G2B keyword 미지원 우회**: backend가 "최근 30일 1개월 청크" 데이터를 cache로 보관 → 키워드 client filter는 cache에서 즉시

**우선 적용 (5초 SLA 임박 효과)**: A + B + C. D는 rate-limit risk 검증 필요. E는 별도 sprint.

---

## 종합 Fix 순서 (갱신)

```
v22.1 ✅ commit db7fb41   F1 포트 정합
v22.2 ✅ commit 9729f72   F4 has_more 보정 (v22.6에서 정정됨)
v22.3 ✅ commit b71f4d2   F2 trace 폴백 R형식 + progressive
v22.4 ✅ commit e66f1b7   F6 UX (trace + agencies cursor-wait + spinner + 메시지)
v22.5 ✅ commit e2762d7   F7 vendor 빈 응답 명시 안내
v22.6 ✅ commit 08025c6   F8 has_more 정정 + isLikeZero trim
v22.7 🟡 자동진행            chore: docs 9 파일 8081 정합 (docker-compose / e2e.yml은 별도 — Dockerfile 정합 필요)
─────────────────────────────────────────────────────
Phase 23 (별도, 사용자 승인 후)  F9 성능 개선 (Streaming + cache + 기본값)
Phase X (별도)                   F3 발주기관 매칭 강화 + F5 deep 재현 시 진단
```

