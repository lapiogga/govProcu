# P0 자동 실행 결과 (2)

- 실행: 2026-05-03 13:29 KST
- API 호출: 69건 (49 PASS / 20 FAIL)
- SKIP (UI): 51건
- 전체 소요: 673.6초

## 결과 표

| ID | 도구 | 상태 | ms | 메시지 |
|---|---|---|---|---|
| S01-C3 | search_bid_notices | FAIL | 6790 | ✗ min_items=1 actual=0 |
| S01-C4 | search_bid_notices | PASS | 5065 | ✓ min_items=1 actual=10 |
| S01-C5 | search_bid_notices | PASS | 10034 | ✓ min_items=3 actual=3 |
| S01-C6 | search_bid_notices | PASS | 8773 | ✓ min_items=3 actual=10 |
| S01-C7 | search_bid_notices | PASS | 13644 | ✓ min_items=5 actual=6 |
| S01-C8 | search_bid_notices | PASS | 10401 | ✓ min_items=5 actual=7 |
| S01-C9 | search_bid_notices | PASS | 13428 | ✓ min_items=5 actual=6 |
| S01-C10 | search_bid_notices | PASS | 21844 | ✓ chunks=3 actual=3 |
| S02-C1 | search_bid_notices | FAIL | 3178 | ✗ endpoints contains ['getBidPblancListInfoServc']: False |
| S02-C2 | search_bid_notices | FAIL | 3273 | ✗ endpoints contains ['getBidPblancListInfoCnstwk']: False |
| S02-C3 | search_bid_notices | FAIL | 2986 | ✗ endpoints contains ['getBidPblancListInfoThng']: False |
| S02-C4 | search_bid_notices | FAIL | 2399 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts="1 validation error for BidNoticeS |
| S02-C5 | search_bid_notices | PASS | 3355 | tool call ok (items=0) |
| S02-C6 | search_bid_notices | PASS | 2904 | tool call ok (items=0) |
| S02-C8 | search_bid_notices | PASS | 3113 | tool call ok (items=0) |
| S02-C9 | search_bid_notices | PASS | 3114 | tool call ok (items=0) |
| S03-C3 | search_bid_notices | PASS | 4831 | ✓ min_items=1 actual=1 |
| S03-C4 | search_bid_notices | PASS | 2377 | ✓ min_items=1 actual=10 |
| S03-C5 | search_bid_notices | PASS | 3273 | tool call ok (items=10) |
| S03-C6 | search_bid_notices | PASS | 5145 | tool call ok (items=10) |
| S03-C7 | search_bid_notices | PASS | 13106 | tool call ok (items=1) |
| S03-C8 | search_bid_notices | PASS | 13828 | tool call ok (items=1) |
| S03-C9 | search_bid_notices | PASS | 10872 | tool call ok (items=10) |
| S03-C10 | search_bid_notices | PASS | 4169 | ✓ chunks=12 actual=12 |
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
| S07-C1 | search_awards_by_vendor | PASS | 19013 | ✓ min_candidates=5 actual=9 |
| S07-C2 | search_awards_by_vendor | PASS | 52413 | ✓ must_contain_any=['디지털'] → True; ✓ min_candidates=1 actual=2 |
| S07-C3 | search_awards_by_vendor | FAIL | 3227 | ✗ min_candidates=1 actual=0 |
| S07-C4 | search_awards_by_vendor | FAIL | 3263 | ✗ min_candidates=1 actual=0 |
| S07-C5 | search_awards_by_vendor | PASS | 21785 | tool call ok (items=10) |
| S07-C9 | search_awards_by_vendor | PASS | 8791 | ✓ chunks=4 actual=4 |
| S08-C1 | vendor_profile | PASS | 6652 | tool call ok (items=0) |
| S08-C2 | vendor_profile | PASS | 6744 | tool call ok (items=0) |
| S08-C3 | vendor_profile | PASS | 3781 | tool call ok (items=0) |
| S08-C10 | vendor_profile | PASS | 3984 | tool call ok (items=0) |
| S09-C1 | agency_procurement_history | PASS | 3300 | tool call ok (items=0) |
| S09-C2 | agency_procurement_history | PASS | 3084 | tool call ok (items=0) |
| S09-C3 | agency_procurement_history | PASS | 2957 | tool call ok (items=0) |
| S09-C4 | agency_procurement_history | PASS | 3843 | tool call ok (items=0) |
| S09-C5 | agency_procurement_history | PASS | 3754 | tool call ok (items=0) |
| S09-C6 | agency_procurement_history | PASS | 2722 | tool call ok (items=0) |
| S09-C7 | agency_procurement_history | FAIL | 2677 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts="1 validation error for BidNoticeS |
| S09-C10 | agency_procurement_history | PASS | 2948 | tool call ok (items=0) |
| S10-C1 | analyze_agency_price_pattern | PASS | 3788 | tool call ok (items=0) |
| S10-C2 | analyze_agency_price_pattern | PASS | 3124 | tool call ok (items=0) |
| S10-C3 | analyze_agency_price_pattern | PASS | 3976 | tool call ok (items=0) |
| S10-C7 |  | SKIP | 0 | UI/action only |
| S11-C1 | trace_bid_lifecycle | PASS | 35549 | tool call ok (items=0) |
| S11-C2 | trace_bid_lifecycle | PASS | 35310 | tool call ok (items=0) |
| S11-C3 | trace_bid_lifecycle | PASS | 37966 | tool call ok (items=0) |
| S11-C4 | trace_bid_lifecycle | PASS | 37182 | tool call ok (items=0) |
| S11-C7 |  | SKIP | 0 | UI/action only |
| S11-C8 | trace_bid_lifecycle | PASS | 17039 | tool call ok (items=0) |
| S12-C1 | trace_bid_lifecycle | PASS | 34069 | tool call ok (items=0) |
| S12-C2 | trace_bid_lifecycle | PASS | 15701 | tool call ok (items=0) |
| S12-C3 | trace_bid_lifecycle | PASS | 35137 | tool call ok (items=0) |
| S12-C4 | trace_bid_lifecycle | FAIL | 3273 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='2 validation errors for call[trac |
| S12-C5 | trace_bid_lifecycle | PASS | 38535 | tool call ok (items=0) |
| S13-C1 | search_kwater_contracts | FAIL | 4034 | ✗ items_eq=5 actual=20; ✓ must_contain_any=['광주시 노후 상수관로'] → True |
| S13-C2 | search_kwater_contracts | FAIL | 3351 | ✗ items_eq=5 actual=20 |
| S13-C3 | search_kwater_contracts | FAIL | 9561 | ✗ items_in_range=[1,5] actual=20 |
| S13-C8 | search_kwater_contracts | PASS | 4199 | tool call ok (items=20) |
| S13-C9 | search_kwater_contracts | PASS | 3373 | tool call ok (items=20) |
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
| S17-C1 | calc_qualification_score | FAIL | 2341 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='1 validation error for call[calc_ |
| S17-C2 | calc_qualification_score | FAIL | 2414 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='1 validation error for call[calc_ |
| S17-C3 | calc_qualification_score | FAIL | 2416 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='1 validation error for call[calc_ |
| S17-C6 | calc_qualification_score | FAIL | 2413 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='6 validation errors for call[calc |
| S18-C1 | predict_bid_price | FAIL | 2342 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='1 validation error for call[predi |
| S18-C2 | predict_bid_price | FAIL | 2405 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='1 validation error for call[predi |
| S18-C3 | predict_bid_price | FAIL | 2510 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='1 validation error for call[predi |
| S18-C5 | predict_bid_price | FAIL | 2389 | unexpected error: inner parse fail: Extra data: line 1 column 3 (char 2); body_starts='1 validation error for call[predi |
| S18-C6 | predict_bid_price | PASS | 2358 | tool call ok (items=0) |
| S18-C10 |  | SKIP | 0 | UI/action only |
| S19-C1 |  | SKIP | 0 | UI/action only |
| S19-C2 |  | SKIP | 0 | UI/action only |
| S19-C3 |  | SKIP | 0 | UI/action only |
| S19-C5 |  | SKIP | 0 | UI/action only |
| S19-C6 |  | SKIP | 0 | UI/action only |
| S19-C10 |  | SKIP | 0 | UI/action only |
| S20-C1 |  | SKIP | 0 | UI/action only |
| S20-C2 |  | SKIP | 0 | UI/action only |
| S20-C3 |  | SKIP | 0 | UI/action only |
| S20-C4 |  | SKIP | 0 | UI/action only |
| S20-C5 |  | SKIP | 0 | UI/action only |
| S20-C6 |  | SKIP | 0 | UI/action only |
| S20-C7 |  | SKIP | 0 | UI/action only |