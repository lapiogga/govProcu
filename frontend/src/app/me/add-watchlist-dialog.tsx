/**
 * 즐겨찾기 추가 Dialog — me 페이지 상단 "추가" 버튼.
 * 사업자번호/공고번호/기관명을 한 폼에서 추가 (server action).
 */
"use client";

import * as React from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { addWatchlistAction } from "./actions";

const SELECT_CLASS =
  "flex h-9 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]";

export function AddWatchlistDialog() {
  const [open, setOpen] = React.useState(false);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Plus className="mr-1 h-3 w-3" />
          추가
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>즐겨찾기 추가</DialogTitle>
          <DialogDescription>
            업체(사업자번호) · 공고(공고번호) · 기관(기관명) 중 하나를 추가합니다.
          </DialogDescription>
        </DialogHeader>
        <form
          action={async (formData) => {
            await addWatchlistAction(formData);
            setOpen(false);
          }}
          className="grid gap-3"
        >
          <div className="grid gap-1.5">
            <Label htmlFor="watchlist-type">유형</Label>
            <select
              id="watchlist-type"
              name="item_type"
              defaultValue="vendor"
              className={SELECT_CLASS}
            >
              <option value="vendor">업체 (사업자번호 10자리)</option>
              <option value="bid">공고 (공고번호)</option>
              <option value="agency">기관 (기관명)</option>
            </select>
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="watchlist-key">키</Label>
            <Input
              id="watchlist-key"
              name="item_key"
              placeholder="예: 1234567890 (사업자) / 20240315678-00 (공고) / 국방재정관리단 (기관)"
              required
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="watchlist-label">라벨 (선택)</Label>
            <Input
              id="watchlist-label"
              name="item_label"
              placeholder="화면에 표시할 별칭"
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="watchlist-note">메모 (선택)</Label>
            <Input id="watchlist-note" name="note" placeholder="비고" />
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="ghost">
                취소
              </Button>
            </DialogClose>
            <Button type="submit">저장</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
