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
import { searchKwaterContracts } from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";
import { fmtWon, fmtDate } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

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

export default async function KwaterContractsPage(props: {
  searchParams: Promise<{ dt?: string; limit?: string }>;
}) {
  const sp = await props.searchParams;
  const searchDt = sp.dt || defaultMonth();
  const limit = parseInt(sp.limit || "30", 10) || 30;

  return (
    <main className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold">한국수자원공사 계약공개</h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          K-water 전자조달 공사 계약 정보 (월 단위 — searchDt YYYYMM).
          외부 어댑터 ACTIVE — apis.data.go.kr/B500001/ebid/cntrct3/cntrwkList
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
              className="max-w-[200px]"
              required
            />
            <Input
              name="limit"
              defaultValue={String(limit)}
              type="number"
              min="1"
              max="1000"
              className="max-w-[120px]"
            />
            <Button type="submit">검색</Button>
            <span className="ml-auto text-xs text-[var(--color-fg-muted)]">
              현재: {searchDt} · 행 {limit}
            </span>
          </form>
        </CardContent>
      </Card>

      <Suspense fallback={<TableSkeleton />}>
        <Results searchDt={searchDt} limit={limit} />
      </Suspense>
    </main>
  );
}

async function Results({
  searchDt,
  limit,
}: {
  searchDt: string;
  limit: number;
}) {
  const r = await searchKwaterContracts(searchDt, limit);
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
  }>(r.data);
  const items = data?.items || [];

  if (items.length === 0) {
    return (
      <p className="rounded border p-4 text-sm">
        결과 없음 ({data?.total_count ?? 0}건). status: {data?.status || "—"}
      </p>
    );
  }

  return (
    <section className="rounded-lg border">
      <div className="flex items-center justify-between border-b bg-[var(--color-bg-muted)] px-4 py-2 text-sm">
        <span>
          {searchDt}월 · 총 {data?.total_count ?? items.length}건 (반환{" "}
          {items.length})
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
          {items.map((it: ContractRow) => (
            <tr
              key={it.contract_no}
              className="border-t hover:bg-[var(--color-bg-muted)]"
            >
              <td className="px-3 py-2 tabular-nums">
                {fmtDate(it.contract_date)}
              </td>
              <td className="px-3 py-2 font-mono text-xs">
                {it.contract_no || "—"}
              </td>
              <td className="px-3 py-2">{it.title || "—"}</td>
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
              <td className="px-3 py-2">{it.winner_name || "—"}</td>
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
          ))}
        </tbody>
      </table>
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
