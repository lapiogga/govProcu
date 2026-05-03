/**
 * 분석/통계 — industry_trend + market_share
 */
import { Suspense } from "react";
import { getIndustryTrend, getMarketShare } from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";
import { fmtWon } from "@/lib/format";
import { IndustryTrendChart } from "@/components/charts/IndustryTrendChart";
import { MarketShareChart } from "@/components/charts/MarketShareChart";
import { VendorLink } from "@/components/EntityLink";

function todayYYYYMMDD(): string {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
}

function defaultAnalyticsFrom(): string {
  // P30-R4 P1-11: from/to 미입력 시 365일 default.
  // 사유: backend industry_trend / market_share 가 무기간 호출되면 G2B inqryBgnDt 누락 →
  // chunk_date_range fallback이 today 1개월만 처리 → 0건/rate_limit 위험.
  // 1년 default로 의미 있는 시계열 + 시장 점유 산출.
  const d = new Date();
  d.setDate(d.getDate() - 365);
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
}

export default async function AnalyticsPage(props: {
  searchParams: Promise<{ type?: string; from?: string; to?: string }>;
}) {
  const sp = await props.searchParams;
  const bizType = sp.type || "용역";
  const dateFrom = sp.from || defaultAnalyticsFrom();
  const dateTo = sp.to || todayYYYYMMDD();

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">분석/통계</h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          업종 동향 + 시장 점유 + 기간 설정
        </p>
      </header>

      <form action="/analytics" className="flex gap-2 rounded border bg-[var(--color-bg-muted)] p-4">
        <select
          name="type"
          defaultValue={bizType}
          className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
        >
          <option value="공사">공사</option>
          <option value="용역">용역</option>
          <option value="물품">물품</option>
        </select>
        <input
          name="from"
          defaultValue={sp.from}
          placeholder="YYYYMMDD (시작)"
          className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
        />
        <input
          name="to"
          defaultValue={sp.to}
          placeholder="YYYYMMDD (종료)"
          className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
        />
        <button
          type="submit"
          className="rounded bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-[var(--color-primary-fg)]"
        >
          분석
        </button>
      </form>

      <Suspense fallback={<Skel h={20} />}>
        <TrendSection bizType={bizType} from={dateFrom} to={dateTo} />
      </Suspense>

      <Suspense fallback={<Skel h={32} />}>
        <MarketShareSection bizType={bizType} from={dateFrom} to={dateTo} />
      </Suspense>
    </main>
  );
}

