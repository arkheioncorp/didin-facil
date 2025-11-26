/**
 * E2E Tests - Products Flow
 * Complete product browsing, filtering, and detail tests
 */

import { test, expect } from './fixtures';
import { ProductsPage } from './pages/ProductsPage';

test.describe('Products Flow', () => {
  test.use({ storageState: 'tests/e2e/.auth/user.json' });

  // ============================================
  // PRODUCTS PAGE LOADING
  // ============================================

  test.describe('Products Page Loading', () => {
    test('should display products page correctly', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await expect(page.locator('h1')).toContainText(/produtos|products/i);
    });

    test('should display product grid', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await expect(products.productCards.first()).toBeVisible();
    });

    test('should display filter sidebar', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await expect(page.locator('[data-testid="filter-sidebar"]')).toBeVisible();
    });

    test('should display sort options', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await expect(page.locator('[data-testid="sort-select"]')).toBeVisible();
    });

    test('should display pagination', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await expect(page.locator('[data-testid="pagination"]')).toBeVisible();
    });
  });

  // ============================================
  // PRODUCT CARDS
  // ============================================

  test.describe('Product Cards', () => {
    test('should display product image', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      const card = products.productCards.first();
      await expect(card.locator('img')).toBeVisible();
    });

    test('should display product title', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      const card = products.productCards.first();
      await expect(card.locator('[data-testid="product-title"]')).toBeVisible();
    });

    test('should display product price', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      const card = products.productCards.first();
      await expect(card.locator('[data-testid="product-price"]')).toBeVisible();
    });

    test('should display sales count', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      const card = products.productCards.first();
      await expect(card.locator('[data-testid="product-sales"]')).toBeVisible();
    });

    test('should display favorite button', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      const card = products.productCards.first();
      await expect(card.locator('[data-testid="favorite-button"]')).toBeVisible();
    });
  });

  // ============================================
  // FILTERING
  // ============================================

  test.describe('Filtering', () => {
    test('should filter by category', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="category-filter"]').click();
      await page.locator('[data-value="electronics"]').click();

      await expect(page).toHaveURL(/category=electronics/);
    });

    test('should filter by price range', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="min-price"]').fill('10');
      await page.locator('[data-testid="max-price"]').fill('100');
      await page.locator('[data-testid="apply-filters"]').click();

      await expect(page).toHaveURL(/min_price=10/);
    });

    test('should filter by sales count', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="min-sales"]').fill('1000');
      await page.locator('[data-testid="apply-filters"]').click();

      await expect(page).toHaveURL(/min_sales=1000/);
    });

    test('should clear all filters', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      // Apply filters
      await page.locator('[data-testid="min-price"]').fill('10');
      await page.locator('[data-testid="apply-filters"]').click();

      // Clear filters
      await page.locator('[data-testid="clear-filters"]').click();

      await expect(page).not.toHaveURL(/min_price/);
    });

    test('should show filtered results count', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await expect(page.locator('[data-testid="results-count"]')).toBeVisible();
    });
  });

  // ============================================
  // SORTING
  // ============================================

  test.describe('Sorting', () => {
    test('should sort by price low to high', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="sort-select"]').click();
      await page.locator('[data-value="price_asc"]').click();

      await expect(page).toHaveURL(/sort=price_asc/);
    });

    test('should sort by price high to low', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="sort-select"]').click();
      await page.locator('[data-value="price_desc"]').click();

      await expect(page).toHaveURL(/sort=price_desc/);
    });

    test('should sort by sales', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="sort-select"]').click();
      await page.locator('[data-value="sales"]').click();

      await expect(page).toHaveURL(/sort=sales/);
    });

    test('should sort by newest', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="sort-select"]').click();
      await page.locator('[data-value="newest"]').click();

      await expect(page).toHaveURL(/sort=newest/);
    });
  });

  // ============================================
  // PRODUCT DETAIL
  // ============================================

  test.describe('Product Detail', () => {
    test('should open product detail modal', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await products.productCards.first().click();

      await expect(products.productDetailModal).toBeVisible();
    });

    test('should display product images gallery', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await products.productCards.first().click();

      await expect(page.locator('[data-testid="product-gallery"]')).toBeVisible();
    });

    test('should display product description', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await products.productCards.first().click();

      await expect(page.locator('[data-testid="product-description"]')).toBeVisible();
    });

    test('should display supplier info', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await products.productCards.first().click();

      await expect(page.locator('[data-testid="supplier-info"]')).toBeVisible();
    });

    test('should copy product info button', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await products.productCards.first().click();
      await page.locator('[data-testid="copy-info"]').click();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/copiado|copied/i);
    });

    test('should generate copy button', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await products.productCards.first().click();
      await page.locator('[data-testid="generate-copy"]').click();

      await expect(page).toHaveURL(/copy/);
    });

    test('should close modal on escape', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await products.productCards.first().click();
      await expect(products.productDetailModal).toBeVisible();

      await page.keyboard.press('Escape');
      await expect(products.productDetailModal).not.toBeVisible();
    });

    test('should close modal on backdrop click', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await products.productCards.first().click();
      await expect(products.productDetailModal).toBeVisible();

      await page.locator('[data-testid="modal-backdrop"]').click({ position: { x: 0, y: 0 }});
      await expect(products.productDetailModal).not.toBeVisible();
    });
  });

  // ============================================
  // PAGINATION
  // ============================================

  test.describe('Pagination', () => {
    test('should navigate to next page', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="next-page"]').click();

      await expect(page).toHaveURL(/page=2/);
    });

    test('should navigate to previous page', async ({ mockedPage: page }) => {
      await page.goto('/products?page=2');

      await page.locator('[data-testid="prev-page"]').click();

      await expect(page).toHaveURL(/page=1/);
    });

    test('should navigate to specific page', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="page-3"]').click();

      await expect(page).toHaveURL(/page=3/);
    });

    test('should show current page indicator', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await expect(page.locator('[data-testid="current-page"]')).toHaveText('1');
    });
  });

  // ============================================
  // VIEW MODES
  // ============================================

  test.describe('View Modes', () => {
    test('should switch to list view', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="list-view"]').click();

      await expect(page.locator('[data-testid="products-list"]')).toBeVisible();
    });

    test('should switch to grid view', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="list-view"]').click();
      await page.locator('[data-testid="grid-view"]').click();

      await expect(page.locator('[data-testid="products-grid"]')).toBeVisible();
    });

    test('should persist view mode preference', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="list-view"]').click();
      await page.reload();

      await expect(page.locator('[data-testid="products-list"]')).toBeVisible();
    });
  });

  // ============================================
  // BULK ACTIONS
  // ============================================

  test.describe('Bulk Actions', () => {
    test('should select multiple products', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="product-checkbox"]').first().check();
      await page.locator('[data-testid="product-checkbox"]').nth(1).check();

      await expect(page.locator('[data-testid="selected-count"]')).toContainText('2');
    });

    test('should select all products', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="select-all"]').check();

      await expect(page.locator('[data-testid="product-checkbox"]:checked')).toHaveCount(
        await page.locator('[data-testid="product-checkbox"]').count()
      );
    });

    test('should add selected to favorites', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="product-checkbox"]').first().check();
      await page.locator('[data-testid="bulk-favorite"]').click();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/adicionado|added/i);
    });

    test('should export selected products', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      await page.locator('[data-testid="product-checkbox"]').first().check();
      await page.locator('[data-testid="bulk-export"]').click();

      await expect(page.locator('[data-testid="export-modal"]')).toBeVisible();
    });
  });

  // ============================================
  // INFINITE SCROLL
  // ============================================

  test.describe('Infinite Scroll', () => {
    test('should load more products on scroll', async ({ mockedPage: page }) => {
      const products = new ProductsPage(page);
      await products.goto();

      const initialCount = await products.productCards.count();

      // Scroll to bottom
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

      // Wait for more products
      await page.waitForTimeout(1000);

      const newCount = await products.productCards.count();
      expect(newCount).toBeGreaterThan(initialCount);
    });
  });
});
