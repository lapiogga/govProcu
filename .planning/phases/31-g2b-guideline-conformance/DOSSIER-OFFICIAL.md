# DOSSIER — G2B 공식 지침 (Phase 31)

> 작성일: 2026-05-04
> 출처 자료: 공공데이터포털 (data.go.kr) 공식 OpenAPI 참고자료 docx (2025-04-10 개정 v1.2),
> 조달청 OpenAPI활용가이드 (PubDataOpnStdService v1.2, 2019-06)
> 작업 스코프: 자료 수집/분석. 코드 수정 금지.

---

## 0. 핵심 결론 (TL;DR)

1. **G2B BidPublicInfoService는 4분류 endpoint만 제공** — 공사(Cnstwk)/용역(Servc)/물품(Thng)/외자(Frgcpt). **"일반용역"/"기술용역" 분리 endpoint는 없다**. 그 구분은 응답 row의 `srvceDivNm` 필드 (값: 일반용역 / 기술용역)와 `ppswGnrlSrvceYn` (조달청일반용역여부 Y/N) 으로 알 수 있다.
2. **R-prefix 입찰공고번호는 차세대 나라장터 (2025-01-06 개통) 신번호체계**. 형식: `R + 년도(2) + 단계구분(2) + 순번(8) = 13자리`. 단계구분 — BK(입찰), TA(계약), DD(발주계획), BD(사전규격). 우리 코드 `R25BK00755515-000` 매칭 실패는 **R 형식 13자리 정상**, 따라서 우리 inqryDiv/날짜 추정 로직과 검색기간 분할 로직에 결함이 있다는 의미.
3. **inqryDiv는 endpoint마다 의미가 다르다** — 단순 4종 매핑이 아니라 endpoint별 1/2/3/4 의미가 다름. 핵심: **getBidPblancListInfoXxx (단일조회)는 1=등록일시(또는 입력일시) 검색, 2=공고번호 직접조회**. **getBidPblancListInfoXxxPPSSrch (검색조건)는 1=공고게시일시, 2=개찰일시**.
4. **검색기간 1개월 제한 확정** — `inqryBgnDt/inqryEndDt` 범위는 최대 1개월. 1년+ 데이터 조회는 1개월씩 chunk 분할 필요. 우리 코드 `chunk_date_range(max_days=31)` 적용 중.
5. **발주기관 LIKE 검색 가능** — PPSSrch endpoint는 `ntceInsttNm`(공고기관명), `dminsttNm`(수요기관명) 둘 다 request 파라미터로 받으며 "일부 입력시에도 조회 가능"이 명시됨. 단, `getBidPblancListInfoXxx` (PPS 미접미사) endpoint에는 이 파라미터가 없음.

---

## 1. BidPublicInfoService 업무구분 endpoint 매핑

### 1.1 base URL

```
운영: https://apis.data.go.kr/1230000/ad/BidPublicInfoService
```
(서비스 ID: `BidPublicInfoService`, 트래픽 30 TPS, 평균 500ms, max msg 4000B)

### 1.2 업무구분별 endpoint (4분류)

| 라벨 | endpoint suffix | 운영국문 |
|------|----------------|---------|
| 공사 | `getBidPblancListInfoCnstwk` | 입찰공고목록 정보에 대한 공사조회 |
| 용역 | `getBidPblancListInfoServc` | 입찰공고목록 정보에 대한 용역조회 |
| 물품 | `getBidPblancListInfoThng` | 입찰공고목록 정보에 대한 물품조회 |
| 외자 | `getBidPblancListInfoFrgcpt` | 입찰공고목록 정보에 대한 외자조회 |

**공사조회 + 검색조건 (PPSSrch) endpoint**:

| 라벨 | endpoint suffix |
|------|----------------|
| 공사 | `getBidPblancListInfoCnstwkPPSSrch` |
| 용역 | `getBidPblancListInfoServcPPSSrch` |
| 물품 | `getBidPblancListInfoThngPPSSrch` |
| 외자 | `getBidPblancListInfoFrgcptPPSSrch` |
| 기타 | `getBidPblancListInfoEtcPPSSrch` |

