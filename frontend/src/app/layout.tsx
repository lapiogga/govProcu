import type { Metadata } from "next";
import "./globals.css";

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
      <body className="min-h-screen antialiased">
        <div className="mx-auto max-w-7xl px-6 py-4">{children}</div>
      </body>
    </html>
  );
}
