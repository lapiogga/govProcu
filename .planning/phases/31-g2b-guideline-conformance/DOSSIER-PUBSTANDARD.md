# DOSSIER — PubDataOpnStdService (Phase 31)

> 작성일: 2026-05-04 (KST)
> 검증 범위: 사용자 첨부 ref-011/012 (swagger UI + API 상세) + 활용가이드 v1.2 docx (`tmp/g2b_guide.docx`)
> + 실 호출 PoC (`poc_pubstd.py` → `poc_pubstd_raw/`)
> 비교 대상: 기존 BidPublicInfoService PPSSrch (POC-G2B.md 7건)
> 작업 스코프: 자료 조사 / 코드 수정 금지

---

## 0. 핵심 결론 (TL;DR)

| 항목 | 결과 |
|------|------|
| **권고 옵션** | **옵션 hybrid** — BidPublicInfoService PPSSrch (현 PLAN R1~R5) 진행 + PubDataOpnStdService는 별도 활용신청 후 P2 단계에서 ETL/통계용으로 채택 |
| **사유 1줄** | PubDataOpnStdService는 (1) **별도 활용신청 미승인 상태** (PoC 0 → 403/500), (2) **LIKE 미지원 + bidNtceNo 단건 미지원** (명세상 검색 파라미터 = 기간 1종 only), (3) **응답에 srvceDivNm/ppswGnrlSrvceYn 부재** → F19/F18/F21 모두 PPSSrch 필요. 단 트래픽 10×, 단일 endpoint, 계약 join 가능은 P2 가치 |
| F18 (R-prefix 단건) | PPSSrch가 우월 (PubStd는 bidNtceNo 파라미터 명세 없음) |
| F19 (발주기관 LIKE) | PPSSrch가 우월 (PubStd는 ntceInsttNm/dmndInsttNm 검색 파라미터 명세 없음) |
| F20 (외자) | PubStd가 단일 호출로 가능 (`bsnsDivCd=2` Scsbid only). Bid는 PPSSrch + Frgcpt suffix 분리 필요 |
| F21 (일반/기술용역) | PPSSrch가 우월 (PubStd 응답에 srvceDivNm/ppswGnrlSrvceYn 명세 없음) |
| 트래픽 | PubStd 10,000/일 vs PPSSrch 1,000/일 (10×) |
| 단일 호출 효율 | PubStd는 4분류 통합 endpoint 1개 (Bid/Scsbid/Cntrct 각 1) vs PPSSrch는 4~5종 fan-out 필요 |
| 계약 join | **PubStd만 가능** — `getDataSetOpnStdCntrctInfo` 응답에 `bidNtceNo` 필드 → 입찰↔계약 join key 직접 제공 |

---

## 1. Swagger 사양 추출

> 출처: 활용가이드 v1.2 docx (`tmp/g2b_guide.docx`, 추출 → `tmp/g2b_guide.txt`)
> + ref-011/012 사용자 첨부 swagger UI (2026-04-30 최신, 활용신청 4,659건)

### 1.1 서비스 메타

| 항목 | 값 |
|------|----|
| 서비스 ID | `PubDataOpnStdService` |
| 서비스명(국문) | 나라장터 공공데이터개방표준서비스 |
| Base URL (가이드 v1.2) | `http://apis.data.go.kr/1230000/PubDataOpnStdService` |
| Base URL (ref-011 swagger) | `apis.data.go.kr/1230000/ao/PubDataOpnStdService` |
| 인증 | ServiceKey (REST GET) |
| 응답 포맷 | XML / JSON (`type=json`) |
| 트래픽 | 개발 10,000 / 운영 무제한 |
| 평균 응답 | 500ms |
| 초당 트랜잭션 | 30 TPS |
| 메시지 사이즈 | 4000 bytes |
| 갱신 주기 | 수시 |
| 행안부 고시 | 공공데이터 개방표준 |
| 등록/최종수정 | 2018-05-09 / **2026-04-30** |

### 1.2 getDataSetOpnStdBidPblancInfo (입찰공고)

#### 요청 파라미터 (활용가이드 v1.2)

