/**
 * 업체 프로필 — `vendor_profile` (W2)
 * NTS 진위 + 기간 내 입찰/응찰/개찰/낙찰 통계.
 */
import { Suspense } from "react";
import { getVendorProfile } from "@/lib/actions";
import { fmtWon, fmtRate, fmtBizNo, fmtDate } from "@/lib/format";
import { VendorAwardChart } from "@/components/charts/VendorAwardChart";
import { AgencyLink, BidLink } from "@/components/EntityLink";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

function defaultFromY(): string {
  // v29.2: 1년 default — false-negative 회피. 36초 소요는 cursor-wait + spinner로 안내.
  const d = new Date();
  d.setDate(d.getDate() - 365);
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
}

function defaultTo(): string {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
}

export default async function VendorPage(props: {
  params: Promise<{ bizNo: string }>;
  searchParams: Promise<{ from?: string; to?: string }>;
}) {
  const { bizNo } = await props.params;
  const sp = await props.searchParams;
  // v29.2: from/to 미입력 시 1년 default 적용 (NameSearchResults와 정합)
  const from = sp.from || defaultFromY();
  const to = sp.to || defaultTo();

  return (
    <main className="space-y-6">
      <header className="space-y-3">
        <div>
          <h1 className="text-2xl font-semibold">
            업체 프로필: {fmtBizNo(bizNo)}
          </h1>
          <p className="text-xs text-[var(--color-fg-muted)]">
            NTS 진위 + 입찰/응찰/개찰/낙찰 통합 (vendor_profile)
          </p>
        </div>
        {/* P30-R5 P1-08: 기간 변경 form — URL 수동 편집 회피 */}
        <form
          action={`/vendors/${bizNo}`}
          className="flex flex-wrap items-center gap-2 rounded border bg-[var(--color-bg-muted)] p-3"
        >
          <label className="text-xs text-[var(--color-fg-muted)]">조회 기간</label>
          <Input
            name="from"
            defaultValue={from}
            placeholder="from YYYYMMDD"
            pattern="\d{8}"
            className="max-w-[140px]"
          />
          <span className="text-xs text-[var(--color-fg-muted)]">~</span>
          <Input
            name="to"
            defaultValue={to}
            placeholder="to YYYYMMDD"
            pattern="\d{8}"
            className="max-w-[140px]"
          />
          <Button type="submit" variant="outline" size="sm">
            재조회
          </Button>
          <span className="ml-auto text-xs text-[var(--color-fg-muted)]">
            현재: {from} ~ {to} (1년 default)
          </span>
        </form>
      </header>

      <Suspense fallback={<ProfileSkeleton />}>
        <Profile bizNo={bizNo} from={from} to={to} />
      </Suspense>
    </main>
  );
}

