/**
 * Authentication Setup Test
 * Creates authenticated state for other tests
 */
import { test as setup, expect } from "@playwright/test";
import path from "path";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const authFile = path.join(__dirname, ".auth/user.json");

setup("authenticate", async ({ page }) => {
  // Navigate to login page
  await page.goto("/login");

  // Wait for the page to load
  await expect(page).toHaveTitle(/TikTrend/i);

  // Fill in login form
  await page.fill('[data-testid="email-input"]', "test@example.com");
  await page.fill('[data-testid="password-input"]', "password123");

  // Submit the form
  await page.click('[data-testid="login-button"]');

  // Wait for navigation to dashboard
  await page.waitForURL("**/", { timeout: 10000 });

  // Verify we're logged in
  await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

  // Save storage state
  await page.context().storageState({ path: authFile });
});
