/**
 * 입찰 검색 — `search_bid_notices`
 *
 * P31-R3 (F23, F26): G2B 표준 UX 정합 검색폼.
 * - 업무구분 5체크박스 다중 선택 (공사/물품/일반용역/기술용역/기타) — 비활성 옵션(민간) 제거
 * - 업무여부 외자 토글 — 비활성 옵션(비축/리스) 제거
 * - 업종 indstryty_cd 4자리 단순 input (자동완성 모달은 R4 분리)
 * - 발주기관 단일 input (공고기관/수요기관 통합 LIKE — backend fan-out)
 * - 결과 테이블: 공고기관(ntceInsttNm) / 수요기관(dminsttNm) 분리 + 업무구분(srvce_div 우선)
 */
import { Suspense } from "react";
import { searchBidNotices } from "@/lib/actions";
import { fmtWon, fmtDate } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { BidLink, AgencyLink } from "@/components/EntityLink";
import { SortMenu, type SortKey } from "./sort-menu";

const VALID_SORTS: SortKey[] = [
  "publish_desc",
  "publish_asc",
  "deadline",
  "amount_desc",
  "amount_asc",
];

// P31-R3: 업무구분 5종 (민간 비활성 제거)
const BIZ_TYPE_OPTIONS = ["공사", "물품", "일반용역", "기술용역", "기타"] as const;
type BizTypeOption = (typeof BIZ_TYPE_OPTIONS)[number];

function parseSort(raw: string | undefined): SortKey {
  if (raw && (VALID_SORTS as string[]).includes(raw)) return raw as SortKey;
  return "publish_desc";
}

/**
 * P31-R4.6 (hot-fix err-91): searchParams의 biz_types 파싱.
 * Next.js form GET method + checkbox name="biz_types" 다중 선택 시
 * searchParams는 string[] 반환 → raw.split(",") TypeError 발생.
 * - string[] (다중 체크박스) / string (CSV) / undefined 모두 처리.
 * - 후방호환: 기존 단일 `type` 파라미터도 수용.
 */
function parseBizTypes(
  raw: string | string[] | undefined,
  legacyType: string | undefined,
): BizTypeOption[] {
  const out: BizTypeOption[] = [];
  const allowed = BIZ_TYPE_OPTIONS as readonly string[];

  // 다중 체크박스 → string[]
  if (Array.isArray(raw)) {
    for (const part of raw) {
      if (typeof part !== "string") continue;
      const v = part.trim();
      if (allowed.includes(v)) out.push(v as BizTypeOption);
    }
  }
  // CSV 또는 단일 string
  else if (typeof raw === "string" && raw) {
    for (const part of raw.split(",")) {
      const v = part.trim();
      if (allowed.includes(v)) out.push(v as BizTypeOption);
    }
  }
  // legacyType fallback (구 단일 type=용역)
  else if (legacyType) {
    if (legacyType === "용역") {
      out.push("일반용역", "기술용역");
    } else if (allowed.includes(legacyType)) {
      out.push(legacyType as BizTypeOption);
    }
  }
  return out;
}

/**
 * P31-R3: 선택된 업무구분 + 외자 토글을 backend `biz_type` 단일 인자로 매핑.
 * - 일반용역/기술용역 둘 다 / 둘 중 하나 → backend "용역" (frontend client-side filter)
 * - 단일 종 → 그대로 전달 (공사/물품/기타)
 * - 0개 선택 + 외자 only → "외자"
 * - 외자 + 다른 종 → biz_type=None (전체 fan-out, 외자 포함됨)
 * - 0개 선택 + 외자 미선택 → biz_type=None (전체 5종 fan-out)
 * - 2종 이상 + 외자 미선택 → biz_type=None (전체 fan-out, 다른 종 결과는 client-side에서 그대로 통과)
 *
 * 단순화 규칙: backend는 "공사"/"용역"/"물품"/"외자"/"기타" 또는 None 만 수용.
 * 정확한 다종 fan-out 매핑은 backend가 None 단일 인자 → 5종 endpoint 병합으로 처리.
 */
