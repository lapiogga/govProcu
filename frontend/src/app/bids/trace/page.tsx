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
          공고번호 1개로 사전규격공개 → 입찰공고 → 개찰 → 낙찰자 결정 → 낙찰자 NTS 검증 → 계약 체결 6단계를 한 번에.
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

      {/* 6단계 타임라인 — F28: 시행령 표제어 정합 명칭 */}
      <section className="space-y-2">
        <Suspense fallback={<StageSkeleton n={1} label="사전규격공개" desc="등록 + 의견수렴" />}>
          <StagePreSpec bidNo={bidNo} bidOrd={bidOrd} />
        </Suspense>
        <Suspense fallback={<StageSkeleton n={2} label="입찰공고" desc="추정가" />}>
          <StageNotice bidNo={bidNo} bidOrd={bidOrd} />
        </Suspense>
        <Suspense fallback={<StageSkeleton n={3} label="개찰 + 응찰업체" desc="응찰자" />}>
          <StageParticipants bidNo={bidNo} bidOrd={bidOrd} />
        </Suspense>
        <Suspense fallback={<StageSkeleton n={4} label="낙찰자 결정" desc="결과" />}>
          <StageAwardAndNts bidNo={bidNo} bidOrd={bidOrd} />
        </Suspense>
        <Stage n={6} label="계약 체결" ok={false} desc="체결 후 추적 가능" inactive />
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
  // P30-R3 P1-03: r.ok === false 분기 — 통신 오류와 데이터 미발견 구분
  if (!r.ok) {
    return <StageError n={1} label="사전규격공개" error={r.error} />;
  }
  const data = extractData(r.data);
  // P30-R3 P1-04: backend note 필드 노출 — "왜" 비어있는지 사용자 안내
  return (
    <Stage
      n={1}
      label="사전규격공개"
      ok={data?.found}
      desc="등록 + 의견수렴"
      note={data?.note}
    />
  );
}

async function StageNotice({ bidNo, bidOrd }: { bidNo: string; bidOrd: string }) {
  const r = await getBidNoticeDetail(bidNo, bidOrd);
  if (!r.ok) {
    return <StageError n={2} label="입찰공고" error={r.error} />;
  }
  const data = extractData(r.data);
  const summary = data?.summary || {};
  const raw = data?.raw || {};
  return (
    <>
      <Stage
        n={2}
        label="입찰공고"
        ok={data?.found}
        desc={`추정가 ${fmtWon(summary.estimated_price ?? summary.presmptPrce)}`}
        note={data?.note}
      />
      {data?.found && <NoticeRequiredFields raw={raw} summary={summary} />}
    </>
  );
}

