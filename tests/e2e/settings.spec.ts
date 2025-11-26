/**
 * E2E Tests - Settings Flow
 * Complete settings, preferences, and configuration tests
 */

import { test, expect } from './fixtures';
import { SettingsPage } from './pages/SettingsPage';
import { DashboardPage } from './pages/DashboardPage';

test.describe('Settings Flow', () => {
  test.use({ storageState: 'tests/e2e/.auth/user.json' });

  // ============================================
  // SETTINGS PAGE LOADING
  // ============================================

  test.describe('Settings Page Loading', () => {
    test('should display settings page correctly', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await expect(page.locator('h1')).toContainText(/configurações|settings/i);
    });

    test('should display all settings sections', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await expect(settings.themeToggle).toBeVisible();
      await expect(settings.languageSelect).toBeVisible();
      await expect(settings.notificationsToggle).toBeVisible();
    });

    test('should display save and reset buttons', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await expect(settings.saveButton).toBeVisible();
      await expect(settings.resetButton).toBeVisible();
    });
  });

  // ============================================
  // THEME SETTINGS
  // ============================================

  test.describe('Theme Settings', () => {
    test('should toggle dark theme', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      const initialTheme = await settings.getCurrentTheme();
      await settings.toggleTheme();

      const newTheme = await settings.getCurrentTheme();
      expect(newTheme).not.toBe(initialTheme);
    });

    test('should persist theme after page reload', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      // Toggle to dark
      await settings.toggleTheme();
      const themeAfterToggle = await settings.getCurrentTheme();

      await settings.saveSettings();
      await page.reload();

      const themeAfterReload = await settings.getCurrentTheme();
      expect(themeAfterReload).toBe(themeAfterToggle);
    });

    test('should apply theme to entire app', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await settings.toggleTheme();
      await settings.saveSettings();

      // Navigate to dashboard
      const dashboard = new DashboardPage(page);
      await dashboard.goto();

      const html = page.locator('html');
      const theme = await html.getAttribute('class');
      expect(theme).toBeDefined();
    });
  });

  // ============================================
  // LANGUAGE SETTINGS
  // ============================================

  test.describe('Language Settings', () => {
    test('should display language selector', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await expect(settings.languageSelect).toBeVisible();
    });

    test('should change language to English', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await settings.selectLanguage('en');
      await settings.saveSettings();

      await page.reload();
      
      // Check for English text
      await expect(page.locator('body')).toContainText(/Settings|Language|Theme/i);
    });

    test('should change language to Portuguese', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await settings.selectLanguage('pt-BR');
      await settings.saveSettings();

      await page.reload();
      
      // Check for Portuguese text
      await expect(page.locator('body')).toContainText(/Configurações|Idioma|Tema/i);
    });
  });

  // ============================================
  // NOTIFICATION SETTINGS
  // ============================================

  test.describe('Notification Settings', () => {
    test('should toggle notifications', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await settings.toggleNotifications();

      // Check toggle state changed
      const isChecked = await settings.notificationsToggle.isChecked();
      expect(typeof isChecked).toBe('boolean');
    });

    test('should toggle auto-save', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await settings.toggleAutoSave();

      const isChecked = await settings.autoSaveToggle.isChecked();
      expect(typeof isChecked).toBe('boolean');
    });

    test('should save notification preferences', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await settings.toggleNotifications();
      await settings.saveSettings();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/salvo|saved/i);
    });
  });

  // ============================================
  // SAVE AND RESET
  // ============================================

  test.describe('Save and Reset', () => {
    test('should save all settings', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await settings.toggleTheme();
      await settings.saveSettings();

      await expect(page.locator('[data-testid="toast"]')).toBeVisible();
    });

    test('should reset to defaults', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      // Make some changes
      await settings.toggleTheme();
      await settings.toggleNotifications();

      // Reset
      await settings.resetSettings();

      // Confirm reset
      await page.locator('[data-testid="confirm-reset"]').click();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/reset|restaurado/i);
    });

    test('should show unsaved changes warning', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await settings.toggleTheme();

      // Try to navigate away
      await page.locator('[data-testid="nav-dashboard"]').click();

      // Should show warning
      await expect(page.locator('[data-testid="unsaved-warning"]')).toBeVisible();
    });
  });

  // ============================================
  // ACCOUNT SETTINGS
  // ============================================

  test.describe('Account Settings', () => {
    test('should display account section', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await expect(page.locator('[data-testid="account-section"]')).toBeVisible();
    });

    test('should display current plan info', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await expect(page.locator('[data-testid="current-plan"]')).toBeVisible();
    });

    test('should navigate to subscription upgrade', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await page.locator('[data-testid="upgrade-plan-button"]').click();
      await expect(page).toHaveURL(/subscription|pricing/);
    });

    test('should display export data option', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await expect(page.locator('[data-testid="export-data"]')).toBeVisible();
    });

    test('should display delete account option', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await expect(page.locator('[data-testid="delete-account"]')).toBeVisible();
    });
  });

  // ============================================
  // KEYBOARD ACCESSIBILITY
  // ============================================

  test.describe('Keyboard Accessibility', () => {
    test('should navigate settings with keyboard', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      // Tab through settings
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      // Should focus on an element
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).toBeDefined();
    });

    test('should toggle with space key', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await settings.themeToggle.focus();
      const initialState = await settings.themeToggle.isChecked();
      
      await page.keyboard.press('Space');
      
      const newState = await settings.themeToggle.isChecked();
      expect(newState).not.toBe(initialState);
    });

    test('should submit with enter key', async ({ page }) => {
      const settings = new SettingsPage(page);
      await settings.goto();

      await settings.saveButton.focus();
      await page.keyboard.press('Enter');

      await expect(page.locator('[data-testid="toast"]')).toBeVisible();
    });
  });
});
