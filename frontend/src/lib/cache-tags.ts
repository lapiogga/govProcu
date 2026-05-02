/**
 * Next.js 15 Cache Components — tag 체계 표준화.
 *
 * Tag 네이밍 규칙:
 *   bid:<bid_notice_no>:<bid_ord>      — 공고 단위 (lifecycle/trace)
 *   vendor:<biz_no>                    — 업체 단위 (profile)
 *   agency:<inst_name>                 — 발주기관 단위 (history/pattern)
 *   contract:<contract_no>             — 계약 단위
 *   industry:<biz_type>                — 업종 단위 (analytics)
 *   user:me                            — 현재 사용자 (watchlist/subscriptions)
 *   global                             — 광역 (전체 무효화 시)
 */

export const cacheTags = {
  bid: (bidNo: string, ord: string = "00") => `bid:${bidNo}:${ord}`,
  vendor: (bizNo: string) => `vendor:${bizNo}`,
  agency: (instName: string) => `agency:${instName}`,
  contract: (contractNo: string) => `contract:${contractNo}`,
  industry: (bizType: string) => `industry:${bizType}`,
  user: () => `user:me`,
  global: () => `global`,
} as const;
