/**
 * Mock fixtures — MCP_MOCK_MODE=true 일 때 callMcpTool 가 반환할 데이터.
 *
 * 각 fixture 의 schema 는 해당 페이지 RSC가 기대하는 형태와 정확히 일치해야 한다.
 * (페이지 코드 base — 임의 수정 금지)
 *
 * 운영 환경에 절대 노출되면 안 됨 (env 분기 필수).
 */

const SAMPLE_BID_NO = "20240315678";
const SAMPLE_BID_ORD = "00";
const SAMPLE_BIZ = "1234567890";
const SAMPLE_INST = "국방재정관리단";
const SAMPLE_INST_CODE = "1234567";
const SAMPLE_CONTRACT = "C-2026-04-789";

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

const traceParticipants = [
  { opening_rank: 1, participant_name: "디지털혁신㈜", participant_biz_no: SAMPLE_BIZ, participant_bid_amount: 268_500_000, is_winner: true },
  { opening_rank: 2, participant_name: "스마트인포텍㈜", participant_biz_no: "9876543210", participant_bid_amount: 271_400_000, is_winner: false },
  { opening_rank: 3, participant_name: "AI솔루션즈㈜", participant_biz_no: "1122334455", participant_bid_amount: 273_200_000, is_winner: false },
  { opening_rank: 4, participant_name: "넥스트테크㈜", participant_biz_no: "5544332211", participant_bid_amount: 275_800_000, is_winner: false },
  { opening_rank: 5, participant_name: "정보통신협력㈜", participant_biz_no: "6677889900", participant_bid_amount: 278_500_000, is_winner: false },
];