| 이름 | 의미 | 필수 | 비고 |
|------|------|------|------|
| `numOfRows` | 한 페이지 결과 수 | 옵션(0) | |
| `pageNo` | 페이지 번호 | 옵션(0) | |
| `ServiceKey` | 인증키 | **필수(1)** | |
| `type` | 리턴 타입 | 옵션(0) | `json` 권장 |
| `bidNtceBgnDt` | 입찰공고시작일시 | **필수(1)** | `YYYYMMDDHHMM`, 1개월 제한 |
| `bidNtceEndDt` | 입찰공고종료일시 | **필수(1)** | `YYYYMMDDHHMM`, 1개월 제한 |

**중대한 명세 사실**:
- **검색 파라미터는 기간(`bidNtceBgnDt/EndDt`) 단 1종**.
- `bidNtceNo` (단건), `ntceInsttNm` (발주기관 LIKE), `bidNtceNm` (제목 LIKE), `bsnsDivCd` (업무구분), `indstrytyCd` (업종), `srvceDivNm` (용역구분) **모두 명세 없음**.
- 즉 **검색은 1개월 dump 후 client-side filter만 가능**.

#### 응답 필드 (52종, 활용가이드 v1.2)

```
bidNtceNo, bidNtceOrd, refNtceNo, refNtceOrd, ppsNtceYn,
bidNtceNm, bidNtceSttusNm, bidNtceDate, bidNtceBgn,
bsnsDivNm, intrntnlBidYn, cmmnCntrctYn, cmmnReciptMethdNm, elctrnBidYn,
cntrctCnclsSttusNm, cntrctCnclsMthdNm, bidwinrDcsnMthdNm,
ntceInsttNm, ntceInsttCd, ntceInsttOfclDeptNm, ntceInsttOfclNm,
  ntceInsttOfclTel, ntceInsttOfclEmailAdrs,
dmndInsttNm, dmndInsttCd, dmndInsttOfclDeptNm, dmndInsttOfclNm,
  dmndInsttOfclTel, dmndInsttOfclEmailAdrs,
presnatnOprtnYn, presnatnOprtnDate, presnatnOprtnTm, presnatnOprtnPlce,
bidPrtcptQlfctRgstClseDate, bidPrtcptQlfctRgstClseTm,
cmmnReciptAgrmntClseDate, cmmnReciptAgrmntClseTm,
bidBeginDate, bidBeginTm, bidClseDate, bidClseTm,
opengDate, opengTm, opengPlce,
asignBdgtAmt, presmptPrce, rsrvtnPrceDcsnMthdNm,
rgnLmtYn, prtcptPsblRgnNm,
indstrytyLmtYn, bidprcPsblIndstrytyNm,
bidNtceUrl, dataBssDate
```

**부재 필드** (BidPublicInfoService PPSSrch에는 있는데 PubStd에는 없음):
- `srvceDivNm` — 일반용역/기술용역 구분 (F21 핵심)
- `ppswGnrlSrvceYn` — 조달청일반용역여부 (F21 보조)
- `rgnLmtBidLocplcNm` — 지역 제한 입찰장소
- `bsnsDivCd` (응답 필드, request도 없음)

> **주의** — 사용자 첨부 ref-011 swagger UI에는 응답 필드 64종이 있다고 표시될 수 있으나, **활용가이드 v1.2는 52종으로 명시**. 차이는 6년 사이 spec 추가 가능성 — 확정은 활용신청 승인 + 실 호출 후. 본 보고서는 **활용가이드 명세를 신뢰하는 보수 기준** 적용.

### 1.3 getDataSetOpnStdScsbidInfo (낙찰)

#### 요청 파라미터

| 이름 | 의미 | 필수 | 비고 |
|------|------|------|------|
| `numOfRows`, `pageNo`, `ServiceKey`, `type` | 공통 | | |
| `bsnsDivCd` | 업무구분코드 | 옵션(0) | **1=물품, 2=외자, 3=공사, 5=용역** (4 미사용) |
| `opengBgnDt` | 개찰시작일시 | **필수(1)** | `YYYYMMDDHHMM`, **1주일 제한** |
| `opengEndDt` | 개찰종료일시 | **필수(1)** | `YYYYMMDDHHMM`, **1주일 제한** |

**검색은 (1) 개찰일시 1주일 (2) `bsnsDivCd` 4분류 — 그 외 검색 파라미터 없음**.

#### 응답 필드 (38종)

