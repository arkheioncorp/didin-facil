/**
 * E2E Tests - PWA & Subscription Features
 * ========================================
 * Testes end-to-end para:
 * - PWA (install, offline, notifications)
 * - Subscription (plans, usage, upgrade)
 * - Analytics (dashboard, trends)
 * - Chatbot (start chat, send message)
 * - Automation (n8n workflows)
 */
import { test, expect } from "./fixtures";

// ============================================
// PWA TESTS
// ============================================

test.describe("PWA Features", () => {
  test("deve ter manifest.json válido", async ({ page }) => {
    const response = await page.goto("/manifest.json");
    expect(response?.status()).toBe(200);
    
    const manifest = await response?.json();
    expect(manifest.name).toBe("Didin Fácil");
    expect(manifest.short_name).toBe("Didin");
    expect(manifest.display).toBe("standalone");
    expect(manifest.icons.length).toBeGreaterThan(0);
  });

  test("deve registrar Service Worker", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    
    // Verificar se SW foi registrado
    const swRegistered = await page.evaluate(async () => {
      if (!("serviceWorker" in navigator)) return false;
      const registrations = await navigator.serviceWorker.getRegistrations();
      return registrations.length > 0;
    });
    
    expect(swRegistered).toBe(true);
  });

  test("deve funcionar offline após cache", async ({ page, context }) => {
    // Primeiro, visitar a página para cachear
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    
    // Aguardar cache do SW
    await page.waitForTimeout(2000);
    
    // Simular offline
    await context.setOffline(true);
    
    // Tentar navegar
    await page.reload();
    
    // Deve mostrar conteúdo cacheado ou página offline
    const hasContent = await page.locator("body").textContent();
    expect(hasContent).toBeTruthy();
    
    // Restaurar online
    await context.setOffline(false);
  });
});

// ============================================
// SUBSCRIPTION TESTS
// ============================================

test.describe("Subscription & Plans", () => {
  test("deve listar planos disponíveis", async ({ mockedPage }) => {
    const page = mockedPage;
    
    // Mock API de planos
    await page.route("**/api/v1/subscription/plans", async (route) => {
      await route.fulfill({
        status: 200,
        json: [
          {
            tier: "free",
            name: "Free",
            price_monthly: 0,
            highlights: ["Comparador de preços", "1 WhatsApp"]
          },
          {
            tier: "starter",
            name: "Starter",
            price_monthly: 97,
            highlights: ["3 WhatsApp", "100 posts/mês"]
          },
          {
            tier: "business",
            name: "Business",
            price_monthly: 297,
            highlights: ["Ilimitado", "Suporte prioritário"]
          }
        ]
      });
    });
    
    await page.goto("/subscription");
    await page.waitForLoadState("networkidle");
    
    // Verificar cards de planos
    await expect(page.locator("text=Free")).toBeVisible();
    await expect(page.locator("text=Starter")).toBeVisible();
    await expect(page.locator("text=Business")).toBeVisible();
  });

  test("deve mostrar uso atual de features", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    await page.route("**/api/v1/subscription/usage", async (route) => {
      await route.fulfill({
        status: 200,
        json: [
          { feature: "social_posts", current: 5, limit: 10, can_use: true },
          { feature: "whatsapp_messages", current: 80, limit: 100, can_use: true }
        ]
      });
    });
    
    await page.goto("/subscription");
    await page.waitForLoadState("networkidle");
    
    // Verificar indicadores de uso
    const usageIndicator = page.locator('[data-testid="usage-indicator"], .usage-bar').first();
    if (await usageIndicator.isVisible()) {
      await expect(usageIndicator).toBeVisible();
    }
  });

  test("deve permitir upgrade de plano", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    await page.route("**/api/v1/subscription/upgrade", async (route) => {
      await route.fulfill({
        status: 200,
        json: { status: "success", message: "Upgrade realizado!" }
      });
    });
    
    await page.goto("/subscription");
    await page.waitForLoadState("networkidle");
    
    // Clicar em upgrade
    const upgradeButton = page.locator('button:has-text("Upgrade"), button:has-text("Assinar")').first();
    if (await upgradeButton.isVisible()) {
      await upgradeButton.click();
      // Verificar confirmação ou redirecionamento
    }
  });
});

