# DOSSIER — G2B (나라장터) 입찰공고정보서비스 실사용 사례 (Phase 31)

> 수집 일시: 2026-05-04 / 작성: research subagent
> 4 결함 (F18 R-prefix 1년+ 빈결과 / F19 발주기관 LIKE / F20 업종 '전체' / F21 일반용역·기술용역 분리)에 대해
> 공식 가이드 외 **실 코드/블로그**에서 발견한 동작 패턴 정리

---

## 0. 가장 중요한 1차 발견 (TL;DR)

**① 우리가 사용해야 할 endpoint는 PPSSrch 계열이지 기본 List 계열이 아니다.**

`getBidPblancListInfoServc` (기본) 와 `getBidPblancListInfoServcPPSSrch` (PPS검색) 는 **검색 가능 파라미터가 완전히 다르다**:

| Endpoint | 검색 가능 필드 |
|---|---|
| `getBidPblancListInfoServc` (그리고 Cnstwk, Thng, Frgcpt, Etc) | `bidNtceNo` 1개 (이름/기관/업종 검색 불가) |
| `getBidPblancListInfoServcPPSSrch` (그리고 PPSSrch suffix) | **20개 필드: bidNtceNm, ntceInsttNm/Cd, dminsttNm/Cd, indstrytyCd/Nm, dtilPrdctClsfcNo, prtcptLmtRgnCd/Nm, presmptPrceBgn/End, refNo, bidClseExcpYn, intrntnlDivCd, prcrmntReqNo, masYn …** |

따라서 **공고명·발주기관·업종·세부품명·지역·예가범위** 등 우리 UI 필터를 백엔드 API에 위임하려면 **반드시 `*PPSSrch` endpoint를 사용해야 한다**. 이게 F19/F20에 직접 적용된다.

**② 업무구분(일반용역/기술용역/공사/물품/외자/기타)은 endpoint 자체로 분리된다.**

PPS 가이드 인용:
> "각 오퍼레이션은 업무구분별(물품, 용역, 공사, 외자 등)로 구분되어 있으며 입찰공고정보의 업무구분에 맞는 오퍼레이션을 이용하여야 정상 응답받으실 수 있습니다."
> 출처: data.go.kr/data/15129394/openapi.do (서비스 description)

→ "용역" 안에서 **일반용역 vs 기술용역**이 별개 endpoint로 더 분리되지는 않는다. 둘 다 `getBidPblancListInfoServc(PPSSrch)` 하나에 들어오고, 응답 필드 `용역구분명` (또는 `bsnsDivNm` / `prdctClsfcNoNm`)으로 구별된다. 이게 F21에 직접 적용된다.

**③ inqryDiv 코드값은 endpoint마다 의미가 다르다 (Narabot 실 코드 주석으로 확인).**

Narabot/NaraJang_scheduler.py 라인 52-58 (실코드 주석 인용):
```python
# 입찰공고 endpoint:
inqryDiv1 = '?inqryDiv=1'  # 조회구분 (1:공고게시일시 2:입찰공고번호) 입찰공고는 1이 기본
# 개찰결과 endpoint:
inqryDiv2 = '?inqryDiv=2'  # 조회구분 (1:공고게시일시 2:개찰일시 3:입찰공고번호) 개찰이후는 2가 기본
inqryDiv3 = '?inqryDiv=3'  # 위와 동일 명세
inqryDiv4 = '?inqryDiv=4'  # 계약현황: 1:계약체결일자, 2:확정계약번호, 3:요청번호, 4:공고번호
```
출처: https://github.com/tobornot2b/Narabot/blob/main/NaraJang_scheduler.py (실 라이브 코드 주석)

→ **입찰공고정보서비스의 inqryDiv는 1=공고게시일시 / 2=입찰공고번호 (정확히 2값)**.
→ "개찰일 기준" 조회는 **입찰공고정보서비스에는 없고 ScsbidInfoService(낙찰정보서비스)에 있다** (별도 service). 우리 코드가 "개찰일 기준" 으로 inqryDiv를 바꿔서 R-prefix 1년+ 데이터를 회복하려는 시도는 **입찰공고정보서비스에서는 불가능**.

