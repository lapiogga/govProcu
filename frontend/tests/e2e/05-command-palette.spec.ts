/**
 * 글로벌 명령 팔레트 — ⌘K / Ctrl+K 단축키.
 *
 * 시연:
 *   - 헤더 "검색…" 버튼 클릭 → 팔레트 열기 → 페이지 그룹 표시
 *   - Ctrl+K → 토글 (body focus 보장)
 *   - 사업자번호 10자리 입력 → "업체 프로필 보기" 옵션 표시
 *   - 페이지 항목 선택 → 라우팅
 */
import { test, expect, type Page } from "@playwright/test";

async function openPalette(page: Page) {
  // 헤더의 ⌘K 트리거 버튼이 가장 안정적 (input focus 영향 없음)
  const trigger = page
    .getByRole("button", { name: /명령 팔레트 열기/ })
    .first();
  await expect(trigger).toBeVisible({ timeout: 15_000 });
  await trigger.click();
  // CommandDialog hydration 안정화
  const input = page.getByPlaceholder(/페이지.*업체.*공고/);
  await expect(input).toBeVisible({ timeout: 5_000 });
  return input;
}

test.describe("Command Palette (⌘K)", () => {
  test("헤더 검색 버튼 클릭 → 팔레트 열기 → 페이지 그룹", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    await openPalette(page);

    await expect(page.getByText("입찰 검색", { exact: true }).first())
      .toBeVisible();
    await expect(page.getByText("업체 분석", { exact: true }).first())
      .toBeVisible();
    await expect(page.getByText("AI 콘솔", { exact: true }).first())
      .toBeVisible();
  });

  test("사업자번호 10자리 입력 → '업체 프로필 보기' 항목", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    const input = await openPalette(page);
    await input.fill("1058705373");
    await expect(page.getByText(/업체 프로필 보기/)).toBeVisible({
      timeout: 5_000,
    });
  });

  test("페이지 항목 선택 → 라우팅", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    const input = await openPalette(page);
    await input.fill("입찰 검색");

    // cmdk Item은 [cmdk-item] 또는 role="option" 으로 노출
    const item = page.locator('[cmdk-item]').filter({ hasText: "입찰 검색" }).first();
    await expect(item).toBeVisible({ timeout: 5_000 });
    await item.click();
    await expect(page).toHaveURL(/\/bids/, { timeout: 10_000 });
  });

  test("ESC → 팔레트 닫기", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    const input = await openPalette(page);
    await page.keyboard.press("Escape");
    await expect(input).toBeHidden({ timeout: 5_000 });
  });
});
