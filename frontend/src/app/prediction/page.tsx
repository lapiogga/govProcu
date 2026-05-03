/**
 * 투찰가 예측 — predict_bid_price + compare_bid_strategies
 */
import { Suspense } from "react";
import { predictBidPrice, compareBidStrategies } from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";
import { fmtWon } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const SELECT_CLASS =
  "flex h-9 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]";

export default async function PredictionPage(props: {
  searchParams: Promise<{
    bid_no?: string;
    base?: string;
    inst?: string;
    type?: string;
    target?: string;
  }>;
}) {
  const sp = await props.searchParams;
  const hasInput = !!(sp.bid_no || (sp.base && sp.inst));

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">투찰가 예측</h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          발주기관 사정률 패턴 + 목표 낙찰확률 → 적정 응찰가 + 95% CI
        </p>
      </header>

      <Card>
        <CardContent className="p-4">
          <form action="/prediction" className="grid grid-cols-2 gap-3 lg:grid-cols-3">
            <div className="space-y-1 lg:col-span-3">
              <Label htmlFor="bid_no" className="text-xs text-[var(--color-fg-muted)]">
                공고번호 (자동 메타 추출)
              </Label>
              <Input
                id="bid_no"
                name="bid_no"
                defaultValue={sp.bid_no}
                placeholder="20240315678 (또는 base+inst 직접 입력)"
              />
            </div>

            <div className="space-y-1">
              <Label htmlFor="base" className="text-xs text-[var(--color-fg-muted)]">
                기초금액 (원)
              </Label>
              <Input id="base" name="base" defaultValue={sp.base} />
            </div>

            <div className="space-y-1">
              <Label htmlFor="inst" className="text-xs text-[var(--color-fg-muted)]">
                발주기관
              </Label>
              <Input id="inst" name="inst" defaultValue={sp.inst} />
            </div>

            <div className="space-y-1">
              <Label htmlFor="type" className="text-xs text-[var(--color-fg-muted)]">
                업종
              </Label>
              <select id="type" name="type" defaultValue={sp.type || "용역"} className={SELECT_CLASS}>
                <option value="공사">공사</option>
                <option value="용역">용역</option>
                <option value="물품">물품</option>
              </select>
            </div>

            <div className="space-y-1">
              <Label htmlFor="target" className="text-xs text-[var(--color-fg-muted)]">
                목표 낙찰 확률
              </Label>
              <select
                id="target"
                name="target"
                defaultValue={sp.target || "0.7"}
                className={SELECT_CLASS}
              >
                <option value="0.9">매우 높음 (0.9 — p10 근처)</option>
                <option value="0.7">높음 (0.7 — p25 근처)</option>
                <option value="0.5">중간 (0.5 — median)</option>
                <option value="0.3">낮음 (0.3 — p75)</option>
              </select>
            </div>

            <Button type="submit" className="self-end">
              예측
            </Button>
          </form>
        </CardContent>
      </Card>

      {hasInput && (
        <Suspense fallback={<Skel h={32} />}>
          <PredictResult params={sp} />
        </Suspense>
      )}

      {sp.base && sp.inst && (
        <Suspense fallback={<Skel h={32} />}>
          <ScenarioTable params={sp} />
        </Suspense>
      )}
    </main>
  );
}

async function PredictResult({ params }: { params: any }) {
  const r = await predictBidPrice({
    bid_notice_no: params.bid_no || undefined,
    base_amount: params.base ? parseInt(params.base) : undefined,
    biz_type: params.type,
    inst_name: params.inst,
    target_win_probability: parseFloat(params.target || "0.7"),
  });
  if (!r.ok) {
    return (
      <Card className="border-[var(--color-danger)]">
        <CardContent className="p-4 text-sm">오류: {r.error}</CardContent>
      </Card>
    );
  }
  const data = extractMcpData<any>(r.data);
  if (!data || data.status === "missing_base_amount") {
    return (
      <Card>
        <CardContent className="p-4 text-sm">
          기초금액 + 발주기관(또는 공고번호) 입력 필요.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-[var(--color-bg-muted)]">
      <CardHeader>
        <CardTitle>예측 결과</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Stat label="추정 응찰가" v={fmtWon(data.recommended_amount)} highlight />
          <Stat label="추정 응찰률" v={`${data.recommended_rate_pct}%`} />
          <Stat label="95% CI 하한" v={fmtWon(data.ci_95?.low_amount)} />
          <Stat label="95% CI 상한" v={fmtWon(data.ci_95?.high_amount)} />
        </div>
        <p className="mt-3 text-xs text-[var(--color-fg-muted)]">
          모델: {data.model} · 발주기관 샘플 n={data.agency_pattern?.sample_count ?? "n/a"} ·{" "}
          {data.agency_pattern?.interpretation || data.note}
        </p>
      </CardContent>
    </Card>
  );
}

async function ScenarioTable({ params }: { params: any }) {
  const r = await compareBidStrategies({
    base_amount: parseInt(params.base),
    inst_name: params.inst,
    biz_type: params.type,
    strategies: [0.82, 0.85, 0.88, 0.9, 0.92, 0.95],
  });
  if (!r.ok) {
    // P30-R4 P1-21: r.ok 분기 — backend 통신 오류 사용자 인지 (PredictResult와 일관)
    return (
      <Card className="border-[var(--color-danger)]">
        <CardContent className="p-4 text-sm">
          시나리오 비교 오류: {r.error || "backend 통신 실패"}
        </CardContent>
      </Card>
    );
  }
  const data = extractMcpData<any>(r.data);
  const scenarios = data?.scenarios || [];

  if (scenarios.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>시나리오별 낙찰 확률 비교 (n={data.agency_sample_count})</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="bg-[var(--color-bg-muted)]">
            <tr>
              <th className="px-3 py-2 text-left">응찰률</th>
              <th className="px-3 py-2 text-right">응찰가</th>
              <th className="px-3 py-2 text-right">예상 낙찰확률</th>
              <th className="px-3 py-2 text-left">막대</th>
            </tr>
          </thead>
          <tbody>
            {scenarios.map((s: any, i: number) => (
              <tr key={i} className="border-t">
                <td className="px-3 py-2 tabular-nums">{s.bid_rate_pct}%</td>
                <td className="px-3 py-2 text-right tabular-nums">{fmtWon(s.bid_amount)}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {(s.estimated_win_prob * 100).toFixed(0)}%
                </td>
                <td className="px-3 py-2">
                  <div
                    className="h-2 rounded bg-[var(--color-primary)]"
                    style={{ width: `${s.estimated_win_prob * 100}%` }}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}

function Stat({
  label,
  v,
  highlight,
}: {
  label: string;
  v: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-md border p-3 ${
        highlight ? "border-[var(--color-primary)] bg-[var(--color-bg)]" : ""
      }`}
    >
      <div className="text-xs text-[var(--color-fg-muted)]">{label}</div>
      <div className="mt-1 font-mono text-lg font-medium tabular-nums">{v}</div>
    </div>
  );
}

function Skel({ h }: { h: number }) {
  return (
    <div
      className="animate-pulse rounded bg-[var(--color-bg-muted)]"
      style={{ height: `${h * 4}px` }}
    />
  );
}