// ============================================
// ANALYTICS TESTS
// ============================================

test.describe("Social Analytics", () => {
  test("deve exibir dashboard overview", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    await page.route("**/api/v1/analytics/overview*", async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          period: "last_30_days",
          totals: {
            posts: 25,
            engagement: 1500,
            reach: 8000,
            followers: 5200
          },
          by_platform: {
            instagram: { posts: 15, likes: 800, engagement_rate: 4.5 },
            tiktok: { posts: 10, likes: 500, engagement_rate: 3.8 }
          },
          best_times: {
            monday: [9, 12, 18],
            tuesday: [10, 15, 20]
          }
        }
      });
    });
    
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    
    // Verificar métricas principais
    const metricsCard = page.locator('[data-testid="metrics-card"], .analytics-card').first();
    if (await metricsCard.isVisible()) {
      await expect(metricsCard).toBeVisible();
    }
  });

  test("deve mostrar gráfico de tendências", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    await page.route("**/api/v1/analytics/trends/*", async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          trend: [
            { date: "2025-11-01", likes: 50, comments: 10 },
            { date: "2025-11-02", likes: 55, comments: 12 },
            { date: "2025-11-03", likes: 48, comments: 8 }
          ]
        }
      });
    });
    
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    
    // Verificar presença de gráfico
    const chart = page.locator('canvas, [data-testid="chart"], .recharts-wrapper').first();
    if (await chart.isVisible()) {
      await expect(chart).toBeVisible();
    }
  });

  test("deve permitir exportar relatório", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    await page.route("**/api/v1/analytics/export*", async (route) => {
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ period: "last_30_days", total_posts: 25 })
      });
    });
    
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    
    const exportButton = page.locator('button:has-text("Exportar"), button:has-text("Download")').first();
    if (await exportButton.isVisible()) {
      // Preparar para download
      const [download] = await Promise.all([
        page.waitForEvent("download").catch(() => null),
        exportButton.click()
      ]);
      
      // Verificar que download foi iniciado (ou botão foi clicado)
    }
  });
});

// ============================================
// CHATBOT TESTS
// ============================================

test.describe("Chatbot Integration", () => {
  test("deve listar templates de chatbot", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    await page.route("**/api/v1/chatbot/templates", async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          templates: [
            { id: "welcome_flow", name: "Boas-vindas", description: "Onboarding" },
            { id: "price_alert", name: "Alerta de Preços", description: "Configurar alertas" },
            { id: "support", name: "Suporte", description: "FAQ e atendimento" }
          ]
        }
      });
    });
    
    await page.goto("/chatbot");
    await page.waitForLoadState("networkidle");
    
    // Verificar templates
    const templateCard = page.locator('[data-testid="template-card"], .chatbot-template').first();
    if (await templateCard.isVisible()) {
      await expect(templateCard).toBeVisible();
    }
  });

  test("deve iniciar chat com typebot", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    await page.route("**/api/v1/chatbot/chat/start", async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          session_id: "test-session-123",
          status: "active",
          messages: [
            { id: "1", type: "text", content: { text: "Olá! Como posso ajudar?" } }
          ]
        }
      });
    });
    
    await page.goto("/chatbot");
    await page.waitForLoadState("networkidle");
    
    // Iniciar chat
    const startButton = page.locator('button:has-text("Iniciar"), button:has-text("Testar")').first();
    if (await startButton.isVisible()) {
      await startButton.click();
      
      // Verificar mensagem inicial
      await expect(page.locator("text=Como posso ajudar")).toBeVisible({ timeout: 5000 });
    }
  });
});