---

## 1. 실제 호출 endpoint + 파라미터 사례

### 사례 A — Narabot (실 GitHub 활성 프로젝트, 텔레그램 봇)

- **출처**: https://github.com/tobornot2b/Narabot/blob/main/NaraJang_scheduler.py
- **사용 base URL**: `http://apis.data.go.kr/1230000/BidPublicInfoService04` (※ **04 suffix** 사용 — 우리 코드는 suffix 없음)
- **operation**: `getBidPblancListInfoThngPPSSrch01` (※ **01 suffix** — 더 신선한 변형)
- **파라미터 조합 (오늘 입찰공고 검색)**:
  ```
  ?inqryDiv=1                                    # 공고게시일시 기준
  &inqryBgnDt=YYYYMMDD0000
  &inqryEndDt=YYYYMMDD2359
  &pageNo=1
  &numOfRows=100
  &bidNtceNm=교복                                  # 키워드(공고명) 검색
  &type=json
  &ServiceKey=...
  ```
- **발견**:
  - URL `BidPublicInfoService04` (우리는 `BidPublicInfoService` 사용) → **버전 차이가 응답 필드/안정성에 영향 줄 수 있음** (재확인 권장).
  - 키워드(`bidNtceNm`)별로 **URL을 별도 생성**해서 하나하나 호출 (G2B는 OR 검색 미지원으로 추정 — 단일 키워드만 가능).
  - **검색기간은 1일 단위로 매일 호출** (배치 형태). "1년 한방 호출"은 시도하지 않음.
- **인용 코드** (라인 60-62):
  ```python
  inqryBgnDt = '&inqryBgnDt=' + datetime.today().strftime('%Y%m%d') + '0000'
  inqryEndDt = '&inqryEndDt=' + datetime.today().strftime('%Y%m%d') + '2359'
  ```

### 사례 B — nyaongnyaong 블로그 (PHP/Python 입문 가이드)

- **출처**: https://nyaongnyaong.com/26 (2020-03-12 게시, "공공데이터포털 API 사용 방법(feat. 나라장터)")
- **operation**: `getBidPblancListInfoServcPPSSrch` ✅ (우리가 가야 할 endpoint)
- **인용 URL**:
  ```
  http://apis.data.go.kr/1230000/BidPublicInfoService/getBidPblancListInfoServcPPSSrch
    ?inqryDiv=1
    &inqryBgnDt=202003010000
    &inqryEndDt=202003122359
    &pageNo=1
    &numOfRows=100
    &type=json
    &arrange=B                          # ← 미지원/미사용으로 추정
    &bidNtceNm=홈페이지
    &ServiceKey=...
  ```
- **발견**:
  - **inqryDiv=1 (공고게시일시 기준)** + **bidNtceNm 키워드**로 12일 범위 한 번에 조회 (12일 가능 입증)
  - 사용자 평: "공고명 '홈페이지' 검색 → 정상 응답"

### 사례 C — gurumii (Python 연구용역 데이터 수집 튜토리얼)

- **출처**: https://gurumii.com/python/example-g2b-api-research-data
- **operation**: `getBidPblancListInfoServcPPSSrch` (용역 PPS검색)
- **인용 URL**:
  ```
  http://apis.data.go.kr/1230000/BidPublicInfoService/getBidPblancListInfoServcPPSSrch
    ?inqryDiv=1
    &type=json
    &indstrytyCd=1169                   # ← 업종코드 (서비스/연구 관련)
    &inqryBgnDt=202002250000
    &inqryEndDt=202002252359
    &pageNo=1
    &numOfRows=999
    &ServiceKey=...
  ```
- **발견**:
  - **`indstrytyCd=1169`** 단독으로 업종 필터 가능 (★ F20 "업종 전체" 결함 직결).
  - 즉 **'전체' 업종 = `indstrytyCd` 미전달**, **특정 업종 = 코드값 1개 전달**.
  - `numOfRows=999` 까지 1회 가능 (1000건 한도).

