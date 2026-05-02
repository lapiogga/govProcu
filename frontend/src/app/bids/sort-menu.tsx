/**
 * 입찰 검색 결과 정렬 메뉴 — 클라이언트 인터랙션.
 *
 * URL searchParam `sort` 갱신 (publish_desc / publish_asc / deadline / amount_desc).
 * 서버 컴포넌트가 받아 정렬 후 다시 렌더.
 */
"use client";

import * as React from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { ArrowDownUp, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";

export type SortKey =
  | "publish_desc"
  | "publish_asc"
  | "deadline"
  | "amount_desc"
  | "amount_asc";

const OPTIONS: Array<{ value: SortKey; label: string }> = [
  { value: "publish_desc", label: "공고일 ↓ (최신순)" },
  { value: "publish_asc", label: "공고일 ↑ (오래된순)" },
  { value: "deadline", label: "마감 임박" },
  { value: "amount_desc", label: "추정가 ↓ (큰 금액)" },
  { value: "amount_asc", label: "추정가 ↑ (작은 금액)" },
];

export function SortMenu({ current = "publish_desc" }: { current?: SortKey }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const setSort = React.useCallback(
    (value: string) => {
      const sp = new URLSearchParams(searchParams.toString());
      sp.set("sort", value);
      router.push(`${pathname}?${sp.toString()}`);
    },
    [router, pathname, searchParams],
  );

  const label =
    OPTIONS.find((o) => o.value === current)?.label || "정렬";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          <ArrowDownUp className="mr-1 h-3 w-3" />
          {label}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>정렬 기준</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuRadioGroup value={current} onValueChange={setSort}>
          {OPTIONS.map((o) => (
            <DropdownMenuRadioItem key={o.value} value={o.value}>
              {o.label}
              {current === o.value && (
                <Check className="ml-auto h-3 w-3 opacity-50" />
              )}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
