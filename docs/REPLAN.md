# GovProcu MCP 서버 — 계획 재수립 (REPLAN v2)

> 작성: 2026-05-02 00:24 KST  
> 사용자 지시(2026-05-02): "입찰의 전 생애주기(사전규격→공고→개찰→낙찰→응찰업체) 통합 추적이 핵심 가치"

---

## 1. 비전 재정렬

### 1.1 사용자 핵심 요구

> **"국가 입찰 한 건을 입력하면, 그 입찰의 사전규격·본 공고·개찰내역·낙찰정보·낙찰업체·응찰업체까지 전 생애주기를 한 번에 조회·확인할 수 있어야 한다."**

### 1.2 기존 v1 대비 변경점

| 항목 | v1 (지금까지) | v2 (재수립) |
|------|--------------|-------------|
| 설계 단위 | API별 도구 나열 (15개 평면) | **시나리오 기반 통합 워크플로우** + 단위 도구 |
| 가치 단위 | 단일 API 호출 결과 | "한 입찰의 전 생애" / "한 업체의 입찰 이력" |
| 도구 구조 | Tier 1만 (단위 도구 14개) | **Tier 1 단위 + Tier 2 통합 워크플로우** 2계층 |
| 우선순위 | search_bid_notices 단독 PoC | trace_bid_lifecycle 풀 PoC |
| 검증 시연 | "입찰공고 검색이 되네" | "이 입찰 어떻게 끝났나? → 한 번에 답" |

### 1.3 시나리오 (사용자 가치)

```
사용자: "공고번호 20240101234-00 이 입찰, 어떻게 됐어?"
↓
서버: trace_bid_lifecycle("20240101234-00")
  → 사전규격: 2024-01-15 공시, 의견수렴 7건
  → 본 공고: 2024-02-01 공고, 추정가 12억, 기초금액 11.8억
  → 개찰: 2024-02-20 개찰, 응찰자 7개사, 낙찰하한가 88%
  → 낙찰: ㈜아이웨이브 (1234567890), 낙찰가 10.4억, 낙찰률 88.1%
  → 응찰업체 7개사: { biz_no, 업체명, 응찰가 }
  → 낙찰업체 NTS 검증: 계속사업자, 일반과세자, b_stt_cd=01
↓
사용자: "낙찰업체 다른 입찰 이력 보여줘"
↓
서버: vendor_profile("1234567890")
  → NTS 진위 + 최근 낙찰 12건 + 평균 낙찰률 87.3% + 주력 업종
```

---

## 2. 도구 매트릭스 v2

### Tier 1 — 단위 조회 도구 (영역별)

