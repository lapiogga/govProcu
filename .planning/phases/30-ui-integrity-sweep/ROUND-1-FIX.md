# ROUND 1 FIX REPORT

> Phase 30 Round 1 — fixer-r1 작업 결과.
> 입력: DIAGNOSIS-G2/G3/G4 P0 small-fix 3건.
> 산출: frontend 단일 atomic commit + 본 리포트.

## 적용한 변경

| ID   | 파일                                          | line  | before                                                   | after                                                                                                          | 근거                                  |
|------|-----------------------------------------------|-------|----------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|---------------------------------------|
| P0-A | `frontend/src/app/bids/trace/page.tsx`        | 406   | `const code = first.b_stt_cd;`                           | `const code = first.status_code \|\| first.b_stt_cd \|\| first.raw?.b_stt_cd;`                                 | DIAGNOSIS-G2 § Stage5 NTS 정규화 키   |
| P0-A | `frontend/src/app/bids/trace/page.tsx`        | 410   | `return first.b_stt \|\| "—";`                            | `return first.status \|\| first.b_stt \|\| first.raw?.b_stt \|\| "—";`                                          | 동일 (fallback chain 일관)            |
| P0-B | `frontend/src/app/agencies/page.tsx`          | 183   | `lg:grid-cols-5`                                         | `lg:grid-cols-6`                                                                                               | DIAGNOSIS-G3 § summary_pct 9-key 노출 |
| P0-B | `frontend/src/app/agencies/page.tsx`          | 188   | (없음)                                                   | `<Stat label="p75" v={\`${s.p75?.toFixed(2)}%\`} />` 1행 추가                                                   | DIAGNOSIS-G3 (0.7 win prob 핵심)      |
| P0-C | `frontend/src/app/analytics/page.tsx`         | 191   | `<VendorLink bizNo={v.biz_no} name={v.biz_no} />`        | `<VendorLink bizNo={v.biz_no} formatBizNo />`                                                                  | DIAGNOSIS-G4 § 시장점유 표 fmtBizNo   |

총 3 파일, 5 라인 변경 (+추가 1행).

## 결정 메모

- **P0-A `status` 폴백 추가**: backend `check_business_status` (vendor.py:111-112)는 코드뿐 아니라 `status` 라벨도 정규화. raw `b_stt`보다 정규화된 `status`를 먼저 표시해야 일관성 유지.
- **P0-B grid 5→6**: 다른 페이지 디자인 토큰 파괴 없음. 기존 `grid-cols-2` (모바일 2열) 유지, lg 브레이크포인트만 6열로 확장.
- **P0-C `formatBizNo` flag 채택**: `name={fmtBizNo(v.biz_no)}` 대신 `VendorLink`의 `formatBizNo` prop 사용 (line 188 `name={v.name}` 컬럼과 역할 분리 명확화). `EntityLink.tsx:42-46` 로직이 `name` 미지정 + `formatBizNo=true` 시 자동 포맷 — import 추가 불필요.

## Commit

- hash: `512b181`
- title: `fix(frontend): P30-R1 P0 small — trace NTS / agencies p75 / analytics fmtBizNo`
- staged 파일: 3개 (`frontend/src/app/bids/trace/page.tsx`, `frontend/src/app/agencies/page.tsx`, `frontend/src/app/analytics/page.tsx`)
- 제외: `.planning/PROMPTS-LOG.md`, `logs/WORK-LOG.md`, untracked 자산 (다른 컨텍스트)

## 자체 sanity check

- [x] Read → Edit 페어링 (3 파일 모두 사전 Read)
- [x] import 누락 없음 (`fmtBizNo`는 `VendorLink` 내부에서만 사용 — analytics는 `formatBizNo` prop만 추가)
- [x] TypeScript syntax: optional chaining + 단순 prop 변경 — type-safe
- [x] grid-cols-6: Tailwind 표준 클래스 (JIT 컴파일 OK)
- [x] 의도 외 라인 수정 없음 (`git diff` 5 hunks만)

## 핸드오프 메시지 (tester-r1 앞)

> R1 fix 완료, 검증 부탁.
> - 적용 ID: P0-A / P0-B / P0-C
> - commit: `512b181`
> - 상세: `.planning/phases/30-ui-integrity-sweep/ROUND-1-FIX.md`
> - L1 (frontend hot-reload): 직접 검증 가능
> - L3 (NTS payload raw 검증): backend `check_business_status` 응답에 `status_code` 키가 실제로 들어오는지 확인 (vendor.py:111-112).
> - 회귀 우려: agencies grid lg:grid-cols-6 — md 이하 화면에서 grid-cols-2 유지되므로 깨짐 없음.
