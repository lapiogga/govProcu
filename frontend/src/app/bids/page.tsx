/**
 * 입찰 검색 — `search_bid_notices`
 */
import { Suspense } from "react";
import { searchBidNotices } from "@/lib/actions";
import { fmtWon, fmtDate } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { BidLink, AgencyLink } from "@/components/EntityLink";
import { SortMenu, type SortKey } from "./sort-menu";

const VALID_SORTS: SortKey[] = [
  "publish_desc",
  "publish_asc",
  "deadline",
  "amount_desc",
  "amount_asc",
];

function parseSort(raw: string | undefined): SortKey {
  if (raw && (VALID_SORTS as string[]).includes(raw)) return raw as SortKey;
  return "publish_desc";
}

function sortItems(items: Bid[], key: SortKey): Bid[] {
  const out = [...items];
  switch (key) {
    case "publish_asc":
      return out.sort((a, b) =>
        (a.publish_date || "").localeCompare(b.publish_date || ""),
      );
    case "deadline":
      return out.sort((a, b) =>
        (a.deadline_date || "9999").localeCompare(b.deadline_date || "9999"),
      );
    case "amount_desc":
      return out.sort(
        (a, b) => (b.estimated_price ?? 0) - (a.estimated_price ?? 0),
      );
    case "amount_asc":
      return out.sort(
        (a, b) => (a.estimated_price ?? 0) - (b.estimated_price ?? 0),
      );
    default:
      return out.sort((a, b) =>
        (b.publish_date || "").localeCompare(a.publish_date || ""),
      );
  }
}

interface Bid {
  bid_no: string;
  bid_ord?: string;
  title?: string;
  inst_name?: string;
  biz_type?: string;
  estimated_price?: number;
  publish_date?: string;
  deadline_date?: string;
}

export default async function BidsPage(props: {
  searchParams: Promise<{
    q?: string;
    type?: string;
    inst?: string;
    from?: string;
    to?: string;
    sort?: string;
    page?: string;
  }>;
}) {
  const sp = await props.searchParams;
  const hasQuery = !!(sp.q || sp.type || sp.inst || sp.from || sp.to);
  const sortKey = parseSort(sp.sort);
  const page = Math.max(1, parseInt(sp.page || "1", 10) || 1);

  return (
    <main className="space-y-4">
      <header className="flex items-start justify-between">
        <h1 className="text-2xl font-semibold">입찰 검색</h1>
        {hasQuery && <SortMenu current={sortKey} />}
      </header>

      <Card>
        <CardContent className="p-4">
          <form action="/bids" className="grid grid-cols-1 gap-2 md:grid-cols-5">
            <Input
              name="q"
              defaultValue={sp.q}
              placeholder="키워드 (예: 정보화)"
              className="md:col-span-2"
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
            <Input name="inst" defaultValue={sp.inst} placeholder="발주기관" />
            <Button type="submit">검색</Button>
            <Input name="from" defaultValue={sp.from} placeholder="YYYYMMDD" />
            <Input name="to" defaultValue={sp.to} placeholder="YYYYMMDD" />
            <input type="hidden" name="sort" value={sortKey} />
            <input type="hidden" name="page" value="1" />
          </form>
        </CardContent>
      </Card>

      {hasQuery ? (
        <Suspense fallback={<TableSkeleton />}>
          <Results
            keyword={sp.q}
            biz_type={sp.type}
            inst_name={sp.inst}
            date_from={sp.from}
            date_to={sp.to}
            sort={sortKey}
            page={page}
            sp={sp}
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
  sort: SortKey;
  page: number;
  sp: Record<string, string | undefined>;
}) {
  const { sort, page, sp, ...searchParams } = params;
  const result = await searchBidNotices({ ...searchParams, page });
  if (!result.ok) {
    return (
      <div className="rounded border border-[var(--color-danger)] p-4 text-sm">
        오류: {result.error}
      </div>
    );
  }
  const data = extractData(result.data);
  const rawItems: Bid[] = data?.items || [];
  const items = sortItems(rawItems, sort);
  const totalCount = data?.total_count ?? 0;
  const hasMore = !!data?.has_more;
  const buildHref = (newPage: number) => {
    const qs = new URLSearchParams();
    if (sp.q) qs.set("q", sp.q);
    if (sp.type) qs.set("type", sp.type);
    if (sp.inst) qs.set("inst", sp.inst);
    if (sp.from) qs.set("from", sp.from);
    if (sp.to) qs.set("to", sp.to);
    if (sort) qs.set("sort", sort);
    qs.set("page", String(newPage));
    return `/bids?${qs.toString()}`;
  };

  if (items.length === 0) {
    return (
      <div className="space-y-2">
        <p className="rounded border p-4 text-sm">
          결과 없음 ({totalCount}건). 페이지 {page}.
          {hasMore && " 다음 페이지를 시도하세요."}
        </p>
        {(page > 1 || hasMore) && (
          <PageNav
            page={page}
            hasMore={hasMore}
            buildHref={buildHref}
            totalCount={totalCount}
          />
        )}
      </div>
    );
  }

  return (
    <section className="rounded-lg border">
      <div className="flex items-center justify-between border-b bg-[var(--color-bg-muted)] px-4 py-2 text-sm">
        <span>
          총 {totalCount}건 (반환 {items.length}, 페이지 {page})
        </span>
        <PageNav
          page={page}
          hasMore={hasMore}
          buildHref={buildHref}
          totalCount={totalCount}
          inline
        />
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
          {items.map((bid: Bid) => (
            <tr key={`${bid.bid_no}-${bid.bid_ord}`} className="border-t hover:bg-[var(--color-bg-muted)]">
              <td className="px-3 py-2 tabular-nums">
                {fmtDate(bid.publish_date)}
              </td>
              <td className="px-3 py-2">
                <BidLink
                  bidNo={bid.bid_no}
                  ord={bid.bid_ord}
                  title={bid.title}
                />
              </td>
              <td className="px-3 py-2">
                <AgencyLink name={bid.inst_name} />
              </td>
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

function PageNav({
  page,
  hasMore,
  buildHref,
  totalCount,
  inline = false,
}: {
  page: number;
  hasMore: boolean;
  buildHref: (newPage: number) => string;
  totalCount: number;
  inline?: boolean;
}) {
  // 단일 페이지 = 999건 (max_scan_pages=1, page_size=999)
  const pageSize = 999;
  const lastPage = Math.max(1, Math.ceil(totalCount / pageSize));

  return (
    <nav className={inline ? "flex items-center gap-2 text-xs" : "flex items-center justify-end gap-2 text-xs"}>
      {page > 1 && (
        <a
          href={buildHref(page - 1)}
          className="rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-bg)]"
        >
          ← 이전
        </a>
      )}
      <span className="text-[var(--color-fg-muted)]">
        {page} / {lastPage}
      </span>
      {hasMore && (
        <a
          href={buildHref(page + 1)}
          className="rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-bg)]"
        >
          다음 →
        </a>
      )}
    </nav>
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
