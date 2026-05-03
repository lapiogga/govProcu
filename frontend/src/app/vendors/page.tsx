/**
 * 업체 분석 인덱스 — 사업자번호 직접 입력 + 업체명 LIKE 검색 + 즐겨찾기 vendor 목록.
 * 대시보드 "업체 분석" 메뉴 카드 진입점.
 *
 * 5/3 N41 — 업체명 LIKE 검색:
 *   사용자가 업체명 일부를 입력하면 search_awards_by_vendor(vendor_name=...) 로
 *   매칭 vendor 후보 리스트를 표시 → 클릭 시 /vendors/{biz_no} 이동.
 */
import { Suspense } from "react";
import { redirect } from "next/navigation";
import {
  listMyWatchlist,
  searchVendorsByName,
} from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";
import { fmtWon, fmtDate } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { VendorLink } from "@/components/EntityLink";

export default async function VendorsIndexPage(props: {
  searchParams: Promise<{ biz?: string; name?: string; from?: string; to?: string; page?: string }>;
}) {
  const { biz, name, from, to, page } = await props.searchParams;
  const pageNum = Math.max(1, parseInt(page || "1", 10) || 1);

  // 사업자번호 입력 시 즉시 redirect
  if (biz) {
    const cleaned = biz.trim().replace(/\D/g, "");
    if (/^\d{10}$/.test(cleaned)) {
      redirect(`/vendors/${cleaned}`);
    }
  }

  const trimmedName = (name || "").trim();
  const hasNameQuery = trimmedName.length >= 2;

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">업체 분석</h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          사업자번호 직접 또는 업체명 LIKE 검색 → NTS 진위 + 입찰/응찰/개찰/낙찰 통계 + 동종업체 비교
        </p>
      </header>

      <Card>
        <CardContent className="space-y-3 p-4">
          <form action="/vendors" className="flex gap-2">
            <Input
              name="biz"
              placeholder="사업자번호 10자리 (예: 1234567890 또는 123-45-67890)"
              defaultValue={biz}
              className="flex-1"
            />
            <Button type="submit" variant="outline">
              사업자번호 조회
            </Button>
          </form>
          {biz && (
            <p className="text-xs text-[var(--color-danger)]">
              사업자번호 형식이 올바르지 않습니다. 10자리 숫자로 입력하세요.
            </p>
          )}

          <div className="border-t pt-3" />

          <form action="/vendors" className="grid grid-cols-1 gap-2 md:grid-cols-5">
            <Input
              name="name"
              placeholder="업체명 LIKE (예: '한국' / '솔루션' / '기술')"
              defaultValue={trimmedName}
              className="md:col-span-2"
            />
            <Input
              name="from"
              defaultValue={from || defaultDateFrom()}
              placeholder="기간 from YYYYMMDD"
            />
            <Input
              name="to"
              defaultValue={to || defaultDateTo()}
              placeholder="기간 to YYYYMMDD"
            />
            <Button type="submit">업체명 검색</Button>
          </form>
          <p className="text-xs text-[var(--color-fg-muted)]">
            낙찰 이력에서 업체명 LIKE 매칭. G2B 낙찰정보 검색은 <strong>최대 1개월 단위</strong>로 제한.
            클릭 시 사업자번호 기반 풀 프로필로 이동.
          </p>
        </CardContent>
      </Card>

      {hasNameQuery && (
        <Suspense fallback={<Skel h={20} />}>
          <NameSearchResults
            name={trimmedName}
            dateFrom={from}
            dateTo={to}
            page={pageNum}
          />
        </Suspense>
      )}

      <Suspense fallback={<Skel h={20} />}>
        <RecentVendors />
      </Suspense>
    </main>
  );
}

