/**
 * AI SDK 5 자연어 콘솔 라우트.
 * R&D-B: LLM이 GovProcu 60개 도구를 자연어로 호출.
 *
 * 사용자 입력 → Anthropic Claude → tool 자동 선택 → MCP 호출 → streaming 결과.
 *
 * 환경변수:
 *   ANTHROPIC_API_KEY: Claude 호출
 *   GOVPROCU_MCP_URL: MCP 서버 (기본 localhost:8080)
 */
import { anthropic } from "@ai-sdk/anthropic";
import { streamText, tool } from "ai";
import { z } from "zod";
import { callMcpTool } from "@/lib/mcp-client";

export const maxDuration = 60;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: anthropic("claude-sonnet-4-6"),
    messages,
    system: [
      "당신은 GovProcu(나라장터 입찰정보 콘솔)의 AI 어시스턴트입니다.",
      "사용자의 자연어 질의를 받아 적절한 GovProcu 도구를 호출합니다.",
      "",
      "핵심 가치 도구:",
      "- trace_bid_lifecycle(bid_notice_no): 입찰 한 건의 사전규격→공고→개찰→낙찰→응찰업체→NTS 검증 6단계 통합",
      "- vendor_profile(vendor_biz_no): 업체의 NTS + 기간 내 입찰/응찰/개찰/낙찰 통계",
      "- agency_procurement_history(inst_name): 발주기관의 발주 이력 + 각 공고별 낙찰업체",
      "- predict_bid_price(bid_notice_no, target_win_probability): 적정 응찰가 예측",
      "",
      "응답은 한국어로 간결하게.",
    ].join("\n"),
    tools: {
      trace_bid_lifecycle: tool({
        description: "입찰 한 건의 전 생애주기(사전규격→공고→개찰→낙찰→응찰업체→NTS) 통합 추적",
        parameters: z.object({
          bid_notice_no: z.string().describe("입찰공고번호 (예: '20240315678')"),
          bid_ord: z.string().default("00").describe("차수"),
        }),
        execute: async ({ bid_notice_no, bid_ord }) => {
          const result = await callMcpTool("trace_bid_lifecycle", {
            bid_notice_no,
            bid_ord,
          });
          return result.data ?? { error: result.error };
        },
      }),
      vendor_profile: tool({
        description: "업체 사업자번호로 NTS 진위 + 입찰/응찰/개찰/낙찰 통계 통합 조회",
        parameters: z.object({
          vendor_biz_no: z.string().describe("사업자번호 10자리"),
          date_from: z.string().optional().describe("YYYYMMDD"),
          date_to: z.string().optional().describe("YYYYMMDD"),
        }),
        execute: async (args) => {
          const result = await callMcpTool("vendor_profile", args);
          return result.data ?? { error: result.error };
        },
      }),
      search_bid_notices: tool({
        description: "키워드/업종/지역/기관/기간으로 입찰공고 검색",
        parameters: z.object({
          keyword: z.string().optional(),
          biz_type: z.enum(["공사", "용역", "물품"]).optional(),
          inst_name: z.string().optional(),
          date_from: z.string().optional(),
          date_to: z.string().optional(),
          limit: z.number().default(20),
        }),
        execute: async (args) => {
          const result = await callMcpTool("search_bid_notices", args);
          return result.data ?? { error: result.error };
        },
      }),
      agency_procurement_history: tool({
        description: "특정 기간·발주기관의 발주 목록 + 각 발주별 낙찰업체 통합 조회",
        parameters: z.object({
          inst_name: z.string().describe("발주기관명"),
          date_from: z.string().optional(),
          date_to: z.string().optional(),
          biz_type: z.enum(["공사", "용역", "물품"]).optional(),
          limit: z.number().default(30),
        }),
        execute: async (args) => {
          const result = await callMcpTool("agency_procurement_history", args);
          return result.data ?? { error: result.error };
        },
      }),
      predict_bid_price: tool({
        description: "발주기관 사정률 패턴 + 목표 낙찰 확률 → 적정 응찰가 예측",
        parameters: z.object({
          bid_notice_no: z.string().optional(),
          base_amount: z.number().optional(),
          biz_type: z.enum(["공사", "용역", "물품"]).optional(),
          inst_name: z.string().optional(),
          target_win_probability: z.number().default(0.7),
        }),
        execute: async (args) => {
          const result = await callMcpTool("predict_bid_price", args);
          return result.data ?? { error: result.error };
        },
      }),
    },
    maxSteps: 5,
  });

  return result.toDataStreamResponse();
}
