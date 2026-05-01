/**
 * 내 즐겨찾기 + 알림 구독
 */
import { Suspense } from "react";
import { listMyWatchlist, listMySubscriptions } from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";
import {
  removeWatchlistAction,
  unsubscribeAction,
  subscribeKeywordAction,
} from "./actions";

export default async function MePage() {
  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">내 활동</h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          즐겨찾기 + 키워드 알림 구독 (P0)
        </p>
      </header>

      <Suspense fallback={<Skel h={32} />}>
        <Watchlist />
      </Suspense>

      <Suspense fallback={<Skel h={32} />}>
        <Subscriptions />
      </Suspense>
    </main>
  );
}

async function Watchlist() {
  const r = await listMyWatchlist();
  const data = extractMcpData<any>(r.data);
  const items = data?.items || [];

  return (
    <section className="rounded-lg border">
      <header className="flex items-center justify-between border-b px-4 py-2 text-sm">
        <span className="font-medium">즐겨찾기</span>
        <span className="text-[var(--color-fg-muted)]">
          총 {data?.total_count ?? 0} ·{" "}
          {Object.entries(data?.by_type || {})
            .map(([k, v]) => `${k}=${v}`)
            .join(" / ")}
        </span>
      </header>
      {items.length === 0 ? (
        <p className="px-4 py-3 text-sm text-[var(--color-fg-muted)]">
          저장된 즐겨찾기 없음. 입찰 추적·업체 프로필 페이지에서 추가하세요.
        </p>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-[var(--color-bg-muted)]">
            <tr>
              <th className="px-3 py-2 text-left">유형</th>
              <th className="px-3 py-2 text-left">키</th>
              <th className="px-3 py-2 text-left">라벨</th>
              <th className="px-3 py-2 text-left">메모</th>
              <th className="px-3 py-2 text-left">추가일</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {items.map((it: any) => (
              <tr key={it.id} className="border-t">
                <td className="px-3 py-2">{badgeLabel(it.item_type)}</td>
                <td className="px-3 py-2 font-mono">
                  <WatchlistLink item={it} />
                </td>
                <td className="px-3 py-2">{it.item_label || "—"}</td>
                <td className="px-3 py-2 text-[var(--color-fg-muted)]">
                  {it.note || ""}
                </td>
                <td className="px-3 py-2 tabular-nums text-xs">
                  {it.created_at}
                </td>
                <td className="px-3 py-2 text-right">
                  <form action={removeWatchlistAction}>
                    <input type="hidden" name="item_type" value={it.item_type} />
                    <input type="hidden" name="item_key" value={it.item_key} />
                    <button
                      type="submit"
                      className="text-xs text-[var(--color-danger)] hover:underline"
                    >
                      제거
                    </button>
                  </form>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

async function Subscriptions() {
  const r = await listMySubscriptions();
  const data = extractMcpData<any>(r.data);
  const subs = data?.items || [];

  return (
    <section className="rounded-lg border">
      <header className="border-b px-4 py-2 text-sm font-medium">
        키워드 알림 구독 ({data?.subscription_count ?? 0})
      </header>

      <form
        action={subscribeKeywordAction}
        className="border-b bg-[var(--color-bg-muted)] p-4"
      >
        <div className="grid grid-cols-2 gap-2 lg:grid-cols-5">
          <input
            name="keyword"
            placeholder="키워드 (예: 정보화)"
            required
            className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
          />
          <select
            name="biz_type"
            className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
          >
            <option value="">업종 전체</option>
            <option value="공사">공사</option>
            <option value="용역">용역</option>
            <option value="물품">물품</option>
          </select>
          <input
            name="inst_name"
            placeholder="발주기관 (선택)"
            className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
          />
          <input
            name="notify_email"
            type="email"
            placeholder="알림 이메일"
            className="rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
          />
          <button
            type="submit"
            className="rounded bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-[var(--color-primary-fg)]"
          >
            구독
          </button>
        </div>
      </form>

      {subs.length === 0 ? (
        <p className="px-4 py-3 text-sm text-[var(--color-fg-muted)]">
          활성 구독 없음.
        </p>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-[var(--color-bg-muted)]">
            <tr>
              <th className="px-3 py-2 text-left">ID</th>
              <th className="px-3 py-2 text-left">키워드</th>
              <th className="px-3 py-2 text-left">업종</th>
              <th className="px-3 py-2 text-left">기관</th>
              <th className="px-3 py-2 text-left">이메일</th>
              <th className="px-3 py-2 text-left">생성일</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {subs.map((s: any) => (
              <tr key={s.id} className="border-t">
                <td className="px-3 py-2 tabular-nums">{s.id}</td>
                <td className="px-3 py-2 font-medium">{s.keyword}</td>
                <td className="px-3 py-2">{s.biz_type || "—"}</td>
                <td className="px-3 py-2">{s.inst_name || "—"}</td>
                <td className="px-3 py-2">{s.notify_email || "—"}</td>
                <td className="px-3 py-2 text-xs tabular-nums">
                  {s.created_at}
                </td>
                <td className="px-3 py-2 text-right">
                  <form action={unsubscribeAction}>
                    <input type="hidden" name="subscription_id" value={s.id} />
                    <button
                      type="submit"
                      className="text-xs text-[var(--color-danger)] hover:underline"
                    >
                      해지
                    </button>
                  </form>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

function badgeLabel(t: string): string {
  return (
    {
      bid: "📋 공고",
      vendor: "🏢 업체",
      agency: "🏛 기관",
      contract: "📜 계약",
    }[t] || t
  );
}

function WatchlistLink({ item }: { item: any }) {
  if (item.item_type === "bid") {
    return (
      <a
        href={`/bids/trace?no=${item.item_key}`}
        className="text-[var(--color-primary)] hover:underline"
      >
        {item.item_key}
      </a>
    );
  }
  if (item.item_type === "vendor") {
    return (
      <a
        href={`/vendors/${item.item_key}`}
        className="text-[var(--color-primary)] hover:underline"
      >
        {item.item_key}
      </a>
    );
  }
  return <span>{item.item_key}</span>;
}

function Skel({ h }: { h: number }) {
  return (
    <div
      className="animate-pulse rounded bg-[var(--color-bg-muted)]"
      style={{ height: `${h * 4}px` }}
    />
  );
}