// F25: 시행령 제36조 입찰공고 필수항목 노출 — DOSSIER-LAW §4.1·§4.2.
// raw 필드 근거: poc4_용역.json (R25BK00755515).
function NoticeRequiredFields({ raw, summary }: { raw: any; summary: any }) {
  const opengDt = raw.opengDt || summary.opengDt;
  const opengPlce = raw.opengPlce || "";
  const bidBeginDt = raw.bidBeginDt;
  const bidClseDt = raw.bidClseDt || summary.deadline_date;
  const bidMethdNm = raw.bidMethdNm;
  const sucsfbidMthdNm = raw.sucsfbidMthdNm;
  const cntrctCnclsMthdNm = raw.cntrctCnclsMthdNm;
  const cmmnSpldmdMethdNm = raw.cmmnSpldmdMethdNm;
  const dcmtgOprtnDt = raw.dcmtgOprtnDt;
  const dcmtgOprtnPlce = raw.dcmtgOprtnPlce;
  const bidPrtcptFee = raw.bidPrtcptFee;
  const bidGrntymnyPaymntYn = raw.bidGrntymnyPaymntYn;
  const ntceInsttOfclNm = raw.ntceInsttOfclNm;
  const ntceInsttOfclTelNo = raw.ntceInsttOfclTelNo;
  const crdtrNm = raw.crdtrNm;
  const indstrytyLmtYn = raw.indstrytyLmtYn;
  const bidPrtcptLmtYn = raw.bidPrtcptLmtYn;
  const prdctClsfcLmtYn = raw.prdctClsfcLmtYn;
  const rgnLmtNm = raw.rgnLmtBidLocplcJdgmBssNm;
  const purchsObjPrdctList = raw.purchsObjPrdctList;

  const qualParts: string[] = [];
  if (bidPrtcptLmtYn === "Y") qualParts.push("참가제한");
  if (indstrytyLmtYn === "Y") qualParts.push("업종제한");
  if (prdctClsfcLmtYn === "Y") qualParts.push("물품분류제한");
  if (rgnLmtNm) qualParts.push(`지역제한(${rgnLmtNm})`);
  const qualText = qualParts.length > 0 ? qualParts.join(" · ") : "제한 없음 (일반)";

  return (
    <section className="ml-9 rounded border bg-[var(--color-bg-muted)] p-3 text-sm">
      <h4 className="mb-2 text-xs font-semibold text-[var(--color-fg-muted)]">
        입찰공고 필수항목 (시행령 제36조)
      </h4>
      <dl className="grid grid-cols-1 gap-x-6 gap-y-2 lg:grid-cols-2">
        <FieldRow label="입찰참가자격">{qualText}</FieldRow>
        <FieldRow label="낙찰자 결정방법">
          {sucsfbidMthdNm || cntrctCnclsMthdNm || "—"}
        </FieldRow>
        <FieldRow label="입찰서 제출방법">{bidMethdNm || "—"}</FieldRow>
        <FieldRow label="입찰 개시·마감">
          {bidBeginDt && bidClseDt
            ? `${fmtDate(bidBeginDt)} ~ ${fmtDate(bidClseDt)}`
            : bidClseDt
              ? `~ ${fmtDate(bidClseDt)}`
              : "—"}
        </FieldRow>
        <FieldRow label="개찰 일시">{opengDt ? fmtDate(opengDt) : "—"}</FieldRow>
        <FieldRow label="개찰 장소">{opengPlce || "전자조달시스템(나라장터)"}</FieldRow>
        <FieldRow label="입찰참가수수료">
          {bidPrtcptFee && Number(bidPrtcptFee) > 0 ? fmtWon(Number(bidPrtcptFee)) : "면제"}
        </FieldRow>
        <FieldRow label="입찰보증금">
          {bidGrntymnyPaymntYn === "Y" ? "납부 필요" : "면제 또는 별도 안내"}
        </FieldRow>
        <FieldRow label="현장설명">
          {dcmtgOprtnDt
            ? `${fmtDate(dcmtgOprtnDt)} ${dcmtgOprtnPlce || ""}`.trim()
            : "—"}
        </FieldRow>
        <FieldRow label="공동계약">
          {cmmnSpldmdMethdNm || "—"}
        </FieldRow>
        <FieldRow label="계약담당공무원">
          {ntceInsttOfclNm
            ? `${ntceInsttOfclNm}${ntceInsttOfclTelNo ? ` (${ntceInsttOfclTelNo})` : ""}`
            : crdtrNm || "—"}
        </FieldRow>
        <FieldRow label="목적물 명세">
          {purchsObjPrdctList || "—"}
        </FieldRow>
      </dl>
      <p className="mt-2 text-xs text-[var(--color-fg-muted)]">
        무효사유 등 상세는 입찰공고문 본문 참조 (시행령 제36조 제12호).
      </p>
    </section>
  );
}

function FieldRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-2">
      <dt className="min-w-[7rem] text-[var(--color-fg-muted)]">{label}</dt>
      <dd className="flex-1 break-words">{children}</dd>
    </div>
  );
}

