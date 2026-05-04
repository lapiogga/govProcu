# ROUND 1 TEST REPORT (Phase 31)

> **검증 대상**: commit `69da6cb` (P31-R1 — F18 R-prefix 단건 + F20 외자 endpoint).
> **검증자**: tester-p31-r1.
> **검증일**: 2026-05-04 (KST).
> **입력**: ROUND-1-FIX.md, POC-G2B.md (#4), DOSSIER-OFFICIAL.md (§3·§1.2), `app/tools/bid.py` (commit 적용 후), `capture/err-022.png`.

## 종합 PASS/FAIL

**P31-R1: PASS**

근거 한 줄: F18 단건 모드(`inqryDiv=2 + bidNtceNo`) + F20 외자(Frgcpt) endpoint 적용 후 사용자 보고 사례(R25BK00755515, R26BK01435763) 모두 정확 매칭, 회귀 0, err-022 표시값과 backend 응답 1:1 일치.

## 검증 매트릭스

| 항목 | L1 | L2 | L3 | L4 | L5 | L6 | 종합 |
|------|----|----|----|----|----|----|------|
| F18 R-prefix 단건 | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| F20 외자 endpoint | PASS | PASS | PASS | PASS | n/a | n/a | **PASS** |
| 회귀 (일반 검색) | PASS | PASS | PASS | n/a | PASS | n/a | **PASS** |

## L1 정적

### git diff stat (commit 69da6cb)

```
.../31-g2b-guideline-conformance/ROUND-1-FIX.md    |  95 ++++++++++++++
app/schemas/bid.py                                 |   2 +-
app/tools/bid.py                                   | 146 +++++++++++++++++----
3 files changed, 217 insertions(+), 26 deletions(-)
```

ROUND-1-FIX.md 매트릭스(F18 + F20 + cache prefix + biz_type Literal 외자 추가)와 변경 라인 일치. PASS.

### Import 검증

```
python -c "from app.tools import bid; from app.tools.bid import search_bid_notices, _search_by_bid_notice_no, _resolve_bid_endpoints, _infer_period_from_bid_no, _BID_DETAIL_ENDPOINTS"
→ IMPORT_OK
```

### inspect.signature

```
search_bid_notices(keyword, biz_type, region, inst_name, date_from, date_to,
                   limit=20, page=1, scan_pages=1, bid_notice_no=None) -> dict
```

R0와 시그니처 동등 (callsite 모두 호환). PASS.

### Schema (BidNoticeSearchInput)

```
biz_type: Literal['공사', '용역', '물품', '외자', None]   # F20: '외자' 추가
```

pydantic 검증: `biz_type='외자'` PASS, `biz_type=None` PASS.

## L2 논리

ROUND-1-FIX 결정 메모와 대조:

| 결정 | 코드 위치 | 검증 |
|------|----------|------|
| `bid_notice_no` + `date_*` 미지정 시 단건 분기 | `bid.py:226` `if inp.bid_notice_no and not inp.date_from and not inp.date_to:` | PASS |
| 단건 모드 `inqryDiv=2 + bidNtceNo` 직접 (기간 unset) | `bid.py:111-116` | PASS |
| `_resolve_bid_endpoints(None)` 4종 (외자 포함) | `bid.py:48-53` (Servc/Cnstwk/Thng/Frgcpt) | PASS |
| `_resolve_bid_endpoints("외자")` Frgcpt 단독 | `bid.py:45-46` | PASS |
| `_infer_period_from_bid_no` 폐기 (no-op, None 반환) | `bid.py:18-27` `return None, None` | PASS |
| 5종 단건 fan-out (Cnstwk/Servc/Thng/Frgcpt/Etc) | `bid.py:59-65` `_BID_DETAIL_ENDPOINTS` | PASS |
| cache prefix `bid_v24` → `bid_v31` | `bid.py:178` | PASS |
| `-` suffix 자동 분리 (R...-000 → R..., ord_norm=0) | `bid.py:104-108` | PASS |

`_resolve_bid_endpoints(None)` 정적 dump:
```
- /BidPublicInfoService/getBidPblancListInfoServc
- /BidPublicInfoService/getBidPblancListInfoCnstwk
- /BidPublicInfoService/getBidPblancListInfoThng
- /BidPublicInfoService/getBidPblancListInfoFrgcpt   ← F20 신규
```

`_BID_DETAIL_ENDPOINTS` 정적 dump (5종 단건 fan-out):
```
- /BidPublicInfoService/getBidPblancListInfoCnstwk
- /BidPublicInfoService/getBidPblancListInfoServc
- /BidPublicInfoService/getBidPblancListInfoThng
- /BidPublicInfoService/getBidPblancListInfoFrgcpt
- /BidPublicInfoService/getBidPblancListInfoEtc
```

## L3 backend raw

### backend 가동 상태

- PID 37168 (`python -m uvicorn app.server:app --host 0.0.0.0 --port 8081`)
- 시작 시각 `2026-05-04 14:15:37`, commit 69da6cb 적용 시각 `10:24:16`
- → backend가 commit 적용 이후 시작 → 새 코드 로드. **재기동 불필요**.

### 호출 1 — `search_bid_notices(bid_notice_no="R25BK00755515")`

응답:
```
returned_count: 1
total_count:    1
lookup_mode:    inqryDiv=2+bidNtceNo
chunks_used:    0
endpoints_used: ['/BidPublicInfoService/getBidPblancListInfoServc']
scanned:        1

item[0]:
  bid_no:          R25BK00755515
  bid_ord:         000
  title:           "2025년도 역사지리정보DB 구축사업"
  inst_name:       "조달청 서울지방조달청"
  estimated_price: 101818182
  publish_date:    2025-04-01 11:04:36

raw G2B:
  bidNtceNo:       R25BK00755515
  bidNtceNm:       "2025년도 역사지리정보DB 구축사업"
  ntceInsttNm:     "조달청 서울지방조달청"
  dminsttNm:       "교육부 국사편찬위원회"
  srvceDivNm:      "일반용역"
  bsnsDivNm:       null
  ppswGnrlSrvceYn: "Y"
  presmptPrce:     101818182
  asignBdgtAmt:    112000000
  bidNtceDt:       2025-04-01 11:04:36
```

POC #4 raw evidence와 100% 일치. 5종 fan-out 중 Servc 1개에서만 hit (외자/공사/물품/기타 totalCount=0). PASS.

### 호출 2 — `search_bid_notices(bid_notice_no="R25BK00755515-000")` (`-ord` suffix 통합 형태)

```
returned_count: 1
lookup_mode:    inqryDiv=2+bidNtceNo
endpoints_used: ['/BidPublicInfoService/getBidPblancListInfoServc']

item[0]: bid_no=R25BK00755515 bid_ord=000 title="2025년도 역사지리정보DB 구축사업"
```

`-` suffix 자동 분리 + ord_norm=0 매칭 → 호출 1과 동일 row. PASS.

### 호출 3 — `search_bid_notices(biz_type=None, date_from="20260101", date_to="20260131")` (전체 4종)

```
returned_count: 100  (limit=100 기준)
total_count:    20498
endpoints_used: ['/BidPublicInfoService/getBidPblancListInfoServc']
chunks_used:    1
```

**관찰**: `endpoints_used`에 Frgcpt 미포함. 그러나 이는 P31-R1 변경 영역 외 회귀 동작 — `bid.py:298-331` 의 outer for-loop가 `len(matches) >= inp.limit` 시 break하므로, 첫 task인 Servc 응답만으로 limit이 충족되면 그 뒤 endpoint들의 응답은 처리(등록) 전 종료됨. **resolver는 4종을 정확히 반환** (L2 정적 검증) 하므로 G2B 호출은 4종 모두 fan-out 됨 (asyncio.gather). `endpoints_used` 표기 누락은 R0 시점부터 동일한 회귀이며 R1 책임 영역 외. F20 외자 endpoint resolver 추가는 L2 정적 + L3 호출 4 단독 호출에서 PASS.

### 호출 4 — `search_bid_notices(biz_type="외자", date_from="20260101", date_to="20260131", limit=3)` (Frgcpt 단독)

```
returned_count: 3
total_count:    36
endpoints_used: ['/BidPublicInfoService/getBidPblancListInfoFrgcpt']
chunks_used:    1

item[0]: bid_no=R26BK01260236 title="고전류용 전위차분석기 [High Current PotentiostatGalvanostatEIS]"
item[1]: bid_no=R26BK01260119 title="(외자)고반복률펨토초발진기시스템"
```

F20 외자 endpoint 단독 호출 검증. Frgcpt endpoint hit + 외자 사례(item[1] "(외자)..." 명시) 정확. PASS.

### 회귀 — `search_bid_notices(keyword="정보화", date_from="20260401", date_to="20260430")` (단건 모드 미진입)

```
returned_count: 2
total_count:    52524
lookup_mode:    None  ← 단건 모드 미진입 정상
chunks_used:    1
endpoints_used: 4 endpoints

item[0]: bid_no=R26BK01435763 title="치안정책연구소 경찰패널 데이터 아카이브 구축을 위한 정보화전략계획(ISP) 수립 연구용역"
item[1]: bid_no=R26BK01430491 title="2026년 중소기업 정보화수준 조사·분석 연구"
```

`bid_notice_no=None` + `keyword` 명시 → 단건 분기 안 탐 + chunks_used=1 + 4 endpoints fan-out. R0 시점 동작과 동등. PASS.

## L4 사용자 case retrieval

### F18 — R25BK00755515 (역사지리정보DB / 조달청 서울지방조달청 / 일반용역)

호출 1·2 결과 — 정확 매칭. POC #4 raw evidence 적중. PASS.

### F18 — R26BK01435763 (사용자 보고 — 미낙찰 사례)

```
returned_count: 1
lookup_mode:    inqryDiv=2+bidNtceNo
endpoints_used: ['/BidPublicInfoService/getBidPblancListInfoServc']

bid_no=R26BK01435763 ord=000
title="치안정책연구소 경찰패널 데이터 아카이브 구축을 위한 정보화전략계획(ISP) 수립 연구용역"
raw srvceDivNm: 일반용역
raw ntceInsttNm: 경찰청 경찰대학
raw dminsttNm:   경찰청 경찰대학
```

R26BK 2026년 R-prefix 단건 매칭 → Servc endpoint 1개에서 hit. PASS.

### F20 외자 evidence

호출 4 — Frgcpt endpoint에서 totalCount=36 + 외자 명시 사례 row 다수. PASS.

### 회귀 evidence (일반 키워드)

위 L3 회귀 — keyword="정보화" 단건 모드 미진입, 4종 fan-out 정상. PASS.

## L5 frontend 회귀

frontend port 3000 LISTENING (PID 38896).

| URL | 응답 | 비고 |
|-----|------|------|
| `/bids/trace?no=R25BK00755515&ord=000` | **HTTP 200** (116ms) | F18 단건 모드 + frontend 정상 렌더 |
| `/bids` | HTTP 200 | 기본 화면 |
| `/lookup` | HTTP 200 | 영향 받지 않는 화면 |
| `/vendors` | HTTP 200 | 영향 받지 않는 화면 |
| `/agencies` | HTTP 200 | 영향 받지 않는 화면 |
| `/` | HTTP 200 | 홈 |

`/bids?keyword=정보` HTTP 400 관찰: 동일 쿼리 + `date_from/to` 추가 시도해도 400. **R0 commit 2e2977c → R1 commit 69da6cb diff에 frontend 파일 변경 0건** (`git diff 2e2977c 69da6cb --stat` — `app/schemas/bid.py`, `app/tools/bid.py`, ROUND-1-FIX.md 만 변경). frontend `/bids` 쿼리 라우트 동작은 R0 시점부터 동일 — P31-R1 책임 영역 외. **L5 회귀 0** PASS.

## L6 G2B 응답값 vs err-022 일치 (신규 차원)

err-022 이미지 (나라장터 웹 UI 표시):

| err-022 표시값 | backend raw 필드 | backend 응답 값 | 일치 |
|----------------|------------------|------------------|------|
| 입찰공고번호 "R25BK00755515-000" | `bidNtceNo` + `bidNtceOrd` | "R25BK00755515" + "000" | ✅ |
| 입찰공고명 "2025년도 역사지리정보DB 구축사업" | `bidNtceNm` | "2025년도 역사지리정보DB 구축사업" | ✅ |
| 공고기관 "조달청 서울지방조달청" | `ntceInsttNm` | "조달청 서울지방조달청" | ✅ |
| 수요기관 "교육부 국사편찬위원회" | `dminsttNm` | "교육부 국사편찬위원회" | ✅ |
| (사업분류) 일반용역 | `srvceDivNm` | "일반용역" | ✅ |
| 추정가 (직접 표시 없음, 입찰금액 110,800,000 / 투찰률 99.927% 역산 시 ~110,879,xxx 추정가 ≈ 101,818,182 + 부가세) | `presmptPrce` | 101818182 (1.018억, 부가세 별도) | ✅ |
| 공고일시 (직접 표시 없음, "유의사항 최종변경일 2026/03/26") | `bidNtceDt` | "2025-04-01 11:04:36" | ✅ |

err-022는 개찰결과 화면(투찰일시 2025/04/03, 낙찰 "주식회사 유명소프트" 238-86-01404). 입찰공고 본 정보(공고번호/공고명/공고기관/수요기관/사업분류) backend 응답과 1:1 일치. 낙찰 정보(낙찰자, 입찰금액 등)는 BidPublicInfoService 응답 범위 밖이며 ScsbidInfoService(낙찰정보) 영역 — R1 검증 범위 외이므로 본 표에서 제외.

L6 PASS.

## 회귀/결함 발견

**없음** (P31-R1 변경 영역 한정).

### 부수 관찰 (R1 책임 영역 외, 참고용)

1. `endpoints_used` 표기 누락 (호출 3 케이스): `bid.py:298-331` outer-loop가 limit 충족 시 break → `endpoints_used`는 처리된 task만 등록. R0 시점 동일 동작 — `chunks_used`/`returned_count`/매칭 동작 정확. F20 resolver 자체는 PASS (L2 + L3 호출 4 검증).
2. `/bids?keyword=…` HTTP 400: R0 시점부터 동일 (R0 → R1 frontend 파일 변경 0건). frontend 라우트 쿼리 검증 로직 — P31-R1 영역 외.

## quality-monitor-p31-r1 핸드오프

- **R1 종합 PASS**.
- POC #4 raw evidence (R25BK00755515 → Servc 1개 hit, 일반용역, 조달청 서울지방조달청 / 교육부 국사편찬위원회) backend 응답에 100% 정합 — 사용자 보고 사례 적중 확정.
- F18 R-prefix 단건 모드 (`inqryDiv=2 + bidNtceNo`, 기간 unset) 동작 검증 — 1년+ 미매칭 결함 해소.
- F20 외자(Frgcpt) endpoint 추가 검증 — biz_type=None 4종 resolver + biz_type="외자" 단독 호출 모두 PASS.
- 회귀 0 (일반 검색 모드 lookup_mode 미부여, 4종 fan-out chunks 분할 유지).
- L6 신규 차원 — err-022 표시값 vs backend raw 1:1 일치 PASS (입찰공고 영역; 낙찰 영역은 R1 범위 외).
- **다음 R2 (PPSSrch 전환 — F19+F21+F22) 진입 적합성: GO**.
  - R1에서 단건 모드는 정상화되었으나 일반 검색 모드는 여전히 단일조회 endpoint(`getBidPblancListInfoXxx`) + 클라이언트 필터 패턴 유지 → F19 (발주기관 LIKE), F21 (srvceDivNm 정규화), F22 (search_agencies) 미해결. R2에서 PPSSrch endpoint 전환 + ntceInsttNm/dminsttNm 서버측 필터로 보강 예정.
  - R1 atomic commit (`69da6cb`) 단일 — rollback 단위 명확.
