import { test, expect } from '@playwright/test';

test('landing page visual regression', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveScreenshot('landing-page.png');
});

test('products page visual regression', async ({ page }) => {
    await page.goto('/products');
    // Wait for products to load or empty state
    await page.waitForSelector('.grid, .text-center');
    await expect(page).toHaveScreenshot('products-page.png');
});
