/**
 * Cross-Lookup — 4개 키 (공고/사업자/기관/계약) 진입.
 * UI Phase D 핵심. 입력 패턴 자동 감지 + 결과 노드 시각화.
 */
import { Suspense } from "react";
import Link from "next/link";
import {
  lookupByBidNo,
  lookupByBizNo,
  lookupByInstCode,
} from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";
import { fmtBizNo } from "@/lib/format";
import { LookupGraph } from "@/components/graph/LookupGraph";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { VendorLink, AgencyLink } from "@/components/EntityLink";

type Mode = "bid" | "biz" | "inst" | "contract";

// P30-R5 P1-18: 기간 default — biz/inst lookup용 1년 default (timeout 위험 회피)
function defaultDateFrom(): string {
  const d = new Date();
  d.setDate(d.getDate() - 365);
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
}

function defaultDateTo(): string {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
}

export default async function LookupPage(props: {
  searchParams: Promise<{
    mode?: Mode;
    q?: string;
    ord?: string;
    from?: string;
    to?: string;
  }>;
}) {
  const sp = await props.searchParams;
  const mode = sp.mode || "bid";
  const q = sp.q;
  // P30-R5 P1-18: 기간 form — biz/inst mode에서만 의미. bid mode는 단건 조회라 무관.
  const from = sp.from || defaultDateFrom();
  const to = sp.to || defaultDateTo();

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Cross-Lookup</h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          4개 핵심 키 (공고번호 / 사업자번호 / 발주기관 / 계약번호) 자동 관계 추적
        </p>
      </header>

      <nav className="flex gap-2 border-b text-sm">
        {[
          { k: "bid", label: "📋 공고번호" },
          { k: "biz", label: "🏢 사업자번호" },
          { k: "inst", label: "🏛 발주기관" },
          { k: "contract", label: "📜 계약번호" },
        ].map((tab) => (
          <a
            key={tab.k}
            href={`/lookup?mode=${tab.k}`}
            className={`border-b-2 px-3 py-2 ${
              mode === tab.k
                ? "border-[var(--color-primary)] font-medium"
                : "border-transparent text-[var(--color-fg-muted)]"
            }`}
          >
            {tab.label}
          </a>
        ))}
      </nav>

      <Card>
        <CardContent className="p-4">
          <form action="/lookup" className="flex flex-wrap gap-2">
            <input type="hidden" name="mode" value={mode} />
            <Input
              name="q"
              defaultValue={q}
              placeholder={placeholderFor(mode)}
              className="flex-1 min-w-[200px]"
              required
            />
            {mode === "bid" && (
              <Input
                name="ord"
                defaultValue={sp.ord || "00"}
                placeholder="차수"
                className="w-20"
              />
            )}
            {/* P30-R5 P1-18: biz/inst mode에 기간 input 추가 — backend timeout 위험 회피 */}
            {(mode === "biz" || mode === "inst") && (
              <>
                <Input
                  name="from"
                  defaultValue={from}
                  placeholder="from YYYYMMDD"
                  pattern="\d{8}"
                  className="max-w-[140px]"
                />
                <span className="self-center text-xs text-[var(--color-fg-muted)]">
                  ~
                </span>
                <Input
                  name="to"
                  defaultValue={to}
                  placeholder="to YYYYMMDD"
                  pattern="\d{8}"
                  className="max-w-[140px]"
                />
              </>
            )}
            <Button type="submit">추적</Button>
          </form>
          {(mode === "biz" || mode === "inst") && (
            <p className="mt-2 text-xs text-[var(--color-fg-muted)]">
              기간 미입력 시 1년 default 적용 (G2B 1개월 chunk 자동 — timeout 위험 회피).
            </p>
          )}
        </CardContent>
      </Card>

      {q ? (
        <Suspense fallback={<Skel h={32} />}>
          <Result
            mode={mode}
            q={q}
            ord={sp.ord || "00"}
            from={from}
            to={to}
          />
        </Suspense>
      ) : (
        <p className="text-sm text-[var(--color-fg-muted)]">
          키를 입력하면 다른 3개 키로의 관계가 자동 추적됩니다.
        </p>
      )}
    </main>
  );
}

