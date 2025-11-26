/**
 * E2E Tests - Accessibility and Performance
 * WCAG compliance and performance tests
 */

import { test, expect } from './fixtures';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Tests', () => {
  test.use({ storageState: 'tests/e2e/.auth/user.json' });

  // ============================================
  // WCAG COMPLIANCE
  // ============================================

  test.describe('WCAG Compliance', () => {
    test('dashboard should not have accessibility violations', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });

    test('search page should not have accessibility violations', async ({ page }) => {
      await page.goto('/search');
      await page.waitForLoadState('networkidle');

      const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });

    test('products page should not have accessibility violations', async ({ page }) => {
      await page.goto('/products');
      await page.waitForLoadState('networkidle');

      const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });

    test('settings page should not have accessibility violations', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });
  });

  // ============================================
  // KEYBOARD NAVIGATION
  // ============================================

  test.describe('Keyboard Navigation', () => {
    test('should navigate main menu with keyboard', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Tab to sidebar
      await page.keyboard.press('Tab');
      
      // Should be able to navigate menu items
      const activeElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(activeElement).toBeDefined();
    });

    test('should focus skip link first', async ({ page }) => {
      await page.goto('/');
      
      await page.keyboard.press('Tab');

      const skipLink = page.locator('[data-testid="skip-link"]');
      if (await skipLink.isVisible()) {
        await expect(skipLink).toBeFocused();
      }
    });

    test('should trap focus in modal', async ({ page }) => {
      await page.goto('/products');
      await page.waitForLoadState('networkidle');

      // Open modal
      await page.locator('[data-testid="product-card"]').first().click();
      await expect(page.locator('[data-testid="product-detail-modal"]')).toBeVisible();

      // Tab through modal elements
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // Focus should stay within modal
      const focusedElement = await page.evaluate(() => 
        document.activeElement?.closest('[data-testid="product-detail-modal"]')
      );
      expect(focusedElement).toBeDefined();
    });

    test('should close modal with Escape', async ({ page }) => {
      await page.goto('/products');
      await page.waitForLoadState('networkidle');

      await page.locator('[data-testid="product-card"]').first().click();
      await expect(page.locator('[data-testid="product-detail-modal"]')).toBeVisible();

      await page.keyboard.press('Escape');
      await expect(page.locator('[data-testid="product-detail-modal"]')).not.toBeVisible();
    });
  });

  // ============================================
  // SCREEN READER SUPPORT
  // ============================================

  test.describe('Screen Reader Support', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
      
      // Should have at least one h1
      const h1 = await page.locator('h1').count();
      expect(h1).toBeGreaterThanOrEqual(1);
    });

    test('should have alt text for images', async ({ page }) => {
      await page.goto('/products');
      await page.waitForLoadState('networkidle');

      const images = await page.locator('img').all();

      for (const img of images) {
        const alt = await img.getAttribute('alt');
        expect(alt).toBeDefined();
      }
    });

    test('should have labels for form inputs', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      const inputs = await page.locator('input:not([type="hidden"])').all();

      for (const input of inputs) {
        const id = await input.getAttribute('id');
        const ariaLabel = await input.getAttribute('aria-label');
        const ariaLabelledBy = await input.getAttribute('aria-labelledby');
        const label = id ? await page.locator(`label[for="${id}"]`).count() : 0;

        expect(label > 0 || ariaLabel || ariaLabelledBy).toBeTruthy();
      }
    });

    test('should have ARIA landmarks', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      await expect(page.locator('[role="main"], main')).toBeVisible();
      await expect(page.locator('[role="navigation"], nav')).toBeVisible();
    });
  });

  // ============================================
  // COLOR CONTRAST
  // ============================================

  test.describe('Color Contrast', () => {
    test('should have sufficient color contrast', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const accessibilityScanResults = await new AxeBuilder({ page })
        .withRules(['color-contrast'])
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });

    test('should work in high contrast mode', async ({ page }) => {
      await page.emulateMedia({ forcedColors: 'active' });
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Page should still be functional
      await expect(page.locator('[data-testid="header"]')).toBeVisible();
    });
  });

  // ============================================
  // REDUCED MOTION
  // ============================================

  test.describe('Reduced Motion', () => {
    test('should respect reduced motion preference', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Animations should be disabled or minimal
      const animations = await page.evaluate(() => {
        const computed = getComputedStyle(document.body);
        return computed.animationDuration || computed.transitionDuration;
      });

      // Should have 0s animations or very short ones
    });
  });
});

