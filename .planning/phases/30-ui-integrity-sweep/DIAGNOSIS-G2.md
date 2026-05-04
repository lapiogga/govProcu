# DIAGNOSIS-G2 — 입찰 검색 / 입찰 추적 / 단건 조회 (3 화면)

> **점검 대상 그룹**: G2 (bids 영역 + lookup 단건)
> **점검자**: sub-agent (자동)
> **시각**: 2026-05-04
> **점검 차원**: D1 extract / D2 key naming / D3 빈 상태 / D4 loading / D5 에러 / D6 기간+coverage / D7 포맷터 / D8 페이지네이션
> **참조 자료**:
> - frontend: `frontend/src/app/bids/page.tsx`, `frontend/src/app/bids/trace/page.tsx`, `frontend/src/app/lookup/page.tsx`, `frontend/src/lib/actions.ts`, `frontend/src/lib/format.ts`, `frontend/src/lib/extract.ts`, `frontend/src/components/EntityLink.tsx`
> - backend: `app/tools/bid.py`, `app/tools/award.py`, `app/tools/workflow.py`, `app/tools/lookup.py`, `app/tools/vendor.py`

---

## A. 화면별 점검 매트릭스

### A.1 `/bids` — 입찰 검색 (W1)

| Dim | 결과 | Evidence | 코멘트 |
|-----|------|----------|--------|
| D1 extract | OK | `page.tsx:408-425` (`extractData`) | inline 구현. `content[0].text` JSON.parse + 직접 dict fallback. null/배열 안전. `lib/extract.ts`의 `extractMcpData` 재사용 안 함(중복) — P3. |
| D2 key naming | OK | `page.tsx:90-99` Bid interface vs `bid.py:_normalize_notice` (`bid_no` / `bid_ord` / `title` / `inst_name` / `biz_type` / `estimated_price` / `publish_date` / `deadline_date`) | snake_case 정렬 일치. `extractData(result.data)?.items` 경로도 backend `BidNoticeSearchResult.items` 일치. |
| D3 빈 상태 | OK | `page.tsx:255-298` | 3가지 분기: ① 매칭 0 + total_count > 0(키워드 필터 0건 + deep 안내) ② 결과 0 + total_count 0 ③ 페이지 초과. trim() 적용으로 공백 입력도 안전. |
| D4 loading | OK | `page.tsx:192,357-364` | Suspense fallback `TableSkeleton` 5행 animate-pulse. `cursor-wait` 미적용(P3). |
| D5 에러 | OK | `page.tsx:230-236` | `result.ok === false` → border-danger 박스 + `result.error`. |
| D6 기간 default + coverage | **WARN** | `page.tsx:120-121,134-191` | 사용자 미입력 시 자동 30일(P99 4.2초). 1개월 초과 시 chunk 안내 표시. **그러나** backend `search_bid_notices`는 `scan_coverage_pct`/`scanned`/`chunks_used`/`endpoints_used`를 반환하는데 frontend가 노출하지 않음 — false-negative 인지 불가(P1). |
| D7 포맷터 | OK | `page.tsx:329-347` | fmtDate(공고일/마감일), fmtWon(추정가), `tabular-nums` 정렬. |
| D8 페이지네이션 | **WARN** | `page.tsx:243-253,366-406` | `buildHref`에 `deep` 파라미터 누락(P1). 사용자가 "깊은 검색" 체크 후 다음 페이지 이동 시 deep 파라미터 손실 → 5x scan 사라짐. `pageSize=999` 가정으로 lastPage 계산하나, `endpoints×chunks` 곱 환경에서 totalCount 합계가 `999`로 나누어 떨어지지 않을 수 있음(P2). hidden form `<input type="hidden" name="page" value="1">`이 항상 1로 reset → 정상(검색 변경 시 1페이지 복귀)이지만 sort 변경 시도 1페이지로 reset되어 의도와 다를 수 있음(P3). |

**기타 관찰**:
- v24.4 keyword 토큰 매칭은 backend에서 처리(`bid.py:217-219` `all(t in title for t in keyword_tokens)`). "정보체계" 단일 키워드는 토큰 1개라 부분 일치되어야 정상 동작. 0건 보고는 30일 기본 + scan_pages=1 한계 가능성 — D6 WARN과 연계.
- `scan_pages` 파라미터는 backend signature에 있고 actions.ts에도 전달하나, frontend는 deep checkbox로 1↔5만 토글. `scan_pages` 슬라이더 등 미세 제어 미제공(P3).
- `deep` 체크박스는 `defaultChecked={sp.deep === "1"}`만 사용 — sort 변경 또는 페이지 이동 후 hidden field 누락으로 url에서 사라짐(P1, D8와 같은 결함).

