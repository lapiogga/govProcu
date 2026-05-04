# POC — G2B 실 호출 raw evidence (Phase 31)

> **목적**: DOSSIER-OFFICIAL/PRACTICE 기반 가설을 backend 우회 직접 httpx 호출 raw payload로 검증.
>
> **실행일**: 2026-05-04 (KST), `python .planning/phases/31-g2b-guideline-conformance/poc_g2b.py`
>
> **호출 환경**:
> - base URL: `https://apis.data.go.kr/1230000/ad`
> - serviceKey: `.env::G2B_KEY_BID` (마스킹 — 산출물에 평문 노출 금지)
> - HTTP 클라이언트: `httpx.AsyncClient`, timeout=60s, `Accept: application/json`
> - resultCode 검증: 모든 호출 `header.resultCode = "00"` ("정상")
>
> **raw dump**: `.planning/phases/31-g2b-guideline-conformance/poc_raw/*.json` (요청+응답 페어, 12 파일)
> **요약 dump**: `poc_raw/_summary.json`

---

## PoC 1 — `getBidPblancListInfoServcPPSSrch` + `ntceInsttNm` LIKE

### 호출
```
GET /BidPublicInfoService/getBidPblancListInfoServcPPSSrch
?ServiceKey=<masked>&type=json
&numOfRows=10&pageNo=1
&inqryDiv=1
&inqryBgnDt=202604010000&inqryEndDt=202604302359
&ntceInsttNm=조달청
```

### 응답 raw (excerpt)
```json
{
  "header": {"resultCode": "00", "resultMsg": "정상"},
  "body": {
    "totalCount": 2336,
    "items": [
      {"ntceInsttNm": "조달청 인천지방조달청", "...": "..."},
      {"ntceInsttNm": "조달청", "...": "..."},
      {"ntceInsttNm": "조달청 대전지방조달청", "...": "..."},
      {"ntceInsttNm": "조달청 부산지방조달청", "...": "..."},
      {"ntceInsttNm": "조달청", "...": "..."}
    ]
  }
}
```

### 결론
- LIKE 동작: ✅ **부분일치 매칭 확인**
- evidence: 첫 5건 중 5건이 모두 query="조달청"을 부분일치로 포함. 본청("조달청") + 지방청("조달청 인천지방조달청", "조달청 대전지방조달청", "조달청 부산지방조달청") 혼재 → LIKE.
- totalCount=2336 (2026-04 한 달, 일반용역 PPSSrch + ntceInsttNm=조달청)

---

## PoC 2 — `getBidPblancListInfoServcPPSSrch` + `dminsttNm` LIKE

### 호출
```
GET .../getBidPblancListInfoServcPPSSrch
?ServiceKey=<masked>&type=json
&numOfRows=10&pageNo=1&inqryDiv=1
&inqryBgnDt=202604010000&inqryEndDt=202604302359
&dminsttNm=국방부
```

### 응답 raw (excerpt)
```json
{
  "header": {"resultCode": "00", "resultMsg": "정상"},
  "body": {
    "totalCount": 63,
    "items": [
      {"dminsttNm": "국방부 전쟁기념사업회"},
      {"dminsttNm": "국방부"},
      {"dminsttNm": "국방부 국군재정관리단"},
      {"dminsttNm": "국방부 전쟁기념사업회"},
      {"dminsttNm": "국방부 국군의무사령부"}
    ]
  }
}
```

### 결론
- LIKE 동작: ✅ **부분일치 매칭 확인**
- evidence: 본부("국방부") + 산하기관("국방부 전쟁기념사업회", "국방부 국군재정관리단", "국방부 국군의무사령부") 혼재.
- **사용자 보고 케이스 적중**: "국방부 / 국군재정관리단" (PLAN.md F19 종료조건) 응답에 포함.
- totalCount=63 (2026-04 한 달, 일반용역 PPSSrch + dminsttNm=국방부)

---

## PoC 3 — `bidNtceNm` LIKE (공고명 부분일치)

### 호출
```
GET .../getBidPblancListInfoServcPPSSrch
?ServiceKey=<masked>&type=json
&numOfRows=10&pageNo=1&inqryDiv=1
&inqryBgnDt=202604010000&inqryEndDt=202604302359
&bidNtceNm=정보화
```

