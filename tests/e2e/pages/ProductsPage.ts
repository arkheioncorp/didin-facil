/**
 * Products Page Object Model
 */
import { Page, Locator, expect } from "@playwright/test";

export class ProductsPage {
  readonly page: Page;
  readonly productsGrid: Locator;
  readonly productCards: Locator;
  readonly viewToggle: Locator;
  readonly sortDropdown: Locator;
  readonly filterPanel: Locator;
  readonly categorySelect: Locator;
  readonly minPriceInput: Locator;
  readonly maxPriceInput: Locator;
  readonly trendingToggle: Locator;
  readonly clearFiltersButton: Locator;
  readonly activeFilterCount: Locator;
  readonly paginationContainer: Locator;
  readonly previousButton: Locator;
  readonly nextButton: Locator;
  readonly currentPageIndicator: Locator;
  readonly favoriteButton: Locator;
  readonly productDetailModal: Locator;

  constructor(page: Page) {
    this.page = page;
    this.productsGrid = page.locator('[data-testid="products-grid"]');
    this.productCards = page.locator('[data-testid="product-card"]');
    this.viewToggle = page.locator('[data-testid="view-toggle"]');
    this.sortDropdown = page.locator('[data-testid="sort-dropdown"]');
    this.filterPanel = page.locator('[data-testid="filter-panel"], [data-testid="filters-panel"]');
    this.categorySelect = page.locator('[data-testid="category-select"]');
    this.minPriceInput = page.locator('[data-testid="min-price-input"]');
    this.maxPriceInput = page.locator('[data-testid="max-price-input"]');
    this.trendingToggle = page.locator('[data-testid="trending-toggle"]');
    this.clearFiltersButton = page.locator('[data-testid="clear-filters"]');
    this.activeFilterCount = page.locator('[data-testid="active-filter-count"]');
    this.paginationContainer = page.locator('[data-testid="pagination"]');
    this.previousButton = page.locator('[data-testid="prev-page"]');
    this.nextButton = page.locator('[data-testid="next-page"]');
    this.currentPageIndicator = page.locator('[data-testid="current-page"]');
    this.favoriteButton = page.locator('[data-testid="favorite-button"]');
    this.productDetailModal = page.locator('[data-testid="product-detail-modal"], [role="dialog"]');
  }

  async goto() {
    await this.page.goto("/products");
    await this.page.waitForLoadState("networkidle");
  }

  async getProductCount(): Promise<number> {
    return await this.productCards.count();
  }

  async clickProduct(index: number) {
    await this.productCards.nth(index).click();
  }

  async toggleView() {
    await this.viewToggle.click();
  }

  async sortBy(option: string) {
    await this.sortDropdown.click();
    await this.page.locator(`[data-value="${option}"]`).click();
  }

  // Filter methods
  async selectCategory(category: string) {
    await this.categorySelect.click();
    await this.page.locator(`[data-value="${category}"]`).click();
  }

  async setPriceRange(min: number, max: number) {
    await this.minPriceInput.fill(String(min));
    await this.maxPriceInput.fill(String(max));
    await this.page.keyboard.press('Enter');
  }

  async toggleTrendingFilter() {
    await this.trendingToggle.click();
  }

  async clearFilters() {
    await this.clearFiltersButton.click();
  }

  // Pagination methods
  async nextPage() {
    await this.nextButton.click();
  }

  async previousPage() {
    await this.previousButton.click();
  }

  async goToPage(pageNumber: number) {
    await this.paginationContainer.locator(`[data-page="${pageNumber}"]`).click();
  }

  // Favorite methods
  async favoriteFirstProduct() {
    await this.favoriteButton.first().click();
  }

  async favoriteProduct(index: number) {
    await this.favoriteButton.nth(index).click();
  }

  // ============================================
  // PRODUCT ACTIONS PANEL METHODS
  // ============================================

  // Modal locators
  get copyModal() {
    return this.page.locator('[role="dialog"]:has-text("Gerar Copy com IA")');
  }

  get whatsappModal() {
    return this.page.locator('[role="dialog"]:has-text("Enviar via WhatsApp")');
  }

  get scheduleModal() {
    return this.page.locator('[role="dialog"]:has-text("Agendar Publicação")');
  }

