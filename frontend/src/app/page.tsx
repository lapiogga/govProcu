/**
 * GovProcu 대시보드 (홈) — shadcn 컴포넌트 적용 (NEXT4-1).
 */
import Link from "next/link";
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function DashboardPage() {
  return (
    <main className="space-y-8">
      <header className="border-b pb-4">
        <h1 className="text-3xl font-semibold">GovProcu</h1>
        <p className="text-sm text-[var(--color-fg-muted)]">
          공고번호·사업자번호 1개로 입찰 전 생애를 한 화면에서 추적
        </p>
      </header>

      {/* 빠른 검색 */}
      <Card>
        <CardContent className="p-4">
          <form action="/search" method="GET" className="flex gap-2">
            <Input
              name="q"
              placeholder="공고번호 / 사업자번호 / 발주기관명·키워드"
              autoFocus
            />
            <Button type="submit">검색</Button>
          </form>
        </CardContent>
      </Card>

      {/* 9개 메뉴 카드 */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        {MENUS.map((m) => (
          <MenuCard key={m.href} {...m} />
        ))}
      </section>

      <footer className="border-t pt-4 text-xs text-[var(--color-fg-muted)]">
        v0.1 PoC · 데스크톱·태블릿 전용 · MCP{" "}
        {process.env.GOVPROCU_MCP_URL || "localhost:8081"}
      </footer>
    </main>
  );
}

const MENUS: MenuItem[] = [
  {
    title: "입찰 검색",
    description: "키워드·업종·기관·기간으로 공고/사전규격/낙찰 통합 검색",
    href: "/bids",
    tag: "기본",
    variant: "secondary",
  },
  {
    title: "입찰 상세 추적 ★",
    description: "사전규격 → 공고 → 개찰 → 낙찰 → 응찰업체 → NTS 검증",
    href: "/bids/trace",
    tag: "핵심",
    variant: "default",
    accent: true,
  },
  {
    title: "업체 분석",
    description: "NTS 진위 + 입찰/응찰/개찰/낙찰 통계 + 동종업체 비교",
    href: "/vendors",
    tag: "P1",
    variant: "secondary",
  },
  {
    title: "발주기관 분석",
    description: "발주 이력 + 낙찰업체 + 사정률 패턴 + 발주규모 통계",
    href: "/agencies",
    tag: "P1",
    variant: "secondary",
  },
  {
    title: "분석/통계",
    description: "동종업체·유사사업·업종 동향·경쟁사 비교·시장 점유",
    href: "/analytics",
  },
  {
    title: "Cross-Lookup",
    description: "공고/계약/기관/사업자 4키로 자동 관계 추적 (xyflow)",
    href: "/lookup",
    tag: "신규",
    variant: "outline",
  },
  {
    title: "알림 + 즐겨찾기",
    description: "키워드 구독·다이제스트·관심 항목 (P0 시장 진입 자격)",
    href: "/me",
    tag: "P0",
    variant: "success",
  },
  {
    title: "투찰가 예측",
    description: "발주기관 사정률 + 목표 낙찰확률 → 적정 응찰가 + 95% CI",
    href: "/prediction",
    tag: "P1",
    variant: "secondary",
  },
  {
    title: "적격심사 계산기",
    description: "입찰가·시공경험·기술자·신용평가 → 종합 점수 (조달청 표준)",
    href: "/qualification",
    tag: "P0",
    variant: "success",
  },
  {
    title: "K-water 계약공개",
    description: "한국수자원공사 전자조달 계약 정보 (월 단위, 외부 어댑터)",
    href: "/external/kwater",
    tag: "외부",
    variant: "outline",
  },
];

interface MenuItem {
  title: string;
  description: string;
  href: string;
  tag?: string;
  variant?: "default" | "secondary" | "outline" | "success";
  accent?: boolean;
}

function MenuCard({ title, description, href, tag, variant, accent }: MenuItem) {
  return (
    <Link href={href}>
      <Card
        className={`h-full transition-colors hover:bg-[var(--color-bg-muted)] ${
          accent ? "border-[var(--color-primary)] bg-[var(--color-bg-muted)]" : ""
        }`}
      >
        <CardContent className="space-y-2 p-4">
          <div className="flex items-start justify-between gap-2">
            <CardTitle>{title}</CardTitle>
            {tag && <Badge variant={variant}>{tag}</Badge>}
          </div>
          <CardDescription>{description}</CardDescription>
        </CardContent>
      </Card>
    </Link>
  );
}
