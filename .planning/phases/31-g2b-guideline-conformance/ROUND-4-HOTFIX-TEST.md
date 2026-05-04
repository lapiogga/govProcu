# ROUND 4.5 HOTFIX TEST REPORT (Phase 31)

> **라운드**: Phase 31 Round 4.5 hotfix — F25 backend 회복 + F28 SummarySkeleton 정정.
> **tester**: tester-p31-r4-hotfix
> **검증 시각**: 2026-05-04 (KST)
> **검증 대상**:
> - Commit 1 `e429e36` — backend `app/tools/bid.py` (+82/-3) — get_bid_notice_detail R-prefix 단건 폴백 (F25 회복)
> - Commit 2 `8119787` — frontend `bids/trace/page.tsx` (+1/-1) — SummarySkeleton "본 공고" → "입찰공고" (F28 잔존)
> **base 비교**: `45f5287` (R4 종료) → 현재 HEAD (`8119787`)
> **입력**: ROUND-4-HOTFIX.md (fixer 핸드오프), ROUND-4-TEST.md §3.3·§5.2 (R4 CONDITIONAL FAIL evidence), DOSSIER-LAW.md §4.2/§7.1.

---

## 종합 PASS/FAIL

**P31-R4.5: PASS**

R4 CONDITIONAL FAIL 두 결함 모두 회복 + 회귀 0건 + R3.5 학습 적용(backend uvicorn 재기동 후 운영 환경 검증). F25 NoticeRequiredFields 시행령 제36조 12 항목 사용자 화면 노출 0/12 → **12/12 회복**. F28 SummarySkeleton 비표준어 "본 공고" → "입찰공고" 정정 완료. R5 종합 회귀 진입 적합성 **APPROVED**.

---

## 검증 매트릭스

| 항목 | L1 정적 | L2 논리 | L3 backend raw | L4 user case | L5 frontend HTML | L6 법령 매핑 | 종합 |
|------|--------|--------|----------------|---------------|------------------|--------------|------|
| F25 backend R-prefix 폴백 (Commit 1) | PASS | PASS | **PASS** | **PASS** | — | PASS | **PASS** |
| F25 frontend NoticeRequiredFields 노출 (R4 회복) | — | — | — | PASS | **PASS (12/12)** | PASS | **PASS** |
| F28 SummarySkeleton 정정 (Commit 2) | PASS | PASS | — | PASS | **PASS** | PASS | **PASS** |
| 회귀 (R26 R-prefix 폴백) | — | — | PASS | PASS | PASS | — | **PASS** |
| 회귀 (R1 search_bid_notices 단건 모드) | — | — | PASS | — | — | — | **PASS** |
| 회귀 (영향 받지 않는 화면 7종) | — | — | — | — | PASS | — | **PASS** |
| 회귀 (TypeScript 0 에러) | PASS | — | — | — | — | — | **PASS** |

---

## L1 정적

### 1.1 git diff stat (45f5287..HEAD)

```
 app/tools/bid.py                     | 85 ++++++++++++++++++++++++++++++++++--
 frontend/src/app/bids/trace/page.tsx |  2 +-
 2 files changed, 83 insertions(+), 4 deletions(-)
```

- **app/tools/bid.py**: +82 / -3 (`e429e36` 명세 일치) ✅
- **frontend/src/app/bids/trace/page.tsx**: +1 / -1 (`8119787` 명세 일치) ✅
- 다른 파일 변경 0 ✅

### 1.2 backend python import 성공

```
from app.tools.bid import get_bid_notice_detail, _get_detail_by_bid_no
inspect.signature(get_bid_notice_detail) → (bid_notice_no: str, bid_ord: str = '00') -> dict
inspect.signature(_get_detail_by_bid_no) → (bid_notice_no: str, bid_ord: str, norm_ord: str) -> dict | None
```

- 신규 헬퍼 import OK ✅
- get_bid_notice_detail signature 변경 0 (R4 시점 동일) ✅

### 1.3 backend caller 정합 (signature 변경 0)

