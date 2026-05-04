"use server";

/**
 * Server Actions — MCP 도구 호출 (RSC에서 직접 사용).
 * UI Phase B 핵심: trace_bid_lifecycle, vendor_profile, search_bid_notices.
 */
import { callMcpTool } from "./mcp-client";

export async function traceBidLifecycle(bidNoticeNo: string, bidOrd = "00") {
  return callMcpTool("trace_bid_lifecycle", {
    bid_notice_no: bidNoticeNo,
    bid_ord: bidOrd,
  });
}

// v26.1: trace Streaming 분리 호출용 5 stage actions
// 각 도구는 backend에서 @cache_result(30분) 적용됨 (v23.5).
// page.tsx에서 6 Suspense로 분리하면 stage별 도착 즉시 화면.

export async function getPreSpecDetail(bidNoticeNo: string, bidOrd = "00") {
  return callMcpTool("get_pre_specification_detail", {
    bid_notice_no: bidNoticeNo,
    bid_ord: bidOrd,
  });
}

export async function getBidNoticeDetail(bidNoticeNo: string, bidOrd = "00") {
  return callMcpTool("get_bid_notice_detail", {
    bid_notice_no: bidNoticeNo,
    bid_ord: bidOrd,
  });
}

export async function listBidParticipants(bidNoticeNo: string, bidOrd = "00") {
  return callMcpTool("list_bid_participants", {
    bid_notice_no: bidNoticeNo,
    bid_ord: bidOrd,
  });
}

export async function getAwardDetail(bidNoticeNo: string, bidOrd = "00") {
  return callMcpTool("get_award_detail", {
    bid_notice_no: bidNoticeNo,
    bid_ord: bidOrd,
  });
}

export async function checkBusinessStatus(bizNos: string[]) {
  return callMcpTool("check_business_status", {
    biz_nos: bizNos,
  });
}

export async function getVendorProfile(
  vendorBizNo: string,
  dateFrom?: string,
  dateTo?: string,
) {
  return callMcpTool("vendor_profile", {
    vendor_biz_no: vendorBizNo,
    date_from: dateFrom,
    date_to: dateTo,
  });
}

export async function searchBidNotices(params: {
  keyword?: string;
  biz_type?: string;
  inst_name?: string;
  indstryty_cd?: string;  // P31-R3 (F23): 업종 코드 4자리 (G2B 서버측 필터)
  bid_notice_no?: string; // P32-R1 (F31): R-prefix bid_no 단건 모드 (P31-R1 backend 단건 모드 활용)
  date_from?: string;
  date_to?: string;
  limit?: number;
  page?: number;
  scan_pages?: number;
}) {
  return callMcpTool("search_bid_notices", {
    ...params,
    limit: params.limit ?? 30,
    page: params.page ?? 1,
    scan_pages: params.scan_pages ?? 1,
  });
}

export async function getAgencyHistory(
  instName: string,
  dateFrom?: string,
  dateTo?: string,
  bizType?: string,
) {
  return callMcpTool("agency_procurement_history", {
    inst_name: instName,
    date_from: dateFrom,
    date_to: dateTo,
    biz_type: bizType,
    limit: 30,
  });
}

export async function getAgencyPricePattern(
  instName: string,
  bizType?: string,
  dateFrom?: string,
  dateTo?: string,
) {
  return callMcpTool("analyze_agency_price_pattern", {
    inst_name: instName,
    biz_type: bizType,
    date_from: dateFrom,
    date_to: dateTo,
    limit: 200,
  });
}

export async function getIndustryTrend(
  bizType: string,
  instName?: string,
  dateFrom?: string,
  dateTo?: string,
) {
  return callMcpTool("industry_trend", {
    biz_type: bizType,
    inst_name: instName,
    date_from: dateFrom,
    date_to: dateTo,
  });
}

export async function getMarketShare(
  bizType: string,
  dateFrom?: string,
  dateTo?: string,
  topN = 20,
) {
  return callMcpTool("market_share", {
    biz_type: bizType,
    date_from: dateFrom,
    date_to: dateTo,
    top_n: topN,
  });
}