출처: 공식 참고자료 v1.2 docx, "오퍼레이션 목록" 표
URL: https://www.data.go.kr/data/15129394/openapi.do (참고문서 다운로드 — `조달청_OpenAPI참고자료_나라장터_입찰공고정보서비스_1.2.docx`, 2025-04-10 개정)

### 1.3 일반용역 / 기술용역 분리 — **endpoint 분리는 없다**

> 공식 참고자료 v1.2:
> `srvceDivNm` (용역구분명, 30자, 옵션) — "공고의 용역구분명으로 일반용역/기술용역으로 구분"
> `ppswGnrlSrvceYn` (조달청일반용역여부, 1자, 옵션) — "공고의 조달청일반용역여부(Y/N)"

이는 모두 **getBidPblancListInfoServc 응답 row의 필드**이며, 일반용역/기술용역을 사전 필터링할 endpoint나 request 파라미터는 제공되지 않는다. 결과로 받은 row에서 `srvceDivNm`을 보고 클라이언트 측에서 분류해야 한다.

**확인된 응답 sample**:
```xml
<bsnsDivNm>용역</bsnsDivNm>
<srvceDivNm>일반용역</srvceDivNm>
<ppswGnrlSrvceYn>N</ppswGnrlSrvceYn>
```

응답 `bsnsDivNm` 값 (실제 examples 9건에서 distinct): `{공사, 용역, 물품}` — **외자(Frgcpt) endpoint도 응답 bsnsDivNm은 별도가 아니라 외자 row 일 것**. 4분류 외에 별도 코드 없음.

### 1.4 별개 — `bsnsDivCd` 코드 (PubDataOpnStdService 한정)

`PubDataOpnStdService.getDataSetOpnStdScsbidInfo` (개방표준서비스) 에서만 `bsnsDivCd` 요청 파라미터 존재.

> "업무구분코드가 1이면 물품, 2면 외자, 3이면 공사, 5면 용역"
> 출처: 공식 활용가이드 PubDataOpnStdService v1.2 (2019-06)
> URL: https://2021-files.globaldatabarometer.org/173/obXkDMY-조달청_OpenAPI활용가이드_나라장터_공공데이터개방표준서비스_1.2.docx

(※ 4가 빠진 점 주의 — 5=용역. 코드값 4는 미사용 또는 reserved.)
이 코드는 BidPublicInfoService에서는 **사용되지 않는다** (BidPublicInfoService는 endpoint 분기 방식).

---

## 2. inqryDiv 의미 (endpoint별로 다름)

> 공식 참고자료 v1.2 docx에서 채택된 inqryDiv 매핑들 (총 7가지 패턴):

| 패턴 | 1 | 2 | 3 | 4 | 적용 endpoint |
|------|---|---|---|---|---------------|
| A | 등록일시 | 입찰공고번호 | 변경일시 | — | `getBidPblancListInfoCnstwk/Servc/Thng/Frgcpt` (단일/단건 조회) |
| B | 입력일시 | 입찰공고번호 | — | — | `getBidPblancListInfoXxxBsisAmount` (기초금액조회) |
| C | 변경일시 | 입찰공고번호 | — | — | `getBidPblancListInfoChgHstryXxx` (변경이력) |
| D | 공고게시일시 | 개찰일시 | — | — | `getBidPblancListInfoXxxPPSSrch` (검색조건) |
| E | 등록일시 | 입찰공고번호 | — | — | `getBidPblancListInfoLicenseLimit`, `PrtcptPsblRgn` 등 부속정보 |
| F | 공고게시일시 | 교부일시 | 입찰공고번호 | — | `getBidPblancListPPIFnlRfpIssAtchFileInfo` |
| G | 등록일시 | 개찰일시 | 공고일시 | 입찰공고번호 | `ScsbidInfoService getScsbidListSttusXxx` (Award) |

**중요한 1: 패턴**:
- "1: 등록일시" — getBidPblancListInfoXxx (단일조회) — 우리가 가장 많이 쓰는 endpoint
- "1: 공고게시일시" — getBidPblancListInfoXxxPPSSrch (검색조건)

