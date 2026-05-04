# Phase 31 — G2B 지침 정합성 (PLAN)

> **트리거**: 발화 #38~#44 (사용자 검증 라운드 + UI 사양 확정)
>
> **목표**: G2B 공식 지침 (DOSSIER-OFFICIAL) + 실 사용 사례 (DOSSIER-PRACTICE) 근거로 6 결함 (F18~F23) fix.
>
> **자료 근거**:
> - 공식 참고자료 v1.2 docx (2025-04-10 개정) — `tmp/bid_pub_info_ref.docx`
> - Award 참고자료 v1.2 — `tmp/award_ref.docx`
> - 차세대 나라장터 (2025-01-06 개통) 신번호체계
> - 사용자 화면 검증 evidence (err-021~035)

## 1. 결함 매트릭스 (3 DOSSIER + raw evidence 통합)

| ID | 화면 | Root Cause | Fix 영역 | 우선 | 자료근거 |
|----|------|-----------|----------|------|----------|
| F18 | /bids/trace | `_infer_period_from_bid_no` 1년 통째 → 1개월 제한 위반. inqryDiv=1만 사용 | backend bid.py | **P0** | DOSSIER-OFFICIAL §3, POC-G2B #4 (R25BK00755515 inqryDiv=2 적중) |
| F19 | /bids 검색 | 단일조회 endpoint는 ntceInsttNm/dminsttNm 미지원. client-side filter만 | backend bid.py | **P0** | DOSSIER-OFFICIAL §4, POC-G2B #1·#2 (LIKE 부분일치 적중, "국방부 국군재정관리단" raw 매칭) |
| F20/F24 | /bids 검색 | `_resolve_bid_endpoints` 외자 endpoint 누락 + indstrytyCd 빈 값 전달 위험 | backend bid.py | **P0** | DOSSIER-OFFICIAL §1.2, POC-G2B #6 (indstrytyCd 22862→3425 필터 적중), DOSSIER-LAW F24 |
| F21 | /bids 화면 | 일반용역/기술용역 응답 필드(srvceDivNm) 미활용 + PPSSrch에서 bsnsDivNm null | backend bid.py + frontend | **P0** | DOSSIER-OFFICIAL §1.3, POC-G2B #5 (srvceDivNm="일반용역" raw 적중) |
| F22 | /bids 검색 | 발주기관 자동완성 부재 (2자 LIKE trigger) + AND 동작 회피 fan-out 필요 | backend 신설 + frontend | P0 | err-035 사양, POC-G2B #7 (ntceInsttNm + dminsttNm 동시 = AND, fan-out 필수) |
| F23 | /bids 화면 | 업무구분/업무여부/업종 3계층 분리 부재 | frontend bids/page.tsx | P1 | err-031~034 사양, 발화 #43~#44 |
| F25 | /bids/trace | 시행령 제36조 입찰공고 필수항목 12개 중 7~8개 미노출 (입찰참가자격/낙찰자결정방법/입찰서 제출방법/개찰 일시·장소/입찰보증금 등) | frontend trace/page.tsx | P1 | DOSSIER-LAW F25 |
| F26 | /bids 화면 | 응답 ntceInsttNm + dminsttNm 두 필드 모두 노출 (사용자 #46/#47 단일 input UX 유지 + 결과 표시 분리) | frontend bids/page.tsx | P1 | DOSSIER-LAW F26, 발화 #46~#47 |
| F27 | /qualification | 라벨 비표준 ("응찰가" → "입찰금액", "기초금액" → "예정가격") | frontend qualification/page.tsx | P1 | DOSSIER-LAW F27 |
| F28 | /bids/trace | 6단계 명칭 비표준 (사전규격 → **사전규격공개**, 본 공고 → **입찰공고**, 낙찰 → **낙찰자 결정**, 계약 → **계약 체결**) | frontend trace/page.tsx | P1 | DOSSIER-LAW F28 |
| K1 | /external/kwater | 물품(내자) endpoint `/dmscptList` 누락. 코드 주석 잘못. 1개월 104건 응답 가능 | backend kwater.py | P2 (별도 phase) | DOSSIER-KWATER K1 |

## 2. 활성/비활성 분류 (발화 #44 반영)

| 차원 | 활성 | 비활성 |
|------|------|--------|
| 업무구분 | 물품 / 일반용역 / 기술용역 / 공사 / 기타 (5) | 민간 |
| 업무여부 | 외자 (1) | 비축, 리스 |
| 업종 | indstrytyCd 자동완성 (2,915종) | — |

## 3. backend 변경 (bid.py)

### 3.1 endpoint 매핑 — PPSSrch 5종

```python
_BID_ENDPOINTS_PPSSRCH = {
    "공사":   "/BidPublicInfoService/getBidPblancListInfoCnstwkPPSSrch",
    "용역":   "/BidPublicInfoService/getBidPblancListInfoServcPPSSrch",   # 일반용역+기술용역 통합
    "물품":   "/BidPublicInfoService/getBidPblancListInfoThngPPSSrch",
    "외자":   "/BidPublicInfoService/getBidPblancListInfoFrgcptPPSSrch",
    "기타":   "/BidPublicInfoService/getBidPblancListInfoEtcPPSSrch",
}

_BID_ENDPOINTS_DETAIL = {  # 단건조회 (inqryDiv=2 + bidNtceNo)
    "공사":   "/BidPublicInfoService/getBidPblancListInfoCnstwk",
    "용역":   "/BidPublicInfoService/getBidPblancListInfoServc",
    "물품":   "/BidPublicInfoService/getBidPblancListInfoThng",
    "외자":   "/BidPublicInfoService/getBidPblancListInfoFrgcpt",
    "기타":   "/BidPublicInfoService/getBidPblancListInfoEtc",
}
```

### 3.2 search_bid_notices 모드 분기 (F18 + F19 + F20)

```python
async def search_bid_notices(...):
    # 모드 1: bid_notice_no 단건 매칭 (F18)
    if inp.bid_notice_no:
        # inqryDiv=2 + bidNtceNo만, 기간 unset
        # 5종 단일조회 endpoint 병렬 (어느 하나에서 매칭)
        for endpoint in _BID_ENDPOINTS_DETAIL.values():
            params = {"inqryDiv": "2", "bidNtceNo": inp.bid_notice_no}
            body = await client.call(endpoint, ...)
            ...
    # 모드 2: 검색 (keyword/inst_name/biz_type 등)
    else:
        # PPSSrch endpoint + inqryDiv=1 (공고게시일시) + 1개월 chunking
        endpoints = _resolve_bid_endpoints_ppssrch(inp.biz_type)  # F20: 외자 포함 5종
        for endpoint in endpoints:
            params = {
                "inqryDiv": "1",  # 공고게시일시
                "inqryBgnDt": ..., "inqryEndDt": ...,  # 1개월 chunk
                "pageNo": ..., "numOfRows": ...,
            }
            # F19: 검색 파라미터 직접 전달
            if inp.keyword: params["bidNtceNm"] = inp.keyword
            if inp.inst_name: params["ntceInsttNm"] = inp.inst_name  # 또는 dminsttNm
            if inp.indstrytyCd: params["indstrytyCd"] = inp.indstrytyCd
            ...
```

### 3.3 F20 — 외자 endpoint 추가

`_resolve_bid_endpoints_ppssrch(None)` → 5종 (Cnstwk/Servc/Thng/Frgcpt/Etc) 병합.
`_resolve_bid_endpoints_ppssrch("외자")` → Frgcpt 단일.

### 3.4 F21 — `srvceDivNm` 응답 필드 추가

```python
def _normalize_notice(raw: dict) -> BidNoticeSummary:
    return BidNoticeSummary(
        ...
        biz_type=raw.get("bsnsDivNm"),       # "용역" 단일값
        srvce_div=raw.get("srvceDivNm"),     # "일반용역" / "기술용역" — 신규
        ppsw_gnrl_yn=raw.get("ppswGnrlSrvceYn"),  # Y/N — 신규
        ...
    )
```

frontend가 srvce_div 활용해 일반용역/기술용역 표시 + 필터 가능.

### 3.5 `_infer_period_from_bid_no` 폐기 또는 단순화

기존 1년 통째 반환 로직 제거. bid_notice_no 단건 모드는 inqryDiv=2 + bidNtceNo 직접 → 기간 불필요.

### 3.6 `_BIZ_DIV_MAP = {"공사": "1", "용역": "2", "물품": "3"}` 점검

BidPublicInfoService는 `bsnsDivCd` 미사용. 이 매핑이 어디서 쓰이는지 grep 후 제거 또는 정정 (PrespecEndpoints에 일부 사용 — 정확 의미 검증 필요).

### 3.7 search_agencies (F22 — 별도 도구 신설)

```python
async def search_agencies(query: str, limit: int = 30) -> dict:
    """발주/수요기관 LIKE 검색 (2자 이상).
    
    구현 옵션:
    - 옵션 A: 사용자정보서비스 OpenAPI (data.go.kr/data/15129466) 활용
    - 옵션 B: search_bid_notices로 ntceInsttNm/dminsttNm LIKE → distinct 추출
    - 옵션 C: 사전 ETL로 기관 마스터 캐시 + Redis SET 검색
    """
```

## 4. frontend 변경 (bids/page.tsx)

### 4.1 검색 form 재구성 (F23)

```tsx
<form>
  <Input name="keyword" placeholder="공고명 (예: 정보화 시스템 구축)" />
  
  <Section label="업무구분">
    <CheckboxGroup name="biz_types" multi>
      <Checkbox value="공사">공사</Checkbox>
      <Checkbox value="물품">물품</Checkbox>
      <Checkbox value="일반용역">일반용역</Checkbox>
      <Checkbox value="기술용역">기술용역</Checkbox>
      <Checkbox value="기타">기타</Checkbox>
    </CheckboxGroup>
  </Section>
  
  <Section label="업무여부">
    <Toggle name="include_frgcpt" label="외자 포함" />
  </Section>
  
  <Section label="업종 (indstrytyCd)">
    <AutocompleteInput
      name="indstryty_cd"
      minLength={2}
      onSearch={debounced(searchIndustries)}
    />
  </Section>
  
  <Section label="발주기관">
    {/* 발화 #46: 공고기관 == 수요기관 동일 대부분 → 단일 input 통합.
        backend가 ntceInsttNm + dminsttNm 두 파라미터로 LIKE 시도. */}
    <AutocompleteInput
      name="inst_name"
      minLength={2}
      onSearch={debounced(searchAgencies)}
      placeholder="발주기관 (공고기관/수요기관 통합, 2자 이상)"
    />
  </Section>
  
  <DateRange from={...} to={...} />
  <Button type="submit">검색</Button>
</form>
```

### 4.2 일반용역/기술용역 표시

응답의 `srvce_div_nm`을 결과 테이블 컬럼으로 노출. dropdown에서 "일반용역" 선택 시 client-side filter `srvce_div_nm === "일반용역"` 적용.

## 5. 검증 절차 (Phase 29 L1~L5 계승 + L6 데이터 정합성)

| 단계 | 검증 |
|------|------|
| L1 | Python import + TypeScript 컴파일 0 에러 |
| L2 | 단위 함수 (endpoint 매핑 / 응답 정규화) |
| L3 | backend MCP 직접 호출 raw payload 검증 — **DOSSIER 명시 필드 (srvceDivNm, ntceInsttNm, ppswGnrlSrvceYn) 응답에 실제로 들어오는지** |
| L4 | 사용자 case retrieval — F18(R25BK00755515-000), F19(국방부 국군재정관리단), F21(역사지리정보DB 일반용역) |
| L5 | frontend 화면 검증 — 3계층 dropdown + 자동완성 + 결과 테이블 srvce_div 컬럼 |
| **L6** | **G2B 응답값 vs 나라장터 웹 UI 표시값 일치 검증** (err-022 대조) |

## 6. Round 분할 권고 (Phase 30 5-round 패턴 계승)

| Round | 범위 | commit 단위 |
|-------|------|------------|
| **R1** | F18 + F20 (P0 backend 핵심) — `_infer_period_from_bid_no` 폐기 + inqryDiv=2 단건 모드 + Frgcpt endpoint 추가 | backend bid.py 1 commit |
| **R2** | F19 + F21 backend (P0) — PPSSrch endpoint 전환 + ntceInsttNm/dminsttNm 직접 전달 + srvceDivNm 응답 추가 | backend bid.py 1 commit |
| **R3** | F23 frontend (P0/P1) — 3계층 dropdown + 비활성 옵션 제거 | frontend bids/page.tsx 1 commit |
| **R4** | F22 (P1) — search_agencies 도구 신설 + frontend 자동완성 | backend + frontend 2 commits |
| **R5** | 종합 회귀 — 14 화면 회귀 + 사용자 case L4 evidence 재확보 | 검증 라운드 |

## 7. 영향 받는 영역

- **backend**: `app/tools/bid.py` (대규모), `app/tools/award.py` (소규모 — Award는 이미 4분류 일치), `app/tools/workflow.py` (W3 trace), `app/schemas/bid.py` (BidNoticeSummary 필드 추가)
- **frontend**: `bids/page.tsx`, `bids/trace/page.tsx`, `agencies/page.tsx` (LIKE), `lookup/page.tsx`
- **schemas**: BidNoticeSummary에 `srvce_div`, `ppsw_gnrl_yn` 추가

## 8. 사용자 승인 후 진행

본 PLAN 승인 시:
1. Phase 31 5-round quality-loop 가동 (Phase 30 패턴)
2. fixer / tester / quality-monitor 3 agent 협업
3. 각 round 별 atomic commit + L1~L6 검증
4. round-over-round 비교 리포트
5. 최종 사용자 검증 라운드

## 9. 비-목표

- award.py / vendor_profile 변경 (Award는 이미 정합)
- 신규 화면 추가
- F0~F17 재진입 (Phase 22~30 영역 — 별도)

## 10. 종료 조건

- F18 R-prefix 1년+ 매칭 evidence (R25BK00755515-000 backend 응답 row 도착)
- F19 발주기관 LIKE evidence (국방부 / 국군재정관리단 backend 응답에 매칭)
- F20 외자 endpoint 응답 정상
- F21 srvceDivNm 일반용역/기술용역 분리 표시
- F22 수요기관 자동완성 2자 trigger 동작
- F23 frontend 3계층 dropdown 정합
- 사용자 "정합성 OK" 확인
