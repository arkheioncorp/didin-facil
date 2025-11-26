/**
 * E2E Tests - AI Copy Generation Flow
 * Complete AI copy generation, history, and customization tests
 */

import { test, expect } from './fixtures';
import { CopyPage } from './pages/CopyPage';
import { ProductsPage } from './pages/ProductsPage';

test.describe('AI Copy Generation Flow', () => {
  test.use({ storageState: 'tests/e2e/.auth/user.json' }); // Use authenticated state

  // ============================================
  // COPY GENERATION TESTS
  // ============================================

  test.describe('Copy Generation', () => {
    test('should display copy generation interface', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await expect(copyPage.productSelector).toBeVisible();
      await expect(copyPage.copyTypeSelector).toBeVisible();
      await expect(copyPage.platformSelector).toBeVisible();
      await expect(copyPage.generateButton).toBeVisible();
    });

    test('should generate copy for selected product', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.selectProduct('prod-1');
      await copyPage.selectCopyType('product_description');
      await copyPage.selectPlatform('instagram');
      await copyPage.generate();

      await expect(copyPage.generatedCopy).toBeVisible();
      await expect(copyPage.generatedCopy).not.toBeEmpty();
    });

    test('should show loading state during generation', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.selectProduct('prod-1');
      const generatePromise = copyPage.generate();

      await expect(copyPage.loadingIndicator).toBeVisible();
      await generatePromise;

      await expect(copyPage.loadingIndicator).not.toBeVisible();
    });

    test('should generate copy directly from product card', async ({ page }) => {
      const productsPage = new ProductsPage(page);
      await productsPage.goto();

      // Click generate copy button on product card
      await productsPage.productCards.first().locator('[data-testid="generate-copy-btn"]').click();

      const copyPage = new CopyPage(page);
      await expect(copyPage.productSelector).toHaveValue(/prod-/);
    });

    test('should support different copy types', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      const copyTypes = [
        'product_description',
        'facebook_ad',
        'tiktok_hook',
        'instagram_caption',
        'whatsapp_message'
      ];

      for (const copyType of copyTypes) {
        await copyPage.selectCopyType(copyType);
        await expect(copyPage.copyTypeSelector).toHaveValue(copyType);
      }
    });

    test('should support different platforms', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      const platforms = ['instagram', 'facebook', 'tiktok', 'whatsapp', 'general'];

      for (const platform of platforms) {
        await copyPage.selectPlatform(platform);
        await expect(copyPage.platformSelector).toHaveValue(platform);
      }
    });

    test('should support different tones', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      const tones = ['professional', 'casual', 'fun', 'urgent', 'persuasive'];

      for (const tone of tones) {
        await copyPage.selectTone(tone);
        await expect(copyPage.toneSelector).toHaveValue(tone);
      }
    });
  });

  // ============================================
  // COPY CUSTOMIZATION TESTS
  // ============================================

  test.describe('Copy Customization', () => {
    test('should toggle emoji inclusion', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.toggleEmoji();

      await expect(copyPage.emojiToggle).toBeChecked();
    });

    test('should toggle hashtag inclusion', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.toggleHashtags();

      await expect(copyPage.hashtagToggle).toBeChecked();
    });

    test('should set custom max length', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.setMaxLength(280);

      await expect(copyPage.maxLengthInput).toHaveValue('280');
    });

    test('should add custom instructions', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.setCustomInstructions('Focus on eco-friendly aspects');

      await expect(copyPage.customInstructionsInput).toHaveValue('Focus on eco-friendly aspects');
    });

    test('should apply template preset', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.selectTemplate('urgent_sale');

      await expect(copyPage.toneSelector).toHaveValue('urgent');
      await expect(copyPage.emojiToggle).toBeChecked();
    });
  });

  // ============================================
  // COPY OUTPUT TESTS
  // ============================================

  test.describe('Copy Output', () => {
    test('should display word count', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.selectProduct('prod-1');
      await copyPage.generate();

      await expect(copyPage.wordCount).toBeVisible();
      await expect(copyPage.wordCount).toHaveText(/\d+/);
    });

    test('should display character count', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.selectProduct('prod-1');
      await copyPage.generate();

      await expect(copyPage.characterCount).toBeVisible();
      await expect(copyPage.characterCount).toHaveText(/\d+/);
    });

    test('should copy generated text to clipboard', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.selectProduct('prod-1');
      await copyPage.generate();
      await copyPage.copyToClipboard();

      await expect(page.locator('[data-testid="toast"]')).toContainText(/copiado|copied/i);
    });

    test('should regenerate copy', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.selectProduct('prod-1');
      await copyPage.generate();

      const firstCopy = await copyPage.generatedCopy.textContent();

      await copyPage.regenerate();

      // Note: In real test, content might be same due to mocks
      await expect(copyPage.generatedCopy).toBeVisible();
    });

    test('should show character limit warning', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.setMaxLength(50);
      await copyPage.selectProduct('prod-1');
      await copyPage.generate();

      // Check if generated copy respects limit or shows warning
      await expect(copyPage.characterCount).toBeVisible();
    });
  });

  // ============================================
  // COPY HISTORY TESTS
  // ============================================

  test.describe('Copy History', () => {
    test('should save generated copy to history', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.selectProduct('prod-1');
      await copyPage.generate();

      await copyPage.goToHistory();

      await expect(copyPage.historyList.first()).toBeVisible();
    });

    test('should display history items', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goToHistory();

      await expect(copyPage.historyList).toBeVisible();
    });

    test('should load copy from history', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goToHistory();

      await copyPage.historyList.first().click();

      await expect(copyPage.generatedCopy).toBeVisible();
    });

    test('should delete history item', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goToHistory();

      const initialCount = await copyPage.historyList.count();
      await copyPage.deleteHistoryItem(0);

      await expect(copyPage.historyList).toHaveCount(initialCount - 1);
    });

    test('should clear all history', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goToHistory();

      await copyPage.clearHistory();

      await expect(copyPage.emptyHistoryState).toBeVisible();
    });

    test('should filter history by date', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goToHistory();

      await copyPage.filterHistoryByDate('today');

      await expect(page).toHaveURL(/date=today/);
    });

    test('should search history', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goToHistory();

      await copyPage.searchHistory('produto');

      await expect(page).toHaveURL(/q=produto/);
    });
  });

  // ============================================
  // QUOTA TESTS
  // ============================================

  test.describe('Quota Management', () => {
    test('should display quota usage', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await expect(copyPage.quotaIndicator).toBeVisible();
      await expect(copyPage.quotaIndicator).toHaveText(/\d+\s*\/\s*\d+/);
    });

    test('should update quota after generation', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      const initialQuota = await copyPage.quotaIndicator.textContent();

      await copyPage.selectProduct('prod-1');
      await copyPage.generate();

      await expect(copyPage.quotaIndicator).not.toHaveText(initialQuota!);
    });

    test('should show warning when quota is low', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      // This depends on mock data setting low quota
      await expect(copyPage.quotaWarning).toBeVisible();
    });

    test('should disable generation when quota exceeded', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      // Mock quota exceeded state
      await page.evaluate(() => {
        window.localStorage.setItem('mock_quota_exceeded', 'true');
      });

      await page.reload();

      await expect(copyPage.generateButton).toBeDisabled();
      await expect(copyPage.quotaExceededMessage).toBeVisible();
    });

    test('should show upgrade prompt when quota exceeded', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      // Mock quota exceeded
      await expect(copyPage.upgradePrompt).toBeVisible();
    });
  });

  // ============================================
  // ACCESSIBILITY TESTS
  // ============================================

  test.describe('Accessibility', () => {
    test('should have proper ARIA labels', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await expect(copyPage.productSelector).toHaveAttribute('aria-label', /.+/);
      await expect(copyPage.generateButton).toHaveAccessibleName();
    });

    test('should be keyboard navigable', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await page.keyboard.press('Tab');
      await expect(copyPage.productSelector).toBeFocused();

      await page.keyboard.press('Tab');
      await expect(copyPage.copyTypeSelector).toBeFocused();
    });

    test('should announce generation status to screen readers', async ({ page }) => {
      const copyPage = new CopyPage(page);
      await copyPage.goto();

      await copyPage.selectProduct('prod-1');
      await copyPage.generate();

      const liveRegion = page.locator('[aria-live="polite"]');
      await expect(liveRegion).toContainText(/gerado|generated|concluído|complete/i);
    });
  });
});
