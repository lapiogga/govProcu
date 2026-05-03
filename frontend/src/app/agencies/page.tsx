/**
 * 발주기관 분석 — agency_procurement_history + analyze_agency_price_pattern
 */
import { Suspense } from "react";
import { getAgencyHistory, getAgencyPricePattern } from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";
import { fmtWon, fmtRate, fmtDate } from "@/lib/format";
import { AgencyPricePatternChart } from "@/components/charts/AgencyPricePatternChart";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { VendorLink, BidLink } from "@/components/EntityLink";

function todayYYYYMMDD(): string {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
}

function defaultAgencyFrom(): string {
  // 5/3 N42 v10.2: 측정 1.7초 vs 실 사용 60초 차이로 1년 default 재검토.
  // 6개월(180일) default — chunks 6 × 4 endpoints = ~30초 (수용 가능).
  // 사용자 spot-check 후 더 좁힐 수 있음.
  const d = new Date();
  d.setDate(d.getDate() - 180);
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
}

export default async function AgenciesPage(props: {
  searchParams: Promise<{
    name?: string;
    type?: string;
    from?: string;
    to?: string;
  }>;
}) {
  const sp = await props.searchParams;
  const dateFrom = sp.from || (sp.name ? defaultAgencyFrom() : undefined);
  const dateTo = sp.to || (sp.name ? todayYYYYMMDD() : undefined);

  // 5/3 N42 v12: 큰 범위(>1년) 입력 시 timeout 위험 명시
  const rangeDays = (() => {
    if (!dateFrom || !dateTo) return 0;
    try {
      const f = new Date(`${dateFrom.slice(0, 4)}-${dateFrom.slice(4, 6)}-${dateFrom.slice(6, 8)}`);
      const t = new Date(`${dateTo.slice(0, 4)}-${dateTo.slice(4, 6)}-${dateTo.slice(6, 8)}`);
      return Math.round((t.getTime() - f.getTime()) / (1000 * 60 * 60 * 24));
    } catch {
      return 0;
    }
  })();
  const isLargeRange = rangeDays > 365;
  const estimatedSec = Math.max(5, Math.round((rangeDays / 31) * 5)); // chunk당 ~5초
  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">발주기관 분석</h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          기관별 발주 이력 + 낙찰업체 + 사정률 패턴
        </p>
      </header>

      <Card>
        <CardContent className="p-4">
          <form action="/agencies" className="flex flex-wrap gap-2">
            <Input
              name="name"
              defaultValue={sp.name}
              placeholder="발주기관명 (예: 국방재정관리단)"
              className="flex-1"
              required
            />
            <select
              name="type"
              defaultValue={sp.type}
              className="rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-1 text-sm"
            >
              <option value="">업종 전체</option>
              <option value="공사">공사</option>
              <option value="용역">용역</option>
              <option value="물품">물품</option>
            </select>
            <Input name="from" defaultValue={sp.from} placeholder="YYYYMMDD" className="w-32" />
            <Input name="to" defaultValue={sp.to} placeholder="YYYYMMDD" className="w-32" />
            <Button type="submit">분석</Button>
          </form>
        </CardContent>
      </Card>

      {sp.name ? (
        <>
          {isLargeRange && (
            <div className="rounded border border-[var(--color-warning,#f59e0b)] bg-[var(--color-warning-bg,#fef3c7)] p-3 text-sm">
              <strong>⚠ 큰 범위 입력 ({Math.round(rangeDays / 365 * 10) / 10}년)</strong>
              {" "}— 응답 약 {estimatedSec}초 예상 (1개월 청크 {Math.ceil(rangeDays / 31)}회 × 4 endpoint).
              빠른 분석은 from/to 단축 권장.
            </div>
          )}
          <Suspense fallback={<Skel h={32} />}>
            <PriceCard
              instName={sp.name}
              bizType={sp.type}
              from={dateFrom}
              to={dateTo}
            />
          </Suspense>
          <Suspense fallback={<Skel h={48} />}>
            <HistoryTable
              instName={sp.name}
              bizType={sp.type}
              from={dateFrom}
              to={dateTo}
            />
          </Suspense>
        </>
      ) : (
        <p className="text-sm text-[var(--color-fg-muted)]">
          기관명을 입력하여 분석을 시작하세요.
        </p>
      )}
    </main>
  );
}