export const MOCK_FIXTURES: Record<string, unknown> = {
  // === bid 영역 ===
  search_bid_notices: {
    items: sampleNoticesList,
    total_count: sampleNoticesList.length,
    page: 1,
  },
  get_bid_notice_detail: sampleNotice,

  // === workflow — trace_bid_lifecycle (★ 핵심, 페이지 schema 정확히 일치) ===
  trace_bid_lifecycle: {
    summary: {
      title: sampleNotice.bid_title,
      inst_name: SAMPLE_INST,
      biz_type: "용역",
      estimated_price: sampleNotice.estimated_price,
      participant_count: 12,
      publish_date: sampleNotice.publish_date,
      open_date: sampleNotice.open_date,
      winner_name: "디지털혁신㈜",
      winner_biz_no: SAMPLE_BIZ,
      award_amount: 268_500_000,
      award_rate: 91.02, // percentage 단위 (fmtRate 가 toFixed(2) + "%")
    },
    stages: {
      pre_specification: { found: true, items: [{ pre_spec_no: "PS-2024-0123" }] },
      bid_notice: { found: true, notice: sampleNotice },
      participants: {
        participant_count: 12,
        items: traceParticipants,
      },
      award: {
        found: true,
        summary: {
          winner_name: "디지털혁신㈜",
          winner_biz_no: SAMPLE_BIZ,
          award_amount: 268_500_000,
          award_rate: 91.02,
        },
      },
      winner_nts_status: {
        items: [{ b_stt_cd: "01", b_stt: "계속사업자" }],
      },
      contract: { found: false },
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
            bid_notice_no: SAMPLE_BID_NO,
            bid_ord: "00",
            bid_title: "AI 기반 입찰정보 통합관리 시스템",
            inst_name: SAMPLE_INST,
            award_amount: 268_500_000,
            award_rate: 91.02,
          },
          {
            open_date: "20260315",
            bid_notice_no: "20240310123",
            bid_title: "데이터 거버넌스 컨설팅",
            inst_name: "행정안전부",
            award_amount: 145_000_000,
            award_rate: 87.5,
          },
          {
            open_date: "20260205",
            bid_notice_no: "20240210456",
            bid_title: "디지털 트윈 PoC",
            inst_name: "국토교통부",
            award_amount: 98_000_000,
            award_rate: 93.4,
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
      { biz_no: SAMPLE_BIZ, name: "디지털혁신㈜", award_total: 8_750_000_000, award_count: 32, market_share_pct: 5.74 },
      { biz_no: "9876543210", name: "스마트인포텍㈜", award_total: 6_200_000_000, award_count: 24, market_share_pct: 4.07 },
      { biz_no: "1122334455", name: "AI솔루션즈㈜", award_total: 5_100_000_000, award_count: 19, market_share_pct: 3.35 },
      { biz_no: "5544332211", name: "넥스트테크㈜", award_total: 4_800_000_000, award_count: 17, market_share_pct: 3.15 },
      { biz_no: "6677889900", name: "정보통신협력㈜", award_total: 3_900_000_000, award_count: 14, market_share_pct: 2.56 },
    ],
  },

  // === lookup (페이지 schema: data.keys.{bid_notice_no, bid_ord, inst_code, inst_name, vendor_biz_no, vendor_name, contract_no}) ===
  lookup_by_bid_no: {
    keys: {
      bid_notice_no: SAMPLE_BID_NO,
      bid_ord: SAMPLE_BID_ORD,
      inst_code: SAMPLE_INST_CODE,
      inst_name: SAMPLE_INST,
      vendor_biz_no: SAMPLE_BIZ,
      vendor_name: "디지털혁신㈜",
      contract_no: SAMPLE_CONTRACT,
    },
    summary: {
      title: sampleNotice.bid_title,
      estimated_price: 320_000_000,
      award_amount: 268_500_000,
      award_rate: 91.02,
    },
  },
  lookup_by_biz_no: {
    keys: {
      bid_notice_no: SAMPLE_BID_NO,
      bid_ord: SAMPLE_BID_ORD,
      inst_code: SAMPLE_INST_CODE,
      inst_name: SAMPLE_INST,
      vendor_biz_no: SAMPLE_BIZ,
      vendor_name: "디지털혁신㈜",
      contract_no: SAMPLE_CONTRACT,
    },
    summary: {
      vendor_name: "디지털혁신㈜",
      recent_awards: 14,
      total_awards_won: 3_750_000_000,
    },
  },
  lookup_by_inst_code: {
    keys: {
      bid_notice_no: SAMPLE_BID_NO,
      bid_ord: SAMPLE_BID_ORD,
      inst_code: SAMPLE_INST_CODE,
      inst_name: SAMPLE_INST,
      vendor_biz_no: SAMPLE_BIZ,
      vendor_name: "디지털혁신㈜",
      contract_no: SAMPLE_CONTRACT,
    },
    summary: {
      inst_name: SAMPLE_INST,
      notice_count: 156,
      total_award_won: 28_500_000_000,
    },
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

  // === 업체명 LIKE 검색 (5/3 N41) — search_awards_by_vendor mock ===
  search_awards_by_vendor: {
    items: [
      {
        bid_no: "20260315678",
        bid_ord: "00",
        bid_title: "AI 기반 정보화전략계획(ISP) 수립 용역",
        winner_name: "디지털혁신㈜",
        winner_biz_no: "1234567890",
        award_amount: 268_500_000,
        open_date: "20260315",
        inst_name: "조달청",
      },
      {
        bid_no: "20260301456",
        bid_ord: "00",
        bid_title: "차세대 통합정보시스템 구축 1단계",
        winner_name: "디지털혁신㈜",
        winner_biz_no: "1234567890",
        award_amount: 412_000_000,
        open_date: "20260301",
        inst_name: "행정안전부",
      },
      {
        bid_no: "20260220123",
        bid_ord: "00",
        bid_title: "공공 데이터 분석 플랫폼 운영 용역",
        winner_name: "테크솔루션 주식회사",
        winner_biz_no: "9876543210",
        award_amount: 195_000_000,
        open_date: "20260220",
        inst_name: "한국정보화진흥원",
      },
      {
        bid_no: "20260105789",
        bid_ord: "01",
        bid_title: "스마트시티 IoT 인프라 구축",
        winner_name: "스마트시스템즈㈜",
        winner_biz_no: "5555556666",
        award_amount: 850_000_000,
        open_date: "20260105",
        inst_name: "국토교통부",
      },
    ],
    total_count: 4,
    scanned: 4,
    returned_count: 4,
    has_more: false,
    endpoints_used: ["/ScsbidInfoService/getOpengResultListInfoServc"],
    filter: {
      vendor_biz_no: null,
      vendor_name: "혁신",
      date_range: [null, null],
      biz_type: null,
    },
  },

  // === external — KWater contract API (5/2 N26 — 실 응답 구조 그대로) ===
  search_kwater_contracts: {
    items: [
      {
        contract_no: "C3202206398",
        contract_date: "20220531",
        title: "보현산댐 부유물 적치장 설치공사",
        inst_name: "한국수자원공사",
        dept_name: "보현산댐지사",
        biz_type: "공사",
        winner_name: "주식회사 예인",
        contract_method: "소액전자",
        limit_method: "-",
        contract_amount: 177_023_000,
        period_from: "20220613",
        period_to: "20220811",
      },
      {
        contract_no: "C3202205364",
        contract_date: "20220531",
        title: "소양강댐 부유물 수거시설 개선공사",
        inst_name: "한국수자원공사",
        dept_name: "소양강댐지사",
        biz_type: "공사",
        winner_name: "다지건설주식회사",
        contract_method: "제한경쟁",
        limit_method: "지역제한",
        contract_amount: 192_174_000,
        period_from: "20220610",
        period_to: "20221206",
      },
      {
        contract_no: "C3202206022",
        contract_date: "20220531",
        title: "2022년 가평군 지방상수도 현대화사업 노후수도미터 교체공사",
        inst_name: "한국수자원공사",
        dept_name: "수도권지역협력단",
        biz_type: "공사",
        winner_name: "주식회사 백율",
        contract_method: "소액전자",
        limit_method: "-",
        contract_amount: 135_190_000,
        period_from: "20220613",
        period_to: "20230207",
      },
      {
        contract_no: "C5202205025",
        contract_date: "20220531",
        title: "광주시 노후 상수관로 교체공사 건설폐기물 처리용역(1차년도)",
        inst_name: "한국수자원공사",
        dept_name: "광주수도지사",
        biz_type: "용역",
        winner_name: "현대환경(주)",
        contract_method: "일반경쟁",
        limit_method: "-",
        contract_amount: 55_182_000,
        period_from: "20220610",
        period_to: "20230204",
      },
      {
        contract_no: "C5202206949",
        contract_date: "20220531",
        title: "임하댐 송강리 생태계 복원사업 공사시 사후모니터링 용역",
        inst_name: "한국수자원공사",
        dept_name: "낙동강영영처",
        biz_type: "용역",
        winner_name: "대현종합기술 주식회사",
        contract_method: "제한경쟁",
        limit_method: "-",
        contract_amount: 114_906_000,
        period_from: "20220607",
        period_to: "20230810",
      },
    ],
    total_count: 61,
    agency: "kwater",
    endpoint: "https://apis.data.go.kr/B500001/ebid/cntrct3/cntrwkList",
    raw_count: 5,
    status: "active",
  },
  list_external_adapters: {
    items: [
      {
        agency: "kwater",
        name: "한국수자원공사",
        base_url: "https://apis.data.go.kr/B500001",
        service_key_env: "KWATER_API_KEY",
        status: "active",
      },
      {
        agency: "lh",
        name: "한국토지주택공사(LH)",
        base_url: "https://apis.data.go.kr/1611000",
        service_key_env: "LH_API_KEY",
        status: "pending_implementation",
      },
      {
        agency: "ex",
        name: "한국도로공사",
        base_url: "https://apis.data.go.kr/1320000",
        service_key_env: "EX_API_KEY",
        status: "pending_implementation",
      },
      {
        agency: "korail",
        name: "한국철도공사(코레일)",
        base_url: "https://apis.data.go.kr/1230000",
        service_key_env: "KORAIL_API_KEY",
        status: "pending_implementation",
      },
    ],
    active_count: 1,
    total: 4,
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
