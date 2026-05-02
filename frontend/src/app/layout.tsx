import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import { ThemeToggle, themeBootstrapScript } from "@/components/ThemeToggle";

export const metadata: Metadata = {
  title: "GovProcu — 나라장터 인터랙티브 콘솔",
  description:
    "공고번호 / 사업자번호 / 발주기관 1개로 입찰 전 생애를 한 화면에서 추적",
};

// 데스크톱·태블릿 전용 (모바일 비대상)
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{ __html: themeBootstrapScript }}
        />
      </head>
      <body className="min-h-screen antialiased">
        <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-muted)]">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-2">
            <Link
              href="/"
              className="text-sm font-semibold tracking-tight text-[var(--color-fg)]"
            >
              GovProcu
            </Link>
            <ThemeToggle />
          </div>
        </header>
        <div className="mx-auto max-w-7xl px-6 py-4">{children}</div>
      </body>
    </html>
  );
}
