/**
 * 입찰 상세 추적 ★ — v26.2 Suspense Streaming 모드.
 *
 * 1 Timeline 통합 await (이전) → 6 Suspense 분리 (현재).
 * 각 stage별 server action이 자체 fetch → 도착 즉시 unsuspend → 사용자 체감 5초 SLA.
 * backend 단건 도구 모두 @cache_result(30분) 적용 (v23.5).
 *
 * URL: /bids/trace?no=20240315678&ord=00
 */
import { Suspense } from "react";
import {
  getPreSpecDetail,
  getBidNoticeDetail,
  listBidParticipants,
  getAwardDetail,
  checkBusinessStatus,
} from "@/lib/actions";
import { fmtWon, fmtRate, fmtDate, fmtBizNo } from "@/lib/format";
import { VendorLink, AgencyLink } from "@/components/EntityLink";

export default async function TracePage(props: {
  searchParams: Promise<{ no?: string; ord?: string }>;
}) {
  const sp = await props.searchParams;
  // 5/3 N42: "R26BK01435763-000" 처럼 suffix 통합된 입력 자동 split
  let bidNo = sp.no;
  let bidOrd = sp.ord ?? "00";
  if (bidNo && bidNo.includes("-") && (!sp.ord || !sp.ord.replace(/0/g, ""))) {
    const lastDash = bidNo.lastIndexOf("-");
    const tail = bidNo.slice(lastDash + 1);
    if (/^\d+$/.test(tail)) {
      bidOrd = tail;
      bidNo = bidNo.slice(0, lastDash);
    }
  }

  if (!bidNo) {
    return (
      <main className="space-y-4">
        <h1 className="text-2xl font-semibold">입찰 상세 추적</h1>
        <form className="flex gap-2 rounded border p-4" action="/bids/trace">
          <input
            name="no"
            placeholder="공고번호 (예: 20240315678)"
            className="flex-1 rounded border bg-[var(--color-bg)] px-3 py-2"
            required
          />
          <input
            name="ord"
            placeholder="차수"
            defaultValue="00"
            className="w-24 rounded border bg-[var(--color-bg)] px-3 py-2"
          />
          <button
            type="submit"
            className="rounded bg-[var(--color-primary)] px-4 py-2 text-[var(--color-primary-fg)]"
          >
            추적
          </button>
        </form>
        <p className="text-sm text-[var(--color-fg-muted)]">
          공고번호 1개로 사전규격 → 본 공고 → 개찰 → 낙찰 → 응찰업체 → 낙찰자 NTS 검증 6단계를 한 번에.
        </p>
      </main>
    );
  }

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">
          입찰 추적: {bidNo}-{bidOrd}
        </h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          v26.2 Streaming — stage별 도착 즉시 표시
        </p>
      </header>

      {/* Summary header (bid_notice 결과) */}
      <Suspense fallback={<SummarySkeleton />}>
        <SummarySection bidNo={bidNo} bidOrd={bidOrd} />
      </Suspense>

      {/* 6단계 타임라인 */}
      <section className="space-y-2">
        <Suspense fallback={<StageSkeleton n={1} label="사전규격" desc="등록 + 의견수렴" />}>
          <StagePreSpec bidNo={bidNo} bidOrd={bidOrd} />
        </Suspense>
        <Suspense fallback={<StageSkeleton n={2} label="본 공고" desc="추정가" />}>
          <StageNotice bidNo={bidNo} bidOrd={bidOrd} />
        </Suspense>
        <Suspense fallback={<StageSkeleton n={3} label="개찰 + 응찰업체" desc="응찰자" />}>
          <StageParticipants bidNo={bidNo} bidOrd={bidOrd} />
        </Suspense>
        <Suspense fallback={<StageSkeleton n={4} label="낙찰" desc="결과" />}>
          <StageAwardAndNts bidNo={bidNo} bidOrd={bidOrd} />
        </Suspense>
        <Stage n={6} label="계약" ok={false} desc="체결 후 추적 가능" inactive />
      </section>

      {/* 액션 링크 */}
      <Suspense fallback={null}>
        <ActionLinks bidNo={bidNo} bidOrd={bidOrd} />
      </Suspense>
    </main>
  );
}

