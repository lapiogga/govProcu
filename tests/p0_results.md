# P0 자동 실행 결과 (2)

- 실행: 2026-05-03 14:39 KST
- API 호출: 73건 (73 PASS / 0 FAIL)
- SKIP (UI): 47건
- 전체 소요: 906.7초

## 결과 표

| ID | 도구 | 상태 | ms | 메시지 |
|---|---|---|---|---|
| S01-C3 | search_bid_notices | PASS | 6389 | ✓ items_in_range=[0,5] actual=0 |
| S01-C4 | search_bid_notices | PASS | 8930 | ✓ min_items=1 actual=10 |
| S01-C5 | search_bid_notices | PASS | 12332 | ✓ min_items=3 actual=3 |
| S01-C6 | search_bid_notices | PASS | 8673 | ✓ min_items=3 actual=10 |
| S01-C7 | search_bid_notices | PASS | 15565 | ✓ min_items=5 actual=6 |
| S01-C8 | search_bid_notices | PASS | 14473 | ✓ min_items=5 actual=7 |
| S01-C9 | search_bid_notices | PASS | 18641 | ✓ min_items=5 actual=6 |
| S01-C10 | search_bid_notices | PASS | 23554 | ✓ chunks=3 actual=3 |
| S02-C1 | search_bid_notices | PASS | 4476 | ✓ endpoints contains ['getBidPblancListInfoServc']: True |
| S02-C2 | search_bid_notices | PASS | 4397 | ✓ endpoints contains ['getBidPblancListInfoCnstwk']: True |
| S02-C3 | search_bid_notices | PASS | 4293 | ✓ endpoints contains ['getBidPblancListInfoThng']: True |
| S02-C4 | search_bid_notices | PASS | 4588 | ✓ endpoints_min=1 actual=1 |
| S02-C5 | search_bid_notices | PASS | 11286 | tool call ok (items=1) |
| S02-C6 | search_bid_notices | PASS | 10731 | tool call ok (items=1) |
| S02-C8 | search_bid_notices | PASS | 12004 | tool call ok (items=1) |
| S02-C9 | search_bid_notices | PASS | 5776 | tool call ok (items=2) |
| S03-C3 | search_bid_notices | PASS | 4234 | ✓ min_items=1 actual=1 |
| S03-C4 | search_bid_notices | PASS | 2373 | ✓ min_items=1 actual=10 |
| S03-C5 | search_bid_notices | PASS | 3598 | tool call ok (items=10) |
| S03-C6 | search_bid_notices | PASS | 5287 | tool call ok (items=10) |
| S03-C7 | search_bid_notices | PASS | 13599 | tool call ok (items=1) |
| S03-C8 | search_bid_notices | PASS | 11141 | tool call ok (items=1) |
| S03-C9 | search_bid_notices | PASS | 12453 | tool call ok (items=10) |
| S03-C10 | search_bid_notices | PASS | 6440 | ✓ chunks=12 actual=12 |
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
| S07-C1 | search_awards_by_vendor | PASS | 15809 | ✓ min_candidates=5 actual=9 |
| S07-C2 | search_awards_by_vendor | PASS | 44463 | ✓ must_contain_any=['디지털'] → True; ✓ min_candidates=1 actual=2 |
| S07-C3 | search_awards_by_vendor | PASS | 4154 | ✓ min_candidates=0 actual=0 |
| S07-C4 | search_awards_by_vendor | PASS | 4069 | ✓ min_candidates=0 actual=0 |
| S07-C5 | search_awards_by_vendor | PASS | 19213 | tool call ok (items=10) |
| S07-C9 | search_awards_by_vendor | PASS | 9099 | ✓ chunks=4 actual=4 |
| S08-C1 | vendor_profile | PASS | 4515 | tool call ok (items=0) |
| S08-C2 | vendor_profile | PASS | 5414 | tool call ok (items=0) |
| S08-C3 | vendor_profile | PASS | 4804 | tool call ok (items=0) |
| S08-C10 | vendor_profile | PASS | 5664 | tool call ok (items=0) |
| S09-C1 | agency_procurement_history | PASS | 3979 | tool call ok (items=0) |
| S09-C2 | agency_procurement_history | PASS | 3912 | tool call ok (items=0) |
| S09-C3 | agency_procurement_history | PASS | 3976 | tool call ok (items=0) |
| S09-C4 | agency_procurement_history | PASS | 3818 | tool call ok (items=0) |
| S09-C5 | agency_procurement_history | PASS | 4807 | tool call ok (items=0) |
| S09-C6 | agency_procurement_history | PASS | 3420 | tool call ok (items=0) |
| S09-C7 | agency_procurement_history | PASS | 43817 | ✓ endpoints_min=1 actual=1 |
| S09-C10 | agency_procurement_history | PASS | 3575 | tool call ok (items=0) |
| S10-C1 | analyze_agency_price_pattern | PASS | 8287 | tool call ok (items=0) |
| S10-C2 | analyze_agency_price_pattern | PASS | 3793 | tool call ok (items=0) |
| S10-C3 | analyze_agency_price_pattern | PASS | 6977 | tool call ok (items=0) |
| S10-C7 |  | SKIP | 0 | UI/action only |
| S11-C1 | trace_bid_lifecycle | PASS | 44692 | tool call ok (items=0) |
| S11-C2 | trace_bid_lifecycle | PASS | 44245 | tool call ok (items=0) |
| S11-C3 | trace_bid_lifecycle | PASS | 38981 | tool call ok (items=0) |
| S11-C4 | trace_bid_lifecycle | PASS | 40125 | tool call ok (items=0) |
| S11-C7 |  | SKIP | 0 | UI/action only |
| S11-C8 | trace_bid_lifecycle | PASS | 27805 | tool call ok (items=0) |
| S12-C1 | trace_bid_lifecycle | PASS | 44531 | tool call ok (items=0) |
| S12-C2 | trace_bid_lifecycle | PASS | 27057 | tool call ok (items=0) |
| S12-C3 | trace_bid_lifecycle | PASS | 41205 | tool call ok (items=0) |
| S12-C4 |  | SKIP | 0 | UI/action only |
| S12-C5 | trace_bid_lifecycle | PASS | 34505 | tool call ok (items=0) |
| S13-C1 | search_kwater_contracts | PASS | 4397 | ✓ items_eq=5 actual=5; ✓ must_contain_any=['광주시 노후 상수관로'] → True |
| S13-C2 | search_kwater_contracts | PASS | 4514 | ✓ items_eq=5 actual=5 |
| S13-C3 | search_kwater_contracts | PASS | 4509 | ✓ items_in_range=[1,5] actual=5 |
| S13-C8 | search_kwater_contracts | PASS | 4050 | tool call ok (items=20) |
| S13-C9 | search_kwater_contracts | PASS | 4230 | tool call ok (items=20) |
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
| S17-C1 | calc_qualification_score | PASS | 2749 | tool call ok (items=0) |
| S17-C2 | calc_qualification_score | PASS | 2779 | tool call ok (items=0) |
| S17-C3 | calc_qualification_score | PASS | 2877 | tool call ok (items=0) |
| S17-C6 | calc_qualification_score | PASS | 2820 | tool call ok (items=0) |
| S18-C1 | predict_bid_price | PASS | 3703 | tool call ok (items=0) |
| S18-C2 | predict_bid_price | PASS | 4139 | tool call ok (items=0) |
| S18-C3 | predict_bid_price | PASS | 3562 | tool call ok (items=0) |
| S18-C5 | compare_bid_strategies | PASS | 4343 | tool call ok (items=0) |
| S18-C6 | estimate_winning_threshold | PASS | 2775 | tool call ok (items=0) |
| S18-C10 |  | SKIP | 0 | UI/action only |
| S19-C1 | lookup_by_bid_no | PASS | 42246 | tool call ok (items=0) |
| S19-C2 | lookup_by_bid_no | PASS | 21318 | tool call ok (items=0) |
| S19-C3 | lookup_by_inst_code | PASS | 5347 | tool call ok (items=0) |
| S19-C5 | lookup_by_biz_no | PASS | 5313 | tool call ok (items=0) |
| S19-C6 | lookup_by_biz_no | PASS | 5007 | tool call ok (items=0) |
| S19-C10 |  | SKIP | 0 | UI/action only |
| S20-C1 |  | SKIP | 0 | UI/action only |
| S20-C2 |  | SKIP | 0 | UI/action only |
| S20-C3 |  | SKIP | 0 | UI/action only |
| S20-C4 |  | SKIP | 0 | UI/action only |
| S20-C5 |  | SKIP | 0 | UI/action only |
| S20-C6 |  | SKIP | 0 | UI/action only |
| S20-C7 |  | SKIP | 0 | UI/action only |