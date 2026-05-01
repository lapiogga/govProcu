/**
 * MCP 응답 → JSON 데이터 추출 헬퍼.
 * MCP는 {content: [{type:'text', text: <json>}]} 또는 직접 dict 형태로 응답.
 */
export function extractMcpData<T = unknown>(raw: unknown): T | null {
  if (!raw) return null;
  if (typeof raw === "object" && raw !== null) {
    const obj = raw as Record<string, unknown>;
    if (obj.content && Array.isArray(obj.content)) {
      const text = (obj.content[0] as { text?: string })?.text;
      if (text) {
        try {
          return JSON.parse(text) as T;
        } catch {
          return null;
        }
      }
    }
    return obj as T;
  }
  return null;
}
