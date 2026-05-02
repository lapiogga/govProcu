/**
 * 시연 시나리오 1 — 입찰 상세 추적
 *
 * 영업 매니저: "공고번호 어떻게 됐어?" → trace_bid_lifecycle 6단계 + 응찰업체 표
 */
import { test, expect } from "@playwright/test";

const TEST_BID_NO = process.env.E2E_TEST_BID_NO || "20240315678";

test.describe("입찰 상세 추적", () => {
  test("빠른검색 redirect → 입찰 추적", async ({ page }) => {
    test.setTimeout(60_000);
    // search 페이지가 패턴 인식 후 trace 로 redirect 하는지 검증
    await page.goto(`/search?q=${TEST_BID_NO}`);
    await expect(page).toHaveURL(new RegExp(`/bids/trace\\?no=${TEST_BID_NO}`), {
      timeout: 15_000,
    });
    await expect(page.getByRole("heading", { name: /입찰 추적/ })).toBeVisible({
      timeout: 15_000,
    });
  });

  test("trace 페이지 직접 접근 + 6단계 표시", async ({ page }) => {
    await page.goto(`/bids/trace?no=${TEST_BID_NO}&ord=00`);

    // 6단계 라벨 확인
    for (const label of ["사전규격", "본 공고", "개찰", "낙찰", "NTS", "계약"]) {
      await expect(page.getByText(label).first()).toBeVisible({
        timeout: 15_000,
      });
    }
  });

  test("공고 폼 입력 페이지", async ({ page }) => {
    await page.goto("/bids/trace");
    // bids/trace 페이지의 공고번호 입력 폼 (placeholder 정확 매치)
    const inp = page
      .getByPlaceholder(/공고번호 \(예:/)
      .first();
    await expect(inp).toBeVisible({ timeout: 15_000 });
    await inp.fill(TEST_BID_NO);
    await page.getByRole("button", { name: "추적" }).click();
    await expect(page).toHaveURL(new RegExp(TEST_BID_NO), { timeout: 15_000 });
  });
});
