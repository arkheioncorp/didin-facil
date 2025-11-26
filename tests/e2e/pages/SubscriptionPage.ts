/**
 * Subscription Page Object Model
 */
import { Page, Locator, expect } from "@playwright/test";

export class SubscriptionPage {
  readonly page: Page;
  readonly planCards: Locator;
  readonly currentPlan: Locator;
  readonly upgradeButton: Locator;
  readonly cancelButton: Locator;
  readonly paymentForm: Locator;
  readonly checkoutButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.planCards = page.locator('[data-testid="plan-card"]');
    this.currentPlan = page.locator('[data-testid="current-plan"]');
    this.upgradeButton = page.locator('[data-testid="upgrade-button"]');
    this.cancelButton = page.locator('[data-testid="cancel-subscription"]');
    this.paymentForm = page.locator('[data-testid="payment-form"]');
    this.checkoutButton = page.locator('[data-testid="checkout-button"]');
  }

  async goto() {
    await this.page.goto("/subscription");
    await this.page.waitForLoadState("networkidle");
  }

  async selectPlan(planId: string) {
    await this.page.locator(`[data-testid="plan-${planId}"]`).click();
  }

  async getCurrentPlanName(): Promise<string> {
    return (await this.currentPlan.textContent()) || "";
  }

  async getPlanCount(): Promise<number> {
    return await this.planCards.count();
  }

  async getPlanPrice(planId: string): Promise<string> {
    const card = this.page.locator(`[data-testid="plan-${planId}"]`);
    return (await card.locator('[data-testid="plan-price"]').textContent()) || "";
  }

  async initiateUpgrade(planId: string) {
    await this.selectPlan(planId);
    await this.upgradeButton.click();
    await expect(this.paymentForm).toBeVisible();
  }

  async completeCheckout() {
    await this.checkoutButton.click();
  }

  async cancelSubscription() {
    await this.cancelButton.click();
    await this.page.locator('[data-testid="confirm-cancel"]').click();
  }
}
