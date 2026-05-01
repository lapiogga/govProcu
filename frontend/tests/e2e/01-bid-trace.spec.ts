/**
 * 시연 시나리오 1 — 입찰 상세 추적
 *
 * 영업 매니저: "공고번호 어떻게 됐어?" → trace_bid_lifecycle 6단계 + 응찰업체 표
 */
import { test, expect } from "@playwright/test";

const TEST_BID_NO = process.env.E2E_TEST_BID_NO || "20240315678";

test.describe("입찰 상세 추적", () => {
  test("대시보드 → 빠른검색 → 입찰 추적", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "GovProcu" })).toBeVisible();

    // 빠른 검색에 공고번호 입력
    const search = page.getByPlaceholder(/공고번호.*사업자번호/);
    await search.fill(TEST_BID_NO);
    await search.press("Enter");

    // 자동으로 /bids/trace?no=... 로 이동
    await expect(page).toHaveURL(new RegExp(`/bids/trace\\?no=${TEST_BID_NO}`));
    await expect(page.getByRole("heading", { name: /입찰 추적/ })).toBeVisible();
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
    await expect(page.getByPlaceholder(/공고번호/)).toBeVisible();
    await page.getByPlaceholder(/공고번호/).fill(TEST_BID_NO);
    await page.getByRole("button", { name: "추적" }).click();
    await expect(page).toHaveURL(new RegExp(TEST_BID_NO));
  });
});