### 응답 raw (excerpt)
```json
{
  "header": {"resultCode": "00", "resultMsg": "정상"},
  "body": {
    "totalCount": 52,
    "items": [
      {"bidNtceNm": "치안정책연구소 빅데이터 플랫폼 글로벌 사이버 보안을 위한 정보화전략계획(ISP) 수립 위탁용역"},
      {"bidNtceNm": "2026년 중소기업 정보화수준 조사·분석 사업"},
      {"bidNtceNm": "2026년 지역정보화 사업계획 수립 및 분석 보고"},
      {"bidNtceNm": "전자투표사업단 AI 전환을 위한 정보화전략계획 수립"},
      {"bidNtceNm": "2026년 라이프주기별 정보화수준 용역"}
    ]
  }
}
```

### 결론
- LIKE 동작: ✅ **부분일치 매칭 확인**
- evidence: 5건 모두 "정보화"를 공고명 내부에 포함 ("정보화전략계획", "정보화수준", "지역정보화" 등). 정확일치가 아니라 부분일치.
- totalCount=52

---

## PoC 4 — 단일조회 endpoint `inqryDiv=2 + bidNtceNo` (R-prefix)

### 호출 (5종 endpoint 순차 시도, target_no=R25BK00755515)
```
GET .../getBidPblancListInfoServc        ?inqryDiv=2&bidNtceNo=R25BK00755515  → totalCount=1, 매칭
GET .../getBidPblancListInfoCnstwk       ?inqryDiv=2&bidNtceNo=R25BK00755515  → totalCount=0
GET .../getBidPblancListInfoThng         ?inqryDiv=2&bidNtceNo=R25BK00755515  → totalCount=0
GET .../getBidPblancListInfoFrgcpt       ?inqryDiv=2&bidNtceNo=R25BK00755515  → totalCount=0
GET .../getBidPblancListInfoEtc          ?inqryDiv=2&bidNtceNo=R25BK00755515  → totalCount=0
```

(주의: `inqryBgnDt/inqryEndDt` 미전달, 기간 unset 상태 호출 — 정상 200 응답)

### 응답 raw (Servc 매칭 1건 — 사용자 보고 사례 정확 적중)
```json
{
  "header": {"resultCode": "00", "resultMsg": "정상"},
  "body": {
    "totalCount": 1,
    "items": [
      {
        "bidNtceNo": "R25BK00755515",
        "bidNtceNm": "2025년도 역사지리정보DB 구축사업",
        "ntceInsttNm": "조달청 서울지방조달청",
        "dminsttNm": "교육부 국사편찬위원회",
        "srvceDivNm": "일반용역",
        "bsnsDivNm": null,
        "ppswGnrlSrvceYn": "Y",
        "bidNtceDt": "2025-04-01 11:04:36",
        "presmptPrce": "101818182",
        "asignBdgtAmt": "112000000"
      }
    ]
  }
}
```

### 결론
- inqryDiv=2 단건 모드 동작: ✅ **기간 unset에도 200 OK + 정확 매칭**
- 사용자 보고 케이스 적중 (PLAN.md F18 종료조건):
  - `bidNtceNo=R25BK00755515` ✅
  - `bidNtceNm="2025년도 역사지리정보DB 구축사업"` (역사지리정보DB) ✅
  - `ntceInsttNm="조달청 서울지방조달청"` ✅
  - `srvceDivNm="일반용역"` ✅ (PLAN F21 종료조건)
- 5종 endpoint 중 **Servc 1개에서만** 매칭 (Cnstwk/Thng/Frgcpt/Etc는 totalCount=0). PLAN 3.2의 "5종 단일조회 endpoint 병렬" 설계 합당 — 외부 호출자는 어느 부서 사업인지 모르므로 5종 fan-out 후 어느 하나에서 hit.
- **R-prefix 1년+ 매칭이 가능했던 이유**: inqryDiv=2 + bidNtceNo만 전달 시 G2B는 기간 제약 적용하지 않음. 즉 `_infer_period_from_bid_no` 1년 통째 폴백은 불필요 (PLAN F18 결론 검증).
- **note**: PPSSrch 응답과 달리 단건조회 endpoint(`getBidPblancListInfoServc`)는 `dminsttNm`에 진짜 수요기관(`교육부 국사편찬위원회`)이 들어옴. PLAN F19 fan-out 전략 정합.

---

## PoC 5 — `getBidPblancListInfoServcPPSSrch` 응답 필드 dump

### 호출 (필터 없이 1개월)
```
GET .../getBidPblancListInfoServcPPSSrch
?ServiceKey=<masked>&type=json
&numOfRows=10&pageNo=1&inqryDiv=1
&inqryBgnDt=202604010000&inqryEndDt=202604302359
```

