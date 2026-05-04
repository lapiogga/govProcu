# ROUND 1 TEST REPORT

> Phase 30 Round 1 — tester-r1 검증 결과.
> 입력: fixer-r1 commit `512b181` (3 files / 5 lines).
> 산출: 본 리포트 + quality-monitor-r1 핸드오프.

## 종합 PASS/FAIL

**R1 종합: PASS** (3/3 P0 small fixes 모두 검증)

## 검증 결과 매트릭스

| ID    | 항목                                  | L1 정적 | L2 논리 | L3 backend  | L4 user case | L5 frontend | 종합 |
|-------|---------------------------------------|--------|---------|-------------|--------------|-------------|------|
| P0-A  | trace stage5 NTS code 키 정합         | PASS   | PASS    | PASS        | PASS         | SKIP*       | PASS |
| P0-B  | agencies summary_pct.p75 슬롯 추가    | PASS   | PASS    | PASS        | PASS         | PASS        | PASS |
| P0-C  | analytics 사업자번호 fmtBizNo         | PASS   | PASS    | N/A         | PASS         | PASS        | PASS |

*P0-A L5 SKIP 사유: 검증 가능한 trace URL `R26BK01435763-000` 이 미낙찰/유찰 케이스라 winner_biz_no 부재 → ntsLabel 호출 경로 자체가 없음 (Stage 5 inactive). 그러나 L2/L3 로 backend `status_code` 응답 + frontend fallback chain 정합 확인되어 logical PASS.

---

## L1 정적 검증

### git show 512b181 --stat
```
frontend/src/app/agencies/page.tsx   | 3 ++-
frontend/src/app/analytics/page.tsx  | 2 +-
frontend/src/app/bids/trace/page.tsx | 5 +++--
3 files changed, 6 insertions(+), 4 deletions(-)
```

### 변경 라인 ROUND-1-FIX.md 표 일치 검증

- **agencies/page.tsx L183**: `lg:grid-cols-5` → `lg:grid-cols-6` ✅
- **agencies/page.tsx L188**: `<Stat label="p75" v={\`${s.p75?.toFixed(2)}%\`} />` 1행 추가 ✅
- **analytics/page.tsx L191**: `<VendorLink bizNo={v.biz_no} name={v.biz_no} />` → `<VendorLink bizNo={v.biz_no} formatBizNo />` ✅
- **bids/trace/page.tsx L406-407**: `const code = first.b_stt_cd;` → 주석 추가 + `const code = first.status_code || first.b_stt_cd || first.raw?.b_stt_cd;` ✅
- **bids/trace/page.tsx L411**: `return first.b_stt || "—";` → `return first.status || first.b_stt || first.raw?.b_stt || "—";` ✅

### TypeScript 컴파일

`cd frontend; npx tsc --noEmit` — **에러 없음** (출력 0줄).

---

## L2 단위/논리 검증

### P0-A — trace ntsLabel fallback chain

backend `app/tools/vendor.py:67-122` `check_business_status` 응답 구조 (vendor.py:107-116):
```python
items.append({
    "biz_no": raw.get("b_no"),
    "status_code": cd,                              # 정규화 코드 ("01"/"02"/"03")
    "status": _NTS_STATUS_CD.get(cd) or ...,        # 정규화 라벨 ("계속사업자")
    "tax_type": ...,
    "end_date": ...,
    "raw": raw,                                     # raw NTS 응답 (b_stt_cd / b_stt 보존)
})
```

frontend `bids/trace/page.tsx:407,411` ntsLabel 함수:
```ts
const code = first.status_code || first.b_stt_cd || first.raw?.b_stt_cd;
if (code === "01") return "계속사업자 (정상)";
if (code === "02") return "휴업";
if (code === "03") return "폐업";
return first.status || first.b_stt || first.raw?.b_stt || "—";
```

**정합 확인**:
- `first.status_code` (backend 정규화 키) 우선 매칭 → "계속사업자 (정상)" 반환 ✅
- 실제 backend 응답에 `status_code="01"` 있음 (L3 검증 참조)
- raw fallback도 보존 (`raw.b_stt_cd` 도달 가능)
- 최종 라벨 fallback: `status` (정규화) → `b_stt` → `raw.b_stt` → "—" 4단계

### P0-B — agencies summary_pct.p75 표시