---

### A.2 `/bids/trace` — 입찰 추적 6단계 (W3, Suspense Streaming)

| Dim | 결과 | Evidence | 코멘트 |
|-----|------|----------|--------|
| D1 extract | OK | `page.tsx:384-401` (`extractData`) | inline. `Record<string, any>` 캐스팅. `lib/extract.ts`의 `extractMcpData` 미사용 — 중복(P3). |
| D2 key naming | **WARN** | `page.tsx:131-148,158-184,209-244,255-272` | **summary fallback chain 일관성 위반**(P2): `summary.title || summary.bidNtceNm`, `summary.inst_name || summary.ntceInsttNm`, `summary.estimated_price ?? summary.presmptPrce`, `summary.publish_date ?? summary.bidNtceDt`. backend `_normalize_notice`(bid.py:66-79)는 항상 snake_case로 정규화해 반환하므로 raw camelCase fallback 절차는 도달 불가(`get_bid_notice_detail`는 항상 `summary: _normalize_notice(...).model_dump()`). 단 `data?.raw` 직접 사용 시(line 121 `data?.summary || data?.raw || {}`) raw camelCase 키도 대응됨 — 의도된 방어 코드지만 죽은 분기(P3). award는 `winner_biz_no`/`winner_name`/`award_amount`/`award_rate`/`open_date` 모두 `_normalize_award_row`(award.py:110-126) 키와 일치. 응찰업체는 `participant_biz_no`/`participant_name`/`participant_bid_amount`/`opening_rank`/`is_winner` 모두 `_normalize_opening_row`(award.py:129-147) 키와 일치 — OK. |
| D3 빈 상태 | **WARN** | `page.tsx:188-191,194-205,266` | StagePreSpec/StageNotice는 `data?.found`만 표시. backend 미발견 시 `note` 필드(`bid.py:482-486`, `award.py:447-452`, `award.py:640-646`)를 반환하는데 frontend가 노출 안 함 — 사용자가 "왜 X단계가 비었는지" 알 수 없음(P1). Stage4 미낙찰 케이스 desc="미낙찰/유찰"은 OK. Stage5 NTS는 winner_biz_no 없으면 inactive 표시 OK. |
| D4 loading | OK | `page.tsx:80-103,350-372` | 6 Suspense + StageSkeleton(`cursor-wait` + spin spinner + 단계 라벨). v22.4 패턴 명시. SummarySkeleton도 cursor-wait. |
| D5 에러 | **WARN** | `page.tsx:113-119` (`SummarySection`만), `188-191,194-205,208-218,255-273` 기타 stage | SummarySection은 `r.ok === false` 분기 표시. **그러나** StagePreSpec/StageNotice/StageParticipants/StageAwardAndNts/StageNts 모두 `r.ok` 체크 누락 — backend가 `ok=false` 반환 시 `extractData(undefined)` → null → `data?.found = undefined` → "○" 표시. 사용자가 통신 오류와 데이터 미발견을 구분 불가(P1). |
| D6 기간 default | N/A | — | trace는 단건 조회라 기간 default 없음. 단 backend 내부 폴백(`bid.py:425-433` 30→90→연도 progressive)은 자동 처리. |
| D7 포맷터 | OK | `page.tsx:142,148,174,180,203,243` | fmtWon(estimated_price/award_amount/participant_bid_amount), fmtRate(award_rate), fmtDate(publish_date/open_date), fmtBizNo(participant_biz_no). `tabular-nums` 일관 적용. |
| D8 페이지네이션 | N/A | — | 단건/제한된 응찰업체 목록. 응찰자 100개 한도(`award.py:619 numOfRows=100`)지만 표시상 모두 노출 가정 — 100개 초과 케이스 미처리(P3, 실 발생 드뭄). |

