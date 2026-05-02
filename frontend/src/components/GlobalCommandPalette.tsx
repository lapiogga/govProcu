/**
 * 글로벌 명령 팔레트 — ⌘K / Ctrl+K 로 즉시 검색.
 *
 * 검색 항목:
 *   1. 14 페이지 라우트 (대시보드 / 입찰 검색 / 입찰 추적 / 업체 / 발주기관 / 분석 / Lookup / 콘솔 / Me / 적격심사 / 투찰가 / 즐겨찾기 / 빠른검색)
 *   2. 즐겨찾기 vendor (사업자번호 → /vendors/{biz})
 *   3. 자유 입력 (10자리 숫자 → vendor / 입찰공고 형식 → bid trace / 그 외 → 검색)
 *
 * 단축키:
 *   ⌘K (mac), Ctrl+K (win/linux) — 열기/닫기 토글
 *   Esc — 닫기
 *   Enter — 선택 항목 이동
 *
 * 헤더에 마운트되며, layout.tsx 에서 한 번만 렌더링.
 */
"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  Building2,
  Calendar,
  Database,
  Eye,
  Heart,
  Home,
  LineChart,
  Network,
  Search,
  Sparkles,
  Target,
  TrendingUp,
  User,
} from "lucide-react";
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandShortcut,
  CommandSeparator,
} from "@/components/ui/command";

interface PageEntry {
  title: string;
  href: string;
  hint?: string;
  icon: React.ComponentType<{ className?: string }>;
  keywords?: string[];
}

const PAGES: PageEntry[] = [
  { title: "대시보드", href: "/", icon: Home, keywords: ["home", "dashboard"] },
  {
    title: "빠른검색",
    href: "/search",
    icon: Search,
    keywords: ["quick", "search"],
  },
  {
    title: "입찰 검색",
    href: "/bids",
    icon: Database,
    keywords: ["bids", "search", "공고"],
  },
  {
    title: "입찰 추적 (lifecycle)",
    href: "/bids/trace",
    icon: Eye,
    keywords: ["trace", "lifecycle"],
  },
  {
    title: "업체 분석",
    href: "/vendors",
    icon: Building2,
    keywords: ["vendor", "업체", "사업자"],
  },
  {
    title: "발주기관 분석",
    href: "/agencies",
    icon: Building2,
    keywords: ["agency", "발주기관", "기관"],
  },
  {
    title: "분석/통계",
    href: "/analytics",
    icon: LineChart,
    keywords: ["analytics", "동향", "통계"],
  },
  {
    title: "Lookup (4-key)",
    href: "/lookup",
    icon: Network,
    keywords: ["lookup", "relational"],
  },
  {
    title: "AI 콘솔",
    href: "/console",
    icon: Sparkles,
    keywords: ["console", "ai", "chat"],
  },
  {
    title: "Me (즐겨찾기/알림)",
    href: "/me",
    icon: User,
    keywords: ["me", "watchlist", "subscription"],
  },
  {
    title: "적격심사",
    href: "/qualification",
    icon: Target,
    keywords: ["qualification", "심사"],
  },
  {
    title: "투찰가 예측",
    href: "/prediction",
    icon: TrendingUp,
    keywords: ["prediction", "투찰가"],
  },
  {
    title: "K-water 계약공개",
    href: "/external/kwater",
    icon: Database,
    keywords: ["kwater", "수자원", "계약", "external"],
  },
];

export interface GlobalCommandPaletteProps {
  /** 즐겨찾기 vendor 목록 (사업자번호 + 라벨) — RSC가 layout 에서 prefetch */
  watchlistVendors?: Array<{ biz_no: string; label?: string }>;
}

