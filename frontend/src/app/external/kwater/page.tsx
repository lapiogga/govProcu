/**
 * KWater 전자조달 계약공개 — 5/2 N27.
 *
 * data.go.kr "한국수자원공사_전자조달 계약정보공개" (15101620) 어댑터.
 * 월 단위(YYYYMM) 검색만 지원. 키워드/기관 필터 미지원.
 *
 * 동등 데이터: G2B 계약 API와 별개로 K-water 자체 발주 계약을 추적.
 * 정보화 영역 외(주로 토목/공사) — 다만 "용역" 항목은 K-water IT 분야 검토 가능.
 */
import { Suspense } from "react";
import Link from "next/link";
import { searchKwaterContracts } from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";
import { fmtWon, fmtDate } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

function buildContractHref(it: ContractRow): string {
  const qs = new URLSearchParams();
  if (it.contract_no) qs.set("no", it.contract_no);
  if (it.contract_date) qs.set("dt", it.contract_date);
  if (it.title) qs.set("title", it.title);
  if (it.dept_name) qs.set("dept", it.dept_name);
  if (it.biz_type) qs.set("biz", it.biz_type);
  if (it.winner_name) qs.set("winner", it.winner_name);
  if (it.contract_method) qs.set("method", it.contract_method);
  if (it.limit_method) qs.set("limit", it.limit_method);
  if (it.contract_amount != null) qs.set("amount", String(it.contract_amount));
  if (it.period_from) qs.set("p_from", it.period_from);
  if (it.period_to) qs.set("p_to", it.period_to);
  return `/external/kwater/contract?${qs.toString()}`;
}

interface ContractRow {
  contract_no?: string;
  contract_date?: string;
  title?: string;
  inst_name?: string;
  dept_name?: string;
  biz_type?: string;
  winner_name?: string;
  contract_method?: string;
  limit_method?: string;
  contract_amount?: number;
  period_from?: string;
  period_to?: string;
}

function defaultMonth(): string {
  // 1년 전 해당 월 — 검증된 데이터 보유 구간
  const now = new Date();
  now.setFullYear(now.getFullYear() - 1);
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  return `${yyyy}${mm}`;
}

const SELECT_CLASS =
  "flex h-9 rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]";

export default async function KwaterContractsPage(props: {
  searchParams: Promise<{ dt?: string; biz?: string; limit?: string; page?: string }>;
}) {
  const sp = await props.searchParams;
  const searchDt = sp.dt || defaultMonth();
  const bizType = sp.biz === "공사" ? "공사" : "용역"; // 정보화 영역 default
  const pageSize = parseInt(sp.limit || "30", 10) || 30;
  // P30-R5 P1-16: 페이지네이션 — backend pageNo 미지원 → client-side slice로 시뮬
  const page = Math.max(1, parseInt(sp.page || "1", 10) || 1);

  return (
    <main className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold">한국수자원공사 계약공개</h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          K-water 전자조달 계약 정보 (월 단위 — searchDt YYYYMM, biz_type 공사/용역).
          외부 어댑터 ACTIVE — apis.data.go.kr/B500001/ebid/cntrct3
        </p>
      </header>

      <Card>
        <CardContent className="p-4">
          <form action="/external/kwater" className="flex flex-wrap gap-2">
            <Input
              name="dt"
              defaultValue={searchDt}
              placeholder="YYYYMM (예: 202205)"
              pattern="\d{6}"
              className="max-w-[180px]"
              required
            />
            <select
              name="biz"
              defaultValue={bizType}
              className={SELECT_CLASS}
            >
              <option value="용역">용역 (정보화)</option>
              <option value="공사">공사</option>
            </select>
            <Input
              name="limit"
              defaultValue={String(pageSize)}
              type="number"
              min="1"
              max="1000"
              className="max-w-[100px]"
              placeholder="페이지당"
            />
            <Button type="submit">검색</Button>
            <span className="ml-auto text-xs text-[var(--color-fg-muted)]">
              현재: {searchDt} · {bizType} · 페이지당 {pageSize} · 페이지 {page}
            </span>
          </form>
        </CardContent>
      </Card>

      <Suspense fallback={<TableSkeleton />}>
        <Results
          searchDt={searchDt}
          bizType={bizType}
          pageSize={pageSize}
          page={page}
        />
      </Suspense>
    </main>
  );
}