**Streaming 정합 추가 점검**:
- `bid_no` 자동 split(`page.tsx:28-35`): "R26BK01435763-000" 입력 + 빈 ord → ord="000", no="R26BK01435763". backend `get_bid_notice_detail`(bid.py:311-314)도 동일 split 로직. **이중 split 안전**: backend 입력 시점에 이미 `-` 제거됨. 단 ord="000"(suffix가 모두 0) 케이스는 frontend `if (...!sp.ord || !sp.ord.replace(/0/g, ""))` 조건으로 split 안 됨 → backend로 그대로 전달 → backend도 동일 조건(`not bid_ord.strip("0")`)으로 split. 동일 로직 중복 — OK이나 backend가 단일 책임으로 이전 권장(P3).
- `Promise.all` for ActionLinks(`page.tsx:289-292`): `getAwardDetail` + `getBidNoticeDetail` 병렬. `@cache_result`(30분)로 SummarySection/StageNotice/StageAwardAndNts에서 이미 호출된 것과 cache hit — OK.
- Stage 5 NTS의 `b_stt_cd`(`page.tsx:407-410`): backend `vendor.check_business_status` 정규화 키 확인 필요. workflow.py:209-213 vendor_profile은 `status_code`/`status` 사용. trace에서는 raw `b_stt_cd` 사용 — **불일치 위험**(P1). check_business_status 응답 정규화 후 키가 status_code로 바뀌었다면 ntsLabel은 항상 fallback `first.b_stt`만 보게 됨.
- Stage 6(계약): 정적 `inactive` 표시. backend `contract_tools` 호출 안 함 — 의도된 미구현(`PLAN.md` 8단계 종료조건 외).

---

### A.3 `/lookup` — Cross-Lookup 단건 조회

| Dim | 결과 | Evidence | 코멘트 |
|-----|------|----------|--------|
| D1 extract | OK | `page.tsx:13,125` | `extractMcpData<any>` 사용 — 표준 헬퍼. 다른 두 화면과 달리 일관됨. |
| D2 key naming | **FAIL** | `page.tsx:128,148,156,167,170,175` vs `lookup.py:50-58` | mode=bid의 `lookup_by_bid_no`는 `keys.bid_notice_no` / `keys.bid_ord` / `keys.inst_code` / `keys.inst_name` / `keys.vendor_biz_no` / `keys.vendor_name` / `keys.contract_no`를 반환. **frontend는 모든 mode에서 같은 keys 객체를 기대하나 `lookup_by_inst_code`/`lookup_by_biz_no`는 keys 형태가 다름**: `lookup_by_inst_code`(lookup.py:156-160)는 `keys = {inst_code, inst_name}`만 — bid_notice_no/vendor_biz_no/contract_no 부재. `lookup_by_biz_no`(lookup.py:236)는 `keys = {vendor_biz_no}`만 — inst_name/bid_notice_no 부재. frontend는 4개 KeyNode를 항상 그리는데 mode=biz/inst에서는 빈 카드(P0). 또한 mode=biz는 `summary.bid_notice_no_list`/`top_agencies`를 반환하는데 frontend는 `keys.bid_notice_no` 단일을 표시(불일치) — Top 업체/Top 발주기관 표는 별도 표시되지만 그래프/카드 패널 정합 깨짐. |
| D3 빈 상태 | **WARN** | `page.tsx:125-126` | `extractMcpData` 결과 null 시 "결과 없음" 1줄. **하지만** mode=biz의 LIKE 0건이거나 mode=inst 조건 없음 등의 구체 사유 미설명(P2). `lookup_by_biz_no`/`lookup_by_inst_code`는 빈 입력 시 ValueError throw → mcp-client가 ok=false로 받지만 사용자는 generic 에러 보임(P3). |
| D4 loading | OK | `page.tsx:84,307-313` | Suspense + `Skel h={32}` (h * 4px = 128px). 단순 pulse — stage별 상태 표시 없음(P3). |
| D5 에러 | OK | `page.tsx:118-124` | `result.ok === false` → border-danger + error 메시지. mode=contract는 stub 안내(`page.tsx:104-110`). |
| D6 기간 default | **WARN** | `page.tsx:113-116` | mode=biz/inst lookup은 backend가 `date_from`/`date_to` optional. frontend는 form에서 기간 입력 받지 않고 항상 None 전달 → backend default(전기간 검색) → G2B 1개월 chunk 자동 처리 가정이지만 chunks_used/endpoints_used 미노출. 빠른 쿼리(현재 30~90일 경량 default 권장)는 backend `search_bid_notices`/`search_awards`에 결정 위임(P1, false-negative 위험). |
| D7 포맷터 | OK | `page.tsx:167,217,221,251` | fmtBizNo, 100억 분모. fmtWon 미사용(억 분모만) — 일관성 부족(P3, 다른 화면은 fmtWon). |
| D8 페이지네이션 | N/A | — | top_winners/top_agencies는 backend 10건 제한. has_more 안내 없음. cross-lookup 특성상 next page 개념 부재 — OK. |