```
bidNtceNo, bidNtceOrd, bidNtceNm, bsnsDivNm,
cntrctCnclsSttusNm, cntrctCnclsMthdNm, bidwinrDcsnMthdNm,
ntceInsttNm, ntceInsttCd, dmndInsttNm, dmndInsttCd,
sucsfLwstlmtRt, presmptPrce, rsrvtnPrce, bssAmt,
opengDate, opengTm, opengRsltDivNm, opengRank,
bidprcCorpBizrno, bidprcCorpNm, bidprcCorpCeoNm,
bidprcAmt, bidprcRt, bidprcDate, bidprcTm,
sucsfYn, dqlfctnRsn,
fnlSucsfAmt, fnlSucsfRt, fnlSucsfDate,
fnlSucsfCorpNm, fnlSucsfCorpCeoNm, fnlSucsfCorpOfclNm,
fnlSucsfCorpBizrno, fnlSucsfCorpAdrs, fnlSucsfCorpContactTel,
dataBssDate
```

**특기**:
- `bidprcCorpNm/Bizrno/CeoNm/Amt/Rt/Date/Tm` 7종 + `fnlSucsf*` 9종 → **응찰업체 + 최종낙찰업체** 모두 단일 응답에 포함 (BidPublicInfoService Award는 분리 endpoint).
- `srvceDivNm` (일반/기술용역) 응답 필드 **없음**.

### 1.4 getDataSetOpnStdCntrctInfo (계약)

#### 요청 파라미터

| 이름 | 의미 | 필수 | 비고 |
|------|------|------|------|
| `numOfRows`, `pageNo`, `ServiceKey`, `type` | 공통 | | |
| `cntrctCnclsBgnDate` | 계약체결시작일자 | **필수(1)** | `YYYYMMDD`, 1개월 제한 (현재 1주일 축소 운영) |
| `cntrctCnclsEndDate` | 계약체결종료일자 | **필수(1)** | `YYYYMMDD`, 1개월 제한 (현재 1주일 축소 운영) |

#### 응답 필드 (44종) — **`bidNtceNo` 포함**

```
cntrctNo, untyCntrctNo, cntrctOrd, cntrctNm,
bsnsDivNm, cntrctCnclsSttusNm, cntrctCnclsMthdNm,
lngtrmCtnuDivNm, cmmnCntrctYn,
cntrctCnclsDate, cntrctPrd, cntrctAmt, ttalCntrctAmt, cntrctInfoUrl,
bidNtceNo, bidNtceOrd, bidNtceNm,    ← 입찰 join key
opengDate, opengTm, rsrvtnPrce,
prvtcntrctRsn, bidNtceUrl,
cntrctInsttDivNm, cntrctInsttNm, cntrctInsttCd,
  cntrctInsttChrgDeptNm, cntrctInsttOfclNm,
  cntrctInsttOfclTel, cntrctInsttOfcl,
dmndInsttDivNm, dmndInsttNm, dmndInsttCd,
  dmndInsttOfclDeptNm, dmndInsttOfclNm,
  dmndInsttOfclTel, dmndInsttOfclEmailAdrs,
rprsntCorpNm, dmstcCorpYn, rprsntCorpCeoNm,
  rprsntCorpOfclNm, rprsntCorpBizrno,
  rprsntCorpAdrs, rprsntCorpContactTel,
dataBssDate
```

**핵심 가치**:
- **`bidNtceNo + bidNtceOrd` 응답 필드 보유** → 입찰공고 ↔ 계약 직접 join 가능. PubDataOpnStdService에서만 누리는 단일 endpoint join.
- `bsnsDivNm` 값 가이드 명세에 `물품/용역/공사/외자/비축` (5종 — Bid의 4종에 비축 추가).
- `prvtcntrctRsn` (수의계약사유) 직접 제공.

---

## 2. 행안부 표준 vs G2B 자체 필드 비교

