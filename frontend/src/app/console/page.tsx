"use client";

import { useState } from "react";
import { useChat } from "@ai-sdk/react";
import { BidLifecycleCard } from "@/components/console/BidLifecycleCard";

const MOCK_DEMO_RESPONSE = {
  id: "mock-demo-1",
  role: "assistant" as const,
  content:
    "[데모 응답] 공고번호 20240315678 의 입찰 생애주기를 추적했습니다. " +
    "사전규격 등록 → 공고 (추정가 3.20억) → 응찰 12개사 → 낙찰자 디지털혁신㈜ (91.02%) → " +
    "NTS 계속사업자 확인 → 계약 체결 대기. 핵심 가치 도구 trace_bid_lifecycle 의 결과 6단계 정상.",
  toolInvocations: [
    {
      toolCallId: "mock-tc-1",
      toolName: "trace_bid_lifecycle",
      args: { bid_notice_no: "20240315678", bid_ord: "00" },
      state: "result" as const,
      result: {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              summary: {
                title: "AI 기반 입찰정보 통합관리 시스템 구축",
                inst_name: "국방재정관리단",
                biz_type: "용역",
                estimated_price: 320_000_000,
                participant_count: 12,
                publish_date: "20260420",
                open_date: "20260505",
                winner_name: "디지털혁신㈜",
                winner_biz_no: "1234567890",
                award_amount: 268_500_000,
                award_rate: 91.02,
              },
            }),
          },
        ],
      },
    },
  ],
};

/**
 * AI SDK 자연어 콘솔.
 * R&D-B: LLM이 GovProcu 도구를 자연어로 자동 호출.
 *
 * 시연 시나리오:
 * - "공고번호 20240315678 어떻게 됐어?" → trace_bid_lifecycle 호출
 * - "1234567890 사업자, 최근 6개월 낙찰 현황" → vendor_profile 호출
 * - "국방재정관리단 이번 달 발주 목록" → agency_procurement_history
 * - "이 입찰 적정 응찰가 추천해줘 (낙찰 70% 목표)" → predict_bid_price
 */
export default function ConsolePage() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } =
    useChat({ api: "/api/chat" });
  const [demoMode, setDemoMode] = useState(false);

  // 데모 모드 — ANTHROPIC_API_KEY 없는 환경에서 한 개 sample 메시지 표시
  const displayMessages = demoMode ? [MOCK_DEMO_RESPONSE] : messages;

  return (
    <main className="space-y-4">
      <header className="border-b pb-4">
        <h1 className="text-2xl font-semibold">AI 자연어 콘솔</h1>
        <p className="text-sm text-[var(--color-fg-muted)]">
          입찰·업체·기관·예측을 자연어로. LLM이 적절한 도구를 자동 호출합니다.
        </p>
      </header>

      <ol className="space-y-3 text-xs text-[var(--color-fg-muted)]">
        <li>예시: "공고번호 20240315678 어떻게 됐어?"</li>
        <li>예시: "사업자번호 1234567890의 최근 6개월 낙찰 현황"</li>
        <li>예시: "국방재정관리단 이번 달 발주 목록"</li>
        <li>예시: "추정가 12억 정보화 용역, 낙찰 70% 목표 응찰가 추천"</li>
      </ol>

      <div className="space-y-3 rounded-lg border bg-[var(--color-bg-muted)] p-4">
        {displayMessages.length === 0 && !demoMode && (
          <div className="text-center text-sm text-[var(--color-fg-muted)]">
            <p>아직 대화가 없습니다. 위 예시를 참고해 자연어로 질문하세요.</p>
            <button
              type="button"
              onClick={() => setDemoMode(true)}
              className="mt-2 text-xs text-[var(--color-primary)] underline"
            >
              ANTHROPIC_API_KEY 없이 데모 응답 보기 →
            </button>
          </div>
        )}
        {displayMessages.map((m: any) => (
          <div
            key={m.id}
            className={`rounded p-3 text-sm ${
              m.role === "user"
                ? "bg-[var(--color-bg)] ml-auto max-w-2xl"
                : "bg-[var(--color-bg)]"
            }`}
          >
            <div className="mb-1 text-xs text-[var(--color-fg-muted)]">
              {m.role === "user" ? "나" : "GovProcu AI"}
            </div>
            <div className="whitespace-pre-wrap">
              {m.content}
              {m.toolInvocations?.map((t: any, i: number) => (
                <div
                  key={i}
                  className="mt-2 space-y-2"
                >
                  <div className="rounded border-l-2 border-[var(--color-primary)] bg-[var(--color-bg-muted)] p-2 text-xs font-mono">
                    🔧 {t.toolName}({JSON.stringify(t.args)})
                  </div>
                  {t.state === "result" && (
                    <GenerativeRender toolName={t.toolName} args={t.args} result={t.result} />
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="text-xs text-[var(--color-fg-muted)]">
            ⏳ AI가 도구를 호출하는 중…
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          name="message"
          value={input}
          onChange={handleInputChange}
          placeholder="자연어로 질문하세요…"
          className="flex-1 rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading}
          className="rounded bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-[var(--color-primary-fg)] disabled:opacity-50"
        >
          전송
        </button>
      </form>

      <footer className="text-xs text-[var(--color-fg-muted)]">
        🤖 Claude Sonnet 4.6 + GovProcu MCP 60개 도구 (5종 etc 노출).
        ANTHROPIC_API_KEY · GOVPROCU_MCP_URL 환경변수 필요.
      </footer>
    </main>
  );
}

/**
 * NEXT4-3 Generative UI — tool 이름별로 적절한 컴포넌트 자동 렌더.
 */
function GenerativeRender({
  toolName,
  args,
  result,
}: {
  toolName: string;
  args: any;
  result: any;
}) {
  // MCP 응답 추출
  const data = extractData(result);
  if (!data) return null;

  if (toolName === "trace_bid_lifecycle" && data.summary) {
    return (
      <BidLifecycleCard
        bidNo={args.bid_notice_no}
        bidOrd={args.bid_ord || "00"}
        summary={data.summary}
      />
    );
  }

  // 기본 fallback: JSON dump
  return (
    <pre className="max-h-64 overflow-auto rounded bg-[var(--color-bg-muted)] p-2 text-[10px]">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function extractData(raw: any): any {
  if (!raw) return null;
  if (raw.content && Array.isArray(raw.content)) {
    const text = raw.content[0]?.text;
    if (text) {
      try {
        return JSON.parse(text);
      } catch {
        return null;
      }
    }
  }
  return raw;
}
