# Phase 32 Round 2 — trace 5 stage actions R-prefix 폴백 일괄 적용 (F30)

> 작성일: 2026-05-04 (KST)
> Fixer: phase-30-quality-loop / fixer
> Scope: backend only (1 atomic commit). Frontend caller 시그니처 변경 0.

## 1. 사용자 보고 evidence

- **err-72 (R26BK01451151 trace)**: 요약 카드의 낙찰자 정보(주식회사 서정이엔지)는 정상 표시되나, 하단 stage 3·4·5·6 (사전규격/공고/응찰업체/낙찰)이 모두 "미발견"으로 표시.
- **err-73**: 나라장터 웹 UI에서 동일 입찰의 응찰업체 50건 정상 노출.

## 2. Root cause (5건 입찰번호 raw evidence — `poc_p32_v3.py`)

`trace_bid_lifecycle`이 호출하는 5 stage actions 중 3개(`get_award_detail`,
`list_bid_participants`, `get_pre_specification_detail`)가 R-prefix 13자리 입찰번호를
G2B endpoint에서 매칭하는 inqryDiv/endpoint 조합이 **운영 실측과 어긋나**
모든 R-prefix 단건 호출이 0건 응답을 반환.

### raw 호출 검증 (5 입찰번호)

| 입찰번호 | `getScsbidListSttus*PPSSrch + inqryDiv=3` (낙찰) | `getOpengResultListInfo* (non-PPSSrch) + inqryDiv=4` (응찰) | 사전규격 endpoint 3종 |
|----------|---|---|---|
| R25BK00755515 | Servc 1건 hit | Servc 1건 hit (prtcptCnum=1) | 0건 |
| R25BK00758431 | 0건 (유찰) | Servc 1건 hit (prtcptCnum=0) | 0건 |
| R25BK00760571 | Cnstwk 1건 hit | Cnstwk 1건 hit (prtcptCnum=82) | 0건 |
| R26BK01451151 | Cnstwk 1건 hit | Cnstwk 1건 hit (prtcptCnum=50) | 0건 |
| R26BK01501665 | 0건 (수의시담) | Cnstwk 1건 hit (prtcptCnum=1) | 0건 |

**기존 코드 매핑은 endpoint/inqryDiv가 모두 정합하지 않아 0건 응답**:
- 기존 `get_award_detail`: `getScsbidListSttus*` (non-PPSSrch) + `inqryDiv=4` → R-prefix 미작동
- 기존 `list_bid_participants`: `getOpengResultListInfo*PPSSrch` + `inqryDiv=4` → R-prefix 미작동
- 기존 `get_pre_specification_detail`: `getPrdctClsfcNoPblancListInfo* + inqryDiv=3` → R-prefix 미작동

DOSSIER-OFFICIAL §6.3 inqryDiv 4분류 표 자체가 endpoint마다 다르다고 명시(註: "endpoint마다 약간 다름"). 실측이 보증.

### 50건 응찰업체 raw row endpoint 부재

`getOpengResultListInfo*` (non-PPSSrch + PPSSrch) 모두 R-prefix 단건에 대해
**1 row만 반환**. row 안에 `prtcptCnum=50`(응찰 총수) + `opengCorpInfo`(낙찰자 1건
caret(`^`) 인코딩 — 예: `"주식회사 서정이엔지^6468800556^이유정^260750100^90.593"`).
50건의 응찰업체 raw list를 row 단위로 받는 OpenAPI endpoint는 **공식 미공개** —
G2B 웹 UI 전용. (`OpengCompt`/`Failing`/`Rebid`/`BidPrcbdrPL*` 등 후보 모두 404 또는 스키마 다름. raw evidence는 `poc_p32_v4.py`.)

→ **fix 정책**: items에는 `opengCorpInfo` 파싱한 낙찰자 1건만 노출, `participant_count`는 G2B 발신 `prtcptCnum`을 그대로 사용. UI 측에서 "응찰업체 50개사 (낙찰자: 주식회사 서정이엔지)"로 표시 가능.

