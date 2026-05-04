# ROUND 4.5 HOTFIX REPORT (Phase 31)

> **라운드**: Phase 31 Round 4.5 — R4 CONDITIONAL FAIL 회복 hotfix.
> **fixer**: fixer-p31-r4.5
> **작성 시각**: 2026-05-04 (KST)
> **검증 commits**: `e429e36` (backend) + `8119787` (frontend) — 2 atomic commits.
> **입력**: ROUND-4-REPORT.md §7 옵션 A, ROUND-4-TEST.md §3.3·§5.2 CONDITIONAL FAIL evidence, POC-G2B.md #4 (R25BK00755515 inqryDiv=2 PASS).

---

## 1. 회귀 정의 (R4 CONDITIONAL FAIL → R4.5 회복 대상)

| 결함 | R4 영역 | R4 결과 | R4.5 회복 |
|------|---------|---------|-----------|
| **F25 backend 의존** | `app/tools/bid.py` `get_bid_notice_detail` 폴백 chain | CONDITIONAL FAIL — frontend 코드 정합 ✅, found=false 차단 → NoticeRequiredFields 노출 0/12 ❌ | Commit 1 (`e429e36`) — inqryDiv=2 + 5종 단일조회 endpoint 병렬 폴백 추가 |
| **F28 SummarySkeleton minor** | `frontend/src/app/bids/trace/page.tsx:537` | CONDITIONAL PASS — "본 공고" 1건 잔존 | Commit 2 (`8119787`) — "입찰공고" 1라인 정정 |

R4 자체 코드 결함은 0건 (raw evidence: ROUND-4-TEST §1·§2). R4.5는 **R4가 의도한 사용자 노출 효과를 차단하던 기존 backend 폴백 chain 결함**(R3.5에서 식별된 동일 issue 재발)을 회복.

---

## 2. Commit 1 — backend hotfix (`e429e36`)

### 2.1 변경 사항

