/**
 * Mock fixtures — MCP_MOCK_MODE=true 일 때 callMcpTool 가 반환할 데이터.
 *
 * 운영 데이터를 흉내 낸 샘플로 11 페이지 전체 캡쳐 검증용.
 * 운영 환경에 절대 노출되면 안 됨 (env 분기 필수).
 */

const SAMPLE_BID_NO = "20240315678";
const SAMPLE_BID_ORD = "00";
const SAMPLE_BIZ = "1234567890";
const SAMPLE_INST = "국방재정관리단";

const sampleNotice = {
  bid_notice_no: SAMPLE_BID_NO,
  bid_ord: SAMPLE_BID_ORD,
  bid_title: "AI 기반 입찰정보 통합관리 시스템 구축",
  inst_name: SAMPLE_INST,
  biz_type: "용역",
  estimated_price: 320_000_000,
  base_amount: 295_000_000,
  publish_date: "20260420",
  open_date: "20260505",
  region: "서울",
  contract_method: "협상에 의한 계약",
};

const sampleNoticesList = [
  sampleNotice,
  {
    bid_notice_no: "20240315679",
    bid_ord: "00",
    bid_title: "AI 정책연구 용역",
    inst_name: "행정안전부",
    biz_type: "용역",
    estimated_price: 180_000_000,
    publish_date: "20260418",
    open_date: "20260503",
  },
  {
    bid_notice_no: "20240315680",
    bid_ord: "00",
    bid_title: "GovProcu 인프라 클라우드 전환",
    inst_name: "조달청",
    biz_type: "공사",
    estimated_price: 850_000_000,
    publish_date: "20260417",
    open_date: "20260502",
  },
];

const sampleVendors = [
  { biz_no: "1234567890", vendor_name: "디지털혁신㈜" },
  { biz_no: "9876543210", vendor_name: "스마트인포텍㈜" },
  { biz_no: "1122334455", vendor_name: "AI솔루션즈㈜" },
];

