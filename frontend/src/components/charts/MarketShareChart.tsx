"use client";

import { DonutChart } from "@tremor/react";

interface TopVendor {
  biz_no: string;
  name: string;
  award_total: number;
  market_share_pct: number;
}

export function MarketShareChart({ top }: { top: TopVendor[] }) {
  if (top.length === 0) return null;

  // Top 5 + 기타
  const top5 = top.slice(0, 5);
  const otherShare = top.slice(5).reduce((s, v) => s + v.market_share_pct, 0);

  const data = [
    ...top5.map((v) => ({
      name: v.name?.slice(0, 12) || v.biz_no,
      share: v.market_share_pct,
    })),
    ...(otherShare > 0
      ? [{ name: "기타", share: Math.round(otherShare * 100) / 100 }]
      : []),
  ];

  return (
    <DonutChart
      data={data}
      category="share"
      index="name"
      valueFormatter={(v: number) => `${v.toFixed(2)}%`}
      colors={["blue", "cyan", "indigo", "violet", "fuchsia", "slate"]}
      className="h-64"
    />
  );
}
