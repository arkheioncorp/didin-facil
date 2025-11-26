/**
 * E2E Tests - Favorites Management Flow
 * Complete favorites management, sync, and export tests
 */

import { test, expect } from './fixtures';
import { FavoritesPage } from './pages/FavoritesPage';
import { ProductsPage } from './pages/ProductsPage';

test.describe('Favorites Management Flow', () => {
  test.use({ storageState: '.auth/user.json' }); // Use authenticated state

  // ============================================
  // ADDING FAVORITES TESTS
  // ============================================

  test.describe('Adding Favorites', () => {
    test('should add product to favorites from products page', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.favoriteFirstProduct();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/adicionado|added/i);
    });

    test('should add product to favorites from product detail', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      // Open product detail
      await productsPage.productCards.first().click();
      await expect(productsPage.productDetailModal).toBeVisible();

      // Add to favorites
      await page.getByRole('button', { name: /favoritar|favorite/i }).click();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/adicionado|added/i);
    });

    test('should update favorite button state after adding', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      const favoriteButton = productsPage.favoriteButton.first();
      
      // Initially not favorited
      await expect(favoriteButton).not.toHaveClass(/active|favorited/);

      await favoriteButton.click();

      // Now should be favorited
      await expect(favoriteButton).toHaveClass(/active|favorited/);
    });

    test('should persist favorites after page refresh', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await productsPage.favoriteFirstProduct();
      
      // Refresh page
      await page.reload();

      const favoriteButton = productsPage.favoriteButton.first();
      await expect(favoriteButton).toHaveClass(/active|favorited/);
    });
  });

  // ============================================
  // VIEWING FAVORITES TESTS
  // ============================================

  test.describe('Viewing Favorites', () => {
    test('should display favorites page correctly', async ({ page }) => {
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await expect(favoritesPage.pageTitle).toBeVisible();
      await expect(favoritesPage.pageTitle).toContainText(/favoritos|favorites/i);
    });

    test('should show empty state when no favorites', async ({ page }) => {
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      // Clear all favorites first (if any)
      await favoritesPage.clearAllFavorites();

      await expect(favoritesPage.emptyState).toBeVisible();
      await expect(favoritesPage.emptyState).toContainText(/nenhum|no favorites/i);
    });

    test('should display favorited products', async ({ page }) => {
      // First add a favorite
      const productsPage = new ProductsPage(page);
      await productsPage.goto();
      await productsPage.favoriteFirstProduct();

      // Then check favorites page
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await expect(favoritesPage.productCards.first()).toBeVisible();
    });

    test('should show favorite count in header', async ({ page }) => {
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await expect(favoritesPage.favoriteCount).toBeVisible();
    });

    test('should sort favorites by date added', async ({ page }) => {
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await favoritesPage.sortBy('date_added');

      await expect(page).toHaveURL(/sort=date_added/);
    });

    test('should filter favorites by category', async ({ page }) => {
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await favoritesPage.filterByCategory('electronics');

      await expect(page).toHaveURL(/category=electronics/);
    });
  });

  // ============================================
  // REMOVING FAVORITES TESTS
  // ============================================

  test.describe('Removing Favorites', () => {
    test('should remove product from favorites', async ({ page }) => {
      // First add a favorite
      const productsPage = new ProductsPage(page);
      await productsPage.goto();
      await productsPage.favoriteFirstProduct();

      // Go to favorites and remove
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      const initialCount = await favoritesPage.productCards.count();
      await favoritesPage.removeFirstFavorite();

      await expect(favoritesPage.productCards).toHaveCount(initialCount - 1);
    });

    test('should show confirmation dialog before removing', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();
      await productsPage.favoriteFirstProduct();

      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await favoritesPage.removeButton.first().click();

      await expect(favoritesPage.confirmDialog).toBeVisible();
    });

    test('should allow canceling removal', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();
      await productsPage.favoriteFirstProduct();

      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      const initialCount = await favoritesPage.productCards.count();

      await favoritesPage.removeButton.first().click();
      await favoritesPage.cancelButton.click();

      await expect(favoritesPage.productCards).toHaveCount(initialCount);
    });

    test('should clear all favorites', async ({ page }) => {
      // Add multiple favorites
      const productsPage = new ProductsPage(page);
      await productsPage.goto();
      await productsPage.favoriteButton.nth(0).click();
      await productsPage.favoriteButton.nth(1).click();

      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await favoritesPage.clearAllFavorites();

      await expect(favoritesPage.emptyState).toBeVisible();
    });
  });

  // ============================================
  // EXPORT FAVORITES TESTS
  // ============================================

  test.describe('Export Favorites', () => {
    test('should export favorites as CSV', async ({ page }) => {
      // Add a favorite first
      const productsPage = new ProductsPage(page);
      await productsPage.goto();
      await productsPage.favoriteFirstProduct();

      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      const downloadPromise = page.waitForEvent('download');
      await favoritesPage.exportButton.click();
      await favoritesPage.exportCSV.click();

      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.csv$/);
    });

    test('should export favorites as Excel', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();
      await productsPage.favoriteFirstProduct();

      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      const downloadPromise = page.waitForEvent('download');
      await favoritesPage.exportButton.click();
      await favoritesPage.exportExcel.click();

      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
    });

    test('should show export options menu', async ({ page }) => {
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await favoritesPage.exportButton.click();

      await expect(favoritesPage.exportMenu).toBeVisible();
      await expect(favoritesPage.exportCSV).toBeVisible();
      await expect(favoritesPage.exportExcel).toBeVisible();
    });

    test('should show error when exporting empty favorites', async ({ page }) => {
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      // Clear all favorites
      await favoritesPage.clearAllFavorites();

      await favoritesPage.exportButton.click();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/vazio|empty/i);
    });
  });

  // ============================================
  // SYNC TESTS
  // ============================================

  test.describe('Favorites Sync', () => {
    test('should sync favorites on page load', async ({ page }) => {
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      // Should show sync indicator
      await expect(favoritesPage.syncIndicator).toBeVisible();
    });

    test('should show offline indicator when disconnected', async ({ page, context }) => {
      await context.setOffline(true);

      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await expect(favoritesPage.offlineIndicator).toBeVisible();
    });

    test('should queue changes when offline', async ({ page, context }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      await context.setOffline(true);

      await productsPage.favoriteFirstProduct();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/offline|pendente/i);
    });
  });

  // ============================================
  // BULK OPERATIONS TESTS
  // ============================================

  test.describe('Bulk Operations', () => {
    test('should enable bulk selection mode', async ({ page }) => {
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await favoritesPage.enableBulkMode();

      await expect(favoritesPage.bulkCheckboxes.first()).toBeVisible();
    });

    test('should select multiple favorites', async ({ page }) => {
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await favoritesPage.enableBulkMode();
      await favoritesPage.bulkCheckboxes.nth(0).click();
      await favoritesPage.bulkCheckboxes.nth(1).click();

      await expect(favoritesPage.selectedCount).toHaveText('2');
    });

    test('should select all favorites', async ({ page }) => {
      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await favoritesPage.enableBulkMode();
      await favoritesPage.selectAllCheckbox.click();

      const totalCount = await favoritesPage.productCards.count();
      await expect(favoritesPage.selectedCount).toHaveText(String(totalCount));
    });

    test('should remove selected favorites', async ({ page }) => {
      // Add multiple favorites first
      const productsPage = new ProductsPage(page);
      await productsPage.goto();
      await productsPage.favoriteButton.nth(0).click();
      await productsPage.favoriteButton.nth(1).click();
      await productsPage.favoriteButton.nth(2).click();

      const favoritesPage = new FavoritesPage(page);
      await favoritesPage.goto();

      await favoritesPage.enableBulkMode();
      await favoritesPage.bulkCheckboxes.nth(0).click();
      await favoritesPage.bulkCheckboxes.nth(1).click();

      await favoritesPage.bulkDeleteButton.click();
      await favoritesPage.confirmButton.click();

      await expect(favoritesPage.productCards).toHaveCount(1);
    });
  });
});