async function NameSearchResults({
  name,
  dateFrom,
  dateTo,
  page = 1,
}: {
  name: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
}) {
  const r = await searchVendorsByName(name, dateFrom, dateTo, 30, page);
  if (!r.ok) {
    return (
      <Card>
        <CardContent className="p-4 text-sm text-[var(--color-danger)]">
          오류: {r.error}
        </CardContent>
      </Card>
    );
  }

  const data = extractMcpData<{
    items?: Array<{
      bid_no?: string;
      bid_ord?: string;
      bid_title?: string;
      winner_name?: string;
      winner_biz_no?: string;
      award_amount?: number;
      open_date?: string;
      inst_name?: string;
    }>;
    total_count?: number;
    scanned?: number;
    returned_count?: number;
    has_more?: boolean;
    scan_coverage_pct?: number;
  }>(r.data);

  const rawItems = data?.items || [];
  // P30-R3 P1-06: has_more / scan_coverage_pct 노출 — Phase 29 backend fix 사용자 도달
  const hasMore = !!data?.has_more;
  const scanCoveragePct = data?.scan_coverage_pct;
  // P30-R3 P1-09: 페이지네이션 — "더 보기" 링크용 buildHref
  const buildPageHref = (newPage: number) => {
    const qs = new URLSearchParams();
    qs.set("name", name);
    if (dateFrom) qs.set("from", dateFrom);
    if (dateTo) qs.set("to", dateTo);
    if (newPage > 1) qs.set("page", String(newPage));
    return `/vendors?${qs.toString()}`;
  };

  // 업체명별 그룹화 (winner_biz_no 기준)
  const groups = new Map<
    string,
    {
      biz_no: string;
      name: string;
      count: number;
      total_amount: number;
      latest_date: string;
    }
  >();

  for (const it of rawItems) {
    const bizNo = (it.winner_biz_no || "").replace(/\D/g, "");
    const name = it.winner_name || "";
    if (!bizNo || !name) continue;
    const key = bizNo;
    const cur = groups.get(key);
    if (cur) {
      cur.count += 1;
      cur.total_amount += it.award_amount || 0;
      if ((it.open_date || "") > cur.latest_date) {
        cur.latest_date = it.open_date || "";
      }
    } else {
      groups.set(key, {
        biz_no: bizNo,
        name,
        count: 1,
        total_amount: it.award_amount || 0,
        latest_date: it.open_date || "",
      });
    }
  }

  const sorted = Array.from(groups.values()).sort(
    (a, b) => b.total_amount - a.total_amount,
  );

  // P30-R3 P1-06: scan_coverage_pct < 100 시 warning, has_more 시 "추가 검색 권장"
  const isLowCoverage =
    typeof scanCoveragePct === "number" && scanCoveragePct < 100;
  const showWarn = hasMore || isLowCoverage;

  return (
    <Card>
      <CardContent className="p-0">
        <header className="flex flex-wrap items-center gap-2 border-b px-4 py-2 text-sm font-medium">
          <span>
            업체명 검색: &ldquo;{name}&rdquo; → 후보 업체 {sorted.length}개
          </span>
          <span className="text-xs font-normal text-[var(--color-fg-muted)]">
            (낙찰 row {data?.returned_count ?? 0}건 · 스캔 {data?.scanned ?? 0}
            {page > 1 && ` · 페이지 ${page}`})
          </span>
          {/* P30-R3 P1-06: has_more / scan_coverage_pct 노출 */}
          {typeof scanCoveragePct === "number" && (
            <span
              className={
                showWarn
                  ? "rounded border border-[var(--color-warning,#f59e0b)] bg-[var(--color-warning-bg,#fef3c7)] px-2 py-0.5 text-xs font-medium"
                  : "rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-0.5 text-xs text-[var(--color-fg-muted)]"
              }
            >
              스캔 {scanCoveragePct}%
              {hasMore && " — 추가 검색 권장"}
            </span>
          )}
          {hasMore && typeof scanCoveragePct !== "number" && (
            <span className="rounded border border-[var(--color-warning,#f59e0b)] bg-[var(--color-warning-bg,#fef3c7)] px-2 py-0.5 text-xs font-medium">
              추가 결과 있음 — 다음 페이지 권장
            </span>
          )}
        </header>
        {sorted.length === 0 ? (
          <p className="p-4 text-sm text-[var(--color-fg-muted)]">
            매칭되는 후보 없음. 다른 키워드 또는 기간 확장.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-bg-muted)]">
              <tr>
                <th className="px-3 py-2 text-left">업체명</th>
                <th className="px-3 py-2 text-left">사업자번호</th>
                <th className="px-3 py-2 text-right">낙찰 건수</th>
                <th className="px-3 py-2 text-right">합계 금액</th>
                <th className="px-3 py-2 text-right">최근 낙찰일</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((v) => (
                <tr
                  key={v.biz_no}
                  className="border-t hover:bg-[var(--color-bg-muted)]"
                >
                  <td className="px-3 py-2">
                    <VendorLink bizNo={v.biz_no} name={v.name} />
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">{v.biz_no}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{v.count}</td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {fmtWon(v.total_amount)}
                  </td>
                  <td className="px-3 py-2 text-right text-xs tabular-nums">
                    {fmtDate(v.latest_date)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {/* P30-R3 P1-09: 페이지네이션 — has_more 시 "더 보기" 링크 + 이전 페이지 */}
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
            {hasMore && (
              <a
                href={buildPageHref(page + 1)}
                className="rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-bg)]"
              >
                더 보기 →
              </a>
            )}
          </nav>
        )}
      </CardContent>
    </Card>
  );
}

async function RecentVendors() {
  const r = await listMyWatchlist();
  const data = extractMcpData<{
    items?: Array<{
      id: number;
      item_type?: string;
      item_key: string;
      item_label?: string;
      note?: string;
      created_at: string;
    }>;
  }>(r.data);
  const items = (data?.items || []).filter(
    (it) => it.item_type === "vendor",
  );

  if (items.length === 0) {
    return (
      <Card>
        <CardContent className="p-4 text-sm text-[var(--color-fg-muted)]">
          즐겨찾기에 추가된 업체가 없습니다. 입찰 추적·응찰업체 표에서 추가하세요.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        <header className="border-b px-4 py-2 text-sm font-medium">
          즐겨찾기 업체 ({items.length})
        </header>
        <table className="w-full text-sm">
          <thead className="bg-[var(--color-bg-muted)]">
            <tr>
              <th className="px-3 py-2 text-left">사업자번호</th>
              <th className="px-3 py-2 text-left">라벨</th>
              <th className="px-3 py-2 text-left">메모</th>
              <th className="px-3 py-2 text-left">추가일</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.id} className="border-t hover:bg-[var(--color-bg-muted)]">
                <td className="px-3 py-2 font-mono">
                  <VendorLink bizNo={it.item_key} formatBizNo />
                </td>
                <td className="px-3 py-2">{it.item_label || "—"}</td>
                <td className="px-3 py-2 text-[var(--color-fg-muted)]">
                  {it.note || ""}
                </td>
                <td className="px-3 py-2 text-xs tabular-nums">{it.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
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

function defaultDateFrom(): string {
  // v29.2: 30일 → 1년 (365일). v29.1.2 V4 병렬화 후 1년 36초.
  // 사용자 보고 사례: 7028600866 1개월 0건이지만 1년 100% 커버 시 1건 발견.
  // 짧은 default는 false-negative 유발 → 1년 default로 첫 조회 정확도 ↑.
  const d = new Date();
  d.setDate(d.getDate() - 365);
  return formatYYYYMMDD(d);
}

function defaultDateTo(): string {
  return formatYYYYMMDD(new Date());
}

function formatYYYYMMDD(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}${m}${day}`;
}