async function PriceCard({
  instName,
  bizType,
  from,
  to,
}: {
  instName: string;
  bizType?: string;
  from?: string;
  to?: string;
}) {
  const r = await getAgencyPricePattern(instName, bizType, from, to);
  const data = extractMcpData<any>(r.data);
  if (!data) return null;
  if (!data.sample_count) {
    return (
      <div className="rounded border p-4 text-sm">
        사정률 패턴: 데이터 없음 ({data.note || "기간 확장 권장"})
      </div>
    );
  }
  const s = data.summary_pct || {};
  return (
    <section className="rounded-lg border bg-[var(--color-bg-muted)] p-4">
      <h2 className="text-sm font-medium">
        사정률 패턴 (n={data.sample_count})
      </h2>
      <p className="mt-1 text-xs text-[var(--color-fg-muted)]">
        {data.interpretation}
      </p>
      <div className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Stat label="평균" v={`${s.mean?.toFixed(2)}%`} />
        <Stat label="중앙값" v={`${s.median?.toFixed(2)}%`} />
        <Stat label="p10" v={`${s.p10?.toFixed(2)}%`} />
        <Stat label="p25" v={`${s.p25?.toFixed(2)}%`} />
        <Stat label="p90" v={`${s.p90?.toFixed(2)}%`} />
      </div>

      <div className="mt-4 rounded border bg-[var(--color-bg)] p-3">
        <AgencyPricePatternChart pattern={s} />
      </div>
    </section>
  );
}

async function HistoryTable({
  instName,
  bizType,
  from,
  to,
}: {
  instName: string;
  bizType?: string;
  from?: string;
  to?: string;
}) {
  const r = await getAgencyHistory(instName, from, to, bizType);
  const data = extractMcpData<any>(r.data);
  if (!data) return null;
  const items = data.items || [];
  const summary = data.summary || {};

  return (
    <section className="rounded-lg border">
      <header className="border-b px-4 py-2 text-sm">
        <span className="font-medium">발주 이력 + 낙찰업체</span>
        <span className="ml-3 text-[var(--color-fg-muted)]">
          공고 {summary.notice_count} · 낙찰 매칭 {summary.award_matched_count} (
          {summary.award_match_rate_pct}%) · 합계 {fmtWon(summary.award_total_won)}
        </span>
      </header>
      <table className="w-full text-sm">
        <thead className="bg-[var(--color-bg-muted)]">
          <tr>
            <th className="px-3 py-2 text-left">공고일</th>
            <th className="px-3 py-2 text-left">제목</th>
            <th className="px-3 py-2 text-left">업종</th>
            <th className="px-3 py-2 text-right">추정가</th>
            <th className="px-3 py-2 text-left">낙찰업체</th>
            <th className="px-3 py-2 text-right">낙찰가</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it: any, i: number) => (
            <tr key={i} className="border-t hover:bg-[var(--color-bg-muted)]">
              <td className="px-3 py-2 tabular-nums">
                {fmtDate(it.publish_date)}
              </td>
              <td className="px-3 py-2">
                <BidLink
                  bidNo={it.bid_notice_no}
                  ord={it.bid_ord}
                  title={it.title}
                />
              </td>
              <td className="px-3 py-2">{it.biz_type || "—"}</td>
              <td className="px-3 py-2 text-right tabular-nums">
                {fmtWon(it.estimated_price)}
              </td>
              <td className="px-3 py-2">
                {it.winner ? (
                  <VendorLink
                    bizNo={it.winner.winner_biz_no}
                    name={it.winner.winner_name}
                  />
                ) : (
                  <span className="text-[var(--color-fg-muted)]">—</span>
                )}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">
                {it.winner ? fmtWon(it.winner.award_amount) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function Stat({ label, v }: { label: string; v: string }) {
  return (
    <div className="rounded border bg-[var(--color-bg)] p-2">
      <div className="text-xs text-[var(--color-fg-muted)]">{label}</div>
      <div className="font-mono text-sm font-medium tabular-nums">{v}</div>
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
