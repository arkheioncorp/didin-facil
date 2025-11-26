/**
 * E2E Tests - Search and Filtering Flow
 * Complete product search, filters, and discovery tests
 */

import { test, expect } from './fixtures';
import { SearchPage } from './pages/SearchPage';
import { ProductsPage } from './pages/ProductsPage';

test.describe('Search and Filtering Flow', () => {
  test.use({ storageState: 'tests/e2e/.auth/user.json' }); // Use authenticated state

  // ============================================
  // SEARCH TESTS
  // ============================================

  test.describe('Search', () => {
    test('should display search interface correctly', async ({ page }) => {
      const searchPage = new SearchPage(page);
      await searchPage.goto();

      await expect(searchPage.searchInput).toBeVisible();
      await expect(searchPage.searchInput).toBeFocused();
    });

    test('should search products by keyword', async ({ page }) => {
      const searchPage = new SearchPage(page);
      await searchPage.goto();

      await searchPage.search('fone bluetooth');

      await expect(searchPage.resultsContainer).toBeVisible();
      await expect(searchPage.productCards.first()).toBeVisible();
    });

    test('should show loading state during search', async ({ page }) => {
      const searchPage = new SearchPage(page);
      await searchPage.goto();

      await searchPage.searchInput.fill('produto');
      const searchPromise = searchPage.submitSearch();

      await expect(searchPage.loadingIndicator).toBeVisible();
      await searchPromise;
    });

    test('should show no results message', async ({ page }) => {
      const searchPage = new SearchPage(page);
      await searchPage.goto();

      await searchPage.search('xyznonexistentproduct123');

      await expect(searchPage.noResultsMessage).toBeVisible();
    });

    test('should clear search input', async ({ page }) => {
      const searchPage = new SearchPage(page);
      await searchPage.goto();

      await searchPage.search('teste');
      await searchPage.clearSearch();

      await expect(searchPage.searchInput).toHaveValue('');
    });

    test('should support keyboard navigation', async ({ page }) => {
      const searchPage = new SearchPage(page);
      await searchPage.goto();

      await searchPage.searchInput.fill('produto');
      await page.keyboard.press('Enter');

      await expect(searchPage.resultsContainer).toBeVisible();
    });

    test('should show search suggestions', async ({ page }) => {
      const searchPage = new SearchPage(page);
      await searchPage.goto();

      await searchPage.searchInput.fill('fone');
      
      // Wait for suggestions to appear
      await page.waitForTimeout(300);

      await expect(searchPage.suggestionsList).toBeVisible();
    });

    test('should save recent searches', async ({ page }) => {
      const searchPage = new SearchPage(page);
      await searchPage.goto();

      await searchPage.search('primeiro termo');
      await searchPage.clearSearch();
      
      await searchPage.searchInput.click();

      await expect(searchPage.recentSearches).toBeVisible();
      await expect(searchPage.recentSearches).toContainText('primeiro termo');
    });
  });

  // ============================================
  // FILTER TESTS
  // ============================================

  test.describe('Filters', () => {
    test('should display filter panel', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await expect(productsPage.filterPanel).toBeVisible();
    });

    test('should filter by category', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.selectCategory('electronics');

      await expect(page).toHaveURL(/category=electronics/);
      await expect(productsPage.productCards.first()).toBeVisible();
    });

    test('should filter by price range', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.setPriceRange(50, 200);

      await expect(page).toHaveURL(/min_price=50.*max_price=200/);
    });

    test('should filter by trending status', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.toggleTrendingFilter();

      await expect(page).toHaveURL(/trending=true/);
    });

    test('should combine multiple filters', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.selectCategory('electronics');
      await productsPage.setPriceRange(100, 300);
      await productsPage.toggleTrendingFilter();

      const url = page.url();
      expect(url).toMatch(/category=electronics/);
      expect(url).toMatch(/min_price=100/);
      expect(url).toMatch(/trending=true/);
    });

    test('should clear all filters', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.selectCategory('electronics');
      await productsPage.setPriceRange(50, 200);
      
      await productsPage.clearFilters();

      expect(page.url()).not.toMatch(/category=/);
      expect(page.url()).not.toMatch(/min_price=/);
    });

    test('should show active filter count', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.selectCategory('electronics');
      await productsPage.toggleTrendingFilter();

      await expect(productsPage.activeFilterCount).toHaveText('2');
    });
  });

  // ============================================
  // SORTING TESTS
  // ============================================

  test.describe('Sorting', () => {
    test('should sort by sales', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.sortBy('sales_30d');

      await expect(page).toHaveURL(/sort=sales_30d/);
    });

    test('should sort by price low to high', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.sortBy('price_asc');

      await expect(page).toHaveURL(/sort=price_asc/);
    });

    test('should sort by price high to low', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.sortBy('price_desc');

      await expect(page).toHaveURL(/sort=price_desc/);
    });

    test('should sort by newest', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.sortBy('newest');

      await expect(page).toHaveURL(/sort=newest/);
    });

    test('should persist sort option on navigation', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.sortBy('sales_30d');
      await page.goto('/favorites');
      await productsPage.goto();

      await expect(page).toHaveURL(/sort=sales_30d/);
    });
  });

  // ============================================
  // PAGINATION TESTS
  // ============================================

  test.describe('Pagination', () => {
    test('should display pagination controls', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await expect(productsPage.paginationContainer).toBeVisible();
    });

    test('should navigate to next page', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.nextPage();

      await expect(page).toHaveURL(/page=2/);
    });

    test('should navigate to previous page', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await page.goto('/products?page=2');

      await productsPage.previousPage();

      await expect(page).toHaveURL(/page=1/);
    });

    test('should navigate to specific page', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.goToPage(3);

      await expect(page).toHaveURL(/page=3/);
    });

    test('should show current page indicator', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await page.goto('/products?page=2');

      await expect(productsPage.currentPageIndicator).toHaveText('2');
    });

    test('should disable previous on first page', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await expect(productsPage.previousButton).toBeDisabled();
    });
  });

  // ============================================
  // PRODUCT CARD INTERACTION TESTS
  // ============================================

  test.describe('Product Card Interactions', () => {
    test('should open product details on click', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.productCards.first().click();

      await expect(productsPage.productDetailModal).toBeVisible();
    });

    test('should add product to favorites from card', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.favoriteFirstProduct();

      await expect(productsPage.favoriteButton.first()).toHaveClass(/active|filled|favorited/);
    });

    test('should show product image', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      const firstProductImage = productsPage.productCards.first().locator('img');
      await expect(firstProductImage).toBeVisible();
    });

    test('should display product price', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      const priceElement = productsPage.productCards.first().locator('[data-testid="price"]');
      await expect(priceElement).toBeVisible();
      await expect(priceElement).toHaveText(/R\$/);
    });

    test('should show trending badge for trending products', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await page.goto('/products?trending=true');

      const trendingBadge = productsPage.productCards.first().locator('[data-testid="trending-badge"]');
      await expect(trendingBadge).toBeVisible();
    });
  });
});
