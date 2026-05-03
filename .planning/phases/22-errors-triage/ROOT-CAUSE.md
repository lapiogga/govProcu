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
