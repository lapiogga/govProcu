"use client";

import { BarChart } from "@tremor/react";

interface MonthlyData {
  yyyymm: string;
  count: number;
  total_amt: number;
  avg_amt: number;
}

export function IndustryTrendChart({ monthly }: { monthly: MonthlyData[] }) {
  if (monthly.length === 0) {
    return (
      <p className="rounded border p-4 text-sm text-[var(--color-fg-muted)]">
        데이터 없음
      </p>
    );
  }

  const data = monthly.map((m) => ({
    yyyymm: m.yyyymm,
    "낙찰 건수": m.count,
    "합계 (억원)": Math.round((m.total_amt || 0) / 100_000_000),
  }));

  return (
    <div className="space-y-4">
      <BarChart
        data={data}
        index="yyyymm"
        categories={["낙찰 건수"]}
        colors={["blue"]}
        yAxisWidth={48}
        showLegend={false}
        className="h-48"
      />
      <BarChart
        data={data}
        index="yyyymm"
        categories={["합계 (억원)"]}
        colors={["emerald"]}
        yAxisWidth={48}
        showLegend={false}
        className="h-48"
      />
    </div>
  );
}
