/**
 * 시연 시나리오 3 — Cross-Lookup 4 키 그래프
 *
 * 분석가: 한 키로 시작하면 다른 3 키와의 관계를 한 화면에서 추적
 */
import { test, expect } from "@playwright/test";

const TEST_BID_NO = process.env.E2E_TEST_BID_NO || "20240315678";
const TEST_INST = process.env.E2E_TEST_INST || "국방재정관리단";

test.describe("Cross-Lookup", () => {
  test("4개 탭 표시", async ({ page }) => {
    await page.goto("/lookup");
    for (const label of [
      "📋 공고번호",
      "🏢 사업자번호",
      "🏛 발주기관",
      "📜 계약번호",
    ]) {
      await expect(page.getByRole("link", { name: label })).toBeVisible();
    }
  });

  test("공고번호 lookup → 그래프 + 키 카드", async ({ page }) => {
    await page.goto(`/lookup?mode=bid&q=${TEST_BID_NO}&ord=00`);

    // xyflow 그래프 컨테이너
    await expect(page.locator(".react-flow")).toBeVisible({ timeout: 15_000 });

    // 4 노드
    for (const label of ["공고번호", "사업자번호", "발주기관", "계약번호"]) {
      await expect(page.getByText(label).first()).toBeVisible();
    }
  });

  test("발주기관 lookup → Top 업체 표", async ({ page }) => {
    await page.goto(`/lookup?mode=inst&q=${encodeURIComponent(TEST_INST)}`);
    await expect(page.locator(".react-flow")).toBeVisible({ timeout: 15_000 });
  });
});

test.describe("AI 자연어 콘솔", () => {
  test("/console 페이지 로드", async ({ page }) => {
    await page.goto("/console");
    await expect(page.getByRole("heading", { name: /AI 자연어 콘솔/ })).toBeVisible();
    await expect(page.getByPlaceholder(/자연어로 질문/)).toBeVisible();
  });
});
