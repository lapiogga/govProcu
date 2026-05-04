# ROUND 2 FIX REPORT

> Phase 30 Round 2 — fixer-r2 작업 결과.
> 입력: ROUND-1-REPORT.md (R2 권고 옵션 A) / DIAGNOSIS-G2.md § A.3 / CHECKLIST.md P0-D row.
> 산출: backend-only atomic commit `21b9eb2` + 본 보고서 → tester-r2 핸드오프.

## 옵션 결정

**옵션 A 채택 (backend-only)**: ROUND-1-REPORT § 6 권고 그대로. R1 atomic 패턴 (단일 영역, 단일 commit) 일관성 유지. frontend 분기 제거는 R3 또는 별도 P2 batch.

## 적용 변경

| 도구 | before keys | after keys | 비고 |
|------|------------|-----------|------|
| `lookup_by_bid_no` (lookup.py:50-58) | `{bid_notice_no, bid_ord, inst_code, inst_name, vendor_biz_no, vendor_name, contract_no}` (7-key) | **변경 없음** — 이미 표준 | 기존 7-key 그대로. 회귀 위험 0 |
| `lookup_by_inst_code` (lookup.py:155-198) | `{inst_code, inst_name}` (2-key) | `{bid_notice_no, bid_ord, inst_code, inst_name, vendor_biz_no, vendor_name, contract_no}` (7-key) | 5-key 추가. 대표값은 awards/notices 첫 row에서 추출 (없으면 None) |
| `lookup_by_biz_no` (lookup.py:234-307) | `{vendor_biz_no}` (1-key) | `{bid_notice_no, bid_ord, inst_code, inst_name, vendor_biz_no, vendor_name, contract_no}` (7-key) | 6-key 추가. awards 첫 row + NTS items 첫 row를 대표값으로 활용 |
| `lookup_by_contract_no` (lookup.py:325-340, stub) | `{contract_no}` (1-key) | 동일 7-key 구조 (모두 None, contract_no만 채움) | stub 유지, keys만 표준 |

## 결정 메모

### bid_notice_no 대표값 채움 정책
- `lookup_by_inst_code`: notices items 첫 row 우선 → 없으면 awards items 첫 row → 없으면 None
- `lookup_by_biz_no`: awards items 첫 row (`bid_notice_no_list[0]`와 동등 — summary와 일관성 보장)
- raw G2B camelCase 키 (`bid_no`)도 fallback 고려 (`get("bid_notice_no") or get("bid_no")`)

### vendor_name 폴백
- `lookup_by_inst_code`: awards 첫 row의 `winner_name` 사용 (별도 API 호출 비용 회피)
- `lookup_by_biz_no`: awards 첫 row의 `winner_name` 우선 → 없으면 NTS items 첫 row의 `tax_type_nm`/`vendor_name` 폴백 → 없으면 None

### inst_code/inst_name 폴백
- `lookup_by_inst_code`: 사용자 입력값 우선 → 없으면 awards/notices 첫 row의 raw camelCase 키 (`dminsttCd`/`ntceInsttCd`) fallback chain
- `lookup_by_biz_no`: awards 첫 row의 `inst_code`/`inst_name` (G2B 응답에 inst_code 직접 없는 경우 raw camelCase fallback)

### cache prefix
- lookup.py는 자체 `@cache_result` decorator 사용 안 함 (underlying `bid_tools`/`award_tools`/`vendor_tools`는 자체 cache 보유, 그 응답 구조는 본 변경에 무영향)
- prefix 변경 **불필요**

## Commit

- hash: `21b9eb2`
- 변경 파일: `app/tools/lookup.py` 1개
- diff stat: 1 file changed, 86 insertions(+), 7 deletions(-)
- 메시지:
  ```
  fix(backend): P30-R2 lookup keys 7-key 표준화 (P0-D)

  lookup_by_bid_no/inst_code/biz_no/contract_no 모든 도구가 동일 keys 구조로 응답.
  - bid_notice_no, bid_ord, inst_code, inst_name, vendor_biz_no, vendor_name, contract_no
  - 없는 키는 None 명시 (frontend 4-카드 그리드 항상 렌더 가능)
  - 상위호환: 기존 키 보존, 신규 키만 추가

  inst_code/biz_no는 awards/notices 첫 row를 대표값으로 활용 (별도 API 호출 없음).
  cross-lookup 핵심 가치 회복. frontend mode=biz/inst에서 bid_notice_no/contract_no 카드 항상 '—' 회피.
  근거: DIAGNOSIS-G2 § A.3 lookup keys 불일치, ROUND-1-REPORT § 6 R2 권고 옵션 A.
  ```

## 자체 sanity check

- [x] Read → Edit 페어링 (lookup.py 전체 정독 후 3개 함수 Edit)
- [x] python `from app.tools import lookup` import 성공
- [x] `lookup_by_contract_no('TEST-001')` 호출 → keys 7-key 모두 존재 (`['bid_notice_no', 'bid_ord', 'contract_no', 'inst_code', 'inst_name', 'vendor_biz_no', 'vendor_name']`) + `contract_no='TEST-001'` 채움
- [x] 4 함수 시그니처 변경 없음 (caller 회귀 0)
- [x] 기존 keys 제거 0 (상위호환 보장) — `lookup_by_bid_no`는 변경 없음, 다른 함수는 None만 추가

## 핸드오프 메시지 (tester-r2 앞)

- **adopt 옵션**: A backend-only. frontend 미변경.
- **L3 검증 우선**:
  - `lookup_by_inst_code(inst_name="조달청")` 응답 keys 7-key 모두 존재 + bid_notice_no/vendor_biz_no 등 awards 대표값 채워졌는지 확인
  - `lookup_by_biz_no(vendor_biz_no="...")` 응답 keys 7-key 모두 존재 + bid_notice_no/inst_name 등 awards 대표값 채워졌는지 확인
  - `lookup_by_bid_no(bid_notice_no="...")` 응답 keys 변경 없음 (회귀 0 검증) — 기존 7-key 그대로
- **L4 사용자 case**: cross-lookup 사용자 사례 — 사업자번호 1건 + 발주기관 1건으로 raw payload 확인. 빈 awards 케이스(0건)에서도 keys 7-key 모두 None으로 정상 반환하는지 점검.
- **L5 frontend (회귀 점검)**: `/lookup?mode=notice&q=...`(기존 mode) 변경 0 검증 필수. mode=biz/inst에서 4-카드 그리드 자동 렌더 정상 (frontend 미변경 — backend 응답만 7-key로 풍부해짐).
- **회귀 우려 사항**:
  - `lookup_by_inst_code` notices/awards 첫 row가 raw G2B 키만 가질 수 있음 (`_normalize_*` 거치지 않은 경우) — fallback chain `get("bid_notice_no") or get("bid_no")` 적용했으나 실제 응답 정합성은 L3 raw 호출로 확인 필요
  - `lookup_by_biz_no`의 `bid_notice_no` 대표값이 `summary.bid_notice_no_list[0]`과 동일해야 함 (consistency)
- **frontend 분기 제거**: 별도 R3 또는 P1 batch (지금은 변경 없음). 본 R2는 backend keys만 7-key로 통일하므로 frontend는 추가 코드 없이 mode=biz/inst에서도 4-카드 모두 렌더됨 (None 카드는 "—" 표시).