function resolveBackendBizType(
  selected: BizTypeOption[],
  includeFrgcpt: boolean,
): string | undefined {
  const hasService = selected.includes("일반용역") || selected.includes("기술용역");
  const nonService = selected.filter((v) => v !== "일반용역" && v !== "기술용역");

  // 외자만 단독 선택
  if (selected.length === 0 && includeFrgcpt) return "외자";

  // 단일 종 (외자 미포함, 일반/기술용역 단독 또는 그 외 1종)
  if (!includeFrgcpt) {
    if (selected.length === 0) return undefined; // 전체
    if (hasService && nonService.length === 0) return "용역"; // 일반/기술용역만
    if (!hasService && nonService.length === 1) return nonService[0];
  }

  // 그 외 (다종 / 외자 + 다른 종) → 전체 fan-out
  return undefined;
}

function sortItems(items: Bid[], key: SortKey, today: string): Bid[] {
  const out = [...items];
  switch (key) {
    case "publish_asc":
      return out.sort((a, b) =>
        (a.publish_date || "").localeCompare(b.publish_date || ""),
      );
    case "deadline": {
      // 5/3 N42 fix: 미래 마감 가까운 순 → 과거 마감 → 빈 마감 (3-tier)
      // deadline_date 는 보통 "YYYYMMDDHHMM" 또는 "YYYYMMDD HHMM". 앞 8자리만 비교.
      const tier = (d?: string): number => {
        if (!d) return 2; // 빈 값 → 마지막
        const ymd = d.replace(/\D/g, "").slice(0, 8);
        if (!ymd) return 2;
        return ymd >= today ? 0 : 1; // 미래 0, 과거 1
      };
      return out.sort((a, b) => {
        const ta = tier(a.deadline_date);
        const tb = tier(b.deadline_date);
        if (ta !== tb) return ta - tb;
        const da = (a.deadline_date || "").replace(/\D/g, "").slice(0, 8);
        const db = (b.deadline_date || "").replace(/\D/g, "").slice(0, 8);
        // tier 0 (미래): 가까운 순 (asc), tier 1 (과거): 최근 순 (desc)
        if (ta === 0) return da.localeCompare(db);
        return db.localeCompare(da);
      });
    }
    case "amount_desc":
      return out.sort(
        (a, b) => (b.estimated_price ?? 0) - (a.estimated_price ?? 0),
      );
    case "amount_asc":
      return out.sort(
        (a, b) => (a.estimated_price ?? 0) - (b.estimated_price ?? 0),
      );
    default:
      return out.sort((a, b) =>
        (b.publish_date || "").localeCompare(a.publish_date || ""),
      );
  }
}

function todayYYYYMMDD(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}${m}${day}`;
}

function defaultBidsFrom(): string {
  // /bids default = 오늘-30일 (라이브 측정 기반, P99 4.2초)
  const d = new Date();
  d.setDate(d.getDate() - 30);
  return formatYYYYMMDD2(d);
}

function formatYYYYMMDD2(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}${m}${day}`;
}

interface Bid {
  bid_no: string;
  bid_ord?: string;
  title?: string;
  inst_name?: string;
  biz_type?: string;
  srvce_div?: string;       // P31-R2: "일반용역" / "기술용역"
  ppsw_gnrl_yn?: string;    // P31-R2: Y/N
  estimated_price?: number;
  publish_date?: string;
  deadline_date?: string;
  raw?: Record<string, unknown> | null; // ntceInsttNm/dminsttNm 직접 활용 (F26)
}

