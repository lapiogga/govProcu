# ROUND 1 FIX REPORT (Phase 31)

> **범위**: F18 (R-prefix 단건 inqryDiv=2) + F20 (외자 endpoint 추가). backend-only.
> **commit 단위**: 1 atomic commit (bid.py + schemas/bid.py).
> **근거**: DOSSIER-OFFICIAL §3 (1개월 제한) + §1.2 (4분류 endpoint), POC-G2B #4 raw evidence.

## 적용 변경

| ID | 파일 | line (수정 전 위치) | before | after | 근거 |
|----|------|---------------------|--------|-------|------|
| F18 | `app/tools/bid.py` | 18-37 | `_infer_period_from_bid_no`가 R/숫자 prefix → `{year}0101`-`{year}1231` 1년 통째 반환 | 항상 `(None, None)` 반환 (시그니처 보존, no-op). award.py 호환 유지 | DOSSIER §3.1 — 1개월 제한 위반 회피 |
| F18 | `app/tools/bid.py` | 86 (cache decorator) / 121-129 (search_bid_notices 진입부) | `_infer_period_from_bid_no` 폴백 후 chunked 검색 | `bid_notice_no` 있고 `date_from/date_to` 미지정 시 즉시 `_search_by_bid_notice_no` 분기 (inqryDiv=2 + bidNtceNo, 기간 unset, 5종 단일조회 endpoint 병렬 fan-out, 매칭 1건 즉시 return) | POC #4: R25BK00755515 → Servc endpoint 1개에서 hit, 기간 unset 정상 |
| F20 | `app/tools/bid.py` | 40-56 | `_resolve_bid_endpoints(None)` → 3종 (공사/용역/물품) 병합 | None → 4종 병합 (외자 Frgcpt 추가). `biz_type="외자"` 분기 신설 | DOSSIER §1.2 — BidPublicInfoService 4분류 endpoint |
| - | `app/schemas/bid.py` | 11 | `BidNoticeSearchInput.biz_type: Literal["공사", "용역", "물품", None]` | `Literal["공사", "용역", "물품", "외자", None]` | F20 backend 정합 |
| - | `app/tools/bid.py` | 82 | `prefix="bid_v24"` | `prefix="bid_v31"` | R1 변경 명시 (캐시 무효화) |
| - | `app/tools/bid.py` | 신규 | (없음) | `_BID_DETAIL_ENDPOINTS` (5종 ordered list — 단건 fan-out용), `_search_by_bid_notice_no` async helper 신설 | POC #4 5종 fan-out 패턴 |

### F18 단건 모드 핵심 흐름

```
search_bid_notices(bid_notice_no="R25BK00755515", date_from=None, date_to=None)
  → _search_by_bid_notice_no(inp)
    → asyncio.gather([
        Cnstwk(inqryDiv=2, bidNtceNo=R25BK00755515),
        Servc (inqryDiv=2, bidNtceNo=R25BK00755515),  # ← totalCount=1, 매칭
        Thng  (inqryDiv=2, bidNtceNo=R25BK00755515),
        Frgcpt(inqryDiv=2, bidNtceNo=R25BK00755515),
        Etc   (inqryDiv=2, bidNtceNo=R25BK00755515),
      ])
    → 매칭 row dedup + _normalize_notice → return {items, lookup_mode="inqryDiv=2+bidNtceNo", chunks_used=0}
```

