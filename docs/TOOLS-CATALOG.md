# GovProcu MCP 도구 카탈로그 (60종)

> 작성: 2026-05-02 KST
> 영역별 도구 정리 + 시그니처 + 사용 예

---

## 영역별 요약

| 영역 | 도구수 | API |
|------|-------|------|
| bid | 4 | G2B BidPublicInfoService |
| award | 6 | G2B ScsbidInfoService |
| contract | 4 | G2B CntrctProcssIntgOpenService |
| stats | 5 | G2B PubPrcrmntStatInfoService |
| user | 1 | (placeholder) |
| vendor | 8 | NTS + 조달데이터허브 EVAL + V1~V3 |
| analytics | 6 | (Tier 2.5 — 자체 집계) |
| workflow | 5 | (Tier 2 통합 — 다른 도구 합성) |
| lookup | 4 | (Tier 3 cross-lookup) |
| alerts | 5 | (P0 stateful — SQLite) |
| watchlist | 3 | (P0 stateful) |
| qualification | 3 | (P0 표준 산식) |
| prediction | 3 | (P1 — histogram quantile) |
| multi_agency | 3 | (P1 — adapter dispatch) |

---

## bid (4)

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `search_bid_notices` | `keyword?, biz_type?, region?, inst_name?, date_from?, date_to?, limit=20` | 입찰공고 검색 (3종 endpoint 자동 분기) |
| `get_bid_notice_detail` | `bid_notice_no, bid_ord="00"` | 공고 단건 상세 |
| `list_pre_specifications` | `keyword?, biz_type?, inst_name?, date_from?, date_to?, limit=20` | 사전규격 목록 |
| `get_pre_specification_detail` | `bid_notice_no, bid_ord="00"` | 사전규격 단건 |

## award (6)

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `list_bid_openings` | `bid_notice_no?, bid_ord?, inst_name?, date_from?, date_to?, biz_type?, limit=20` | 개찰 결과 |
| `search_awards` | `inst_name?, date_from?, date_to?, biz_type?, keyword?, limit=20` | 낙찰 검색 |
| `get_award_detail` | `bid_notice_no, bid_ord="00"` | 낙찰 단건 |
| `search_awards_by_vendor` | `vendor_name?, vendor_biz_no?, date_from?, date_to?, biz_type?, limit=20` | V4: 업체 낙찰 이력 |
| `list_bid_participants` | `bid_notice_no, bid_ord="00"` | 응찰업체 목록 (개찰결과 row) |
| `placeholder_award` | () | 호환 |

## contract (4)

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `get_contract_process` | `bid_notice_no, bid_ord="00"` | 계약 진행과정 (4 endpoint 자동) |
| `get_contract_detail` | `bid_notice_no?, bid_ord="00", contract_no?` | 계약 단건 |
| `search_contracts` | `inst_code?, ...` | 별도 키 필요 (스텁) |
| `list_contract_changes` | `contract_no?, ...` | 별도 키 필요 (스텁) |

## stats (5)

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `get_procurement_stats` | `year?, ym?, biz_type?` | 전체 조달 실적 |
| `list_top_vendors_by_period` | `year?, ym?, biz_type?, top_n=20` | 상위 낙찰업체 |
| `agency_procurement_volume` | `inst_code?, inst_name?, year?, ym?` | 발주기관 조달규모 |
| `industry_procurement_stats` | `year?, ym?` | 업무대상별 |
| `placeholder_stats` | () | 호환 |

## vendor (8)

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `check_business_status` | `biz_nos: list \| str` | NTS 사업자 상태 (1~100건) |
| `verify_business_info` | `biz_no, start_dt, p_nm, ...` | NTS 진위확인 |
| `search_bid_participants` | `bid_notice_no?, vendor_biz_no?, ...` | 응찰자 (EVAL 키 필요) |
| `get_evaluation_scores` | `bid_notice_no, vendor_biz_no` | 평가점수 (EVAL 키) |
| `search_bids_by_vendor` | `vendor_biz_no?, ...` | V1: 업체 입찰 이력 |
| `search_participations_by_vendor` | `vendor_biz_no?, ...` | V2: 업체 응찰 이력 |
| `search_openings_by_vendor` | `vendor_biz_no?, ...` | V3: 업체 개찰 이력 |
| `placeholder_vendor` | () | 호환 |

