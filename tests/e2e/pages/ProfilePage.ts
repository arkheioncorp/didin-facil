/**
 * Profile Page Object Model
 */
import { Page, Locator, expect } from "@playwright/test";

export class ProfilePage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly userAvatar: Locator;
  readonly userName: Locator;
  readonly userEmail: Locator;
  readonly planBadge: Locator;
  readonly editButton: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;
  readonly nameInput: Locator;
  readonly avatarInput: Locator;
  readonly usageStats: Locator;
  readonly subscriptionSection: Locator;
  readonly devicesSection: Locator;
  readonly securitySection: Locator;
  readonly upgradeButton: Locator;
  readonly changePasswordButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('h1');
    this.userAvatar = page.locator('[data-testid="user-avatar"]');
    this.userName = page.locator('[data-testid="user-name"]');
    this.userEmail = page.locator('[data-testid="user-email"]');
    this.planBadge = page.locator('[data-testid="plan-badge"]');
    this.editButton = page.locator('[data-testid="edit-profile"]');
    this.saveButton = page.locator('[data-testid="save-profile"]');
    this.cancelButton = page.locator('[data-testid="cancel-edit"]');
    this.nameInput = page.locator('[data-testid="name-input"]');
    this.avatarInput = page.locator('[data-testid="avatar-input"]');
    this.usageStats = page.locator('[data-testid="usage-stats"]');
    this.subscriptionSection = page.locator('[data-testid="subscription-section"]');
    this.devicesSection = page.locator('[data-testid="devices-section"]');
    this.securitySection = page.locator('[data-testid="security-section"]');
    this.upgradeButton = page.locator('[data-testid="upgrade-button"]');
    this.changePasswordButton = page.locator('[data-testid="change-password"]');
  }

  async goto() {
    await this.page.goto("/profile");
    await this.page.waitForLoadState("networkidle");
  }

  async enableEditMode() {
    await this.editButton.click();
    await expect(this.nameInput).toBeEnabled();
  }

  async updateName(name: string) {
    await this.nameInput.fill(name);
  }

  async saveProfile() {
    await this.saveButton.click();
  }

  async cancelEdit() {
    await this.cancelButton.click();
  }

  async uploadAvatar(filePath: string) {
    await this.avatarInput.setInputFiles(filePath);
  }

  async navigateToUpgrade() {
    await this.upgradeButton.click();
    await this.page.waitForURL(/subscription|pricing/);
  }

  async openChangePassword() {
    await this.changePasswordButton.click();
    await expect(this.page.locator('[data-testid="password-modal"]')).toBeVisible();
  }

  async getCurrentPlan(): Promise<string> {
    return (await this.planBadge.textContent()) || '';
  }

  async getUsageStats(): Promise<Record<string, string>> {
    const stats: Record<string, string> = {};
    
    const productsSearched = await this.page.locator('[data-testid="products-searched"]').textContent();
    const copiesGenerated = await this.page.locator('[data-testid="copies-generated"]').textContent();
    const favoritesCount = await this.page.locator('[data-testid="favorites-count"]').textContent();
    
    if (productsSearched) stats.productsSearched = productsSearched;
    if (copiesGenerated) stats.copiesGenerated = copiesGenerated;
    if (favoritesCount) stats.favoritesCount = favoritesCount;
    
    return stats;
  }
}
