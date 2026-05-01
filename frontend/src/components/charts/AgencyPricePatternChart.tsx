"use client";

import { BarChart } from "@tremor/react";

interface PricePattern {
  mean?: number;
  median?: number;
  p10?: number;
  p25?: number;
  p75?: number;
  p90?: number;
}

/**
 * 발주기관 사정률 분위수 시각화.
 */
export function AgencyPricePatternChart({ pattern }: { pattern: PricePattern }) {
  const data = [
    { quantile: "p10", "낙찰률 (%)": pattern.p10 ?? 0 },
    { quantile: "p25", "낙찰률 (%)": pattern.p25 ?? 0 },
    { quantile: "median", "낙찰률 (%)": pattern.median ?? 0 },
    { quantile: "p75", "낙찰률 (%)": pattern.p75 ?? 0 },
    { quantile: "p90", "낙찰률 (%)": pattern.p90 ?? 0 },
  ];

  return (
    <BarChart
      data={data}
      index="quantile"
      categories={["낙찰률 (%)"]}
      colors={["indigo"]}
      yAxisWidth={48}
      showLegend={false}
      className="h-48"
      valueFormatter={(v: number) => `${v.toFixed(2)}%`}
    />
  );
}