**inqryDiv=2 의미 분기**:
- 단일조회 (`getBidPblancListInfoCnstwk` 등): 2 = 입찰공고번호 직접조회 → `bidNtceNo` 필수, 기간 불필요
- PPSSrch: 2 = 개찰일시 → 기간 필수, 다른 의미

**범위 제약**: 기간 검색시 `inqryBgnDt/inqryEndDt` 범위 **"최대 1개월"** (조회구분 1 또는 1,2,3 등 기간조회 패턴 모두 동일).

출처: 참고자료 v1.2 — 각 오퍼레이션 "요청 메시지 명세" inqryDiv 행
> 예: `inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분 | 1:등록일시, 2.입찰공고번호, 3.변경일시`
> 예: `inqryEndDt | "YYYYMMDDHHMM"(조회구분 1인 경우 필수이며 범위는 최대 1개월로 제한)`

---

## 3. inqryBgnDt / inqryEndDt 정책

- **형식**: `YYYYMMDDHHMM` (12자, 분 단위)
- **범위 제약**: **최대 1개월**. 1개월 초과 입력은 응답 데이터 결손/오류 가능성.
- **필수 조건**: 조회구분이 기간 패턴 (대개 1)이면 inqryBgnDt/inqryEndDt 둘 다 필수. 조회구분이 번호 패턴 (대개 2 또는 4)이면 `bidNtceNo` 필수, 기간 불필요.
- **R-prefix bid_no 1년+ 조회 방법**: bidNtceNo 직접 매칭 (inqryDiv=2)이면 기간 무관하게 단건 조회 가능. **단**, 단건 조회는 1건만 반환되므로 "최근 1년 내 R-prefix" 같은 검색에는 부적합. 1년 검색은 12개 chunk로 분할 후 합치기.

출처: 참고자료 v1.2 docx — "검색하고자하는 등록일시 조회종료일시 'YYYYMMDDHHMM'(조회구분 1인 경우 필수이며 범위는 최대 1개월로 제한)"

### 3.1 우리 코드 `_infer_period_from_bid_no` 의 결함 분석

현재 `app/tools/bid.py:18-37`:
```python
if len(s) >= 3 and s.startswith("R") and s[1:3].isdigit():
    yy = int(s[1:3])
    year = 2000 + yy if yy < 80 else 1900 + yy
    return f"{year}0101", f"{year}1231"  # ← 1년 통째로 반환 → 1개월 제한 위반
```

**문제**: 1년 범위로 inqryBgnDt/inqryEndDt 설정 → G2B 1개월 제한 초과 → 일부 month 응답 누락 가능.

**해결**: 이 함수를 None 반환으로 단순화 + bidNtceNo 모드는 **inqryDiv=2 + bidNtceNo만 보내면 됨** (기간 불필요). 또는 chunking 로직으로 1년을 12개월로 분할.

(기존 `chunk_date_range(max_days=31)` 호출이 있으니 1년 chunk 분할은 동작해야 하지만, F18 미매칭 원인은 별도 — 아래 5절 참조.)

---

## 4. 발주기관 파라미터 분리

### 4.1 응답 필드 (4종)

| 영문 | 국문 | 의미 |
|------|------|------|
| `ntceInsttCd` | 공고기관코드 | 7자, 행자부코드(없으면 조달청 부여 코드) |
| `ntceInsttNm` | 공고기관명 | 400자, "수요기관의 의뢰를 받아 공고하는 기관의 명" |
| `dminsttCd` | 수요기관코드 | 7자, 실제 수요기관 코드 |
| `dminsttNm` | 수요기관명 | 400자, "계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음" |

### 4.2 요청 파라미터 — PPSSrch endpoint만 지원