### 사례 D — sadam.media (연구용역 데이터 수집)

- **출처**: https://www.sadam.media/e51d12e4-f302-4c39-9561-c3d022d1a9d8 (직접 fetch 실패 — 검색 결과 인용)
- **API 한도 인용**: "API allows requests for up to 1,000 data points at once, and to request more than 1,000 data points, you must repeatedly request the data."
- **endpoint**: 나라장터 입찰공고정보서비스 → 용역 부분 검색.
- **검색기간 패턴**: 일/주/월 단위 분할 호출 후 합산.

---

## 2. 업무구분(bsnsDivCd / bsnsDivNm) 응답값 실 사례

### 2.1 endpoint 자체로 1차 분리 (확정 사실)

data.go.kr swagger 명세 추출:

| Endpoint suffix | 업무구분 | 검색조건 description (인용) |
|---|---|---|
| `Cnstwk` | 공사 | "검색조건에 공고게시일시, 개찰일시 범위, 공고기관, 수요기관, 참조번호 등을 입력하여 나라장터의 입찰공고번호, 공고명, 발주기관, 수요기관, 계약체결방법명 등 **공사부분**의 입찰공고정보를 조회함" |
| `Thng` | 물품 | "…**물품부분**의 입찰공고정보를 조회함" |
| `Servc` | 용역 (일반용역+기술용역) | "…**용역부분**의 입찰공고정보를 조회함" |
| `Frgcpt` | 외자 | "…**외자부분**의 입찰공고정보를 조회함" |
| `Etc` | 기타공고 | "…**기타공고**정보를 조회" |

### 2.2 용역 = 일반용역 + 기술용역 (응답 필드로 구별, ★ F21 직결)

- **공식 description (조달청 PPS, 검색결과 인용)**: "기술용역과 일반용역은 나라장터에서 업무편의상 구분되는데, 기술용역은 건설기술진흥법, 엔지니어링기술진흥법, 건축사법 등 여러 법률에 의해 정의되고 있다."
- **응답 필드** (data.go.kr swagger): `용역구분명`, `업무구분명`, `prdctClsfcNoNm` (물품분류번호명) — bsnsDivCd/bsnsDivNm 자체는 swagger output에 명시되지 않음 (응답 일부에서만 등장).
- **결론**: 우리 코드에서 "기술용역만" 또는 "일반용역만" 분리 조회는 다음 두 방식:
  - **(권장) 응답 후 client-side 필터링** — Servc endpoint로 받은 후 `용역구분명`이 "기술용역" 인지로 분리.
  - **(대안) `dtilPrdctClsfcNo` 활용** — 기술용역에 해당하는 분류번호 화이트리스트로 필터링.
- **블로거 인용 (검색결과)**: "나라장터 시스템은 표준연도/조달업무구분(물품, 일반용역, 기술용역, 공사)별 검색 기능을 제공" — UI 레벨에서는 4분 (물품/일반용역/기술용역/공사) 이지만 API는 3분 (Thng/Servc/Cnstwk) → **API 호출 후 클라이언트 분리 필수**.

---

## 3. 발주기관(ntceInsttNm) 검색 패턴 (★ F19 직결)

### 3.1 PPSSrch endpoint에서 ntceInsttNm·ntceInsttCd 둘 다 지원

data.go.kr swagger 추출 (PPSSrch endpoint 파라미터):
- `ntceInsttNm` (공고기관명, optional)
- `ntceInsttCd` (공고기관코드, optional)
- `dminsttNm` (수요기관명, optional)
- `dminsttCd` (수요기관코드, optional)

### 3.2 LIKE 부분일치 vs 정확일치 — 결정적 단서 부족, 추정만 가능

