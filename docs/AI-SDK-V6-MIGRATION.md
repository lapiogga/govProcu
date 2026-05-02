# AI SDK v5 → v6 마이그레이션 가이드 (보류 트랙)

> 사용자 36번 발화 후속 보안 평가에서 분리. moderate 4건(`ai`/`jsondiffpatch`)은 file upload 기능을 쓰지 않는 본 프로젝트에서는 실 위험이 낮다고 판단해 차기 트랙으로 분리. 본 문서는 마이그레이션 시점에 즉시 착수할 수 있도록 변경 영역을 정리한 reference.

---

## 1. 현재 상태 (v5)

| 패키지 | 버전 | 사용 위치 |
|--------|------|----------|
| `ai` | ^4.0.0 (v5 시리즈로 deprecated 표기) | `app/api/chat/route.ts` (`streamText`, `tool`) |
| `@ai-sdk/anthropic` | ^1.0.0 | 동 route.ts (`anthropic("claude-sonnet-4-6")`) |
| `@ai-sdk/react` | ^1.0.0 | `app/console/page.tsx` (`useChat`) |

audit moderate 4건:
- `ai <5.0.52` filetype whitelist bypass — file upload API 사용 없음 → exposure 없음
- `jsondiffpatch <0.7.2` (HtmlFormatter XSS) — ai 의 transitive dep, 사용 없음

---

## 2. v6 주요 Breaking Changes

### 2.1 `streamText` tool 정의

```ts
// v5
streamText({
  tools: {
    trace_bid_lifecycle: tool({
      description: "...",
      parameters: z.object({ bid_notice_no: z.string() }),
      execute: async ({ bid_notice_no }) => { ... },
    }),
  },
  maxSteps: 5,
});
return result.toDataStreamResponse();

// v6
streamText({
  tools: {
    trace_bid_lifecycle: tool({
      description: "...",
      inputSchema: z.object({ bid_notice_no: z.string() }), // ← parameters → inputSchema
      execute: async ({ bid_notice_no }) => { ... },
    }),
  },
  stopWhen: stepCountIs(5), // ← maxSteps → stopWhen
});
return result.toUIMessageStreamResponse(); // ← toDataStreamResponse → toUIMessageStreamResponse
```

영향 파일: `frontend/src/app/api/chat/route.ts`

### 2.2 `useChat` 시그니처

```tsx
// v5
const { messages, input, handleInputChange, handleSubmit, isLoading } =
  useChat({ api: "/api/chat" });

// v6 — input 관리 사라짐, 사용자가 useState 로 직접 관리
const { messages, sendMessage, status, error } = useChat({
  transport: new DefaultChatTransport({ api: "/api/chat" }),
});
const [input, setInput] = useState("");

// submit 도 직접 작성
const onSubmit = (e: React.FormEvent) => {
  e.preventDefault();
  if (!input.trim()) return;
  sendMessage({ text: input });
  setInput("");
};
```

영향 파일: `frontend/src/app/console/page.tsx`

### 2.3 messages parts 구조

```tsx
// v5 — m.content (문자열) + m.toolInvocations (별도)
{messages.map((m) => (
  <div>
    {m.content}
    {m.toolInvocations?.map((t) => (
      <Tool key={t.toolCallId} tool={t} />
    ))}
  </div>
))}

// v6 — m.parts 배열로 통합
{messages.map((m) => (
  <div>
    {m.parts.map((part, i) => {
      if (part.type === "text") return <span key={i}>{part.text}</span>;
      if (part.type === "tool-call") return <ToolCall key={i} part={part} />;
      if (part.type === "tool-result") return <ToolResult key={i} part={part} />;
      if (part.type === "step-start") return null;
      return null;
    })}
  </div>
))}
```

영향 파일: `frontend/src/app/console/page.tsx` + `frontend/src/components/console/BidLifecycleCard.tsx` (Generative UI 호출부 수정 필요)

### 2.4 status 값

| v5 | v6 |
|----|----|
| `isLoading: boolean` | `status: 'submitted' \| 'streaming' \| 'ready' \| 'error'` |

```tsx
const isWorking = status === "submitted" || status === "streaming";
```

---

## 3. 마이그레이션 체크리스트

- [ ] `npm install ai@^6 @ai-sdk/anthropic@^2 @ai-sdk/react@^2`
- [ ] `route.ts`: `parameters` → `inputSchema`, `maxSteps: N` → `stopWhen: stepCountIs(N)`, `toDataStreamResponse()` → `toUIMessageStreamResponse()`
- [ ] `console/page.tsx`: `useChat` 반환값 갱신 + input state 분리 + `messages.map(m.parts.map(...))` 패턴 + status 분기
- [ ] `BidLifecycleCard` 호출부: tool-result part에서 `result` 추출 패턴 갱신
- [ ] mock 모드 호환성 검증 (`MCP_MOCK_MODE=true`)
- [ ] e2e/screenshots 재실행 → console 페이지 mock fallback 정상 확인

---

## 4. 보류 사유

본 프로젝트는 다음 이유로 v5 lock 유지가 합리적:

1. **moderate 위험만 잔존, exposure 없음** — `ai` filetype bypass 는 file upload API를 쓰지 않으면 도달 불가
2. **console 페이지가 시연 핵심이 아님** — mock 검증 단계에서는 ANTHROPIC_API_KEY 없이 빈 상태 fallback 충분
3. **breaking changes 광범위** — `useChat` 거의 전체 재작성 + Generative UI 패턴 변경
4. **차기 메이저 트랙으로 분리** — 운영 도입 직전 단계에서 일괄 처리 권장

마이그레이션 착수 시점:
- 사용자가 console 페이지를 실 운영 시연용으로 활성화하기로 결정
- 또는 ai SDK 가 v7 로 추가 메이저 업데이트되어 v5 EOL 임박
- 또는 v5 의 critical advisory 발견 시 즉시

---

## 5. v5 lock 설정

`package.json`:
```json
{
  "dependencies": {
    "ai": "^4.0.0",
    "@ai-sdk/anthropic": "^1.0.0",
    "@ai-sdk/react": "^1.0.0"
  }
}
```

새 메이저로의 자동 업그레이드 차단됨 (caret range 가 4.x 내 patch 만 허용).

작성: 2026-05-02 · NEXT8-T3 분석 결과 (마이그레이션 미실행, 가이드만 보존)