| Endpoint | ntceInsttNm | dminsttNm | bidNtceNm | indstrytyCd |
|----------|:-----------:|:---------:|:---------:|:-----------:|
| `getBidPblancListInfoCnstwk` (단일) | ❌ | ❌ | ❌ | ❌ |
| `getBidPblancListInfoCnstwkPPSSrch` (검색조건) | ✅ | ✅ | ✅ | ✅ |
| `getBidPblancListInfoServcPPSSrch` | ✅ | ✅ | ✅ | ✅ |
| `getBidPblancListInfoThngPPSSrch` | ✅ | ✅ | ✅ | ✅ |
| `getBidPblancListInfoFrgcptPPSSrch` | ✅ | ✅ | ✅ | ✅ |

**LIKE 매칭 가능**: 공식 참고자료 v1.2 명시 — "공고기관명 일부 입력시에도 조회 가능" / "수요기관명 일부 입력시에도 조회 가능" / "공고명 일부 입력시에도 조회 가능".

**즉**: 발주기관 LIKE 검색 동작 안 됨 = 우리 코드가 **PPSSrch endpoint를 안 쓰거나, PPSSrch에 ntceInsttNm/dminsttNm을 안 넘기고 있다**는 의미.

### 4.3 우리 코드 진단

`app/tools/bid.py:_resolve_bid_endpoints`는 **PPSSrch가 아닌 단일조회 endpoint만 사용** (`getBidPblancListInfoCnstwk`, `Servc`, `Thng`). 이 endpoint들은 ntceInsttNm 등 검색 파라미터를 지원하지 않으므로:

- 우리 코드 `inst_name=...` 인자는 G2B 호출시 **요청에 안 실리고**, 응답을 받아 **클라이언트측 substring 필터로만 동작**.
- 결과: G2B에서 1페이지 100건 받아 클라이언트 필터로 검색 → "국방부 국군재정관리단" 같은 발주기관이 1페이지 100건에 없으면 매칭 실패 (false negative).

**fix 권고**: PPSSrch endpoint를 inst_name이 있을 때 사용. 또는 page_size=999 + scan_pages 충분히 늘려 클라이언트 필터로 커버.

---

## 5. bid_no 형식 — R/G prefix 의미

### 5.1 차세대 나라장터 (2025-01-06 개통)

> 출처: 참고자료 v1.2 — "*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성"
> 단계구분: BK(입찰), TA(계약), DD(발주계획), BD(사전규격), BK(통합입찰)

- `R25BK00755515` = R(차세대) + 25(2025년) + BK(입찰) + 00755515(순번) = 13자리
- `R25TA00012345` = R + 25 + TA(계약) + 12345 + ... = 13자리
- `R26BK...` = 2026년 입찰

### 5.2 기존 시스템 (2025-01-06 이전)

> 출처: 참고자료 v1.2 — "조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며"
> 즉: `YYYYMM+5digits` = 11자리 (예: `20240500001`)

### 5.3 G-prefix?

공식 참고자료 v1.2 docx 내 `G` prefix 입찰번호는 발견되지 않았다. (예시 100여 건 모두 `R` 또는 11자리 숫자.)

**추정**: G-prefix는 일부 자체전자조달시스템 또는 특수 케이스 (예: 비공개/협상). **별도 추가 조사 필요** — 공식 자료에 G에 대한 명시 없음.

### 5.4 1년+ 데이터 조회 안 됨 (F18) 원인 추정

R-prefix는 차세대 시스템 (2025-01-06 ~)이므로 2025년 이후 데이터는 **무조건 R-prefix**로 응답 옴. 1년 이상 미매칭 원인 가설:
1. 우리 `_infer_period_from_bid_no`가 1년 통째 (`{year}0101`-`{year}1231`)로 inqryBgnDt 세팅 → 1개월 제한 위반 → G2B에서 일부 응답 결손.
2. 다만 우리는 `chunk_date_range(max_days=31)` 가 있어서 chunk되긴 함. 그러나 chunk와 endpoint 병렬 시 dedup key가 (bid_no, bid_ord)인지 확인 필요.
3. **단순 해결**: `inqryDiv=2 + bidNtceNo` 모드만 쓰면 기간 무관하게 단건 매칭됨. 우리 코드가 inqryDiv=2를 쓰는지, inqryDiv=1을 강제하는지 확인 필요.

