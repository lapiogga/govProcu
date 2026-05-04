import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import { ThemeToggle, themeBootstrapScript } from "@/components/ThemeToggle";
import { GlobalCommandPalette } from "@/components/GlobalCommandPalette";
import { listMyWatchlist } from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";

export const metadata: Metadata = {
  title: "GovProcu — 나라장터 인터랙티브 콘솔",
  description:
    "공고번호 / 사업자번호 / 발주기관 1개로 입찰 전 생애를 한 화면에서 추적",
};

// 데스크톱·태블릿 전용 (모바일 비대상)
export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const watchlistVendors = await loadWatchlistVendors();
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{ __html: themeBootstrapScript }}
        />
      </head>
      <body className="min-h-screen antialiased" suppressHydrationWarning>
        <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-muted)]">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-2">
            <Link
              href="/"
              className="text-sm font-semibold tracking-tight text-[var(--color-fg)]"
            >
              GovProcu
            </Link>
            <div className="flex items-center gap-3">
              <GlobalCommandPalette watchlistVendors={watchlistVendors} />
              <ThemeToggle />
            </div>
          </div>
        </header>
        <div className="mx-auto max-w-7xl px-6 py-4">{children}</div>
      </body>
    </html>
  );
}

async function loadWatchlistVendors(): Promise<
  Array<{ biz_no: string; label?: string }>
> {
  try {
    const r = await listMyWatchlist("vendor");
    if (!r.ok) return [];
    const data = extractMcpData<{
      items?: Array<{ item_type?: string; item_key?: string; item_label?: string }>;
    }>(r.data);
    const items = (data?.items || []).filter((it) => it.item_type === "vendor");
    return items.map((it) => ({
      biz_no: it.item_key || "",
      label: it.item_label,
    }));
  } catch {
    return [];
  }
}
