"use server";

import { revalidatePath } from "next/cache";
import {
  removeFromWatchlist,
  unsubscribeKeyword,
  subscribeKeyword,
} from "@/lib/actions";

export async function removeWatchlistAction(formData: FormData) {
  const item_type = formData.get("item_type") as string;
  const item_key = formData.get("item_key") as string;
  await removeFromWatchlist(item_type, item_key);
  revalidatePath("/me");
}

export async function unsubscribeAction(formData: FormData) {
  const id = parseInt(formData.get("subscription_id") as string, 10);
  await unsubscribeKeyword(id);
  revalidatePath("/me");
}

export async function subscribeKeywordAction(formData: FormData) {
  const keyword = formData.get("keyword") as string;
  const biz_type = (formData.get("biz_type") as string) || undefined;
  const inst_name = (formData.get("inst_name") as string) || undefined;
  const notify_email = (formData.get("notify_email") as string) || undefined;
  await subscribeKeyword({ keyword, biz_type, inst_name, notify_email });
  revalidatePath("/me");
}