export default async function BidsPage(props: {
  searchParams: Promise<{
    q?: string;
    type?: string;        // 후방호환 (구: 단일 select)
    biz_types?: string | string[];   // P31-R4.6: form 다중 체크박스 → string[] 가능
    frgcpt?: string;      // P31-R3: 외자 토글 ("1")
    indstryty?: string;   // P31-R3: 업종 코드 4자리
    inst?: string;
    from?: string;
    to?: string;
    sort?: string;
    page?: string;
    deep?: string;
  }>;
}) {
  const sp = await props.searchParams;

  // P31-R3: biz_types 다중 + frgcpt 토글 + indstryty
  const selectedBizTypes = parseBizTypes(sp.biz_types, sp.type);
  const includeFrgcpt = sp.frgcpt === "1";
  const indstrytyCd = (sp.indstryty || "").trim();

  const hasQuery = !!(
    sp.q ||
    sp.biz_types ||
    sp.type ||
    sp.frgcpt ||
    sp.indstryty ||
    sp.inst ||
    sp.from ||
    sp.to
  );
  const sortKey = parseSort(sp.sort);
  const page = Math.max(1, parseInt(sp.page || "1", 10) || 1);
  // 5/3 N40: deep=1 → scan_pages=5 (LIKE 매칭률↑), default scan_pages=1
  const scanPages = sp.deep === "1" ? 5 : 1;
  // 5/3 N42: 라이브 측정 기반 default 30일 (P99 4.2초). 사용자 미입력 시 자동 적용.
  const dateFrom = sp.from || (hasQuery ? defaultBidsFrom() : undefined);
  const dateTo = sp.to || (hasQuery ? todayYYYYMMDD() : undefined);

  // backend로 전달할 단일 biz_type
  const backendBizType = resolveBackendBizType(selectedBizTypes, includeFrgcpt);

  // 5/3 N42 v12: 1개월 초과 입력 시 timeout 위험 안내
  const rangeDays = (() => {
    if (!dateFrom || !dateTo) return 0;
    try {
      const f = new Date(`${dateFrom.slice(0, 4)}-${dateFrom.slice(4, 6)}-${dateFrom.slice(6, 8)}`);
      const t = new Date(`${dateTo.slice(0, 4)}-${dateTo.slice(4, 6)}-${dateTo.slice(6, 8)}`);
      return Math.round((t.getTime() - f.getTime()) / (1000 * 60 * 60 * 24));
    } catch {
      return 0;
    }
  })();
  const isLargeRange = rangeDays > 31;
  const chunks = Math.max(1, Math.ceil(rangeDays / 31));
  // 단일 endpoint(특정 biz_type) vs 전체 5종 fan-out 추정
  const endpointCount = backendBizType ? 1 : 5;
  const estimatedSec = chunks * (scanPages === 1 ? 5 : 22) * endpointCount;

  return (
    <main className="space-y-4">
      <header className="flex items-start justify-between">
        <h1 className="text-2xl font-semibold">입찰 검색</h1>
        {hasQuery && <SortMenu current={sortKey} />}
      </header>

      <Card>
        <CardContent className="p-4">
          <form action="/bids" className="space-y-3">
            {/* 1행: 키워드 + 발주기관 + 업종 코드 + 검색 */}
            <div className="grid grid-cols-1 gap-2 md:grid-cols-5">
              <Input
                name="q"
                defaultValue={sp.q}
                placeholder="공고명 (예: 정보화 시스템 구축)"
                className="md:col-span-2"
              />
              <Input
                name="inst"
                defaultValue={sp.inst}
                placeholder="발주기관 (공고/수요 통합, 2자+)"
                minLength={2}
              />
              <Input
                name="indstryty"
                defaultValue={sp.indstryty}
                placeholder="업종 코드 4자리 (예: 0036)"
                pattern="\d{4}"
                title="업종 코드 4자리 (미입력 = 전체)"
                maxLength={4}
              />
              <Button type="submit">검색</Button>
            </div>

            {/* 2행: 업무구분 5체크박스 + 외자 토글 */}
            <fieldset className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded border border-[var(--color-border)] bg-[var(--color-bg-muted)] px-3 py-2 text-sm">
              <legend className="px-1 text-xs font-medium text-[var(--color-fg-muted)]">
                업무구분 (다중 선택, 미선택 = 전체)
              </legend>
              {BIZ_TYPE_OPTIONS.map((opt) => (
                <label key={opt} className="flex items-center gap-1">
                  <input
                    type="checkbox"
                    name="biz_types"
                    value={opt}
                    defaultChecked={selectedBizTypes.includes(opt)}
                    className="h-3.5 w-3.5"
                  />
                  {opt}
                </label>
              ))}
              <span className="ml-auto flex items-center gap-3 border-l border-[var(--color-border)] pl-3">
                <span className="text-xs text-[var(--color-fg-muted)]">업무여부</span>
                <label className="flex items-center gap-1">
                  <input
                    type="checkbox"
                    name="frgcpt"
                    value="1"
                    defaultChecked={includeFrgcpt}
                    className="h-3.5 w-3.5"
                  />
                  외자
                </label>
              </span>
            </fieldset>

            {/* 3행: 기간 + 깊은 검색 */}
            <div className="grid grid-cols-1 gap-2 md:grid-cols-5">
              <Input name="from" defaultValue={sp.from} placeholder="YYYYMMDD (시작)" />
              <Input name="to" defaultValue={sp.to} placeholder="YYYYMMDD (종료)" />
              <label className="flex items-center gap-1 text-xs text-[var(--color-fg-muted)] md:col-span-3">
                <input
                  type="checkbox"
                  name="deep"
                  value="1"
                  defaultChecked={sp.deep === "1"}
                  className="h-3.5 w-3.5"
                />
                깊은 검색(5x, LIKE 매칭률↑)
              </label>
            </div>

            <input type="hidden" name="sort" value={sortKey} />
            <input type="hidden" name="page" value="1" />
          </form>
        </CardContent>
      </Card>

      {hasQuery ? (
        <>
          {isLargeRange && (
            <div className="rounded border border-[var(--color-warning,#f59e0b)] bg-[var(--color-warning-bg,#fef3c7)] p-3 text-sm">
              <strong>⚠ 큰 범위 입력 ({Math.round(rangeDays / 31 * 10) / 10}개월)</strong>
              {" "}— 응답 약 {estimatedSec}초 예상 (1개월 청크 {chunks}회{!backendBizType ? " × 5 endpoint" : ""}{scanPages > 1 ? ` × deep ${scanPages}` : ""}). G2B 1개월 제약 자동 분할.
            </div>
          )}
          <Suspense fallback={<TableSkeleton />}>
            <Results
              keyword={sp.q}
              biz_type={backendBizType}
              inst_name={sp.inst}
              indstryty_cd={indstrytyCd || undefined}
              date_from={dateFrom}
              date_to={dateTo}
              sort={sortKey}
              page={page}
              scanPages={scanPages}
              selectedBizTypes={selectedBizTypes}
              sp={sp}
            />
          </Suspense>
        </>
      ) : (
        <p className="text-sm text-[var(--color-fg-muted)]">
          검색 조건을 입력하세요. 예: 키워드 + 업무구분 + 기간.
        </p>
      )}
    </main>
  );
}

