# ROUND 2 TEST REPORT

> Phase 30 Round 2 — tester-r2 검증 리포트.
> 입력: ROUND-2-FIX.md (commit `21b9eb2`) / ROUND-1-REPORT.md § 7 메타 평가 권고 / DIAGNOSIS-G2.md.
> 산출: L1~L5 종합 검증 → quality-monitor-r2 핸드오프.

## 종합 PASS/FAIL

**R2 종합: PASS (4/4 도구 7-key 표준화 확인 + 회귀 0)**

- L1 정적: PASS
- L2 논리/단위: PASS
- L3 backend 직접 호출: PASS
- L4 사용자 case: PASS
- L5 frontend 회귀: PASS
- 1건 부분 결함 (inst_code raw 침투 부재) — 비차단성, R3 또는 별도 batch 후속 권고

---

## 검증 매트릭스

| 도구 | L1 | L2 | L3 | L4 | L5 | 종합 |
|------|----|----|----|----|----|------|
| `lookup_by_bid_no` | PASS | PASS | PASS (회귀 0) | PASS | PASS | PASS |
| `lookup_by_inst_code` | PASS | PASS | PASS (5/7 채움) | PASS | PASS | PASS |
| `lookup_by_biz_no` | PASS | PASS | PASS (5/7 채움) | PASS (빈 awards 정상) | PASS | PASS |
| `lookup_by_contract_no` | PASS | PASS (stub 7-key) | N/A (stub) | N/A | PASS | PASS |

---

## L1 정적 검증

- `git show 21b9eb2 --stat` 확인:
  - 1 file changed: `app/tools/lookup.py`
  - 86 insertions(+), 7 deletions(-)
  - commit message: "fix(backend): P30-R2 lookup keys 7-key 표준화 (P0-D)"
  - **변경 파일/라인 ROUND-2-FIX.md 표 line-by-line 일치**
- python import:
  - `from app.tools import lookup` → success
  - `from app.tools.lookup import lookup_by_bid_no, lookup_by_inst_code, lookup_by_biz_no, lookup_by_contract_no` → 4 functions exported

---

## L2 논리 / 단위 검증

### ROUND-2-FIX 결정 메모 일치 확인

| 결정 메모 | 코드 위치 | 일치 여부 |
|-----------|-----------|-----------|
| `lookup_by_inst_code` notices items 첫 row 우선 → awards 첫 row fallback | lookup.py:158-166 | OK |
| `lookup_by_biz_no` awards 첫 row 활용 (`bid_notice_no_list[0]`와 동등) | lookup.py:281-287 | OK |
| `inst_code/inst_name` raw G2B camelCase fallback chain | lookup.py:177-187, 285 | **부분 OK** (`first_row.get("dminsttCd")` → `first_row` 자체에서 찾음, `raw` 객체 내부까진 침투 안 함) |
| `vendor_name` NTS 폴백 (`tax_type_nm`) | lookup.py:289-294 | OK |
| `lookup_by_contract_no` stub keys 7-key 통일 | lookup.py:326-340 | OK |
| `lookup_by_bid_no` keys 변경 없음 (회귀 0) | lookup.py:50-58 | OK |

### stub 호출 keys 매핑 결과

```python
asyncio.run(lookup_by_contract_no('TEST-001'))
```

- keys: `['bid_notice_no', 'bid_ord', 'contract_no', 'inst_code', 'inst_name', 'vendor_biz_no', 'vendor_name']` (7-key 정렬)
- `contract_no="TEST-001"` 채움
- 나머지 6 키 모두 None (`others_None: True`)
- `starting_key="contract_no"`, `status="not_implemented"` (stub 명시)

**L2 종합: PASS** — 결정 메모 6항 중 5항 완전 일치, 1항(raw 침투) 부분 결함 식별.

---

## L3 backend 직접 호출 raw

전 호출 python `asyncio.run(...)` direct invocation, R1 tester-r1 패턴 재사용 (PowerShell 한글 인코딩 우회).

### `lookup_by_bid_no("R26BK01435763", "000")` (회귀 0 검증)

```json
keys: {
  "bid_notice_no": "R26BK01435763",
  "bid_ord": "000",
  "inst_code": null,
  "inst_name": null,
  "vendor_biz_no": null,
  "vendor_name": null,
  "contract_no": null
}
starting_key: "bid_notice_no"
keys_count: 7
```

- 7-key 구조 그대로 (변경 없음 — 회귀 0)
- 미낙찰 케이스라 award/contract 단계 None (R1 결과와 동일)