### 응답 raw (첫 5건의 핵심 필드 dump)
```json
{
  "header": {"resultCode": "00", "resultMsg": "정상"},
  "body": {
    "totalCount": 22862,
    "items": [
      {
        "bidNtceNo": "R26BK01433053",
        "bidNtceNm": "KPS위성 1호기 탑재체 FM 하네스 설계 및 제작 용역",
        "ntceInsttNm": "한국항공우주연구원",
        "dminsttNm": "한국항공우주연구원",
        "bsnsDivNm": null,
        "srvceDivNm": "일반용역",
        "ppswGnrlSrvceYn": "N"
      },
      {
        "bidNtceNo": "R26BK01433996",
        "bidNtceNm": "연안경제·관광 정책지원 모니터링 플랫폼 운영사업",
        "ntceInsttNm": "한국해양수산개발원",
        "dminsttNm": "한국해양수산개발원",
        "bsnsDivNm": null,
        "srvceDivNm": "일반용역",
        "ppswGnrlSrvceYn": "N"
      },
      "... (3 more rows, all srvceDivNm='일반용역', ppswGnrlSrvceYn='N')"
    ]
  }
}
```

### 결론
- `srvceDivNm` 필드 존재: ✅ "**일반용역**" 값 5/5 도착 (검색 endpoint가 Servc만 단일이라 표본은 일반용역 단일값)
- `ppswGnrlSrvceYn` 필드 존재: ✅ "Y"/"N" 값 도착 (PoC4 일반용역 단건 응답: "Y", 본 표본: "N" 다양 — 변별력 있음)
- `bsnsDivNm` 필드: ❌ **PPSSrch 응답에서 항상 null** (5/5 null) — 단건조회와 다름
- 다른 신뢰 가능 필드: `bidNtceNo`, `bidNtceNm`, `ntceInsttNm`, `dminsttNm` 모두 정상 채워짐
- **PLAN F21 검증**: srvceDivNm 응답 활용 가능 → backend `_normalize_notice` 추가 권장 합당.
- **DOSSIER §4 필드 명시 PASS** (srvceDivNm, ppswGnrlSrvceYn)
- 1개월 일반용역 totalCount=22862 — pagination 필수 (numOfRows 100 max → 229 페이지)

---

## PoC 6 — `indstrytyCd` 파라미터 (업종)

### 호출 (필터 없음 vs `indstrytyCd=1169`)
```
A: GET .../getBidPblancListInfoServcPPSSrch ?inqryDiv=1&inqryBgnDt=...&inqryEndDt=...
B: GET .../getBidPblancListInfoServcPPSSrch ?inqryDiv=1&inqryBgnDt=...&inqryEndDt=...&indstrytyCd=1169
```

### 응답 raw (excerpt — 비교)
```json
A (no filter):  {"header": {"resultCode": "00"}, "body": {"totalCount": 22862, ...}}
B (indstrytyCd=1169): {"header": {"resultCode": "00"}, "body": {"totalCount": 3425, "items": [...]}}

B 첫 1건 발췌 (industry-related 키만):
{
  "indstrytyLmtYn": "Y",
  "srvceDivNm": "일반용역"
}
```

### 결론
- `indstrytyCd` 파라미터 동작: ✅ **서버측 필터링 적용**
  - 미전달: totalCount=22862
  - 전달(`indstrytyCd=1169`): totalCount=3425
  - 차이 19,437건 → 필터 active (filter_active=true)
- 응답 items에는 `indstrytyCd` 필드는 직접 안 들어옴, 대신 `indstrytyLmtYn="Y"` (업종 제한 여부 플래그) 도착.
- 결과 화면에 업종명 표시하려면 별도 매핑(사용자정보서비스 OpenAPI 또는 사전 ETL — PLAN F22 옵션 A/C)이 필요.

---

## PoC 7 — `ntceInsttNm` + `dminsttNm` 동시 전달 (AND vs OR)

### 호출 (3 케이스 비교)
```
A: ntceInsttNm=조달청            → totalCount=2336
B: dminsttNm=국방부              → totalCount=63
C: ntceInsttNm=조달청 + dminsttNm=국방부 → totalCount=19
```

### 응답 raw (C 케이스 첫 3건)
```json
{
  "header": {"resultCode": "00", "resultMsg": "정상"},
  "body": {
    "totalCount": 19,
    "items": [
      {"ntceInsttNm": "조달청 서울지방조달청", "dminsttNm": "국방부"},
      {"ntceInsttNm": "조달청 서울지방조달청", "dminsttNm": "국방부"},
      {"ntceInsttNm": "조달청 서울지방조달청", "dminsttNm": "국방부"}
    ]
  }
}
```

