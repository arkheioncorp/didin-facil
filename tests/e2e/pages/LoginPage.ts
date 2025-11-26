/**
 * Login Page Object Model
 * Page object for the login page
 */
import { Page, Locator, expect } from "@playwright/test";

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly submitButton: Locator;
  readonly registerLink: Locator;
  readonly forgotPasswordLink: Locator;
  readonly errorMessage: Locator;
  readonly errorAlert: Locator;
  readonly emailError: Locator;
  readonly passwordError: Locator;
  readonly loadingSpinner: Locator;
  readonly passwordToggleButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('[data-testid="email-input"]');
    this.passwordInput = page.locator('[data-testid="password-input"]');
    this.loginButton = page.locator('[data-testid="login-button"]');
    this.submitButton = this.loginButton;
    this.registerLink = page.locator('[data-testid="register-link"]');
    this.forgotPasswordLink = page.locator('[data-testid="forgot-password-link"]');
    this.errorMessage = page.locator('[data-testid="error-message"]');
    this.errorAlert = page.locator('[data-testid="error-alert"], [role="alert"]');
    this.emailError = page.locator('[data-testid="email-error"]');
    this.passwordError = page.locator('[data-testid="password-error"]');
    this.loadingSpinner = page.locator('[data-testid="loading-spinner"]');
    this.passwordToggleButton = page.locator('[data-testid="password-toggle"]');
  }

  // Navigate to login page
  async goto() {
    await this.page.goto("/login");
    await this.page.waitForLoadState("networkidle");
  }

  // Fill login form
  async fillLoginForm(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
  }

  // Submit login form
  async submit() {
    await this.loginButton.click();
  }

  // Perform complete login
  async login(email: string, password: string) {
    await this.fillLoginForm(email, password);
    await this.submit();
  }

  // Wait for successful login (redirect to dashboard)
  async waitForLoginSuccess() {
    await this.page.waitForURL("**/", { timeout: 10000 });
  }

  // Wait for login error
  async waitForLoginError() {
    await expect(this.errorMessage).toBeVisible({ timeout: 5000 });
  }

  // Get error message text
  async getErrorMessage(): Promise<string> {
    return (await this.errorMessage.textContent()) || "";
  }

  // Check if login button is disabled
  async isLoginButtonDisabled(): Promise<boolean> {
    return await this.loginButton.isDisabled();
  }

  // Check if form is loading
  async isLoading(): Promise<boolean> {
    return await this.loadingSpinner.isVisible();
  }

  // Navigate to register page
  async goToRegister() {
    await this.registerLink.click();
    await this.page.waitForURL("**/register");
  }

  // Navigate to register (alias)
  async navigateToRegister() {
    await this.goToRegister();
  }

  // Toggle password visibility
  async togglePasswordVisibility() {
    await this.passwordToggleButton.click();
  }

  // Navigate to forgot password
  async goToForgotPassword() {
    await this.forgotPasswordLink.click();
    await this.page.waitForURL("**/forgot-password");
  }

  // Validate form fields
  async validateEmail(email: string): Promise<boolean> {
    await this.emailInput.fill(email);
    await this.emailInput.blur();
    return !(await this.emailError.isVisible());
  }

  // Check form state
  async isFormValid(): Promise<boolean> {
    const emailValue = await this.emailInput.inputValue();
    const passwordValue = await this.passwordInput.inputValue();
    return emailValue.length > 0 && passwordValue.length > 0;
  }
}