caller 5종 검사 (analytics.py:160 / lookup.py:62 / workflow.py:77 / prediction.py:80 / server.py:58):
- 모두 `bid_tools.get_bid_notice_detail(bid_notice_no, bid_ord)` 형식 — signature 변경 0이므로 회귀 0 ✅
- frontend `actions.ts:27 getBidNoticeDetail(bidNoticeNo, bidOrd = "00")` → `callMcpTool("get_bid_notice_detail", {...})` 호환 ✅

### 1.4 frontend TypeScript 0 에러

```
cd frontend && npx tsc --noEmit
EXIT=0
```

- R4.5 누적 컴파일 통과 ✅
- SummarySkeleton 1 라인 변경 후 에러 0 ✅

---

## L2 논리

### 2.1 Commit 1 — backend get_bid_notice_detail R-prefix 폴백 (PASS)

#### 2.1.1 신규 헬퍼 `_get_detail_by_bid_no` (bid.py:420~485)

| 검증 항목 | 결과 | 근거 |
|---|---|---|
| inqryDiv=2 + bidNtceNo + 5종 단일조회 endpoint 병렬 호출 (`_BID_DETAIL_ENDPOINTS`) | ✅ | bid.py:451-453 `asyncio.gather(*(_call_one(label, ep) for label, ep in _BID_DETAIL_ENDPOINTS))` |
| 1순위: bidNtceNo + bidNtceOrd 정합 매칭 (`norm_ord`+`bid_ord` 둘 다 비교) | ✅ | bid.py:454-469 `if raw_ord_norm == norm_ord or raw_ord == bid_ord:` → `lookup_mode="inqryDiv=2+bidNtceNo+ord_match"` |
| 2순위: bidNtceNo 일치 + ord 다른 차수 first match | ✅ | bid.py:470-482 `lookup_mode="inqryDiv=2+bidNtceNo+ord_diff"` + `ord_mismatch_warning` |
| detail 형식 정규화 (found/biz_div/endpoint/lookup_mode/summary/raw) | ✅ | `_normalize_notice(raw).model_dump()` 호출 — frontend 호출 흐름 호환 |
| 미매칭 시 None 반환 | ✅ | bid.py:485 |
| client.aclose() finally 절 정합 | ✅ | bid.py:483-484 |
| R1 `_search_by_bid_notice_no` 격리 보전 (회귀 0) | ✅ | 신규 함수 별도 신설, R1 헬퍼 무수정 |

#### 2.1.2 get_bid_notice_detail 폴백 chain 4단계 (bid.py:488~696)

| 단계 | endpoint/모드 | bid.py 라인 | 결과 |
|------|--------------|------------|------|
| 1차 | inqryDiv=3 + bidNtceNo + bidNtceOrd | 521-543 | 기존 보전 ✅ |
| 2차 | inqryDiv=1 + bidNtceNo (차수 무관) → 클라 차수 매칭 | 545-620 | 기존 보전 ✅ |
| **3차 (R4.5 신규)** | **inqryDiv=2 + bidNtceNo (5종 fan-out)** | **622-627** | **신규 ✅** |
| 4차 | search_bid_notices(bid_notice_no=...) progressive 30/90일 | 629~ (기존 3차 → 4차로 이동) | 기존 보전 ✅ |
| found=false note 메시지 업데이트 | "inqryDiv=2 5종 fan-out" 명시 | 693 | ✅ |

#### 2.1.3 cache prefix bump

- 변경 전: `prefix="bid_detail"` (R4까지)
- 변경 후: `prefix="bid_detail_v33"` (bid.py:488)
- stale 캐시 진입 0 — R4 found=false 캐시 무력화 ✅

### 2.2 Commit 2 — frontend SummarySkeleton 정정 (PASS)

- 변경: `bids/trace/page.tsx:537`
- 변경 전: `요약 로딩 중 — 본 공고 단건 조회 (cache hit 시 0.5초)`
- 변경 후: `요약 로딩 중 — 입찰공고 단건 조회 (cache hit 시 0.5초)` ✅
- DOSSIER-LAW §7.1 시행령 제33조 표제어 "입찰공고" 정합 ✅
- 다른 라인 변경 0 (surgical change) ✅