// === Summary 섹션 (bid_notice 결과) ===

async function SummarySection({ bidNo, bidOrd }: { bidNo: string; bidOrd: string }) {
  const r = await getBidNoticeDetail(bidNo, bidOrd);
  if (!r.ok) {
    return (
      <div className="rounded border border-[var(--color-danger)] p-4 text-sm">
        본 공고 조회 오류: {r.error}
      </div>
    );
  }
  const data = extractData(r.data);
  const summary = data?.summary || data?.raw || {};
  // 낙찰 정보는 stage4(award)에서 추가 — summary header는 공고 기본 + 낙찰자 placeholder
  return (
    <section className="rounded-lg border bg-[var(--color-bg-muted)] p-4">
      <h2 className="text-lg font-medium">
        {summary.title || summary.bidNtceNm || "(제목 없음)"}
      </h2>
      <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-2 text-sm lg:grid-cols-4">
        <div>
          <dt className="text-[var(--color-fg-muted)]">발주기관</dt>
          <dd className="font-medium">
            <AgencyLink name={summary.inst_name || summary.ntceInsttNm} />
          </dd>
        </div>
        <div>
          <dt className="text-[var(--color-fg-muted)]">업종</dt>
          <dd>{summary.biz_type || summary.bsnsDivNm || "—"}</dd>
        </div>
        <div>
          <dt className="text-[var(--color-fg-muted)]">추정가</dt>
          <dd className="tabular-nums font-medium">
            {fmtWon(summary.estimated_price ?? summary.presmptPrce)}
          </dd>
        </div>
        <div>
          <dt className="text-[var(--color-fg-muted)]">공고일</dt>
          <dd className="tabular-nums">{fmtDate(summary.publish_date ?? summary.bidNtceDt)}</dd>
        </div>
      </dl>
      {/* 낙찰 정보는 Stage4 도착 후 별도 표시 */}
      <Suspense fallback={<p className="mt-3 text-xs text-[var(--color-fg-muted)]">낙찰 정보 로딩 중…</p>}>
        <AwardSummary bidNo={bidNo} bidOrd={bidOrd} />
      </Suspense>
    </section>
  );
}

async function AwardSummary({ bidNo, bidOrd }: { bidNo: string; bidOrd: string }) {
  const r = await getAwardDetail(bidNo, bidOrd);
  if (!r.ok) return null;
  const data = extractData(r.data);
  const aw = data?.summary || {};
  if (!aw.winner_name && !aw.award_amount) return null;
  return (
    <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-2 border-t pt-3 text-sm lg:grid-cols-3">
      <div>
        <dt className="text-[var(--color-fg-muted)]">낙찰자</dt>
        <dd className="font-medium">
          <VendorLink bizNo={aw.winner_biz_no} name={aw.winner_name} />
        </dd>
      </div>
      <div>
        <dt className="text-[var(--color-fg-muted)]">낙찰가/낙찰률</dt>
        <dd className="tabular-nums font-medium">
          {fmtWon(aw.award_amount)} / {fmtRate(aw.award_rate)}
        </dd>
      </div>
      <div>
        <dt className="text-[var(--color-fg-muted)]">개찰일</dt>
        <dd className="tabular-nums">{fmtDate(aw.open_date)}</dd>
      </div>
    </dl>
  );
}

// === Stage 컴포넌트들 ===

async function StagePreSpec({ bidNo, bidOrd }: { bidNo: string; bidOrd: string }) {
  const r = await getPreSpecDetail(bidNo, bidOrd);
  const data = extractData(r.data);
  return <Stage n={1} label="사전규격" ok={data?.found} desc="등록 + 의견수렴" />;
}