async function TrendSection({
  bizType,
  from,
  to,
}: {
  bizType: string;
  from?: string;
  to?: string;
}) {
  // Cache 전략은 NEXT7-SEC-1 후 보류 (CACHE-STRATEGY.md §2)
  const r = await getIndustryTrend(bizType, undefined, from, to);
  if (!r.ok) {
    // P30-R4 P1-20: r.ok 분기 — backend 통신 오류 사용자 인지 (silent "데이터 없음"과 구분)
    return (
      <div className="rounded border border-[var(--color-danger,#dc2626)] bg-[var(--color-danger-bg,#fee2e2)] p-3 text-sm">
        <strong>업종 동향 조회 오류</strong> — {r.error || "backend 통신 실패"}
      </div>
    );
  }
  const data = extractMcpData<any>(r.data);
  const monthly = data?.monthly || [];

  return (
    <section className="rounded-lg border">
      <header className="border-b px-4 py-2 text-sm">
        <span className="font-medium">{bizType} 월별 동향</span>
        <span className="ml-3 text-[var(--color-fg-muted)]">
          누적 {data?.total_count} 건 · {fmtWon(data?.total_amt)}
        </span>
      </header>

      {/* Tremor 차트 */}
      <div className="border-b p-4">
        <IndustryTrendChart monthly={monthly} />
      </div>

      <table className="w-full text-sm">
        <thead className="bg-[var(--color-bg-muted)]">
          <tr>
            <th className="px-3 py-2 text-left">YYYYMM</th>
            <th className="px-3 py-2 text-right">건수</th>
            <th className="px-3 py-2 text-right">합계 금액</th>
            <th className="px-3 py-2 text-right">평균 금액</th>
            <th className="px-3 py-2 text-left">막대 (상대)</th>
          </tr>
        </thead>
        <tbody>
          {monthly.map((m: any) => {
            const max = Math.max(...monthly.map((x: any) => x.total_amt || 0), 1);
            const pct = ((m.total_amt || 0) / max) * 100;
            return (
              <tr key={m.yyyymm} className="border-t">
                <td className="px-3 py-2 tabular-nums">{m.yyyymm}</td>
                <td className="px-3 py-2 text-right tabular-nums">{m.count}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {fmtWon(m.total_amt)}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {fmtWon(m.avg_amt)}
                </td>
                <td className="px-3 py-2">
                  <div
                    className="h-2 rounded bg-[var(--color-primary)]"
                    style={{ width: `${pct}%` }}
                  />
                </td>
              </tr>
            );
          })}
          {monthly.length === 0 && (
            <tr>
              <td colSpan={5} className="px-3 py-4 text-center text-[var(--color-fg-muted)]">
                데이터 없음
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}

async function MarketShareSection({
  bizType,
  from,
  to,
}: {
  bizType: string;
  from?: string;
  to?: string;
}) {
  const r = await getMarketShare(bizType, from, to, 20);
  if (!r.ok) {
    // P30-R4 P1-20: r.ok 분기 — backend 통신 오류 사용자 인지 (silent "데이터 없음"과 구분)
    return (
      <div className="rounded border border-[var(--color-danger,#dc2626)] bg-[var(--color-danger-bg,#fee2e2)] p-3 text-sm">
        <strong>시장 점유 조회 오류</strong> — {r.error || "backend 통신 실패"}
      </div>
    );
  }
  const data = extractMcpData<any>(r.data);
  const top = data?.top_vendors || [];
  const grandTotal = data?.grand_total_won || 0;

  return (
    <section className="rounded-lg border">
      <header className="border-b px-4 py-2 text-sm">
        <span className="font-medium">{bizType} 시장 점유 Top 20</span>
        <span className="ml-3 text-[var(--color-fg-muted)]">
          전체 {fmtWon(grandTotal)} · 활동 업체 {data?.vendor_count_total ?? "—"}
        </span>
      </header>

      {/* Tremor Donut */}
      {top.length > 0 && (
        <div className="border-b p-4">
          <MarketShareChart top={top} />
        </div>
      )}

      <table className="w-full text-sm">
        <thead className="bg-[var(--color-bg-muted)]">
          <tr>
            <th className="px-3 py-2 text-left">순위</th>
            <th className="px-3 py-2 text-left">업체명</th>
            <th className="px-3 py-2 text-left">사업자번호</th>
            <th className="px-3 py-2 text-right">낙찰합계</th>
            <th className="px-3 py-2 text-right">건수</th>
            <th className="px-3 py-2 text-right">점유율</th>
          </tr>
        </thead>
        <tbody>
          {top.map((v: any, i: number) => (
            <tr key={v.biz_no} className="border-t hover:bg-[var(--color-bg-muted)]">
              <td className="px-3 py-2 tabular-nums">{i + 1}</td>
              <td className="px-3 py-2">
                <VendorLink bizNo={v.biz_no} name={v.name} />
              </td>
              <td className="px-3 py-2 tabular-nums">
                <VendorLink bizNo={v.biz_no} formatBizNo />
              </td>
              <td className="px-3 py-2 text-right tabular-nums">
                {fmtWon(v.award_total)}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">
                {v.award_count}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">
                {v.market_share_pct?.toFixed(2)}%
              </td>
            </tr>
          ))}
          {top.length === 0 && (
            <tr>
              <td colSpan={6} className="px-3 py-4 text-center text-[var(--color-fg-muted)]">
                데이터 없음
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
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
