"use client";

import { AreaChart } from "@tremor/react";

interface AwardItem {
  open_date?: string;
  award_amount?: number;
}

/**
 * 업체 프로필 — 월별 낙찰 추이.
 */
export function VendorAwardChart({ items }: { items: AwardItem[] }) {
  if (items.length === 0) return null;

  // 월별 집계
  const byMonth: Record<string, { count: number; total: number }> = {};
  for (const it of items) {
    const d = (it.open_date || "").slice(0, 6);
    if (d.length !== 6) continue;
    if (!byMonth[d]) byMonth[d] = { count: 0, total: 0 };
    byMonth[d].count += 1;
    byMonth[d].total += it.award_amount || 0;
  }

  const data = Object.entries(byMonth)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([yyyymm, v]) => ({
      yyyymm,
      "낙찰 건수": v.count,
      "합계 (억)": Math.round(v.total / 100_000_000),
    }));

  if (data.length === 0) return null;

  return (
    <AreaChart
      data={data}
      index="yyyymm"
      categories={["낙찰 건수", "합계 (억)"]}
      colors={["blue", "emerald"]}
      yAxisWidth={48}
      className="h-48"
    />
  );
}
