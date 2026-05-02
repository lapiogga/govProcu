# Cache 전략 v1

> Next.js 15 Cache Components (`'use cache'` + `cacheTag`) + revalidateTag.
> 일관된 tag 체계로 mutation → invalidation 흐름 표준화.

---

## 1. Tag 체계

`frontend/src/lib/cache-tags.ts`:

| Tag | 형식 | 적용 범위 |
|-----|------|----------|
| `bid:<bid_no>:<ord>` | 공고+차수 | trace_bid_lifecycle, search_bid_notices 결과 중 단일 공고 |
| `vendor:<biz_no>` | 사업자번호 | vendor_profile, lookup_by_biz_no |
| `agency:<inst_name>` | 발주기관명 | agency_procurement_history, agency_price_pattern |
| `contract:<contract_no>` | 계약번호 | lookup_by_contract_no |
| `industry:<biz_type>` | 업종 (공사/용역/물품) | industry_trend, market_share |
| `user:me` | 현재 사용자 | watchlist, subscriptions |
| `global` | 전역 | 전체 invalidation 비상용 |

명시적인 헬퍼 사용 (typo 방지):

```ts
import { unstable_cacheTag as cacheTag } from "next/cache";
import { cacheTags } from "@/lib/cache-tags";

async function Profile({ bizNo }) {
  "use cache";
  cacheTag(cacheTags.vendor(bizNo));
  return await getVendorProfile(bizNo);
}
```

---

## 2. 적용 현황

| 페이지 | 함수 | tag | 상태 |
|--------|------|-----|------|
| `/analytics` | IndustryTrendSection | `industry:<bizType>` | ✅ NEXT7 |
| `/analytics` | MarketShareSection | `industry:<bizType>` | ✅ NEXT7 |
| `/agencies` | PriceCard | `agency:<instName>` | ✅ NEXT7 |
| `/agencies` | HistoryTable | `agency:<instName>` | ✅ NEXT7 |
| `/vendors/[bizNo]` | Profile | `vendor:<bizNo>` | ✅ NEXT7 |
| `/bids/trace` | trace 결과 | `bid:<bidNo>:<ord>` | 🔲 TODO (Streaming Suspense 호환성 재검토) |
| `/lookup` | bid/biz/inst 결과 | 키별 tag | 🔲 TODO |

---

## 3. Mutation → Invalidation 매핑

| Mutation | revalidateTag |
|----------|---------------|
| `addToWatchlist`, `removeFromWatchlist` | `cacheTags.user()` |
| `subscribeKeyword`, `unsubscribeKeyword` | `cacheTags.user()` |
| ETL 일일 동기화 (벤더 통계 갱신) | `cacheTags.vendor(bizNo)` (벤더 단위 push) |
| ETL 일일 동기화 (기관 패턴 갱신) | `cacheTags.agency(instName)` |
| 신규 공고 ingest | `cacheTags.bid(no, ord)` + `cacheTags.industry(bizType)` |

ETL은 외부 cron이므로 Webhook(`POST /api/webhook/revalidate`)으로 invalidation 실행. 별도 트랙(차기 세션) — 본 문서 §5 참조.

---

## 4. cacheLife 권장값

`'use cache'` 만으로는 캐시가 무한히 유지되므로, [`cacheLife`](https://nextjs.org/docs/app/api-reference/functions/cacheLife) 보강 권장:

| Tag 그룹 | 권장 stale | revalidate | expire |
|----------|------------|------------|--------|
| `bid:*` | 5분 | 1시간 | 1일 |
| `vendor:*` | 1시간 | 6시간 | 1주 |
| `agency:*` | 1시간 | 6시간 | 1주 |
| `industry:*` | 1일 | 1일 | 1주 |
| `user:me` | 즉시 | 즉시 | 즉시 (mutation 의존) |

운영 데이터 누적 후 cache hit ratio 측정 → 조정.

---

## 5. ETL 연동 Webhook (TODO 차기 세션)

```ts
// frontend/src/app/api/webhook/revalidate/route.ts (예정)
import { revalidateTag } from "next/cache";
import { cacheTags } from "@/lib/cache-tags";

export async function POST(req: Request) {
  // Bearer 토큰 검증
  const auth = req.headers.get("authorization");
  if (auth !== `Bearer ${process.env.REVALIDATE_TOKEN}`) {
    return Response.json({ ok: false }, { status: 401 });
  }
  const { tags } = await req.json();
  for (const t of tags) revalidateTag(t);
  return Response.json({ ok: true, count: tags.length });
}
```

ETL 일일 스크립트가 변경된 row에서 추출한 tag 목록을 POST. 본 라우트는 차기 세션에서 추가.

---

## 6. 디버깅

### 6.1 캐시 hit 확인
브라우저 DevTools → Network → `x-nextjs-cache: HIT|STALE|MISS` 헤더.

### 6.2 강제 무효화 (개발)
```bash
# Next.js dev 서버 .next/cache/ 삭제
rm -rf C:/Users/User/GovProcu/frontend/.next/cache
```

### 6.3 cacheTag 누락 검증
```bash
grep -rn "use cache" frontend/src/app/ | xargs -I{} ...
# 동일 파일에 cacheTag 호출 있는지 페어 확인
```

작성: 2026-05-02 · NEXT7-T6