---

## 6. AwardPublicInfoService (낙찰정보) 동일 정보

### 6.1 base URL

```
운영: https://apis.data.go.kr/1230000/as/ScsbidInfoService
```

### 6.2 endpoint 목록 (업무구분 4분류)

**낙찰목록** (`getScsbidListSttusXxx`):
- `getScsbidListSttusCnstwk` (공사)
- `getScsbidListSttusServc` (용역)
- `getScsbidListSttusThng` (물품)
- `getScsbidListSttusFrgcpt` (외자)

**개찰결과 목록** (`getOpengResultListInfoXxx`):
- `getOpengResultListInfoCnstwk` / `Servc` / `Thng` / `Frgcpt`

**검색조건 (PPSSrch)**:
- `getScsbidListSttusXxxPPSSrch` (4종)
- `getOpengResultListInfoXxxPPSSrch` (4종)

**예비가격 상세** (`PreparPcDetail`):
- `getOpengResultListInfoCnstwkPreparPcDetail` 등 4종

**기타**:
- `getOpengResultListInfoOpengCompt` (개찰완료)
- `getOpengResultListInfoFailing` (유찰)
- `getOpengResultListInfoRebid` (재입찰)

### 6.3 inqryDiv (Award 공통 패턴)

```
1. 등록일시
2. 공고일시
3. 개찰일시
4. 입찰공고번호
```

(또는 일부 endpoint는 1=공고일시, 2=개찰일시, 3=입찰공고번호 — endpoint마다 약간 다름.)

기간 조회 시 1,2,3 → 기간 필수. 4 → bidNtceNo 필수.

### 6.4 Award 도구 일반용역/기술용역 분리

Award 참고자료 v1.2에는 `srvceDivNm`/`ppswGnrlSrvceYn`/`일반용역`/`기술용역` 키워드 모두 0회. **Award 응답에는 용역구분 필드가 제공되지 않을 가능성** (또는 doc에 누락). 만약 frontend에서 일반용역/기술용역 필터가 필요하면, 입찰공고 (Bid) 결과의 srvceDivNm으로 join 후 필터하는 형태로 우회.

**우리 코드**:
- `app/tools/award.py:67` `_BIZ_DIV_MAP = {"공사": "Cnstwk", "용역": "Servc", "물품": "Thng", "외자": "Frgcpt"}` ✅ — 공식 4분류 일치.

---

## 7. Rate limit / 활용 정책

| 항목 | 값 | 출처 |
|------|----|------|
| 초당 최대 트랜잭션 | 30 TPS | 참고자료 v1.2 |
| 평균 응답 시간 | 500 ms | 참고자료 v1.2 |
| 최대 메시지 사이즈 | 4000 bytes | 참고자료 v1.2 |
| 일일 활용 (개발계정) | 1,000건/일 | data.go.kr 페이지 |
| 일일 활용 (운영계정) | 활용사례 등록 후 증가 신청 가능 | data.go.kr 페이지 |
| 데이터 시간범위 | 1995년 10월 ~ 2025년 1월 (doc 작성 시점 기준) | data.go.kr 페이지 |
| 업데이트 주기 | 실시간 | data.go.kr 페이지 |

URL: https://www.data.go.kr/data/15129394/openapi.do

---

## 8. 결론 — 우리 코드 fix 포인트

### 8.1 `app/tools/bid.py`

