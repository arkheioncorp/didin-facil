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
  await page.waitForLoadState('networkidle');

  // Check if we're already logged in (redirected to dashboard)
  const currentUrl = page.url();
  if (currentUrl.includes('/dashboard') || currentUrl.endsWith('/')) {
    // Already logged in, just verify
    const welcomeMessage = page.locator('[data-testid="welcome-message"]');
    if (await welcomeMessage.isVisible({ timeout: 5000 }).catch(() => false)) {
      await page.context().storageState({ path: authFile });
      return;
    }
  }

  // Check if we're on login page
  const emailInput = page.locator('[data-testid="email-input"], input[type="email"], input[name="email"]');
  const isLoginPage = await emailInput.first().isVisible({ timeout: 5000 }).catch(() => false);

  if (isLoginPage) {
    // Fill in login form
    await emailInput.first().fill("test@example.com");
    
    const passwordInput = page.locator('[data-testid="password-input"], input[type="password"], input[name="password"]');
    await passwordInput.first().fill("password123");

    // Submit the form
    const loginButton = page.locator('[data-testid="login-button"], button[type="submit"]:has-text("Entrar"), button[type="submit"]:has-text("Login")');
    await loginButton.first().click();

    // Wait for navigation
    await page.waitForURL('**/', { timeout: 15000 }).catch(() => {});
  }

  // Verify we're logged in - check for any dashboard content
  const dashboardContent = page.locator('[data-testid="welcome-message"], [data-testid="stats-card"], [data-testid="quick-actions"], .dashboard, main');
  await expect(dashboardContent.first()).toBeVisible({ timeout: 15000 });

  // Mark tutorial as completed to prevent it from blocking tests
  await page.evaluate(() => {
    localStorage.setItem('tutorial_completed', 'true');
    localStorage.setItem('onboarding_completed', 'true');
  });

  // Save storage state
  await page.context().storageState({ path: authFile });
});
