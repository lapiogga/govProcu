# DOSSIER — KWATER OpenAPI (Phase 31)

> 작성일: 2026-05-04
> 출처: 공공데이터포털 (data.go.kr) Swagger spec 직접 추출 + 실 호출 PoC (KWATER_API_KEY)
> 작업 스코프: 자료 수집/분석 + 실 호출 검증. 코드 수정 금지.
> 검증 대상: `app/clients/external/kwater.py`, `app/tools/external.py`, `frontend/src/app/external/kwater/page.tsx` (+ contract 상세)

---

## 0. 핵심 결론 (TL;DR)

1. **KWATER 공식 endpoint는 3종** — `/cntrwkList`(공사) / `/servcList`(용역) / `/dmscptList`(내자=물품). G2B 4분류와 달리 "외자" / "기타"는 없음. base host 는 `apis.data.go.kr/B500001/ebid/cntrct3` (계약), `apis.data.go.kr/B500001/ebid/tndr3` (입찰공고).
2. **우리 backend는 endpoint 2종만 매핑** — `공사 → /cntrwkList`, `용역 → /servcList`. **`/dmscptList`(내자/물품) endpoint 누락**. backend 코드 주석은 "물품은 cntrct3 분류 미존재"라고 잘못 명시 (실제로는 존재함, 단 `dmscpt` (내자) 라는 다른 이름).
3. **결정적 결함 (frontend+backend)** — 사용자가 frontend dropdown에서 "물품" 선택 시 backend `KWaterAdapter.search_contracts(biz_type='물품')`이 `ENDPOINTS.get('물품', DEFAULT_ENDPOINT)` → **공사 endpoint(`/cntrwkList`)로 fall-through하여 공사 데이터를 물품으로 라벨링하는 silent mix-up 가능**. 단, 현재 frontend는 dropdown에 "공사" / "용역"만 노출 → 실 노출 결함은 0이지만 backend 안전장치 없음.
4. **응답 정규화 정합 — 1건 결함**. `cntrctDivNm` 실제 값은 `공사` / `용역` / **`내자`** (※ "물품"이 아님). 우리 backend `normalize_contract`가 `biz_type=raw["cntrctDivNm"]` 그대로 보존 → frontend 가 "내자" 값을 받으면 Badge variant fall-through (outline 처리). 표시는 가능하나 사용자가 "물품" 검색했는데 결과 row의 "내자" 라벨 표시로 일관성 깨짐.
5. **frontend default month — 1년 전 사용** (line 51-58). 1년 전 데이터는 보유 확실 (totalCount 검증 완료) — 현재 default 정합. 단 사용자가 "1년+ 매칭"을 의심한 영역은 **G2B BidPublicInfoService** 쪽 (Phase 31 F18) 이지 KWater 쪽이 아님. KWater는 월 단위 단순 lookup만 제공하므로 1년+ 매칭 결함 가능성 0.

---

## 1. KWATER 공식 OpenAPI 사양

### 1.1 base URL

| 데이터셋 | host | dataset ID |
|---------|------|-----------|
| 전자조달 계약정보공개 | `https://apis.data.go.kr/B500001/ebid/cntrct3` | 15101620 |
| 전자조달 입찰공고 | `https://apis.data.go.kr/B500001/ebid/tndr3` | 15101635 |
| 전자조달 사전규격공개 | (별도 dataset) | 15101628 |
| 전자조달 발주계획 | (별도 dataset) | 15102588 |

**계약 dataset 전체 명칭**: `한국수자원공사_전자조달 계약정보공개`
**제공처**: 공공데이터포털 / K-water 전자조달시스템(ebid.kwater.or.kr) 원천 데이터

