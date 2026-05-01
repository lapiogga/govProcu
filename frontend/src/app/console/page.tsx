"use client";

import { useChat } from "@ai-sdk/react";

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
        {messages.map((m) => (
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
              {m.toolInvocations?.map((t, i) => (
                <div
                  key={i}
                  className="mt-2 rounded border-l-2 border-[var(--color-primary)] bg-[var(--color-bg-muted)] p-2 text-xs"
                >
                  <div className="font-mono">
                    🔧 {t.toolName}({JSON.stringify(t.args)})
                  </div>
                  {t.state === "result" && (
                    <pre className="mt-1 max-h-64 overflow-auto text-[10px]">
                      {JSON.stringify(t.result, null, 2)}
                    </pre>
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
