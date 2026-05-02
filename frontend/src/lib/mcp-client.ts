/**
 * GovProcu MCP HTTP 클라이언트.
 *
 * MCP Streamable HTTP transport 호환. AI SDK 5의 tool 호출에 직결.
 * UI-PLAN.md 기술 스택, FRONTEND-TECH.md Wave 2.
 */
import { buildMockResult } from "./mocks";

const MCP_URL = process.env.GOVPROCU_MCP_URL || "http://localhost:8080";
const MOCK_MODE = process.env.MCP_MOCK_MODE === "true";

export interface McpToolCall {
  name: string;
  arguments: Record<string, unknown>;
}

export interface McpResult {
  ok: boolean;
  data?: unknown;
  error?: string;
}

/**
 * MCP tool 호출 (Server Action·Route Handler에서 사용).
 * 클라이언트에서 직접 호출하지 않음 (CORS·인증 분리).
 *
 * MCP_MOCK_MODE=true 시 fixture 응답 (캡쳐 검증용).
 */
export async function callMcpTool(
  toolName: string,
  args: Record<string, unknown> = {},
): Promise<McpResult> {
  if (MOCK_MODE) {
    return { ok: true, data: buildMockResult(toolName) };
  }

  try {
    const resp = await fetch(`${MCP_URL}/mcp`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: Date.now(),
        method: "tools/call",
        params: { name: toolName, arguments: args },
      }),
    });
    if (!resp.ok) {
      return { ok: false, error: `HTTP ${resp.status}` };
    }
    const text = await resp.text();
    // SSE 또는 JSON 응답 파싱
    // SSE 의 keepalive ping(`: ping - N`) line 은 무시하고
    // 마지막 `data:` line 의 JSON 만 사용 (5/3 N40 — 22초+ 응답 대응)
    let payload: { result?: unknown };
    if (text.startsWith("event:") || text.includes("\ndata:")) {
      const dataLines = text
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim());
      const lastData = dataLines[dataLines.length - 1] || "{}";
      payload = JSON.parse(lastData);
    } else {
      payload = JSON.parse(text);
    }

    return { ok: true, data: payload.result };
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : String(err),
    };
  }
}

/**
 * 60개 도구 카탈로그 (frontend에서 자연어 콘솔이 LLM에 노출).
 * server.py에서 mcp.tool() 등록된 모든 함수.
 */
export const TOOL_CATALOG = {
  // bid (4)
  search_bid_notices: "키워드/업종/지역/기관/기간으로 입찰공고 검색",
  get_bid_notice_detail: "공고번호+차수로 입찰공고 단건 상세",
  list_pre_specifications: "사전규격공개 목록",
  get_pre_specification_detail: "사전규격 단건 상세",

  // award (5+1)
  list_bid_openings: "개찰결과 목록",
  search_awards: "낙찰 목록 (기간/기관/업종/키워드)",
  get_award_detail: "낙찰 단건 상세",
  search_awards_by_vendor: "업체 기준 낙찰 이력",
  list_bid_participants: "응찰업체 목록",

  // contract (4)
  get_contract_process: "계약 진행과정 통합 추적",
  search_contracts: "체결 계약 목록 (별도 키 필요)",
  list_contract_changes: "변경 계약 이력 (별도 키)",
  get_contract_detail: "계약 단건 상세",

  // stats (4+1)
  get_procurement_stats: "전체 조달 통계",
  list_top_vendors_by_period: "기간 내 상위 낙찰업체",
  agency_procurement_volume: "발주기관별 조달 규모",
  industry_procurement_stats: "업무대상별 조달 현황",

  // vendor (7+1)
  search_bid_participants: "응찰업체 검색 (EVAL 키 필요)",
  get_evaluation_scores: "평가점수 (EVAL 키 필요)",
  check_business_status: "NTS 사업자 상태 (휴/폐업)",
  verify_business_info: "NTS 사업자 진위확인",
  search_bids_by_vendor: "업체 기준 입찰 검색 (V1)",
  search_participations_by_vendor: "업체 기준 응찰 이력 (V2)",
  search_openings_by_vendor: "업체 기준 개찰 이력 (V3)",

  // analytics (6)
  find_similar_vendors: "동종업체 찾기",
  find_similar_bids: "유사 사업 찾기",
  industry_trend: "업종 동향",
  peer_analysis: "경쟁사 비교",
  market_share: "시장 점유",
  analyze_agency_price_pattern: "발주기관 사정률 패턴 (P1)",

  // workflow (5)
  trace_bid_lifecycle: "★ 입찰 전 생애주기 (사전규격→공고→개찰→낙찰→응찰업체→NTS)",
  vendor_profile: "업체 통합 프로필",
  agency_bid_summary: "발주기관 요약",
  competitor_analysis: "경쟁사 분석",
  agency_procurement_history: "발주기관 발주 이력 + 낙찰업체",

  // lookup (4)
  lookup_by_bid_no: "공고번호로 시작하여 4 키 추적",
  lookup_by_inst_code: "발주기관으로 시작",
  lookup_by_biz_no: "사업자번호로 시작",
  lookup_by_contract_no: "계약번호로 시작 (별도 키 필요)",

  // P0 (11): alerts (5) + watchlist (3) + qualification (3)
  subscribe_keyword_alerts: "키워드/조건 알림 구독",
  unsubscribe_keyword_alerts: "구독 해제",
  list_my_subscriptions: "내 구독 목록",
  daily_bid_digest: "오늘 신규공고 다이제스트",
  weekly_bid_digest: "지난 7일 요약",
  add_to_watchlist: "즐겨찾기 추가",
  remove_from_watchlist: "즐겨찾기 제거",
  list_my_watchlist: "내 즐겨찾기 목록",
  calc_qualification_score: "적격심사 점수 계산",
  calc_bid_price_score: "입찰가격 점수 단독 계산",
  get_qualification_rule: "적격심사 산식 안내",

  // P1 (7): prediction (3) + multi_agency (3) + analytics A6 (1)
  predict_bid_price: "투찰가 예측 (95% CI)",
  estimate_winning_threshold: "낙찰 하한가 추정",
  compare_bid_strategies: "응찰가 시나리오별 낙찰 확률",
  list_supported_agencies: "통합 지원 발주기관 목록",
  search_multi_agency_bids: "다중 발주기관 동시 검색",
  search_agency_specific: "특정 기관 단독 검색",
} as const;

export type ToolName = keyof typeof TOOL_CATALOG;
