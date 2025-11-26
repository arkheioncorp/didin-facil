/**
 * Favorites Page Object Model
 */
import { Page, Locator, expect } from "@playwright/test";

export class FavoritesPage {
  readonly page: Page;
  readonly lists: Locator;
  readonly createListButton: Locator;
  readonly favoriteItems: Locator;
  readonly emptyState: Locator;
  readonly exportButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.lists = page.locator('[data-testid="favorite-list"]');
    this.createListButton = page.locator('[data-testid="create-list-button"]');
    this.favoriteItems = page.locator('[data-testid="favorite-item"]');
    this.emptyState = page.locator('[data-testid="empty-favorites"]');
    this.exportButton = page.locator('[data-testid="export-button"]');
  }

  async goto() {
    await this.page.goto("/favorites");
    await this.page.waitForLoadState("networkidle");
  }

  async createList(name: string, description?: string) {
    await this.createListButton.click();
    await this.page.locator('[data-testid="list-name-input"]').fill(name);
    if (description) {
      await this.page.locator('[data-testid="list-description-input"]').fill(description);
    }
    await this.page.locator('[data-testid="save-list-button"]').click();
  }

  async selectList(index: number) {
    await this.lists.nth(index).click();
  }

  async getListCount(): Promise<number> {
    return await this.lists.count();
  }

  async getFavoriteCount(): Promise<number> {
    return await this.favoriteItems.count();
  }

  async removeFavorite(index: number) {
    await this.favoriteItems.nth(index).locator('[data-testid="remove-favorite"]').click();
  }

  async exportFavorites(format: string) {
    await this.exportButton.click();
    await this.page.locator(`[data-testid="export-${format}"]`).click();
  }

  async isEmpty(): Promise<boolean> {
    return await this.emptyState.isVisible();
  }
}