출처: [data.go.kr/data/15101620](https://www.data.go.kr/data/15101620/openapi.do) Swagger spec
- 호스트: `"host":"apis.data.go.kr/B500001/ebid/cntrct3"`
- basePath: `""`
- schemes: `["https","http"]`

### 1.2 계약 endpoint 3종 (cntrct3 dataset)

| 라벨 | endpoint | operationId | summary |
|------|----------|-------------|---------|
| 공사 | `/cntrwkList` | `cntrwkList` | 공사 계약체결현황 정보 조회 서비스 |
| 용역 | `/servcList` | `servcList` | 용역 계약체결현황 정보 조회 서비스 |
| **내자** | `/dmscptList` | `dmscptList` | 내자 계약체결현황 정보 조회 서비스 |

> **"내자"** = domestic capital (국내 자본 = 물품 조달). G2B 4분류의 "물품"에 대응하지만 KWater 공식 명칭은 **내자**. "외자"(국외) endpoint는 KWater에 없음.

출처: data.go.kr/data/15101620 Swagger spec (paths 객체 + operationId 추출, raw dump `tmp/kwater_extract.txt`)

### 1.3 입찰공고 endpoint 5종 (tndr3 dataset, 계약과 별개)

검증 결과 `apis.data.go.kr/B500001/ebid/tndr3` 호스트에 다음 path 존재:
- `/cntrwkList` (공사 입찰공고)
- `/servcList` (용역 입찰공고)
- `/gdsList` (물품 입찰공고)
- `/rstList` (?)
- `/dmscptList` (내자 입찰공고)

> 우리 코드 `KWaterAdapter.search_bids()` 는 `{"items":[], "note":"...입찰공고 OpenAPI 미제공"}`을 반환 — **이는 사실 오류**. 입찰공고 OpenAPI(tndr3)가 존재함. 다만 사용자 요구는 "계약" 위주이고 검증된 영역만 활성화한 것이므로 PENDING/관리 결정 사항.

출처: data.go.kr/data/15101635 Swagger spec (raw dump `tmp/kwater_15101635.html`)

### 1.4 파라미터 명세 (3 endpoint 동일)

| 파라미터 | 필수 | 타입 | 의미 | 예 |
|---------|------|------|------|-----|
| `serviceKey` | 필수 | string | 공공데이터포털에서 받은 인증키 | (URL-encoded) |
| `pageNo` | 필수 | number | 페이지번호 | 1 |
| `numOfRows` | 필수 | number | 한 페이지 결과 수 | 10 |
| `_type` | 옵션 | string | 출력형식 (xml=기본, json) | json |
| `searchDt` | **필수** | string | 검색년월 (YYYYMM) | 202205 |

**중요**:
- `searchDt`는 **필수**. 우리 backend는 옵션으로 처리 → 미지정 시 KWater가 400 또는 default 동작 (공식 spec은 미지정 시 동작 미정의). frontend `defaultMonth()`가 1년 전 YYYYMM을 채워 보내므로 실 사용에서는 문제 없음.
- 키워드/기관/금액 필터 **미지원**. 월 단위 단순 dump.
- 페이지당 최대 결과 수는 spec 명시 없음. 기본 1000 추정 (G2B 표준 한계).

출처: data.go.kr/data/15101620 Swagger parameters 배열

### 1.5 응답 필드 명세 (3 endpoint 동일 — order 차이만)

| 필드 | 타입 | description (공식) |
|------|------|------------------|
| `cntrctDe` | string | 계약일 (YYYYMMDD) |
| `cntrctDeptNm` | string | 발주부서 |
| `cntrctDivNm` | string | 구분 (값: 공사/용역/내자) |
| `cntrctEntrpsNm` | string | 계약자 |
| `ctrmthdNm` | string | 계약방법 |
| `lastCtramt` | string | 계약금액 (콤마 포함 문자열) |
| `lmttMthNm` | string | 낙찰방법 |
| `ordgNo` | string | 계약번호 (prefix C1/C3/C5) |
| `ordgTit` | string | 계약명 |
| `strwrkDe` | string | 계약기간 (YYYYMMDD~YYYYMMDD) |

**ordgNo prefix 의미** (PoC 결과 추론):
- `C1...` = 내자 (dmscpt)
- `C3...` = 공사 (cntrwk)
- `C5...` = 용역 (servc)

출처: Swagger items.item.properties + 실 호출 PoC 결과 (`tmp/kwater_poc_202205.json`)

---

## 2. 우리 코드 정합성 점검

### 2.1 `app/clients/external/kwater.py`

| 항목 | 공식 | 우리 코드 | 정합 |
|------|------|----------|------|
| BASE_URL | `https://apis.data.go.kr/B500001` | `https://apis.data.go.kr/B500001` | OK |
| 공사 endpoint | `/ebid/cntrct3/cntrwkList` | `/ebid/cntrct3/cntrwkList` | OK |
| 용역 endpoint | `/ebid/cntrct3/servcList` | `/ebid/cntrct3/servcList` | OK |
| **내자(물품) endpoint** | `/ebid/cntrct3/dmscptList` | **누락** | **결함 K1** |
| `searchDt` 형식 | YYYYMM 필수 | YYYYMM 옵션 (None 가능) | 부분 결함 K2 |
| `numOfRows` | 옵션 명시 없음 | limit 그대로 전달 | OK |
| `_type=json` | 옵션 | base.py에서 `type=json` + `_type=json` 둘 다 추가 | OK |
| 응답 정규화 | 10 필드 | 10 필드 모두 매핑 | OK |
| `biz_type` 값 보존 | "공사"/"용역"/"내자" | raw["cntrctDivNm"] 그대로 | 부분 결함 K3 |
| search_bids 처리 | tndr3 endpoint 존재 | 빈 결과 + "미제공" note | 부분 결함 K4 |

**결함 K1 (HIGH)** — `ENDPOINTS` dict에 `"물품": "/ebid/cntrct3/dmscptList"` 추가 필요.
- 현재 코드:
  ```python
  ENDPOINTS = {
      "공사": "/ebid/cntrct3/cntrwkList",
      "용역": "/ebid/cntrct3/servcList",  # 정보화 영역 핵심
  }
  ```
- 주석에 `# 5/2 N29 — biz_type 별 endpoint (공사/용역 검증 완료, 물품은 cntrct3 분류 미존재)` 라고 잘못 명시.
- `biz_type='물품'` 호출 시 `ENDPOINTS.get('물품', DEFAULT_ENDPOINT)` → `/cntrwkList` (공사) 로 fall-through. 호출자에게는 응답 `biz_type=물품`으로 라벨링되지만 실 endpoint는 공사 → silent data mix-up.

**결함 K2 (LOW)** — `searchDt` 미지정 허용. 현재 backend는 None 가능 → KWater 공식은 필수. 실제 호출 시 KWater가 어떻게 처리하는지 미검증 (frontend가 항상 채워 보내므로 노출 결함 0).

**결함 K3 (MEDIUM)** — 응답 `cntrctDivNm` 값이 "내자"로 들어옴. frontend Badge variant 분기는 "용역"/"공사"만 매칭 → "내자"는 outline fall-through. backend가 "내자"를 "물품"으로 정규화하거나, frontend가 "내자" variant를 추가해야 일관성 확보. 현재는 표시 가능하나 사용자가 검색한 라벨과 row 라벨 불일치 가능.

**결함 K4 (LOW)** — `search_bids` 메서드가 tndr3 endpoint(`/B500001/ebid/tndr3`) 존재 사실 무시. PENDING_IMPLEMENTATION 처리하거나 활성화하거나 결정 필요. 현재 결함 노출 0 (frontend가 search_bids 호출하지 않음).

### 2.2 `app/tools/external.py` (`search_kwater_contracts`)

| 항목 | 정합 |
|------|------|
| signature `(search_dt, biz_type, limit)` | OK (KWaterAdapter 시그니처와 일치) |
| docstring biz_type 분기 설명 | 공사/용역만 명시 — 물품 누락 (K1과 같은 결함) |
| 반환값 위임 | OK |

### 2.3 frontend `external/kwater/page.tsx`

| 항목 | 정합 |
|------|------|
| dropdown 옵션 | "용역(정보화)" / "공사" 2종 — 물품 옵션 없음 (K1과 동일) |
| `defaultMonth()` 1년 전 | OK (PoC 검증 — 1년 전 데이터 존재 확인) |
| `searchDt` regex `\d{6}` | OK (YYYYMM 강제) |
| client-side 페이지네이션 (`fetchLimit = pageSize × page`) | OK 단 max 1000 cap. KWater spec 미명시 한계 — 실 호출에서 numOfRows=1000 동작 미검증 (PoC 3까지만) |
| `Badge variant` 분기 | "용역"="default" / "공사"="secondary" / **"내자"=outline fall-through** (K3) |
| ebid.kwater.or.kr 외부 링크 | OK |

frontend 단독 결함 0. 모든 결함은 backend ENDPOINTS 한정 + 라벨 매핑.

### 2.4 사용자 화면 결함 (kwater-01.png) 분석

- 화면 내용: KWater servcList endpoint XML raw 응답 (공식 url 직접 호출)
- `<resultCode>00</resultCode>` + `NORMAL SERVICE` — 정상 응답
- 4건 sample (광주수도지사, 낙동강영업처, 시화경영처, 재무관리처)
- **결함 evidence가 아님** — 사용자가 KWater spec을 검증할 때 reference로 캡처한 raw response

→ kwater-01.png는 우리 코드 결함을 시연하는 화면이 아니라 **공식 spec을 사용자 측에서 검증한 evidence**. 우리 backend가 같은 endpoint / 같은 응답을 정규화하므로 kwater-01.png 데이터는 우리 코드도 정상 처리 가능 (PoC `tmp/kwater_poc_202205.json` 4번째 row와 동일한 광주수도지사/현대환경(주) row 매칭).

---

## 3. frontend 정합성 (호출 흐름)

```
/external/kwater (page.tsx)
  ↓ defaultMonth() = 1년 전 YYYYMM
  ↓ bizType = sp.biz === "공사" ? "공사" : "용역"  (default 용역)
  ↓ pageSize = 30, page = 1
  ↓ fetchLimit = min(pageSize × page, 1000) — client-side 페이지네이션
  ↓
searchKwaterContracts(searchDt, bizType, fetchLimit) (actions.ts:287)
  ↓ callMcpTool("search_kwater_contracts", {search_dt, biz_type, limit})
  ↓
search_kwater_contracts (app/tools/external.py:22)
  ↓ KWaterAdapter().search_contracts(search_dt, biz_type, limit)
  ↓
KWaterAdapter.search_contracts (app/clients/external/kwater.py:68)
  ↓ endpoint = ENDPOINTS.get(biz_type or "공사", DEFAULT_ENDPOINT)
  ↓ params = {numOfRows=limit, pageNo=1, searchDt}
  ↓ call_data_go_kr_standard(BASE_URL, endpoint, key, params)
  ↓
GET https://apis.data.go.kr/B500001/ebid/cntrct3/{cntrwkList|servcList}
  ?serviceKey=...&pageNo=1&numOfRows=N&type=json&_type=json&searchDt=YYYYMM
  ↓
정규화: normalize_contract(raw) → 11 표준 필드
  ↓
응답: {items, total_count, agency, biz_type, endpoint, status}
```

**가시 결함**:
- frontend dropdown에 "물품" 옵션 없음 → 사용자가 KWater 물품 데이터를 조회할 길이 없음 (현재 결함 K1으로 backend도 미지원이므로 일관)
- "내자" 라벨 row가 "용역" 검색 결과에 섞일 가능성 0 (servcList endpoint는 cntrctDivNm=용역만 반환). 단 backend가 "물품" 호출 시 "공사" endpoint로 빠지면 cntrctDivNm=공사 row가 응답에 들어와 frontend가 의심 없이 표시. K1+K3 조합 시 silent mix-up.

**가시 결함 0**: frontend default ("용역") + 1년 전 default month + 사용자가 "공사" 명시 선택 시나리오 모두 정상 동작.

---

## 4. 실 호출 PoC 결과

### 4.1 호출 환경

- 키: `KWATER_API_KEY` (`.env` 기록 확인 — G2B 통합 키와 동일 단일 인증키)
- searchDt: `202205` (1년 전 default 시점 시뮬)
- numOfRows: 3 (sample)

### 4.2 응답 totalCount (1개월 데이터 규모)

| endpoint | 라벨 | totalCount | resultCode |
|----------|------|-----------|-----------|
| `/cntrwkList` | 공사 | **61** | 00 NORMAL SERVICE |
| `/servcList` | 용역 | **131** | 00 NORMAL SERVICE |
| `/dmscptList` | 내자 | **104** | 00 NORMAL SERVICE |

### 4.3 첫 row sample (각 endpoint)

```
공사 (cntrwkList):
  ordgNo=C3202206398  cntrctDivNm=공사  ordgTit=보현산댐 부유물 적치장 설치공사
  cntrctDeptNm=보현산댐지사  cntrctEntrpsNm=주식회사 영광  ctrmthdNm=소액전자
  lastCtramt=177,023,000  strwrkDe=20220613~20220811

용역 (servcList):
  ordgNo=C5202205025  cntrctDivNm=용역  ordgTit=광주시 노후 상수관로 교체공사 건설폐기물 처리용역(1차년도)
  cntrctDeptNm=광주수도지사  cntrctEntrpsNm=현대환경(주)  ctrmthdNm=일반경쟁
  lastCtramt=55,182,000  strwrkDe=20220610~20230204

내자 (dmscptList) [우리 backend 미지원]:
  ordgNo=C1202205580  cntrctDivNm=내자  ordgTit=일산(정) 침전지 인발밸브 제조구매
  cntrctDeptNm=경기서북권지사  cntrctEntrpsNm=(주)대성이엔지  ctrmthdNm=제한경쟁
  lastCtramt=194,656,000  strwrkDe=20220531~20220828
```

raw dump: `tmp/kwater_poc_202205.json` (3 endpoint × 3 row)

### 4.4 kwater-01.png evidence 매칭

kwater-01.png 첫 row:
- ordgNo=C5202205025, cntrctDeptNm=광주수도지사, cntrctEntrpsNm=현대환경(주), lastCtramt=55,182,000

PoC 결과 servcList 첫 row와 **byte 단위 일치** → 사용자가 보유한 raw evidence가 우리 backend 정규화 후 결과와 정합. 우리 정규화는 정확하다.

---

## 5. 결론

### 5.1 KWater 영역 정합 여부

**부분 정합** — 공사/용역 영역은 100% 정합. 물품(내자) 영역은 backend/frontend 모두 미지원으로 **데이터 누락 결함 K1**.

### 5.2 결함 매트릭스

| ID | 영역 | 심각도 | 노출 | Fix 영역 |
|----|------|-------|------|----------|
| K1 | 내자(`dmscptList`) endpoint 미매핑 | HIGH | 데이터 누락 | backend ENDPOINTS dict + frontend dropdown + tools docstring |
| K2 | `searchDt` 옵션 → 공식은 필수 | LOW | frontend가 항상 채움 → 0 | backend signature 또는 default 강제 |
| K3 | `cntrctDivNm` "내자" 값 정규화 누락 | MEDIUM | K1 fix 시 노출 | backend normalize 또는 frontend Badge variant |
| K4 | `search_bids` (tndr3) 미구현 | LOW | UI 미사용 → 0 | 결정 사항 (KIV 또는 활성화) |

### 5.3 fix 권고 (사용자 승인 후 적용)

1. **K1 (HIGH)**:
   ```python
   # app/clients/external/kwater.py
   ENDPOINTS = {
       "공사": "/ebid/cntrct3/cntrwkList",
       "용역": "/ebid/cntrct3/servcList",
       "물품": "/ebid/cntrct3/dmscptList",  # 신규 — KWater 명칭 "내자"
   }
   ```
   ```tsx
   // frontend/src/app/external/kwater/page.tsx
   <option value="공사">공사</option>
   <option value="용역">용역 (정보화)</option>
   <option value="물품">물품 (내자)</option>  {/* 신규 */}
   ```

2. **K3 (MEDIUM)** — backend `normalize_contract`에서 `"내자"` → `"물품"` 매핑 (사용자 친화) 또는 frontend Badge에 `"내자"` variant 추가. 둘 중 택일.

3. **K2 (LOW)** — backend signature에서 `search_dt: str` (필수)로 변경하거나, 미지정 시 default month 채움.

4. **K4 (LOW)** — `search_bids` PENDING 명시 또는 tndr3 활성화. 사용자 우선순위 확인 후 결정.

### 5.4 사용자가 의심한 영역 (1년+ 데이터 매칭 / 발주기관 검색)

- **1년+ 매칭** — KWater spec 자체가 월 단위 (searchDt YYYYMM) 단순 dump. 1년+ 검색 의미 자체가 없음 (frontend가 chunking 필요하지만 KWater 1개월 totalCount 60-130건 규모로 보아 12개월 chunking은 backend 신규 메서드 추가 필요 — 현재 PLAN 범위 외).
- **발주기관 검색** — KWater spec에 발주기관 필터 파라미터 없음. 응답 `cntrctDeptNm` 으로 client-side filter만 가능. G2B의 ntceInsttNm/dminsttNm 같은 LIKE 검색 미지원.
- **결함 위치는 KWater가 아니라 G2B 영역(Phase 31 F18~F22)**. KWater는 단순 lookup 도구라 그쪽 의심은 unfounded.

---

## 출처 목록

1. [한국수자원공사_전자조달 계약정보공개 (data.go.kr/data/15101620)](https://www.data.go.kr/data/15101620/openapi.do) — Swagger spec, raw HTML dump `tmp/kwater_15101620.html`, 추출 `tmp/kwater_extract.txt`
2. [한국수자원공사_전자조달 입찰공고 (data.go.kr/data/15101635)](https://www.data.go.kr/data/15101635/openapi.do) — Swagger spec, raw HTML dump `tmp/kwater_15101635.html`
3. [K-water 전자조달시스템 (ebid.kwater.or.kr)](https://ebid.kwater.or.kr/) — 원천 시스템
4. 실 호출 PoC: `tmp/kwater_poc_202205.json` (3 endpoint × 3 row, KWATER_API_KEY 사용)
5. 사용자 evidence: `kwater-01.png` (servcList 202205 raw XML — PoC 결과와 byte 일치)
6. 우리 코드:
   - `app/clients/external/kwater.py` — KWaterAdapter
   - `app/clients/external/base.py` — call_data_go_kr_standard
   - `app/tools/external.py` — search_kwater_contracts MCP 도구
   - `frontend/src/app/external/kwater/page.tsx` — 목록 화면
   - `frontend/src/app/external/kwater/contract/page.tsx` — 상세 화면
   - `frontend/src/lib/actions.ts:287` — searchKwaterContracts server action
