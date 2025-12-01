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

  // ============================================
  // PRODUCT ACTIONS PANEL
  // ============================================

  test.describe('Product Actions Panel', () => {
    test.describe('Copy AI Modal', () => {
      test('should open Copy AI modal from product detail', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        // Open product detail
        await products.productCards.first().click();
        await expect(products.productDetailModal).toBeVisible();

        // Click on Actions tab
        await page.locator('[data-testid="tab-actions"]').click();

        // Click Generate Copy button
        await page.locator('button:has-text("Gerar Copy com IA")').click();

        // Verify modal opened
        await expect(page.locator('[role="dialog"]:has-text("Gerar Copy com IA")')).toBeVisible();
      });

      test('should select copy type and tone', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Gerar Copy com IA")').click();

        // Select copy type
        await page.locator('[data-testid="copy-type-select"]').click();
        await page.locator('[data-value="ad"]').click();

        // Select tone
        await page.locator('[data-testid="copy-tone-select"]').click();
        await page.locator('[data-value="professional"]').click();

        await expect(page.locator('[data-testid="copy-type-select"]')).toContainText('Anúncio');
        await expect(page.locator('[data-testid="copy-tone-select"]')).toContainText('Profissional');
      });

      test('should navigate to full copy page', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Gerar Copy com IA")').click();

        // Click "Abrir Página" button
        await page.locator('button:has-text("Abrir Página")').click();

        await expect(page).toHaveURL(/\/copy/);
      });

      test('should close Copy modal on cancel', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Gerar Copy com IA")').click();

        // Click cancel
        await page.locator('button:has-text("Cancelar")').click();

        await expect(page.locator('[role="dialog"]:has-text("Gerar Copy com IA")')).not.toBeVisible();
      });
    });

    test.describe('WhatsApp Modal', () => {
      test('should open WhatsApp modal from product detail', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Enviar via WhatsApp")').click();

        await expect(page.locator('[role="dialog"]:has-text("Enviar via WhatsApp")')).toBeVisible();
      });

      test('should have pre-filled message with product info', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Enviar via WhatsApp")').click();

        const messageField = page.locator('textarea');
        await expect(messageField).not.toBeEmpty();
        await expect(messageField).toContainText(/🛍️/);
      });

      test('should allow editing phone number', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Enviar via WhatsApp")').click();

        const phoneInput = page.locator('input[type="tel"]');
        await phoneInput.fill('+5511999999999');
        
        await expect(phoneInput).toHaveValue('+5511999999999');
      });

      test('should navigate to WhatsApp page', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Enviar via WhatsApp")').click();

        await page.locator('button:has-text("Abrir Página")').click();

        await expect(page).toHaveURL(/\/whatsapp/);
      });
    });

    test.describe('Schedule Modal', () => {
      test('should open Schedule modal from product detail', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Agendar Publicação")').click();

        await expect(page.locator('[role="dialog"]:has-text("Agendar Publicação")')).toBeVisible();
      });

      test('should select platform for scheduling', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Agendar Publicação")').click();

        // Select TikTok platform
        await page.locator('[data-testid="platform-select"]').click();
        await page.locator('[data-value="tiktok"]').click();

        await expect(page.locator('[data-testid="platform-select"]')).toContainText('TikTok');
      });

      test('should set schedule date and time', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Agendar Publicação")').click();

        // Set future date
        const futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + 1);
        const dateString = futureDate.toISOString().slice(0, 16);
        
        await page.locator('input[type="datetime-local"]').fill(dateString);
        
        await expect(page.locator('input[type="datetime-local"]')).toHaveValue(dateString);
      });

      test('should show post preview', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Agendar Publicação")').click();

        await expect(page.locator('text=Preview do Post')).toBeVisible();
        await expect(page.locator('text=🛍️')).toBeVisible();
      });

      test('should navigate to advanced scheduler', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Agendar Publicação")').click();

        await page.locator('button:has-text("Configurar Avançado")').click();

        await expect(page).toHaveURL(/\/automation\/scheduler/);
      });
    });

    test.describe('Quick Actions', () => {
      test('should copy product info', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Copiar Informações")').click();

        await expect(page.locator('[data-testid="toast"]')).toContainText(/copiado|copied/i);
      });

      test('should navigate to seller bot', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Seller Bot")').click();

        await expect(page).toHaveURL(/\/seller-bot/);
      });

      test('should add to CRM', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Adicionar ao CRM")').click();

        // Should show success toast or navigate to CRM
        await expect(page.locator('[data-testid="toast"]').or(page)).toBeVisible();
      });

      test('should navigate to Instagram post', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Publicar no Instagram")').click();

        await expect(page).toHaveURL(/\/social\/instagram/);
      });

      test('should navigate to TikTok post', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Publicar no TikTok")').click();

        await expect(page).toHaveURL(/\/social\/tiktok/);
      });

      test('should navigate to YouTube post', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();
        await page.locator('button:has-text("Publicar no YouTube")').click();

        await expect(page).toHaveURL(/\/social\/youtube/);
      });
    });

    test.describe('Product Detail Modal Tabs', () => {
      test('should display Info tab by default', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();

        await expect(page.locator('[data-testid="tab-info"]')).toHaveAttribute('data-state', 'active');
      });

      test('should switch to Stats tab', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-stats"]').click();

        await expect(page.locator('[data-testid="tab-stats"]')).toHaveAttribute('data-state', 'active');
        await expect(page.locator('[data-testid="stats-content"]')).toBeVisible();
      });

      test('should switch to Actions tab', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();

        await expect(page.locator('[data-testid="tab-actions"]')).toHaveAttribute('data-state', 'active');
        await expect(page.locator('[data-testid="actions-panel"]')).toBeVisible();
      });

      test('should display quick stats in Actions tab', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        await products.productCards.first().click();
        await page.locator('[data-testid="tab-actions"]').click();

        await expect(page.locator('text=Vendas Totais')).toBeVisible();
        await expect(page.locator('text=Avaliação')).toBeVisible();
      });
    });

    test.describe('Compact Actions Bar', () => {
      test('should show quick actions on card hover', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        const card = products.productCards.first();
        await card.hover();

        await expect(card.locator('[data-testid="quick-actions"]')).toBeVisible();
      });

      test('should trigger Copy AI from quick actions', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        const card = products.productCards.first();
        await card.hover();
        await card.locator('button:has-text("Gerar Copy")').click();

        await expect(page.locator('[role="dialog"]:has-text("Gerar Copy com IA")')).toBeVisible();
      });

      test('should trigger Schedule from quick actions', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        const card = products.productCards.first();
        await card.hover();
        await card.locator('[data-testid="quick-schedule"]').click();

        await expect(page.locator('[role="dialog"]:has-text("Agendar Publicação")')).toBeVisible();
      });

      test('should trigger WhatsApp from quick actions', async ({ mockedPage: page }) => {
        const products = new ProductsPage(page);
        await products.goto();

        const card = products.productCards.first();
        await card.hover();
        await card.locator('[data-testid="quick-whatsapp"]').click();

        await expect(page.locator('[role="dialog"]:has-text("Enviar via WhatsApp")')).toBeVisible();
      });
    });
  });
});
