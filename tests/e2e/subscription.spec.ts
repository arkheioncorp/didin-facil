/**
 * E2E Tests - Subscription and Payment Flow
 * Complete subscription management, payment, and plan tests
 */

import { test, expect } from './fixtures';
import { SubscriptionPage } from './pages/SubscriptionPage';
import { SettingsPage } from './pages/SettingsPage';

test.describe('Subscription and Payment Flow', () => {
  test.use({ storageState: 'tests/e2e/.auth/user.json' }); // Use authenticated state

  // ============================================
  // SUBSCRIPTION DISPLAY TESTS
  // ============================================

  test.describe('Subscription Display', () => {
    test('should display current subscription status', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await expect(subscriptionPage.currentPlanCard).toBeVisible();
      await expect(subscriptionPage.planName).toBeVisible();
    });

    test('should show plan features', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await expect(subscriptionPage.featuresList).toBeVisible();
      await expect(subscriptionPage.featuresList.locator('li').first()).toBeVisible();
    });

    test('should display billing information', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await expect(subscriptionPage.billingSection).toBeVisible();
      await expect(subscriptionPage.nextBillingDate).toBeVisible();
    });

    test('should show usage statistics', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await expect(subscriptionPage.usageSection).toBeVisible();
      await expect(subscriptionPage.copyUsage).toBeVisible();
      await expect(subscriptionPage.searchUsage).toBeVisible();
    });
  });

  // ============================================
  // PLAN COMPARISON TESTS
  // ============================================

  test.describe('Plan Comparison', () => {
    test('should display all available plans', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await expect(subscriptionPage.planCards).toHaveCount(3); // Free, Pro, Enterprise
    });

    test('should highlight current plan', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await expect(subscriptionPage.currentPlanCard).toHaveClass(/current|active|selected/);
    });

    test('should show plan prices', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      const proPlan = subscriptionPage.planCards.filter({ hasText: /pro/i });
      await expect(proPlan.locator('[data-testid="price"]')).toContainText(/R\$|BRL/);
    });

    test('should toggle between monthly and yearly pricing', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.toggleBillingPeriod('yearly');

      await expect(subscriptionPage.yearlyToggle).toBeChecked();
      // Prices should update
      const proPlan = subscriptionPage.planCards.filter({ hasText: /pro/i });
      await expect(proPlan.locator('[data-testid="price"]')).toContainText(/ano|year/i);
    });

    test('should show discount for yearly plans', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.toggleBillingPeriod('yearly');

      await expect(subscriptionPage.discountBadge).toBeVisible();
      await expect(subscriptionPage.discountBadge).toContainText(/\d+%/);
    });

    test('should compare features between plans', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.openComparison();

      await expect(subscriptionPage.comparisonTable).toBeVisible();
    });
  });

  // ============================================
  // UPGRADE FLOW TESTS
  // ============================================

  test.describe('Upgrade Flow', () => {
    test('should show upgrade button for free plan', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await expect(subscriptionPage.upgradeButton).toBeVisible();
    });

    test('should open checkout modal on upgrade click', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickUpgrade('pro');

      await expect(subscriptionPage.checkoutModal).toBeVisible();
    });

    test('should display payment methods', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickUpgrade('pro');

      await expect(subscriptionPage.paymentMethods).toBeVisible();
      await expect(subscriptionPage.pixOption).toBeVisible();
      await expect(subscriptionPage.cardOption).toBeVisible();
    });

    test('should generate PIX QR code', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickUpgrade('pro');
      await subscriptionPage.selectPaymentMethod('pix');

      await expect(subscriptionPage.pixQRCode).toBeVisible();
      await expect(subscriptionPage.pixCode).toBeVisible();
    });

    test('should copy PIX code to clipboard', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickUpgrade('pro');
      await subscriptionPage.selectPaymentMethod('pix');
      await subscriptionPage.copyPixCode();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/copiado|copied/i);
    });

    test('should show credit card form', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickUpgrade('pro');
      await subscriptionPage.selectPaymentMethod('card');

      await expect(subscriptionPage.cardNumberInput).toBeVisible();
      await expect(subscriptionPage.cardExpiryInput).toBeVisible();
      await expect(subscriptionPage.cardCVVInput).toBeVisible();
    });

    test('should validate credit card fields', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickUpgrade('pro');
      await subscriptionPage.selectPaymentMethod('card');
      await subscriptionPage.submitPayment();

      await expect(subscriptionPage.cardNumberError).toBeVisible();
    });

    test('should show order summary', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickUpgrade('pro');

      await expect(subscriptionPage.orderSummary).toBeVisible();
      await expect(subscriptionPage.orderTotal).toBeVisible();
    });

    test('should apply coupon code', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickUpgrade('pro');
      await subscriptionPage.applyCoupon('DISCOUNT20');

      await expect(subscriptionPage.couponApplied).toBeVisible();
      await expect(subscriptionPage.discountAmount).toBeVisible();
    });

    test('should show error for invalid coupon', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickUpgrade('pro');
      await subscriptionPage.applyCoupon('INVALIDCODE');

      await expect(subscriptionPage.couponError).toBeVisible();
    });
  });

  // ============================================
  // DOWNGRADE FLOW TESTS
  // ============================================

  test.describe('Downgrade Flow', () => {
    test('should show downgrade option for paid plans', async ({ page }) => {
      // Assume user has pro plan
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await expect(subscriptionPage.downgradeLink).toBeVisible();
    });

    test('should show downgrade confirmation', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickDowngrade();

      await expect(subscriptionPage.downgradeConfirmModal).toBeVisible();
      await expect(subscriptionPage.downgradeWarning).toContainText(/perder|lose/i);
    });

    test('should list features that will be lost', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickDowngrade();

      await expect(subscriptionPage.lostFeaturesList).toBeVisible();
    });

    test('should allow canceling downgrade', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickDowngrade();
      await subscriptionPage.cancelDowngrade();

      await expect(subscriptionPage.downgradeConfirmModal).not.toBeVisible();
    });
  });

  // ============================================
  // CANCELLATION FLOW TESTS
  // ============================================

  test.describe('Cancellation Flow', () => {
    test('should show cancel subscription option', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await expect(subscriptionPage.cancelSubscriptionLink).toBeVisible();
    });

    test('should show cancellation survey', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickCancelSubscription();

      await expect(subscriptionPage.cancellationSurvey).toBeVisible();
    });

    test('should require reason for cancellation', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickCancelSubscription();
      await subscriptionPage.confirmCancellation();

      await expect(subscriptionPage.reasonError).toBeVisible();
    });

    test('should offer retention discount', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickCancelSubscription();
      await subscriptionPage.selectCancellationReason('too_expensive');

      await expect(subscriptionPage.retentionOffer).toBeVisible();
      await expect(subscriptionPage.retentionOffer).toContainText(/desconto|discount/i);
    });

    test('should show end date after cancellation', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.clickCancelSubscription();
      await subscriptionPage.selectCancellationReason('not_using');
      await subscriptionPage.confirmCancellation();

      await expect(subscriptionPage.subscriptionEndDate).toBeVisible();
    });
  });

  // ============================================
  // BILLING HISTORY TESTS
  // ============================================

  test.describe('Billing History', () => {
    test('should display billing history', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.goToBillingHistory();

      await expect(subscriptionPage.billingHistoryList).toBeVisible();
    });

    test('should show invoice details', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goToBillingHistory();

      await subscriptionPage.billingHistoryList.first().click();

      await expect(subscriptionPage.invoiceModal).toBeVisible();
      await expect(subscriptionPage.invoiceAmount).toBeVisible();
      await expect(subscriptionPage.invoiceDate).toBeVisible();
    });

    test('should download invoice PDF', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goToBillingHistory();

      const downloadPromise = page.waitForEvent('download');
      await subscriptionPage.downloadInvoice(0);

      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.pdf$/);
    });

    test('should show payment status badges', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goToBillingHistory();

      await expect(subscriptionPage.paymentStatusBadge.first()).toBeVisible();
    });
  });

  // ============================================
  // LICENSE KEY TESTS
  // ============================================

  test.describe('License Key', () => {
    test('should display license key', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await expect(subscriptionPage.licenseKey).toBeVisible();
    });

    test('should copy license key', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await subscriptionPage.copyLicenseKey();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/copiado|copied/i);
    });

    test('should activate license with key', async ({ page }) => {
      const settingsPage = new SettingsPage(page);
      await settingsPage.goto();

      await settingsPage.licenseKeyInput.fill('NEW-LICENSE-KEY-123');
      await settingsPage.activateLicenseButton.click();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/ativad|activated/i);
    });

    test('should show error for invalid license key', async ({ page }) => {
      const settingsPage = new SettingsPage(page);
      await settingsPage.goto();

      await settingsPage.licenseKeyInput.fill('INVALID-KEY');
      await settingsPage.activateLicenseButton.click();

      await expect(settingsPage.licenseError).toBeVisible();
    });

    test('should show device count', async ({ page }) => {
      const subscriptionPage = new SubscriptionPage(page);
      await subscriptionPage.goto();

      await expect(subscriptionPage.deviceCount).toBeVisible();
      await expect(subscriptionPage.deviceCount).toHaveText(/\d+\s*\/\s*\d+/);
    });
  });
});
