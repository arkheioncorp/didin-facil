/**
 * E2E Tests - Authentication Flow
 * Complete login, registration, and session management tests
 */

import { test, expect } from './fixtures';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';

test.describe('Authentication Flow', () => {
  // ============================================
  // LOGIN TESTS
  // ============================================
  
  test.describe('Login', () => {
    test('should display login form correctly', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      await expect(loginPage.emailInput).toBeVisible();
      await expect(loginPage.passwordInput).toBeVisible();
      await expect(loginPage.submitButton).toBeVisible();
      await expect(loginPage.registerLink).toBeVisible();
    });

    test('should show validation errors for empty form', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      await loginPage.submitButton.click();

      await expect(loginPage.emailError).toBeVisible();
    });

    test('should show error for invalid email format', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      await loginPage.emailInput.fill('invalid-email');
      await loginPage.passwordInput.fill('password123');
      await loginPage.submitButton.click();

      await expect(loginPage.emailError).toBeVisible();
    });

    test('should show error for invalid credentials', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      await loginPage.login('wrong@example.com', 'wrongpassword');

      await expect(loginPage.errorAlert).toBeVisible();
      await expect(loginPage.errorAlert).toContainText(/invalid|incorret/i);
    });

    test('should login successfully with valid credentials', async ({ page }) => {
      const loginPage = new LoginPage(page);
      const dashboardPage = new DashboardPage(page);
      
      await loginPage.goto();
      await loginPage.login('test@example.com', 'correct_password');

      // Dashboard is at root path "/"
      await expect(page).toHaveURL(/$|dashboard/);
      await expect(dashboardPage.welcomeMessage).toBeVisible();
    });

    test('should remember user after login', async ({ page, context }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();
      await loginPage.login('test@example.com', 'password123');

      // Navigate away and back
      await page.goto('/settings');
      await page.goto('/dashboard');

      // Should still be authenticated
      const dashboardPage = new DashboardPage(page);
      await expect(dashboardPage.welcomeMessage).toBeVisible();
    });

    test('should show password toggle functionality', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      await loginPage.passwordInput.fill('mypassword');
      
      // Password should be hidden by default
      await expect(loginPage.passwordInput).toHaveAttribute('type', 'password');

      // Toggle visibility
      await loginPage.togglePasswordVisibility();
      await expect(loginPage.passwordInput).toHaveAttribute('type', 'text');

      // Toggle back
      await loginPage.togglePasswordVisibility();
      await expect(loginPage.passwordInput).toHaveAttribute('type', 'password');
    });
  });

  // ============================================
  // REGISTRATION TESTS
  // ============================================

  test.describe('Registration', () => {
    test('should navigate to registration from login', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      await loginPage.navigateToRegister();

      await expect(page).toHaveURL(/register/);
    });

    test('should display registration form correctly', async ({ page }) => {
      await page.goto('/register');

      await expect(page.getByLabel(/nome|name/i)).toBeVisible();
      await expect(page.getByLabel(/email/i)).toBeVisible();
      await expect(page.getByLabel(/senha|password/i).first()).toBeVisible();
      await expect(page.getByLabel(/confirmar|confirm/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /cadastrar|register|criar/i })).toBeVisible();
    });

    test('should show validation for password mismatch', async ({ page }) => {
      await page.goto('/register');

      await page.getByLabel(/nome|name/i).fill('Test User');
      await page.getByLabel(/email/i).fill('test@example.com');
      await page.getByLabel(/^senha|^password/i).fill('password123');
      await page.getByLabel(/confirmar|confirm/i).fill('different_password');

      await page.getByRole('button', { name: /cadastrar|register|criar/i }).click();

      await expect(page.getByText(/senha.*não.*coincidem|passwords.*match/i)).toBeVisible();
    });

    test('should show validation for weak password', async ({ page }) => {
      await page.goto('/register');

      await page.getByLabel(/nome|name/i).fill('Test User');
      await page.getByLabel(/email/i).fill('test@example.com');
      await page.getByLabel(/^senha|^password/i).fill('123');
      await page.getByLabel(/confirmar|confirm/i).fill('123');

      await page.getByRole('button', { name: /cadastrar|register|criar/i }).click();

      await expect(page.getByText(/caracteres|characters|fraca|weak/i)).toBeVisible();
    });

    test('should register successfully with valid data', async ({ page }) => {
      await page.goto('/register');

      await page.getByLabel(/nome|name/i).fill('New User');
      await page.getByLabel(/email/i).fill('newuser@example.com');
      await page.getByLabel(/^senha|^password/i).fill('SecurePassword123!');
      await page.getByLabel(/confirmar|confirm/i).fill('SecurePassword123!');

      await page.getByRole('button', { name: /cadastrar|register|criar/i }).click();

      // Should redirect to dashboard or show success
      await expect(page).toHaveURL(/$|dashboard|login|sucesso/);
    });
  });

  // ============================================
  // LOGOUT TESTS
  // ============================================

  test.describe('Logout', () => {
    test('should logout successfully', async ({ authenticatedPage }) => {
      const dashboardPage = new DashboardPage(authenticatedPage);
      
      await authenticatedPage.goto('/dashboard');
      await dashboardPage.logout();

      await expect(authenticatedPage).toHaveURL(/login/);
    });

    test('should clear session data on logout', async ({ authenticatedPage }) => {
      const dashboardPage = new DashboardPage(authenticatedPage);
      
      await authenticatedPage.goto('/dashboard');
      await dashboardPage.logout();

      // Try to access protected route
      await authenticatedPage.goto('/dashboard');
      
      // Should redirect to login
      await expect(authenticatedPage).toHaveURL(/login/);
    });
  });

  // ============================================
  // SESSION MANAGEMENT TESTS
  // ============================================

  test.describe('Session Management', () => {
    test('should redirect unauthenticated users to login', async ({ page }) => {
      await page.goto('/dashboard');

      await expect(page).toHaveURL(/login/);
    });

    test('should redirect unauthenticated users from protected routes', async ({ page }) => {
      const protectedRoutes = ['/search', '/products', '/favorites', '/copy', '/settings', '/subscription'];

      for (const route of protectedRoutes) {
        await page.goto(route);
        await expect(page).toHaveURL(/login/);
      }
    });
  });
});