  get actionsTab() {
    return this.page.locator('[data-testid="tab-actions"]');
  }

  get statsTab() {
    return this.page.locator('[data-testid="tab-stats"]');
  }

  get infoTab() {
    return this.page.locator('[data-testid="tab-info"]');
  }

  get actionsPanel() {
    return this.page.locator('[data-testid="actions-panel"]');
  }

  // Open product and switch to actions tab
  async openProductActions(index: number = 0) {
    await this.productCards.nth(index).click();
    await this.productDetailModal.waitFor({ state: 'visible' });
    await this.actionsTab.click();
  }

  // Copy AI Modal actions
  async openCopyModal() {
    await this.page.locator('button:has-text("Gerar Copy com IA")').click();
    await this.copyModal.waitFor({ state: 'visible' });
  }

  async selectCopyType(type: string) {
    await this.page.locator('[data-testid="copy-type-select"]').click();
    await this.page.locator(`[data-value="${type}"]`).click();
  }

  async selectCopyTone(tone: string) {
    await this.page.locator('[data-testid="copy-tone-select"]').click();
    await this.page.locator(`[data-value="${tone}"]`).click();
  }

  async generateCopy() {
    await this.page.locator('button:has-text("Gerar Copy")').click();
  }

  // WhatsApp Modal actions
  async openWhatsAppModal() {
    await this.page.locator('button:has-text("Enviar via WhatsApp")').click();
    await this.whatsappModal.waitFor({ state: 'visible' });
  }

  async fillWhatsAppNumber(number: string) {
    await this.page.locator('input[type="tel"]').fill(number);
  }

  async editWhatsAppMessage(message: string) {
    await this.page.locator('textarea').fill(message);
  }

  async sendWhatsApp() {
    await this.page.locator('button:has-text("Enviar")').click();
  }

  // Schedule Modal actions
  async openScheduleModal() {
    await this.page.locator('button:has-text("Agendar Publicação")').click();
    await this.scheduleModal.waitFor({ state: 'visible' });
  }

  async selectSchedulePlatform(platform: string) {
    await this.page.locator('[data-testid="platform-select"]').click();
    await this.page.locator(`[data-value="${platform}"]`).click();
  }

  async setScheduleDateTime(dateTime: string) {
    await this.page.locator('input[type="datetime-local"]').fill(dateTime);
  }

  async confirmSchedule() {
    await this.page.locator('button:has-text("Agendar")').click();
  }

  // Quick actions (card hover)
  async hoverProductCard(index: number = 0) {
    await this.productCards.nth(index).hover();
  }

  async clickQuickCopy(index: number = 0) {
    await this.hoverProductCard(index);
    await this.productCards.nth(index).locator('button:has-text("Gerar Copy")').click();
  }

  async clickQuickSchedule(index: number = 0) {
    await this.hoverProductCard(index);
    await this.productCards.nth(index).locator('[data-testid="quick-schedule"]').click();
  }

  async clickQuickWhatsApp(index: number = 0) {
    await this.hoverProductCard(index);
    await this.productCards.nth(index).locator('[data-testid="quick-whatsapp"]').click();
  }

  async clickQuickFavorite(index: number = 0) {
    await this.hoverProductCard(index);
    await this.productCards.nth(index).locator('[data-testid="quick-favorite"]').click();
  }

  // Other quick actions
  async copyProductInfo() {
    await this.page.locator('button:has-text("Copiar Informações")').click();
  }

  async clickSellerBot() {
    await this.page.locator('button:has-text("Seller Bot")').click();
  }

  async clickAddToCRM() {
    await this.page.locator('button:has-text("Adicionar ao CRM")').click();
  }

  async clickInstagram() {
    await this.page.locator('button:has-text("Publicar no Instagram")').click();
  }

  async clickTikTok() {
    await this.page.locator('button:has-text("Publicar no TikTok")').click();
  }

  async clickYouTube() {
    await this.page.locator('button:has-text("Publicar no YouTube")').click();
  }

  // Close modals
  async closeModal() {
    await this.page.locator('button:has-text("Cancelar")').click();
  }

  async closeModalByEscape() {
    await this.page.keyboard.press('Escape');
  }
}