function placeholderFor(mode: Mode): string {
  if (mode === "bid") return "공고번호 (예: 20240315678)";
  if (mode === "biz") return "사업자번호 10자리 (예: 1234567890)";
  if (mode === "inst") return "발주기관명 (예: 국방재정관리단)";
  return "계약번호 (별도 키 필요)";
}

async function Result({
  mode,
  q,
  ord,
  from,
  to,
}: {
  mode: Mode;
  q: string;
  ord: string;
  from: string;
  to: string;
}) {
  if (mode === "contract") {
    return (
      <div className="rounded border p-4 text-sm text-[var(--color-fg-muted)]">
        계약번호 단독 lookup은 별도 계약정보서비스(15129427) 키 필요. 현재
        스텁 상태.
      </div>
    );
  }

  let r;
  // P30-R5 P1-18: biz/inst mode에 기간 인자 전달 — backend 무기간 호출 timeout 위험 회피
  if (mode === "bid") r = await lookupByBidNo(q, ord);
  else if (mode === "biz") r = await lookupByBizNo(q, from, to);
  else r = await lookupByInstCode(q, from, to);

  if (!r.ok) {
    return (
      <div className="rounded border border-[var(--color-danger)] p-4 text-sm">
        오류: {r.error}
      </div>
    );
  }
  const data = extractMcpData<any>(r.data);
  if (!data) return <p className="text-sm">결과 없음</p>;

  const keys = data.keys || {};
  const summary = data.summary || {};

  return (
    <div className="space-y-4">
      {/* 4 키 그래프 시각화 (xyflow) */}
      <section>
        <h2 className="mb-2 text-sm font-medium">관계 그래프</h2>
        <LookupGraph keys={keys} startingKey={mode} />
      </section>

      {/* 4 키 카드 (보조) */}
      <section className="rounded-lg border bg-[var(--color-bg-muted)] p-4">
        <h2 className="mb-3 text-sm font-medium">키 상세 + 빠른 이동</h2>
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-4">
          <KeyNode
            label="📋 공고번호"
            value={keys.bid_notice_no || "—"}
            ord={keys.bid_ord}
            href={
              keys.bid_notice_no
                ? `/bids/trace?no=${keys.bid_notice_no}&ord=${keys.bid_ord || "00"}`
                : undefined
            }
            highlight={mode === "bid"}
          />
          <KeyNode
            label="🏛 발주기관"
            value={keys.inst_name || "—"}
            sub={keys.inst_code}
            href={
              keys.inst_name
                ? `/agencies?name=${encodeURIComponent(keys.inst_name)}`
                : undefined
            }
            highlight={mode === "inst"}
          />
          <KeyNode
            label="🏢 사업자번호"
            value={fmtBizNo(keys.vendor_biz_no)}
            sub={keys.vendor_name}
            href={
              keys.vendor_biz_no ? `/vendors/${keys.vendor_biz_no}` : undefined
            }
            highlight={mode === "biz"}
          />
          <KeyNode
            label="📜 계약번호"
            value={keys.contract_no || "—"}
            highlight={false}
          />
        </div>
      </section>

      {/* 요약 통계 */}
      {summary && Object.keys(summary).length > 0 && (
        <section className="rounded-lg border p-4">
          <h2 className="mb-2 text-sm font-medium">요약</h2>
          <pre className="overflow-x-auto text-xs">
            {JSON.stringify(summary, null, 2)}
          </pre>
        </section>
      )}

      {/* Top winners (mode=inst) */}
      {summary?.top_winners?.length > 0 && (
        <section className="rounded-lg border">
          <header className="border-b px-4 py-2 text-sm font-medium">
            거래 빈도 Top 업체
          </header>
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-bg-muted)]">
              <tr>
                <th className="px-3 py-2 text-left">업체명</th>
                <th className="px-3 py-2 text-left">사업자번호</th>
                <th className="px-3 py-2 text-right">거래수</th>
                <th className="px-3 py-2 text-right">합계</th>
              </tr>
            </thead>
            <tbody>
              {summary.top_winners.map((w: any) => (
                <tr key={w.vendor_biz_no} className="border-t">
                  <td className="px-3 py-2">
                    <VendorLink bizNo={w.vendor_biz_no} name={w.vendor_name} />
                  </td>
                  <td className="px-3 py-2 tabular-nums">
                    <VendorLink
                      bizNo={w.vendor_biz_no}
                      name={fmtBizNo(w.vendor_biz_no)}
                    />
                  </td>
                  <td className="px-3 py-2 text-right">{w.award_count}</td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {(w.award_total_won / 100_000_000).toFixed(2)}억
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* P30-R5 P1-17: bid_notice_no_list 표시 (mode=biz) — 이 업체가 받은 공고 목록 */}
      {mode === "biz" && summary?.bid_notice_no_list?.length > 0 && (
        <section className="rounded-lg border">
          <header className="flex flex-wrap items-center gap-2 border-b px-4 py-2 text-sm font-medium">
            <span>이 업체가 받은 공고 목록</span>
            <span className="text-xs font-normal text-[var(--color-fg-muted)]">
              (낙찰 {summary.award_count ?? 0}건 · 첫{" "}
              {summary.bid_notice_no_list.length}건)
            </span>
          </header>
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-bg-muted)]">
              <tr>
                <th className="px-3 py-2 text-left">#</th>
                <th className="px-3 py-2 text-left">공고번호</th>
                <th className="px-3 py-2 text-right">바로가기</th>
              </tr>
            </thead>
            <tbody>
              {summary.bid_notice_no_list.map(
                (bidNo: string, i: number) => (
                  <tr key={i} className="border-t">
                    <td className="px-3 py-2 tabular-nums text-[var(--color-fg-muted)]">
                      {i + 1}
                    </td>
                    <td className="px-3 py-2 font-mono">
                      <Link
                        href={`/bids/trace?no=${bidNo}&ord=00`}
                        className="entity-link"
                      >
                        {bidNo}
                      </Link>
                    </td>
                    <td className="px-3 py-2 text-right text-xs">
                      <Link
                        href={`/bids/trace?no=${bidNo}&ord=00`}
                        className="entity-link"
                      >
                        추적 →
                      </Link>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </section>
      )}

      {/* Top agencies (mode=biz) */}
      {summary?.top_agencies?.length > 0 && (
        <section className="rounded-lg border">
          <header className="border-b px-4 py-2 text-sm font-medium">
            주요 거래 발주기관
          </header>
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-bg-muted)]">
              <tr>
                <th className="px-3 py-2 text-left">기관</th>
                <th className="px-3 py-2 text-right">거래수</th>
                <th className="px-3 py-2 text-right">합계</th>
              </tr>
            </thead>
            <tbody>
              {summary.top_agencies.map((a: any, i: number) => (
                <tr key={i} className="border-t">
                  <td className="px-3 py-2">
                    <AgencyLink name={a.inst_name} />
                  </td>
                  <td className="px-3 py-2 text-right">{a.deal_count}</td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {(a.deal_total_won / 100_000_000).toFixed(2)}억
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}

function KeyNode({
  label,
  value,
  sub,
  ord,
  href,
  highlight,
}: {
  label: string;
  value: string;
  sub?: string;
  ord?: string;
  href?: string;
  highlight: boolean;
}) {
  const inner = (
    <div
      className={`rounded-lg border p-3 transition-colors ${
        highlight
          ? "border-[var(--color-primary)] bg-[var(--color-bg-muted)]"
          : "hover:border-[var(--color-primary)] hover:bg-[var(--color-bg-muted)]"
      }`}
    >
      <div className="text-xs text-[var(--color-fg-muted)]">{label}</div>
      <div className="mt-1 font-medium tabular-nums">{value}</div>
      {ord && <div className="text-xs">차수 {ord}</div>}
      {sub && <div className="text-xs text-[var(--color-fg-muted)]">{sub}</div>}
      {href && (
        <div className="mt-2 text-[10px] text-[var(--color-primary)]">
          → 상세로 이동
        </div>
      )}
    </div>
  );
  return href ? (
    <Link href={href} className="block">
      {inner}
    </Link>
  ) : (
    inner
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