| # | 영역 | 도구 | API | 상태 (5/2 00:24) |
|---|------|------|-----|------|
| 1 | bid | `search_bid_notices` | BidPublicInfoService | ✅ 구현 (146줄) |
| 2 | bid | `get_bid_notice_detail` | BidPublicInfoService | 🟡 스텁 → 실 구현 |
| 3 | bid | `list_pre_specifications` | BidPublicInfoService | 🟡 스텁 → 실 구현 |
| 4 | bid | `get_pre_specification_detail` | BidPublicInfoService | 🆕 신규 |
| 5 | award | `list_bid_openings` | ScsbidInfoService | 🆕 신규 (개찰) |
| 6 | award | `search_awards` | ScsbidInfoService | 🆕 신규 |
| 7 | award | `get_award_detail` | ScsbidInfoService | 🆕 신규 |
| 8 | award | `search_awards_by_vendor` | ScsbidInfoService | 🟡 스텁 → 실 구현 |
| 9 | award | `list_bid_participants` | ScsbidInfoService | 🆕 신규 (응찰업체) |
| 10 | contract | `get_contract_process` | 계약과정통합공개 | 🟡 스텁 → 실 구현 |
| 11 | contract | `search_contracts` | 계약과정통합공개 | 🟡 스텁 → 실 구현 |
| 12 | contract | `list_contract_changes` | 계약과정통합공개 | 🆕 신규 |
| 13 | vendor | `search_bid_participants` | 조달데이터허브 EVAL | 🟡 스텁 (키 발급 후) |
| 14 | vendor | `get_evaluation_scores` | 조달데이터허브 EVAL | 🟡 스텁 (키 발급 후) |
| 15 | vendor | `check_business_status` | NTS | ✅ 구현 |
| 16 | vendor | `verify_business_info` | NTS | ✅ 구현 |
| 17 | stats | `get_procurement_stats` | 공공조달통계 | 🆕 신규 |
| 18 | stats | `list_top_vendors_by_period` | 공공조달통계 | 🆕 신규 |
| **V1** | **vendor-by-vendor** | **`search_bids_by_vendor(biz_no, date_from, date_to)`** | BidPublicInfoService + 클라이언트 필터 | 🆕 신규 |
| **V2** | **vendor-by-vendor** | **`search_participations_by_vendor(biz_no, date_from, date_to)`** | 조달데이터허브 EVAL or 우회 | 🆕 신규 |
| **V3** | **vendor-by-vendor** | **`search_openings_by_vendor(biz_no, date_from, date_to)`** | ScsbidInfoService + 클라이언트 필터 | 🆕 신규 |
| **V4** | **vendor-by-vendor** | **`search_awards_by_vendor(biz_no, date_from, date_to)`** (= #8 강화) | ScsbidInfoService | 🟡 스텁 → 실 구현 |

> **사용자 추가 지시 (2026-05-02 00:25)**: 특정 업체의 기간 내 입찰/응찰/개찰/낙찰 검색 4종(V1~V4)을 award.py·vendor.py에 추가.

### Tier 2 — 통합 워크플로우 도구 (가치)

| # | 도구 | 입력 | 결과 | 의존 도구 |
|---|------|------|------|----------|
| W1 | **`trace_bid_lifecycle`** | bid_notice_no | 사전규격→공고→개찰→낙찰→응찰업체→낙찰업체 NTS 검증 일괄 | 1,2,5,6,7,9,15 |
| W2 | **`vendor_profile`** | biz_no, date_from, date_to | NTS 진위·상태 + **기간 내 입찰/응찰/개찰/낙찰 4종 통계** + 낙찰률 + 주력 업종 | V1,V2,V3,V4,15,16 |
| W3 | **`agency_bid_summary`** | inst_code, period | 발주기관별 사전규격→공고→낙찰 요약 | 1,3,6,17 |
| W4 | **`competitor_analysis`** | biz_no, period | 동일 업종 경쟁사 비교 (낙찰률·평균 응찰가) | 8,9,18 |

### Tier 2.5 — 분석/탐색 도구 (보조)

> **사용자 추가 지시 (2026-05-02 00:36)**: "동종업체·경쟁업체 동향·유사사업 통계 보조 검색 자료 추출 서비스 보강"

| # | 도구 | 입력 | 결과 | 의존 |
|---|------|------|------|------|
| A1 | **`find_similar_vendors`** | biz_no, biz_type?, region?, period | 동일 업종·규모 동종업체 목록 (낙찰합계 기반 유사도) | V4, 17 |
| A2 | **`find_similar_bids`** | bid_notice_no, similarity_factors | 유사 사업(같은 발주기관·키워드·금액대) 입찰 목록 | 1, 2, 6 |
| A3 | **`industry_trend`** | biz_type, region?, period | 업종별 월별 입찰수·낙찰가·낙찰률 추이 | 6, 17 |
| A4 | **`peer_analysis`** | biz_no, peer_count, period | 같은 규모 경쟁사 N개 비교 (낙찰률·평균가·시장점유) | V4, 17, A1 |
| A5 | **`market_share`** | biz_type, period | 업종 내 시장점유 상위 업체 + 점유율 | 17, 18 |

### Tier 3 — Relational Key Cross-Lookup

> **사용자 통찰 (2026-05-02 00:48)**: "공고번호(+차수), 계약번호, 발주기관코드, 사업자등록번호 4개가 모든 정보를 엮어주는 핵심 relational key"

**4개 핵심 키**:
- `bid_notice_no (+ bid_ord)`: 입찰 한 건의 1차 키
- `contract_no`: 체결된 계약의 1차 키
- `inst_code (+ inst_name)`: 발주 주체
- `vendor_biz_no`: 응찰자/낙찰자 주체

| # | 도구 | 시작 키 | 추적 키 |
|---|------|---------|---------|
| L1 | **`lookup_by_bid_no`** | bid_notice_no | inst_code, vendor_biz_no, contract_no |
| L2 | **`lookup_by_inst_code`** | inst_code or inst_name | bid_notice_no 목록, vendor_biz_no 분포 |
| L3 | **`lookup_by_biz_no`** | vendor_biz_no | NTS 진위, bid_notice_no 목록, inst_name 분포 |
| L4 | **`lookup_by_contract_no`** | contract_no | (별개 키 필요로 스텁) |

---

## 3. 단계별 추진 계획

### Phase 0 — 기반 정리 ✅ (완료)
- Git 분기 동기화 (origin 우선)
- vendor.py 풀 구현 복원 (216줄)
- 절단 파일 보정 (config.py, server.py, .env.example)

### Phase 1 — 계획 재수립 🟡 (진행 중)
- REPLAN.md 작성 (본 문서)
- WORK-LOG 5/2 시계열 기록 시작

### Phase 2 — API 엔드포인트 매핑 (Research Team 병렬)
- BidPublicInfoService: 사전규격(`getPreStdInfoList`?)·공고 상세(`getBidPblancListInfoServcDetail`?) 검증
- ScsbidInfoService: 개찰목록·낙찰목록·응찰업체 정확한 endpoint
- ContractInfoService: 계약진행·체결계약 endpoint
- 공공조달통계: endpoint
- → `docs/API_ENDPOINT_MAP.md`

### Phase 3 — Tier 1 단위 도구 실 구현 (Backend Team 병렬)
- 영역별 sub-agent로 동시 진행:
  - **Team Alpha**: bid (사전규격·공고 detail 3종)
  - **Team Bravo**: award (개찰·낙찰·응찰업체 5종)
  - **Team Charlie**: contract (3종) + stats (2종)

### Phase 4 — Tier 2 통합 워크플로우 (Workflow Team)
- `app/tools/workflow.py` 신규
- W1~W4 4개 도구 — Tier 1 도구를 internal 호출하여 결합
- 각 결과는 dict 형태 통일

### Phase 5 — 통합 검증 + Push
- 14개 .py syntax PASS
- server.py 도구 등록 정합성 (등록 = 정의)
- 단일 commit + PAT push
- WORK-LOG 5/2 작업 마무리 기록

---

## 4. API 영역별 키 매핑

| API | 환경변수 | 용도 |
|-----|---------|------|
| 입찰공고/사전규격 (`BidPublicInfoService`) | `G2B_KEY_BID`, `G2B_KEY_PRESPEC` | bid 영역 |
| 낙찰/개찰 (`ScsbidInfoService`) | `G2B_KEY_AWARD` | award 영역 |
| 계약과정통합공개 (`CntrctInfoService`?) | `G2B_KEY_CONTRACT` | contract 영역 |
| 사용자정보 | `G2B_KEY_USER` | user 영역 (보류) |
| 공공조달통계 | `G2B_KEY_STATS` | stats 영역 |
| 평가정보/응찰업체 (조달데이터허브) | `G2B_KEY_EVAL` | vendor.search_bid_participants (키 발급 후) |
| 사업자등록 진위/상태 (NTS) | `NTS_API_KEY` | vendor (구현 완료) |

---

## 5. 성공 기준 (MVP)

1. `trace_bid_lifecycle("실 공고번호")` 호출 시 사전규격→공고→개찰→낙찰→응찰업체→NTS 6개 섹션 모두 결과 반환 (실 데이터)
2. `vendor_profile("실 사업자번호")` 호출 시 NTS 진위 + 최근 낙찰 이력 통합 반환
3. Claude Desktop에서 자연어 질의로 위 2가지 시연 가능
4. 14개 .py 파일 syntax PASS, 모든 도구가 server.py에 등록되어 호출 가능
