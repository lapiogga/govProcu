/**
 * 내 즐겨찾기 + 알림 구독
 */
import { Suspense } from "react";
import { listMyWatchlist, listMySubscriptions } from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";
import {
  unsubscribeAction,
  subscribeKeywordAction,
} from "./actions";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { WatchlistTable, type WatchlistItem } from "./watchlist-table";
import { AddWatchlistDialog } from "./add-watchlist-dialog";

const SELECT_CLASS =
  "flex h-9 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]";

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
  const data = extractMcpData<{
    items?: WatchlistItem[];
    total_count?: number;
    by_type?: Record<string, number>;
  }>(r.data);
  const items: WatchlistItem[] = data?.items || [];
  const summary =
    Object.entries(data?.by_type || {})
      .map(([k, v]) => `${k}=${v}`)
      .join(" / ") || "—";

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>즐겨찾기</CardTitle>
          <p className="mt-1 text-xs text-[var(--color-fg-muted)]">
            총 {data?.total_count ?? 0} · {summary}
          </p>
        </div>
        <AddWatchlistDialog />
      </CardHeader>
      <CardContent className="p-4">
        {items.length === 0 ? (
          <p className="text-sm text-[var(--color-fg-muted)]">
            저장된 즐겨찾기 없음. "추가" 버튼 또는 입찰 추적·업체 프로필 페이지에서 추가하세요.
          </p>
        ) : (
          <WatchlistTable items={items} />
        )}
      </CardContent>
    </Card>
  );
}

async function Subscriptions() {
  const r = await listMySubscriptions();
  const data = extractMcpData<any>(r.data);
  const subs = data?.items || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>키워드 알림 구독 ({data?.subscription_count ?? 0})</CardTitle>
      </CardHeader>

      <form
        action={subscribeKeywordAction}
        className="border-b bg-[var(--color-bg-muted)] p-4"
      >
        <div className="grid grid-cols-2 gap-2 lg:grid-cols-5">
          <Input name="keyword" placeholder="키워드 (예: 정보화)" required />
          <select name="biz_type" defaultValue="" className={SELECT_CLASS}>
            <option value="">업종 전체</option>
            <option value="공사">공사</option>
            <option value="용역">용역</option>
            <option value="물품">물품</option>
          </select>
          <Input name="inst_name" placeholder="발주기관 (선택)" />
          <Input name="notify_email" type="email" placeholder="알림 이메일" />
          <Button type="submit">구독</Button>
        </div>
      </form>

      <CardContent className="p-0">
        {subs.length === 0 ? (
          <p className="p-4 text-sm text-[var(--color-fg-muted)]">활성 구독 없음.</p>
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
                  <td className="px-3 py-2 text-xs tabular-nums">{s.created_at}</td>
                  <td className="px-3 py-2 text-right">
                    <form action={unsubscribeAction}>
                      <input type="hidden" name="subscription_id" value={s.id} />
                      <Button type="submit" variant="link" size="sm" className="text-[var(--color-danger)]">
                        해지
                      </Button>
                    </form>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
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