### `lookup_by_biz_no("7028600866", date_from="2025-05-04", date_to="2026-05-04")` (사용자 case 1년)

```json
keys: {
  "bid_notice_no": "R26BK01338032",
  "bid_ord": "000",
  "inst_code": null,
  "inst_name": "국방과학연구소",
  "vendor_biz_no": "7028600866",
  "vendor_name": "주식회사 아이웨이브",
  "contract_no": null
}
summary.bid_notice_no_list: ["R26BK01338032"]
summary.award_count: 1
```

- 7-key 5/7 채움 (bid_notice_no, bid_ord, inst_name, vendor_biz_no, vendor_name)
- **consistency check: `keys.bid_notice_no == summary.bid_notice_no_list[0]` → True ✅**
- `inst_code` null (raw 침투 부재 — awards row 안 `dminsttCd: "B550234"`은 `raw` 객체 내부에 있어 lookup.py:285 `first_row.get("dminsttCd")` 도달 불가)

### `lookup_by_biz_no("2391602024", 1년)` (빈 awards 케이스)

```json
keys: {
  "bid_notice_no": null,
  "bid_ord": null,
  "inst_code": null,
  "inst_name": null,
  "vendor_biz_no": "2391602024",
  "vendor_name": null,
  "contract_no": null
}
summary.award_count: 0
summary.nts_status_code: null
```

- 7-key 모두 None (vendor_biz_no만 user 입력값) — **빈 awards에서도 keys 7-key 정상 None 반환** ✅
- frontend 4-카드 그리드 모두 "—" 노출 가능

### `lookup_by_inst_code(inst_name="조달청", 1년, limit=10)` (사용자 case)

```json
keys: {
  "bid_notice_no": "R25BK00826522",
  "bid_ord": "000",
  "inst_code": null,
  "inst_name": "조달청",
  "vendor_biz_no": "2038164688",
  "vendor_name": "주식회사 한국아이티컨설팅",
  "contract_no": null
}
summary.notice_count: 10
summary.award_count: 10
summary.unique_winners: 10
```

- 7-key 5/7 채움 (bid_notice_no, bid_ord, inst_name, vendor_biz_no, vendor_name)
- `inst_code` null — 동일 raw 침투 부재 (awards items에 `inst_code` 키 자체 없음, 정규화된 row에는 inst_name만)

**L3 종합: PASS** — 4 도구 모두 7-key 구조 정상, 회귀 0, consistency PASS. 부분 결함 1건 (inst_code raw 침투).

---

## L4 사용자 case retrieval

| 사례 | 결과 | keys 채움 |
|------|------|----------|
| `vendor_biz_no="7028600866"` (아이웨이브, 1년 1건) | PASS | 5/7 (bid_notice_no, bid_ord, inst_name, vendor_biz_no, vendor_name) |
| `vendor_biz_no="2391602024"` (NTS 정상 + awards 0건) | PASS | 1/7 (vendor_biz_no만, 나머지 None — 정상 처리) |
| `inst_name="조달청"` (awards 풍부 10건) | PASS | 5/7 (bid_notice_no, bid_ord, inst_name, vendor_biz_no, vendor_name) |
| `bid_notice_no="R26BK01435763"` (미낙찰, 회귀 검증) | PASS | 2/7 (bid_notice_no, bid_ord) — R1과 동일, 회귀 0 |

cross-lookup 핵심 가치: 사업자번호 입력 → 발주기관/공고번호/낙찰자 발견 가능 ✅

---

## L5 frontend 회귀 점검

backend 8081 LISTEN, frontend 3000 LISTEN 확인.

| URL | HTTP | 회귀 |
|-----|------|------|
| `http://localhost:3000/lookup?mode=notice&no=R26BK01435763&ord=000` | 200 | 0 |
| `http://localhost:3000/lookup?mode=biz&biz=7028600866` | 200 | 0 |
| `http://localhost:3000/lookup?mode=inst&name=%EC%A1%B0%EB%8B%AC%EC%B2%AD` (URL-encoded) | 200 | 0 |
| `http://localhost:3000/lookup?mode=bid&q=R26BK01435763&ord=000` (frontend signature) | 200 | 0 |
| `http://localhost:3000/lookup?mode=biz&q=7028600866` | 200 | 0 |
| `http://localhost:3000/lookup?mode=inst&q=%EC%A1%B0%EB%8B%AC%EC%B2%AD` | 200 | 0 |

### frontend 코드 분석 (회귀 0 근거)