## 3. Fix (backend, 1 atomic commit)

### 3.1 공용 헬퍼 — `_is_r_prefix`

`app/tools/award.py` 와 `app/tools/bid.py` 양쪽에 동치 헬퍼 (R4.5 패턴 정합):

```python
_R_PREFIX_PATTERN = re.compile(r"^R\d{2}[A-Z]{2}\d{8}$", re.IGNORECASE)

def _is_r_prefix(bid_no: str | None) -> bool:
    if not bid_no:
        return False
    head = bid_no.split("-")[0].strip()
    return bool(_R_PREFIX_PATTERN.match(head))
```

### 3.2 `award.py:get_award_detail` 1차 폴백 추가

R-prefix면 `getScsbidListSttus{Cnstwk,Servc,Thng,Frgcpt}PPSSrch + inqryDiv=3 + bidNtceNo`
4종 fan-out을 1차 우선순위로 신설. 미매칭 시 기존 `inqryDiv=4 + inqryDiv=1+추정기간` chain 그대로.

신규 `_AWARD_PPSSRCH_ENDPOINTS` 매핑 + `lookup_mode = "PPSSrch+inqryDiv=3+bidNtceNo"` 가시화.

### 3.3 `award.py:list_bid_participants` 1차 폴백 + opengCorpInfo 파싱

R-prefix면 `getOpengResultListInfo{X}` (non-PPSSrch) + `inqryDiv=4 + bidNtceNo` 4종 fan-out.
응답 row의 `opengCorpInfo`를 caret 분리 후 낙찰자 1건 정규화 (`_parse_openg_corp_info`).
`participant_count = prtcptCnum` (G2B 발신 응찰 총수). `winner_only=True` 플래그 + 사용자
설명 note 포함.

신규 `_OPENING_NONPPS_ENDPOINTS` 매핑.

### 3.4 `bid.py:get_pre_specification_detail` 2차 폴백 추가

기존 `inqryDiv=3` 1차 chain 보전 후, R-prefix면 `getPrdctClsfcNoPblancListInfo{Cnstwk,Servc,Thng} + inqryDiv=2 + bidNtceNo` 3종 fan-out 2차 폴백 신설.
(BidPublicInfoService 단일조회 패턴 A: `2 = 입찰공고번호`. DOSSIER-OFFICIAL §2 patternA.)

### 3.5 cache prefix 갱신 (변경 명시)

- `award_detail` → `award_detail_v32`
- `participants` → `participants_v32`
- `prespec_detail` → `prespec_detail_v32`

기존 캐시는 자동 무효화 (prefix mismatch).

### 3.6 변경 0 확인

- backend 함수 시그니처(인자, 반환 dict 키): 모두 동일 — `found / summary / items / participant_count / lookup_mode / endpoint / biz_div / raw / note`. lookup_mode 값만 신규 case 추가 (caller가 표시용으로만 사용 — 분기 로직 변경 0).
- frontend caller (`actions.ts` 등) 시그니처 호출 변경 불필요.
- R4.5 헬퍼 `bid.py:_get_detail_by_bid_no` 격리 보전 (회귀 0).

## 4. Raw 검증 evidence (fix 적용 후 — `verify_p32_fix.py`)

5 입찰번호 backend 함수 직접 호출 결과 (캐시 prefix v32 → 항상 fresh 호출):

