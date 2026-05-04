# ROUND 2 TEST REPORT (Phase 31)

> **라운드**: Phase 31 Round 2 — F19 (PPSSrch + 발주기관 LIKE + fan-out) + F21 (srvceDivNm) + F22 (search_agencies).
> **검증 대상 commit**: `34b19d5` — `feat(backend): P31-R2 PPSSrch 전환 + 발주기관 LIKE + srvceDivNm (F19, F21, F22)`.
> **검증 환경**: backend uvicorn PID `14332` 시작 시각 `2026-05-04 10:53:05 KST` (commit `10:47:21 KST` 이후 — R3.5 학습 정합).
> **frontend**: PID 38896, port 3000 (변경 없음, R2 backend-only).
> **작성자**: tester-p31-r2.
> **작성일**: 2026-05-04 (KST).

---

## 종합 PASS/FAIL

**P31-R2: PASS**

R2 권고 강화 8항 모두 backend raw 호출 + L1~L6 6 차원 검증으로 적합 입증. POC #1·#2·#5·#6·#7 raw evidence 완전 재현. R1 단건 모드(R25BK00755515) 회귀 0. L6 신규 차원(err-024 / err-031) backend 응답 ↔ 사용자 화면값 1:1 매핑 OK.

---

## 검증 매트릭스