export const MOCK_FIXTURES: Record<string, unknown> = {
  // === bid 영역 ===
  search_bid_notices: {
    items: sampleNoticesList,
    total_count: sampleNoticesList.length,
    page: 1,
  },
  get_bid_notice_detail: sampleNotice,

  // === workflow — trace_bid_lifecycle (★ 핵심) ===
  trace_bid_lifecycle: {
    bid_notice_no: SAMPLE_BID_NO,
    bid_ord: SAMPLE_BID_ORD,
    summary: {
      title: sampleNotice.bid_title,
      inst_name: SAMPLE_INST,
      biz_type: "용역",
      estimated_price: sampleNotice.estimated_price,
      base_amount: sampleNotice.base_amount,
      publish_date: sampleNotice.publish_date,
      stages_complete: 5,
      stages_total: 6,
    },
    stages: {
      "1_pre_spec": {
        status: "found",
        items: [{ pre_spec_no: "PS-2024-0123", title: sampleNotice.bid_title }],
      },
      "2_notice": { status: "found", notice: sampleNotice },
      "3_participants": {
        status: "found",
        count: 12,
        items: sampleVendors.concat([
          { biz_no: "5544332211", vendor_name: "넥스트테크㈜" },
          { biz_no: "6677889900", vendor_name: "정보통신협력㈜" },
        ]),
      },
      "4_award": {
        status: "found",
        winner: {
          biz_no: "1234567890",
          vendor_name: "디지털혁신㈜",
          award_amount: 268_500_000,
          award_rate: 0.91,
        },
      },
      "5_nts_verify": {
        status: "found",
        biz_status_code: "01",
        verified: true,
      },
      "6_contract": {
        status: "found",
        contract_no: "C-2026-04-789",
        signed_date: "20260512",
        amount: 268_500_000,
      },
    },
  },

  // === vendor_profile ===
  vendor_profile: {
    summary: {
      biz_no: SAMPLE_BIZ,
      vendor_name: "디지털혁신㈜",
      nts_status_code: "01",
      bids_count: 38,
      participations_count: 42,
      openings_count: 35,
      awards_count: 14,
      awards_total_won: 3_750_000_000,
      awards_avg_won: 267_857_142,
      win_rate_pct: 36.84,
      implementation_status: "active",
    },
    sections: {
      awards: {
        items: [
          {
            open_date: "20260420",
            bid_notice_no: "20240315678",
            bid_ord: "00",
            bid_title: "AI 기반 입찰정보 통합관리 시스템",
            inst_name: SAMPLE_INST,
            award_amount: 268_500_000,
            award_rate: 0.91,
          },
          {
            open_date: "20260315",
            bid_notice_no: "20240310123",
            bid_title: "데이터 거버넌스 컨설팅",
            inst_name: "행정안전부",
            award_amount: 145_000_000,
            award_rate: 0.87,
          },
          {
            open_date: "20260205",
            bid_notice_no: "20240210456",
            bid_title: "디지털 트윈 PoC",
            inst_name: "국토교통부",
            award_amount: 98_000_000,
            award_rate: 0.93,
          },
        ],
      },
    },
  },

  // === agencies ===
  agency_procurement_history: {
    summary: {
      notice_count: 156,
      award_matched_count: 142,
      award_match_rate_pct: 91.0,
      award_total_won: 28_500_000_000,
    },
    items: [
      {
        bid_notice_no: SAMPLE_BID_NO,
        bid_ord: "00",
        title: sampleNotice.bid_title,
        biz_type: "용역",
        publish_date: "20260420",
        estimated_price: 320_000_000,
        winner: {
          winner_biz_no: SAMPLE_BIZ,
          winner_name: "디지털혁신㈜",
          award_amount: 268_500_000,
        },
      },
      {
        bid_notice_no: "20240310456",
        bid_ord: "00",
        title: "통합 보안관제 시스템 구축",
        biz_type: "공사",
        publish_date: "20260315",
        estimated_price: 1_200_000_000,
        winner: {
          winner_biz_no: "9876543210",
          winner_name: "스마트인포텍㈜",
          award_amount: 1_098_000_000,
        },
      },
    ],
  },
  analyze_agency_price_pattern: {
    sample_count: 142,
    summary_pct: { mean: 89.4, median: 90.2, p10: 84.5, p25: 87.1, p90: 93.8 },
    interpretation: "발주기관 평균 사정률 89.4% — 산업 평균(87.5%) 대비 약간 높음.",
  },

  // === analytics ===
  industry_trend: {
    total_count: 1284,
    total_amt: 152_300_000_000,
    monthly: [
      { yyyymm: "202511", count: 88, total_amt: 11_800_000_000, avg_amt: 134_090_909 },
      { yyyymm: "202512", count: 102, total_amt: 13_400_000_000, avg_amt: 131_372_549 },
      { yyyymm: "202601", count: 121, total_amt: 14_900_000_000, avg_amt: 123_140_495 },
      { yyyymm: "202602", count: 142, total_amt: 17_200_000_000, avg_amt: 121_126_760 },
      { yyyymm: "202603", count: 155, total_amt: 19_500_000_000, avg_amt: 125_806_451 },
      { yyyymm: "202604", count: 178, total_amt: 21_800_000_000, avg_amt: 122_471_910 },
    ],
  },
  market_share: {
    grand_total_won: 152_300_000_000,
    vendor_count_total: 487,
    top_vendors: [
      { biz_no: "1234567890", vendor_name: "디지털혁신㈜", awards_total: 8_750_000_000, share_pct: 5.74 },
      { biz_no: "9876543210", vendor_name: "스마트인포텍㈜", awards_total: 6_200_000_000, share_pct: 4.07 },
      { biz_no: "1122334455", vendor_name: "AI솔루션즈㈜", awards_total: 5_100_000_000, share_pct: 3.35 },
      { biz_no: "5544332211", vendor_name: "넥스트테크㈜", awards_total: 4_800_000_000, share_pct: 3.15 },
      { biz_no: "6677889900", vendor_name: "정보통신협력㈜", awards_total: 3_900_000_000, share_pct: 2.56 },
    ],
  },

  // === lookup ===
  lookup_by_bid_no: {
    bid_notice: sampleNotice,
    agency: { inst_code: "1234567", inst_name: SAMPLE_INST },
    winner: { biz_no: SAMPLE_BIZ, vendor_name: "디지털혁신㈜", award_amount: 268_500_000 },
    contract: { contract_no: "C-2026-04-789", signed_date: "20260512" },
  },
  lookup_by_biz_no: {
    vendor: { biz_no: SAMPLE_BIZ, vendor_name: "디지털혁신㈜" },
    recent_awards: 14,
    top_agencies: [
      { inst_name: SAMPLE_INST, deal_count: 5, total_amount: 1_200_000_000 },
      { inst_name: "행정안전부", deal_count: 3, total_amount: 580_000_000 },
    ],
  },
  lookup_by_inst_code: {
    agency: { inst_code: "1234567", inst_name: SAMPLE_INST },
    notice_count: 156,
    top_winners: [
      { winner_biz_no: SAMPLE_BIZ, winner_name: "디지털혁신㈜", deal_count: 5 },
      { winner_biz_no: "9876543210", winner_name: "스마트인포텍㈜", deal_count: 3 },
    ],
  },

  // === me ===
  list_my_watchlist: {
    total_count: 4,
    by_type: { bid: 2, vendor: 1, agency: 1 },
    items: [
      {
        id: 1,
        item_type: "bid",
        item_key: SAMPLE_BID_NO,
        item_label: "AI 통합관리 시스템",
        note: "5/5 개찰 — 응찰 검토",
        created_at: "2026-04-20 10:15",
      },
      {
        id: 2,
        item_type: "vendor",
        item_key: SAMPLE_BIZ,
        item_label: "디지털혁신㈜",
        note: "주요 경쟁사",
        created_at: "2026-04-15 09:00",
      },
      {
        id: 3,
        item_type: "agency",
        item_key: SAMPLE_INST,
        item_label: SAMPLE_INST,
        note: "",
        created_at: "2026-04-10 14:22",
      },
    ],
  },
  list_my_subscriptions: {
    subscription_count: 2,
    items: [
      {
        id: 1,
        keyword: "AI 시스템",
        biz_type: "용역",
        inst_name: "",
        notify_email: "me@example.com",
        created_at: "2026-04-01 09:00",
      },
      {
        id: 2,
        keyword: "데이터 분석",
        biz_type: "",
        inst_name: SAMPLE_INST,
        notify_email: "me@example.com",
        created_at: "2026-04-05 11:30",
      },
    ],
  },

  // === qualification ===
  calc_qualification_score: {
    total: 87.5,
    max_total: 100,
    ratio_pct: 87.5,
    scores: {
      bid_price: {
        score: 28,
        max: 30,
        detail: { bid_rate_pct: 91.0, lower_rate_pct: 87.745, status: "통과" },
      },
      experience: { score: 13, max: 15, detail: { ratio_pct: 86.7 } },
      tech_capability: { score: 18, max: 20, detail: { ratio_pct: 90.0 } },
      credit: { score: 14, max: 15, detail: { grade: "AA-", ratio: 0.93 } },
      management: { score: 9, max: 10 },
      etc: { score: 5.5, max: 10 },
    },
    note: "조달청 표준 산식. 입찰가격 점수가 가장 큰 비중.",
  },

  // === prediction ===
  predict_bid_price: {
    recommended_amount: 268_500_000,
    recommended_rate_pct: 91.02,
    ci_95: { low_amount: 254_200_000, high_amount: 282_800_000 },
    model: "휴리스틱 v0 — 발주기관 사정률 분위수 룩업",
    agency_pattern: {
      sample_count: 142,
      interpretation: "발주기관 평균 사정률 89.4% / 목표 0.7 → p25=87.1% 사용",
    },
  },
  compare_bid_strategies: {
    agency_sample_count: 142,
    scenarios: [
      { bid_rate_pct: 82, bid_amount: 241_900_000, estimated_win_prob: 0.95 },
      { bid_rate_pct: 85, bid_amount: 250_750_000, estimated_win_prob: 0.88 },
      { bid_rate_pct: 88, bid_amount: 259_600_000, estimated_win_prob: 0.74 },
      { bid_rate_pct: 90, bid_amount: 265_500_000, estimated_win_prob: 0.6 },
      { bid_rate_pct: 92, bid_amount: 271_400_000, estimated_win_prob: 0.42 },
      { bid_rate_pct: 95, bid_amount: 280_250_000, estimated_win_prob: 0.18 },
    ],
  },

  // === multi_agency ===
  list_supported_agencies: {
    agencies: [
      { agency: "g2b", name: "나라장터(G2B)", status: "active" },
      { agency: "lh", name: "한국토지주택공사(LH)", status: "pending_implementation" },
      { agency: "ex", name: "한국도로공사", status: "pending_implementation" },
      { agency: "kwater", name: "한국수자원공사", status: "pending_implementation" },
      { agency: "korail", name: "한국철도공사(코레일)", status: "pending_implementation" },
    ],
  },
};

/**
 * mock 응답 빌더 — MCP standard 응답 구조로 래핑.
 */
export function buildMockResult(toolName: string): { content: { type: "text"; text: string }[] } {
  const fixture = MOCK_FIXTURES[toolName];
  if (fixture === undefined) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ status: "mock_no_fixture", tool: toolName }),
        },
      ],
    };
  }
  return {
    content: [{ type: "text", text: JSON.stringify(fixture) }],
  };
}
