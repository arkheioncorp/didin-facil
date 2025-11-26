/**
 * Settings Page Object Model
 */
import { Page, Locator, expect } from "@playwright/test";

export class SettingsPage {
  readonly page: Page;
  readonly themeToggle: Locator;
  readonly languageSelect: Locator;
  readonly notificationsToggle: Locator;
  readonly autoSaveToggle: Locator;
  readonly saveButton: Locator;
  readonly resetButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.themeToggle = page.locator('[data-testid="theme-toggle"]');
    this.languageSelect = page.locator('[data-testid="language-select"]');
    this.notificationsToggle = page.locator('[data-testid="notifications-toggle"]');
    this.autoSaveToggle = page.locator('[data-testid="autosave-toggle"]');
    this.saveButton = page.locator('[data-testid="save-settings"]');
    this.resetButton = page.locator('[data-testid="reset-settings"]');
  }

  async goto() {
    await this.page.goto("/settings");
    await this.page.waitForLoadState("networkidle");
  }

  async toggleTheme() {
    await this.themeToggle.click();
  }

  async selectLanguage(lang: string) {
    await this.languageSelect.click();
    await this.page.locator(`[data-value="${lang}"]`).click();
  }

  async toggleNotifications() {
    await this.notificationsToggle.click();
  }

  async toggleAutoSave() {
    await this.autoSaveToggle.click();
  }

  async saveSettings() {
    await this.saveButton.click();
  }

  async resetSettings() {
    await this.resetButton.click();
  }

  async getCurrentTheme(): Promise<string> {
    const html = this.page.locator("html");
    return (await html.getAttribute("class")) || "light";
  }
}
