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
  date_from?: string;
  date_to?: string;
  limit?: number;
}) {
  return callMcpTool("search_bid_notices", {
    ...params,
    limit: params.limit ?? 30,
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