**핵심 결함**:
1. **mode=biz/inst keys 객체 형식 불일치**: `lookup_by_inst_code` 응답 keys는 inst_code/inst_name만, `lookup_by_biz_no`는 vendor_biz_no만. frontend는 4 KeyNode 카드를 그릴 때 `keys.bid_notice_no`/`keys.contract_no`를 항상 참조 → "—" 표시. 본래 cross-lookup 가치(다른 키로 추적)가 mode=biz/inst에서 그래프/카드 패널로 안 드러남(`LookupGraph` 컴포넌트 동작은 별도 점검 필요 — G2 범위 외).
2. **`lookup_by_biz_no` summary**: `bid_notice_no_list`(첫 20건)와 `top_agencies` 제공. frontend는 top_agencies만 표시(`page.tsx:230-258`). bid_notice_no_list 미노출 → 사용자가 "이 업체가 받은 공고 목록"을 직접 못 봄(P1).
3. **mode=contract stub**: `page.tsx:104-110`은 안내 표시. backend `lookup_by_contract_no`(lookup.py:250-261)도 `status: "not_implemented"` 반환. frontend는 backend 호출도 안 함 — 정합 OK.

---

## B. 결함 요약

### B.1 P0 (차단)

| ID | 화면 | 결함 | 결과 |
|----|------|------|------|
| G2-P0-01 | `/lookup` mode=biz/inst | `keys` 객체 형식 backend가 mode별 다른데 frontend는 단일 4-카드 그리드 — bid_notice_no / contract_no 카드 항상 "—" | cross-lookup 핵심 가치 손실 |

### B.2 P1 (중요)

| ID | 화면 | 결함 | 결과 |
|----|------|------|------|
| G2-P1-01 | `/bids` | `searchBidNotices` 응답의 `scan_coverage_pct` / `scanned` / `chunks_used` / `endpoints_used` frontend 미노출 → false-negative(키워드 0건이 진짜 0건인지, 미스캔인지) 인지 불가 | UX 혼란 / 잘못된 결정 |
| G2-P1-02 | `/bids` | `buildHref`에 `deep` / `sort` 파라미터 일관 보존 누락 — 페이지 이동 시 deep 체크 풀림(scan_pages 5→1) | "깊은 검색"이 1페이지에서만 작동 |
| G2-P1-03 | `/bids/trace` | StagePreSpec/StageNotice/StageParticipants/StageAwardAndNts/StageNts 모두 `r.ok === false` 분기 미처리 — 통신 오류와 데이터 미발견 동일 표시 | 사용자가 backend 다운/네트워크 오류 인지 불가 |
| G2-P1-04 | `/bids/trace` | backend `note` 필드(미발견 사유) 무시 — 6단계가 비어있어도 "왜"를 알 수 없음 | F2(빈 결과) 잔존, 사용자 보고 사례와 일치 |
| G2-P1-05 | `/bids/trace` Stage5 | NTS 응답 키를 `b_stt_cd`/`b_stt`(raw G2B)로 참조하나 backend `check_business_status` 정규화 후 `status_code`/`status`로 변환됐을 수 있음 — vendor_profile에서는 status_code 사용. ntsLabel 항상 fallback "—" 가능 | 낙찰자 NTS 검증 단계 무용 |
| G2-P1-06 | `/lookup` mode=biz | `summary.bid_notice_no_list`(첫 20건) frontend 미노출 — "이 업체가 받은 공고 목록" 직접 표시 안 함 | 사용자 가치 손실 |
| G2-P1-07 | `/lookup` mode=biz/inst | 기간 입력 폼 부재 → backend가 내부 default(전기간)로 넓게 스캔 — 응답 시간 증가 + scan_coverage 미노출 | F-리스크: 큰 기간으로 timeout |

### B.3 P2 (권장)

| ID | 화면 | 결함 | 결과 |
|----|------|------|------|
| G2-P2-01 | `/bids/trace` | `summary.bidNtceNm` / `summary.ntceInsttNm` / `summary.presmptPrce` / `summary.bidNtceDt` raw camelCase fallback chain — backend가 항상 snake_case 정규화 후 반환하므로 죽은 분기 | 코드 일관성 / 가독성 |
| G2-P2-02 | `/bids` | `lastPage = ceil(total / 999)` 계산이 endpoints/chunks 합산 totalCount와 어긋날 수 있음(다중 endpoint 합계는 page_size 배수 아님) | 페이지네이션 마지막 페이지 부정확 |
| G2-P2-03 | `/lookup` mode=biz/inst | 빈 응답 사유 구분 안 함(LIKE 0건 / 입력 누락 / 백엔드 0건) | UX 정밀도 |