```
R25BK00755515:
  award:    found=True biz=Servc  winner=주식회사 유명소프트  amt=110,800,000   lookup=PPSSrch+inqryDiv=3+bidNtceNo
  parts:    found=True biz=Servc  count=1   items=1  winner_item=주식회사 유명소프트  lookup=non-PPSSrch+inqryDiv=4+bidNtceNo
  prespec:  found=False (R-prefix div=2 폴백 후에도 0건 — 사전규격 미등록 입찰)

R25BK00758431:
  award:    found=False (유찰 — ScsbidListSttus*PPSSrch 0건 응답 정상)
  parts:    found=True biz=Servc  count=0   items=0   lookup=non-PPSSrch+inqryDiv=4+bidNtceNo (응찰 0건 + 유찰)
  prespec:  found=False

R25BK00760571:
  award:    found=True biz=Cnstwk winner=헥사콘 주식회사  amt=531,501,300   lookup=PPSSrch+inqryDiv=3+bidNtceNo
  parts:    found=True biz=Cnstwk count=82  items=1  winner_item=헥사콘 주식회사  lookup=non-PPSSrch+inqryDiv=4+bidNtceNo
  prespec:  found=False

R26BK01451151:  ← err-72 핵심
  award:    found=True biz=Cnstwk winner=주식회사 서정이엔지  amt=260,750,100   lookup=PPSSrch+inqryDiv=3+bidNtceNo
  parts:    found=True biz=Cnstwk count=50  items=1  winner_item=주식회사 서정이엔지  lookup=non-PPSSrch+inqryDiv=4+bidNtceNo
  prespec:  found=False

R26BK01501665:
  award:    found=False (수의시담 — 낙찰목록 미게재)
  parts:    found=True biz=Cnstwk count=1   items=1  winner_item=보광기업  lookup=non-PPSSrch+inqryDiv=4+bidNtceNo
  prespec:  found=False
```

raw payload 전체: `.planning/phases/32-trace-stage-fallback/verify_p32_fix_raw/{bid_no}.json`.

### 사용자 비판 #59 반영 (검증 시뮬 강화)

| 항목 | 결과 |
|------|------|
| 5 입찰번호 모두 raw 호출 검증 | ✅ 5/5 |
| awards: 미발견 사례(유찰/수의시담)도 backend 응답 정상 | ✅ R25BK00758431 / R26BK01501665 found=False note 명시 |
| participants: 50건 카운트 노출 | ✅ R26BK01451151 count=50 |
| 사전규격: 미존재 케이스 fallback chain 동작 | ✅ inqryDiv=3 → R-prefix inqryDiv=2 → found=False note |

## 5. 자체 sanity check

- [x] backend 호출 시그니처 변경 0 (caller 정합)
- [x] R4.5 `_get_detail_by_bid_no` 헬퍼 격리 보전 (회귀 0)
- [x] python import 성공 (`from app.tools import award, bid, workflow`)
- [x] 5 입찰번호 raw 응답 검증 (위 표)
- [x] frontend caller 시그니처 변경 0 — `award.found/summary/items/participant_count` 키 동일
- [x] cache prefix v32 갱신 (변경 명시)
- [x] uvicorn 재기동 절차 — 사용자 측 backend restart 필요 (캐시 + import re-eval)

## 6. 산출물 위치

- backend: `app/tools/award.py` (헬퍼 + get_award_detail + list_bid_participants 수정), `app/tools/bid.py` (get_pre_specification_detail 수정 + `re` import 추가)
- raw evidence: `.planning/phases/32-trace-stage-fallback/poc_p32_raw_v3/{bid_no}.json` (fix 전), `.planning/phases/32-trace-stage-fallback/verify_p32_fix_raw/{bid_no}.json` (fix 후)
- raw probe 스크립트: `poc_p32.py`(v1 미작동 reproduce), `poc_p32_v2.py`(inqryDiv 매핑 탐색), `poc_p32_v3.py`(5건 패턴 확정), `poc_p32_v4.py`(50건 row endpoint 부재 확인), `verify_p32_fix.py`(fix 검증)
- 본 보고서: 이 파일

## 7. Frontend 표시 권장 (참고)

`participants` items=1 + count=50 케이스에서 UI는 현재 단일 row만 렌더할 가능성.
권장 표시:
- "응찰업체 **50개사** (낙찰자: 주식회사 서정이엔지)" 같이 count + 낙찰자 분리
- `winner_only=true` + `note` 필드 활용 (기존 응답 키에 포함)

frontend 변경은 본 R2 fix 범위 밖 — lead 위임.