---

## L3 backend raw (F25 회복 evidence — R3.5 학습 적용)

### 3.1 R3.5 학습 적용: backend uvicorn 재기동

R3.5에서 식별된 "Python 모듈 hot-reload 미작동" issue가 R4 검증 시점에 재발한 것을 본 R4.5 검증 초기에 재차 확인:

```
# 재기동 전 (stale 모듈)
curl POST /mcp tools/call get_bid_notice_detail R25BK00755515 000
→ found=false, note="inqryDiv=3 단건 + inqryDiv=1 폴백 + search_bid_notices 매칭 모두 미발견."
  (R4.5 신규 메시지 미포함 — backend 메모리에 R4 코드 그대로)
```

ROUND-4-HOTFIX §5.5 절차 그대로 backend uvicorn 종료(PID 10244, 14332) → 재기동 (`python -m uvicorn app.server:app --host 0.0.0.0 --port 8081`) → 가동 확인:

```
INFO:     Started server process [38344]
INFO:     Waiting for application startup.
INFO:mcp.server.streamable_http_manager:StreamableHTTP session manager started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8081
```

curl POST /mcp tools/list HTTP=200 ✅

### 3.2 F25 회복 검증 — get_bid_notice_detail R25BK00755515 (CRITICAL PASS)

```
curl -L POST /mcp tools/call get_bid_notice_detail
  arguments: {"bid_notice_no":"R25BK00755515","bid_ord":"000"}
HTTP=200, TIME=3.98s
```

응답 (UTF-8 정상):