backend `app/tools/analytics.py:464-474` `analyze_agency_price_pattern.summary_pct` 9-key:
```python
"summary_pct": {
    "mean", "median", "std", "min", "max", "p10", "p25", "p75", "p90"
}
```

frontend `agencies/page.tsx:183-190` Stat 6 슬롯 (lg:grid-cols-6):
- 평균(mean) / 중앙값(median) / p10 / p25 / **p75 (신규)** / p90

**정합 확인**: p75 키가 backend 응답에 명시 (analytics.py:472), frontend에서 `s.p75?.toFixed(2)+'%'` 안전 표시 ✅
- grid-cols-6 → md 이하는 grid-cols-2 유지 (모바일 레이아웃 보존)
- 디자인 토큰 변경 없음 (Tailwind JIT 표준 클래스)

### P0-C — analytics VendorLink formatBizNo

`frontend/src/components/EntityLink.tsx:23-56` VendorLink 동작:
```ts
const display = name
    ? trim(name)
    : formatBizNo
        ? fmtBizNo(biz)        // ← formatBizNo=true + name 미지정 시 자동 포맷
        : biz;
```

`analytics/page.tsx:188-191` 두 컬럼:
- 1열 (업체명): `<VendorLink bizNo={v.biz_no} name={v.name} />` — name 우선
- 2열 (사업자번호): `<VendorLink bizNo={v.biz_no} formatBizNo />` — name 없음 + formatBizNo=true → fmtBizNo(biz_no) 자동 적용

**정합 확인**: import 추가 없음 (VendorLink 내부 fmtBizNo 사용). raw 10자리 → `XXX-XX-XXXXX` 변환 보장.

---

## L3 backend 직접 호출 검증

### Endpoint 결정
- backend FastMCP streamable HTTP: `POST http://localhost:8081/mcp`
- AuthMiddleware → `Authorization: Bearer dev-token-replace-me` 필요 (env `MCP_API_TOKENS`)
- JSON-RPC 2.0 envelope: `method=tools/call`, `params={name, arguments}`

### P0-A 검증 — `check_business_status(biz_nos=["7028600866"])`

응답 (`structuredContent.items[0]`):
```json
{
  "biz_no": "7028600866",
  "status_code": "01",
  "status": "계속사업자",
  "tax_type": "...",
  "end_date": null,
  "raw": {
    "b_no": "7028600866",
    "b_stt": "계속사업자",
    "b_stt_cd": "01",
    ...
  }
}
```
✅ `status_code="01"`, `raw.b_stt_cd="01"` 모두 도착 → frontend fallback chain 모두 매칭 가능.

### P0-A 추가 — `check_business_status(biz_nos=["2391602024"])`
응답: `biz_no=2391602024`, `status_code=01`, `raw.b_stt_cd=01` ✅

### P0-B 검증 — `analyze_agency_price_pattern(inst_name="조달청", date_from=20250504, date_to=20260504)`
(* PowerShell HTTP 경로의 한글 인코딩 한계로 backend tool 직접 호출, `PYTHONUTF8=1` 설정.)

응답:
```
sample_count=34
summary_pct keys: ['mean', 'median', 'std', 'min', 'max', 'p10', 'p25', 'p75', 'p90']
  has p75? True  -> p75=100.0
  full: {"mean": 97.937, "median": 100.0, "std": 11.14, "min": 33.958, "max": 100.0, "p10": 99.401, "p25": 99.801, "p75": 100.0, "p90": 100.0}
```
✅ p75 키 존재, 9-key 모두 정합.

추가:
- 한국수자원공사: `p75=88.216`, 9-key 모두 ✅
- 한국전력공사: `p75=98.37`, 9-key 모두 ✅

### P0-C 검증
backend 변경 없음 — frontend prop 변경뿐. L5에서 렌더 결과로 검증.

---

## L4 사용자 case retrieval

| case                       | 결과 |
|----------------------------|------|
| 7028600866 NTS status_code | ✅ 도착 ("01" 계속사업자) |
| 2391602024 NTS status_code | ✅ 도착 ("01" 계속사업자) |
| "조달청" agency p75       | ✅ 도착 (100.0%) |

---

## L5 frontend 화면 (curl HTML)