기간 (`inqryBgnDt/inqryEndDt`) 미전달 → DOSSIER §3 1개월 제한 회피 (POC #4 검증).

### F18 `-` suffix 통합 형태 처리

`bid_notice_no="R25BK00755515-000"` 입력 시 `target_no="R25BK00755515"` + `target_ord_norm="0"` 자동 분리. ord 값 매칭 검증 추가.

### 회귀 안정성

- 일반 검색 모드 (`bid_notice_no=None`): 분기 진입 안 함 → 기존 chunks × endpoints 병렬 호출 패턴 그대로.
- award.py `_infer_period_from_bid_no` import: 시그니처 동일 + 호출처에 `if bgn_dt and end_dt` 가드 있음 → (None, None) 반환에 안전. 단, award.py 2차 폴백은 기간 미전달 호출이 됨 (영향 R2 외).
- bid.py `get_bid_notice_detail` 폴백: 동일 가드. 3차 폴백 `search_bid_notices(bid_notice_no=..., date_from=fb_from, date_to=fb_to)`은 date_from/to 명시 → 단건 모드 분기 회피 (의도적: detail은 inqryDiv=3 1차 + inqryDiv=1 2차 + 검색 폴백 패턴 유지).

## Commit

- hash: (작업자가 commit 후 채움)

## 자체 sanity check

- [x] **L1 backend 호출 시그니처 변경 여부**: `search_bid_notices(...)` 시그니처 변경 없음 (동작만 추가). `_infer_period_from_bid_no(bid_notice_no: str) -> tuple[str|None, str|None]` 시그니처 동일.
- [x] **L1 caller 정합성**: `app/tools/{award.py, alerts.py, lookup.py, multi_agency.py, analytics.py, workflow.py, server.py}` 모두 변경 없이 import 정상 (`python -c "from app.tools import bid, award, ...; from app.server import mcp"` 통과).
- [x] **L1 schemas import**: `BidNoticeSearchInput.biz_type` Literal 확장 — pydantic 검증 호환. 기존 호출자가 "외자" 미사용 시 무영향.
- [x] **L3 raw PoC 검증**: `bid_notice_no="R25BK00755515"` 호출 → totalCount=1, lookup_mode="inqryDiv=2+bidNtceNo", endpoints_used=[Servc], 5종 중 Servc 1개만 hit. POC-G2B #4 raw evidence 정확 재현.
- [x] **L3 응답 정합성**: bid_no="R25BK00755515", title="2025년도 역사지리정보DB 구축사업", inst_name="조달청 서울지방조달청", srvceDivNm="일반용역" — DOSSIER §1.3 응답 필드 명시 + 사용자 사례 적중.
- [x] **L3 회귀 검증**: `search_bid_notices(date_from='20260401', date_to='20260430', limit=3)` (bid_notice_no=None) 호출 → lookup_mode 미존재, chunks_used=1, returned_count=3. 일반 검색 모드 변경 0 검증.

## 핸드오프 메시지 (tester-p31-r1 앞)

### L3 핵심 검증 포인트

1. **단건 모드 동작 검증** (POC #4 재현):
   - 입력: `search_bid_notices(bid_notice_no="R25BK00755515")`
   - 기대: `lookup_mode="inqryDiv=2+bidNtceNo"`, `chunks_used=0`, 5종 endpoint 중 Servc 1개에서만 매칭, `srvceDivNm="일반용역"`
   - raw 검증: `endpoints_used=["/BidPublicInfoService/getBidPblancListInfoServc"]`

2. **`-` suffix 통합 형태 단건 매칭**:
   - 입력: `search_bid_notices(bid_notice_no="R25BK00755515-000")`
   - 기대: ord 분리 후 ord_norm="0" 매칭 — 동일 row 반환

3. **외자(Frgcpt) endpoint 단건 호출**:
   - 입력: `search_bid_notices(bid_notice_no="<외자 R-prefix>")`
   - 기대: 5종 fan-out 중 Frgcpt에서 hit (외자 사례 있을 때)

### L4 사용자 case retrieval

- **R25BK00755515** (역사지리정보DB / 조달청 서울지방조달청 / 일반용역) — POC #4 검증 완료
- 확장 candidates (사용자 보고 사례 후보 — tester가 추가 확보 권장):
  - R26BK... (2026년 입찰)
  - 외자 case (외자 endpoint 검증용)

### 회귀 — 변경 0 보장 영역

- 일반 검색 모드 (`bid_notice_no=None` + keyword/inst_name/biz_type 단독): 단건 분기 안 탐 → 기존 v22~v24 동작 유지 필수.
- `search_bid_notices(bid_notice_no=..., date_from=..., date_to=...)` (date 명시): 단건 분기 안 탐 → 기존 chunked 검색 + client-side filter 동작 유지 (`get_bid_notice_detail` 3차 폴백 시나리오).

### 단건 모드 한계 (R2에서 보강 예정 — R1 범위 외)

- F19 발주기관 LIKE: 단건 모드는 `bidNtceNo` 직접 매칭 → ntceInsttNm 활용 불가. 일반 검색 모드 PPSSrch 전환은 R2.
- F21 srvceDivNm 응답 추가: 현재 `_normalize_notice`는 `bsnsDivNm`만 매핑. R2에서 `srvce_div`, `ppsw_gnrl_yn` 추가.
- F22 search_agencies 신설: R4.

## 결함/보류

없음 — F18 + F20 atomic 적용 완료. R2 (F19+F21+F22) 진행 가능.