| 의미 | PubStd 필드 | BidPublicInfoService PPSSrch 필드 | 차이 |
|------|------------|-----------------------------------|------|
| 입찰공고번호 | `bidNtceNo` | `bidNtceNo` | 동일 |
| 입찰공고명 | `bidNtceNm` | `bidNtceNm` | 동일 |
| 공고기관 | `ntceInsttNm` | `ntceInsttNm` | 동일 |
| 수요기관 (PubStd) | `dmndInsttNm` | `dminsttNm` (PPSSrch) | **표기 다름** ⚠️ — PubStd는 `dmndInsttNm`(d**m**nd), PPSSrch는 `dminsttNm`(d**mi**n) |
| 업무구분명 | `bsnsDivNm` | `bsnsDivNm` | 동일. PubStd는 5종(물품/용역/공사/외자/비축), PPSSrch는 응답값 4종 |
| 업무구분코드 | `bsnsDivCd` (req only, Scsbid) | (미사용) | **PubStd만** |
| 일반/기술용역 | (없음) | `srvceDivNm` ("일반용역"/"기술용역") | **PPSSrch만** |
| 조달청일반용역여부 | (없음) | `ppswGnrlSrvceYn` (Y/N) | **PPSSrch만** |
| 지역제한 (시도) | `prtcptPsblRgnNm` | `rgnLmtBidLocplcNm` 또는 `prtcptPsblRgnNm` | PPSSrch가 더 풍부 |
| 업종제한 코드 | (응답 없음, request 없음) | `indstrytyCd` (req param OK, POC #6 검증) | **PPSSrch만** |

### 2.1 bsnsDivCd 코드 매핑 (PubStd Scsbid only)

> 활용가이드 v1.2 명문: "업무구분코드가 1이면 물품, 2면 외자, 3이면 공사, 5면 용역"

| 코드 | 라벨 |
|------|------|
| 1 | 물품 |
| 2 | 외자 |
| 3 | 공사 |
| 4 | (미사용 / reserved) |
| 5 | 용역 |

**4 결번 주의**. 5는 "용역" (일반/기술 미분리). PubStd는 `srvceDivNm` 미응답이므로 일반용역 vs 기술용역 분리 어디서도 불가.

### 2.2 표기 차이 — `dmndInsttNm` vs `dminsttNm`

- **PubStd (행안부 고시)**: `dmndInsttNm` (demand institute의 약어)
- **BidPublicInfoService (G2B 자체)**: `dminsttNm` (이전 표기)

backend 정규화 시 두 필드 모두 fallback 필요:
```python
inst_name = raw.get("dmndInsttNm") or raw.get("dminsttNm") or raw.get("ntceInsttNm")
```

---

## 3. 실 호출 PoC raw 응답 dump

> 실행: `python .planning/phases/31-g2b-guideline-conformance/poc_pubstd.py`
> raw: `.planning/phases/31-g2b-guideline-conformance/poc_pubstd_raw/`

### 3.1 PoC 0 — Base URL 후보 검증 (3개)

| Base URL | HTTP | body | 해석 |
|----------|------|------|------|
| `https://apis.data.go.kr/1230000/ao/PubDataOpnStdService` | **403** | `Forbidden` | endpoint **존재** but 키 권한 없음 (활용신청 미승인) |
| `https://apis.data.go.kr/1230000/PubDataOpnStdService` | **500** | `Unexpected errors` | 활용가이드 v1.2 base — 활용신청 미승인 시 일반 500 |
| `https://apis.data.go.kr/1230000/ad/PubDataOpnStdService` | **404** | `API not found` | path 잘못됨 — `/ad`는 BidPublicInfoService 영역 |

**결정적 evidence**: ref-011 swagger UI 명시 base (`/ao/PubDataOpnStdService`) 가 정확. 하지만 **우리 G2B_KEY_BID(=ALL keys 동일)는 활용신청 미승인 상태**. 따라서:

- 응답 raw 직접 검증은 **불가**.
- 활용가이드 v1.2 명세 + ref-011 swagger UI 명세를 신뢰 기준 채택.
- 활용신청 (data.go.kr/data/15058815/openapi.do) 후 후속 PoC 재실행 권고.

### 3.2 PoC 1~6 (skip — 모두 403/500 by 활용신청 미승인)

PoC 0에서 base URL 모두 인증 실패 → PoC 1~6 skip 처리. 활용신청 승인 후 동일 스크립트 재실행으로 raw evidence 확보 가능.

```python
# 활용신청 승인 후 재실행할 PoC 목록 (poc_pubstd.py 내장)
- PoC 1: getDataSetOpnStdBidPblancInfo 1주일 baseline (응답 필드 카탈로그)
- PoC 2: ntceInsttNm=조달청 추가 → totalCount 비교 (LIKE 미적용 검증)
- PoC 3: bidNtceNm=공사 추가 → 동일
- PoC 4: getDataSetOpnStdScsbidInfo + bsnsDivCd 1/2/3/5 매핑 검증
- PoC 5: getDataSetOpnStdCntrctInfo 1주일 dump (bidNtceNo join key 검증)
- PoC 6: bidNtceNo 명세 외 파라미터 추가 (R-prefix 단건 시도)
```

### 3.3 PoC 0 raw

```json
// poc_pubstd_raw/_summary.json (excerpt)
{
  "chosen_base": null,
  "poc0_probe_results": [
    {"base": "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService",
     "status": 403, "body_excerpt": "Forbidden\n"},
    {"base": "https://apis.data.go.kr/1230000/PubDataOpnStdService",
     "status": 500, "body_excerpt": "Unexpected errors\n"},
    {"base": "https://apis.data.go.kr/1230000/ad/PubDataOpnStdService",
     "status": 404, "body_excerpt": "API not found\n"}
  ]
}
```

---

## 4. 우리 PLAN과 매핑 표

| ID | 결함 | BidPublicInfoService PPSSrch (현 PLAN, POC-G2B 검증) | PubDataOpnStdService (명세 + PoC 0 검증) | 판정 |
|----|------|------------------------------------------------|----------------------------------------|------|
| F18 | R-prefix 1년+ 단건 (R25BK00755515) | ✅ `inqryDiv=2 + bidNtceNo`, 기간 unset OK (POC #4 적중) | ❌ `bidNtceNo` request 파라미터 명세 없음. 기간 필수 + 1개월 제한. 1년 단건은 12개월 chunk dump 후 client-side `bidNtceNo` 매칭 — **고비용** | **PPSSrch 우월** |
| F19 | 발주기관 LIKE | ✅ `ntceInsttNm`/`dminsttNm` LIKE PPSSrch 직접 전달 (POC #1·#2 적중) | ❌ `ntceInsttNm` request 파라미터 명세 없음. 기간 dump 후 client-side substring 필터 | **PPSSrch 우월** |
| F20 | 외자 + indstrytyCd | ✅ `Frgcpt` suffix endpoint + `indstrytyCd` request 파라미터 (POC #6 적중) | ⚠️ Scsbid에서 `bsnsDivCd=2` 단일 호출로 가능. **단 입찰공고는 `bsnsDivCd` request 파라미터 없음** (응답 `bsnsDivNm`로만) → Bid 외자 분리는 PubStd에서 client-side filter | **PPSSrch 우월** (입찰공고 외자 분리), Scsbid는 PubStd가 약간 우월 |
| F21 | 일반용역/기술용역 분리 | ✅ `srvceDivNm` 응답 필드 (POC #5 raw 적중) | ❌ `srvceDivNm`/`ppswGnrlSrvceYn` 응답 명세 없음 | **PPSSrch 우월** |
| F22 | 발주기관 자동완성 | △ search_bid_notices distinct로 가능하지만 비용 높음 — 별도 데이터 소스 권장 | △ 동일. PubStd는 응답 필드명 차이 (`dmndInsttNm`)만 있고 LIKE 미지원은 동일 | 동등 |
| F23 | 3계층 dropdown | frontend 변경 (backend 무관) | 동일 | 동등 |
| 트래픽 | 1,000/일 (개발) | **10,000/일 (개발) — 10×** | **PubStd 우월** |
| 단일 호출 효율 | 4-5종 fan-out 필요 (Cnstwk/Servc/Thng/Frgcpt/Etc) | **단일 endpoint** (4분류 통합) | **PubStd 우월** |
| 계약 join | ❌ Cntrct는 `/ao/CntrctProcssIntgOpenService` 별도 서비스 (별도 활용신청) | ✅ `getDataSetOpnStdCntrctInfo` 응답에 `bidNtceNo` 직접 → 입찰↔계약 단일 endpoint join | **PubStd 우월** |
| 1주일 vs 1개월 범위 | 1개월 (Bid) | **1주일 (Scsbid 운영 축소)** | PPSSrch 우월 |
| 응찰업체 정보 | 별도 (`getOpengResultListInfoXxx`) | **Scsbid 응답 단일에 bidprcCorp + fnlSucsfCorp 포함** | PubStd 약간 우월 |
| 활용신청 | ✅ 승인 (현 G2B_KEY_BID 사용 중) | ❌ **미승인** (PoC 0: 403/500) | PPSSrch 즉시 사용 가능 |

### 4.1 점수 합산 (P0 결함 4건 + 효율 + 운영)

| 차원 | PPSSrch 우세 | PubStd 우세 | 동등 |
|------|:---:|:---:|:---:|
| F18~F21 (P0) | **4** | 0 | 0 |
| 효율 (트래픽/단일호출/계약join/응찰합산) | 0 | **4** | 0 |
| 운영 즉시성 | **1** | 0 | 0 |
| **합** | **5** | 4 | — |

P0 결함 fix는 PPSSrch가 **결정적으로** 우월. 효율은 PubStd가 우월하나 **현재 P0를 막지 못함**.

---

## 5. 결론 — 옵션 A / B / hybrid 권고

### 5.1 권고: **옵션 hybrid** (시기 분리)

**Stage 1 (현 Phase 31, R1~R5 PLAN 그대로 진행)**:
- BidPublicInfoService PPSSrch 5종 endpoint 채택 (현 PLAN.md §3.1).
- F18 (`inqryDiv=2 + bidNtceNo`), F19 (`ntceInsttNm/dminsttNm` LIKE), F20 (`Frgcpt` 추가), F21 (`srvceDivNm` 응답 정규화) 모두 **PPSSrch만으로** 해결.
- Award/Contract도 기존 ScsbidInfoService/CntrctProcssIntgOpenService 그대로.

**Stage 2 (별도 후속 phase)**:
- data.go.kr/data/15058815/openapi.do **활용신청 추진** (10,000/일 트래픽 + 단일 endpoint).
- 승인 후 PubDataOpnStdService 채택 영역:
  - **대량 ETL/dump 작업**: 일별 1주일~1개월 기간 dump → Redis/DB 적재. 4종 endpoint fan-out 대신 단일 호출로 비용 절감.
  - **계약 정보 통합 화면**: `getDataSetOpnStdCntrctInfo` 응답에 `bidNtceNo` 포함 → 입찰↔낙찰↔계약 단일 join. CntrctProcssIntgOpenService(`/ao`) 의존 제거 가능.
  - **통계/대시보드**: 트래픽 10× 활용 일별 집계.
  - **vendor profile 보강**: Scsbid 응답에 응찰업체 + 최종낙찰업체 동시 포함 — 업체별 응찰·낙찰 history 단일 호출로 수집.

**Stage 2 배제 영역** (PPSSrch 유지):
- 사용자 검색 UI (`/bids` 화면) — F19 LIKE 필수, 일반/기술용역 분리(F21) 필수, 단건 매칭(F18) 필수 모두 PPSSrch만 가능.

### 5.2 옵션별 명시 비교

| 옵션 | 채택 | 사유 |
|------|------|------|
| A: PPSSrch only | △ Stage 1만 | 현 PLAN 그대로. P0 결함 모두 해결. 단 트래픽 1,000/일 한계 |
| B: PubStd only (메인) | ❌ | F19 LIKE/F21 srvceDivNm/F18 단건 모두 client-side dump filter — 비현실적 (1주일 dump 22,862건 → 검색 1건당 22,862건 scan). 사용자 UX 회복 불가 |
| **hybrid** | ✅ **Stage 1=A → Stage 2 PubStd 추가** | **이상적** — 검색 UX는 PPSSrch (즉시 사용), 대량/통계/계약은 PubStd (10× 트래픽, 활용신청 후) |

### 5.3 BidPublicInfoService PPSSrch 대체 가능 영역

**없음** — F18~F21 모두 PPSSrch 응답 필드/파라미터에 의존. PubStd 명세에 동등 기능 부재.

### 5.4 BidPublicInfoService PPSSrch 우월 영역

- F18 R-prefix bidNtceNo 단건 (`inqryDiv=2`)
- F19 발주기관/공고명 LIKE (`ntceInsttNm`/`dminsttNm`/`bidNtceNm` request param)
- F20 외자 분리 (`Frgcpt` suffix endpoint)
- F21 일반/기술용역 (`srvceDivNm`/`ppswGnrlSrvceYn` 응답)
- 업종 필터 (`indstrytyCd` request param, POC #6 22862→3425 검증)
- 활용신청 즉시 사용 가능 (현 G2B_KEY_BID 승인됨)

### 5.5 PubDataOpnStdService 활용 권고 시기

| 시점 | 작업 |
|------|------|
| Phase 31 진행 중 | **활용신청 제출** (data.go.kr/data/15058815/openapi.do) — 승인 2~3일 |
| Phase 31 종료 후 | 별도 phase에서 PubStd 채택 — ETL 적재 + 계약 단일 join 통합 |
| Phase 32+ (제안) | (1) 일별 dump cron → Redis/DB / (2) `/contracts` 화면 새로 그리기 / (3) `vendor_profile` 응찰·낙찰 history 보강 / (4) 통계 대시보드 |

### 5.6 코드 영향 (Stage 2 시점)

- 신규 module: `app/clients/g2b_pubstd.py` (별도 client — base URL `/ao/PubDataOpnStdService`)
- 신규 settings: `g2b_pubstd_base_url`, `g2b_key_pubstd` (또는 단일 키 재사용 — data.go.kr 단일 ServiceKey)
- 응답 정규화 시 `dmndInsttNm` ↔ `dminsttNm` fallback 처리 필요
- 기존 PPSSrch 코드는 **유지** (사용자 검색 UI 채널)

---

## 출처

1. **공공데이터포털 — 조달청 나라장터 공공데이터개방표준서비스**
   URL: https://www.data.go.kr/data/15058815/openapi.do
   메타: 등록 2018-05-09 / 최종 2026-04-30 / 활용신청 4,659건 / 트래픽 10,000(개발)·무제한(운영)

2. **활용가이드 v1.2 (2019-06)** — `tmp/g2b_guide.docx` (335 KB)
   추출 텍스트: `tmp/g2b_guide.txt`
   섹션: 1.1 서비스명세 / 오퍼레이션 3종 명세 / 에러코드

3. **사용자 첨부 ref-011 (swagger UI)** — base URL `apis.data.go.kr/1230000/ao/PubDataOpnStdService`
   사용자 첨부 ref-012 (오픈API 상세) — 트래픽/등록일 메타

4. **PoC 실행 결과** — `.planning/phases/31-g2b-guideline-conformance/poc_pubstd_raw/_summary.json`
   - PoC 0: 3개 base URL 후보 검증 → 403/500/404 (활용신청 미승인 확인)
   - PoC 1~6: 명세 검증용 — 활용신청 승인 후 재실행 가능

5. **DOSSIER-OFFICIAL.md §1.4** (선행 분석) — `bsnsDivCd` 1/2/3/5 매핑 활용가이드 인용

6. **POC-G2B.md** (BidPublicInfoService PPSSrch 비교 baseline) — 7건 raw evidence 검증 완료

7. **공공데이터 개방표준** — 행안부 고시 (개방표준 dataset 명세)

---

## 부록 — 활용신청 승인 후 추가 검증 항목

활용신청 승인되면 PoC 0 base URL 채택 후 다음 핵심 검증 필요:

1. **응답 필드 실제 카탈로그 vs 활용가이드 v1.2 명세** — swagger UI(2026-04-30 갱신)가 가이드(2019)보다 새로움. `srvceDivNm`/`ppswGnrlSrvceYn` 추가 여부 재검증.
2. **`bidNtceNo` 명세 외 파라미터 시도** — 일부 endpoint는 명세 외 파라미터를 받을 수 있음 (BidPublicInfoService처럼). 받아주면 F18 단건 가능.
3. **`bsnsDivCd` 입찰공고에서 동작 여부** — 가이드는 Scsbid only지만 실 호출 시 Bid도 받을지 검증.
4. **계약 ↔ 입찰 join key 정확도** — `getDataSetOpnStdCntrctInfo.bidNtceNo`가 `R25BK...` 형식 일치하는지 (수의계약은 NULL 가능 — 가이드 sample에 NULL 있음).
5. **트래픽 실측** — 10,000/일이 실제로 적용되는지 (개발/운영 차이).