### B.4 P3 (보완)

| ID | 화면 | 결함 |
|----|------|------|
| G2-P3-01 | 3 화면 모두 | `extractMcpData`(lib/extract.ts) 표준 헬퍼 있음에도 bids/page와 trace/page는 inline `extractData` 중복 정의 |
| G2-P3-02 | `/bids` | `TableSkeleton`에 cursor-wait 미적용 (trace는 적용) |
| G2-P3-03 | `/bids` | `bid_no` + `-` 자동 split 로직이 frontend(trace) + backend(bid_detail) 양쪽 중복 — backend 단일 책임 권장 |
| G2-P3-04 | `/bids` | sort 변경 시 page=1 reset이 의도된 동작인지 불분명 (URL 직접 편집 사용자에게 혼란) |
| G2-P3-05 | `/bids/trace` | 응찰업체 100개 초과 케이스 미처리 (page-size=100 한계) |
| G2-P3-06 | `/bids/trace` Stage6 | "체결 후 추적 가능" 안내만 — contract_tools 호출 미구현 표기 명확화 가능 |
| G2-P3-07 | `/lookup` | 합계 표시 100억 분모만(`(amount/100_000_000).toFixed(2)억`) — 다른 화면 fmtWon과 일관성 부재 |
| G2-P3-08 | `/lookup` mode=contract | 폼 입력은 받으나 backend 호출 없이 stub 안내 — 입력 disabled 권장 |

---

## C. 사용자 보고 사례 매핑

| 사례 | 매핑 결함 | 평가 |
|------|----------|------|
| F2 잔존 (입찰 추적이 빈 결과) | G2-P1-04 (note 무시) + G2-P1-05 (NTS 키 불일치) | trace 6단계 모두 ○ 표시 시 사용자는 "왜"를 알 수 없음. backend 폴백 노력(progressive 30→90→연도)이 무용지물처럼 보임. |
| F16 ("정보체계" 검색 0건) | G2-P1-01 (scan_coverage 미노출) + 30일 default | backend는 토큰 매칭(`bid.py:217-219`) + 기본 30일이라, "정보체계"가 30일 내 매칭되지 않으면 0건. coverage/chunks 안 보여 사용자가 "기간 늘리면 보일까"를 판단 못 함. |
| 입찰 추적 오래 걸림 | (구조적 문제) | trace는 6 Suspense로 분리되어 stage별 도착 즉시 표시 — 5초 SLA 설계는 적정. 다만 backend `get_bid_notice_detail`이 inqryDiv=3 미스 시 inqryDiv=1 폴백 + search_bid_notices 30→90→연도 폴백이라 R-prefix 케이스가 30+초 걸릴 수 있음. frontend는 이 동안 spinner 유지(D4 OK). |

---

## D. 권장 수정 우선순위

1. **G2-P0-01 즉시**: `/lookup` mode=biz/inst의 keys 객체 구조 통일 — backend가 모든 mode에서 4 키 dict 반환하도록 표준화. 또는 frontend가 mode별 다른 카드 레이아웃.
2. **G2-P1-05 검증 후 즉시**: NTS 키 이름 backend(`vendor.check_business_status`) 응답 schema 확인 → trace ntsLabel 정합화.
3. **G2-P1-03 + G2-P1-04**: Stage 컴포넌트들에 `r.ok` 분기 + `note` 표시 추가. extractMcpData도 통일.
4. **G2-P1-01 + G2-P1-02**: bids 검색 결과 헤더에 `scan_coverage_pct % (chunks_used개월 × endpoints_used개)` 표기 + `buildHref`에 deep/sort 보존.
5. **G2-P1-06 + G2-P1-07**: lookup mode=biz의 bid_notice_no_list 표시 + 기간 입력 form.

---

## E. 결론

3 화면 모두 골격(Suspense / EntityLink / 포맷터 일관)은 견고하나, **빈 결과/통신 오류/coverage**의 사용자 가시성 부족이 일관된 약점. P0 1건(lookup keys 형식)은 cross-lookup 핵심 기능 무력화 가능성. P1 7건 중 4건(scan_coverage / r.ok 분기 / note 노출 / NTS 키)이 사용자 보고 F2/F16과 직결.
