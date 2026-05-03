# P0 자동 실행 결과 (2)

- 실행: 2026-05-03 13:54 KST
- API 호출: 74건 (64 PASS / 10 FAIL)
- SKIP (UI): 46건
- 전체 소요: 743.5초

## 결과 표

| ID | 도구 | 상태 | ms | 메시지 |
|---|---|---|---|---|
| S01-C3 | search_bid_notices | FAIL | 4584 | ✗ min_items=1 actual=0 |
| S01-C4 | search_bid_notices | PASS | 5431 | ✓ min_items=1 actual=10 |
| S01-C5 | search_bid_notices | PASS | 10509 | ✓ min_items=3 actual=3 |
| S01-C6 | search_bid_notices | PASS | 7606 | ✓ min_items=3 actual=10 |
| S01-C7 | search_bid_notices | PASS | 11894 | ✓ min_items=5 actual=6 |
| S01-C8 | search_bid_notices | PASS | 10583 | ✓ min_items=5 actual=7 |
| S01-C9 | search_bid_notices | PASS | 13975 | ✓ min_items=5 actual=6 |
| S01-C10 | search_bid_notices | PASS | 21814 | ✓ chunks=3 actual=3 |
| S02-C1 | search_bid_notices | PASS | 3820 | ✓ endpoints contains ['getBidPblancListInfoServc']: True |
| S02-C2 | search_bid_notices | PASS | 3955 | ✓ endpoints contains ['getBidPblancListInfoCnstwk']: True |
| S02-C3 | search_bid_notices | PASS | 3519 | ✓ endpoints contains ['getBidPblancListInfoThng']: True |
| S02-C4 | search_bid_notices | FAIL | 4464 | ✗ endpoints_count=3 actual=1 |
| S02-C5 | search_bid_notices | PASS | 10179 | tool call ok (items=1) |
| S02-C6 | search_bid_notices | PASS | 9495 | tool call ok (items=1) |
| S02-C8 | search_bid_notices | PASS | 11014 | tool call ok (items=1) |
| S02-C9 | search_bid_notices | PASS | 5499 | tool call ok (items=2) |
| S03-C3 | search_bid_notices | PASS | 5104 | ✓ min_items=1 actual=1 |
| S03-C4 | search_bid_notices | PASS | 2371 | ✓ min_items=1 actual=10 |
| S03-C5 | search_bid_notices | PASS | 3413 | tool call ok (items=10) |
| S03-C6 | search_bid_notices | PASS | 5038 | tool call ok (items=10) |
| S03-C7 | search_bid_notices | PASS | 10598 | tool call ok (items=1) |
| S03-C8 | search_bid_notices | PASS | 9852 | tool call ok (items=1) |
| S03-C9 | search_bid_notices | PASS | 11734 | tool call ok (items=10) |
| S03-C10 | search_bid_notices | PASS | 5792 | ✓ chunks=12 actual=12 |
| S04-C1 |  | SKIP | 0 | UI/action only |
| S04-C2 |  | SKIP | 0 | UI/action only |
| S04-C3 |  | SKIP | 0 | UI/action only |
| S04-C4 |  | SKIP | 0 | UI/action only |
| S04-C5 |  | SKIP | 0 | UI/action only |
| S04-C6 |  | SKIP | 0 | UI/action only |
| S05-C1 |  | SKIP | 0 | UI/action only |
| S05-C2 |  | SKIP | 0 | UI/action only |
| S05-C3 |  | SKIP | 0 | UI/action only |
| S05-C5 |  | SKIP | 0 | UI/action only |
| S05-C6 |  | SKIP | 0 | UI/action only |
| S05-C10 |  | SKIP | 0 | UI/action only |
| S06-C1 |  | SKIP | 0 | UI/action only |
| S06-C2 |  | SKIP | 0 | UI/action only |
| S06-C3 |  | SKIP | 0 | UI/action only |
| S06-C4 |  | SKIP | 0 | UI/action only |
| S06-C6 |  | SKIP | 0 | UI/action only |
| S06-C7 |  | SKIP | 0 | UI/action only |
| S06-C10 |  | SKIP | 0 | UI/action only |
| S07-C1 | search_awards_by_vendor | PASS | 16689 | ✓ min_candidates=5 actual=9 |
| S07-C2 | search_awards_by_vendor | PASS | 44829 | ✓ must_contain_any=['디지털'] → True; ✓ min_candidates=1 actual=2 |
| S07-C3 | search_awards_by_vendor | FAIL | 3278 | ✗ min_candidates=1 actual=0 |
| S07-C4 | search_awards_by_vendor | FAIL | 4218 | ✗ min_candidates=1 actual=0 |
| S07-C5 | search_awards_by_vendor | PASS | 18450 | tool call ok (items=10) |
| S07-C9 | search_awards_by_vendor | PASS | 7490 | ✓ chunks=4 actual=4 |
| S08-C1 | vendor_profile | PASS | 4338 | tool call ok (items=0) |
| S08-C2 | vendor_profile | PASS | 3741 | tool call ok (items=0) |
| S08-C3 | vendor_profile | PASS | 4526 | tool call ok (items=0) |
| S08-C10 | vendor_profile | PASS | 4087 | tool call ok (items=0) |
| S09-C1 | agency_procurement_history | PASS | 3081 | tool call ok (items=0) |
| S09-C2 | agency_procurement_history | PASS | 3204 | tool call ok (items=0) |
| S09-C3 | agency_procurement_history | PASS | 3816 | tool call ok (items=0) |
| S09-C4 | agency_procurement_history | PASS | 3050 | tool call ok (items=0) |
| S09-C5 | agency_procurement_history | PASS | 3511 | tool call ok (items=0) |
| S09-C6 | agency_procurement_history | PASS | 4225 | tool call ok (items=0) |
| S09-C7 | agency_procurement_history | FAIL | 19142 | ✗ endpoints_min=3 actual=0 |
| S09-C10 | agency_procurement_history | PASS | 3122 | tool call ok (items=0) |
| S10-C1 | analyze_agency_price_pattern | PASS | 3483 | tool call ok (items=0) |
| S10-C2 | analyze_agency_price_pattern | PASS | 4226 | tool call ok (items=0) |
| S10-C3 | analyze_agency_price_pattern | PASS | 4097 | tool call ok (items=0) |
| S10-C7 |  | SKIP | 0 | UI/action only |
| S11-C1 | trace_bid_lifecycle | PASS | 40904 | tool call ok (items=0) |
| S11-C2 | trace_bid_lifecycle | PASS | 44269 | tool call ok (items=0) |
| S11-C3 | trace_bid_lifecycle | PASS | 36386 | tool call ok (items=0) |
| S11-C4 | trace_bid_lifecycle | PASS | 38333 | tool call ok (items=0) |
| S11-C7 |  | SKIP | 0 | UI/action only |
| S11-C8 | trace_bid_lifecycle | PASS | 18645 | tool call ok (items=0) |
| S12-C1 | trace_bid_lifecycle | PASS | 36726 | tool call ok (items=0) |
| S12-C2 | trace_bid_lifecycle | PASS | 18449 | tool call ok (items=0) |
| S12-C3 | trace_bid_lifecycle | PASS | 39955 | tool call ok (items=0) |
| S12-C4 | trace_bid_lifecycle | FAIL | 2585 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='2 validation errors for call[trac |
| S12-C5 | trace_bid_lifecycle | PASS | 39608 | tool call ok (items=0) |
| S13-C1 | search_kwater_contracts | PASS | 7843 | ✓ items_eq=5 actual=5; ✓ must_contain_any=['광주시 노후 상수관로'] → True |
| S13-C2 | search_kwater_contracts | PASS | 4296 | ✓ items_eq=5 actual=5 |
| S13-C3 | search_kwater_contracts | PASS | 3875 | ✓ items_in_range=[1,5] actual=5 |
| S13-C8 | search_kwater_contracts | PASS | 4207 | tool call ok (items=20) |
| S13-C9 | search_kwater_contracts | PASS | 3763 | tool call ok (items=20) |
| S14-C1 |  | SKIP | 0 | UI/action only |
| S14-C2 |  | SKIP | 0 | UI/action only |
| S14-C6 |  | SKIP | 0 | UI/action only |
| S14-C7 |  | SKIP | 0 | UI/action only |
| S15-C1 |  | SKIP | 0 | UI/action only |
| S15-C2 |  | SKIP | 0 | UI/action only |
| S15-C3 |  | SKIP | 0 | UI/action only |
| S15-C4 |  | SKIP | 0 | UI/action only |
| S15-C8 |  | SKIP | 0 | UI/action only |
| S15-C9 |  | SKIP | 0 | UI/action only |
| S16-C1 |  | SKIP | 0 | UI/action only |
| S16-C2 |  | SKIP | 0 | UI/action only |
| S16-C3 |  | SKIP | 0 | UI/action only |
| S16-C4 |  | SKIP | 0 | UI/action only |
| S16-C5 |  | SKIP | 0 | UI/action only |
| S16-C6 |  | SKIP | 0 | UI/action only |
| S17-C1 | calc_qualification_score | PASS | 2699 | tool call ok (items=0) |
| S17-C2 | calc_qualification_score | PASS | 2521 | tool call ok (items=0) |
| S17-C3 | calc_qualification_score | PASS | 2565 | tool call ok (items=0) |
| S17-C6 | calc_qualification_score | PASS | 2450 | tool call ok (items=0) |
| S18-C1 | predict_bid_price | PASS | 3434 | tool call ok (items=0) |
| S18-C2 | predict_bid_price | PASS | 4221 | tool call ok (items=0) |
| S18-C3 | predict_bid_price | PASS | 4041 | tool call ok (items=0) |
| S18-C5 | compare_bid_strategies | PASS | 3727 | tool call ok (items=0) |
| S18-C6 | estimate_winning_threshold | PASS | 2517 | tool call ok (items=0) |
| S18-C10 |  | SKIP | 0 | UI/action only |
| S19-C1 | lookup_by_bid_no | FAIL | 2576 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='3 validation errors for call[look |
| S19-C2 | lookup_by_bid_no | FAIL | 2588 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='3 validation errors for call[look |
| S19-C3 | lookup_by_inst_code | PASS | 6450 | tool call ok (items=0) |
| S19-C5 | lookup_by_biz_no | FAIL | 2559 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='2 validation errors for call[look |
| S19-C6 | lookup_by_biz_no | FAIL | 2463 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='2 validation errors for call[look |
| S19-C10 |  | SKIP | 0 | UI/action only |
| S20-C1 |  | SKIP | 0 | UI/action only |
| S20-C2 |  | SKIP | 0 | UI/action only |
| S20-C3 |  | SKIP | 0 | UI/action only |
| S20-C4 |  | SKIP | 0 | UI/action only |
| S20-C5 |  | SKIP | 0 | UI/action only |
| S20-C6 |  | SKIP | 0 | UI/action only |
| S20-C7 |  | SKIP | 0 | UI/action only |