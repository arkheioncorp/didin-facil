/**
 * Products Page Object Model
 */
import { Page, Locator, expect } from "@playwright/test";

export class ProductsPage {
  readonly page: Page;
  readonly productsGrid: Locator;
  readonly productCards: Locator;
  readonly viewToggle: Locator;
  readonly sortDropdown: Locator;
  readonly filterPanel: Locator;
  readonly categorySelect: Locator;
  readonly minPriceInput: Locator;
  readonly maxPriceInput: Locator;
  readonly trendingToggle: Locator;
  readonly clearFiltersButton: Locator;
  readonly activeFilterCount: Locator;
  readonly paginationContainer: Locator;
  readonly previousButton: Locator;
  readonly nextButton: Locator;
  readonly currentPageIndicator: Locator;
  readonly favoriteButton: Locator;
  readonly productDetailModal: Locator;

  constructor(page: Page) {
    this.page = page;
    this.productsGrid = page.locator('[data-testid="products-grid"]');
    this.productCards = page.locator('[data-testid="product-card"]');
    this.viewToggle = page.locator('[data-testid="view-toggle"]');
    this.sortDropdown = page.locator('[data-testid="sort-dropdown"]');
    this.filterPanel = page.locator('[data-testid="filter-panel"], [data-testid="filters-panel"]');
    this.categorySelect = page.locator('[data-testid="category-select"]');
    this.minPriceInput = page.locator('[data-testid="min-price-input"]');
    this.maxPriceInput = page.locator('[data-testid="max-price-input"]');
    this.trendingToggle = page.locator('[data-testid="trending-toggle"]');
    this.clearFiltersButton = page.locator('[data-testid="clear-filters"]');
    this.activeFilterCount = page.locator('[data-testid="active-filter-count"]');
    this.paginationContainer = page.locator('[data-testid="pagination"]');
    this.previousButton = page.locator('[data-testid="prev-page"]');
    this.nextButton = page.locator('[data-testid="next-page"]');
    this.currentPageIndicator = page.locator('[data-testid="current-page"]');
    this.favoriteButton = page.locator('[data-testid="favorite-button"]');
    this.productDetailModal = page.locator('[data-testid="product-detail-modal"], [role="dialog"]');
  }

  async goto() {
    await this.page.goto("/products");
    await this.page.waitForLoadState("networkidle");
  }

  async getProductCount(): Promise<number> {
    return await this.productCards.count();
  }

  async clickProduct(index: number) {
    await this.productCards.nth(index).click();
  }

  async toggleView() {
    await this.viewToggle.click();
  }

  async sortBy(option: string) {
    await this.sortDropdown.click();
    await this.page.locator(`[data-value="${option}"]`).click();
  }

  // Filter methods
  async selectCategory(category: string) {
    await this.categorySelect.click();
    await this.page.locator(`[data-value="${category}"]`).click();
  }

  async setPriceRange(min: number, max: number) {
    await this.minPriceInput.fill(String(min));
    await this.maxPriceInput.fill(String(max));
    await this.page.keyboard.press('Enter');
  }

  async toggleTrendingFilter() {
    await this.trendingToggle.click();
  }

  async clearFilters() {
    await this.clearFiltersButton.click();
  }

  // Pagination methods
  async nextPage() {
    await this.nextButton.click();
  }

  async previousPage() {
    await this.previousButton.click();
  }

  async goToPage(pageNumber: number) {
    await this.paginationContainer.locator(`[data-page="${pageNumber}"]`).click();
  }

  // Favorite methods
  async favoriteFirstProduct() {
    await this.favoriteButton.first().click();
  }

  async favoriteProduct(index: number) {
    await this.favoriteButton.nth(index).click();
  }
}
