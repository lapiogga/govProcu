/**
 * 표시 포맷터 (입찰액·날짜·낙찰률).
 */

export function fmtWon(amount: number | null | undefined): string {
  if (amount == null) return "—";
  if (amount >= 100_000_000) {
    const eok = amount / 100_000_000;
    return `${eok.toFixed(eok >= 100 ? 0 : 2)}억`;
  }
  if (amount >= 10_000) {
    return `${(amount / 10_000).toFixed(0)}만`;
  }
  return amount.toLocaleString("ko-KR");
}

export function fmtRate(rate: number | string | null | undefined): string {
  if (rate == null) return "—";
  const r = typeof rate === "string" ? parseFloat(rate.replace("%", "")) : rate;
  if (Number.isNaN(r)) return "—";
  return `${r.toFixed(2)}%`;
}

export function fmtDate(s: string | null | undefined): string {
  if (!s) return "—";
  const cleaned = s.replace(/[^\d]/g, "").slice(0, 8);
  if (cleaned.length !== 8) return s;
  return `${cleaned.slice(0, 4)}-${cleaned.slice(4, 6)}-${cleaned.slice(6, 8)}`;
}

export function fmtBizNo(s: string | null | undefined): string {
  if (!s) return "—";
  const d = s.replace(/\D/g, "");
  if (d.length !== 10) return s;
  return `${d.slice(0, 3)}-${d.slice(3, 5)}-${d.slice(5)}`;
}
