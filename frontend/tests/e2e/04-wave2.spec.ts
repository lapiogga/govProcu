/**
 * Wave 2 컴포넌트 — DropdownMenu (정렬), Dialog (즐겨찾기 추가), DataTable (검색·정렬·페이징).
 *
 * 시연:
 *   - bids 페이지: 정렬 드롭다운 → 마감 임박 → URL ?sort=deadline
 *   - me 페이지: 추가 다이얼로그 열기 → 입력 필드 노출
 *   - me 페이지: DataTable 라벨 검색 입력 (또는 빈 메시지)
 */
import { test, expect } from "@playwright/test";

test.describe("Wave 2: DropdownMenu — 입찰 정렬", () => {
  test("정렬 메뉴 열기 → 마감 임박 선택 → URL sort 갱신", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/bids?q=AI");
    await page.waitForLoadState("domcontentloaded");

    // SortMenu trigger button (header 우측, "↓" "↑" "최신순" 등 라벨 포함)
    const sortBtn = page
      .getByRole("button", { name: /최신순|마감|↓|↑/ })
      .first();
    await expect(sortBtn).toBeVisible({ timeout: 15_000 });
    await sortBtn.click();

    const optDeadline = page.getByRole("menuitemradio", { name: /마감 임박/ });
    await expect(optDeadline).toBeVisible({ timeout: 5_000 });
    await optDeadline.click();

    await expect(page).toHaveURL(/sort=deadline/, { timeout: 10_000 });
  });
});

test.describe("Wave 2: Dialog — 즐겨찾기 추가", () => {
  test("/me 추가 버튼 → 다이얼로그 열기 → 입력 필드 노출", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/me");
    await page.waitForLoadState("domcontentloaded");

    const addBtn = page.getByRole("button", { name: /^추가$/ }).first();
    await expect(addBtn).toBeVisible({ timeout: 15_000 });
    await addBtn.click();

    await expect(
      page.getByRole("heading", { name: /즐겨찾기 추가/ }),
    ).toBeVisible({ timeout: 5_000 });
    await expect(page.getByLabel(/^유형$/)).toBeVisible();
    await expect(page.getByLabel(/^키$/)).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(
      page.getByRole("heading", { name: /즐겨찾기 추가/ }),
    ).toBeHidden({ timeout: 5_000 });
  });
});

test.describe("Wave 2: DataTable — 즐겨찾기 검색", () => {
  test("/me 라벨 검색 입력 가능 (또는 빈 안내)", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/me");
    await page.waitForLoadState("domcontentloaded");

    const searchInput = page.getByPlaceholder(/라벨로 검색/);
    if ((await searchInput.count()) > 0) {
      await expect(searchInput.first()).toBeVisible();
      await searchInput.first().fill("test");
    } else {
      await expect(page.getByText(/저장된 즐겨찾기 없음/)).toBeVisible();
    }
  });
});
