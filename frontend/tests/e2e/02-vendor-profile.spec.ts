/**
 * 시연 시나리오 2 — 업체 프로필
 *
 * 영업/임원: "이 업체 어떤 회사인가?" → NTS + 입찰/응찰/개찰/낙찰 통계
 */
import { test, expect } from "@playwright/test";

const TEST_BIZ_NO = process.env.E2E_TEST_BIZ_NO || "1058705373";

test.describe("업체 프로필", () => {
  test("빠른검색 → 사업자번호 → vendor 페이지", async ({ page }) => {
    await page.goto("/");
    const search = page.getByPlaceholder(/공고번호.*사업자번호/);
    await search.fill(TEST_BIZ_NO);
    await page.getByRole("button", { name: "검색" }).click();

    await expect(page).toHaveURL(new RegExp(`/vendors/${TEST_BIZ_NO}`), {
      timeout: 15_000,
    });
    await expect(
      page.getByRole("heading", { name: /업체 프로필/ }),
    ).toBeVisible({ timeout: 15_000 });
  });

  test("vendor 페이지에 NTS + 5종 통계", async ({ page }) => {
    await page.goto(`/vendors/${TEST_BIZ_NO}`);

    // NTS 검증 섹션
    await expect(page.getByText(/NTS 검증/)).toBeVisible({ timeout: 15_000 });

    // 5종 통계 라벨
    for (const label of ["입찰", "응찰", "개찰참여", "낙찰", "낙찰합계"]) {
      await expect(page.getByText(label).first()).toBeVisible();
    }
  });
});
