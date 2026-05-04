# ROUND 1 QUALITY REPORT (Phase 31)

> **라운드**: Phase 31 Round 1 — F18 (R-prefix 단건 inqryDiv=2) + F20 (외자 endpoint 추가).
> **검증 commit**: `69da6cb` — backend-only (`app/tools/bid.py` + `app/schemas/bid.py`).
> **기간**: 2026-05-04 (KST) 단일 라운드.
> **작성자**: quality-monitor-p31-r1.
> **입력**: PLAN.md, DOSSIER-OFFICIAL.md, POC-G2B.md, DOSSIER-LAW.md, ROUND-1-FIX.md, ROUND-1-TEST.md.

---

## 라운드 종합 평가

- **적용 fix**: 2/2 PASS (F18 + F20, atomic commit `69da6cb`).
- **회귀**: 0건 (R1 변경 영역 한정).
- **baseline 대비 P0 잔여**: 4 → 2 (50% 해소).
- **L6 신규 차원 적용** — err-022 backend raw 응답과 나라장터 웹 UI 표시값 1:1 일치 검증.
- **사용자 보고 사례 적중** — R25BK00755515 (역사지리정보DB) + R26BK01435763 (경찰청 ISP) 정확 매칭.
- **최종 권고**: **APPROVED — R2 즉시 진입**.

---

## 1. 작업 정합성 평가

| 항목 | 평가 | 근거 |
|------|------|------|
| F18 POC #4 적용 정확성 | **EXCELLENT** | ROUND-1-TEST § L3 호출 1·2 — 5종 fan-out 중 Servc 1개에서만 hit, `lookup_mode="inqryDiv=2+bidNtceNo"`, `chunks_used=0` (기간 unset) — POC #4 raw payload와 100% 정합 |
| F18 `-` suffix 통합 형태 분리 | **EXCELLENT** | `R25BK00755515-000` 입력 시 `target_no=R25BK00755515` + `target_ord_norm="0"` 자동 분리, ord 검증 추가 — 사용자 발화 #38 일관 형태 처리 |
| F18 `_infer_period_from_bid_no` 폐기 정합 | **EXCELLENT** | 시그니처(`tuple[str|None, str|None]`) 보존 + `(None, None)` 반환 — DOSSIER §3.1 1개월 제한 회피 + award.py·alerts.py·get_bid_notice_detail 등 caller 호환 유지 |
| F20 외자 endpoint resolver 추가 | **EXCELLENT** | `_resolve_bid_endpoints(None)` 4종(Servc/Cnstwk/Thng/Frgcpt) + `_resolve_bid_endpoints("외자")` Frgcpt 단독 — DOSSIER §1.2 4분류 endpoint 매핑 정합 |
| F20 schema biz_type Literal 확장 | **EXCELLENT** | `Literal["공사","용역","물품","외자",None]` — pydantic 검증 호환, 기존 caller 미영향 |
| 단일 round / atomic commit | **EXCELLENT** | 1 commit (`69da6cb`) = F18 + F20 + cache prefix `bid_v31` + schema 1라인 — rollback 단위 명확 |
| 회귀 0 검증 | **EXCELLENT** | ROUND-1-TEST § L3 회귀 — `keyword="정보화"` + date 명시 시 단건 분기 미진입(`lookup_mode=None`), 4종 fan-out + chunks_used=1 유지 |
| 변경 영역 외 보전 | **EXCELLENT** | F19/F21/F22는 R2 영역으로 명시 분리 — scope creep 없음 |

---

## 2. 검증 깊이 (L6 신규 차원 평가)