async function StageNotice({ bidNo, bidOrd }: { bidNo: string; bidOrd: string }) {
  const r = await getBidNoticeDetail(bidNo, bidOrd);
  const data = extractData(r.data);
  const summary = data?.summary || {};
  return (
    <Stage
      n={2}
      label="본 공고"
      ok={data?.found}
      desc={`추정가 ${fmtWon(summary.estimated_price ?? summary.presmptPrce)}`}
    />
  );
}

async function StageParticipants({ bidNo, bidOrd }: { bidNo: string; bidOrd: string }) {
  const r = await listBidParticipants(bidNo, bidOrd);
  const data = extractData(r.data);
  const items: ParticipantRow[] = data?.items || [];
  return (
    <>
      <Stage
        n={3}
        label="개찰 + 응찰업체"
        ok={items.length > 0}
        desc={`응찰자 ${data?.participant_count ?? items.length}개사`}
      />
      {items.length > 0 && (
        <section className="rounded-lg border">
          <h3 className="border-b px-4 py-2 text-sm font-medium">응찰업체 {items.length}개사</h3>
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-bg-muted)]">
              <tr>
                <th className="px-3 py-2 text-left">순위</th>
                <th className="px-3 py-2 text-left">업체명</th>
                <th className="px-3 py-2 text-left">사업자번호</th>
                <th className="px-3 py-2 text-right">응찰가</th>
                <th className="px-3 py-2 text-center">낙찰</th>
              </tr>
            </thead>
            <tbody>
              {items.map((p, i) => (
                <tr key={i} className="border-t">
                  <td className="px-3 py-2 tabular-nums">{p.opening_rank ?? "—"}</td>
                  <td className="px-3 py-2">
                    <VendorLink bizNo={p.participant_biz_no} name={p.participant_name} />
                  </td>
                  <td className="px-3 py-2 tabular-nums">
                    <VendorLink bizNo={p.participant_biz_no} name={fmtBizNo(p.participant_biz_no)} />
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">{fmtWon(p.participant_bid_amount)}</td>
                  <td className="px-3 py-2 text-center">{p.is_winner ? "🏆" : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </>
  );
}

async function StageAwardAndNts({ bidNo, bidOrd }: { bidNo: string; bidOrd: string }) {
  const r = await getAwardDetail(bidNo, bidOrd);
  const data = extractData(r.data);
  const aw = data?.summary || {};
  const winnerBizNo = aw.winner_biz_no;
  const stage4Desc = aw.winner_name
    ? `${aw.winner_name} (${fmtRate(aw.award_rate)})`
    : "미낙찰/유찰";

  return (
    <>
      <Stage n={4} label="낙찰" ok={data?.found} desc={stage4Desc} />
      {/* Stage 5: NTS — winner_biz_no 의존 (자식 Suspense로 streaming) */}
      <Suspense fallback={<StageSkeleton n={5} label="낙찰자 NTS 검증" desc="—" />}>
        <StageNts winnerBizNo={winnerBizNo} />
      </Suspense>
    </>
  );
}

async function StageNts({ winnerBizNo }: { winnerBizNo?: string }) {
  if (!winnerBizNo) {
    return <Stage n={5} label="낙찰자 NTS 검증" ok={false} desc="—" inactive />;
  }
  const r = await checkBusinessStatus([winnerBizNo]);
  const data = extractData(r.data);
  const items = data?.items || [];
  return (
    <Stage n={5} label="낙찰자 NTS 검증" ok={items.length > 0} desc={ntsLabel(data)} />
  );
}

async function ActionLinks({ bidNo, bidOrd }: { bidNo: string; bidOrd: string }) {
  // 낙찰자 사업자번호와 발주기관명을 위한 두 도구 호출 (cache hit 0.5초)
  const [awardR, noticeR] = await Promise.all([
    getAwardDetail(bidNo, bidOrd),
    getBidNoticeDetail(bidNo, bidOrd),
  ]);
  const aw = extractData(awardR.data)?.summary || {};
  const nt = extractData(noticeR.data)?.summary || extractData(noticeR.data)?.raw || {};
  const winnerBizNo = aw.winner_biz_no;
  const instName = nt.inst_name || nt.ntceInsttNm;
  if (!winnerBizNo && !instName) return null;
  return (
    <section className="flex gap-2 text-sm">
      {winnerBizNo && (
        <a
          href={`/vendors/${winnerBizNo}`}
          className="rounded border px-3 py-2 hover:bg-[var(--color-bg-muted)]"
        >
          🔗 낙찰업체 프로필
        </a>
      )}
      {instName && (
        <a
          href={`/agencies?name=${encodeURIComponent(instName)}`}
          className="rounded border px-3 py-2 hover:bg-[var(--color-bg-muted)]"
        >
          🏛 발주기관 분석
        </a>
      )}
    </section>
  );
}

// === Stage / Skeleton 헬퍼 ===

function Stage({
  n,
  label,
  ok,
  desc,
  inactive,
}: {
  n: number;
  label: string;
  ok: boolean | undefined;
  desc?: string;
  inactive?: boolean;
}) {
  const status = inactive ? "○" : ok ? "✅" : "○";
  return (
    <div
      className={`flex items-center gap-3 rounded border px-4 py-2 ${
        ok ? "border-[var(--color-success)]" : ""
      }`}
    >
      <span className="font-mono text-xs">{n}</span>
      <span>{status}</span>
      <span className="font-medium">{label}</span>
      <span className="text-sm text-[var(--color-fg-muted)]">{desc}</span>
    </div>
  );
}

function StageSkeleton({ n, label, desc }: { n: number; label: string; desc?: string }) {
  // v22.4 패턴: cursor-wait + spin spinner + 단계 라벨
  return (
    <div className="flex cursor-wait items-center gap-3 rounded border bg-[var(--color-bg-muted)] px-4 py-2">
      <span className="font-mono text-xs">{n}</span>
      <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-[var(--color-fg-muted)] border-t-transparent" />
      <span className="font-medium">{label}</span>
      <span className="text-sm text-[var(--color-fg-muted)]">{desc} · 조회 중…</span>
    </div>
  );
}

function SummarySkeleton() {
  return (
    <div className="cursor-wait space-y-3 rounded-lg border bg-[var(--color-bg-muted)] p-4">
      <div className="flex items-center gap-3">
        <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-[var(--color-fg-muted)] border-t-transparent" />
        <span className="text-sm font-medium">요약 로딩 중 — 본 공고 단건 조회 (cache hit 시 0.5초)</span>
      </div>
      <div className="h-12 animate-pulse rounded bg-[var(--color-bg)]" />
    </div>
  );
}

// === 타입 + 유틸 ===

interface ParticipantRow {
  opening_rank?: number;
  participant_name?: string;
  participant_biz_no?: string;
  participant_bid_amount?: number;
  is_winner?: boolean;
}

function extractData(raw: unknown): Record<string, any> | null {
  if (!raw) return null;
  if (typeof raw === "object" && raw !== null) {
    const obj = raw as Record<string, unknown>;
    if (obj.content && Array.isArray(obj.content)) {
      const text = (obj.content[0] as { text?: string })?.text;
      if (text) {
        try {
          return JSON.parse(text);
        } catch {
          return null;
        }
      }
    }
    return obj as Record<string, any>;
  }
  return null;
}

function ntsLabel(stat: any): string {
  if (!stat?.items?.length) return "—";
  const first = stat.items[0];
  const code = first.b_stt_cd;
  if (code === "01") return "계속사업자 (정상)";
  if (code === "02") return "휴업";
  if (code === "03") return "폐업";
  return first.b_stt || "—";
}