## analytics (6) — Tier 2.5

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `find_similar_vendors` | `vendor_biz_no, biz_type?, date_from?, date_to?, limit=20` | A1: 동종업체 |
| `find_similar_bids` | `bid_notice_no, similarity_factors?, limit=20` | A2: 유사 사업 |
| `industry_trend` | `biz_type, inst_name?, date_from?, date_to?` | A3: 업종 동향 |
| `peer_analysis` | `vendor_biz_no, peer_count=5, ...` | A4: 경쟁사 비교 |
| `market_share` | `biz_type, date_from?, date_to?, top_n=10` | A5: 시장 점유 |
| `analyze_agency_price_pattern` | `inst_name, biz_type?, ...` | A6: 사정률 분포 |

## workflow (5) — Tier 2 ★ 핵심

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| **`trace_bid_lifecycle`** ⭐ | `bid_notice_no, bid_ord="00"` | 한 입찰 6단계 통합 추적 |
| `vendor_profile` | `vendor_biz_no, date_from?, date_to?, limit=50` | 업체 통합 프로필 |
| `agency_bid_summary` | `inst_name, ...` | 발주기관 요약 |
| `competitor_analysis` | `vendor_biz_no, peer_count=5, ...` | 경쟁사 분석 (peer_analysis 래퍼) |
| `agency_procurement_history` | `inst_name, date_from?, date_to?, biz_type?, limit=30` | 발주기관 이력 + 낙찰업체 매칭 |

## lookup (4) — Tier 3

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `lookup_by_bid_no` | `bid_notice_no, bid_ord="00"` | 공고 → 발주기관/낙찰자/계약 |
| `lookup_by_inst_code` | `inst_code?, inst_name?, ...` | 발주기관 → 공고/Top 낙찰자 |
| `lookup_by_biz_no` | `vendor_biz_no, date_from?, date_to?, limit=30` | 사업자 → NTS/낙찰/거래기관 |
| `lookup_by_contract_no` | `contract_no` | (별도 키 필요로 스텁) |

## alerts (5) — P0 stateful

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `subscribe_keyword_alerts` | `keyword, user_token?, biz_type?, inst_name?, ...` | 구독 등록 |
| `unsubscribe_keyword_alerts` | `subscription_id?, keyword?, user_token?` | 해제 |
| `list_my_subscriptions` | `user_token?` | 내 구독 |
| `daily_bid_digest` | `user_token?, date_target?` | 일일 다이제스트 |
| `weekly_bid_digest` | `user_token?, date_to?` | 주간 다이제스트 |

## watchlist (3) — P0 stateful

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `add_to_watchlist` | `item_type, item_key, user_token?, item_label?, note?` | 즐겨찾기 추가 |
| `remove_from_watchlist` | `item_type?, item_key?, watchlist_id?, user_token?` | 제거 |
| `list_my_watchlist` | `user_token?, item_type?` | 내 즐겨찾기 |

## qualification (3) — P0 적격심사

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `calc_qualification_score` | `bid_amount, base_amount, biz_type, ...` | 종합 점수 (입찰가 + 경험 + 기술 + 신용 + 경영 + 기타) |
| `calc_bid_price_score` | `bid_amount, base_amount, biz_type, max_score=30` | 입찰가격 점수 단독 |
| `get_qualification_rule` | `biz_type, estimated_price?` | 산식 가중치 안내 |

## prediction (3) — P1 ML 휴리스틱

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `predict_bid_price` | `bid_notice_no?, base_amount?, biz_type?, inst_name?, target_win_probability=0.7` | 예측 응찰가 + 95% CI |
| `estimate_winning_threshold` | `inst_name, biz_type?, confidence=0.8, ...` | 낙찰 하한가 |
| `compare_bid_strategies` | `base_amount, inst_name, biz_type?, strategies?` | 시나리오 비교 |

## multi_agency (3) — P1 다중기관

| 도구 | 시그니처 | 설명 |
|------|---------|------|
| `list_supported_agencies` | () | 지원 기관 + 키 발급 상태 |
| `search_multi_agency_bids` | `keyword?, biz_type?, region?, ..., agencies?, limit_per_agency=30` | 다중 기관 동시 검색 |
| `search_agency_specific` | `agency, keyword?, ...` | 단일 기관 |

---

## 사용 예 (자연어 질의)

| 사용자 질의 | 호출 도구 |
|-----------|---------|
| "20240315678 어떻게 됐어?" | `trace_bid_lifecycle("20240315678")` |
| "1234567890 사업자 최근 6개월" | `vendor_profile("1234567890", date_from, date_to)` |
| "국방재정관리단 이번 달 발주" | `agency_procurement_history("국방재정관리단", ...)` |
| "추정가 12억 정보화 용역, 70% 낙찰 목표" | `predict_bid_price(..., target_win_probability=0.7)` |
| "정보화 용역 이번 주 신규 알림" | `subscribe_keyword_alerts("정보화", biz_type="용역")` |

자연어 콘솔(`/console`)이 위 매핑을 자동 수행.
