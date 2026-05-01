/**
 * GovProcu 대시보드 (홈)
 *
 * UI-PLAN.md 핵심 가치: 공고번호 1개로 입찰 전 생애 추적, 사업자번호 1개로 업체 시장 위치.
 * FRONTEND-TECH.md Wave 1: RSC + Streaming + Suspense.
 * 사용자 5/2 23번 정정: 데스크톱·태블릿 only (모바일 비대상).
 */
import Link from "next/link";

export default function DashboardPage() {
  return (
    <main className="space-y-8">
      <header className="border-b pb-4">
        <h1 className="text-3xl font-semibold">GovProcu</h1>
        <p className="text-sm text-[var(--color-fg-muted)]">
          공고번호·사업자번호 1개로 입찰 전 생애를 한 화면에서 추적
        </p>
      </header>

      {/* 빠른 검색 (cmd+k 향후 통합) */}
      <section>
        <form
          action="/search"
          method="GET"
          className="flex gap-2 rounded-lg border bg-[var(--color-bg-muted)] p-4"
        >
          <input
            name="q"
            type="text"
            placeholder="공고번호(20240315678) / 사업자번호(1234567890) / 발주기관명·키워드"
            className="flex-1 rounded border bg-[var(--color-bg)] px-3 py-2 text-sm"
            autoFocus
          />
          <button
            type="submit"
            className="rounded bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-[var(--color-primary-fg)]"
          >
            검색
          </button>
        </form>
      </section>

      {/* 7대 메뉴 영역 */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        <MenuCard
          title="입찰 검색"
          description="키워드·업종·기관·기간으로 공고/사전규격/낙찰 통합 검색"
          href="/bids"
          tag="기본"
        />
        <MenuCard
          title="입찰 상세 추적 ★"
          description="사전규격 → 공고 → 개찰 → 낙찰 → 응찰업체 → NTS 검증"
          href="/bids/trace"
          tag="핵심"
          accent
        />
        <MenuCard
          title="업체 분석"
          description="NTS 진위 + 입찰/응찰/개찰/낙찰 통계 + 동종업체 비교"
          href="/vendors"
          tag="P1"
        />
        <MenuCard
          title="발주기관 분석"
          description="발주 이력 + 낙찰업체 + 사정률 패턴 + 발주규모 통계"
          href="/agencies"
          tag="P1"
        />
        <MenuCard
          title="분석/통계"
          description="동종업체·유사사업·업종 동향·경쟁사 비교·시장 점유"
          href="/analytics"
        />
        <MenuCard
          title="Cross-Lookup"
          description="공고/계약/기관/사업자 4키로 자동 관계 추적"
          href="/lookup"
          tag="신규"
        />
        <MenuCard
          title="알림 + 즐겨찾기"
          description="키워드 구독·다이제스트·관심 항목 (P0 시장 진입 자격)"
          href="/me"
          tag="P0"
        />
        <MenuCard
          title="투찰가 예측"
          description="발주기관 사정률 + 목표 낙찰확률 → 적정 응찰가 + 95% CI"
          href="/prediction"
          tag="P1"
        />
        <MenuCard
          title="적격심사 계산기"
          description="입찰가·시공경험·기술자·신용평가 → 종합 점수 (조달청 표준)"
          href="/qualification"
          tag="P0"
        />
      </section>

      <footer className="border-t pt-4 text-xs text-[var(--color-fg-muted)]">
        v0.1 PoC · 데스크톱·태블릿 전용 · MCP {process.env.GOVPROCU_MCP_URL || "localhost:8080"}
      </footer>
    </main>
  );
}

function MenuCard({
  title,
  description,
  href,
  tag,
  accent,
}: {
  title: string;
  description: string;
  href: string;
  tag?: string;
  accent?: boolean;
}) {
  return (
    <Link
      href={href}
      className={`block rounded-lg border p-4 transition-colors hover:bg-[var(--color-bg-muted)] ${
        accent ? "border-[var(--color-primary)] bg-[var(--color-bg-muted)]" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <h2 className="text-base font-medium">{title}</h2>
        {tag && (
          <span className="rounded bg-[var(--color-primary)] px-2 py-0.5 text-xs text-[var(--color-primary-fg)]">
            {tag}
          </span>
        )}
      </div>
      <p className="mt-2 text-sm text-[var(--color-fg-muted)]">{description}</p>
    </Link>
  );
}
