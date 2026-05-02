/**
 * 테마 모드 3종 스크린샷 비교.
 *
 * 대시보드 1개 페이지를 system / light / dark 3 모드로 캡쳐.
 * 결과: tests/e2e/screenshots/<viewport>/theme-{system,light,dark}.png
 */
import { test } from "@playwright/test";

const MODES = ["system", "light", "dark"] as const;

test.describe("@theme Theme mode captures", () => {
  for (const mode of MODES) {
    test(`dashboard - ${mode}`, async ({ page }, testInfo) => {
      // 1. 사전에 localStorage 설정 후 페이지 이동
      await page.addInitScript((m) => {
        try {
          localStorage.setItem("govprocu.theme", m);
        } catch {}
      }, mode);

      await page.goto("/", { waitUntil: "networkidle", timeout: 30_000 });
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(500);

      const dir = `screenshots/${testInfo.project.name.replace(/\s+/g, "-")}`;
      await page.screenshot({
        path: `tests/e2e/${dir}/theme-${mode}.png`,
        fullPage: true,
      });
    });
  }
});