| F# | 결함 | 근본 원인 | 수정 권고 |
|----|------|----------|----------|
| F18 | R-prefix 1년+ 미매칭 | `_infer_period_from_bid_no`가 1년 범위로 setting → G2B 1개월 제한 위반 가능 | bid_notice_no 인자 받으면 **inqryDiv=2 + bidNtceNo만 보내고 기간 unset**. 또는 1년을 12개월 chunk로 강제 분할. |
| F19 | 발주기관명 LIKE 검색 안됨 | `getBidPblancListInfoXxx` (PPS 미접미사) endpoint가 ntceInsttNm 파라미터 미지원 | inst_name 인자 있을 때 **`getBidPblancListInfoXxxPPSSrch` 으로 endpoint 변경**. PPSSrch는 inqryDiv 의미가 다르니 inqryDiv 매핑도 endpoint별 분기. |
| F20 | 업종 "전체" 옵션 동작 안 함 | 코드상 None 시 3종 endpoint (Cnstwk/Servc/Thng) 병합 — **외자(Frgcpt) 누락** | `_resolve_bid_endpoints(None)` 에 Frgcpt endpoint 추가. 4종 병합. |
| F21 | 일반용역/기술용역 미분리 | G2B 응답 `bsnsDivNm`은 "용역" 단일 값. `srvceDivNm` 필드를 추출해서 일반용역/기술용역 구분 후 frontend 매핑 | 1) `_normalize_notice` 응답에 `srvce_div = raw.get("srvceDivNm")` 추가. 2) frontend 업종 dropdown은 5분류 (공사/물품/일반용역/기술용역/외자)로 변경 시, biz_type="일반용역" 입력은 **endpoint=Servc + 클라이언트 필터 srvceDivNm=="일반용역"** 처럼 구현. |

### 8.2 `app/tools/bid.py:_BIZ_DIV_MAP` 의 의미

```python
_BIZ_DIV_MAP = {"공사": "1", "용역": "2", "물품": "3"}
```
이 map은 코드를 grep해 봐야 사용처가 명확하지만, 만약 `bsnsDivCd` 요청 파라미터로 쓰고 있다면 **잘못된 매핑**이다 (BidPublicInfoService는 `bsnsDivCd` 미사용). PubDataOpnStdService에서만 1=물품, 2=외자, 3=공사, 5=용역. 코드 내 사용처 확인 후 제거 또는 정정.

### 8.3 `app/tools/award.py`

```python
_BIZ_DIV_MAP = {"공사": "Cnstwk", "용역": "Servc", "물품": "Thng", "외자": "Frgcpt"}
```
✅ **공식 endpoint 4분류와 일치**. 변경 불필요.

단, 만약 일반용역/기술용역 분리 필요 시 (F21 confirm), frontend 분류 추가 시 award 도구도 응답 row의 `srvceDivNm` (만약 제공된다면) 또는 입찰공고 join으로 후처리 필요.

### 8.4 frontend 업종 dropdown

> 사용자 보고: "나라장터에서 업무구분이 공사/물품/일반용역/기술용역으로 분리 표시"

이는 G2B 웹 UI의 업종 필터 표현. API endpoint 측면에서는:
- **G2B 자체는 공사/용역/물품/외자 4종 endpoint** + 응답 row `srvceDivNm`(일반용역/기술용역) 필드로 분리 처리.
- **frontend에서 5종(공사/물품/일반용역/기술용역/외자) dropdown 구현은**: 일반용역/기술용역 선택 시 → endpoint=`Servc` + 응답 `srvceDivNm` 필드로 클라이언트 필터.

### 8.5 keyword vs ntceInsttNm 별도 파라미터 분리 권고

현재 `search_bid_notices`는 `keyword` (제목 부분일치) + `inst_name`(발주기관) 둘 다 클라이언트측 substring 필터. PPSSrch endpoint를 채택하면:
- `keyword` → `bidNtceNm` request param
- `inst_name` → `ntceInsttNm` request param (또는 dminsttNm을 OR 처리할지 결정)
- `region` → `prtcptPsblRgnNm` 또는 `rgnLmtBidLocplcNm` 응답 필드 (request param 없음, 클라이언트 필터)

이렇게 하면 G2B 서버측 페이징/검색을 활용해 응답건수를 적절히 줄일 수 있음.

---

## 출처 목록

1. **공공데이터포털 — 조달청 나라장터 입찰공고정보서비스**
   URL: https://www.data.go.kr/data/15129394/openapi.do
   참고문서: `조달청_OpenAPI참고자료_나라장터_입찰공고정보서비스_1.2.docx` (2025-04-10 개정 v1.2)
   다운로드 URL: `https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003623980&fileDetailSn=1`
   로컬 파일: `tmp/bid_pub_info_ref.docx` (365 KB)