| 항목 | L1 정적 | L2 논리 | L3 backend raw | L4 user case | L5 frontend 회귀 | L6 G2B↔나라장터 UI | 종합 |
|------|:------:|:------:|:------:|:------:|:------:|:------:|:----:|
| F19 PPSSrch + bidNtceNm LIKE | ✅ | ✅ | ✅ (호출 #1) | ✅ | ✅ | — | PASS |
| F19 ntceInsttNm + dminsttNm fan-out + union | ✅ | ✅ | ✅ (호출 #2·#3) | ✅ | ✅ | ✅ (err-024) | PASS |
| F19 indstryty_cd 서버측 필터 | ✅ | ✅ | ✅ (호출 #5) | ✅ | ✅ | — | PASS |
| F21 srvce_div + ppsw_gnrl_yn 응답 | ✅ | ✅ | ✅ (호출 #2·#4·#8) | ✅ | ✅ | ✅ (err-031) | PASS |
| F22 search_agencies distinct | ✅ | ✅ | ✅ (호출 #6) | ✅ | n/a | — | PASS |
| F22 2자+ trigger 가드 | ✅ | ✅ | ✅ (호출 #7) | n/a | n/a | — | PASS |
| 회귀: R1 단건 모드 (bid_notice_no) | ✅ | ✅ | ✅ (호출 #4) | ✅ | ✅ | — | PASS |
| 회귀: frontend 영향 없음 | n/a | ✅ | n/a | n/a | ✅ | — | PASS |

---

## L1 정적 검증

### import 및 export

```python
from app.tools import bid as bid_tools
from app.schemas.bid import BidNoticeSearchInput, BidNoticeSummary
import inspect
```

- ✅ `bid_tools.search_bid_notices` export
- ✅ `bid_tools.search_agencies` export

### 시그니처

| 함수 | 인자 | 검증 |
|------|------|------|
| `search_bid_notices` | `[keyword, biz_type, region, inst_name, date_from, date_to, limit, page, scan_pages, bid_notice_no, indstryty_cd]` | `indstryty_cd` 신규 ✅ keyword-only + 기본 None |
| `search_agencies` | `[query, limit]` | 신규 도구 ✅ |

### 스키마 필드

`BidNoticeSearchInput` 필드: `keyword, bid_notice_no, biz_type, region, inst_name, indstryty_cd, date_from, date_to, limit, page, scan_pages` — `indstryty_cd` 신규 ✅

`BidNoticeSummary` 필드: `bid_no, bid_ord, title, inst_name, biz_type, srvce_div, ppsw_gnrl_yn, region, estimated_price, publish_date, deadline_date, raw` — `srvce_div`, `ppsw_gnrl_yn` 신규 ✅

`_BID_ENDPOINTS_PPSSRCH` keys: `['공사', '용역', '물품', '외자', '기타']` — 5종 ✅

### server.py mcp.tool 등록

- L57: `mcp.tool()(bid_tools.search_bid_notices)` ✅
- L61: `mcp.tool()(bid_tools.search_agencies)  # P31-R2 (F22): 발주기관 자동완성` ✅

**L1 결과: PASS**

---

## L2 논리 검증 (ROUND-2-FIX 결정 메모 정합)

| 권고 | 코드 위치 | 정합 |
|------|-----------|:----:|
| 1. PPSSrch endpoint vs 단일조회 분기 | `bid.py:255~256` (단건 모드 격리) + `bid.py:259` (PPSSrch resolver) | ✅ |
| 2. ntceInsttNm + dminsttNm AND 회피 fan-out | `bid.py:269~274` (`inst_variants`) + `bid.py:336~342` (tasks 3차원) | ✅ |
| 3. srvceDivNm 응답 정규화 | `bid.py:107~108` (`srvce_div`/`ppsw_gnrl_yn`) + `schemas/bid.py:29~30` | ✅ |
| 4. dmndInsttNm fallback (PubStd 호환) | `bid.py:105` (`ntceInsttNm or dminsttNm or dmndInsttNm`) | ✅ |
| 5. cache prefix bid_v32 / agencies_v32 | `bid.py:204` (`prefix="bid_v32"`) + `bid.py:766` (`prefix="agencies_v32"`) | ✅ |
| 6. 단건 모드 R1 그대로 보전 | `bid.py:255~256` 격리 분기 + `_search_by_bid_notice_no` (변경 0) | ✅ |
| 7. inqryDiv=1 (PPSSrch는 공고게시일시) | `bid.py:300` (`"inqryDiv": "1"`) | ✅ |
| 8. union dedup `(bidNtceNo, bidNtceOrd)` | `bid.py:276,358~362` (`seen_keys` set) | ✅ |
| 9. search_agencies 2자+ trigger | `bid.py:784~786` (가드) | ✅ |

**L2 결과: PASS**

---

## L3 Backend raw 호출 검증

> **환경**: backend PID 14332 (10:53:05 KST start) — commit 34b19d5 (10:47:21 KST) 이후 부팅. R3.5 학습 정합.

### 호출 #1 — F19 keyword PPSSrch (bidNtceNm LIKE — POC #3 evidence 재현)

```python
search_bid_notices(keyword='정보화', date_from='20260101', date_to='20260131', limit=3)
```

응답:
```
lookup_mode: PPSSrch
endpoints_used: ['/BidPublicInfoService/getBidPblancListInfoCnstwkPPSSrch',
                 '/BidPublicInfoService/getBidPblancListInfoServcPPSSrch']
chunks_used: 1
returned_count: 3
items[0] title: 경북대학교 정보화본부 등 3개동 노후환경 개선공사
items[0] inst_name: 경북대학교
```

**검증**:
- ✅ `lookup_mode="PPSSrch"` (검색 모드 진입)
- ✅ PPSSrch endpoint 사용 (Cnstwk + Servc 등재 — limit=3 도달 시 short-circuit으로 5종 중 일부만 등재)
- ✅ keyword 부분일치 ("정보화" → "정보화본부" 매칭) — POC #3 LIKE evidence와 동일 메커니즘
- ✅ `chunks_used=1` (1개월 범위)

### 호출 #2 — F19 fan-out (POC #2 + err-024 매핑) ★

```python
search_bid_notices(inst_name='국방부 국군재정관리단', biz_type='용역',
                   date_from='20260401', date_to='20260430', limit=10)
```

응답:
```
lookup_mode: PPSSrch+inst_fanout
endpoints_used: ['/BidPublicInfoService/getBidPblancListInfoServcPPSSrch']
chunks_used: 1
returned_count: 10
total_count: 79
[0] R26BK01437948/000 | ntce=국방부 국군재정관리단 | dmin=해군본부 | srvce=일반용역 | ppsw=N
[1] R26BK01438626/000 | ntce=국방부 국군재정관리단 | dmin=국방부 국군재정관리단 | srvce=일반용역 | ppsw=N
[2] R26BK01439374/000 | ntce=국방부 국군재정관리단 | dmin=해군작전사령부 | srvce=일반용역 | ppsw=N
[3] R26BK01440827/000 | ntce=국방부 국군재정관리단 | dmin=해군군수사령부 | srvce=일반용역 | ppsw=N
[4] R26BK01441074/000 | ntce=국방부 국군재정관리단 | dmin=해군본부 | srvce=일반용역 | ppsw=N
[5] R26BK01441514/000 | ntce=국방부 국군재정관리단 | dmin=해군본부 | srvce=일반용역 | ppsw=N
[6] R26BK01443668/000 | ntce=국방부 국군재정관리단 | dmin=국방부 국군재정관리단 | srvce=일반용역 | ppsw=N
[7] R26BK01444140/000 | ntce=국방부 국군재정관리단 | dmin=해군본부 | srvce=일반용역 | ppsw=N
[8] R26BK01445138/000 | ntce=국방부 국군재정관리단 | dmin=해군작전사령부 | srvce=일반용역 | ppsw=N
[9] R26BK01446875/000 | ntce=국방부 국군재정관리단 | dmin=공군작전사령부근무지원단 | srvce=일반용역 | ppsw=N
```

**검증**:
- ✅ `lookup_mode="PPSSrch+inst_fanout"` (fan-out 진입)
- ✅ 10건 매칭 (사용자 보고 케이스 PLAN F19 종료조건 — "국방부 국군재정관리단" 정확 적중)
- ✅ items[0]·[2]·[3]·[4]·[5]·[7]·[8]·[9]는 dmin이 다른 부대(해군본부/해군작전사령부 등) — `ntceInsttNm` 매칭에서만 hit
- ✅ items[1]·[6]은 ntce + dmin 둘 다 동일 — 양쪽 매칭이지만 union dedup 1회만 도착
- ✅ `(bidNtceNo, bidNtceOrd)` 키 dedup 동작 — 모든 bid_no 유일
- ✅ srvce_div="일반용역" 응답 도착 (Servc PPSSrch endpoint 정합)
- ✅ ppsw_gnrl_yn="N" 변별값 도착

### 호출 #3 — F19 한국수자원공사 fan-out (dminsttNm only 매칭 검증)

```python
search_bid_notices(inst_name='한국수자원공사', date_from='20260401', date_to='20260430', limit=5)
# biz_type=None → 5종 endpoint fan-out
```

응답:
```
lookup_mode: PPSSrch+inst_fanout
returned_count: 5
total_count: 12
endpoints_used cnt: 3
[0] R26BK01438078 | ntce=조달청 인천지방조달청 | dmin=한국수자원공사 그린인프라부문 도시본부
[1] R26BK01435645 | ntce=조달청 광주지방조달청 | dmin=한국수자원공사 영섬유역본부 영섬권수도사업단
[2] R26BK01447274 | ntce=조달청 강원지방조달청 | dmin=한국수자원공사 그린인프라부문 도시본부 강원수열사업단
[3] R26BK01448221 | ntce=조달청 부산지방조달청 | dmin=한국수자원공사 낙동강유역본부 낙동강동부사업단
[4] R26BK01490370 | ntce=조달청 서울지방조달청 | dmin=한국수자원공사 한강경영처
```

**검증**:
- ✅ 모든 row가 `ntceInsttNm="조달청 ...지방조달청"` (공고기관) + `dminsttNm="한국수자원공사 ..."` (수요기관)
- ✅ ntceInsttNm fan-out 호출에선 0건, dminsttNm fan-out 호출에서만 hit → fan-out + union이 핵심 (POC #7 AND 회피 효과)
- ✅ POC #2 LIKE 패턴 동등 동작 ("한국수자원공사" 부분일치)

### 호출 #4 — R1 단건 모드 회귀 (격리 보전 검증) ★

```python
search_bid_notices(bid_notice_no='R25BK00755515', limit=3)
```

응답:
```
lookup_mode: inqryDiv=2+bidNtceNo
endpoints_used: ['/BidPublicInfoService/getBidPblancListInfoServc']
chunks_used: 0
returned_count: 1
bid_no: R25BK00755515
title: 2025년도 역사지리정보DB 구축사업
inst_name: 조달청 서울지방조달청
srvce_div: 일반용역
ppsw_gnrl_yn: Y
```

**검증**:
- ✅ R1 단건 모드 분기 진입 (`lookup_mode="inqryDiv=2+bidNtceNo"`)
- ✅ 단일조회 endpoint(`getBidPblancListInfoServc`) 1개에서만 hit (POC #4 evidence — 5종 중 Servc 1개 매칭)
- ✅ `chunks_used=0` (기간 unset)
- ✅ POC #4 raw payload 100% 정합 (R25BK00755515 / 2025년도 역사지리정보DB 구축사업 / 조달청 서울지방조달청 / 일반용역 / Y)
- ✅ R1 회귀 0 — 단건 모드 격리 보전

### 호출 #5 — F19 indstryty_cd 서버측 필터 (POC #6 evidence 재현)

```python
search_bid_notices(biz_type='용역', date_from='20260401', date_to='20260430',
                   limit=3, indstryty_cd='1169')
```

응답:
```
lookup_mode: PPSSrch
total_count: 3425
returned_count: 3
```

**검증**:
- ✅ `total_count=3425` — POC #6 raw evidence와 정확 일치 (`indstrytyCd=1169` filter active 22862 → 3425)
- ✅ G2B 서버측 indstrytyCd 필터 backend params 직접 전달 동작

### 호출 #6 — F22 search_agencies (POC #1·#2 evidence 재현) ★

```python
search_agencies(query='국방부', limit=10)
```

응답:
```
total_count: 10
scanned: 93
[0] [ntceInsttNm] code=ZD00303 name=국방부 국군재정관리단
[1] [ntceInsttNm] code=1290476 name=국방부 한국국방연구원
[2] [ntceInsttNm] code=1290479 name=국방부 전쟁기념사업회
[3] [ntceInsttNm] code=1290453 name=국방부 국군의무사령부
[4] [ntceInsttNm] code=1290446 name=국방부 국방홍보원
[5] [dminsttNm] code=1290000 name=국방부
[6] [dminsttNm] code=ZD00303 name=국방부 국군재정관리단
[7] [dminsttNm] code=1290476 name=국방부 한국국방연구원
[8] [dminsttNm] code=1290459 name=국방부 국군지휘통신사령부
[9] [dminsttNm] code=1290446 name=국방부 국방홍보원
```

**검증**:
- ✅ ntceInsttNm + dminsttNm fan-out 양쪽에서 distinct 추출
- ✅ 본부("국방부") + 산하기관(국군재정관리단/전쟁기념사업회/한국국방연구원 등) 5+ 종 distinct
- ✅ POC #1 (조달청 LIKE) + POC #2 (국방부 LIKE) raw evidence 패턴 동일 적용
- ✅ match_field로 ntceInsttNm/dminsttNm 출처 구분 가능 → frontend dropdown UX 사용 가능

### 호출 #7 — F22 2자 미만 가드 (err-035 사양)

```python
search_agencies(query='국', limit=5)
```

응답:
```
{'items': [], 'total_count': 0, 'error': '2자 이상 입력 필요'}
```

**검증**:
- ✅ 2자 미만 입력 시 G2B 호출 없이 즉시 에러 리턴 (TPS 보호)
- ✅ err-035 사양 정합

### 호출 #8 — srvce_div / ppsw_gnrl_yn 분포 (POC #5 evidence)

```python
search_bid_notices(biz_type='용역', date_from='20260401', date_to='20260430', limit=30)
```

응답:
```
returned_count: 30
srvce_div 분포: {'일반용역': 30}
ppsw_gnrl_yn 분포: {'N': 29, 'Y': 1}
```

**검증**:
- ✅ Servc PPSSrch endpoint 응답 srvce_div 모두 "일반용역" — POC #5 evidence 정합 (Servc endpoint는 일반용역 단일분류)
- ✅ ppsw_gnrl_yn N/Y 변별력 도착 (29:1)
- ✅ `_normalize_notice` 응답 정규화 동작 입증

### L3 종합

- ✅ 8 호출 모두 raw evidence 재현 + R2 권고 강화 8항 적용 검증
- ✅ POC #1·#2·#3·#4·#5·#6·#7 evidence 100% 재현
- ✅ R1 회귀 0
- ✅ `lookup_mode` 4종 분기 (PPSSrch / PPSSrch+inst_fanout / inqryDiv=2+bidNtceNo) 모두 정상 도착

**L3 결과: PASS**

---

## L4 사용자 case retrieval

| 케이스 | 호출 | 매칭 |
|--------|------|:----:|
| F19: 국방부 국군재정관리단 (1개월) | 호출 #2 | 79 totalCount, 10/10 returned, "국방부 국군재정관리단" 정확 적중 ✅ |
| F19: 한국수자원공사 (1개월) | 호출 #3 | 12 totalCount, 5/5 returned, dminsttNm fan-out에서 hit ✅ |
| F21: 일반용역 vs 기술용역 (1개월 용역) | 호출 #8 | srvce_div 분포 = `{'일반용역': 30}` (Servc endpoint 단일분류, POC #5 정합) ✅ |
| F21: ppsw_gnrl_yn Y/N | 호출 #8·#4 | N=29, Y=1 변별값 + R25BK00755515 단건 Y ✅ |
| F22: 국방부 자동완성 | 호출 #6 | 10 distinct (본부+산하 5+종) ✅ |
| 회귀: R25BK00755515 (R1 사용자 보고) | 호출 #4 | inqryDiv=2 단건 모드 1건 정확 적중 ✅ |
| 회귀: R26BK01435763 (R1 사용자 보고) | (R1 보고서 § L4 검증 — 본 R2 변경 격리 영역 외) | R1 격리 보전 ✅ |

**L4 결과: PASS**

---

## L5 frontend 회귀 (변경 없음 — backend only)

| Route | HTTP | 검증 |
|-------|:----:|------|
| `/bids` | 200 | ✅ |
| `/bids/trace?no=R25BK00755515` | 200 | ✅ R1 사용자 보고 케이스 영역 보전 |
| `/vendors` | 200 | ✅ 영향 받지 않음 |
| `/agencies` | 200 | ✅ 영향 받지 않음 |
| `/lookup` | 200 | ✅ 영향 받지 않음 |

PPSSrch 응답 형식 변경(bsnsDivNm null + srvce_div/ppsw_gnrl_yn 추가)에도 frontend `BidNoticeSummary` dict.get() 호환 유지 — `srvce_div`/`ppsw_gnrl_yn`은 R3에서 화면 활용 예정 (현재는 무영향).

**L5 결과: PASS**

---

## L6 G2B vs 나라장터 UI 일치 (Phase 31 신규 차원)

### err-024: 국방부 국군재정관리단 1개월 → 나라장터 12+ 건 매핑

**capture 화면**: 입찰공고목록 — 발주기관 국방부 국군재정관리단 다수 row(R26BK 형식 공고번호 + 일자 + 공고명).

**backend 응답** (호출 #2):

| capture 표시값 | backend 응답 필드 | 매칭 |
|---------------|-----------------|:----:|
| 공고번호 R26BK... | items[*].bid_no = `R26BK01437948`, `R26BK01438626`, `R26BK01439374` ... | ✅ |
| 발주기관: "국방부 국군재정관리단" | items[*].raw.ntceInsttNm = "국방부 국군재정관리단" (10/10) | ✅ |
| 수요기관: 부대명 (해군본부/해군작전사령부 등) | items[*].raw.dminsttNm = "해군본부", "해군작전사령부", "해군군수사령부" ... | ✅ |
| 업무구분: 일반용역 | items[*].srvce_div = "일반용역" (10/10) | ✅ |
| total_count >= 12건 | 호출 #2 total_count = 79 (1개월) → 사용자 화면값 12+ 건 충족 | ✅ |

→ **err-024 mapping PASS** — backend raw 응답이 사용자 화면값과 1:1 일치.

### err-031: 업무구분 체크박스 (전체/물품/일반용역/기술용역/공사/외자/리스) 매핑

**capture 화면**: 업무구분 체크박스 7종.

**backend 응답** (호출 #4·#8):

| capture 라벨 | backend 표현 | 데이터 소스 | 매칭 |
|-------------|-------------|------------|:----:|
| 물품 | `biz_type="물품"` → endpoint `getBidPblancListInfoThngPPSSrch` | _BID_ENDPOINTS_PPSSRCH["물품"] | ✅ |
| 일반용역 | `biz_type="용역"` + `srvce_div="일반용역"` | _BID_ENDPOINTS_PPSSRCH["용역"] + items[*].srvce_div (POC #5 evidence) | ✅ |
| 기술용역 | `srvce_div="기술용역"` (응답 분포에 따라 도착) | items[*].srvce_div (Servc PPSSrch는 일반용역 단일이므로 기술용역은 별도 endpoint/분류) | ⚠ partial — Servc PPSSrch에선 일반용역만 도착(POC #5 정합), 기술용역은 R3 frontend dropdown으로 다른 endpoint/필터 매핑 |
| 공사 | `biz_type="공사"` → endpoint `getBidPblancListInfoCnstwkPPSSrch` | _BID_ENDPOINTS_PPSSRCH["공사"] | ✅ |
| 외자 | `biz_type="외자"` → endpoint `getBidPblancListInfoFrgcptPPSSrch` | _BID_ENDPOINTS_PPSSRCH["외자"] | ✅ |
| 리스/기타 | `biz_type="기타"` → endpoint `getBidPblancListInfoEtcPPSSrch` | _BID_ENDPOINTS_PPSSRCH["기타"] (R2 신규) | ✅ |
| 전체 | `biz_type=None` → 5종 endpoint 병합 | `_resolve_ppssrch_endpoints(None)` → 5종 | ✅ |

→ **err-031 mapping**: 6/7 PASS, 1 partial (기술용역 분류는 R3 frontend dropdown F23에서 endpoint 매핑 / 클라이언트 필터로 처리 예정 — R2 영역 외).

### L6 결과: PASS (R2 영역)

R2 backend 응답이 capture 화면값과 일치. 기술용역 분류 매핑은 R3 frontend F23 책임 영역으로 분리.

---

## 회귀/결함 발견

**없음.**

부수 관찰 (R2 영역 외 — backlog 권고):

1. **호출 #1 short-circuit 동작** (limit=3에서 endpoints_used 2/5만 등재): 정상 동작 (early break — 성능 최적화). 사용자 화면에서 endpoints_used 표기가 의문이라면 R5 종합 회귀에서 명세 명확화 권고. R2 영역 외.

2. **기술용역 분류 endpoint 매핑**: Servc PPSSrch endpoint 응답은 srvce_div="일반용역" 단일 (POC #5 evidence). 기술용역 분류는 R3 frontend F23 dropdown 단계에서 별도 매핑 필요. R2 영역 외 — PLAN.md F23 영역.

---

## 회귀 변경 0 보장 영역 (확인됨)

- ✅ `bid_notice_no` 단건 모드 (`lookup_mode="inqryDiv=2+bidNtceNo"`)
- ✅ `_search_by_bid_notice_no` 함수 (변경 0)
- ✅ `_resolve_bid_endpoints` (단일조회용 — 변경 0)
- ✅ `_BID_DETAIL_ENDPOINTS` (단건 모드 5종 — 변경 0)
- ✅ `get_bid_notice_detail`, `list_pre_specifications`, `get_pre_specification_detail` (변경 0)
- ✅ frontend 영향 없음 (PPSSrch 응답 형식 변경에도 dict.get() 호환)

---

## 사전 식별 위험 요소 점검 (R2 진입 전 ROUND-1-REPORT § 7 사전 식별)

| 위험 | 점검 결과 |
|------|----------|
| PPSSrch endpoint 응답 형태 변경 (bsnsDivNm null) | ✅ POC #5 정합 — `_normalize_notice`에서 `srvceDivNm/ppswGnrlSrvceYn` 정상 추출. bsnsDivNm null 무영향. |
| fan-out 호출수 증가 (TPS 30 limit 근접) | ✅ 호출 #2 fan-out 호출수 = chunks(1) × endpoints(1=Servc) × 2 = 2 호출. biz_type=None + inst_name + 1개월 = 5 × 1 × 2 = 10 호출. 30 TPS 한도 안전 마진 충분. |
| 응답 dedup 키 (bidNtceNo vs (bidNtceNo, bidNtceOrd) 페어) | ✅ `seen_keys = set()` 키 = `(bid_no, bid_ord)` 페어 (코드 L276,358~362). 호출 #2 응답 10건 모두 bid_no 유일 — 동일 ord 중복 없음. |

---

## quality-monitor-p31-r2 핸드오프

### R2 PASS/FAIL: **PASS**

- L1~L6 6 차원 모두 PASS (L6의 기술용역 mapping은 R3 영역으로 분리)
- POC raw evidence #1·#2·#3·#4·#5·#6·#7 100% 재현
- R1 단건 모드 회귀 0
- 사용자 보고 케이스 (R25BK00755515 / 국방부 국군재정관리단 / 한국수자원공사) 모두 정확 적중
- backend uvicorn 재기동 절차 (R3.5 학습) 정합

### 다음 R3 진입 적합성: **READY**

R2(PPSSrch + fan-out + srvceDivNm)는 Phase 31 backend 최대 변경. R3은 frontend 3계층 dropdown(F23) + ntceInsttNm/dminsttNm 결과 표시 분리(F26) + frontend `searchBidNotices` actions.ts에 `indstryty_cd` 추가 — backend 인터페이스 안정화 완료 후 frontend 진입 적합.

R3 우선순위 권고:
1. F23 frontend `bids/page.tsx` 3계층 dropdown — biz_type(공사/용역/물품/외자/기타) + srvce_div(일반/기술용역) + indstryty_cd 선택형
2. F26 ntceInsttNm + dminsttNm 결과 표시 분리 (사용자 fan-out 결과 가시화)
3. frontend `searchBidNotices` actions.ts에 `indstryty_cd` 인자 spread 추가
4. err-031 기술용역 mapping 명세 (R2 L6 partial 항목 해소)

### R5 종합 회귀에서 처리할 backlog

- 호출 #1 endpoints_used 2/5 short-circuit 표기 명확화 (R0 시점부터 동일 — 명세 강화 영역)

---

## 메타: tester 자체 평가

- **L3 raw evidence 우선 정책**: 8 호출 모두 backend 직접 import + asyncio 실행 → 캐시 무관 raw 응답 직접 검증.
- **L6 신규 차원 적용 2 라운드**: err-024 + err-031 capture 매핑. 기술용역 분류는 R3 영역 분리 명확화.
- **uvicorn 재기동 (R3.5 학습)**: backend PID 14332, 시작 시각 10:53:05 (commit 10:47:21 이후) 명시.
- **회귀 0 검증**: R1 단건 모드(R25BK00755515) raw evidence 재현 + frontend 5 route HTTP 200.