async function Profile({
  bizNo,
  from,
  to,
}: {
  bizNo: string;
  from?: string;
  to?: string;
}) {
  const result = await getVendorProfile(bizNo, from, to);

  if (!result.ok) {
    return (
      <div className="rounded border border-[var(--color-danger)] p-4 text-sm">
        오류: {result.error}
      </div>
    );
  }

  const data = extractData(result.data);
  if (!data) {
    return (
      <div className="rounded-lg border border-[var(--color-danger)] p-4 text-sm">
        <p className="font-medium">응답 파싱 실패</p>
        <p className="mt-1 text-[var(--color-fg-muted)]">
          backend가 응답을 보냈으나 frontend가 파싱하지 못했습니다.
          MCP 응답 구조 확인 또는 backend 로그 점검.
        </p>
      </div>
    );
  }

  const summary = data.summary || {};
  const sections = data.sections || {};

  // v22.5 (F7): 모든 영역이 비어있는지 검증 — backend는 정상 응답이지만 NTS 키/EVAL 키 미설정으로 sections 빈 응답 케이스
  const hasAnyData =
    (sections.awards?.items?.length ?? 0) > 0 ||
    (sections.participations?.items?.length ?? 0) > 0 ||
    (sections.openings?.items?.length ?? 0) > 0 ||
    (sections.bids?.items?.length ?? 0) > 0 ||
    !!summary.nts_status_code;

  return (
    <div className="space-y-4">
      {/* v22.5 (F7): 빈 응답 명시 안내 (사용자 "전혀 표시가 안됨" 인식 차단) */}
      {!hasAnyData && (
        <div className="rounded-lg border border-[var(--color-warning,#f59e0b)] bg-[var(--color-warning-bg,#fef3c7)] p-4 text-sm">
          <p className="font-medium">데이터 없음</p>
          <p className="mt-1 text-[var(--color-fg-muted)]">
            이 사업자번호로 NTS·낙찰·응찰·개찰·입찰 어느 영역에서도 데이터가 조회되지 않았습니다.
          </p>
          <p className="mt-2 text-xs font-medium">가능 원인</p>
          <ul className="ml-4 list-disc text-xs text-[var(--color-fg-muted)]">
            <li>사업자번호 잘못 입력 (10자리 숫자 정확 확인)</li>
            <li>지정 기간 내 활동 없음 — 기간을 확장하거나 default 사용</li>
            <li>NTS 진위확인 API 키 미설정 (`.env` 의 `NTS_API_KEY`)</li>
            <li>V1·V2·V3 도구는 EVAL 키 발급 후 활성화 — 현재는 V4(awards) 영역만 작동</li>
          </ul>
          <p className="mt-2 text-xs">
            구현 상태:{" "}
            <span className="font-mono">{summary.implementation_status || "—"}</span>
          </p>
        </div>
      )}

      {/* NTS 검증 */}
      <section className="rounded-lg border bg-[var(--color-bg-muted)] p-4">
        <h2 className="mb-2 text-sm font-medium">NTS 검증</h2>
        <p className="text-sm">
          상태 코드: <span className="font-mono">{summary.nts_status_code || "—"}</span>{" "}
          {summary.nts_status_code === "01" && (
            <span className="text-[var(--color-success)]">✅ 계속사업자</span>
          )}
          {!summary.nts_status_code && (
            <span className="text-[var(--color-fg-muted)]">— (NTS 키 미설정 또는 응답 없음)</span>
          )}
        </p>
      </section>

      {/* 통계 */}
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Stat label="입찰" value={summary.bids_count} />
        <Stat label="응찰" value={summary.participations_count} />
        <Stat label="개찰참여" value={summary.openings_count} />
        <Stat label="낙찰" value={summary.awards_count} />
        <Stat
          label="낙찰합계"
          value={fmtWon(summary.awards_total_won)}
          tabular
        />
      </section>

      {summary.win_rate_pct != null && (
        <section className="rounded-lg border p-4">
          <p className="text-sm">
            낙찰률:{" "}
            <span className="font-mono text-lg font-medium">
              {summary.win_rate_pct.toFixed(2)}%
            </span>
            {" · "}
            평균 낙찰가: {fmtWon(summary.awards_avg_won)}
          </p>
        </section>
      )}

      {/* 월별 낙찰 추이 */}
      {sections.awards?.items?.length > 0 && (
        <section className="rounded-lg border p-4">
          <h3 className="mb-3 text-sm font-medium">월별 낙찰 추이</h3>
          <VendorAwardChart items={sections.awards.items} />
        </section>
      )}

      {/* 최근 낙찰 5건 */}
      {sections.awards?.items?.length > 0 && (
        <section className="rounded-lg border">
          <h3 className="flex flex-wrap items-center gap-2 border-b px-4 py-2 text-sm font-medium">
            <span>최근 낙찰 {sections.awards.items.length}건</span>
            {/* P30-R3 P1-06: has_more / scan_coverage_pct 노출 — Phase 29 backend fix 사용자 도달 */}
            {typeof sections.awards.scan_coverage_pct === "number" && (
              <span
                className={
                  sections.awards.has_more || sections.awards.scan_coverage_pct < 100
                    ? "rounded border border-[var(--color-warning,#f59e0b)] bg-[var(--color-warning-bg,#fef3c7)] px-2 py-0.5 text-xs font-medium"
                    : "rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-0.5 text-xs text-[var(--color-fg-muted)]"
                }
              >
                스캔 {sections.awards.scan_coverage_pct}%
                {sections.awards.has_more && " — 추가 검색 권장"}
              </span>
            )}
            {sections.awards.has_more &&
              typeof sections.awards.scan_coverage_pct !== "number" && (
                <span className="rounded border border-[var(--color-warning,#f59e0b)] bg-[var(--color-warning-bg,#fef3c7)] px-2 py-0.5 text-xs font-medium">
                  추가 결과 있음 — 기간 분할 권장
                </span>
              )}
          </h3>
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-bg-muted)]">
              <tr>
                <th className="px-3 py-2 text-left">개찰일</th>
                <th className="px-3 py-2 text-left">공고제목</th>
                <th className="px-3 py-2 text-left">발주기관</th>
                <th className="px-3 py-2 text-right">낙찰가</th>
                <th className="px-3 py-2 text-right">낙찰률</th>
              </tr>
            </thead>
            <tbody>
              {sections.awards.items.slice(0, 10).map((a: any, i: number) => (
                <tr key={i} className="border-t">
                  <td className="px-3 py-2 tabular-nums">
                    {fmtDate(a.open_date)}
                  </td>
                  <td className="px-3 py-2">
                    <BidLink
                      bidNo={a.bid_notice_no}
                      ord={a.bid_ord}
                      title={a.bid_title}
                    />
                  </td>
                  <td className="px-3 py-2">
                    <AgencyLink name={a.inst_name} />
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {fmtWon(a.award_amount)}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {fmtRate(a.award_rate)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section className="text-xs text-[var(--color-fg-muted)]">
        구현 상태: {summary.implementation_status || "—"}
      </section>
    </div>
  );
}

function Stat({
  label,
  value,
  tabular,
}: {
  label: string;
  value: number | string | undefined;
  tabular?: boolean;
}) {
  return (
    <div className="rounded border p-3">
      <div className="text-xs text-[var(--color-fg-muted)]">{label}</div>
      <div className={`mt-1 text-lg font-medium ${tabular ? "tabular-nums" : ""}`}>
        {value ?? "—"}
      </div>
    </div>
  );
}

function ProfileSkeleton() {
  // P30-R5 P1-07: 36초 대기 loading UX 강화 — spinner + 진행 메시지 + cursor-wait
  return (
    <div className="cursor-wait space-y-3">
      <div className="flex items-center gap-3 rounded border bg-[var(--color-bg-muted)] p-4">
        <svg
          className="h-5 w-5 animate-spin text-[var(--color-primary)]"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8 8 8 0 008 8v-4l-3 3 3 3v-4a8 8 0 008-8h-4z"
          />
        </svg>
        <div>
          <p className="text-sm font-medium">검색 중 (최대 1분 소요)</p>
          <p className="text-xs text-[var(--color-fg-muted)]">
            G2B 1년 데이터 12회 chunk × 4 endpoint 병렬 — 페이지를 닫지 마세요.
          </p>
        </div>
      </div>
      <div className="h-20 animate-pulse rounded bg-[var(--color-bg-muted)]" />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        {[1, 2, 3, 4, 5].map((n) => (
          <div
            key={n}
            className="h-16 animate-pulse rounded bg-[var(--color-bg-muted)]"
          />
        ))}
      </div>
    </div>
  );
}

function extractData(raw: unknown): any {
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
    return obj;
  }
  return null;
}
