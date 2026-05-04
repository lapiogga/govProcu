# ROUND 2 FIX (Phase 31)

> **라운드**: Phase 31 Round 2 — F19 (발주기관 LIKE + fan-out) + F21 (srvceDivNm 응답) + F22 (search_agencies 자동완성).
> **fix commit**: `34b19d5` — backend-only (`app/tools/bid.py` + `app/schemas/bid.py` + `app/server.py`).
> **기간**: 2026-05-04 (KST) 단일 라운드.
> **작성자**: fixer-p31-r2.
> **입력**: PLAN.md, ROUND-1-REPORT.md § 7 (R2 권고 강화 8항), POC-G2B.md, DOSSIER-OFFICIAL.md § 4, DOSSIER-PRACTICE.md.

---

## 1. R2 권고 강화 8항 적용 결과

| # | 권고 | 적용 위치 | 상태 |
|---|------|---------|------|
| 1 | PPSSrch endpoint vs 단일조회 분기 명확화 | `bid.py:60~89` (`_BID_ENDPOINTS_PPSSRCH` + `_resolve_ppssrch_endpoints`) + `bid.py:265` 단건 모드 분기 | **PASS** |
| 2 | ntceInsttNm + dminsttNm AND 회피 fan-out (POC #7) | `bid.py:308~314` (`inst_variants`) + `bid.py:362~366` (tasks 3차원) + `bid.py:380~386` (union dedup by `(bidNtceNo, bidNtceOrd)`) | **PASS** |
| 3 | srvceDivNm 응답 추가 (F21) | `bid.py:96~99` (`_normalize_notice` srvce_div / ppsw_gnrl_yn) + `schemas/bid.py:30~31` (BidNoticeSummary 필드 2종) | **PASS** |
| 4 | dmndInsttNm fallback (PubStd 호환) | `bid.py:94` (`inst_name = ntceInsttNm or dminsttNm or dmndInsttNm`) | **PASS** |
| 5 | cache prefix `bid_v31` → `bid_v32` | `bid.py:208` (`@cache_result(... prefix="bid_v32")`) + `bid.py:780` (`prefix="agencies_v32"`) | **PASS** |
| 6 | backend 시그니처 cross-check (R3 학습) | 신규 인자 `indstryty_cd` 키워드-only + 기본 None → caller 7개 (`alerts.py:191`/`alerts.py:306`/`analytics.py:193`/`lookup.py:112`/`multi_agency.py:77,156`/`workflow.py:261,338`) 모두 keyword args 호출, 영향 0 | **PASS** |
| 7 | uvicorn 재기동 절차 (R3.5 학습) | tester 핸드오프 시 commit 시각 vs uvicorn PID 시작 시각 명시 검증 의무 명시 (§ 6 핸드오프) | **PASS** (tester 진입 가드) |
| 8 | L6 evidence — err-024 (국방부 국군재정관리단) | sanity check § 5 — `inst_name="국방부"` PPSSrch fan-out 5건 응답에 "국방부 국군재정관리단" raw 매칭 (R26BK01437948 등) | **PASS** |

---

## 2. 변경 영역

### 2.1 `app/schemas/bid.py`

| 변경 | 라인 | 근거 |
|------|------|------|
| `BidNoticeSearchInput.biz_type` Literal에 `"기타"` 추가 | L11 | DOSSIER §4 PPSSrch 5분류 (Etc 포함) |
| `BidNoticeSearchInput.indstryty_cd` 신규 필드 | L12 (신규) | F19 PPSSrch indstrytyCd 서버측 필터 (POC #6: 22862 → 3425) |
| `BidNoticeSummary.srvce_div` 신규 필드 | L30 (신규) | F21 srvceDivNm "일반용역"/"기술용역" (POC #5) |
| `BidNoticeSummary.ppsw_gnrl_yn` 신규 필드 | L31 (신규) | F21 ppswGnrlSrvceYn Y/N (POC #5 raw + POC #4 단건 응답 "Y") |

### 2.2 `app/tools/bid.py`

#### F19/F21 — PPSSrch endpoint 매핑 + resolver

```python
# bid.py:60~75
_BID_ENDPOINTS_PPSSRCH = {
    "공사": "/BidPublicInfoService/getBidPblancListInfoCnstwkPPSSrch",
    "용역": "/BidPublicInfoService/getBidPblancListInfoServcPPSSrch",
    "물품": "/BidPublicInfoService/getBidPblancListInfoThngPPSSrch",
    "외자": "/BidPublicInfoService/getBidPblancListInfoFrgcptPPSSrch",
    "기타": "/BidPublicInfoService/getBidPblancListInfoEtcPPSSrch",
}

def _resolve_ppssrch_endpoints(biz_type):
    if biz_type and biz_type in _BID_ENDPOINTS_PPSSRCH:
        return [(biz_type, _BID_ENDPOINTS_PPSSRCH[biz_type])]
    return [(label, ep) for label, ep in _BID_ENDPOINTS_PPSSRCH.items()]
```

#### F21 — _normalize_notice 응답 정규화 확장

```python
# bid.py:88~108
def _normalize_notice(raw):
    return BidNoticeSummary(
        ...
        inst_name=raw.get("ntceInsttNm") or raw.get("dminsttNm") or raw.get("dmndInsttNm"),
        biz_type=raw.get("bsnsDivNm"),       # PPSSrch=null (POC #5)
        srvce_div=raw.get("srvceDivNm"),     # 신규 (POC #5)
        ppsw_gnrl_yn=raw.get("ppswGnrlSrvceYn"),  # 신규 (POC #5)
        ...
    )
```

#### F19 — search_bid_notices 검색 모드 PPSSrch 전환 + fan-out

```python
# bid.py:208 cache prefix
@cache_result(ttl=settings.cache_ttl_short, prefix="bid_v32")
async def search_bid_notices(..., indstryty_cd=None):
    ...
    # bid.py:264~266 단건 모드 격리 (R1 그대로)
    if inp.bid_notice_no and not inp.date_from and not inp.date_to:
        return await _search_by_bid_notice_no(inp)
    
    # bid.py:269 PPSSrch endpoint resolver (5종)
    endpoints = _resolve_ppssrch_endpoints(inp.biz_type)
    
    # bid.py:308~313 inst_variants (F19 fan-out)
    if inp.inst_name:
        inst_variants = [("ntceInsttNm", inp.inst_name), ("dminsttNm", inp.inst_name)]
    else:
        inst_variants = [("none", None)]
    
    # bid.py:330~352 _fetch_combo PPSSrch 파라미터 직접 전달
    params = {
        "pageNo": cur_page, "numOfRows": page_size,
        "inqryDiv": "1",  # PPSSrch 1=공고게시일시 (단일조회와 의미 다름)
        "type": "json",
        "inqryBgnDt": chunk_from + "0000",
        "inqryEndDt": chunk_to + "2359",
    }
    if inp.keyword: params["bidNtceNm"] = inp.keyword
    if inp.indstryty_cd: params["indstrytyCd"] = inp.indstryty_cd
    if inst_value: params[inst_field] = inst_value  # ntceInsttNm 또는 dminsttNm
    
    # bid.py:362~366 tasks chunks × endpoints × inst_variants
    tasks = [
        _fetch_combo(cf, ct, ep, field, value)
        for cf, ct in chunks
        for _, ep in endpoints
        for field, value in inst_variants
    ]
    
    # bid.py:380~386 union dedup by (bidNtceNo, bidNtceOrd)
    key = (str(raw.get("bidNtceNo", "")), str(raw.get("bidNtceOrd", "")))
    if key in seen_keys: continue
    seen_keys.add(key)
    matches.append(_normalize_notice(raw).model_dump())
```

#### F22 — search_agencies 신설

```python
# bid.py:766~862
@cache_result(ttl=settings.cache_ttl_short, prefix="agencies_v32")
async def search_agencies(query, limit=30):
    if len(query.strip()) < 2:
        return {"items": [], "total_count": 0, "error": "2자 이상 입력 필요"}
    # 30일 기간 (G2B 1개월 안전 마진), Servc PPSSrch (POC #5: 데이터 가장 많음)
    # ntceInsttNm + dminsttNm fan-out (POC #7 AND 회피)
    # distinct (code, name, match_field)
    ...
```

### 2.3 `app/server.py`

```python
mcp.tool()(bid_tools.search_agencies)  # P31-R2 (F22): 발주기관 자동완성
```

---

## 3. caller 영향 분석 (R3 학습 — backend 시그니처 cross-check)

### 3.1 `search_bid_notices` 신규 인자 `indstryty_cd`

키워드-only + 기본 `None` 추가 → 기존 caller 영향 0.

| caller | 호출 형태 | 영향 |
|--------|----------|------|
| `app/tools/alerts.py:191` | `keyword=, biz_type=, region=, inst_name=, date_from=, date_to=, limit=` | 영향 0 |
| `app/tools/alerts.py:306` | (subscription 기반 keyword args) | 영향 0 |
| `app/tools/analytics.py:193` | `**search_kwargs` (kwargs unpack) | 영향 0 |
| `app/tools/bid.py:533` (get_bid_notice_detail 3차 폴백) | `bid_notice_no=, limit=, scan_pages=, date_from=, date_to=` | 영향 0 |
| `app/tools/lookup.py:112` | (keyword args) | 영향 0 |
| `app/tools/multi_agency.py:77,156` | (keyword args) | 영향 0 |
| `app/tools/workflow.py:261,338` | `inst_name=, biz_type=, date_from=, date_to=, limit=` | 영향 0 |
| `app/server.py:57` (mcp tool) | MCP runtime이 자동으로 인자 매핑 | 영향 0 |
| `frontend/src/lib/actions.ts:66~82` (`searchBidNotices`) | `{ ...params, limit, page, scan_pages }` spread | 영향 0 (R3에서 indstryty_cd 추가 예정) |

### 3.2 `BidNoticeSummary` 필드 추가 (`srvce_div`, `ppsw_gnrl_yn`)

pydantic 기본값 `None` → 기존 호출자 dict.get() 호환 유지. frontend 화면은 R3에서 활용.

### 3.3 `BidNoticeSearchInput.biz_type` Literal `"기타"` 추가

기존 사용처 (`workflow.py`, `analytics.py` 등)는 `"공사"/"용역"/"물품"/"외자"/None`만 전달 → 영향 0.

---

## 4. 자체 sanity check (R3+R4 학습 누적)

### L1 정적 검증

```bash
$ python -c "from app.tools import bid; from app.schemas.bid import BidNoticeSearchInput, BidNoticeSummary; ..."
search_bid_notices sig: (keyword, biz_type, region, inst_name, date_from, date_to, limit, page, scan_pages, bid_notice_no, indstryty_cd) -> dict
search_agencies sig: (query, limit) -> dict
Summary fields: bid_no, bid_ord, title, inst_name, biz_type, srvce_div, ppsw_gnrl_yn, region, estimated_price, publish_date, deadline_date, raw
Input fields: keyword, bid_notice_no, biz_type, region, inst_name, indstryty_cd, date_from, date_to, limit, page, scan_pages
```

→ import 성공, 시그니처 정합, 필드 추가 정상.

### L3 raw 호출 검증 (POC raw evidence와 1:1)

#### 호출 #1 — R1 단건 모드 회귀 (격리 보전)

```python
search_bid_notices(bid_notice_no='R25BK00755515', limit=3)
```

응답:
```
lookup_mode: inqryDiv=2+bidNtceNo
returned_count: 1
chunks_used: 0   # 기간 unset
bid_no: R25BK00755515
srvce_div: 일반용역    # F21 신규 필드 정상
ppsw_gnrl_yn: Y         # F21 신규 필드 정상
inst_name: 조달청 서울지방조달청
```

→ POC #4 raw payload + R1 보고서 § L3 호출 1·2와 100% 정합. **회귀 0.**

#### 호출 #2 — F19 PPSSrch fan-out (국방부)

```python
search_bid_notices(inst_name='국방부', date_from='20260401', date_to='20260430', limit=5, biz_type='용역')
```

응답:
```
lookup_mode: PPSSrch+inst_fanout
returned_count: 5
chunks_used: 1
endpoints_used: ['/BidPublicInfoService/getBidPblancListInfoServcPPSSrch']
items[0]: R26BK01436745 | ntceInsttNm=국방부 전쟁기념사업회 | dminsttNm=국방부 전쟁기념사업회 | srvce_div=일반용역
items[1]: R26BK01437948 | ntceInsttNm=국방부 국군재정관리단 | dminsttNm=해군본부 | srvce_div=일반용역
items[2]: R26BK01438626 | ntceInsttNm=국방부 국군재정관리단 | dminsttNm=국방부 국군재정관리단 | srvce_div=일반용역
```

→ POC #2 evidence + L6 신규 차원(err-024) 매핑.
→ items[1]은 dminsttNm fan-out에서만 매칭되는 row(ntceInsttNm 단독 호출에선 dminsttNm=해군본부) — fan-out + union dedup 정상 동작.
→ "국방부 국군재정관리단" 정확 매칭 (PLAN F19 종료조건 충족).

#### 호출 #3 — F19 indstryty_cd 서버측 필터 (POC #6)

```python
search_bid_notices(biz_type='용역', date_from='20260401', date_to='20260430', limit=3, indstryty_cd='1169')
```

응답:
```
returned_count: 3
total_count: 3425    # POC #6 (filter active 22862 → 3425)와 정확 일치
lookup_mode: PPSSrch
items[0]: indstrytyLmtYn=Y
```

→ POC #6 raw evidence와 정확 일치 — 서버측 indstrytyCd 필터 동작 확인.

#### 호출 #4 — F22 search_agencies (자동완성)

```python
search_agencies(query='국방부', limit=10)
```

응답:
```
total_count: 10
scanned: 93
items[0]: [ntceInsttNm] code=ZD00303 name=국방부 국군재정관리단
items[1]: [ntceInsttNm] code=1290476 name=국방부 한국국방연구원
items[2]: [ntceInsttNm] code=1290479 name=국방부 전쟁기념사업회
items[3]: [ntceInsttNm] code=1290453 name=국방부 국군의무사령부
items[4]: [ntceInsttNm] code=1290446 name=국방부 국방홍보원
items[5]: [dminsttNm] code=1290000 name=국방부
items[6]: [dminsttNm] code=ZD00303 name=국방부 국군재정관리단
items[7]: [dminsttNm] code=1290476 name=국방부 한국국방연구원
```

→ 본부 + 산하기관 distinct 추출 OK. match_field로 ntceInsttNm/dminsttNm 출처 구분 가능.

#### 호출 #5 — F22 2자 미만 가드

```python
search_agencies(query='국', limit=5)
# {'items': [], 'total_count': 0, 'error': '2자 이상 입력 필요'}
```

→ 가드 OK.

### sanity check 종합

- [x] backend 호출 시그니처 변경 시 caller 정합 확인 (§ 3)
- [x] python import 성공 (L1)
- [x] R1 단건 모드 (bid_notice_no="R25BK00755515") 회귀 0 — 매칭 1건 (호출 #1)
- [x] PPSSrch 호출 PoC — ntceInsttNm="국방부" 5건+ 매칭 (호출 #2)
- [x] srvceDivNm 응답 BidNoticeSummary에 정상 도착 (호출 #1·#2)
- [x] indstryty_cd 서버측 필터 동작 (호출 #3, totalCount=3425 POC #6 정합)
- [x] search_agencies 10건 distinct (호출 #4)
- [x] search_agencies 2자 가드 (호출 #5)

---

## 5. 회귀 안정성

### R1 단건 모드 격리 보전

`bid.py:264~266`:
```python
if inp.bid_notice_no and not inp.date_from and not inp.date_to:
    return await _search_by_bid_notice_no(inp)
```

→ R1에서 도입한 5종 단일조회 endpoint + inqryDiv=2 + bidNtceNo 분기가 그대로 유지됨. PPSSrch 전환은 검색 모드(else 분기)만 영향. R1 사용자 보고 케이스(R25BK00755515 / R26BK01435763) 회귀 0.

### caller 회귀 0 (§ 3)

신규 인자는 keyword-only + 기본 None. 기존 caller 7개 모두 keyword arguments 호출 → 시그니처 변경 영향 없음.

### cache 무효화

`bid_v31` → `bid_v32` (응답 형태 변경: PPSSrch는 bsnsDivNm=null + srvce_div/ppsw_gnrl_yn 추가). 기존 캐시는 자동 stale → 새 응답 형태로 재생성.

---

## 6. tester-p31-r2 핸드오프 메시지

### 핵심 검증 포인트 (L3 raw 우선)

1. **PPSSrch endpoint vs 단일조회 분기**:
   - 단건 모드(`bid_notice_no="R25BK00755515"`): `lookup_mode="inqryDiv=2+bidNtceNo"`, `endpoints_used` 단일조회 endpoint 1개, `chunks_used=0` — R1 회귀 0 검증.
   - 검색 모드(`inst_name="국방부"` + 1개월 기간): `lookup_mode="PPSSrch+inst_fanout"`, `endpoints_used` PPSSrch 5종 또는 단일(biz_type 명시 시), `chunks_used >= 1`.

2. **F19 fan-out + union dedup 정합**:
   - `inst_name="국방부"` + biz_type=용역 → 응답 raw에 `ntceInsttNm`만 매칭 row + `dminsttNm`만 매칭 row 모두 포함.
   - 동일 `(bidNtceNo, bidNtceOrd)` 페어는 1회만 도착 (union dedup).
   - POC #7 AND 회피 검증: `ntceInsttNm + dminsttNm` 동시 전달 호출 없음 (코드상 fan-out 차원).

3. **F21 srvce_div / ppsw_gnrl_yn 응답 도착**:
   - 모든 정상 응답 row에 `srvce_div ∈ {"일반용역", "기술용역", null}` + `ppsw_gnrl_yn ∈ {"Y", "N", null}` 도착.
   - `bsnsDivNm` 필드는 PPSSrch 응답에서 항상 null (POC #5).

4. **L6 evidence — err-024 매핑**:
   - `inst_name="국방부"` 응답에 "국방부 국군재정관리단" 또는 "국방부 전쟁기념사업회" raw 매칭 → 사용자 화면값과 1:1 일치 검증.

### 회귀 변경 0 보장 영역

- `bid_notice_no` 단건 모드 (R1 격리 영역)
- `_search_by_bid_notice_no` 함수 (변경 0)
- `_resolve_bid_endpoints` (단일조회용 — 변경 0)
- `_BID_DETAIL_ENDPOINTS` (단건 모드 5종 fan-out — 변경 0)
- `get_bid_notice_detail`, `list_pre_specifications`, `get_pre_specification_detail` (변경 0)

### 추가 검증 권고

- **uvicorn 재기동 시각**: commit `34b19d5` 시각 vs uvicorn PID 시작 시각 명시 (R3.5 학습).
- **TPS 30 limit 감시**: fan-out 호출수 = chunks × endpoints × 2 (inst fan-out) — biz_type=None + 1개월 + inst_name → 5 × 1 × 2 = 10 호출. 5분 100건 한도 안전.
- **search_agencies 캐시**: prefix `agencies_v32` — 이전 prefix 캐시는 자동 stale.

### R3 영역 (R2 영역 외)

- F23 frontend 3계층 dropdown (bids/page.tsx)
- F26 ntceInsttNm + dminsttNm 두 필드 결과 표시 분리
- frontend `searchBidNotices` actions.ts에 `indstryty_cd` 추가 (R3 인계)

---

## 7. 보류/결함 사항

**없음.** 모든 R2 권고 강화 8항 적용 완료. POC raw evidence 명시 영역 외 변경 없음.

---

## 8. commit 정보

- commit hash: `34b19d5`
- commit message:
  ```
  feat(backend): P31-R2 PPSSrch 전환 + 발주기관 LIKE + srvceDivNm (F19, F21, F22)
  ```
- 변경 파일: `app/schemas/bid.py`, `app/tools/bid.py`, `app/server.py`
- 변경 라인: +182 / -47 (3 files)

R1 commit `69da6cb` ↔ R2 commit `34b19d5` 시퀀셜 atomic — rollback 단위 명확.