### `/agencies?name=조달청&from=2025-05-04&to=2026-05-04`
- HTTP 200 / 264738 bytes
- HTML 내 텍스트 검사: **`p75`, `p10`, `p25`, `p90` 4 라벨 모두 FOUND** ✅
- p75 슬롯 정상 노출 확인.

### `/analytics?bizType=용역&from=2025-05-04&to=2026-05-04`
- HTTP 200 / 203179 bytes
- 사업자번호 하이픈 포맷 매칭 (regex `\d{3}-\d{2}-\d{5}`):
  - `624-81-02142`, `113-81-84945`, `211-81-08009`, `215-86-11516`, `229-81-37320` 등 다수 ✅
  - HTML context: `entity-link font-medium` 클래스 + `title="업체 프로필 — 624-81-02142"` + children 동일 → VendorLink formatBizNo 모드 정상 렌더
- raw 10자리 사업자번호가 `<td tabular-nums>` 안에 직접 표시되는 케이스 0건 (회귀 없음) ✅

### `/bids/trace?no=R26BK01435763&ord=000`
- HTTP 200 / 92543 bytes
- Stage 4: "낙찰 — 미낙찰/유찰" → winner 부재
- Stage 5: "낙찰자 NTS 검증 — —" → ntsLabel 미호출 경로 (winner_biz_no 없으므로)
- 본 URL로는 P0-A 시각 검증 불가 (다른 winner 있는 trace URL 필요), L2/L3로 logical PASS.

---

## 회귀 점검

### TypeScript 컴파일
- `npx tsc --noEmit` 0 에러 ✅

### 영향 받지 않는 화면
- vendor profile (`/vendors/[bizNo]`) — VendorLink 사용처 다수, prop 시그니처 비호환 변경 없음 (formatBizNo는 default false) ✅
- search, lookup — 변경 없음 ✅
- analytics 첫 컬럼 (업체명) — `name={v.name}` 그대로, prop 추가/제거 없음 ✅
- agencies grid — md 이하 `grid-cols-2` 유지, lg에서만 `grid-cols-6` (모바일 레이아웃 보존) ✅

### 디자인 토큰
- Tailwind JIT 표준 클래스 (`lg:grid-cols-6`) — config 변경 없음 ✅

### import / 식별자
- analytics: import 변경 없음 (VendorLink 내부 fmtBizNo 사용) ✅
- agencies: 신규 Stat 슬롯 1개만 추가, 변수/import 동일 ✅
- trace: ntsLabel 함수 내부만 수정 ✅

---

## 결함/회귀 발견

**없음.**

3 P0 small fixes 모두 의도대로 적용되었고, backend 정합성 (status_code / summary_pct.p75) + frontend 렌더 (p75 라벨, 하이픈 사업자번호) 검증 완료. 회귀 없음.

---

## quality-monitor-r1 핸드오프 요약

- **R1 PASS** (3/3 P0)
- **주요 evidence**:
  - L3 backend: `check_business_status` 응답에 `status_code="01"` 명시 (vendor.py:111), `analyze_agency_price_pattern.summary_pct.p75` 9-key 모두 존재 (analytics.py:472)
  - L5 frontend: `/agencies` p75 라벨 노출 + `/analytics` 사업자번호 `XXX-XX-XXXXX` 하이픈 포맷 다수 검출
  - L1 TypeScript: 컴파일 0 에러
- **회귀**: 없음
- **다음 단계 적합성**: R2 (P0-D backend lookup keys 표준화) 진행 가능

---

## 참고 — 검증 보조 자료

- backend gating: `Authorization: Bearer dev-token-replace-me` (`.env` MCP_API_TOKENS)
- backend port: 8081 (uvicorn / FastMCP streamable_http)
- frontend port: 3000 (Next.js dev)
- 사용 스크립트:
  - `tmp/test-nts-check.ps1` — NTS 7028600866
  - `tmp/test-nts-check2.ps1` — NTS 2391602024
  - `tmp/test-agency-py.py` — analyze_agency_price_pattern (조달청/한국수자원공사/한국전력공사)
  - `tmp/test-frontend-screens.ps1` — agencies/analytics/trace HTML 검사
  - `tmp/test-trace-detail.ps1` — trace HTML stage 분석
  - `tmp/test-analytics-detail.ps1` — analytics 사업자번호 하이픈 검출