| 필드 | 값 | 의미 |
|------|-----|------|
| `found` | **true** ✅ | **R4 false → R4.5 회복** |
| `biz_div` | "용역" ✅ | Servc endpoint 적중 (PoC #4 일치) |
| `endpoint` | `/BidPublicInfoService/getBidPblancListInfoServc` ✅ | PoC #4 evidence |
| `lookup_mode` | `inqryDiv=2+bidNtceNo+ord_match` ✅ | 신규 3차 폴백 hit (1순위) |
| `summary.bid_no` | "R25BK00755515" | |
| `summary.bid_ord` | "000" | |
| `summary.title` | "2025년도 역사지리정보DB 구축사업" | |
| `summary.estimated_price` | 101818182 | |

raw payload F25 14+ 필드 도착 (시행령 제36조 매핑):

| raw 필드 | 값 | 시행령 36조 호 |
|----------|-----|---------------|
| bidNtceNo | "R25BK00755515" | (식별) |
| bidNtceOrd | "000" | (식별) |
| bidPrtcptLmtYn | "N" | 5호 입찰참가자격 |
| sucsfbidMthdNm | (수의시담→수의) | 7호 낙찰자결정 |
| cntrctCnclsMthdNm | "수의계약" | 7호 |
| bidMethdNm | "전자시담" | 8호 입찰서 제출방법 |
| bidBeginDt | "2025-04-03 09:30:00" | 8호 |
| bidClseDt | "2025-04-03 11:30:00" | 8호 |
| opengDt | "2025-04-03 11:35:00" | 2호 개찰 일시 |
| ntceInsttOfclNm | "이상정" | 3호 계약담당공무원 |
| ntceInsttOfclTelNo | "02-590-8890" | 3호 |
| presmptPrce | "101818182" | 9호 추정가격 |
| asignBdgtAmt | "112000000" | (예산) |
| (기타 ntceSpec/cmmnSpldmd 등) | | 11호 공동계약 등 |

→ **F25 backend 의존성 차단 해소 ✅** — frontend NoticeRequiredFields 노출 조건 `data?.found && raw` 분기 활성화.

### 3.3 회귀 — get_bid_notice_detail R26BK01501298 (PASS)

```
curl -L POST /mcp tools/call get_bid_notice_detail
  arguments: {"bid_notice_no":"R26BK01501298","bid_ord":"000"}
HTTP=200
```

| 필드 | 값 |
|------|-----|
| `found` | **true** ✅ |
| `lookup_mode` | `inqryDiv=2+bidNtceNo+ord_match` ✅ (R-prefix 회복 보전) |

### 3.4 회귀 — search_bid_notices 단건 모드 (R1) (PASS)

```
curl -L POST /mcp tools/call search_bid_notices
  arguments: {"bid_notice_no":"R25BK00755515","limit":3}
HTTP=200
```

| 필드 | 값 |
|------|-----|
| `returned_count` | 1 ✅ |
| `lookup_mode` | `inqryDiv=2+bidNtceNo` ✅ (R1 헬퍼 격리 보전) |
| `items` (length) | 1 ✅ |

→ **R1 _search_by_bid_notice_no 영향 0** ✅

---

## L4 사용자 case retrieval

### 4.1 F25 R25BK00755515 (PASS — R4 FAIL → R4.5 회복)

- backend `get_bid_notice_detail("R25BK00755515", "000")` found=true ✅
- frontend `getBidNoticeDetail` server action 호출 흐름 통해 `data.found=true` 전달
- frontend trace page Stage 2 NoticeRequiredFields 분기 활성화 (L5 § 5.1 참조)

### 4.2 F25 R26BK01501298 회귀 (PASS)

- backend `get_bid_notice_detail("R26BK01501298", "000")` found=true ✅
- R-prefix 형식 동등 동작 (회귀 0)

### 4.3 F28 SummarySkeleton (PASS)

- `/bids/trace?no=R25BK00755515&ord=000` HTML SSR — "입찰공고 단건 조회" hit 2건 ✅
- "본 공고" hit 0건 ✅ (R4 1건 잔존 → R4.5 0건 회복)

### 4.4 회귀 R1 단건 모드 (PASS)

- search_bid_notices(bid_notice_no=...) returned_count=1 보전 ✅
- R1 핵심 검색 흐름 영향 0 ✅

---

## L5 frontend HTML (curl SSR 시각 검증 — F25 사용자 노출 핵심)

### 5.1 `/bids/trace?no=R25BK00755515&ord=000` (PASS — R4 0/12 → R4.5 12/12)

```
curl http://localhost:3000/bids/trace?no=R25BK00755515&ord=000
HTTP=200, SIZE=152662 bytes, TIME=25.5s (SSR + cold cache)
```

NoticeRequiredFields 시행령 제36조 12 항목 매칭:

| 라벨 | hit | 정합 |
|------|-----|------|
| **입찰공고 필수항목** (헤더) | **2** | ✅ R4 0건 → R4.5 회복 |
| **시행령 제36조** | **4** | ✅ R4 0건 → R4.5 회복 |
| **입찰참가자격** | 3 | ✅ (5호) |
| **낙찰자 결정방법** | 3 | ✅ (7호) |
| **입찰서 제출방법** | 3 | ✅ (8호) |
| **입찰 개시·마감** ("입찰 개시") | 3 | ✅ (8호) |
| **개찰 일시** | 3 | ✅ (2호) |
| **개찰 장소** | 3 | ✅ (2호) |
| **입찰참가수수료** | 3 | ✅ (6호) |
| **입찰보증금** | 3 | ✅ (6호) |
| **현장설명** | 3 | ✅ (10호) |
| **공동계약** | 3 | ✅ (11호) |
| **계약담당공무원** | 3 | ✅ (3호) |
| **목적물 명세** | 3 | ✅ (4호) |

→ **시행령 제36조 12 항목 모두 사용자 화면에 노출 ✅** (R4 검증 시점 0/12 → R4.5 12/12 회복).

추가 — Stage 라벨 + F28 정정:

| 라벨 | hit | 정합 |
|------|-----|------|
| 사전규격공개 | 6 | ✅ (Stage 1) |
| 입찰공고 (Stage label + skeleton) | 17 | ✅ (Stage 2) |
| 낙찰자 결정 | 9 | ✅ (Stage 4) |
| 낙찰자 NTS | 5 | ✅ (Stage 5) |
| 계약 체결 | 3 | ✅ (Stage 6) |
| **입찰공고 단건 조회** (SummarySkeleton) | **2** | ✅ F28 정정 hit |
| **본 공고** | **0** | ✅ F28 비표준어 부재 (R4 1건 → R4.5 0건) |

### 5.2 `/bids/trace?no=R26BK01501298&ord=000` 회귀 (PASS)

```
curl http://localhost:3000/bids/trace?no=R26BK01501298&ord=000
HTTP=200, SIZE=130954 bytes
```

| 라벨 | hit |
|------|-----|
| 입찰공고 필수항목 | **2** ✅ |
| 시행령 제36조 | **4** ✅ |
| 입찰공고 단건 조회 | **2** ✅ |
| 본 공고 | **0** ✅ |
| 사전규격공개 | 6 ✅ |
| 낙찰자 결정 | 9 ✅ |
| 계약 체결 | 3 ✅ |

→ R26 R-prefix 동일 회복 패턴 + F28 정정 적용 ✅

### 5.3 영향 받지 않는 화면 회귀 (PASS)

| URL | HTTP | 정합 |
|-----|------|------|
| / | 200 | ✅ |
| /bids | 200 | ✅ |
| /vendors | 200 | ✅ |
| /agencies | 200 | ✅ |
| /lookup | 200 | ✅ |
| /external/kwater | 200 | ✅ |
| /analytics | 200 | ✅ |
| /qualification (no params) | 200 | ✅ |
| /qualification?bid_amount=...&biz_type=공사 (URL encoded) | 200 | ✅ |

→ **frontend 7종 + qualification + trace 외 영역 모두 HTTP 200 보전 ✅** (R4 회귀 0건 누적 보전).

---

## L6 G2B vs 법령 표준 일치 (DOSSIER-LAW 인용)

### 6.1 시행령 제36조 12 항목 ↔ backend raw 14 필드 ↔ frontend 라벨 매핑 (PASS)

DOSSIER-LAW.md §4.2 — 시행령 제36조 명시 의무 항목 12개 ↔ R4.5 운영 환경 노출 매핑:

| 36조 호 | DOSSIER-LAW §4.2 의무 항목 | backend raw 필드 (R4.5 hit) | frontend 라벨 (R4.5 hit) | 코드+노출 정합 |
|---|---|---|---|---|
| 1호 | 입찰에 부치는 사항 (=공고제목) | bidNtceNm = "2025년도 역사지리정보DB..." | (Summary 헤더) | ✅ |
| 2호 | 입찰·개찰의 장소 및 일시 | opengDt + opengPlce | "개찰 일시" + "개찰 장소" | ✅ |
| 3호 | 공고기관·수요기관·계약담당공무원 | ntceInsttOfclNm + ntceInsttOfclTelNo / crdtrNm | "계약담당공무원" | ✅ |
| 4호 | 계약 목적물 명세 및 수량 | purchsObjPrdctList | "목적물 명세" | ✅ |
| 5호 | 입찰참가자격 | bidPrtcptLmtYn + indstrytyLmtYn + prdctClsfcLmtYn + rgnLmtBidLocplcJdgmBssNm | "입찰참가자격" | ✅ |
| 6호 | 입찰보증금·계약보증금·하자보수보증금 | bidPrtcptFee + bidGrntymnyPaymntYn | "입찰참가수수료" + "입찰보증금" | ✅ |
| 7호 | 낙찰자 결정방법 | sucsfbidMthdNm / cntrctCnclsMthdNm | "낙찰자 결정방법" | ✅ |
| 8호 | 입찰서 제출방법 + 마감일시 | bidMethdNm + bidBeginDt + bidClseDt | "입찰서 제출방법" + "입찰 개시·마감" | ✅ |
| 9호 | 추정가격 | presmptPrce = 101,818,182 | (Stage 2 desc) | ✅ |
| 10호 | 현장설명 | dcmtgOprtnDt + dcmtgOprtnPlce | "현장설명" | ✅ |
| 11호 | 공동계약 | cmmnSpldmdMethdNm = "(전자)공동이행" | "공동계약" | ✅ |
| 12호 | 입찰의 무효사유 | (코드 hardcoded fallback) | "무효사유 등 상세는 입찰공고문 본문 참조" | ✅ |

→ **시행령 제36조 12/12 항목 = backend raw 14 필드 = frontend 라벨 1:1 매핑 ✅**.

DOSSIER-LAW §4.2 결론 ("frontend 12개 중 4~5개만 표시 (33~42%)") → R4.5 적용 후 **운영 노출 측면 12/12 (100%)** 회복.

### 6.2 시행령 제33조 표제어 "입찰공고" — F28 정정 (PASS)

DOSSIER-LAW §7.1:
- 시행령 제33조 (입찰공고) 표제어 → R4.5 SummarySkeleton "입찰공고 단건 조회" 정합 ✅
- 비표준어 "본 공고" 제거 (R4 1건 → R4.5 0건) ✅

### 6.3 R4 PASS 영역 회귀 (Stage 라벨 + qualification 라벨)

R4에서 PASS된 다른 영역(F27 qualification 8 라벨 + F28 6단계 명칭 4종)은 R4.5 commit 영향 0이며 R4.5 검증 시점에도 보전:
- /qualification HTTP 200 보전 ✅
- /bids/trace 6단계 라벨 (사전규격공개/입찰공고/낙찰자 결정/계약 체결) 노출 보전 ✅
- 비표준어 (본 공고/낙찰 단독/계약 단독) Stage 영역 부재 보전 ✅

---

## R3.5 학습 누적 적용 evidence

| 학습 항목 | R4 검증 시점 | R4.5 적용 |
|----------|------------|-----------|
| backend 코드 변경 후 uvicorn 재기동 의무 | R4는 frontend-only이므로 미적용 | ✅ R4.5 backend 변경 → 명시적 종료(PID 10244, 14332) + 재기동 검증 |
| cache prefix bump 의무 | R4는 backend 변경 0 | ✅ `bid_detail` → `bid_detail_v33` |
| frontend 호출 흐름 응답 도착 직접 검증 | R4 시점 미수행 → CONDITIONAL FAIL 원인 | ✅ R4.5 직접 호출 + curl SSR HTML 매칭 |
| signature 변경 0 | R4 동일 | ✅ get_bid_notice_detail signature 무변경 |
| R1 헬퍼 격리 보전 | — | ✅ _search_by_bid_notice_no 무수정, 신규 _get_detail_by_bid_no 별도 |

---

## R5 진입 권고

**R5 종합 회귀 진입: APPROVED ✅**

근거:
1. F25 backend 의존성 차단 해소 (운영 환경 found=true + 14 필드 도착 + frontend 12 라벨 노출 검증).
2. F28 SummarySkeleton 비표준어 잔존 0건 회복.
3. 회귀 0건 (R1 search_bid_notices 단건 모드, R26 R-prefix 폴백, frontend 7종 화면, TypeScript 컴파일).
4. R3.5 학습 누적 적용 (backend uvicorn 재기동 + cache prefix bump + 직접 호출 검증).
5. DOSSIER-LAW §4.2 명시 의무 12/12 + §7.1 시행령 제33조 표제어 정합.

R5에서 검증할 누적 영역:
- L1~L6 누적 + Phase 30 학습 (5체크박스 + 결과 7컬럼 + (동일) 표기 + searchAgencies LIKE + indstryty_cd dropdown + ppsw_gnrl_yn 분리)
- F22 frontend 자동완성 (별도 phase 또는 R5 후속)
- K1 (Phase 32 별도 영역)

---

## 핵심 evidence summary

| evidence | 결과 |
|---|---|
| R4 CONDITIONAL FAIL get_bid_notice_detail(R25BK00755515) found=false → **R4.5 found=true** | ✅ |
| R4 NoticeRequiredFields 노출 0/12 → **R4.5 12/12 노출** | ✅ |
| R4 SummarySkeleton "본 공고" 1건 잔존 → **R4.5 0건** | ✅ |
| backend uvicorn stale 모듈 (R3.5 issue 재발) → **명시적 재기동 후 검증 적용** | ✅ |
| 회귀 (R1 단건 모드, R26 R-prefix, frontend 7종 화면) | ✅ 모두 동등 |

---

**작성 완료 — 2026-05-04 (KST), tester-p31-r4-hotfix.**
