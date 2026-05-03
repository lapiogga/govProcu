# P0 자동 실행 결과 (2)

- 실행: 2026-05-03 14:18 KST
- API 호출: 74건 (68 PASS / 6 FAIL)
- SKIP (UI): 46건
- 전체 소요: 877.6초

## 결과 표

| ID | 도구 | 상태 | ms | 메시지 |
|---|---|---|---|---|
| S01-C3 | search_bid_notices | FAIL | 6310 | ✗ min_items=1 actual=0 |
| S01-C4 | search_bid_notices | PASS | 7958 | ✓ min_items=1 actual=10 |
| S01-C5 | search_bid_notices | PASS | 11996 | ✓ min_items=3 actual=3 |
| S01-C6 | search_bid_notices | PASS | 8519 | ✓ min_items=3 actual=10 |
| S01-C7 | search_bid_notices | PASS | 15542 | ✓ min_items=5 actual=6 |
| S01-C8 | search_bid_notices | PASS | 12841 | ✓ min_items=5 actual=7 |
| S01-C9 | search_bid_notices | PASS | 17433 | ✓ min_items=5 actual=6 |
| S01-C10 | search_bid_notices | PASS | 22913 | ✓ chunks=3 actual=3 |
| S02-C1 | search_bid_notices | PASS | 5339 | ✓ endpoints contains ['getBidPblancListInfoServc']: True |
| S02-C2 | search_bid_notices | PASS | 4567 | ✓ endpoints contains ['getBidPblancListInfoCnstwk']: True |
| S02-C3 | search_bid_notices | PASS | 4181 | ✓ endpoints contains ['getBidPblancListInfoThng']: True |
| S02-C4 | search_bid_notices | FAIL | 4444 | ✗ endpoints_count=3 actual=1 |
| S02-C5 | search_bid_notices | PASS | 12423 | tool call ok (items=1) |
| S02-C6 | search_bid_notices | PASS | 12377 | tool call ok (items=1) |
| S02-C8 | search_bid_notices | PASS | 10715 | tool call ok (items=1) |
| S02-C9 | search_bid_notices | PASS | 6286 | tool call ok (items=2) |
| S03-C3 | search_bid_notices | PASS | 6186 | ✓ min_items=1 actual=1 |
| S03-C4 | search_bid_notices | PASS | 2761 | ✓ min_items=1 actual=10 |
| S03-C5 | search_bid_notices | PASS | 4382 | tool call ok (items=10) |
| S03-C6 | search_bid_notices | PASS | 6242 | tool call ok (items=10) |
| S03-C7 | search_bid_notices | PASS | 12826 | tool call ok (items=1) |
| S03-C8 | search_bid_notices | PASS | 11437 | tool call ok (items=1) |
| S03-C9 | search_bid_notices | PASS | 12548 | tool call ok (items=10) |
| S03-C10 | search_bid_notices | PASS | 7926 | ✓ chunks=12 actual=12 |
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
| S07-C1 | search_awards_by_vendor | PASS | 13054 | ✓ min_candidates=5 actual=9 |
| S07-C2 | search_awards_by_vendor | PASS | 45181 | ✓ must_contain_any=['디지털'] → True; ✓ min_candidates=1 actual=2 |
| S07-C3 | search_awards_by_vendor | FAIL | 4068 | ✗ min_candidates=1 actual=0 |
| S07-C4 | search_awards_by_vendor | FAIL | 3989 | ✗ min_candidates=1 actual=0 |
| S07-C5 | search_awards_by_vendor | PASS | 18879 | tool call ok (items=10) |
| S07-C9 | search_awards_by_vendor | PASS | 8396 | ✓ chunks=4 actual=4 |
| S08-C1 | vendor_profile | PASS | 5794 | tool call ok (items=0) |
| S08-C2 | vendor_profile | PASS | 5076 | tool call ok (items=0) |
| S08-C3 | vendor_profile | PASS | 5039 | tool call ok (items=0) |
| S08-C10 | vendor_profile | PASS | 5709 | tool call ok (items=0) |
| S09-C1 | agency_procurement_history | PASS | 3953 | tool call ok (items=0) |
| S09-C2 | agency_procurement_history | PASS | 3858 | tool call ok (items=0) |
| S09-C3 | agency_procurement_history | PASS | 4055 | tool call ok (items=0) |
| S09-C4 | agency_procurement_history | PASS | 5198 | tool call ok (items=0) |
| S09-C5 | agency_procurement_history | PASS | 4043 | tool call ok (items=0) |
| S09-C6 | agency_procurement_history | PASS | 3809 | tool call ok (items=0) |
| S09-C7 | agency_procurement_history | FAIL | 24794 | ✗ endpoints_min=3 actual=0 |
| S09-C10 | agency_procurement_history | PASS | 3888 | tool call ok (items=0) |
| S10-C1 | analyze_agency_price_pattern | PASS | 8636 | tool call ok (items=0) |
| S10-C2 | analyze_agency_price_pattern | PASS | 4671 | tool call ok (items=0) |
| S10-C3 | analyze_agency_price_pattern | PASS | 4797 | tool call ok (items=0) |
| S10-C7 |  | SKIP | 0 | UI/action only |
| S11-C1 | trace_bid_lifecycle | PASS | 37591 | tool call ok (items=0) |
| S11-C2 | trace_bid_lifecycle | PASS | 38971 | tool call ok (items=0) |
| S11-C3 | trace_bid_lifecycle | PASS | 41165 | tool call ok (items=0) |
| S11-C4 | trace_bid_lifecycle | PASS | 40071 | tool call ok (items=0) |
| S11-C7 |  | SKIP | 0 | UI/action only |
| S11-C8 | trace_bid_lifecycle | PASS | 15972 | tool call ok (items=0) |
| S12-C1 | trace_bid_lifecycle | PASS | 35534 | tool call ok (items=0) |
| S12-C2 | trace_bid_lifecycle | PASS | 19148 | tool call ok (items=0) |
| S12-C3 | trace_bid_lifecycle | PASS | 37748 | tool call ok (items=0) |
| S12-C4 | trace_bid_lifecycle | FAIL | 2775 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='2 validation errors for call[trac |
| S12-C5 | trace_bid_lifecycle | PASS | 44697 | tool call ok (items=0) |
| S13-C1 | search_kwater_contracts | PASS | 13433 | ✓ items_eq=5 actual=5; ✓ must_contain_any=['광주시 노후 상수관로'] → True |
| S13-C2 | search_kwater_contracts | PASS | 6536 | ✓ items_eq=5 actual=5 |
| S13-C3 | search_kwater_contracts | PASS | 4458 | ✓ items_in_range=[1,5] actual=5 |
| S13-C8 | search_kwater_contracts | PASS | 4599 | tool call ok (items=20) |
| S13-C9 | search_kwater_contracts | PASS | 4509 | tool call ok (items=20) |
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
| S17-C1 | calc_qualification_score | PASS | 3113 | tool call ok (items=0) |
| S17-C2 | calc_qualification_score | PASS | 3137 | tool call ok (items=0) |
| S17-C3 | calc_qualification_score | PASS | 2727 | tool call ok (items=0) |
| S17-C6 | calc_qualification_score | PASS | 2838 | tool call ok (items=0) |
| S18-C1 | predict_bid_price | PASS | 3538 | tool call ok (items=0) |
| S18-C2 | predict_bid_price | PASS | 3723 | tool call ok (items=0) |
| S18-C3 | predict_bid_price | PASS | 3561 | tool call ok (items=0) |
| S18-C5 | compare_bid_strategies | PASS | 4510 | tool call ok (items=0) |
| S18-C6 | estimate_winning_threshold | PASS | 2805 | tool call ok (items=0) |
| S18-C10 |  | SKIP | 0 | UI/action only |
| S19-C1 | lookup_by_bid_no | PASS | 48898 | tool call ok (items=0) |
| S19-C2 | lookup_by_bid_no | PASS | 21545 | tool call ok (items=0) |
| S19-C3 | lookup_by_inst_code | PASS | 4928 | tool call ok (items=0) |
| S19-C5 | lookup_by_biz_no | PASS | 4955 | tool call ok (items=0) |
| S19-C6 | lookup_by_biz_no | PASS | 5035 | tool call ok (items=0) |
| S19-C10 |  | SKIP | 0 | UI/action only |
| S20-C1 |  | SKIP | 0 | UI/action only |
| S20-C2 |  | SKIP | 0 | UI/action only |
| S20-C3 |  | SKIP | 0 | UI/action only |
| S20-C4 |  | SKIP | 0 | UI/action only |
| S20-C5 |  | SKIP | 0 | UI/action only |
| S20-C6 |  | SKIP | 0 | UI/action only |
| S20-C7 |  | SKIP | 0 | UI/action only |