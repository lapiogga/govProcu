/**
 * AI SDK Generative UI 컴포넌트.
 * trace_bid_lifecycle 결과 → 카드 형태 자동 렌더.
 */
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface LifecycleSummary {
  title?: string;
  inst_name?: string;
  biz_type?: string;
  estimated_price?: number;
  participant_count?: number;
  winner_name?: string;
  winner_biz_no?: string;
  award_amount?: number;
  award_rate?: string;
  stages_found?: string[];
}

export function BidLifecycleCard({
  bidNo,
  bidOrd,
  summary,
}: {
  bidNo: string;
  bidOrd: string;
  summary: LifecycleSummary;
}) {
  const stages = ["pre_specification", "bid_notice", "participants", "award", "winner_nts_status"];
  const found = new Set(summary.stages_found || []);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle>
              {summary.title || `공고 ${bidNo}-${bidOrd}`}
            </CardTitle>
            <p className="mt-1 text-xs text-[var(--color-fg-muted)]">
              {summary.inst_name} · {summary.biz_type}
            </p>
          </div>
          <Badge variant="outline">{bidNo}-{bidOrd}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* 6단계 인디케이터 */}
        <div className="flex flex-wrap gap-2 text-xs">
          {stages.map((s, i) => (
            <Badge key={s} variant={found.has(s) ? "success" : "secondary"}>
              {i + 1}. {labelMap[s]}
            </Badge>
          ))}
        </div>

        {/* 핵심 KPI */}
        <div className="grid grid-cols-2 gap-3 text-sm lg:grid-cols-4">
          <Stat label="추정가" value={fmt(summary.estimated_price)} />
          <Stat label="응찰자" value={summary.participant_count ?? "—"} />
          <Stat label="낙찰가" value={fmt(summary.award_amount)} />
          <Stat label="낙찰률" value={summary.award_rate || "—"} />
        </div>

        {summary.winner_biz_no && (
          <div className="border-t pt-3 text-sm">
            낙찰자:{" "}
            <a
              href={`/vendors/${summary.winner_biz_no}`}
              className="text-[var(--color-primary)] hover:underline"
            >
              {summary.winner_name} ({summary.winner_biz_no})
            </a>
          </div>
        )}

        <div className="flex gap-2 border-t pt-3 text-xs">
          <a
            href={`/bids/trace?no=${bidNo}&ord=${bidOrd}`}
            className="text-[var(--color-primary)] hover:underline"
          >
            전체 화면 보기 →
          </a>
        </div>
      </CardContent>
    </Card>
  );
}

const labelMap: Record<string, string> = {
  pre_specification: "사전규격",
  bid_notice: "공고",
  participants: "응찰",
  award: "낙찰",
  winner_nts_status: "NTS",
};

function fmt(n: number | undefined): string {
  if (!n) return "—";
  if (n >= 100_000_000) return `${(n / 100_000_000).toFixed(2)}억`;
  return n.toLocaleString("ko-KR");
}

function Stat({ label, value }: { label: string; value: any }) {
  return (
    <div className="rounded border bg-[var(--color-bg-muted)] p-2">
      <div className="text-xs text-[var(--color-fg-muted)]">{label}</div>
      <div className="font-mono text-sm font-medium tabular-nums">{value}</div>
    </div>
  );
}