| 차원 | 결과 | 비고 |
|------|------|------|
| **L1 정적** | PASS | git diff stat 일치 (3 files, +217/-26), import 정상, `inspect.signature` R0 동등 |
| **L2 논리** | PASS | 8개 결정 메모(분기 조건, 4종 resolver, 5종 fan-out, cache prefix, ord 분리) 코드 라인 단위 매핑 검증 |
| **L3 backend raw** | PASS | 4 호출 + 회귀 1 호출 — POC #4 raw payload 100% 재현 (`presmptPrce=101818182`, `srvceDivNm="일반용역"`, `ppswGnrlSrvceYn="Y"`) |
| **L4 사용자 case** | PASS | R25BK00755515 (POC #4 적중) + R26BK01435763 (R-prefix 2026년 추가 evidence) — 두 case 모두 Servc 단일 endpoint hit |
| **L5 frontend** | PASS | `/bids/trace?no=R25BK00755515&ord=000` HTTP 200 (116ms), `/bids` `/lookup` `/vendors` `/agencies` `/` HTTP 200 — frontend 변경 0건 + 회귀 0 |
| **L6 G2B vs 나라장터 UI** | **PASS** | err-022 표시값(공고번호/공고명/공고기관/수요기관/사업분류) backend raw 응답과 **1:1 일치** — 신규 차원 적용 첫 라운드 효과 확인 |

### L6 신규 차원 효과 평가

L6은 Phase 31 신규 도입 차원(PLAN § 5)으로, "G2B 응답값 vs 나라장터 웹 UI 표시값 일치"를 명시적으로 검증한다. tester가 err-022 capture(개찰결과 화면)의 입찰공고 본정보 5개 필드(공고번호/공고명/공고기관/수요기관/사업분류)를 backend raw 응답과 매핑한 결과 5/5 일치. 추가로 추정가 부분은 err-022 화면에 직접 표시되지 않으나 입찰금액 110,800,000 / 투찰률 99.927% 역산으로 backend `presmptPrce=101,818,182` (부가세 별도) 정합 검증 — 간접 evidence로 합당.

**평가**: L6은 사용자 발화 #48 신뢰 회복 요구("raw evidence 명시") 충족. **신규 차원 효과적**. R2~R5 라운드에서도 표준 차원으로 적용 권고.

### 검증 깊이 종합

L1~L6 6 차원 모두 PASS + 각 차원에서 raw evidence 명시 — Phase 30 R1~R5 5 차원(L1~L5) 대비 깊이 +20% 확장. tester가 R1 책임 영역 외 부수 관찰(`endpoints_used` 표기 누락, `/bids?keyword=` HTTP 400)을 정확히 R1 영역 외로 분리한 점도 평가 정밀성 입증.

---

## 3. baseline 대비 진척

### Phase 31 결함 매트릭스 진척 (PLAN § 1 기준)

| 분류 | baseline (Phase 31 시작) | R1 후 | 변화 | 비고 |
|------|--------------------------|-------|------|------|
| **P0** (F18, F19, F20, F21) | 4 | 2 | **-2 (F18, F20 해소)** | F19+F21은 R2 (PPSSrch 전환) |
| **P1** (F22, F23, F25, F26, F27, F28) | 6 | 6 | 0 | R3(F23), R4(F22), R5 + 별도 라운드(F25~F28) |
| **별도 phase** (K1) | 1 | 1 | 0 | Phase 32 권고 (kwater 외자 endpoint) |

### 결함 해소율

- **P0**: 50% (2/4)
- **전체**: 18% (2/11)
- **R1 단독 기여**: F18 + F20 — 두 결함 모두 사용자 발화 #38 (R-prefix 1년+ 미매칭) + 차세대 나라장터 외자 4분류 정합 직결.

### 잔여 P0 (F19, F21)

| ID | R2 적용 예정 | 의존도 |
|----|------------|---------|
| F19 (발주기관 LIKE) | PPSSrch endpoint 전환 + ntceInsttNm/dminsttNm 직접 전달 + fan-out (POC #7) | 단건 모드 R1 격리 → 일반 검색 모드 PPSSrch 전환 영향 단독 |
| F21 (srvceDivNm 응답 추가) | `_normalize_notice` BidNoticeSummary 필드 확장 (`srvce_div`, `ppsw_gnrl_yn`) | R2 PPSSrch 응답 정규화와 동시 적용 |

**평가**: R1 작업 분할(단건 모드 vs PPSSrch 전환)이 R2 진입 충격 완화에 합당. F19/F21을 R1에 동반 적용했다면 atomic 영역이 너무 커져 회귀 위험 ↑.

---

## 4. Phase 30 vs Phase 31 R1 비교

| 차원 | Phase 30 R1 | Phase 31 R1 | 평가 |
|------|------------|-------------|------|
| 적용 fix | 3 P0 small fixes | 2 P0 (F18 + F20) | 작업량 -33% / 단건모드 신설 책임 +50% |
| 검증 차원 | L1~L5 (5차원) | L1~L6 (6차원, L6 신규) | 깊이 +20% |
| raw evidence 적용 | HTTP 200 + 코드 정합 | POC raw payload 1:1 매칭 + err-022 capture 대조 | **POC 우선 정책 효과 확인** |
| 사용자 사례 영향 | (해당 fix 영역에 직접 case 없음) | F18 R25BK00755515 + R26BK01435763 직접 적중 | **사용자 신뢰 회복 직결** |
| atomic commit 단위 | 3 fixes 1 commit | 2 fixes 1 commit | 동등 — rollback 단위 일관 |
| 회귀 (round 단위) | 0 | 0 | 동등 |

### 핵심 변별

- **POC raw evidence 우선 정책**: Phase 31은 ROUND 1 진입 전 POC-G2B.md를 통해 5종 endpoint 단건 fan-out + Servc 1개 hit 패턴을 직접 호출 검증 → fixer가 "구현 후 검증" 대신 "검증 후 구현" 흐름. 사용자 발화 #48 신뢰 회복 요구 충족.
- **L6 신규 차원**: Phase 30은 backend 정합까지 검증, Phase 31은 backend ↔ 나라장터 웹 UI 매핑까지 검증 — 사용자 화면 직결성 강화.

---

## 5. 사용자 보고 사례 영향

### F18 직접 적중 사례

| bid_no | 표시 정보 | R1 검증 |
|--------|----------|---------|
| **R25BK00755515** | "2025년도 역사지리정보DB 구축사업" / 조달청 서울지방조달청 / 교육부 국사편찬위원회 / 일반용역 | ROUND-1-TEST § L3 호출 1·2 — Servc endpoint 1개 hit, raw 7개 필드 일치 ✅ |
| **R26BK01435763** | "치안정책연구소 경찰패널 데이터 아카이브 구축을 위한 정보화전략계획(ISP) 수립 연구용역" / 경찰청 경찰대학 / 일반용역 | ROUND-1-TEST § L4 — Servc endpoint 1개 hit ✅ |

### 신뢰 회복 효과

- **사용자 발화 #38**: "1년 이상 매칭 안 됨" → R1 후 R-prefix 단건 모드 inqryDiv=2 + bidNtceNo 직접 호출 → **기간 unset에서 정상 매칭** (POC #4 검증 + L3 호출 1 재현).
- **사용자 발화 #48**: "raw evidence 명시" → R1은 POC payload + L3 raw payload 두 단계 명시 → **충족**.

### 외자 evidence (F20)

ROUND-1-TEST § L3 호출 4 — `biz_type="외자"` 단독 호출 → Frgcpt endpoint hit, `R26BK01260236` (고전류용 전위차분석기), `R26BK01260119` ("(외자)고반복률펨토초발진기시스템") 등 외자 명시 row 다수 (totalCount=36/1개월). 외자 검색 누락 결함 해소 확정.

---

## 6. 회귀 추세

| Round | 회귀 | 비고 |
|-------|------|------|
| Phase 30 R1 | 0 | small fixes |
| Phase 30 R2 | 0 | |
| Phase 30 R3 | **1 차단** | backend 시그니처 mismatch — R3.5에서 회복 |
| Phase 30 R3.5 | 회복 | uvicorn 재기동 절차 도입 |
| Phase 30 R4 | 0 | sanity check 강화 |
| Phase 30 R5 | 0 | |
| **Phase 31 R1** | **0** | **시작점 양호** |

### Phase 30 학습 누적 효과 검증

- **R3 학습 (backend 시그니처 cross-check)**: ROUND-1-FIX § "회귀 안정성"에서 `_infer_period_from_bid_no` 시그니처 보존(`tuple[str|None, str|None]`) + caller 7개(`award.py`, `alerts.py`, `lookup.py`, `multi_agency.py`, `analytics.py`, `workflow.py`, `server.py`) 호환 명시 검증 → **사전 cross-check 적용 OK**.
- **R3.5 학습 (uvicorn 재기동 절차)**: ROUND-1-TEST § L3 "backend 가동 상태"에서 PID 37168 시작 시각(`14:15:37`) > commit 적용 시각(`10:24:16`) 명시 → **재기동 후 새 코드 로드 검증 OK**.
- **R4 학습 (sanity check 강화)**: ROUND-1-FIX § "자체 sanity check" 6개 항목(L1 시그니처/caller/schema, L3 raw/응답/회귀) — fixer 단계에서 self-validation → tester L1~L6과 별도 안전망 → **이중 안전망 OK**.

**평가**: Phase 30 5-round 학습 패턴 사전 적용 → Phase 31 R1 회귀 0 시작점 확립. R2 진입 후에도 동일 패턴 유지 권고.

---

## 7. R2 진입 적합성

### 평가: **APPROVED — R2 즉시 진입**

### 근거

1. R1 atomic commit(`69da6cb`) — rollback 단위 명확, 단건 모드 격리 정합.
2. 단건 모드(R1) ↔ 일반 검색 모드(R2) 코드 분기 명확(`bid.py:226 if inp.bid_notice_no and not inp.date_from and not inp.date_to:`) — R2 PPSSrch 전환이 단건 모드에 영향 없음.
3. R2 적용 대상 결함(F19, F21, F22 일부) 모두 일반 검색 모드 한정 — R1 격리 영역 보전.
4. POC #1·#2·#3·#5·#7 raw evidence 사전 확보 — fixer가 "검증 후 구현" 진입 가능.

### R2 권고 강화 항목 (Phase 30 학습 + R1 정합 유지)

R2는 **Phase 31에서 가장 큰 변경**(PPSSrch endpoint 전환 + fan-out + 응답 정규화 확장). 다음 8개 항목 의무 적용 권고:

1. **PPSSrch endpoint vs 단일조회 endpoint 분기 명확화**
   - `search_bid_notices` 모드 분기: `bid_notice_no` 단건 모드(R1 유지) vs 일반 검색 모드(R2 신규 PPSSrch 전환).
   - PPSSrch endpoint inqryDiv 의미는 단일조회와 다름(DOSSIER §2 패턴 D — 1=공고게시일시, 2=개찰일시) → inqryDiv 매핑 endpoint별 분기 필수.
   - resolver: `_resolve_bid_endpoints_ppssrch(None)` → 5종(Cnstwk/Servc/Thng/Frgcpt/Etc).

2. **ntceInsttNm + dminsttNm AND 회피 — fan-out 구현 (POC #7 evidence)**
   - 동시 전달 = AND (POC #7: A=2336, B=63, C=19) → 단일 input 통합 UX는 두 호출 fan-out + bidNtceNo 기반 dedup 합집합 필수.
   - 발화 #46 "공고기관 == 수요기관 동일 대부분" 합당 적용.

3. **srvceDivNm 응답 추가 (F21)**
   - `_normalize_notice` 변경 — `srvce_div = raw.get("srvceDivNm")`, `ppsw_gnrl_yn = raw.get("ppswGnrlSrvceYn")` 추가.
   - `BidNoticeSummary` schema 필드 추가 — `srvce_div: str | None`, `ppsw_gnrl_yn: Literal["Y","N"] | None`.
   - PPSSrch는 bsnsDivNm=null (POC #5) — 단건조회 응답과 다름 명시.

4. **dmndInsttNm fallback (PubStd 호환)**
   - 일부 API(PubDataOpnStdService)는 dmndInsttNm 필드 사용. backend 정규화에 fallback 추가 권고.

5. **cache prefix `bid_v31` → `bid_v32` (R2 변경 명시)**
   - PPSSrch 전환은 응답 형태 변경 → 캐시 무효화 필수.

6. **backend 시그니처 cross-check 의무 (R3 학습)**
   - `search_bid_notices` 시그니처 변경 가능성(인자 추가) → caller 7개(`award.py` 등) 호환 사전 검증.
   - `_normalize_notice` 반환 type 확장 → BidNoticeSummary 사용처 grep 후 영향 분석.

7. **uvicorn 재기동 절차 (R3.5 학습)**
   - commit 시각 vs uvicorn PID 시작 시각 명시 검증 — tester L3 진입 전 가드.

8. **L6 evidence — err-024 (국방부 국군재정관리단)**
   - F19 PPSSrch + dminsttNm="국방부" LIKE 검증 (POC #2 evidence + err-024 capture 매핑).
   - L6 차원 R2 표준 적용 — backend raw vs 사용자 화면값 1:1 매핑.

### R2 진입 후 위험 요소 (사전 식별)

- **PPSSrch endpoint 응답 형태 변경 가능성**: 단일조회와 응답 필드 차이 가능 (예: bsnsDivNm null) → tester L3 raw dump 강화 필수.
- **fan-out 호출수 증가**: 단일 endpoint → 2 endpoint(ntceInsttNm + dminsttNm) × N chunks → TPS 30 limit 근접 감시 필수.
- **응답 dedup 키**: bidNtceNo 단독 vs (bidNtceNo, bidNtceOrd) 페어 — POC raw에서 ord 정상 도착 확인 필수.

---

## 8. 메타 평가

### fixer-p31-r1

- **평가**: **EXCELLENT**
- **근거**:
  - POC #4 raw evidence 정확 적용 — 5종 fan-out 패턴 + 기간 unset 호출 그대로 구현.
  - `_infer_period_from_bid_no` 폐기 시 시그니처 보존 + caller 호환 검증 — Phase 30 R3 학습 사전 적용.
  - atomic commit 단위 적정(F18 + F20 = 단건 모드 + 외자 endpoint, 두 결함 모두 R-prefix 차세대 나라장터 정합 영역).
  - cache prefix bumping 명시.
- **개선 여지**: ROUND-1-FIX 결함/보류 섹션 — "없음" 명확. Phase 30 R5 패턴 동등.

### tester-p31-r1

- **평가**: **EXCELLENT**
- **근거**:
  - L1~L6 6 차원 모두 raw evidence + line 단위 매핑.
  - L6 신규 차원 적용 첫 라운드 — err-022 capture 5개 필드 1:1 매핑 정확.
  - 부수 관찰(`endpoints_used` 표기 누락, `/bids?keyword=` HTTP 400) R1 책임 영역 외 정확 분리.
  - 회귀 검증(`keyword="정보화"` 단건 모드 미진입) — R0 동작 동등성 확인.
  - uvicorn PID 시작 시각 vs commit 시각 명시 (Phase 30 R3.5 학습 적용).
- **개선 여지**: 호출 3 케이스 `endpoints_used` 표기 누락 부수 관찰 — R0 시점 동일이라 R1 영역 외이지만 backlog로 기록 권고(R5 종합 회귀에서 처리).

### 협업

- **평가**: **정합**
- **근거**: fixer가 ROUND-1-FIX § "핸드오프 메시지 (tester-p31-r1 앞)"에서 L3 핵심 검증 포인트 3개 + L4 사용자 case 2개 + 회귀 변경 0 보장 영역 + R2 보강 영역 명시 → tester가 동일 항목 L3·L4·회귀로 1:1 검증 → 핸드오프 정밀 매핑 OK.

---

## 9. 최종 권고

### **APPROVED — R2 진입 OK**

R1은 Phase 31의 토대 라운드로서, POC raw evidence 우선 정책 + L6 신규 차원 적용 + Phase 30 5-round 학습 누적 효과 모두 합당 적용되었다. F18 + F20 atomic 적용 + 회귀 0 + 사용자 보고 사례 직접 적중(R25BK00755515 + R26BK01435763) → **사용자 신뢰 회복 시작점 확립**.

R2(PPSSrch 전환 + fan-out + srvceDivNm 응답 추가)는 Phase 31 최대 변경이므로, § 7 권고 강화 항목 8개 의무 적용 후 발주 권고. fixer-p31-r2 작업 시 R1 격리 영역(`bid_notice_no` 단건 모드 분기) 보전 필수.

### R3 진입 사전 조건

- R2 commit atomic + 회귀 0 + L6 evidence(err-024 등) 매핑 검증 → R3(F23 frontend 3계층 dropdown) 진입 적합.