async function Results({
  searchDt,
  bizType,
  pageSize,
  page,
}: {
  searchDt: string;
  bizType: string;
  pageSize: number;
  page: number;
}) {
  // P30-R5 P1-16: client-side 페이지네이션 — backend `searchKwaterContracts(limit)` 시그니처 변경 0
  // page * pageSize 만큼 fetch 후 [(page-1)*pageSize : page*pageSize] slice
  // backend pageNo 미지원 한계 우회. limit max=1000 (KWater API 한계)
  const fetchLimit = Math.min(pageSize * page, 1000);
  const r = await searchKwaterContracts(searchDt, bizType, fetchLimit);
  if (!r.ok) {
    return (
      <div className="rounded border border-[var(--color-danger)] p-4 text-sm">
        오류: {r.error}
      </div>
    );
  }
  const data = extractMcpData<{
    items?: ContractRow[];
    total_count?: number;
    raw_count?: number;
    status?: string;
    endpoint?: string;
    note?: string;
  }>(r.data);
  const allItems = data?.items || [];
  // P30-R5 P1-16: client-side slice
  const startIdx = (page - 1) * pageSize;
  const items = allItems.slice(startIdx, startIdx + pageSize);
  const totalCount = data?.total_count ?? allItems.length;
  const hasMore = totalCount > page * pageSize;

  // P30-R5 P1-15: status === "pending_key" 안내 — KWATER_API_KEY 미설정 명시
  if (data?.status === "pending_key") {
    return (
      <div className="rounded border border-[var(--color-warning,#f59e0b)] bg-[var(--color-warning-bg,#fef3c7)] p-4 text-sm">
        <p className="font-medium">외부 API 키 미설정</p>
        <p className="mt-1 text-[var(--color-fg-muted)]">
          {data?.note ||
            "KWATER_API_KEY 환경변수 미설정 — 운영자에게 문의 또는 .env 확인."}
        </p>
        <p className="mt-2 text-xs">
          status: <span className="font-mono">{data.status}</span>
        </p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <p className="rounded border p-4 text-sm">
        결과 없음 ({totalCount}건). status: {data?.status || "—"}
        {page > 1 && " — 마지막 페이지 도달 (이전 페이지로 이동)"}
      </p>
    );
  }

  // P30-R5 P1-16: 페이지네이션 nav buildHref
  const buildPageHref = (newPage: number): string => {
    const qs = new URLSearchParams();
    qs.set("dt", searchDt);
    qs.set("biz", bizType);
    qs.set("limit", String(pageSize));
    if (newPage > 1) qs.set("page", String(newPage));
    return `/external/kwater?${qs.toString()}`;
  };

  return (
    <section className="rounded-lg border">
      <div className="flex items-center justify-between border-b bg-[var(--color-bg-muted)] px-4 py-2 text-sm">
        <span>
          {searchDt}월 · {bizType} · 총 {totalCount}건 (페이지 {page} · 표시{" "}
          {items.length}건 / 페이지당 {pageSize})
        </span>
        <span className="text-xs text-[var(--color-fg-muted)]">
          {data?.endpoint || "—"}
        </span>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-[var(--color-bg-muted)]">
          <tr>
            <th className="px-3 py-2 text-left">계약일</th>
            <th className="px-3 py-2 text-left">계약번호</th>
            <th className="px-3 py-2 text-left">계약제목</th>
            <th className="px-3 py-2 text-left">부서</th>
            <th className="px-3 py-2 text-left">업종</th>
            <th className="px-3 py-2 text-left">계약업체</th>
            <th className="px-3 py-2 text-left">방식</th>
            <th className="px-3 py-2 text-right">계약금액</th>
            <th className="px-3 py-2 text-left">기간</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it: ContractRow) => {
            const detailHref = buildContractHref(it);
            return (
              <tr
                key={it.contract_no}
                className="border-t hover:bg-[var(--color-bg-muted)]"
              >
                <td className="px-3 py-2 tabular-nums">
                  {fmtDate(it.contract_date)}
                </td>
                <td className="px-3 py-2 font-mono text-xs">
                  {it.contract_no ? (
                    <Link
                      href={detailHref}
                      className="entity-link"
                      title={`계약 상세 — ${it.contract_no}`}
                    >
                      {it.contract_no}
                    </Link>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-3 py-2">
                  {it.title ? (
                    <Link
                      href={detailHref}
                      className="entity-link font-medium"
                      title={`계약 상세 — ${it.title}`}
                    >
                      {it.title}
                    </Link>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-3 py-2 text-xs">{it.dept_name || "—"}</td>
                <td className="px-3 py-2">
                  <Badge
                    variant={
                      it.biz_type === "용역"
                        ? "default"
                        : it.biz_type === "공사"
                          ? "secondary"
                          : "outline"
                    }
                  >
                    {it.biz_type || "—"}
                  </Badge>
                </td>
                <td className="px-3 py-2">
                  {it.winner_name ? (
                    <Link
                      href={`/vendors?name=${encodeURIComponent(it.winner_name)}`}
                      className="entity-link font-medium"
                      title={`업체 LIKE 검색 — ${it.winner_name}`}
                    >
                      {it.winner_name}
                    </Link>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-3 py-2 text-xs">
                  {it.contract_method || "—"}
                  {it.limit_method && it.limit_method !== "-" && (
                    <span className="ml-1 text-[var(--color-fg-muted)]">
                      ({it.limit_method})
                    </span>
                  )}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {fmtWon(it.contract_amount)}
                </td>
                <td className="px-3 py-2 text-xs tabular-nums">
                  {fmtDate(it.period_from)}~{fmtDate(it.period_to)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {/* P30-R5 P1-16: 페이지네이션 nav */}
      {(hasMore || page > 1) && (
        <nav className="flex items-center justify-end gap-2 border-t px-4 py-2 text-xs">
          {page > 1 && (
            <a
              href={buildPageHref(page - 1)}
              className="rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-bg)]"
            >
              ← 이전
            </a>
          )}
          <span className="text-[var(--color-fg-muted)]">페이지 {page}</span>
          {hasMore && fetchLimit < 1000 && (
            <a
              href={buildPageHref(page + 1)}
              className="rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-bg)]"
            >
              다음 →
            </a>
          )}
          {fetchLimit >= 1000 && hasMore && (
            <span className="text-[var(--color-warning,#f59e0b)]">
              (KWater API 한계 1000건 도달 — searchDt 변경 권장)
            </span>
          )}
        </nav>
      )}
    </section>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {[1, 2, 3, 4, 5].map((n) => (
        <div
          key={n}
          className="h-10 animate-pulse rounded bg-[var(--color-bg-muted)]"
        />
      ))}
    </div>
  );
}
