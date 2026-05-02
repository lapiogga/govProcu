/**
 * 시연 시나리오 2 — 업체 프로필
 *
 * 영업/임원: "이 업체 어떤 회사인가?" → NTS + 입찰/응찰/개찰/낙찰 통계
 */
import { test, expect } from "@playwright/test";

const TEST_BIZ_NO = process.env.E2E_TEST_BIZ_NO || "1058705373";

test.describe("업체 프로필", () => {
  test("빠른검색 redirect → vendor 페이지", async ({ page }) => {
    test.setTimeout(60_000);
    // search 페이지가 10자리 사업자번호를 인식해 vendors/ 로 redirect
    await page.goto(`/search?q=${TEST_BIZ_NO}`);
    await expect(page).toHaveURL(new RegExp(`/vendors/${TEST_BIZ_NO}`), {
      timeout: 15_000,
    });
    await expect(
      page.getByRole("heading", { name: /업체 프로필/ }),
    ).toBeVisible({ timeout: 15_000 });
  });

  test("vendor 페이지에 NTS + 5종 통계", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto(`/vendors/${TEST_BIZ_NO}`);

    // NTS 검증 섹션 (Suspense streaming 후)
    await expect(page.getByText(/NTS 검증/)).toBeVisible({ timeout: 30_000 });

    // 5종 통계 라벨
    for (const label of ["입찰", "응찰", "개찰참여", "낙찰", "낙찰합계"]) {
      await expect(page.getByText(label).first()).toBeVisible({
        timeout: 30_000,
      });
    }
  });
});
