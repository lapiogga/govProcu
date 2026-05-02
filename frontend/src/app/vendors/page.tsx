/**
 * 업체 분석 인덱스 — 사업자번호 직접 입력 + 즐겨찾기 vendor 목록.
 * 대시보드 "업체 분석" 메뉴 카드 진입점.
 */
import { Suspense } from "react";
import { redirect } from "next/navigation";
import { listMyWatchlist } from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { VendorLink } from "@/components/EntityLink";

export default async function VendorsIndexPage(props: {
  searchParams: Promise<{ biz?: string }>;
}) {
  const { biz } = await props.searchParams;

  // 사업자번호 입력 시 즉시 redirect
  if (biz) {
    const cleaned = biz.trim().replace(/\D/g, "");
    if (/^\d{10}$/.test(cleaned)) {
      redirect(`/vendors/${cleaned}`);
    }
  }

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">업체 분석</h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          사업자번호로 NTS 진위 + 입찰/응찰/개찰/낙찰 통계 + 동종업체 비교 (vendor_profile)
        </p>
      </header>

      <Card>
        <CardContent className="p-4">
          <form action="/vendors" className="flex gap-2">
            <Input
              name="biz"
              placeholder="사업자번호 10자리 (예: 1234567890 또는 123-45-67890)"
              defaultValue={biz}
              className="flex-1"
              required
            />
            <Button type="submit">조회</Button>
          </form>
          {biz && (
            <p className="mt-2 text-xs text-[var(--color-danger)]">
              사업자번호 형식이 올바르지 않습니다. 10자리 숫자로 입력하세요.
            </p>
          )}
        </CardContent>
      </Card>

      <Suspense fallback={<Skel h={20} />}>
        <RecentVendors />
      </Suspense>
    </main>
  );
}

async function RecentVendors() {
  const r = await listMyWatchlist();
  const data = extractMcpData<any>(r.data);
  const items = (data?.items || []).filter((it: any) => it.item_type === "vendor");

  if (items.length === 0) {
    return (
      <Card>
        <CardContent className="p-4 text-sm text-[var(--color-fg-muted)]">
          즐겨찾기에 추가된 업체가 없습니다. 입찰 추적·응찰업체 표에서 추가하세요.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        <header className="border-b px-4 py-2 text-sm font-medium">
          즐겨찾기 업체 ({items.length})
        </header>
        <table className="w-full text-sm">
          <thead className="bg-[var(--color-bg-muted)]">
            <tr>
              <th className="px-3 py-2 text-left">사업자번호</th>
              <th className="px-3 py-2 text-left">라벨</th>
              <th className="px-3 py-2 text-left">메모</th>
              <th className="px-3 py-2 text-left">추가일</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it: any) => (
              <tr key={it.id} className="border-t hover:bg-[var(--color-bg-muted)]">
                <td className="px-3 py-2 font-mono">
                  <VendorLink bizNo={it.item_key} formatBizNo />
                </td>
                <td className="px-3 py-2">{it.item_label || "—"}</td>
                <td className="px-3 py-2 text-[var(--color-fg-muted)]">
                  {it.note || ""}
                </td>
                <td className="px-3 py-2 text-xs tabular-nums">{it.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
