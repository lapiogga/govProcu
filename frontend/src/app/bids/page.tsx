/**
 * 입찰 검색 — `search_bid_notices`
 */
import { Suspense } from "react";
import { searchBidNotices } from "@/lib/actions";
import { fmtWon, fmtDate } from "@/lib/format";

export default async function BidsPage(props: {
  searchParams: Promise<{
    q?: string;
    type?: string;
    inst?: string;
    from?: string;
    to?: string;
  }>;
}) {
  const sp = await props.searchParams;
  const hasQuery = !!(sp.q || sp.type || sp.inst || sp.from || sp.to);

  return (
    <main className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold">입찰 검색</h1>
      </header>

      <form action="/bids" className="grid grid-cols-1 gap-2 rounded border bg-[var(--color-bg-muted)] p-4 md:grid-cols-5">
        <input
          name="q"
          defaultValue={sp.q}
          placeholder="키워드 (예: 정보화)"
          className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm md:col-span-2"
        />
        <select
          name="type"
          defaultValue={sp.type}
          className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
        >
          <option value="">업종 전체</option>
          <option value="공사">공사</option>
          <option value="용역">용역</option>
          <option value="물품">물품</option>
        </select>
        <input
          name="inst"
          defaultValue={sp.inst}
          placeholder="발주기관"
          className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
        />
        <button
          type="submit"
          className="rounded bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-[var(--color-primary-fg)]"
        >
          검색
        </button>
        <input
          name="from"
          defaultValue={sp.from}
          placeholder="YYYYMMDD"
          className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
        />
        <input
          name="to"
          defaultValue={sp.to}
          placeholder="YYYYMMDD"
          className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
        />
      </form>

      {hasQuery ? (
        <Suspense fallback={<TableSkeleton />}>
          <Results
            keyword={sp.q}
            biz_type={sp.type}
            inst_name={sp.inst}
            date_from={sp.from}
            date_to={sp.to}
          />
        </Suspense>
      ) : (
        <p className="text-sm text-[var(--color-fg-muted)]">
          검색 조건을 입력하세요. 예: 키워드 + 업종 + 기간.
        </p>
      )}
    </main>
  );
}

async function Results(params: {
  keyword?: string;
  biz_type?: string;
  inst_name?: string;
  date_from?: string;
  date_to?: string;
}) {
  const result = await searchBidNotices(params);
  if (!result.ok) {
    return (
      <div className="rounded border border-[var(--color-danger)] p-4 text-sm">
        오류: {result.error}
      </div>
    );
  }
  const data = extractData(result.data);
  const items = data?.items || [];

  if (items.length === 0) {
    return (
      <p className="rounded border p-4 text-sm">
        결과 없음 ({data?.total_count ?? 0}건)
      </p>
    );
  }

  return (
    <section className="rounded-lg border">
      <div className="border-b bg-[var(--color-bg-muted)] px-4 py-2 text-sm">
        총 {data?.total_count ?? items.length}건 (반환 {items.length})
      </div>
      <table className="w-full text-sm">
        <thead className="bg-[var(--color-bg-muted)]">
          <tr>
            <th className="px-3 py-2 text-left">공고일</th>
            <th className="px-3 py-2 text-left">공고제목</th>
            <th className="px-3 py-2 text-left">발주기관</th>
            <th className="px-3 py-2 text-left">업종</th>
            <th className="px-3 py-2 text-right">추정가</th>
            <th className="px-3 py-2 text-right">마감일</th>
          </tr>
        </thead>
        <tbody>
          {items.map((bid: any) => (
            <tr key={`${bid.bid_no}-${bid.bid_ord}`} className="border-t hover:bg-[var(--color-bg-muted)]">
              <td className="px-3 py-2 tabular-nums">
                {fmtDate(bid.publish_date)}
              </td>
              <td className="px-3 py-2">
                <a
                  href={`/bids/trace?no=${bid.bid_no}&ord=${bid.bid_ord || "00"}`}
                  className="text-[var(--color-primary)] hover:underline"
                >
                  {bid.title}
                </a>
              </td>
              <td className="px-3 py-2">{bid.inst_name || "—"}</td>
              <td className="px-3 py-2">{bid.biz_type || "—"}</td>
              <td className="px-3 py-2 text-right tabular-nums">
                {fmtWon(bid.estimated_price)}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">
                {fmtDate(bid.deadline_date)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {[1, 2, 3, 4, 5].map((n) => (
        <div key={n} className="h-10 animate-pulse rounded bg-[var(--color-bg-muted)]" />
      ))}
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
