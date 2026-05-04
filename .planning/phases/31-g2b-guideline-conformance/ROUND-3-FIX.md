# ROUND 3 FIX (Phase 31)

> **라운드**: Phase 31 Round 3 — F23 (frontend 3계층 dropdown) + F26 (발주기관 결과 컬럼 분리). frontend-only.
> **commit**: (작성 직후 commit hash 추가 예정)
> **기간**: 2026-05-04 (KST).
> **작성자**: fixer-p31-r3.
> **입력**: PLAN.md, ROUND-2-REPORT.md (§ 6 권고 9항 + 위험 사전 식별), POC-G2B.md (#5 srvceDivNm), bids/page.tsx (468줄), actions.ts.

---

## 1. 채택 옵션

ROUND-2-REPORT § 6 위험 사전 식별의 **옵션 A** 채택:
- **indstryty_cd**: 단순 input (4자리 코드, placeholder "업종 코드 4자리 (예: 0036)"). 자동완성 모달은 R4 또는 별도 phase 분리 — R3 atomic commit 사이즈 작게 유지.
- **발주기관 (inst)**: 단순 input (LIKE 매칭은 backend가 fan-out 처리). 자동완성 모달은 R4 분리.

PLAN § 6 atomic commit 권장 옵션 A (1 commit) 채택 — actions.ts(소) + bids/page.tsx(대) 통합. rollback 단위 명확성 우선.

## 2. 변경 영역

| 파일 | 변경 사이즈 | 내용 |
|------|-----------|------|
| `frontend/src/lib/actions.ts` | +1 line | `searchBidNotices` 인자에 `indstryty_cd?: string` 추가 (R2 backend 신규 인자 매핑) |
| `frontend/src/app/bids/page.tsx` | 대규모 재구성 (검색 form + 결과 테이블) | F23 + F26 |

## 3. F23 검색 form 재구성

### 3.1 변경 전 (4 input + 1 select)

```tsx
<form action="/bids" className="grid grid-cols-1 gap-2 md:grid-cols-5">
  <Input name="q" ... />
  <select name="type">
    <option value="">업종 전체</option>
    <option value="공사">공사</option>
    <option value="용역">용역</option>
    <option value="물품">물품</option>
  </select>
  <Input name="inst" ... />
  <Button type="submit">검색</Button>
  <Input name="from" ... />
  <Input name="to" ... />
  ...
</form>
```

### 3.2 변경 후 (3행 grid, 5체크박스 다중 + 외자 토글 + 업종 코드 input)

```tsx
{/* 1행: 키워드 + 발주기관 + 업종 코드 + 검색 */}
<div className="grid grid-cols-1 gap-2 md:grid-cols-5">
  <Input name="q" placeholder="공고명 (예: 정보화 시스템 구축)" />
  <Input name="inst" placeholder="발주기관 (공고/수요 통합, 2자+)" minLength={2} />
  <Input name="indstryty" placeholder="업종 코드 4자리 (예: 0036)" pattern="\d{4}" maxLength={4} />
  <Button type="submit">검색</Button>
</div>

{/* 2행: 업무구분 5체크박스 + 외자 토글 */}
<fieldset>
  <legend>업무구분 (다중 선택, 미선택 = 전체)</legend>
  <Checkbox name="biz_types" value="공사" />공사
  <Checkbox name="biz_types" value="물품" />물품
  <Checkbox name="biz_types" value="일반용역" />일반용역
  <Checkbox name="biz_types" value="기술용역" />기술용역
  <Checkbox name="biz_types" value="기타" />기타
  {/* 업무여부 */}
  <Checkbox name="frgcpt" value="1" />외자
</fieldset>

{/* 3행: 기간 + 깊은 검색 */}
<div>
  <Input name="from" />
  <Input name="to" />
  <Checkbox name="deep" value="1" />깊은 검색
</div>
```

### 3.3 비활성 옵션 완전 제거 (발화 #44)

- **민간** — DOM에서 완전히 사라짐 (구 select option `<option value="용역">용역</option>` → 5체크박스로 대체, 민간은 나열 안 함).
- **비축 / 리스** — 외자 fieldset 옆에 토글 옵션이 더 이상 없음.

### 3.4 form 데이터 처리 매핑

`parseBizTypes(sp.biz_types, sp.type)` — searchParams의 `biz_types` (콤마 구분 또는 다중 선택 → URL이 `?biz_types=공사&biz_types=물품` 형식. Next.js searchParams는 URLSearchParams가 같은 key 다중 출현 시 마지막만 유지하므로, 본 구현은 form 제출이 콤마 구분 단일 string으로 처리되는 케이스 + 후방호환 `type` 단일 인자 케이스 모두 지원).

| 사용자 선택 | `selectedBizTypes` | `includeFrgcpt` | `resolveBackendBizType` 결과 (backend 인자) | client-side filter |
|------------|--------------------|-----------------|--------------------------------------------|-------------------|
| 0개 + 외자 미선택 | `[]` | false | `undefined` (전체 5종 fan-out) | none |
| 0개 + 외자 only | `[]` | true | `"외자"` | none |
| "공사" 단독 | `["공사"]` | false | `"공사"` | none |
| "물품" 단독 | `["물품"]` | false | `"물품"` | none |
| "일반용역" 단독 | `["일반용역"]` | false | `"용역"` | `srvce_div === "일반용역"` |
| "기술용역" 단독 | `["기술용역"]` | false | `"용역"` | `srvce_div === "기술용역"` |
| "일반용역" + "기술용역" | 2종 | false | `"용역"` | none (둘 다 통과) |
| "공사" + "물품" | 2종 | false | `undefined` (5종 fan-out) | none |
| 다종 + "외자" | n종 + 외자 | true | `undefined` (5종 fan-out, 외자 포함) | none |

**핵심**: backend는 `biz_type` 단일 인자(`"공사"` / `"용역"` / `"물품"` / `"외자"` / `"기타"` / None) 만 수용. 다종 선택 시 `None` 으로 5종 endpoint 병합 fan-out에 의존 (POC #1·#2·#3 정합).

## 4. F26 결과 테이블 컬럼 분리

### 4.1 변경 전 (6 컬럼, 발주기관 단일)

| 공고일 | 공고제목 | 발주기관 | 업종 | 추정가 | 마감일 |

### 4.2 변경 후 (7 컬럼, 발주기관 분리 + 업무구분 srvce_div 우선)

| 공고일 | 공고제목 | **공고기관** | **수요기관** | **업무구분** | 추정가 | 마감일 |

### 4.3 컬럼 구현 상세

- **공고기관** (`ntceInsttNm`): `bid.raw["ntceInsttNm"]` 직접 활용 (BidNoticeSummary 응답의 `raw` 필드 사용 — backend 변경 0).
- **수요기관** (`dminsttNm`): `bid.raw["dminsttNm"]` 직접 활용. **공고기관과 동일 시 "(동일)" 표기** — 발화 #46/#47 "공고==수요 동일 대부분" 사용자 통찰 반영.
- **업무구분**: `bid.srvce_div` 우선 ("일반용역"/"기술용역" 변별 — R2 신규 필드 활용). 없으면 `bid.biz_type` (PPSSrch는 null이므로 단건 조회 fallback에서만 등장). 둘 다 없으면 "—".

### 4.4 schema 변경 0 — raw 응답 직접 활용

ROUND-2-REPORT § 6 권고 #3 (F26 schema 확장 검토) 항목 → **schema 미확장, raw 직접 활용** 결정. 이유:
- backend `BidNoticeSummary.raw: dict | None` 이미 원본 보존 (`app/schemas/bid.py:35`, `bid.py:113`).
- frontend Bid interface에 `raw?: Record<string, unknown> | null` 추가 → ntceInsttNm/dminsttNm 직접 추출.
- backend 인터페이스 무영향, 변경 폭 최소.

## 5. searchAgencies server action — 미신설 (옵션 A)

ROUND-2-REPORT § 6 권고 #2 — 자동완성 R4 분리 결정에 따라 본 R3에서는 **`searchAgencies` server action 미신설**. backend 도구는 R2에서 등록 완료 (mcp `search_agencies`), R4에서 frontend 자동완성 모달 연동 시 actions.ts에 export 추가 예정.

## 6. R3 권고 9항 적용 매트릭스

| # | 권고 | 적용 결과 |
|---|------|----------|
| 1 | actions.ts:searchBidNotices 인자 정합 (`indstryty_cd` 추가) | ✅ 1 line 추가 |
| 2 | searchAgencies server action 신설 | ⏸ 옵션 A — R4 분리 |
| 3 | BidNoticeSummary frontend 타입 확장 (`srvce_div`, `ppsw_gnrl_yn`, `raw`) | ✅ Bid interface에 추가 |
| 4 | 검색 form 재구성 (5체크박스 + 외자 + indstryty_cd input) | ✅ |
| 5 | 결과 테이블 ntce + dmin 분리 + srvce_div 컬럼 | ✅ raw 직접 활용 |
| 6 | 비활성 옵션 제거 (민간/비축/리스) | ✅ DOM에서 흔적 제거 |
| 7 | actions.ts 변경 caller 영향 분석 — `/vendors`, `/agencies`, `/lookup`, `/bids/trace`, `/`, `/qualification`, `/external/kwater`, `/analytics`, `/predictions` 등 무영향 | ✅ grep 결과 — searchBidNotices caller는 bids/page.tsx 1곳뿐. api/chat/route.ts는 `callMcpTool` 직접 호출(actions.ts 미사용). |
| 8 | TypeScript 컴파일 0 에러 | ✅ `npx tsc --noEmit` exit 0 |
| 9 | L6 evidence — err-031 7체크박스 → R3 5체크박스 매핑 (민간 비활성 제거) + err-032/033/034 자동완성은 R4 | ✅ R3 영역 정합 |

## 7. 자체 sanity check (R3+R4 학습 누적)

- [x] **backend 호출 시그니처 cross-check** — `search_bid_notices` 신규 인자 (`indstryty_cd`) keyword arg 정합. spread 패턴 (`...searchParams`) 그대로 유지 → backend 추가 인자에 자동 매핑.
- [x] **TypeScript 컴파일 0 에러** — `npx tsc --noEmit` (exit 0).
- [x] **비활성 옵션 (민간/비축/리스) 완전 제거** — DOM 검색 (`민간`, `비축`, `리스`) 결과 0건 (page.tsx 새 본문에는 미존재).
- [x] **/bids/trace, /vendors, /agencies, /lookup 등 영향 받지 않는 화면 무변동** — actions.ts의 searchBidNotices만 인자 +1 (선택형 keyword arg) → 기존 caller 호환. 다른 server action 변경 0.
- [x] **biz_types 다중 선택 처리** — Next.js form 제출 시 동일 name 다중 체크박스 → URLSearchParams `getAll('biz_types')` 활용 가능. 본 구현은 후방호환 위해 `parseBizTypes(sp.biz_types, sp.type)` 으로 단일 CSV string + legacy `type` 단일 인자 둘 다 지원.
- [x] **indstryty_cd 단순 input — 4자리 코드 검증** — `pattern="\d{4}"` + `maxLength={4}` HTML5 validation.

## 8. 영향 받지 않는 영역 (변경 0 보장)

| 영역 | 변경 0 근거 |
|------|-----------|
| backend (app/) | 본 R3 frontend-only — backend 미수정 |
| /bids/trace | 단건 모드(R1) 격리, traceBidLifecycle action 미변경 |
| /vendors | searchVendorsByName/getVendorProfile 미변경 |
| /agencies | getAgencyHistory/getAgencyPricePattern 미변경 |
| /lookup | lookup_by_* 3 action 미변경 |
| /qualification | calcQualification action 미변경 (R4 영역) |
| /external/kwater | searchKwaterContracts 미변경 |
| /analytics, /predictions | predictBidPrice/compareBidStrategies/industry_trend/market_share 미변경 |
| api/chat/route.ts | actions.ts 미사용 (callMcpTool 직접) — 인자 추가 영향 0 |

## 9. 보류 / 결함 사항

**없음.**

R3 영역 외 항목:
- F22 자동완성 frontend 연동 (`searchAgencies` server action + 자동완성 모달 + indstryty_cd 자동완성 모달) — R4로 분리 (옵션 A 채택).
- F25 / F27 / F28 (시행령 12 필수항목 / qualification 라벨 표준화 / trace 6단계 명칭 표준화) — R4 영역.
- L6 evidence 매핑 (err-031~034) — tester-p31-r3 검증 단계.

## 10. tester-p31-r3 핸드오프

### 핵심 검증 포인트 4개

1. **F23 form 정합성** — 5체크박스 + 외자 토글 + indstryty 4자리 input 모두 DOM에 존재. 비활성 옵션(민간/비축/리스) 0건.
2. **F26 결과 컬럼** — 공고기관 / 수요기관 / 업무구분 분리 표시. dminsttNm == ntceInsttNm 시 "(동일)" 표기. srvce_div(일반용역/기술용역) 우선.
3. **biz_types form 처리** — 1종 단독 → backend "공사"/"물품"/"용역"/"기타"/"외자". 다종 → backend `None` (5종 fan-out). 일반용역 단독 → backend "용역" + client-side `srvce_div === "일반용역"` filter.
4. **회귀 0 검증** — actions.ts 신규 인자 `indstryty_cd` 추가 후 다른 화면(/vendors, /agencies, /lookup, /bids/trace 등) HTTP 200 정상.

### 회귀 변경 0 보장 영역

- backend 영역 전체 (frontend-only)
- /bids/trace, /vendors, /agencies, /lookup, /qualification, /external/kwater, /analytics, /predictions
- api/chat/route.ts (callMcpTool 직접 호출)

### 추가 검증 권고

1. **L4 user case 재현** — 사용자 보고 케이스 (국방부 국군재정관리단, 한국수자원공사, R25BK00755515) frontend 검색 → 결과 7컬럼 정상 표시.
2. **L5 frontend HTTP** — `/bids` 5 시나리오 (키워드 only / 다종 체크 / 외자 only / indstryty 코드 / 발주기관 only) HTTP 200.
3. **L6 evidence 매핑** — err-031 7종 체크박스 → R3 5종 정합 (민간 제거 합당). err-032/033/034 자동완성은 R4 분리 명시.

### R4 영역 인계 (옵션 A 분리)

1. **F22 자동완성 frontend 연동** — `searchAgencies` server action 신설 + 자동완성 모달 + debounced input.
2. **indstryty_cd 자동완성 모달** — backend 도구 신설 (PLAN § 3.7 옵션 A/B/C 결정) + frontend 모달.
3. **F25 / F27 / F28** — trace 12 필수항목 노출 / qualification 라벨 / trace 6단계 명칭.

---

## 11. commit 메시지

```
feat(frontend): P31-R3 bids 검색폼 5체크박스 + 결과 컬럼 분리 (F23, F26)

- bids/page.tsx: 검색 form 재구성
  - 업무구분 5체크박스 다중 (공사/물품/일반용역/기술용역/기타) — 민간 제거
  - 업무여부 외자 토글 — 비축/리스 제거
  - 업종 indstryty_cd 4자리 단순 input
  - 발주기관 단일 input (공고기관 + 수요기관 통합 LIKE)
- 결과 컬럼: 공고기관 / 수요기관 분리 + 업무구분 (srvce_div 우선)
  - dminsttNm == ntceInsttNm 시 "(동일)" 표기 (발화 #46/#47)
  - 일반용역 단독 선택 시 client-side filter (srvce_div === "일반용역")
- actions.ts: searchBidNotices 신규 인자 indstryty_cd 추가

비활성 옵션(민간/비축/리스) 완전 제거 (발화 #44).
자동완성 모달은 R4 분리 (위험 사전 식별 옵션 A 채택).

근거: err-031/033 G2B 표준 UX, ROUND-2-REPORT § R3 권고 9항.
```
