/**
 * Dashboard Page Object Model
 * Page object for the main dashboard
 */
import { Page, Locator, expect } from "@playwright/test";

export class DashboardPage {
  readonly page: Page;
  readonly header: Locator;
  readonly sidebar: Locator;
  readonly userMenu: Locator;
  readonly searchInput: Locator;
  readonly statsCards: Locator;
  readonly recentProducts: Locator;
  readonly trendingProducts: Locator;
  readonly quickActions: Locator;
  readonly notifications: Locator;
  readonly welcomeMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.locator('[data-testid="header"]');
    this.sidebar = page.locator('[data-testid="sidebar"]');
    this.userMenu = page.locator('[data-testid="user-menu"]');
    this.searchInput = page.locator('[data-testid="search-input"]');
    this.statsCards = page.locator('[data-testid="stats-card"]');
    this.recentProducts = page.locator('[data-testid="recent-products"]');
    this.trendingProducts = page.locator('[data-testid="trending-products"]');
    this.quickActions = page.locator('[data-testid="quick-actions"]');
    this.notifications = page.locator('[data-testid="notifications"]');
    this.welcomeMessage = page.locator('[data-testid="welcome-message"], h1:has-text("Bem-vindo"), h1:has-text("Welcome")');
  }

  // Navigate to dashboard
  async goto() {
    await this.page.goto("/");
    await this.page.waitForLoadState("networkidle");
  }

  // Wait for dashboard to load
  async waitForLoad() {
    await expect(this.header).toBeVisible();
    await expect(this.sidebar).toBeVisible();
    // Wait for stats to load
    await this.page.waitForSelector('[data-testid="stats-card"]', {
      state: "visible",
      timeout: 10000,
    }).catch(() => {});
  }

  // Wait for dashboard to load on mobile (sidebar is hidden)
  async waitForLoadMobile() {
    await expect(this.header).toBeVisible();
    // Wait for stats to load
    await this.page.waitForSelector('[data-testid="stats-card"]', {
      state: "visible",
      timeout: 10000,
    }).catch(() => {});
  }

  // Get stats card values
  async getStatsValues(): Promise<Record<string, string>> {
    const cards = await this.statsCards.all();
    const stats: Record<string, string> = {};

    for (const card of cards) {
      const label = await card.locator('[data-testid="stat-label"]').textContent();
      const value = await card.locator('[data-testid="stat-value"]').textContent();
      if (label && value) {
        stats[label] = value;
      }
    }

    return stats;
  }

  // Navigate via sidebar
  async navigateTo(route: string) {
    await this.sidebar.locator(`[data-testid="nav-${route}"]`).click();
    await this.page.waitForURL(`**/${route}`);
  }

  // Open user menu
  async openUserMenu() {
    await this.userMenu.click();
    await expect(this.page.locator('[data-testid="user-dropdown"]')).toBeVisible();
  }

  // Logout via user menu
  async logout() {
    await this.openUserMenu();
    await this.page.locator('[data-testid="logout-button"]').click({ force: true });
    await this.page.waitForURL("**/login");
  }

  // Perform quick search
  async quickSearch(query: string) {
    await this.searchInput.fill(query);
    await this.page.keyboard.press("Enter");
    await this.page.waitForURL("**/search**");
  }

  // Get recent products count
  async getRecentProductsCount(): Promise<number> {
    const products = await this.recentProducts.locator('[data-testid="product-card"]').all();
    return products.length;
  }

  // Get trending products
  async getTrendingProducts(): Promise<string[]> {
    const products = await this.trendingProducts.locator('[data-testid="product-title"]').all();
    const titles: string[] = [];
    for (const product of products) {
      const title = await product.textContent();
      if (title) titles.push(title);
    }
    return titles;
  }

  // Check if user is authenticated
  async isAuthenticated(): Promise<boolean> {
    return await this.userMenu.isVisible();
  }

  // Open notifications
  async openNotifications() {
    await this.notifications.click();
    await expect(this.page.locator('[data-testid="notifications-panel"]')).toBeVisible();
  }

  // Get notification count
  async getNotificationCount(): Promise<number> {
    const badge = await this.notifications.locator('[data-testid="notification-badge"]').textContent();
    return badge ? parseInt(badge, 10) : 0;
  }
}
