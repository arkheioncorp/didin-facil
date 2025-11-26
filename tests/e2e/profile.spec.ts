/**
 * E2E Tests - Profile Flow
 * Complete user profile management tests
 */

import { test, expect } from './fixtures';

test.describe('Profile Flow', () => {
  test.use({ storageState: 'tests/e2e/.auth/user.json' });

  // ============================================
  // PROFILE PAGE LOADING
  // ============================================

  test.describe('Profile Page Loading', () => {
    test('should display profile page correctly', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('h1')).toContainText(/perfil|profile/i);
    });

    test('should display user avatar', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="user-avatar"]')).toBeVisible();
    });

    test('should display user information', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="user-name"]')).toBeVisible();
      await expect(page.locator('[data-testid="user-email"]')).toBeVisible();
    });

    test('should display current plan badge', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="plan-badge"]')).toBeVisible();
    });
  });

  // ============================================
  // EDIT PROFILE
  // ============================================

  test.describe('Edit Profile', () => {
    test('should enable edit mode', async ({ page }) => {
      await page.goto('/profile');

      await page.locator('[data-testid="edit-profile"]').click();

      await expect(page.locator('[data-testid="name-input"]')).toBeEnabled();
    });

    test('should update user name', async ({ page }) => {
      await page.goto('/profile');

      await page.locator('[data-testid="edit-profile"]').click();
      await page.locator('[data-testid="name-input"]').fill('Novo Nome');
      await page.locator('[data-testid="save-profile"]').click();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/salvo|saved/i);
    });

    test('should upload new avatar', async ({ page }) => {
      await page.goto('/profile');

      const fileInput = page.locator('[data-testid="avatar-input"]');
      
      // Create a test file
      await fileInput.setInputFiles({
        name: 'avatar.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-content')
      });

      await expect(page.locator('[data-testid="avatar-preview"]')).toBeVisible();
    });

    test('should cancel edit mode', async ({ page }) => {
      await page.goto('/profile');

      await page.locator('[data-testid="edit-profile"]').click();
      await page.locator('[data-testid="name-input"]').fill('Mudança que será cancelada');
      await page.locator('[data-testid="cancel-edit"]').click();

      await expect(page.locator('[data-testid="name-input"]')).not.toBeVisible();
    });
  });

  // ============================================
  // USAGE STATISTICS
  // ============================================

  test.describe('Usage Statistics', () => {
    test('should display usage stats section', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="usage-stats"]')).toBeVisible();
    });

    test('should show products searched count', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="products-searched"]')).toBeVisible();
    });

    test('should show copies generated count', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="copies-generated"]')).toBeVisible();
    });

    test('should show favorites count', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="favorites-count"]')).toBeVisible();
    });
  });

  // ============================================
  // SUBSCRIPTION INFO
  // ============================================

  test.describe('Subscription Info', () => {
    test('should display subscription section', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="subscription-section"]')).toBeVisible();
    });

    test('should show plan expiration date', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="plan-expiration"]')).toBeVisible();
    });

    test('should navigate to upgrade page', async ({ page }) => {
      await page.goto('/profile');

      await page.locator('[data-testid="upgrade-button"]').click();
      await expect(page).toHaveURL(/subscription|pricing/);
    });
  });

  // ============================================
  // CONNECTED DEVICES
  // ============================================

  test.describe('Connected Devices', () => {
    test('should display devices section', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="devices-section"]')).toBeVisible();
    });

    test('should show current device', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="current-device"]')).toBeVisible();
      await expect(page.locator('[data-testid="current-device"]')).toContainText(/atual|current/i);
    });

    test('should disconnect other device', async ({ page }) => {
      await page.goto('/profile');

      const otherDevice = page.locator('[data-testid="device-item"]:not([data-current="true"])').first();
      
      if (await otherDevice.isVisible()) {
        await otherDevice.locator('[data-testid="disconnect-device"]').click();
        await page.locator('[data-testid="confirm-disconnect"]').click();
        
        await expect(page.locator('[data-testid="toast"]')).toContainText(/desconectado|disconnected/i);
      }
    });
  });

  // ============================================
  // SECURITY SETTINGS
  // ============================================

  test.describe('Security Settings', () => {
    test('should display security section', async ({ page }) => {
      await page.goto('/profile');

      await expect(page.locator('[data-testid="security-section"]')).toBeVisible();
    });

    test('should open change password modal', async ({ page }) => {
      await page.goto('/profile');

      await page.locator('[data-testid="change-password"]').click();
      await expect(page.locator('[data-testid="password-modal"]')).toBeVisible();
    });

    test('should validate password requirements', async ({ page }) => {
      await page.goto('/profile');

      await page.locator('[data-testid="change-password"]').click();
      await page.locator('[data-testid="new-password"]').fill('weak');
      
      await expect(page.locator('[data-testid="password-error"]')).toBeVisible();
    });

    test('should enable two-factor auth', async ({ page }) => {
      await page.goto('/profile');

      await page.locator('[data-testid="enable-2fa"]').click();
      await expect(page.locator('[data-testid="2fa-setup-modal"]')).toBeVisible();
    });
  });
});
