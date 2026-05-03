/**
 * 빠른 검색 라우터 — 입력 패턴을 분석해 적절한 페이지로 redirect.
 * - 10자리 숫자 → 사업자번호 (vendor profile)
 * - 8~15자리 숫자 → 공고번호 (trace)
 * - 그 외 → bid 검색
 */
import { redirect } from "next/navigation";

export default async function QuickSearchPage(props: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await props.searchParams;

  if (!q) redirect("/");
  const cleaned = q.trim().replace(/[-\s]/g, "");

  // 사업자번호 패턴 (10자리 숫자)
  if (/^\d{10}$/.test(cleaned)) {
    redirect(`/vendors/${cleaned}`);
  }

  // 공고번호 패턴 (숫자 8~15)
  if (/^\d{8,15}$/.test(cleaned)) {
    redirect(`/bids/trace?no=${cleaned}`);
  }

  // 그 외 키워드 검색 — P30-R3 P1-05 (F16):
  // /search 진입은 사용자가 키워드만 빠르게 시도하는 경로 → deep=1 자동 부여로
  // scan_pages=5 매칭률 ↑ ("정보체계" / "아이웨이브" 0건 false-negative 회피).
  redirect(`/bids?q=${encodeURIComponent(q)}&deep=1`);
}