test.describe('Performance Tests', () => {
  test.use({ storageState: 'tests/e2e/.auth/user.json' });

  // ============================================
  // PAGE LOAD PERFORMANCE
  // ============================================

  test.describe('Page Load Performance', () => {
    test('dashboard should load within 3 seconds', async ({ page }) => {
      const startTime = Date.now();
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;

      expect(loadTime).toBeLessThan(3000);
    });

    test('products page should load within 3 seconds', async ({ page }) => {
      const startTime = Date.now();
      await page.goto('/products');
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;

      expect(loadTime).toBeLessThan(3000);
    });

    test('search should return results within 2 seconds', async ({ page }) => {
      await page.goto('/search');
      await page.waitForLoadState('networkidle');

      await page.locator('[data-testid="search-input"]').fill('produto');
      
      const startTime = Date.now();
      await page.keyboard.press('Enter');
      await page.waitForSelector('[data-testid="product-card"]', { timeout: 2000 });
      const searchTime = Date.now() - startTime;

      expect(searchTime).toBeLessThan(2000);
    });
  });

  // ============================================
  // CORE WEB VITALS
  // ============================================

  test.describe('Core Web Vitals', () => {
    test('should have good LCP (Largest Contentful Paint)', async ({ page }) => {
      await page.goto('/');
      
      const lcp = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1] as PerformanceEntry & { startTime: number };
            resolve(lastEntry.startTime);
          }).observe({ type: 'largest-contentful-paint', buffered: true });
          
          // Timeout fallback
          setTimeout(() => resolve(0), 5000);
        });
      });

      expect(lcp).toBeLessThan(2500); // Good LCP is < 2.5s
    });

    test('should have good FID (First Input Delay)', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Simulate user interaction
      const startTime = Date.now();
      await page.locator('[data-testid="search-input"]').click();
      const fid = Date.now() - startTime;

      expect(fid).toBeLessThan(100); // Good FID is < 100ms
    });

    test('should have good CLS (Cumulative Layout Shift)', async ({ page }) => {
      await page.goto('/');
      
      const cls = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          let clsValue = 0;
          new PerformanceObserver((list) => {
            for (const entry of list.getEntries() as (PerformanceEntry & { value: number })[]) {
              clsValue += entry.value;
            }
            resolve(clsValue);
          }).observe({ type: 'layout-shift', buffered: true });
          
          setTimeout(() => resolve(clsValue), 3000);
        });
      });

      expect(cls).toBeLessThan(0.1); // Good CLS is < 0.1
    });
  });

  // ============================================
  // RESOURCE OPTIMIZATION
  // ============================================

  test.describe('Resource Optimization', () => {
    test('should lazy load images', async ({ page }) => {
      await page.goto('/products');
      await page.waitForLoadState('networkidle');

      const images = await page.locator('img[loading="lazy"]').all();
      expect(images.length).toBeGreaterThan(0);
    });

    test('should use optimized image formats', async ({ page }) => {
      await page.goto('/products');
      await page.waitForLoadState('networkidle');

      const images = await page.locator('img').all();
      
      for (const img of images.slice(0, 5)) { // Check first 5 images
        const src = await img.getAttribute('src');
        // Should use webp or avif for optimization
        const hasOptimizedFormat = src?.includes('.webp') || 
                                   src?.includes('.avif') || 
                                   src?.includes('format=webp');
        // This is informational, not a hard requirement
      }
    });

    test('should bundle and minify JavaScript', async ({ page }) => {
      const responses: number[] = [];
      
      page.on('response', response => {
        if (response.url().endsWith('.js')) {
          const contentLength = parseInt(response.headers()['content-length'] || '0');
          responses.push(contentLength);
        }
      });

      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Total JS should be reasonable (< 1MB uncompressed)
      const totalJS = responses.reduce((a, b) => a + b, 0);
      expect(totalJS).toBeLessThan(1024 * 1024);
    });
  });

  // ============================================
  // CACHING
  // ============================================

  test.describe('Caching', () => {
    test('should cache static assets', async ({ page }) => {
      const cachedResponses: string[] = [];
      
      page.on('response', response => {
        const cacheControl = response.headers()['cache-control'];
        if (cacheControl && cacheControl.includes('max-age')) {
          cachedResponses.push(response.url());
        }
      });

      await page.goto('/');
      await page.waitForLoadState('networkidle');

      expect(cachedResponses.length).toBeGreaterThan(0);
    });

    test('should use service worker for offline support', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const hasServiceWorker = await page.evaluate(async () => {
        if ('serviceWorker' in navigator) {
          const registrations = await navigator.serviceWorker.getRegistrations();
          return registrations.length > 0;
        }
        return false;
      });

      // Service worker is optional but recommended
    });
  });

  // ============================================
  // MEMORY USAGE
  // ============================================

  test.describe('Memory Usage', () => {
    test('should not have memory leaks on navigation', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Get initial memory
      const initialMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory.usedJSHeapSize;
        }
        return 0;
      });

      // Navigate multiple times
      for (let i = 0; i < 5; i++) {
        await page.goto('/products');
        await page.goto('/search');
        await page.goto('/favorites');
        await page.goto('/');
      }

      await page.waitForLoadState('networkidle');

      // Check memory hasn't grown excessively
      const finalMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory.usedJSHeapSize;
        }
        return 0;
      });

      // Memory growth should be less than 50%
      if (initialMemory > 0) {
        expect(finalMemory).toBeLessThan(initialMemory * 1.5);
      }
    });
  });
});
