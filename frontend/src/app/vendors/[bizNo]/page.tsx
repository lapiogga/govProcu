/**
 * 업체 프로필 — `vendor_profile` (W2)
 * NTS 진위 + 기간 내 입찰/응찰/개찰/낙찰 통계.
 */
import { Suspense } from "react";
import { getVendorProfile } from "@/lib/actions";
import { fmtWon, fmtRate, fmtBizNo, fmtDate } from "@/lib/format";
import { VendorAwardChart } from "@/components/charts/VendorAwardChart";

export default async function VendorPage(props: {
  params: Promise<{ bizNo: string }>;
  searchParams: Promise<{ from?: string; to?: string }>;
}) {
  const { bizNo } = await props.params;
  const sp = await props.searchParams;
  const from = sp.from;
  const to = sp.to;

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">
          업체 프로필: {fmtBizNo(bizNo)}
        </h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          NTS 진위 + 입찰/응찰/개찰/낙찰 통합 (vendor_profile)
        </p>
      </header>

      <Suspense fallback={<ProfileSkeleton />}>
        <Profile bizNo={bizNo} from={from} to={to} />
      </Suspense>
    </main>
  );
}

async function Profile({
  bizNo,
  from,
  to,
}: {
  bizNo: string;
  from?: string;
  to?: string;
}) {
  const result = await getVendorProfile(bizNo, from, to);

  if (!result.ok) {
    return (
      <div className="rounded border border-[var(--color-danger)] p-4 text-sm">
        오류: {result.error}
      </div>
    );
  }

  const data = extractData(result.data);
  if (!data) {
    return <div className="rounded border p-4 text-sm">응답 없음</div>;
  }

  const summary = data.summary || {};
  const sections = data.sections || {};

  return (
    <div className="space-y-4">
      {/* NTS 검증 */}
      <section className="rounded-lg border bg-[var(--color-bg-muted)] p-4">
        <h2 className="mb-2 text-sm font-medium">NTS 검증</h2>
        <p className="text-sm">
          상태 코드: <span className="font-mono">{summary.nts_status_code || "—"}</span>{" "}
          {summary.nts_status_code === "01" && (
            <span className="text-[var(--color-success)]">✅ 계속사업자</span>
          )}
        </p>
      </section>

      {/* 통계 */}
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Stat label="입찰" value={summary.bids_count} />
        <Stat label="응찰" value={summary.participations_count} />
        <Stat label="개찰참여" value={summary.openings_count} />
        <Stat label="낙찰" value={summary.awards_count} />
        <Stat
          label="낙찰합계"
          value={fmtWon(summary.awards_total_won)}
          tabular
        />
      </section>

      {summary.win_rate_pct != null && (
        <section className="rounded-lg border p-4">
          <p className="text-sm">
            낙찰률:{" "}
            <span className="font-mono text-lg font-medium">
              {summary.win_rate_pct.toFixed(2)}%
            </span>
            {" · "}
            평균 낙찰가: {fmtWon(summary.awards_avg_won)}
          </p>
        </section>
      )}

      {/* 월별 낙찰 추이 */}
      {sections.awards?.items?.length > 0 && (
        <section className="rounded-lg border p-4">
          <h3 className="mb-3 text-sm font-medium">월별 낙찰 추이</h3>
          <VendorAwardChart items={sections.awards.items} />
        </section>
      )}

      {/* 최근 낙찰 5건 */}
      {sections.awards?.items?.length > 0 && (
        <section className="rounded-lg border">
          <h3 className="border-b px-4 py-2 text-sm font-medium">
            최근 낙찰 {sections.awards.items.length}건
          </h3>
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-bg-muted)]">
              <tr>
                <th className="px-3 py-2 text-left">개찰일</th>
                <th className="px-3 py-2 text-left">공고제목</th>
                <th className="px-3 py-2 text-left">발주기관</th>
                <th className="px-3 py-2 text-right">낙찰가</th>
                <th className="px-3 py-2 text-right">낙찰률</th>
              </tr>
            </thead>
            <tbody>
              {sections.awards.items.slice(0, 10).map((a: any, i: number) => (
                <tr key={i} className="border-t">
                  <td className="px-3 py-2 tabular-nums">
                    {fmtDate(a.open_date)}
                  </td>
                  <td className="px-3 py-2">
                    {a.bid_notice_no ? (
                      <a
                        href={`/bids/trace?no=${a.bid_notice_no}&ord=${a.bid_ord || "00"}`}
                        className="text-[var(--color-primary)] hover:underline"
                      >
                        {a.bid_title || a.bid_notice_no}
                      </a>
                    ) : (
                      a.bid_title || "—"
                    )}
                  </td>
                  <td className="px-3 py-2">{a.inst_name || "—"}</td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {fmtWon(a.award_amount)}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {fmtRate(a.award_rate)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section className="text-xs text-[var(--color-fg-muted)]">
        구현 상태: {summary.implementation_status || "—"}
      </section>
    </div>
  );
}

function Stat({
  label,
  value,
  tabular,
}: {
  label: string;
  value: number | string | undefined;
  tabular?: boolean;
}) {
  return (
    <div className="rounded border p-3">
      <div className="text-xs text-[var(--color-fg-muted)]">{label}</div>
      <div className={`mt-1 text-lg font-medium ${tabular ? "tabular-nums" : ""}`}>
        {value ?? "—"}
      </div>
    </div>
  );
}

function ProfileSkeleton() {
  return (
    <div className="space-y-3">
      <div className="h-20 animate-pulse rounded bg-[var(--color-bg-muted)]" />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        {[1, 2, 3, 4, 5].map((n) => (
          <div
            key={n}
            className="h-16 animate-pulse rounded bg-[var(--color-bg-muted)]"
          />
        ))}
      </div>
    </div>
  );
}

function extractData(raw: unknown): any {
  if (!raw) return null;
  if (typeof raw === "object" && raw !== null) {
    const obj = raw as Record<string, unknown>;
    if (obj.content && Array.isArray(obj.content)) {
      const text = (obj.content[0] as { text?: string })?.text;
      if (text) {
        try {
          return JSON.parse(text);
        } catch {
          return null;
        }
      }
    }
    return obj;
  }
  return null;
}
