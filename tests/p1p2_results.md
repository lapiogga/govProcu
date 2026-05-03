# P0 자동 실행 결과 (2)

- 실행: 2026-05-03 15:03 KST
- API 호출: 41건 (41 PASS / 0 FAIL)
- SKIP (UI): 39건
- 전체 소요: 429.1초

## 결과 표

| ID | 도구 | 상태 | ms | 메시지 |
|---|---|---|---|---|
| S01-C1 | search_bid_notices | PASS | 4421 | ✓ items_in_range=[0,5] actual=0 |
| S01-C2 | search_bid_notices | PASS | 5032 | ✓ items_in_range=[0,20] actual=10 |
| S02-C7 | search_bid_notices | PASS | 12736 | tool call ok (items=2) |
| S02-C10 | search_bid_notices | PASS | 6400 | tool call ok (items=10) |
| S03-C1 | search_bid_notices | PASS | 3689 | tool call ok (items=1) |
| S03-C2 | search_bid_notices | PASS | 5253 | tool call ok (items=10) |
| S04-C7 |  | SKIP | 0 | UI/action only |
| S04-C8 |  | SKIP | 0 | UI/action only |
| S04-C9 |  | SKIP | 0 | UI/action only |
| S04-C10 |  | SKIP | 0 | UI/action only |
| S05-C4 |  | SKIP | 0 | UI/action only |
| S05-C7 |  | SKIP | 0 | UI/action only |
| S05-C8 |  | SKIP | 0 | UI/action only |
| S05-C9 |  | SKIP | 0 | UI/action only |
| S06-C5 |  | SKIP | 0 | UI/action only |
| S06-C8 |  | SKIP | 0 | UI/action only |
| S06-C9 |  | SKIP | 0 | UI/action only |
| S07-C6 | search_awards_by_vendor | PASS | 3797 | ✓ min_candidates=0 actual=0 |
| S07-C7 | search_awards_by_vendor | PASS | 3518 | ✓ min_candidates=0 actual=0 |
| S07-C8 | search_awards_by_vendor | PASS | 13978 | ✓ min_candidates=1 actual=10 |
| S07-C10 | search_awards_by_vendor | PASS | 3487 | tool call ok (items=0) |
| S08-C4 | vendor_profile | PASS | 4174 | tool call ok (items=0) |
| S08-C5 | vendor_profile | PASS | 4364 | tool call ok (items=0) |
| S08-C6 | vendor_profile | PASS | 3668 | tool call ok (items=0) |
| S08-C7 | vendor_profile | PASS | 3894 | tool call ok (items=0) |
| S08-C8 |  | SKIP | 0 | UI/action only |
| S08-C9 |  | SKIP | 0 | UI/action only |
| S09-C8 | agency_procurement_history | PASS | 36585 | ✓ chunks_min=12 actual=16 |
| S09-C9 | agency_procurement_history | PASS | 3021 | tool call ok (items=0) |
| S10-C4 | analyze_agency_price_pattern | PASS | 3724 | tool call ok (items=0) |
| S10-C5 | analyze_agency_price_pattern | PASS | 2757 | tool call ok (items=0) |
| S10-C6 | analyze_agency_price_pattern | PASS | 3194 | tool call ok (items=0) |
| S10-C8 | analyze_agency_price_pattern | PASS | 45387 | ✓ chunks_min=1 actual=63 |
| S10-C9 | analyze_agency_price_pattern | PASS | 2967 | tool call ok (items=0) |
| S10-C10 |  | SKIP | 0 | UI/action only |
| S11-C5 | trace_bid_lifecycle | PASS | 50347 | tool call ok (items=0) |
| S11-C6 | trace_bid_lifecycle | PASS | 58167 | tool call ok (items=0) |
| S11-C9 | trace_bid_lifecycle | PASS | 35285 | tool call ok (items=0) |
| S11-C10 | trace_bid_lifecycle | PASS | 41161 | tool call ok (items=0) |
| S12-C6 |  | SKIP | 0 | UI/action only |
| S12-C7 |  | SKIP | 0 | UI/action only |
| S12-C8 |  | SKIP | 0 | UI/action only |
| S12-C9 |  | SKIP | 0 | UI/action only |
| S12-C10 | trace_bid_lifecycle | PASS | 17722 | tool call ok (items=0) |
| S13-C4 | search_kwater_contracts | PASS | 9552 | ✓ items_in_range=[1,5] actual=5 |
| S13-C5 | search_kwater_contracts | PASS | 4344 | ✓ items_in_range=[1,5] actual=5 |
| S13-C6 | search_kwater_contracts | PASS | 3482 | ✓ items_in_range=[1,5] actual=5 |
| S13-C7 | search_kwater_contracts | PASS | 3742 | ✓ items_in_range=[0,5] actual=5 |
| S13-C10 | search_kwater_contracts | PASS | 3035 | ✓ items_eq=0 actual=0 |
| S14-C3 |  | SKIP | 0 | UI/action only |
| S14-C4 |  | SKIP | 0 | UI/action only |
| S14-C5 |  | SKIP | 0 | UI/action only |
| S14-C8 |  | SKIP | 0 | UI/action only |
| S14-C9 |  | SKIP | 0 | UI/action only |
| S14-C10 |  | SKIP | 0 | UI/action only |
| S15-C5 |  | SKIP | 0 | UI/action only |
| S15-C6 |  | SKIP | 0 | UI/action only |
| S15-C7 |  | SKIP | 0 | UI/action only |
| S15-C10 |  | SKIP | 0 | UI/action only |
| S16-C7 |  | SKIP | 0 | UI/action only |
| S16-C8 |  | SKIP | 0 | UI/action only |
| S16-C9 |  | SKIP | 0 | UI/action only |
| S16-C10 |  | SKIP | 0 | UI/action only |
| S17-C4 | calc_qualification_score | PASS | 2381 | tool call ok (items=0) |
| S17-C5 | calc_qualification_score | PASS | 2374 | tool call ok (items=0) |
| S17-C7 | calc_qualification_score | PASS | 2483 | tool call ok (items=0) |
| S17-C8 | calc_qualification_score | PASS | 2776 | tool call ok (items=0) |
| S17-C9 |  | SKIP | 0 | UI/action only |
| S17-C10 | calc_qualification_score | PASS | 2372 | tool call ok (items=0) |
| S18-C4 | predict_bid_price | PASS | 3203 | tool call ok (items=0) |
| S18-C7 | predict_bid_price | PASS | 2460 | tool call ok (items=0) |
| S18-C8 | predict_bid_price | PASS | 2408 | tool call ok (items=0) |
| S18-C9 |  | SKIP | 0 | UI/action only |
| S19-C4 | lookup_by_inst_code | PASS | 3333 | tool call ok (items=0) |
| S19-C7 | lookup_by_contract_no | PASS | 2453 | tool call ok (items=0) |
| S19-C8 |  | SKIP | 0 | UI/action only |
| S19-C9 |  | SKIP | 0 | UI/action only |
| S20-C8 |  | SKIP | 0 | UI/action only |
| S20-C9 |  | SKIP | 0 | UI/action only |
| S20-C10 |  | SKIP | 0 | UI/action only |