// 즐겨찾기
export async function listMyWatchlist(itemType?: string) {
  return callMcpTool("list_my_watchlist", {
    user_token: "default",
    item_type: itemType,
  });
}

export async function addToWatchlist(
  itemType: "bid" | "vendor" | "agency" | "contract",
  itemKey: string,
  itemLabel?: string,
  note?: string,
) {
  return callMcpTool("add_to_watchlist", {
    item_type: itemType,
    item_key: itemKey,
    item_label: itemLabel,
    note,
    user_token: "default",
  });
}

export async function removeFromWatchlist(
  itemType: string,
  itemKey: string,
) {
  return callMcpTool("remove_from_watchlist", {
    item_type: itemType,
    item_key: itemKey,
    user_token: "default",
  });
}

// 알림
export async function listMySubscriptions() {
  return callMcpTool("list_my_subscriptions", { user_token: "default" });
}

export async function subscribeKeyword(params: {
  keyword: string;
  biz_type?: string;
  inst_name?: string;
  region?: string;
  notify_email?: string;
}) {
  return callMcpTool("subscribe_keyword_alerts", {
    ...params,
    user_token: "default",
  });
}

export async function unsubscribeKeyword(subscriptionId: number) {
  return callMcpTool("unsubscribe_keyword_alerts", {
    subscription_id: subscriptionId,
    user_token: "default",
  });
}

// 적격심사
export async function calcQualification(params: {
  bid_amount: number;
  base_amount: number;
  biz_type: string;
  estimated_price?: number;
  experience_actual?: number;
  experience_standard?: number;
  tech_count?: number;
  tech_required?: number;
  credit_grade?: string;
}) {
  return callMcpTool("calc_qualification_score", params);
}

// 투찰가 예측
export async function predictBidPrice(params: {
  bid_notice_no?: string;
  base_amount?: number;
  biz_type?: string;
  inst_name?: string;
  target_win_probability?: number;
}) {
  return callMcpTool("predict_bid_price", params);
}

export async function compareBidStrategies(params: {
  base_amount: number;
  inst_name: string;
  biz_type?: string;
  strategies?: number[];
}) {
  return callMcpTool("compare_bid_strategies", params);
}

// Cross-Lookup
export async function lookupByBidNo(bidNoticeNo: string, bidOrd = "00") {
  return callMcpTool("lookup_by_bid_no", {
    bid_notice_no: bidNoticeNo,
    bid_ord: bidOrd,
  });
}

export async function lookupByBizNo(
  vendorBizNo: string,
  dateFrom?: string,
  dateTo?: string,
) {
  return callMcpTool("lookup_by_biz_no", {
    vendor_biz_no: vendorBizNo,
    date_from: dateFrom,
    date_to: dateTo,
  });
}

export async function lookupByInstCode(
  instName: string,
  dateFrom?: string,
  dateTo?: string,
) {
  return callMcpTool("lookup_by_inst_code", {
    inst_name: instName,
    date_from: dateFrom,
    date_to: dateTo,
  });
}

// 업체명 LIKE 검색 (5/3 N41) — search_awards_by_vendor 활용
// P30-R3 P1-09: page 파라미터 추가 — 페이지네이션 지원 ("더 보기" 링크)
export async function searchVendorsByName(
  vendorName: string,
  dateFrom?: string,
  dateTo?: string,
  limit = 30,
  page = 1,
) {
  return callMcpTool("search_awards_by_vendor", {
    vendor_name: vendorName,
    date_from: dateFrom,
    date_to: dateTo,
    limit,
    page,
  });
}

// 외부 발주기관 OpenAPI (5/2 N26 + N30 — biz_type)
export async function searchKwaterContracts(
  searchDt?: string,
  bizType?: string,
  limit = 30,
) {
  return callMcpTool("search_kwater_contracts", {
    search_dt: searchDt,
    biz_type: bizType,
    limit,
  });
}

export async function listExternalAdapters() {
  return callMcpTool("list_external_adapters", {});
}