- **파일**: `app/tools/bid.py`
- **라인**: +82 / -3 (insertions/deletions, .gitstat 기준)
- **신규 헬퍼**: `_get_detail_by_bid_no(bid_notice_no, bid_ord, norm_ord) -> dict | None`
  - inqryDiv=2 + bidNtceNo 직접 + 5종 단일조회 endpoint(`Cnstwk`/`Servc`/`Thng`/`Frgcpt`/`Etc`) 병렬 호출 (`asyncio.gather`)
  - 1순위: `bidNtceNo + bidNtceOrd` 정합 매칭 → `lookup_mode="inqryDiv=2+bidNtceNo+ord_match"`
  - 2순위: `bidNtceNo` 일치하나 ord 다른 차수 first match → `lookup_mode="inqryDiv=2+bidNtceNo+ord_diff"` + `ord_mismatch_warning`
  - detail 형식 정규화 (found/biz_div/endpoint/lookup_mode/summary/raw) — frontend 호출 흐름 호환 보전
  - R1 헬퍼 `_search_by_bid_notice_no` 호출 구조 동일 (PoC #4 패턴 재사용), 단 list 반환 vs dict 반환 차이만 분리
- **`get_bid_notice_detail` 폴백 chain 4단계로 확장**:
  1. inqryDiv=3 + bidNtceNo + bidNtceOrd (단건 직접) — 기존 보전
  2. inqryDiv=1 + bidNtceNo (차수 무관) → 클라이언트측 차수 매칭 — 기존 보전
  3. **inqryDiv=2 + bidNtceNo (5종 fan-out)** — P31-R4.5 신규
  4. `search_bid_notices(bid_notice_no=...)` (progressive 30/90일 + 추정 연도) — 기존 보전 (3차 → 4차로 번호만 이동)
- **cache prefix bump**: `bid_detail` → `bid_detail_v33` (R4.5 변경 명시)
- **note 메시지 업데이트**: found=false 시 "inqryDiv=2 5종 fan-out" 명시.

### 2.2 signature 변경 0 (caller 정합 보전)

```
async def get_bid_notice_detail(bid_notice_no: str, bid_ord: str = "00") -> dict
```
인자/반환 형식 모두 무변경 — frontend `bids/trace/page.tsx:208` `getBidNoticeDetail(bidNo, bidOrd)` server action 호출 흐름 영향 0.

### 2.3 R1 헬퍼 격리 보전 (회귀 0)

`_search_by_bid_notice_no`(R1, list 반환)는 무변경. 신규 `_get_detail_by_bid_no`(R4.5, dict 반환)는 별도 함수로 격리. PoC #4 패턴(inqryDiv=2 + 5종 fan-out + ord 매칭)은 동일하나 `BidNoticeSearchResult` schema 변환 의존성 없음.

---

## 3. Commit 2 — frontend SummarySkeleton 정정 (`8119787`)

- **파일**: `frontend/src/app/bids/trace/page.tsx`
- **라인**: +1 / -1
- **변경**: line 537
  - 변경 전: `요약 로딩 중 — 본 공고 단건 조회 (cache hit 시 0.5초)`
  - 변경 후: `요약 로딩 중 — 입찰공고 단건 조회 (cache hit 시 0.5초)`
- **근거**: ROUND-4-TEST §5.2 — F28 의도 "본 공고 단독 사용 0"에 부합. DOSSIER-LAW §7.1 시행령 제33조 표제어 "입찰공고".

---

## 4. 자체 sanity check (R3+R4 학습 누적 + R4 신규 학습 적용)

| 항목 | 결과 | evidence |
|------|------|----------|
| backend get_bid_notice_detail signature 변경 0 | ✅ | `inspect.signature` 변경 전후 동일: `(bid_notice_no: str, bid_ord: str = '00') -> dict` |
| R1 `_search_by_bid_notice_no` 헬퍼 격리 보전 (회귀 0) | ✅ | 신규 `_get_detail_by_bid_no` 별도 함수 신설, R1 코드 무수정 |
| python import 성공 | ✅ | `from app.tools.bid import get_bid_notice_detail, _get_detail_by_bid_no` OK |
| **frontend 호출 흐름 응답 도착 여부 직접 호출 검증** (R4 신규 학습) | ✅ | `get_bid_notice_detail("R25BK00755515", "000")` → found=true + lookup_mode=`inqryDiv=2+bidNtceNo+ord_match` + endpoint=`/BidPublicInfoService/getBidPblancListInfoServc` + **F25 raw 14/14 필드 도착** (bidPrtcptLmtYn / indstrytyLmtYn / sucsfbidMthdNm / cntrctCnclsMthdNm / bidMethdNm / bidBeginDt / bidClseDt / opengDt / opengPlce / bidPrtcptFee / cmmnSpldmdMethdNm / ntceInsttOfclNm / crdtrNm / purchsObjPrdctList) |
| 회귀 점검 — R26BK01501298 | ✅ | found=true, lookup_mode=`inqryDiv=2+bidNtceNo+ord_match` (R-prefix 형식 동일 패턴 hit) |
| 회귀 점검 — search_bid_notices 단건 모드 (R1) | ✅ | `search_bid_notices(bid_notice_no="R25BK00755515", limit=3)` → returned_count=1, lookup_mode=`inqryDiv=2+bidNtceNo` (R1 영향 0) |
| TypeScript 0 에러 (frontend SummarySkeleton 변경 후) | ✅ | `cd frontend && npx tsc --noEmit` EXIT=0 |
| uvicorn 재기동 절차 (R3.5 학습) — backend 변경 후 의무 | ⚠ 권고 명시 | tester-p31-r4-hotfix가 검증 시작 전 backend 재기동 필요 |

---

## 5. 핸드오프 메시지 (tester-p31-r4-hotfix 앞)

### 5.1 검증 대상 (2 commits 누적)

- Commit 1 `e429e36` — backend `app/tools/bid.py` (+82/-3)
- Commit 2 `8119787` — frontend `bids/trace/page.tsx` (+1/-1)
- base 비교: `45f5287` (R4 종료) → 현재 HEAD (`8119787`)

### 5.2 L3 핵심 검증 포인트

- `get_bid_notice_detail("R25BK00755515", "000")` → **found=true + 14 필드 도착 (F25 raw)**
- lookup_mode=`inqryDiv=2+bidNtceNo+ord_match` (PoC #4 evidence 일치, endpoint=Servc)
- `get_bid_notice_detail("R26BK01501298", "000")` → found=true (R-prefix 회복 보전)
- 8자리 형식 회귀 점검 — 사용자 임의 case (예: 20240315678) 시도 시 폴백 chain 단계별 거동 확인

### 5.3 L5 시각 검증 포인트

- `/bids/trace?no=R25BK00755515&ord=000` Stage 2 NoticeRequiredFields 헤더 "입찰공고 필수항목 (시행령 제36조)" hit ≥1 + 12 항목 라벨(입찰참가자격/낙찰자 결정방법/입찰서 제출방법/입찰 개시·마감/개찰 일시/개찰 장소/입찰참가수수료/입찰보증금/현장설명/공동계약/계약담당공무원/목적물 명세) 노출 검증.
- `/bids/trace?no=R26BK01501298&ord=000` SummarySkeleton fallback 영역 "입찰공고 단건 조회" 텍스트 hit + "본 공고 단건 조회" hit 0건 검증.

### 5.4 회귀 점검 영역

- search_bid_notices 단건 모드 (R1) 영향 0 — `_search_by_bid_notice_no` 헬퍼 무변경 + R1 returned_count 동일.
- 다른 trace stage(StagePreSpec/StageAwardAndNts) 영향 0 — Commit 2는 SummarySkeleton 1라인 단독 정정.
- frontend 영향 받지 않는 화면 7종(/, /bids, /vendors, /agencies, /lookup, /external/kwater, /analytics) HTTP 200 보전 의무.

### 5.5 backend 재기동 절차 명시 (R3.5 학습)

```
# 기존 uvicorn 프로세스 종료 후 재시작
# (Windows PowerShell)
Get-Process | Where-Object { $_.ProcessName -eq 'python' } | Stop-Process -Force
cd C:\Users\User\GovProcu
uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
```

`bid_detail_v33` 캐시 prefix bump로 stale 캐시 진입 0 — 그러나 Python 모듈 hot-reload 미작동 환경에선 명시적 재기동 필수.

---

## 6. 다음 단계 (lead 결정 의무)

- R4.5 hotfix 자체 PASS 여부 → tester-p31-r4-hotfix L1~L6 회귀 검증 후 lead 판단.
- PASS 시 R5 종합 회귀(L1~L6 누적 + 14 화면) 진입 사전 조건 충족.
- F22 frontend 자동완성 (R5 또는 별도 phase) + K1 (Phase 32) 별도 영역.

---

**작성 완료 — 2026-05-04 (KST)**
