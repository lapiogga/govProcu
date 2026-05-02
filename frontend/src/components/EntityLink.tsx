/**
 * 엔티티 링크 헬퍼 — 표·카드·시각화 어디서나 일관된 라우팅.
 *
 * 사용자 정책 (5/2):
 *   업체명 / 사업자번호    → /vendors/{biz_no}
 *   발주기관명             → /agencies?name={inst_name}
 *   공고제목 / 공고번호    → /bids/trace?no={bid_no}&ord={ord}
 *
 * 모든 페이지에서 동일 컴포넌트를 사용해야 하며, 직접 <a href=...> 작성 금지.
 * 값이 없으면 '—' 또는 fallback 문자열 표시 (link 미생성).
 */
import Link from "next/link";
import type { ReactNode } from "react";
import { fmtBizNo } from "@/lib/format";

const LINK_CLASS = "entity-link font-medium";

function trim(s: string | undefined | null): string {
  return (s ?? "").toString().trim();
}

/** 업체명 또는 사업자번호로 vendor 프로필로 이동. biz_no 가 진짜 키. */
export function VendorLink({
  bizNo,
  name,
  formatBizNo = false,
  fallback = "—",
  className,
}: {
  bizNo?: string | null;
  /** 표시할 텍스트. 미지정 시 사업자번호 표시 */
  name?: string | null;
  /** true 면 사업자번호를 'XXX-XX-XXXXX' 로 포맷 */
  formatBizNo?: boolean;
  fallback?: ReactNode;
  className?: string;
}) {
  const biz = trim(bizNo).replace(/\D/g, "");
  if (!biz) {
    return <span className={className}>{name || fallback}</span>;
  }
  const display = name
    ? trim(name)
    : formatBizNo
      ? fmtBizNo(biz)
      : biz;
  return (
    <Link
      href={`/vendors/${biz}`}
      className={`${LINK_CLASS} ${className ?? ""}`}
      title={`업체 프로필 — ${name || fmtBizNo(biz)}`}
    >
      {display}
    </Link>
  );
}

/** 발주기관명으로 agencies 분석으로 이동. */
export function AgencyLink({
  name,
  fallback = "—",
  className,
}: {
  name?: string | null;
  fallback?: ReactNode;
  className?: string;
}) {
  const inst = trim(name);
  if (!inst) {
    return <span className={className}>{fallback}</span>;
  }
  return (
    <Link
      href={`/agencies?name=${encodeURIComponent(inst)}`}
      className={`${LINK_CLASS} ${className ?? ""}`}
      title={`발주기관 분석 — ${inst}`}
    >
      {inst}
    </Link>
  );
}

/** 공고번호+차수로 입찰 추적으로 이동. 텍스트는 제목(있으면) 또는 공고번호. */
export function BidLink({
  bidNo,
  ord = "00",
  title,
  fallback = "—",
  className,
}: {
  bidNo?: string | null;
  ord?: string | null;
  /** 표시할 텍스트. 미지정 시 공고번호 표시 */
  title?: string | null;
  fallback?: ReactNode;
  className?: string;
}) {
  const no = trim(bidNo);
  if (!no) {
    return <span className={className}>{title || fallback}</span>;
  }
  const display = title ? trim(title) : no;
  const ordVal = trim(ord) || "00";
  return (
    <Link
      href={`/bids/trace?no=${encodeURIComponent(no)}&ord=${encodeURIComponent(ordVal)}`}
      className={`${LINK_CLASS} ${className ?? ""}`}
      title={`입찰 추적 — ${no}-${ordVal}`}
    >
      {display}
    </Link>
  );
}