2. **공공데이터포털 — 조달청 나라장터 낙찰정보서비스**
   URL: https://www.data.go.kr/data/15129397/openapi.do
   참고문서: `조달청_OpenAPI참고자료_나라장터_낙찰정보서비스` v1.2
   다운로드 URL: `https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003578187&fileDetailSn=1`
   로컬 파일: `tmp/award_ref.docx` (557 KB)

3. **조달청 OpenAPI활용가이드 — 나라장터 공공데이터개방표준서비스 v1.2 (2019-06)**
   URL: https://2021-files.globaldatabarometer.org/173/obXkDMY-조달청_OpenAPI활용가이드_나라장터_공공데이터개방표준서비스_1.2.docx
   로컬 파일: `tmp/g2b_guide.docx` (335 KB)
   주: PubDataOpnStdService 전용. BidPublicInfoService와 별개 서비스.

4. **차세대 나라장터 개통 안내**
   URL: https://www.koit.co.kr/news/articleView.html?idxno=127146 (정보통신신문 2025-01-06)
   기사 요지: "차세대 나라장터·종합쇼핑몰 2025년 1월 6일 개통" (시범 개통).

5. **gurumii.com — 나라장터 API 데이터 수집** (실제 호출 example)
   URL: https://gurumii.com/python/example-g2b-api-research-data
   유용한 점: getBidPblancListInfoServc 와 PPSSrch 호출 예시. inqryDiv=1 사용.

6. **jungi.net — 조달청 오픈 API 공공자료 가이드 PDF**
   URL: https://www.jungi.net/fileDownload?file_url=...3.%20조달청%20오픈%20API%20공공자료.pdf
   로컬 파일: `tmp/jungi_g2b.pdf` (1.8 MB)
   주: 텍스트 추출 시 일부 깨짐. 보조용.

---

## 부록 — 오퍼레이션 전체 목록 (BidPublicInfoService 25종)

```
getBidPblancListInfoCnstwk                 # 공사 단일
getBidPblancListInfoServc                  # 용역 단일
getBidPblancListInfoThng                   # 물품 단일
getBidPblancListInfoFrgcpt                 # 외자 단일
getBidPblancListInfoEtc                    # 기타공고 단일
getBidPblancListInfoCnstwkPPSSrch          # 공사 검색조건
getBidPblancListInfoServcPPSSrch           # 용역 검색조건
getBidPblancListInfoThngPPSSrch            # 물품 검색조건
getBidPblancListInfoFrgcptPPSSrch          # 외자 검색조건
getBidPblancListInfoEtcPPSSrch             # 기타 검색조건
getBidPblancListInfoCnstwkBsisAmount       # 공사 기초금액
getBidPblancListInfoServcBsisAmount        # 용역 기초금액
getBidPblancListInfoThngBsisAmount         # 물품 기초금액
getBidPblancListInfoChgHstryCnstwk         # 공사 변경이력
getBidPblancListInfoChgHstryServc          # 용역 변경이력
getBidPblancListInfoChgHstryThng           # 물품 변경이력
getBidPblancListInfoLicenseLimit           # 면허제한정보
getBidPblancListInfoPrtcptPsblRgn          # 참가가능지역정보
getBidPblancListInfoThngPurchsObjPrdct     # 물품 구매대상물품
getBidPblancListInfoServcPurchsObjPrdct    # 용역 구매대상물품
getBidPblancListInfoFrgcptPurchsObjPrdct   # 외자 구매대상물품
getBidPblancListInfoEorderAtchFileInfo     # e발주 첨부파일정보
getBidPblancListPPIFnlRfpIssAtchFileInfo   # 혁신장터 최종제안요청서 첨부파일
getBidPblancListBidPrceCalclAInfo          # 입찰가격산식A정보
getBidPblancListEvaluationIndstrytyMfrcInfo # 평가대상주력분야
```

(PubDataOpnStdService와 BidPublicInfoService는 별개. PubDataOpnStdService는 입찰/낙찰/계약 통합 표준 데이터 3종 endpoint만 제공.)
