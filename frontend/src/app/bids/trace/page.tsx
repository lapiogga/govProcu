/**
 * 입찰 상세 추적 ★ — `trace_bid_lifecycle`
 * UI Phase B 핵심 화면. 6단계 Streaming Timeline.
 *
 * URL: /bids/trace?no=20240315678&ord=00
 */
import { Suspense } from "react";
import { traceBidLifecycle } from "@/lib/actions";
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
          공고번호 1개로 사전규격 → 본 공고 → 개찰 → 낙찰 → 응찰업체 → 낙찰자
          NTS 검증 6단계를 한 번에.
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
          MCP `trace_bid_lifecycle` 호출 중…
        </p>
      </header>

      <Suspense fallback={<TimelineSkeleton />}>
        <Timeline bidNo={bidNo} bidOrd={bidOrd} />
      </Suspense>
    </main>
  );
}

async function Timeline({ bidNo, bidOrd }: { bidNo: string; bidOrd: string }) {
  const result = await traceBidLifecycle(bidNo, bidOrd);

  if (!result.ok) {
    return (
      <div className="rounded border border-[var(--color-danger)] p-4 text-sm">
        오류: {result.error}
      </div>
    );
  }

  // MCP 응답 구조: {content: [{type:'text', text:'<JSON>'}]} or 직접 dict
  const data = extractData(result.data);
  if (!data) {
    return (
      <div className="rounded border p-4 text-sm">
        응답 데이터 없음. MCP 서버 상태를 확인하세요.
      </div>
    );
  }

  const summary = data.summary || {};
  const stages = data.stages || {};

  return (
    <div className="space-y-4">
      {/* 요약 */}
      <section className="rounded-lg border bg-[var(--color-bg-muted)] p-4">
        <h2 className="text-lg font-medium">{summary.title || "(제목 없음)"}</h2>
        <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-2 text-sm lg:grid-cols-4">
          <div>
            <dt className="text-[var(--color-fg-muted)]">발주기관</dt>
            <dd className="font-medium">
              <AgencyLink name={summary.inst_name} />
            </dd>
          </div>
          <div>
            <dt className="text-[var(--color-fg-muted)]">업종</dt>
            <dd>{summary.biz_type || "—"}</dd>
          </div>
          <div>
            <dt className="text-[var(--color-fg-muted)]">추정가</dt>
            <dd className="tabular-nums font-medium">
              {fmtWon(summary.estimated_price)}
            </dd>
          </div>
          <div>
            <dt className="text-[var(--color-fg-muted)]">응찰자수</dt>
            <dd className="tabular-nums">{summary.participant_count ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-[var(--color-fg-muted)]">공고일</dt>
            <dd className="tabular-nums">{fmtDate(summary.publish_date)}</dd>
          </div>
          <div>
            <dt className="text-[var(--color-fg-muted)]">개찰일</dt>
            <dd className="tabular-nums">{fmtDate(summary.open_date)}</dd>
          </div>
          <div>
            <dt className="text-[var(--color-fg-muted)]">낙찰자</dt>
            <dd className="font-medium">
              <VendorLink
                bizNo={summary.winner_biz_no}
                name={summary.winner_name}
              />
            </dd>
          </div>
          <div>
            <dt className="text-[var(--color-fg-muted)]">낙찰가/낙찰률</dt>
            <dd className="tabular-nums font-medium">
              {fmtWon(summary.award_amount)} / {fmtRate(summary.award_rate)}
            </dd>
          </div>
        </dl>
      </section>

      {/* 6단계 타임라인 */}
      <section className="space-y-2">
        <Stage
          n={1}
          label="사전규격"
          ok={stages.pre_specification?.found}
          desc="등록 + 의견수렴"
        />
        <Stage
          n={2}
          label="본 공고"
          ok={stages.bid_notice?.found}
          desc={`추정가 ${fmtWon(summary.estimated_price)}`}
        />
        <Stage
          n={3}
          label="개찰 + 응찰업체"
          ok={(stages.participants?.items?.length ?? 0) > 0}
          desc={`응찰자 ${stages.participants?.participant_count ?? 0}개사`}
        />
        <Stage
          n={4}
          label="낙찰"
          ok={stages.award?.found}
          desc={
            stages.award?.summary?.winner_name
              ? `${stages.award.summary.winner_name} (${fmtRate(stages.award.summary.award_rate)})`
              : "미낙찰/유찰"
          }
        />
        <Stage
          n={5}
          label="낙찰자 NTS 검증"
          ok={!!stages.winner_nts_status?.items?.length}
          desc={ntsLabel(stages.winner_nts_status)}
        />
        <Stage n={6} label="계약" ok={false} desc="체결 후 추적 가능" inactive />
      </section>

      {/* 응찰업체 표 */}
      {stages.participants?.items?.length > 0 && (
        <section className="rounded-lg border">
          <h3 className="border-b px-4 py-2 text-sm font-medium">
            응찰업체 {stages.participants.items.length}개사
          </h3>
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
              {stages.participants.items.map((p: ParticipantRow, i: number) => (
                <tr key={i} className="border-t">
                  <td className="px-3 py-2 tabular-nums">
                    {p.opening_rank ?? "—"}
                  </td>
                  <td className="px-3 py-2">
                    <VendorLink
                      bizNo={p.participant_biz_no}
                      name={p.participant_name}
                    />
                  </td>
                  <td className="px-3 py-2 tabular-nums">
                    <VendorLink
                      bizNo={p.participant_biz_no}
                      name={fmtBizNo(p.participant_biz_no)}
                    />
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {fmtWon(p.participant_bid_amount)}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {p.is_winner ? "🏆" : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* 액션 */}
      <section className="flex gap-2 text-sm">
        {summary.winner_biz_no && (
          <a
            href={`/vendors/${summary.winner_biz_no}`}
            className="rounded border px-3 py-2 hover:bg-[var(--color-bg-muted)]"
          >
            🔗 낙찰업체 프로필
          </a>
        )}
        {summary.inst_name && (
          <a
            href={`/agencies?name=${encodeURIComponent(summary.inst_name)}`}
            className="rounded border px-3 py-2 hover:bg-[var(--color-bg-muted)]"
          >
            🏛 발주기관 분석
          </a>
        )}
      </section>
    </div>
  );
}

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

function TimelineSkeleton() {
  // v22.4 (F6): 사용자 인지 강화 — cursor-wait + 큰 spinner + 진행 메시지
  return (
    <div className="cursor-wait space-y-4">
      <div className="flex items-center gap-3 rounded border border-[var(--color-warning,#f59e0b)] bg-[var(--color-warning-bg,#fef3c7)] p-4">
        <span className="inline-block h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-[var(--color-warning,#f59e0b)] border-t-transparent" />
        <span className="text-sm font-medium text-[var(--color-fg)]">
          조회 중 — G2B API 6단계 병렬 호출. R 형식 채번은 연도 범위 폴백(12 chunks)으로 30~90초 소요 가능.
        </span>
      </div>
      <div className="space-y-2">
        {[1, 2, 3, 4, 5, 6].map((n) => (
          <div
            key={n}
            className="flex h-12 animate-pulse items-center gap-3 rounded border bg-[var(--color-bg-muted)] px-4"
          >
            <span className="font-mono text-xs">{n}</span>
            <span>⏳</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface ParticipantRow {
  opening_rank?: number;
  participant_name?: string;
  participant_biz_no?: string;
  participant_bid_amount?: number;
  is_winner?: boolean;
}

interface TraceData {
  summary?: Record<string, unknown> & {
    title?: string;
    inst_name?: string;
    biz_type?: string;
    estimated_price?: number;
    participant_count?: number;
    publish_date?: string;
    open_date?: string;
    winner_name?: string;
    winner_biz_no?: string;
    award_amount?: number;
    award_rate?: string;
  };
  stages?: Record<string, any>;
}

function extractData(raw: unknown): TraceData | null {
  if (!raw) return null;
  // MCP는 {content: [{type:'text', text: JSON.stringify(...)}]} 또는 직접 dict
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
    return obj as TraceData;
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
