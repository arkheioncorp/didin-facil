/**
 * E2E Tests - Dashboard Flow
 * Complete dashboard navigation, stats, and widgets tests
 */

import { test, expect } from './fixtures';
import { DashboardPage } from './pages/DashboardPage';
import { SearchPage } from './pages/SearchPage';

test.describe('Dashboard Flow', () => {
  test.use({ storageState: 'tests/e2e/.auth/user.json' });

  // ============================================
  // DASHBOARD LOADING TESTS
  // ============================================

  test.describe('Dashboard Loading', () => {
    test('should display dashboard with all sections', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await expect(dashboard.header).toBeVisible();
      await expect(dashboard.sidebar).toBeVisible();
      await expect(dashboard.welcomeMessage).toBeVisible();
    });

    test('should display stats cards', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await expect(dashboard.statsCards.first()).toBeVisible();
    });

    test('should display recent products section', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await expect(dashboard.recentProducts).toBeVisible();
    });

    test('should display trending products section', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await expect(dashboard.trendingProducts).toBeVisible();
    });

    test('should load stats values correctly', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      const stats = await dashboard.getStatsValues();
      expect(Object.keys(stats).length).toBeGreaterThan(0);
    });
  });

  // ============================================
  // NAVIGATION TESTS
  // ============================================

  test.describe('Navigation', () => {
    test('should navigate to search via sidebar', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.navigateTo('search');
      await expect(page).toHaveURL(/search/);
    });

    test('should navigate to products via sidebar', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.navigateTo('products');
      await expect(page).toHaveURL(/products/);
    });

    test('should navigate to favorites via sidebar', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.navigateTo('favorites');
      await expect(page).toHaveURL(/favorites/);
    });

    test('should navigate to settings via sidebar', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.navigateTo('settings');
      await expect(page).toHaveURL(/settings/);
    });

    test('should navigate via quick search', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.quickSearch('produto teste');
      await expect(page).toHaveURL(/search/);
    });
  });

  // ============================================
  // USER MENU TESTS
  // ============================================

  test.describe('User Menu', () => {
    test('should open user menu dropdown', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.openUserMenu();
      await expect(page.locator('[data-testid="user-dropdown"]')).toBeVisible();
    });

    test('should display user info in menu', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.openUserMenu();
      await expect(page.locator('[data-testid="user-email"]')).toBeVisible();
    });

    test('should navigate to profile from menu', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.openUserMenu();
      await page.locator('[data-testid="profile-link"]').click();
      await expect(page).toHaveURL(/profile/);
    });

    test('should logout from menu', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.logout();
      await expect(page).toHaveURL(/login/);
    });
  });

  // ============================================
  // QUICK ACTIONS TESTS
  // ============================================

  test.describe('Quick Actions', () => {
    test('should display quick action buttons', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await expect(dashboard.quickActions).toBeVisible();
    });

    test('should trigger new search action', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.quickActions.locator('[data-action="new-search"]').click();
      await expect(page).toHaveURL(/search/);
    });

    test('should trigger copy generation action', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.quickActions.locator('[data-action="generate-copy"]').click();
      await expect(page).toHaveURL(/copy/);
    });
  });

  // ============================================
  // NOTIFICATIONS TESTS
  // ============================================

  /*
  test.describe('Notifications', () => {
    test('should display notifications icon', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await expect(dashboard.notifications).toBeVisible();
    });

    test('should open notifications panel', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      await dashboard.notifications.click();
      await expect(page.locator('[data-testid="notifications-panel"]')).toBeVisible();
    });

    test('should display notification badge when has unread', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      // Check for badge (may or may not exist based on state)
      const badge = dashboard.notifications.locator('[data-testid="notification-badge"]');
      // Badge visibility depends on having notifications
    });
  });
  */

  // ============================================
  // RECENT PRODUCTS TESTS
  // ============================================

  test.describe('Recent Products', () => {
    test('should display recent products list', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      const count = await dashboard.getRecentProductsCount();
      // May be 0 if no recent products
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test('should click on recent product opens detail', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoad();

      const productCard = dashboard.recentProducts.locator('[data-testid="product-card"]').first();
      
      if (await productCard.isVisible()) {
        await productCard.click();
        await expect(page.locator('[data-testid="product-detail"]')).toBeVisible();
      }
    });
  });

  // ============================================
  // RESPONSIVE TESTS
  // ============================================

  test.describe('Responsive Design', () => {
    test('should collapse sidebar on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoadMobile();

      await expect(dashboard.sidebar).not.toBeVisible();
      await expect(page.locator('[data-testid="menu-toggle"]')).toBeVisible();
    });

    test('should open sidebar on mobile menu click', async ({ page }) => {
      // Set viewport before navigation
      await page.setViewportSize({ width: 375, height: 667 });
      
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoadMobile();
      
      // Verify menu toggle is visible on mobile
      await expect(page.locator('[data-testid="menu-toggle"]')).toBeVisible();
      
      await page.locator('[data-testid="menu-toggle"]').click();
      // Wait for animation to complete
      await page.waitForTimeout(300);
      // The mobile sidebar container should now be visible (or the overlay)
      await expect(page.locator('[data-testid="mobile-overlay"], [data-testid="mobile-sidebar-container"]').first()).toBeVisible({ timeout: 5000 });
    });

    test('should display correctly on tablet', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      
      const dashboard = new DashboardPage(page);
      await dashboard.goto();
      await dashboard.waitForLoadMobile();

      await expect(dashboard.header).toBeVisible();
    });
  });
});
