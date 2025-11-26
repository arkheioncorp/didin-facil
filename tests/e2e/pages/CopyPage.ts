/**
 * Copy Page Object Model
 * Page object for AI copy generation
 */
import { Page, Locator, expect } from "@playwright/test";

export class CopyPage {
  readonly page: Page;
  readonly productSelector: Locator;
  readonly copyTypeSelect: Locator;
  readonly toneSelect: Locator;
  readonly generateButton: Locator;
  readonly copyOutput: Locator;
  readonly copyButton: Locator;
  readonly regenerateButton: Locator;
  readonly historyList: Locator;
  readonly quotaDisplay: Locator;
  readonly loadingState: Locator;

  constructor(page: Page) {
    this.page = page;
    this.productSelector = page.locator('[data-testid="product-selector"]');
    this.copyTypeSelect = page.locator('[data-testid="copy-type-select"]');
    this.toneSelect = page.locator('[data-testid="tone-select"]');
    this.generateButton = page.locator('[data-testid="generate-button"]');
    this.copyOutput = page.locator('[data-testid="copy-output"]');
    this.copyButton = page.locator('[data-testid="copy-to-clipboard"]');
    this.regenerateButton = page.locator('[data-testid="regenerate-button"]');
    this.historyList = page.locator('[data-testid="copy-history"]');
    this.quotaDisplay = page.locator('[data-testid="quota-display"]');
    this.loadingState = page.locator('[data-testid="generating-state"]');
  }

  async goto() {
    await this.page.goto("/copy");
    await this.page.waitForLoadState("networkidle");
  }

  async selectProduct(productId: string) {
    await this.productSelector.click();
    await this.page.locator(`[data-value="${productId}"]`).click();
  }

  async selectCopyType(type: string) {
    await this.copyTypeSelect.click();
    await this.page.locator(`[data-value="${type}"]`).click();
  }

  async selectTone(tone: string) {
    await this.toneSelect.click();
    await this.page.locator(`[data-value="${tone}"]`).click();
  }

  async generate() {
    await this.generateButton.click();
    await expect(this.loadingState).toBeVisible();
    await expect(this.loadingState).toBeHidden({ timeout: 30000 });
  }

  async getCopyText(): Promise<string> {
    return (await this.copyOutput.textContent()) || "";
  }

  async copyToClipboard() {
    await this.copyButton.click();
  }

  async regenerate() {
    await this.regenerateButton.click();
    await expect(this.loadingState).toBeVisible();
    await expect(this.loadingState).toBeHidden({ timeout: 30000 });
  }

  async getQuotaInfo(): Promise<{ used: number; limit: number }> {
    const text = await this.quotaDisplay.textContent();
    const match = text?.match(/(\d+)\s*\/\s*(\d+)/);
    return {
      used: match ? parseInt(match[1], 10) : 0,
      limit: match ? parseInt(match[2], 10) : 0,
    };
  }

  async getHistoryCount(): Promise<number> {
    return await this.historyList.locator('[data-testid="history-item"]').count();
  }

  async selectFromHistory(index: number) {
    await this.historyList.locator('[data-testid="history-item"]').nth(index).click();
  }
}