- **공식 가이드**: ntceInsttNm 매칭 방식 명시 안 됨 (swagger description에 "공고기관" 만 표기)
- **실 코드 사례 부재**: GitHub 검색에서 ntceInsttNm 사용 사례를 직접 찾지 못함 (Narabot도 사용 안 함; 키워드는 bidNtceNm만 사용).
- **블로거 / G2B UI 추정**: 나라장터 자체 UI는 "발주기관: 키워드 입력" 으로 부분일치 LIKE처럼 동작 (g2bplus.kr 등 3rd-party 검색 서비스에서도 부분일치 사용).
- **권고**: 우리 코드는 **`ntceInsttNm`에 짧은 핵심 키워드(예: "한국수자원공사")** 를 전달하여 LIKE처럼 동작하는지 1회 PoC 호출로 검증 (응답 결과의 ntceInsttNm 필드와 비교). 정확일치만 지원하면 수요기관명(`dminsttNm`)도 동시에 전달하는 방식 또는 클라이언트 사후 필터로 우회.

### 3.3 별도 발주기관 검색 API 존재 — `사용자정보서비스` (데이터셋 15129466)

- **출처**: https://www.data.go.kr/data/15129466/openapi.do (검색결과 등장)
- **이름**: 조달청_나라장터 사용자정보 서비스
- **용도**: 기관 목록/코드 마스터 데이터 조회 가능 (단, 우리는 입찰공고 검색용이 아니라 코드 룩업으로 활용 가능).

---

## 4. R-prefix bid_no 1년+ 데이터 조회

### 4.1 R-prefix 의미 (검색결과 종합)

- **공식 명시 미발견** — data.go.kr / pps.go.kr / 블로그 어디에도 "R-" 접두어의 명시적 정의는 없음.
- **실무 추정** (lee-v.com 재공고 가이드, neobid.org 등 종합):
  - 입찰이 **유찰/무효** 되어 동일 내용을 다시 공고하는 절차 = "재공고"
  - 재공고 시 입찰공고번호가 **변경**됨 → "R-" 접두어가 재공고 식별자로 사용될 가능성이 높음 (Re-announcement)

### 4.2 입찰공고정보서비스에 "개찰일 기준" 옵션은 **없다**

- data.go.kr swagger 검증: `getBidPblancListInfo*` (그리고 `*PPSSrch`) 의 `inqryDiv`는 **공고게시일시 기준**만 (값 1) 또는 **입찰공고번호 기준** (값 2). 개찰일 기준은 미지원.
- **개찰일 기준 조회**는 **별도 서비스** `ScsbidInfoService` (낙찰정보) 에서만 가능 — Narabot 코드 라인 53 주석:
  ```python
  inqryDiv2 = '?inqryDiv=2'  # 조회구분 (1:공고게시일시 2:개찰일시 3:입찰공고번호)
  # 위 주석은 ScsbidInfoService(낙찰조회)용
  ```
- **결론 (★ F18)**: R-prefix 입찰공고를 **공고일 기준 1년 전부터** 조회하려면 단순히 `inqryBgnDt`/`inqryEndDt`를 1년 범위로 늘리면 되며, **개찰일 기준 옵션 변경은 입찰공고서비스에서 불가능**.
- **검색기간 1년+ 분할 호출 패턴 (실 운영 사례)**: gurumii / sadam / Narabot 모두 **일 단위 또는 월 단위로 분할 후 누적** 방식 (1회 1000건 한도 회피). 1년 단일 호출 사례 발견 못 함.

---

## 5. 분류번호 기준 조회 (dtilPrdctClsfcNo 활용)

### 5.1 endpoint 자체는 별도 없음 — PPSSrch에 파라미터로 통합

- 우리가 처음에 가정한 `getPrdctClsfcNoPblancListInfoXxx` 같은 별도 endpoint는 **존재하지 않음** (data.go.kr swagger 전체 추출 결과).
- 대신 `getBidPblancListInfoServcPPSSrch` / `ThngPPSSrch` / `FrgcptPPSSrch` 안에 **`dtilPrdctClsfcNo` (세부품명분류번호) 파라미터**가 있음.

