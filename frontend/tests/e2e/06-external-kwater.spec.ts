/**
 * 외부 어댑터 — K-water 전자조달 계약공개.
 *
 * 5/2 N28: 어댑터 ACTIVE 상태에서 mock fixture 5건 표시.
 *  - 페이지 로드 → 5 row + total_count 61
 *  - 월(YYYYMM) 입력 form 유지
 *  - 메뉴 카드(외부)에서 진입 가능
 */
import { test, expect } from "@playwright/test";

test.describe("External — K-water 계약공개", () => {
  test("페이지 로드 → 5 row + 표 헤더", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/external/kwater");
    await page.waitForLoadState("domcontentloaded");

    await expect(
      page.getByRole("heading", { name: /한국수자원공사 계약공개/ }),
    ).toBeVisible({ timeout: 15_000 });

    // mock fixture 표시 (실 endpoint URL 표시)
    await expect(
      page.getByText(/apis\.data\.go\.kr\/B500001/).first(),
    ).toBeVisible({ timeout: 15_000 });

    // 5건 데이터 (mocks.ts 의 search_kwater_contracts fixture)
    await expect(page.getByText("보현산댐 부유물 적치장 설치공사")).toBeVisible();
    await expect(
      page.getByText("광주시 노후 상수관로 교체공사 건설폐기물 처리용역(1차년도)"),
    ).toBeVisible();
  });

  test("YYYYMM form 으로 다른 월 검색 → URL 갱신", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/external/kwater?dt=202205");
    await page.waitForLoadState("domcontentloaded");

    // form 값 유지
    const dtInput = page.locator('input[name="dt"]');
    await expect(dtInput).toHaveValue("202205");

    await dtInput.fill("202206");
    await page.getByRole("button", { name: /^검색$/ }).click();
    await expect(page).toHaveURL(/dt=202206/, { timeout: 10_000 });
  });

  test("biz_type selector — 용역 default + 공사 전환 (5/2 N30)", async ({
    page,
  }) => {
    test.setTimeout(60_000);
    await page.goto("/external/kwater");
    await page.waitForLoadState("domcontentloaded");

    // default = 용역 (정보화 영역)
    const bizSelect = page.locator('select[name="biz"]');
    await expect(bizSelect).toHaveValue("용역");

    // 공사로 전환 후 검색
    await bizSelect.selectOption("공사");
    await page.getByRole("button", { name: /^검색$/ }).click();
    await expect(page).toHaveURL(/biz=%EA%B3%B5%EC%82%AC|biz=공사/, {
      timeout: 10_000,
    });
  });

  test("대시보드 메뉴 카드 → 진입", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    const card = page
      .getByRole("link", { name: /K-water 계약공개/ })
      .first();
    await expect(card).toBeVisible({ timeout: 15_000 });
    await card.click();
    await expect(page).toHaveURL(/\/external\/kwater/, { timeout: 10_000 });
  });
});
