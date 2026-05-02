/**
 * 즐겨찾기 DataTable — me 페이지 client wrapper.
 * 정렬·검색·페이징을 한 번에 제공.
 */
"use client";

import * as React from "react";
import { type ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/ui/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { VendorLink, AgencyLink, BidLink } from "@/components/EntityLink";
import { removeWatchlistAction } from "./actions";

export interface WatchlistItem {
  id: number;
  item_type: "bid" | "vendor" | "agency" | "contract" | string;
  item_key: string;
  item_label?: string | null;
  note?: string | null;
  created_at: string;
}

export function WatchlistTable({ items }: { items: WatchlistItem[] }) {
  const columns = React.useMemo<ColumnDef<WatchlistItem>[]>(
    () => [
      {
        accessorKey: "item_type",
        header: "유형",
        cell: ({ row }) => <TypeBadge type={row.original.item_type} />,
      },
      {
        accessorKey: "item_key",
        header: "키",
        cell: ({ row }) => (
          <span className="font-mono">
            <KeyLink item={row.original} />
          </span>
        ),
      },
      {
        accessorKey: "item_label",
        header: "라벨",
        cell: ({ row }) => row.original.item_label || "—",
      },
      {
        accessorKey: "note",
        header: "메모",
        cell: ({ row }) => (
          <span className="text-[var(--color-fg-muted)]">
            {row.original.note || ""}
          </span>
        ),
      },
      {
        accessorKey: "created_at",
        header: "추가일",
        cell: ({ row }) => (
          <span className="tabular-nums text-xs">{row.original.created_at}</span>
        ),
      },
      {
        id: "actions",
        header: "",
        enableSorting: false,
        cell: ({ row }) => (
          <form action={removeWatchlistAction}>
            <input
              type="hidden"
              name="item_type"
              value={row.original.item_type}
            />
            <input
              type="hidden"
              name="item_key"
              value={row.original.item_key}
            />
            <Button
              type="submit"
              variant="link"
              size="sm"
              className="text-[var(--color-danger)]"
            >
              제거
            </Button>
          </form>
        ),
      },
    ],
    [],
  );

  return (
    <DataTable
      columns={columns}
      data={items}
      searchKey="item_label"
      searchPlaceholder="라벨로 검색…"
      pageSize={10}
    />
  );
}

function TypeBadge({ type }: { type: string }) {
  const map: Record<
    string,
    { label: string; variant: "default" | "secondary" | "outline" }
  > = {
    bid: { label: "공고", variant: "default" },
    vendor: { label: "업체", variant: "secondary" },
    agency: { label: "기관", variant: "outline" },
    contract: { label: "계약", variant: "outline" },
  };
  const cfg = map[type] || { label: type, variant: "outline" as const };
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
}

function KeyLink({ item }: { item: WatchlistItem }) {
  if (item.item_type === "bid") {
    return <BidLink bidNo={item.item_key} title={item.item_key} />;
  }
  if (item.item_type === "vendor") {
    return <VendorLink bizNo={item.item_key} name={item.item_key} />;
  }
  if (item.item_type === "agency") {
    return <AgencyLink name={item.item_key} />;
  }
  return <span>{item.item_key}</span>;
}