### 5.2 세부품명번호(dtilPrdctClsfcNo) 명세

- **자릿수**: 10자리 (물품분류번호 8자리 + 세부 2자리)
- **용도** (블로그 인용): "나라장터 입찰 참가자격 등록, 다수공급자계약 구매입찰공고, 중소기업자간 경쟁제품 지정 공고 등 물자 구매와 관련된 다양한 용도에 활용"
- **출처**: 조달청 PPS 공지 (https://www.pps.go.kr/kor/content.do?key=00179) / sabbatical92.com 블로그
- **실 사용 사례**: 발견 못 함 (대부분 블로그는 `bidNtceNm` 키워드 또는 `indstrytyCd` 업종코드 위주).

---

## 6. Rate limit / 데이터 신선도

### 6.1 운영 시간 제한

- **출처**: https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000003915
- **공지 제목**: "[조달청]Open API 이용시간 제한 안내 (이용가능 시간: 18:00 …)"
- **추정**: 일정 시간대(18시 이후 등)에 운영 차단 가능성 — Narabot도 `end_date='YYYY-MM-DD 18:00:00'` 으로 스케줄러 종료 시각 설정 (라인 670 부근).

### 6.2 처리량 / 한도

- **1회 호출 한도**: numOfRows ≤ 1000 (Narabot 100, gurumii 999, sadam 1000 명시).
- **일일 트래픽**: 개발계정 기본 한도 있음 (error_code 22 인용: "일일 활용건수가 초과함(활용건수 증가 필요)" → 운영계정 변경신청 필요).
- **에러 06**: "날짜Format 에러" — `YYYYMMDDHHMM` (12자리) 형식 엄수 (사례 모두 `+0000`/`+2359` 패턴).
- **에러 07**: "입력범위값 초과" — numOfRows>1000 또는 검색범위 너무 넓을 때 발생 가능.

### 6.3 응답 필드 신선도

- 응답 필드 `등록일시(rgstDt)`, `공고게시일시`, `입력일시(inptDt)`는 **실시간 업데이트** (Narabot은 4시간 주기 polling).
- **변경이력**: `getBidPblancListInfoChgHstryServc/Cnstwk/Thng` 별도 endpoint로 변경 이력 조회 가능 (우리는 미사용).

---

## 7. 결론 — 우리 코드 적용 권고

### F18 (R-prefix 1년+ 빈결과)
- **원인 추정**: `getBidPblancListInfoServc` (기본 List, 검색은 `bidNtceNo`만) 사용 시 R-prefix 매칭이 잘못된 endpoint를 거치고 있을 가능성. **PPSSrch + bidNtceNo + 1년 범위 inqryBgnDt/EndDt** 조합으로 재시도.
- **개찰일 기준 조회는 입찰공고정보서비스에 없다** — ScsbidInfoService 별도 호출 필요. 우리가 이 가설로 코드를 짰다면 즉시 폐기.
- 1년+ 데이터는 **월 단위 분할 누적**이 표준 패턴 (1회 1000건 한도).

### F19 (발주기관 LIKE)
- **반드시 PPSSrch endpoint 사용** — 기본 endpoint는 `ntceInsttNm` 파라미터 자체가 없음.
- LIKE 부분일치 여부는 1회 PoC 호출로 검증 권장 (예: `ntceInsttNm=한국수자원` 부분 키워드로 응답에 "한국수자원공사" 포함되는지 확인).
- 정확일치만 지원 시 → `ntceInsttCd` 코드 + 사용자정보서비스 마스터 lookup, 또는 클라이언트 사후 필터링.

### F20 (업종 '전체')
- **`indstrytyCd` 파라미터를 URL에서 완전히 제거**하면 '전체' 가 된다 (gurumii 사례: 코드 전달 시 필터 / 미전달 시 무필터 입증).
- 우리 코드가 `indstrytyCd=` (빈 값) 또는 `indstrytyCd=ALL` 을 보내고 있다면 **에러 06/07** 가능 — 빈 값 제거 처리 검토.

### F21 (일반용역·기술용역 분리)
- **API endpoint 레벨에서는 분리 불가** (둘 다 `Servc` endpoint에 합쳐짐).
- **응답 필드 `용역구분명` (또는 `업무구분명`/`prdctClsfcNoNm`)으로 클라이언트 사후 분리** — 가장 확실한 패턴.
- 추가 정밀화 원하면 `dtilPrdctClsfcNo` 또는 `indstrytyCd` 화이트리스트로 분리 (단, 매핑 테이블 필요).

---

## 출처 일람 (URL)

1. **공식 명세**: https://www.data.go.kr/data/15129394/openapi.do (조달청_나라장터 입찰공고정보서비스 — swagger UI)
2. **공식 명세**: https://www.data.go.kr/data/15129466/openapi.do (사용자정보 서비스 — 기관 마스터)
3. **공식 명세**: https://www.data.go.kr/data/15129397/openapi.do (낙찰정보서비스 ScsbidInfoService — 개찰일 기준 조회)
4. **공식 명세**: https://www.data.go.kr/data/15058815/openapi.do (공공데이터개방표준서비스 — 통합 데이터)
5. **PPS 공지**: https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000003915 ([조달청]Open API 이용시간 제한)
6. **GitHub 실코드**: https://github.com/tobornot2b/Narabot — 텔레그램 봇, BidPublicInfoService04, ScsbidInfoService 모두 사용
7. **GitHub error codes**: https://github.com/tobornot2b/Narabot/blob/main/error_code.md (코드 01~32 의미)
8. **블로그 (Python 입문)**: https://nyaongnyaong.com/26 (getBidPblancListInfoServcPPSSrch 사용)
9. **블로그 (연구용역)**: https://gurumii.com/python/example-g2b-api-research-data (indstrytyCd=1169 활용)
10. **블로그 (연구용역)**: https://www.sadam.media/e51d12e4-f302-4c39-9561-c3d022d1a9d8
11. **블로그 (분석)**: https://teddylee777.github.io/pandas/pandas-bidding/ (입찰공고 ML 예측, 데이터셋 활용)
12. **블로그 (재공고)**: https://lee-v.com/179 (재공고 절차 — R-prefix 추정 근거)
13. **블로그 (세부품명)**: https://sabbatical92.com/entry/조달청-나라장터-물품-품명-... (dtilPrdctClsfcNo 10자리)
14. **PPS 공식**: https://www.pps.go.kr/kor/content.do?key=00179 (세부품명번호 활용 안내)
15. **GitHub 라이브러리**: https://github.com/WooilJeong/PublicDataReader (참고 — Procurement 모듈 별도 확인 권장)
16. **G2B 본 사이트**: https://www.g2b.go.kr/

---

## 부록 — data.go.kr 입찰공고정보서비스 endpoint 22종 전수 + 검색 가능 파라미터

(본 DOSSIER 작성 시 swagger 추출 결과 자체)

```
getBidPblancListBidPrceCalclAInfo                   -> [bidNtceNo, inqryBgnDt, inqryDiv, inqryEndDt, ...]
getBidPblancListEvaluationIndstrytyMfrcInfo         -> [bidNtceNo, inqryBgnDt, inqryDiv, inqryEndDt, ...]
getBidPblancListInfoChgHstryCnstwk                  -> [bidNtceNo, ...]
getBidPblancListInfoChgHstryServc                   -> [bidNtceNo, ...]
getBidPblancListInfoChgHstryThng                    -> [bidNtceNo, ...]
getBidPblancListInfoCnstwk                          -> [bidNtceNo, inqryBgnDt, inqryDiv, inqryEndDt, numOfRows, pageNo, serviceKey, type]
getBidPblancListInfoCnstwkBsisAmount                -> [bidNtceNo, ...]
getBidPblancListInfoCnstwkPPSSrch                   -> [bidClseExcpYn, bidNtceNm, dminsttCd, dminsttNm, indstrytyCd, indstrytyNm, inqryBgnDt, inqryDiv, inqryEndDt, intrntnlDivCd, ntceInsttCd, ntceInsttNm, numOfRows, pageNo, prcrmntReqNo, presmptPrceBgn, presmptPrceEnd, prtcptLmtRgnCd, prtcptLmtRgnNm, refNo, serviceKey, type]
getBidPblancListInfoEorderAtchFileInfo              -> [bidNtceNo, ...]
getBidPblancListInfoEtc                             -> [bidNtceNo, inqryBgnDt, inqryDiv, inqryEndDt, ...]
getBidPblancListInfoEtcPPSSrch                      -> [bidClseExcpYn, bidNtceNm, dminsttNm, inqryBgnDt, inqryDiv, inqryEndDt, ntceInsttCd, ntceInsttNm, numOfRows, pageNo, presmptPrceBgn, presmptPrceEnd, refNo, serviceKey, type]
getBidPblancListInfoFrgcpt                          -> [bidNtceNo, ...]
getBidPblancListInfoFrgcptPPSSrch                   -> [bidClseExcpYn, bidNtceNm, dminsttCd, dminsttNm, dtilPrdctClsfcNo, indstrytyCd, indstrytyNm, inqryBgnDt, inqryDiv, inqryEndDt, intrntnlDivCd, masYn, ntceInsttCd, ntceInsttNm, numOfRows, pageNo, prcrmntReqNo, presmptPrceBgn, presmptPrceEnd, prtcptLmtRgnCd, prtcptLmtRgnNm, refNo, serviceKey, type]
getBidPblancListInfoFrgcptPurchsObjPrdct            -> [bidNtceNo, bidNtceOrd, ...]
getBidPblancListInfoLicenseLimit                    -> [bidNtceNo, bidNtceOrd, ...]
getBidPblancListInfoPrtcptPsblRgn                   -> [bidNtceNo, bidNtceOrd, ...]
getBidPblancListInfoServc                           -> [bidNtceNo, inqryBgnDt, inqryDiv, inqryEndDt, numOfRows, pageNo, serviceKey, type]
getBidPblancListInfoServcBsisAmount                 -> [bidNtceNo, ...]
getBidPblancListInfoServcPPSSrch                    -> [bidClseExcpYn, bidNtceNm, dminsttCd, dminsttNm, dtilPrdctClsfcNo, indstrytyCd, indstrytyNm, inqryBgnDt, inqryDiv, inqryEndDt, intrntnlDivCd, ntceInsttCd, ntceInsttNm, numOfRows, pageNo, prcrmntReqNo, presmptPrceBgn, presmptPrceEnd, prtcptLmtRgnCd, prtcptLmtRgnNm, refNo, serviceKey, type]
getBidPblancListInfoServcPurchsObjPrdct             -> [bidNtceNo, bidNtceOrd, ...]
getBidPblancListInfoThng                            -> [bidNtceNo, inqryBgnDt, inqryDiv, inqryEndDt, numOfRows, pageNo, serviceKey, type]
getBidPblancListInfoThngBsisAmount                  -> [bidNtceNo, ...]
getBidPblancListInfoThngPPSSrch                     -> [bidClseExcpYn, bidNtceNm, dminsttCd, dminsttNm, dtilPrdctClsfcNo, indstrytyCd, indstrytyNm, inqryBgnDt, inqryDiv, inqryEndDt, intrntnlDivCd, masYn, ntceInsttCd, ntceInsttNm, numOfRows, pageNo, prcrmntReqNo, presmptPrceBgn, presmptPrceEnd, prtcptLmtRgnCd, prtcptLmtRgnNm, refNo, serviceKey, type]
getBidPblancListInfoThngPurchsObjPrdct              -> [bidNtceNo, bidNtceOrd, ...]
```

→ **요약: 검색은 PPSSrch 5종 (Cnstwk/Etc/Frgcpt/Servc/Thng) 으로만, bidNtceNo 단건 조회는 기본 List 5종으로 분리 사용.**