async function StageParticipants({ bidNo, bidOrd }: { bidNo: string; bidOrd: string }) {
  const r = await listBidParticipants(bidNo, bidOrd);
  if (!r.ok) {
    return <StageError n={3} label="개찰 + 응찰업체" error={r.error} />;
  }
  const data = extractData(r.data);
  const items: ParticipantRow[] = data?.items || [];
  // P32-R2 (F30): G2B 비공개 API — R-prefix 케이스에서 participant_count(prtcptCnum)는 N건이지만
  // items는 낙찰자 1건만 (opengCorpInfo 응답 한계). UI에 명시 표시.
  const totalCount = data?.participant_count ?? items.length;
  const isPartialList = totalCount > items.length;
  return (
    <>
      <Stage
        n={3}
        label="개찰 + 응찰업체"
        ok={totalCount > 0}
        desc={`응찰자 ${totalCount}개사`}
        note={data?.note}
      />
      {items.length > 0 && (
        <section className="rounded-lg border">
          <h3 className="border-b px-4 py-2 text-sm font-medium">
            응찰업체 {totalCount}개사
            {isPartialList && (
              <span className="ml-2 text-xs font-normal text-[var(--color-fg-muted)]">
                (낙찰자 {items.length}건만 공개 — G2B 비공개 API)
              </span>
            )}
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
  if (!r.ok) {
    return <StageError n={4} label="낙찰자 결정" error={r.error} />;
  }
  const data = extractData(r.data);
  const aw = data?.summary || {};
  const winnerBizNo = aw.winner_biz_no;
  const stage4Desc = aw.winner_name
    ? `${aw.winner_name} (${fmtRate(aw.award_rate)})`
    : "미낙찰/유찰";

  return (
    <>
      <Stage
        n={4}
        label="낙찰자 결정"
        ok={data?.found}
        desc={stage4Desc}
        note={data?.note}
      />
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
  if (!r.ok) {
    return <StageError n={5} label="낙찰자 NTS 검증" error={r.error} />;
  }
  const data = extractData(r.data);
  const items = data?.items || [];
  return (
    <Stage
      n={5}
      label="낙찰자 NTS 검증"
      ok={items.length > 0}
      desc={ntsLabel(data)}
      note={data?.note}
    />
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
  note,
}: {
  n: number;
  label: string;
  ok: boolean | undefined;
  desc?: string;
  inactive?: boolean;
  note?: string;
}) {
  const status = inactive ? "○" : ok ? "✅" : "○";
  return (
    <div
      className={`rounded border px-4 py-2 ${
        ok ? "border-[var(--color-success)]" : ""
      }`}
    >
      <div className="flex items-center gap-3">
        <span className="font-mono text-xs">{n}</span>
        <span>{status}</span>
        <span className="font-medium">{label}</span>
        <span className="text-sm text-[var(--color-fg-muted)]">{desc}</span>
      </div>
      {/* P30-R3 P1-04: backend note (미발견 사유) 노출 — F2 사용자 사례 직결 */}
      {note && (
        <p className="mt-1 ml-9 text-xs text-[var(--color-fg-muted)]">
          {note}
        </p>
      )}
    </div>
  );
}

// P30-R3 P1-03: backend 통신 오류 (r.ok=false) 전용 — 데이터 미발견과 구분
function StageError({
  n,
  label,
  error,
}: {
  n: number;
  label: string;
  error?: string;
}) {
  return (
    <div className="rounded border border-[var(--color-danger)] bg-[var(--color-danger-bg,#fee2e2)] px-4 py-2">
      <div className="flex items-center gap-3">
        <span className="font-mono text-xs">{n}</span>
        <span>⚠</span>
        <span className="font-medium">{label}</span>
        <span className="text-sm text-[var(--color-danger)]">통신 오류</span>
      </div>
      {error && (
        <p className="mt-1 ml-9 text-xs text-[var(--color-danger)]">
          {error}
        </p>
      )}
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
        <span className="text-sm font-medium">요약 로딩 중 — 입찰공고 단건 조회 (cache hit 시 0.5초)</span>
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
  // P0-A (Phase 30): backend `check_business_status` 정규화 키 우선, raw 폴백
  const code = first.status_code || first.b_stt_cd || first.raw?.b_stt_cd;
  if (code === "01") return "계속사업자 (정상)";
  if (code === "02") return "휴업";
  if (code === "03") return "폐업";
  return first.status || first.b_stt || first.raw?.b_stt || "—";
}
