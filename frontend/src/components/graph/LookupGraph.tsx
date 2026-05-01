"use client";

/**
 * Cross-Lookup 4 키 그래프 시각화 (xyflow).
 * 공고/사업자/기관/계약 노드 + 관계 엣지.
 */
import {
  ReactFlow,
  Background,
  Controls,
  MarkerType,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

interface LookupKeys {
  bid_notice_no?: string | null;
  bid_ord?: string | null;
  inst_code?: string | null;
  inst_name?: string | null;
  vendor_biz_no?: string | null;
  vendor_name?: string | null;
  contract_no?: string | null;
}

export function LookupGraph({
  keys,
  startingKey,
}: {
  keys: LookupKeys;
  startingKey: "bid" | "biz" | "inst" | "contract";
}) {
  const nodes: Node[] = [
    {
      id: "bid",
      type: "default",
      position: { x: 50, y: 50 },
      data: {
        label: keys.bid_notice_no
          ? `📋 ${keys.bid_notice_no}-${keys.bid_ord || "00"}`
          : "📋 공고번호 (없음)",
      },
      style: nodeStyle(startingKey === "bid", !!keys.bid_notice_no),
    },
    {
      id: "inst",
      type: "default",
      position: { x: 380, y: 50 },
      data: {
        label: keys.inst_name
          ? `🏛 ${keys.inst_name}${keys.inst_code ? ` (${keys.inst_code})` : ""}`
          : "🏛 발주기관 (없음)",
      },
      style: nodeStyle(startingKey === "inst", !!keys.inst_name),
    },
    {
      id: "vendor",
      type: "default",
      position: { x: 50, y: 220 },
      data: {
        label: keys.vendor_biz_no
          ? `🏢 ${keys.vendor_name || ""} (${keys.vendor_biz_no})`
          : "🏢 사업자번호 (없음)",
      },
      style: nodeStyle(startingKey === "biz", !!keys.vendor_biz_no),
    },
    {
      id: "contract",
      type: "default",
      position: { x: 380, y: 220 },
      data: {
        label: keys.contract_no ? `📜 ${keys.contract_no}` : "📜 계약번호 (없음)",
      },
      style: nodeStyle(startingKey === "contract", !!keys.contract_no),
    },
  ];

  const edges: Edge[] = [];
  if (keys.bid_notice_no && keys.inst_name) {
    edges.push(edge("bid", "inst", "ISSUED_BY"));
  }
  if (keys.bid_notice_no && keys.vendor_biz_no) {
    edges.push(edge("bid", "vendor", "AWARDED_TO"));
  }
  if (keys.bid_notice_no && keys.contract_no) {
    edges.push(edge("bid", "contract", "CONTRACTED_AS"));
  }
  if (keys.contract_no && keys.vendor_biz_no) {
    edges.push(edge("contract", "vendor", "SIGNED_WITH"));
  }
  if (keys.inst_name && keys.vendor_biz_no) {
    edges.push(edge("inst", "vendor", "거래"));
  }

  return (
    <div className="h-[420px] rounded-lg border bg-[var(--color-bg)]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        nodesDraggable={false}
        nodesConnectable={false}
      >
        <Background gap={16} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

function edge(source: string, target: string, label: string): Edge {
  return {
    id: `${source}-${target}`,
    source,
    target,
    label,
    labelStyle: { fontSize: 11, fill: "var(--color-fg-muted)" },
    style: { stroke: "var(--color-fg-muted)", strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "var(--color-fg-muted)" },
  };
}

function nodeStyle(isStart: boolean, hasValue: boolean) {
  const base = {
    border: "1px solid var(--color-border)",
    borderRadius: 8,
    padding: 12,
    fontSize: 13,
    fontWeight: 500,
    width: 280,
  };
  if (isStart) {
    return {
      ...base,
      background: "oklch(95% 0.05 250)",
      borderColor: "var(--color-primary)",
      borderWidth: 2,
    };
  }
  if (!hasValue) {
    return { ...base, background: "var(--color-bg-muted)", opacity: 0.5 };
  }
  return { ...base, background: "var(--color-bg)" };
}