interface ResultsParams {
  keyword?: string;
  biz_type?: string;
  inst_name?: string;
  indstryty_cd?: string;
  date_from?: string;
  date_to?: string;
  sort: SortKey;
  page: number;
  scanPages: number;
  selectedBizTypes: BizTypeOption[];
  sp: {
    q?: string;
    type?: string;
    biz_types?: string | string[];
    frgcpt?: string;
    indstryty?: string;
    inst?: string;
    from?: string;
    to?: string;
    sort?: string;
    page?: string;
    deep?: string;
  };
}

async function Results(params: ResultsParams) {
  const { sort, page, scanPages, sp, selectedBizTypes, ...searchParams } = params;
  const result = await searchBidNotices({ ...searchParams, page, scan_pages: scanPages });
  if (!result.ok) {
    return (
      <div className="rounded border border-[var(--color-danger)] p-4 text-sm">
        오류: {result.error}
      </div>
    );
  }
  const data = extractData(result.data);
  let rawItems: Bid[] = data?.items || [];

  // P31-R3 (F23): 일반용역/기술용역 단독 선택 시 client-side filter (backend는 "용역" 통합 응답).
  // 두 종 모두 선택 또는 일반용역+기술용역 외 다른 종이 섞이면 필터 미적용.
  const onlyService =
    selectedBizTypes.length > 0 &&
    selectedBizTypes.every((v) => v === "일반용역" || v === "기술용역");
  if (onlyService && selectedBizTypes.length === 1) {
    const target = selectedBizTypes[0];
    rawItems = rawItems.filter((it) => (it.srvce_div || "") === target);
  }

  const items = sortItems(rawItems, sort, todayYYYYMMDD());
  const totalCount = data?.total_count ?? 0;
  const hasMore = !!data?.has_more;
  const isDeep = sp.deep === "1";
  // P30-R3 P1-01: scan coverage 메타 — false-negative 인지용
  const scanCoveragePct = data?.scan_coverage_pct;
  const chunksUsed = data?.chunks_used;
  const endpointsUsed = data?.endpoints_used;
  const scanned = data?.scanned;
  const buildHref = (newPage: number) => {
    const qs = new URLSearchParams();
    if (sp.q) qs.set("q", sp.q);
    // P31-R4.6 hot-fix: biz_types가 string[] 일 때 append 다중 (.set은 단일 string만)
    if (sp.biz_types) {
      if (Array.isArray(sp.biz_types)) {
        for (const v of sp.biz_types) qs.append("biz_types", v);
      } else {
        qs.set("biz_types", sp.biz_types);
      }
    }
    if (sp.frgcpt) qs.set("frgcpt", sp.frgcpt);
    if (sp.indstryty) qs.set("indstryty", sp.indstryty);
    if (sp.inst) qs.set("inst", sp.inst);
    if (sp.from) qs.set("from", sp.from);
    if (sp.to) qs.set("to", sp.to);
    if (sort) qs.set("sort", sort);
    // P30-R3 P1-02: deep / sort 파라미터 페이지 이동 시 보존 — "깊은 검색" 풀림 방지
    if (sp.deep) qs.set("deep", sp.deep);
    qs.set("page", String(newPage));
    return `/bids?${qs.toString()}`;
  };

  // P30-R3 P1-01: 빈 결과 + scan_coverage_pct < 100 시 강조 — F16 사용자 사례 직결
  const isLowCoverage =
    typeof scanCoveragePct === "number" && scanCoveragePct < 100;
  const showCoverageWarning = items.length === 0 && isLowCoverage;
  const renderCoverageBadge = () => {
    if (typeof scanCoveragePct !== "number") return null;
    const cls = showCoverageWarning
      ? "rounded border border-[var(--color-warning,#f59e0b)] bg-[var(--color-warning-bg,#fef3c7)] px-2 py-0.5 text-xs font-medium"
      : "rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-0.5 text-xs text-[var(--color-fg-muted)]";
    return (
      <span className={cls}>
        스캔 {scanCoveragePct}%
        {(chunksUsed || endpointsUsed) && (
          <>
            {" "}({chunksUsed ?? "?"}개월 × {endpointsUsed ?? "?"} endpoint
            {typeof scanned === "number" && typeof totalCount === "number" && (
              <>, scanned {scanned} / total {totalCount.toLocaleString()}</>
            )}
            )
          </>
        )}
      </span>
    );
  };

  if (items.length === 0) {
    // 5/3 N42 fix #6 + v22.6: total_count가 큰데 매칭 0이면 키워드 매칭률 문제 — 명확한 메시지
    // trim() 추가: 공백만 입력된 케이스 정합화
    const trimmedKeyword = params.keyword?.trim() || "";
    const trimmedInst = params.inst_name?.trim() || "";
    const hasFilter = !!(trimmedKeyword || trimmedInst);
    const isLikeZero = hasFilter && totalCount > 0;
    return (
      <div className="space-y-2">
        {(typeof scanCoveragePct === "number") && (
          <div className="flex items-center gap-2">{renderCoverageBadge()}</div>
        )}
        <p className="rounded border p-4 text-sm">
          {isLikeZero ? (
            <>
              <strong>
                이 페이지에서 {trimmedKeyword && `키워드 "${trimmedKeyword}"`}
                {trimmedKeyword && trimmedInst && " + "}
                {trimmedInst && `발주기관 "${trimmedInst}"`}
                {" "}매칭 0건
              </strong>
              {" "}— 기간 내 총 {totalCount.toLocaleString()}건 공고가 있지만 본 페이지에서는 매칭이 없습니다.
              {!isDeep && (
                <>
                  {" "}<strong>&ldquo;깊은 검색&rdquo; 체크박스</strong>를 켜면 5배 깊이 스캔하여 매칭률을 높입니다 (응답 시간 ~22초).
                </>
              )}
              {hasMore && " 또는 다음 페이지로 이동해보세요."}
            </>
          ) : (
            <>
              결과 없음 (총 {totalCount.toLocaleString()}건). 페이지 {page}.
              {hasMore && " 다음 페이지를 시도하세요."}
              {showCoverageWarning && (
                <>
                  {" "}<strong>스캔 {scanCoveragePct}%</strong> — 기간 확장 또는 깊은 검색 권장.
                </>
              )}
            </>
          )}
        </p>
        {(page > 1 || hasMore) && (
          <PageNav
            page={page}
            hasMore={hasMore}
            buildHref={buildHref}
            totalCount={totalCount}
          />
        )}
      </div>
    );
  }

  return (
    <section className="rounded-lg border">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b bg-[var(--color-bg-muted)] px-4 py-2 text-sm">
        <span className="flex flex-wrap items-center gap-2">
          <span>
            총 {totalCount}건 (반환 {items.length}, 페이지 {page})
          </span>
          {renderCoverageBadge()}
        </span>
        <PageNav
          page={page}
          hasMore={hasMore}
          buildHref={buildHref}
          totalCount={totalCount}
          inline
        />
      </div>
      <table className="w-full text-sm">
        <thead className="bg-[var(--color-bg-muted)]">
          <tr>
            <th className="px-3 py-2 text-left">공고일</th>
            <th className="px-3 py-2 text-left">공고제목</th>
            <th className="px-3 py-2 text-left">공고기관</th>
            <th className="px-3 py-2 text-left">수요기관</th>
            <th className="px-3 py-2 text-left">업무구분</th>
            <th className="px-3 py-2 text-right">추정가</th>
            <th className="px-3 py-2 text-right">마감일</th>
          </tr>
        </thead>
        <tbody>
          {items.map((bid: Bid) => {
            // P31-R3 (F26): ntceInsttNm + dminsttNm 분리 표시 (raw 응답 직접 활용)
            const raw = bid.raw || {};
            const ntceInst = (raw["ntceInsttNm"] as string | undefined) || undefined;
            const dminInst = (raw["dminsttNm"] as string | undefined) || undefined;
            // 업무구분: srvce_div 우선 (일반용역/기술용역 변별), 없으면 biz_type
            const workDiv = bid.srvce_div || bid.biz_type || "—";
            return (
              <tr key={`${bid.bid_no}-${bid.bid_ord}`} className="border-t hover:bg-[var(--color-bg-muted)]">
                <td className="px-3 py-2 tabular-nums">
                  {fmtDate(bid.publish_date)}
                </td>
                <td className="px-3 py-2">
                  <BidLink
                    bidNo={bid.bid_no}
                    ord={bid.bid_ord}
                    title={bid.title}
                  />
                </td>
                <td className="px-3 py-2">
                  {ntceInst ? <AgencyLink name={ntceInst} /> : "—"}
                </td>
                <td className="px-3 py-2">
                  {dminInst && dminInst !== ntceInst ? (
                    <AgencyLink name={dminInst} />
                  ) : (
                    <span className="text-[var(--color-fg-muted)]">
                      {dminInst === ntceInst ? "(동일)" : "—"}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2">{workDiv}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {fmtWon(bid.estimated_price)}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {fmtDate(bid.deadline_date)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {[1, 2, 3, 4, 5].map((n) => (
        <div key={n} className="h-10 animate-pulse rounded bg-[var(--color-bg-muted)]" />
      ))}
    </div>
  );
}

function PageNav({
  page,
  hasMore,
  buildHref,
  totalCount,
  inline = false,
}: {
  page: number;
  hasMore: boolean;
  buildHref: (newPage: number) => string;
  totalCount: number;
  inline?: boolean;
}) {
  // 단일 페이지 = 999건 (max_scan_pages=1, page_size=999)
  const pageSize = 999;
  const lastPage = Math.max(1, Math.ceil(totalCount / pageSize));

  return (
    <nav className={inline ? "flex items-center gap-2 text-xs" : "flex items-center justify-end gap-2 text-xs"}>
      {page > 1 && (
        <a
          href={buildHref(page - 1)}
          className="rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-bg)]"
        >
          ← 이전
        </a>
      )}
      <span className="text-[var(--color-fg-muted)]">
        {page} / {lastPage}
      </span>
      {hasMore && (
        <a
          href={buildHref(page + 1)}
          className="rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-bg)]"
        >
          다음 →
        </a>
      )}
    </nav>
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