### 결론
- 동시 전달 시 동작: ✅ **AND (intersection)**
  - C(19) ≤ min(A=2336, B=63) → 두 조건 동시 만족만 반환
  - 첫 3건 모두 ntceInsttNm에 "조달청"·dminsttNm에 "국방부" 둘 다 매칭
- **PLAN F19 backend 설계 함의**:
  - 사용자 발화 #46 "공고기관 == 수요기관 동일 대부분, 단일 input 통합" — 단일 input 1개 키워드를 ntceInsttNm/dminsttNm **둘 중 한쪽**으로만 보내거나, **두 호출 fan-out 후 union** 처리 필요.
  - 절대 **단일 호출에 두 파라미터 동시 전달**해서는 안 됨 (AND이므로 결과 너무 좁아짐).
- 권장: backend가 동일 keyword를 두 endpoint 호출로 fan-out → client-side union → bidNtceNo 기반 dedup.

---

## 종합 결론

| PoC | 결과 | 핵심 evidence | DOSSIER/PLAN 항목 검증 |
|-----|------|----------------|------------------------|
| 1 | LIKE OK (ntceInsttNm) | "조달청 인천지방조달청" 매칭 (q="조달청") | DOSSIER §4 LIKE 명시 ✅, PLAN F19 PPSSrch 직접 전달 ✅ |
| 2 | LIKE OK (dminsttNm) | "국방부 국군재정관리단" 매칭 (q="국방부") | PLAN F19 종료조건 (국방부 / 국군재정관리단 매칭) ✅ |
| 3 | LIKE OK (bidNtceNm) | "정보화전략계획", "정보화수준" 매칭 (q="정보화") | PLAN F19 keyword→bidNtceNm 직접 전달 ✅ |
| 4 | inqryDiv=2 + bidNtceNo 단건 OK | R25BK00755515 / 역사지리정보DB / 서울지방조달청 / 일반용역 정확 적중. 5종 중 Servc 1개만 hit | PLAN F18 종료조건 ✅, _infer_period_from_bid_no 폐기 합당 ✅ |
| 5 | srvceDivNm/ppswGnrlSrvceYn 응답 도착, bsnsDivNm=null | "일반용역", "Y/N" 채워짐 / PPSSrch는 bsnsDivNm null | PLAN F21 BidNoticeSummary 필드 추가 합당 ✅ |
| 6 | indstrytyCd 서버측 필터 active | 22862 → 3425 | PLAN F22/F23 indstrytyCd 자동완성 기반 필터링 가능 ✅ |
| 7 | ntceInsttNm + dminsttNm = AND | A=2336, B=63, C=19 (≤min) | PLAN F19 fan-out 두 호출 + union 필수 ✅ |

### 핵심 발견
1. **PPSSrch endpoint는 LIKE 매칭 (3가지 텍스트 필드: ntceInsttNm, dminsttNm, bidNtceNm 모두)** — 부분일치 검색 직접 전달 가능. 단건조회 endpoint와는 별개의 검색 채널.
2. **단건조회(inqryDiv=2 + bidNtceNo)는 기간 unset에도 정상** — `_infer_period_from_bid_no` 1년 통째 폴백 로직은 불필요 (PLAN F18 폐기 결정 합당).
3. **사용자 보고 케이스(R25BK00755515) 5종 endpoint 중 Servc 1개에서만 매칭** — 외부 호출자는 사업 분류를 모르므로 PLAN 3.2 5종 fan-out 설계가 정확.
4. **`srvceDivNm`("일반용역"/"기술용역")은 PPSSrch + 단건조회 모두에 도착, `bsnsDivNm`은 PPSSrch에서 항상 null** — 일반용역/기술용역 분리 표시는 srvceDivNm으로만 가능 (PLAN F21).
5. **두 기관 파라미터 동시 전달은 AND** — 단일 input 통합 UX 위해 backend가 fan-out + union으로 OR 행동 모방 필수 (PLAN F19 보강).
6. **resultCode = "00" 모든 호출** — API 키, base URL, 파라미터 명세 모두 정합.

### 산출물 위치
- 본 보고서: `C:\Users\User\GovProcu\.planning\phases\31-g2b-guideline-conformance\POC-G2B.md`
- raw payload dumps: `C:\Users\User\GovProcu\.planning\phases\31-g2b-guideline-conformance\poc_raw\*.json`
- 실행 스크립트: `C:\Users\User\GovProcu\.planning\phases\31-g2b-guideline-conformance\poc_g2b.py`