export function GlobalCommandPalette({
  watchlistVendors = [],
}: GlobalCommandPaletteProps) {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");

  // ⌘K / Ctrl+K 글로벌 단축키
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // 자유 입력 패턴 매칭
  const trimmed = query.trim();
  const onlyDigits = trimmed.replace(/\D/g, "");
  const isBizNo = /^\d{10}$/.test(onlyDigits);
  const isBidNo = /^\d{8,12}(-?\d{2})?$/.test(trimmed);
  const hasFreeText = trimmed.length >= 2;

  function go(href: string) {
    setOpen(false);
    setQuery("");
    router.push(href);
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="inline-flex h-8 items-center gap-2 rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-2.5 text-xs text-[var(--color-fg-muted)] transition-colors hover:bg-[var(--color-bg-muted)]"
        aria-label="명령 팔레트 열기"
      >
        <Search className="h-3 w-3" />
        <span>검색…</span>
        <kbd className="rounded border border-[var(--color-border)] bg-[var(--color-bg-muted)] px-1.5 py-0.5 font-mono text-[10px] tracking-wide">
          ⌘K
        </kbd>
      </button>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput
          placeholder="페이지·업체·공고 검색 (⌘K 토글)"
          value={query}
          onValueChange={setQuery}
        />
        <CommandList>
          <CommandEmpty>일치 항목이 없습니다.</CommandEmpty>

          {(isBizNo || isBidNo || hasFreeText) && (
            <>
              <CommandGroup heading="빠른 이동">
                {isBizNo && (
                  <CommandItem
                    onSelect={() => go(`/vendors/${onlyDigits}`)}
                    value={`vendor-${onlyDigits}`}
                  >
                    <Building2 className="h-4 w-4" />
                    <span>업체 프로필 보기</span>
                    <CommandShortcut>{onlyDigits}</CommandShortcut>
                  </CommandItem>
                )}
                {isBidNo && !isBizNo && (
                  <CommandItem
                    onSelect={() => {
                      const [no, ord] = trimmed.split("-");
                      go(`/bids/trace?no=${no}&ord=${ord || "00"}`);
                    }}
                    value={`bid-${trimmed}`}
                  >
                    <Eye className="h-4 w-4" />
                    <span>입찰 추적 (공고번호)</span>
                    <CommandShortcut>{trimmed}</CommandShortcut>
                  </CommandItem>
                )}
                {hasFreeText && !isBizNo && !isBidNo && (
                  <CommandItem
                    onSelect={() =>
                      go(`/bids?keyword=${encodeURIComponent(trimmed)}`)
                    }
                    value={`keyword-${trimmed}`}
                  >
                    <Search className="h-4 w-4" />
                    <span>입찰 키워드 검색</span>
                    <CommandShortcut>{trimmed}</CommandShortcut>
                  </CommandItem>
                )}
              </CommandGroup>
              <CommandSeparator />
            </>
          )}

          <CommandGroup heading="페이지">
            {PAGES.map((p) => {
              const Icon = p.icon;
              const value = `page-${p.title} ${(p.keywords || []).join(" ")}`;
              return (
                <CommandItem
                  key={p.href}
                  value={value}
                  onSelect={() => go(p.href)}
                >
                  <Icon className="h-4 w-4" />
                  <span>{p.title}</span>
                  {p.hint && (
                    <CommandShortcut>{p.hint}</CommandShortcut>
                  )}
                </CommandItem>
              );
            })}
          </CommandGroup>

          {watchlistVendors.length > 0 && (
            <>
              <CommandSeparator />
              <CommandGroup heading="즐겨찾기 업체">
                {watchlistVendors.slice(0, 10).map((v) => (
                  <CommandItem
                    key={v.biz_no}
                    value={`fav-vendor-${v.biz_no} ${v.label || ""}`}
                    onSelect={() => go(`/vendors/${v.biz_no}`)}
                  >
                    <Heart className="h-4 w-4" />
                    <span>{v.label || v.biz_no}</span>
                    <CommandShortcut>{v.biz_no}</CommandShortcut>
                  </CommandItem>
                ))}
              </CommandGroup>
            </>
          )}

          <CommandSeparator />
          <CommandGroup heading="단축 안내">
            <CommandItem disabled value="hint">
              <Calendar className="h-4 w-4" />
              <span>10자리 숫자 → 업체 / 8자리+ → 입찰 / 그 외 → 키워드</span>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  );
}
