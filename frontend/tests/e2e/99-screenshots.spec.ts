/**
 * 전체 페이지 mock 데이터 기반 스크린샷 검증.
 *
 * 실행 전 dev 서버를 MCP_MOCK_MODE=true 로 띄워야 함:
 *   $env:MCP_MOCK_MODE = "true"; npm run dev
 *
 * 캡쳐:
 *   npm run test:e2e -- --grep @screenshot
 *
 * 결과: tests/e2e/screenshots/<project>/<page>.png
 */
import { test, expect } from "@playwright/test";

const PAGES: { name: string; path: string }[] = [
  { name: "01-dashboard", path: "/" },
  { name: "02-bids-trace", path: "/bids/trace?no=20240315678&ord=00" },
  { name: "03-search-redirect", path: "/search?q=AI" },
  { name: "04-bids-list", path: "/bids?keyword=AI" },
  { name: "05-vendor-profile", path: "/vendors/1234567890" },
  { name: "06-agencies", path: "/agencies?name=%EA%B5%AD%EB%B0%A9%EC%9E%AC%EC%A0%95%EA%B4%80%EB%A6%AC%EB%8B%A8" },
  { name: "07-analytics", path: "/analytics?type=%EC%9A%A9%EC%97%AD" },
  { name: "08-lookup-bid", path: "/lookup?mode=bid&q=20240315678&ord=00" },
  { name: "09-lookup-biz", path: "/lookup?mode=biz&q=1234567890" },
  { name: "10-me", path: "/me" },
  { name: "11-qualification", path: "/qualification?bid_amount=268500000&base_amount=295000000&biz_type=%EC%9A%A9%EC%97%AD&experience_actual=8&experience_standard=10&tech_count=12&tech_required=10&credit_grade=AA-" },
  { name: "12-prediction", path: "/prediction?bid_no=20240315678&base=295000000&inst=%EA%B5%AD%EB%B0%A9%EC%9E%AC%EC%A0%95%EA%B4%80%EB%A6%AC%EB%8B%A8&type=%EC%9A%A9%EC%97%AD&target=0.7" },
  { name: "13-console", path: "/console" },
];

test.describe("@screenshot Mock-mode full page captures", () => {
  for (const p of PAGES) {
    test(`${p.name}`, async ({ page }, testInfo) => {
      // 다른 spec 과 동시 실행 시 dev 서버 부하 buffer
      test.setTimeout(60_000);
      const url = p.path;
      const resp = await page.goto(url, { waitUntil: "networkidle", timeout: 45_000 });
      expect(resp?.ok(), `Page ${url} responded ${resp?.status()}`).toBeTruthy();

      // Suspense streaming + Tremor hydration 안정화
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(2000);

      const dir = `screenshots/${testInfo.project.name.replace(/\s+/g, "-")}`;
      await page.screenshot({
        path: `tests/e2e/${dir}/${p.name}.png`,
        fullPage: true,
      });
    });
  }
});
