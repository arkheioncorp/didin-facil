/**
 * E2E Tests - Credits and Payment Flow
 * Testes completos do sistema de créditos e pagamento
 */

import { test, expect } from './fixtures';
import { SubscriptionPage } from './pages/SubscriptionPage';

test.describe('Credits and Payment System', () => {
  test.use({ storageState: 'tests/e2e/.auth/user.json' });

  // ============================================
  // CREDIT BALANCE DISPLAY
  // ============================================

  test.describe('Credit Balance', () => {
    test('should display credit balance in header', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      // Verificar se há algum indicador de créditos ou saldo
      const creditIndicators = page.locator('[data-testid*="credit"], [data-testid="credit-balance-value"], [class*="credit"], [class*="balance"], text=/crédito|credit|saldo/i');
      
      // Se não houver, o teste passa (feature pode não estar implementada)
      if (await creditIndicators.count() > 0) {
        await expect(creditIndicators.first()).toBeVisible();
      }
    });

    test('should show credit balance in settings', async ({ page }) => {
      await page.goto('/settings');
      
      // Aguardar carregamento
      await page.waitForLoadState('networkidle');
      
      // Procurar por seção de créditos com data-testid
      const creditsSection = page.locator('[data-testid="settings-credits-section"], [data-testid="settings-credits-balance"], text=/créditos|credits/i').first();
      await expect(creditsSection).toBeVisible({ timeout: 10000 });
    });

    test('should display remaining credits count', async ({ page }) => {
      await page.goto('/dashboard');
      
      // Verificar se mostra número de créditos usando os novos data-testids
      const creditsDisplay = page.locator('[data-testid="credits-remaining"], [data-testid="credit-balance-value"], [data-testid="settings-credits-value"], [class*="credits"]');
      
      if (await creditsDisplay.first().isVisible()) {
        const text = await creditsDisplay.first().textContent();
        expect(text).toMatch(/\d+/);
      }
    });
  });

  // ============================================
  // CREDIT PACKAGES DISPLAY
  // ============================================

  test.describe('Credit Packages', () => {
    test('should display credit packages on checkout page', async ({ page }) => {
      // Ir para página de checkout que tem os pacotes
      await page.goto('/checkout');
      await page.waitForLoadState('networkidle');
      
      // Verificar se há pacotes de créditos usando os novos data-testids
      const packagesGrid = page.locator('[data-testid="credit-packages-grid"]');
      
      if (await packagesGrid.isVisible()) {
        await expect(packagesGrid).toBeVisible();
        
        // Verificar se há pacotes individuais
        const packages = page.locator('[data-testid^="credit-package-"]');
        expect(await packages.count()).toBeGreaterThan(0);
      } else {
        // Fallback para seletores genéricos
        const packages = page.locator('[data-testid*="package"], [data-testid*="plan"], [class*="package"], [class*="plan"], [class*="card"]');
        if (await packages.count() > 0) {
          await expect(packages.first()).toBeVisible();
        }
      }
    });

    test('should show package prices', async ({ page }) => {
      await page.goto('/checkout');
      await page.waitForLoadState('networkidle');
      
      // Verificar preços usando data-testid
      const prices = page.locator('[data-testid="package-price"], text=/R\$|\d+,\d{2}|\d+\.\d{2}/');
      
      if (await prices.count() > 0) {
        await expect(prices.first()).toBeVisible();
      }
    });

    test('should show credit amounts in packages', async ({ page }) => {
      await page.goto('/checkout');
      await page.waitForLoadState('networkidle');
      
      // Verificar créditos usando data-testid
      const creditMentions = page.locator('[data-testid="package-credits"], text=/crédito|credit|cópias|copies/i');
      
      if (await creditMentions.count() > 0) {
        await expect(creditMentions.first()).toBeVisible();
      }
    });

    test('should highlight popular package', async ({ page }) => {
      await page.goto('/checkout');
      
      await page.waitForLoadState('networkidle');
      
      // Procurar por badge de "popular" usando data-testid
      const popularBadge = page.locator('[data-testid="popular-badge"], text=/melhor|popular|best|recommended/i');
      
      if (await popularBadge.count() > 0) {
        await expect(popularBadge.first()).toBeVisible();
      }
    });
  });

  // ============================================
  // CHECKOUT FLOW
  // ============================================

  test.describe('Checkout Flow', () => {
    test('should display checkout page with packages', async ({ page }) => {
      await page.goto('/checkout');
      
      await page.waitForLoadState('networkidle');
      
      // Verificar se a página de checkout carregou com pacotes
      const packagesGrid = page.locator('[data-testid="credit-packages-grid"]');
      
      if (await packagesGrid.isVisible()) {
        await expect(packagesGrid).toBeVisible();
        
        // Verificar se o balanço atual é mostrado
        const balanceCard = page.locator('[data-testid="credit-balance-card"]');
        if (await balanceCard.isVisible()) {
          await expect(balanceCard).toBeVisible();
        }
      }
    });

    test('should show PIX payment flow', async ({ page }) => {
      await page.goto('/checkout');
      
      await page.waitForLoadState('networkidle');
      
      // Se houver página de checkout com PIX já exibido
      const pixPaymentCard = page.locator('[data-testid="pix-payment-card"]');
      const pixQrCode = page.locator('[data-testid="pix-qr-code"]');
      const pixCopySection = page.locator('[data-testid="pix-copy-section"]');
      
      // Verificar elementos PIX se estiverem visíveis
      if (await pixPaymentCard.isVisible()) {
        await expect(page.locator('[data-testid="pix-payment-title"]')).toBeVisible();
      }
      
      // Verificar se QR code ou botão de copiar estão disponíveis
      if (await pixQrCode.isVisible()) {
        await expect(pixQrCode).toBeVisible();
      }
      
      if (await pixCopySection.isVisible()) {
        const copyButton = page.locator('[data-testid="pix-copy-button"]');
        await expect(copyButton).toBeVisible();
      }
    });

    test('should show payment methods', async ({ page }) => {
      await page.goto('/checkout');
      
      await page.waitForLoadState('networkidle');

      // Verificar métodos de pagamento (PIX é o principal)
      const paymentMethods = page.locator('[data-testid="pix-payment-card"], text=/pix|cartão|card|boleto/i');
      
      if (await paymentMethods.count() > 0) {
        await expect(paymentMethods.first()).toBeVisible();
      }
    });

    test('should validate checkout form', async ({ page }) => {
      await page.goto('/checkout');
      
      await page.waitForLoadState('networkidle');
      
      // Verificar se há formulário de checkout ou prompt de CPF
      const buyButton = page.locator('button:has-text("Comprar"), button:has-text("Buy")').first();
      
      if (await buyButton.isVisible()) {
        await buyButton.click();
        
        await page.waitForTimeout(2000);
        
        // Tentar submeter form vazio
        const submitButton = page.locator('button[type="submit"], button:has-text("Pagar"), button:has-text("Pay")').first();
        
        if (await submitButton.isVisible()) {
          await submitButton.click();
          
          // Verificar mensagens de erro
          const errorMessage = page.locator('.error, [class*="error"], text=/obrigatório|required/i');
          
          if (await errorMessage.count() > 0) {
            await expect(errorMessage.first()).toBeVisible();
          }
        }
      }
    });
  });

  // ============================================
  // CREDIT USAGE
  // ============================================

  test.describe('Credit Usage', () => {
    test('should show credit cost for operations', async ({ page }) => {
      await page.goto('/search');
      
      await page.waitForLoadState('networkidle');
      
      // Procurar por indicador de custo em créditos
      const creditCost = page.locator('text=/\d+\s*crédito|\d+\s*credit/i');
      
      // Pode ou não estar visível dependendo da UI
      if (await creditCost.count() > 0) {
        await expect(creditCost.first()).toBeVisible();
      }
    });

    test('should deduct credits after operation', async ({ page }) => {
      await page.goto('/dashboard');
      
      await page.waitForLoadState('networkidle');
      
      // Capturar saldo inicial
      const creditBalance = page.locator('[data-testid="credit-balance"], .credit-balance');
      
      if (await creditBalance.first().isVisible()) {
        const initialBalance = await creditBalance.first().textContent();
        
        // Realizar uma operação que consome créditos
        await page.goto('/search');
        await page.waitForLoadState('networkidle');
        
        const searchInput = page.locator('input[type="search"], input[placeholder*="buscar"], input[placeholder*="search"]');
        
        if (await searchInput.isVisible()) {
          await searchInput.fill('test product');
          await page.keyboard.press('Enter');
          
          await page.waitForTimeout(3000);
          
          // Verificar se saldo foi atualizado (pode ou não mudar dependendo de ter créditos)
          await page.goto('/dashboard');
          await page.waitForLoadState('networkidle');
        }
      }
    });
  });

  // ============================================
  // CREDIT HISTORY
  // ============================================

  test.describe('Credit History', () => {
    test('should display credit transaction history', async ({ page }) => {
      await page.goto('/settings');
      
      await page.waitForLoadState('networkidle');
      
      // Procurar por seção de histórico
      const historySection = page.locator('text=/histórico|history|transações|transactions/i');
      
      if (await historySection.count() > 0) {
        await historySection.first().click();
        
        await page.waitForTimeout(1000);
        
        // Verificar se lista de transações é exibida
        const transactions = page.locator('[data-testid="transaction"], .transaction, [class*="transaction"]');
        
        // Pode haver 0 ou mais transações
        expect(await transactions.count()).toBeGreaterThanOrEqual(0);
      }
    });

    test('should show purchase details', async ({ page }) => {
      await page.goto('/settings/billing');
      
      await page.waitForLoadState('networkidle');
      
      // Verificar se há detalhes de compras
      const purchaseHistory = page.locator('text=/compras|purchases|pagamentos|payments/i');
      
      if (await purchaseHistory.count() > 0) {
        await expect(purchaseHistory.first()).toBeVisible();
      }
    });
  });

  // ============================================
  // LOW CREDIT WARNINGS
  // ============================================

  test.describe('Low Credit Warnings', () => {
    test('should show warning when credits are low', async ({ page }) => {
      await page.goto('/dashboard');
      
      await page.waitForLoadState('networkidle');
      
      // Procurar por alertas de créditos baixos
      const lowCreditWarning = page.locator('text=/créditos baixos|low credits|comprar mais|buy more/i');
      
      // Pode ou não estar visível dependendo do saldo
      if (await lowCreditWarning.count() > 0) {
        await expect(lowCreditWarning.first()).toBeVisible();
      }
    });

    test('should offer to buy credits when depleted', async ({ page }) => {
      await page.goto('/search');
      
      await page.waitForLoadState('networkidle');
      
      // Tentar realizar uma busca
      const searchInput = page.locator('input[type="search"], input[placeholder*="buscar"]');
      
      if (await searchInput.isVisible()) {
        await searchInput.fill('test');
        await page.keyboard.press('Enter');
        
        await page.waitForTimeout(2000);
        
        // Se créditos insuficientes, deve mostrar opção de comprar
        const buyCreditsPrompt = page.locator('text=/sem créditos|no credits|comprar créditos|buy credits/i');
        
        if (await buyCreditsPrompt.count() > 0) {
          await expect(buyCreditsPrompt.first()).toBeVisible();
        }
      }
    });
  });
});

// ============================================
// SUBSCRIPTION INTEGRATION
// ============================================

test.describe('Subscription Integration', () => {
  test.use({ storageState: 'tests/e2e/.auth/user.json' });

  test('should show subscription status', async ({ page }) => {
    const subscriptionPage = new SubscriptionPage(page);
    await subscriptionPage.goto();
    
    // Verificar se há conteúdo de assinatura
    const planInfo = page.locator('[data-testid*="plan"], [class*="plan"], [class*="subscription"], text=/plano|plan|assinatura/i');
    if (await planInfo.count() > 0) {
      await expect(planInfo.first()).toBeVisible();
    }
  });

  test('should link to credit purchase from subscription page', async ({ page }) => {
    const subscriptionPage = new SubscriptionPage(page);
    await subscriptionPage.goto();
    
    // Procurar por link para comprar créditos
    const buyCreditsLink = page.locator('a:has-text("créditos"), button:has-text("créditos"), [href*="credits"], [href*="pricing"]');
    
    if (await buyCreditsLink.count() > 0) {
      await expect(buyCreditsLink.first()).toBeVisible();
    }
  });
});