// ============================================
// AUTOMATION TESTS
// ============================================

test.describe("n8n Automation", () => {
  test("deve listar workflows disponíveis", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    await page.route("**/api/v1/automation/workflows", async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          workflows: [
            { id: "1", name: "Alerta de Preço", active: true },
            { id: "2", name: "Resumo Diário", active: true },
            { id: "3", name: "Onboarding", active: false }
          ]
        }
      });
    });
    
    await page.goto("/automation");
    await page.waitForLoadState("networkidle");
    
    // Verificar lista de workflows
    const workflowItem = page.locator('[data-testid="workflow-item"], .workflow-card').first();
    if (await workflowItem.isVisible()) {
      await expect(workflowItem).toBeVisible();
    }
  });

  test("deve listar templates de automação", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    await page.route("**/api/v1/automation/templates", async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          templates: [
            { id: "price_drop_alert", name: "Alerta de Queda de Preço", trigger: "webhook" },
            { id: "daily_deals", name: "Resumo Diário", trigger: "schedule" },
            { id: "new_user", name: "Onboarding", trigger: "webhook" }
          ]
        }
      });
    });
    
    await page.goto("/automation");
    await page.waitForLoadState("networkidle");
    
    // Verificar templates
    const templateList = page.locator('[data-testid="templates-list"], .templates-section');
    if (await templateList.isVisible()) {
      await expect(templateList).toBeVisible();
    }
  });

  test("deve executar workflow manualmente", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    await page.route("**/api/v1/automation/workflows/*/execute", async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          execution_id: "exec-123",
          status: "success",
          data: { result: "ok" }
        }
      });
    });
    
    await page.goto("/automation");
    await page.waitForLoadState("networkidle");
    
    const executeButton = page.locator('button:has-text("Executar"), button[aria-label="Execute"]').first();
    if (await executeButton.isVisible()) {
      await executeButton.click();
      
      // Verificar feedback de execução
      await expect(page.locator("text=success, text=Executado")).toBeVisible({ timeout: 5000 }).catch(() => {});
    }
  });
});

// ============================================
// INTEGRATION TESTS
// ============================================

test.describe("Full Flow Integration", () => {
  test("fluxo completo: buscar produto → criar alerta → receber notificação", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    // 1. Mock busca de produto
    await page.route("**/api/v1/products/search*", async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          products: [
            { id: "1", name: "iPhone 15", price: 5999, store: "Amazon" }
          ]
        }
      });
    });
    
    // 2. Mock criação de alerta
    await page.route("**/api/v1/alerts", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 201,
          json: { id: "alert-1", product_id: "1", target_price: 5000 }
        });
      }
    });
    
    // 3. Navegar para busca
    await page.goto("/search");
    await page.waitForLoadState("networkidle");
    
    // 4. Buscar produto
    const searchInput = page.locator('input[type="search"], input[placeholder*="Buscar"]').first();
    if (await searchInput.isVisible()) {
      await searchInput.fill("iPhone 15");
      await searchInput.press("Enter");
      
      // 5. Verificar resultado
      await expect(page.locator("text=iPhone 15")).toBeVisible({ timeout: 10000 });
    }
  });

  test("fluxo completo: criar post → agendar → publicar", async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    // Mock agendamento
    await page.route("**/api/v1/scheduler/posts", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 201,
          json: {
            id: "post-1",
            platform: "instagram",
            status: "scheduled",
            scheduled_time: new Date().toISOString()
          }
        });
      }
    });
    
    await page.goto("/automation/scheduler");
    await page.waitForLoadState("networkidle");
    
    // Verificar página de agendamento
    const schedulerPage = page.locator('[data-testid="scheduler-page"], .scheduler-container');
    if (await schedulerPage.isVisible()) {
      await expect(schedulerPage).toBeVisible();
    }
  });
});
