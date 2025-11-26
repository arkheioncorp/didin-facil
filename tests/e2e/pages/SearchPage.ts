/**
 * Search Page Object Model
 * Page object for the search page with filters
 */
import { Page, Locator, expect } from "@playwright/test";

export class SearchPage {
  readonly page: Page;
  readonly searchInput: Locator;
  readonly searchButton: Locator;
  readonly filtersPanel: Locator;
  readonly categoryFilter: Locator;
  readonly priceRangeSlider: Locator;
  readonly minPriceInput: Locator;
  readonly maxPriceInput: Locator;
  readonly ratingFilter: Locator;
  readonly sortSelect: Locator;
  readonly resultsGrid: Locator;
  readonly resultsContainer: Locator;
  readonly resultCount: Locator;
  readonly pagination: Locator;
  readonly clearFiltersButton: Locator;
  readonly loadingIndicator: Locator;
  readonly noResultsMessage: Locator;
  readonly productCards: Locator;
  readonly suggestionsList: Locator;
  readonly recentSearches: Locator;

  constructor(page: Page) {
    this.page = page;
    this.searchInput = page.locator('[data-testid="search-input"]');
    this.searchButton = page.locator('[data-testid="search-button"]');
    this.filtersPanel = page.locator('[data-testid="filters-panel"]');
    this.categoryFilter = page.locator('[data-testid="category-filter"]');
    this.priceRangeSlider = page.locator('[data-testid="price-range-slider"]');
    this.minPriceInput = page.locator('[data-testid="min-price-input"]');
    this.maxPriceInput = page.locator('[data-testid="max-price-input"]');
    this.ratingFilter = page.locator('[data-testid="rating-filter"]');
    this.sortSelect = page.locator('[data-testid="sort-select"]');
    this.resultsGrid = page.locator('[data-testid="results-grid"]');
    this.resultsContainer = page.locator('[data-testid="results-container"], [data-testid="results-grid"]');
    this.resultCount = page.locator('[data-testid="result-count"]');
    this.pagination = page.locator('[data-testid="pagination"]');
    this.clearFiltersButton = page.locator('[data-testid="clear-filters"]');
    this.loadingIndicator = page.locator('[data-testid="loading-indicator"], [data-testid="loading"]');
    this.noResultsMessage = page.locator('[data-testid="no-results"]');
    this.productCards = page.locator('[data-testid="product-card"]');
    this.suggestionsList = page.locator('[data-testid="suggestions-list"], [role="listbox"]');
    this.recentSearches = page.locator('[data-testid="recent-searches"]');
  }

  // Navigate to search page
  async goto(query?: string) {
    const url = query ? `/search?q=${encodeURIComponent(query)}` : "/search";
    await this.page.goto(url);
    await this.page.waitForLoadState("networkidle");
  }

  // Perform search
  async search(query: string) {
    await this.searchInput.fill(query);
    await this.searchButton.click();
    await this.waitForResults();
  }

  // Wait for search results
  async waitForResults() {
    await expect(this.loadingIndicator).toBeHidden({ timeout: 10000 });
    await this.page.waitForLoadState("networkidle");
  }

  // Apply category filter
  async filterByCategory(category: string) {
    await this.categoryFilter.click();
    await this.page.locator(`[data-testid="category-option-${category}"]`).click();
    await this.waitForResults();
  }

  // Apply price range filter
  async filterByPriceRange(min: number, max: number) {
    await this.minPriceInput.fill(min.toString());
    await this.maxPriceInput.fill(max.toString());
    await this.page.keyboard.press("Enter");
    await this.waitForResults();
  }

  // Apply rating filter
  async filterByRating(minRating: number) {
    await this.ratingFilter.locator(`[data-testid="rating-${minRating}"]`).click();
    await this.waitForResults();
  }

  // Apply sorting
  async sortBy(option: string) {
    await this.sortSelect.click();
    await this.page.locator(`[data-testid="sort-option-${option}"]`).click();
    await this.waitForResults();
  }

  // Clear all filters
  async clearFilters() {
    await this.clearFiltersButton.click();
    await this.waitForResults();
  }

  // Get result count
  async getResultCount(): Promise<number> {
    const text = await this.resultCount.textContent();
    const match = text?.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  // Get product cards
  async getProductCards() {
    return await this.resultsGrid.locator('[data-testid="product-card"]').all();
  }

  // Get product card info
  async getProductInfo(index: number): Promise<{
    title: string;
    price: string;
    rating: string;
  }> {
    const cards = await this.getProductCards();
    const card = cards[index];

    return {
      title: (await card.locator('[data-testid="product-title"]').textContent()) || "",
      price: (await card.locator('[data-testid="product-price"]').textContent()) || "",
      rating: (await card.locator('[data-testid="product-rating"]').textContent()) || "",
    };
  }

  // Navigate to next page
  async nextPage() {
    await this.pagination.locator('[data-testid="next-page"]').click();
    await this.waitForResults();
  }

  // Navigate to previous page
  async previousPage() {
    await this.pagination.locator('[data-testid="prev-page"]').click();
    await this.waitForResults();
  }

  // Go to specific page
  async goToPage(pageNumber: number) {
    await this.pagination.locator(`[data-testid="page-${pageNumber}"]`).click();
    await this.waitForResults();
  }

  // Get current page number
  async getCurrentPage(): Promise<number> {
    const activePage = await this.pagination.locator('[data-testid="page-active"]').textContent();
    return activePage ? parseInt(activePage, 10) : 1;
  }

  // Check if no results
  async hasNoResults(): Promise<boolean> {
    return await this.noResultsMessage.isVisible();
  }

  // Click on product card
  async clickProduct(index: number) {
    const cards = await this.getProductCards();
    await cards[index].click();
  }

  // Add product to favorites
  async addToFavorites(index: number) {
    const cards = await this.getProductCards();
    await cards[index].locator('[data-testid="favorite-button"]').click();
  }

  // Submit search
  async submitSearch() {
    await this.searchButton.click();
    await this.waitForResults();
  }

  // Clear search
  async clearSearch() {
    await this.searchInput.clear();
  }

  // Get applied filters
  async getAppliedFilters(): Promise<string[]> {
    const tags = await this.filtersPanel.locator('[data-testid="filter-tag"]').all();
    const filters: string[] = [];
    for (const tag of tags) {
      const text = await tag.textContent();
      if (text) filters.push(text);
    }
    return filters;
  }
}