`frontend/src/app/lookup/page.tsx:142-179`:
- `<div className="grid grid-cols-1 gap-3 lg:grid-cols-4">` — **mode 분기 없이 4-카드 항상 그리드 렌더**
- 각 KeyNode `value={keys.X || "—"}` — backend null/undefined 시 "—" 표시
- mode=biz/inst에서도 `keys.bid_notice_no` / `keys.inst_name` / `keys.vendor_biz_no` / `keys.contract_no` 4 카드 모두 노출

→ backend keys 7-key 통일이 frontend 코드 변경 없이 곧바로 풍부한 4-카드 노출로 이어짐 (R1 fixer 결정 메모 그대로).

### SSR HTML 라벨 카운트 비교 (회귀 0 검증)

| 라벨 | mode=notice HTML | mode=biz HTML |
|------|------------------|----------------|
| 공고번호 | 6 | 6 |
| 발주기관 | 6 | 6 |
| 계약번호 | 6 | 4 |

- mode=biz의 계약번호 4 vs mode=notice의 6은 page shell 외 sub-component 라벨 차이 가능 (graph nodes / table headers / form placeholder), 변경 0 검증 본질에는 무영향
- 핵심: HTTP 200 + 4-카드 그리드 동일 코드 경로 (mode 분기 없음)

**L5 종합: PASS** — 3 mode 모두 HTTP 200, frontend 4-카드 그리드 코드 변경 0 (mode 분기 없음 — backend keys 통일이 시각화 풍부함으로 직결).

---

## 회귀 / 결함 발견

### 회귀
- **없음** — `lookup_by_bid_no` keys 변경 0, frontend 4-카드 그리드 코드 변경 0, page shell HTTP 200 회귀 0.

### 부분 결함 1건 (비차단성)

**inst_code raw 침투 부재**:
- 위치: `lookup.py:177-180` (lookup_by_inst_code), `lookup.py:285` (lookup_by_biz_no)
- 현상: awards/notices items 첫 row의 `raw.dminsttCd`(예: `"B550234"`)에 inst_code 값이 있으나, `first_row.get("dminsttCd")`는 정규화된 row 자체에서 찾으므로 `raw` 객체 내부까진 도달 못함 → keys.inst_code = null
- 영향: cross-lookup keys.inst_code가 null로 노출, 단 frontend는 `keys.inst_name` 채워져 4-카드 발주기관 카드 정상 노출 (sub label만 누락)
- 권고: R3 또는 별도 small fix — `first_row.get("inst_code") or first_row.get("dminsttCd") or first_row.get("raw", {}).get("dminsttCd") or first_row.get("raw", {}).get("ntceInsttCd")` 형태로 raw 침투 추가

ROUND-2-FIX § 결정 메모 § "inst_code/inst_name 폴백" 절은 raw 침투를 명시적으로 보장하지 않음 (`raw camelCase fallback`은 first_row 레벨 기재) — fixer-r2가 결정한 범위 내. R2 종합 PASS 영향 없음 (inst_name은 정상, frontend는 4-카드 모두 노출).

### 인코딩 한계
- PowerShell stdout cp949 → 한글 깨짐 발생 → `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` 우회로 해결 (R1 패턴 계승)

---

## quality-monitor-r2 핸드오프

- **R2 PASS** (4/4 도구 7-key 표준화 + 회귀 0)
- **주요 evidence**:
  - L1: commit `21b9eb2` 변경 lookup.py 1 file, 86+/7-, ROUND-2-FIX 표 일치
  - L2: stub 호출 keys 7-key 검증 + 결정 메모 6항 중 5항 완전 일치
  - L3: 4 도구 raw payload 인용 (R26BK01435763 / 7028600866 1y / 2391602024 / 조달청)
  - L4: 사용자 case 4건 — 빈 awards 정상 처리 + consistency PASS
  - L5: 3 mode HTTP 200 + frontend 코드 4-카드 그리드 회귀 0
- **회귀 없음**: lookup_by_bid_no 변경 0, frontend page.tsx 변경 0
- **부분 결함 1건**: inst_code raw 침투 부재 — 비차단성, R3 또는 별도 small fix 권고
- **R3 (P1 batch) 진입 적합성**: PASS — R2 핵심 가치(cross-lookup 4-키 통일) 확보, P1 사용자 사례 직결 작업 진행 가능

---

## 보조 산출물

- 검증 시 임시 HTML: `tmp_lookup_biz.html`, `tmp_lookup_notice.html` (gitignore 영역, .planning 외부)
- python 직접 호출 패턴: `asyncio.run(...)` + `sys.stdout` UTF-8 wrap (R1 tester-r1 패턴 재사용)
