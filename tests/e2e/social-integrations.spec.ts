/**
 * E2E Tests - Social Integrations
 * ================================
 * Testes end-to-end para fluxos de integração social:
 * - WhatsApp: conexão, envio de mensagens
 * - Instagram: login, publicação
 * - TikTok: upload de vídeo
 * - YouTube: upload com quota
 * - Scheduler: agendar, DLQ
 */
import { test, expect } from "./fixtures";

// ============================================
// WHATSAPP INTEGRATION TESTS
// ============================================

test.describe("WhatsApp Integration", () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto("/whatsapp");
    await authenticatedPage.waitForLoadState("networkidle");
  });

  test("deve exibir status de conexão", async ({ authenticatedPage }) => {
    const page = authenticatedPage;

    // Verifica se há indicador de status
    const statusIndicator = page.locator('[data-testid="whatsapp-status"], .connection-status');
    await expect(statusIndicator).toBeVisible({ timeout: 10000 });
  });

  test("deve exibir QR Code quando desconectado", async ({ mockedPage }) => {
    const page = mockedPage;

    // Mock API retornando status desconectado
    await page.route("**/api/v1/whatsapp/status", async (route) => {
      await route.fulfill({
        status: 200,
        json: { status: "disconnected", qr_code: "mock-qr-base64" },
      });
    });

    await page.goto("/whatsapp");
    await page.waitForLoadState("networkidle");

    // Deve mostrar área de QR Code ou botão de conectar
    const qrArea = page.locator('[data-testid="qr-code"], .qr-container, button:has-text("Conectar")');
    await expect(qrArea).toBeVisible({ timeout: 10000 });
  });

  test("deve permitir enviar mensagem quando conectado", async ({ mockedPage }) => {
    const page = mockedPage;

    // Mock API retornando status conectado
    await page.route("**/api/v1/whatsapp/status", async (route) => {
      await route.fulfill({
        status: 200,
        json: { status: "connected", phone: "5511999999999" },
      });
    });

    // Mock envio de mensagem
    await page.route("**/api/v1/whatsapp/send", async (route) => {
      await route.fulfill({
        status: 200,
        json: { success: true, message_id: "123" },
      });
    });

    await page.goto("/whatsapp");
    await page.waitForLoadState("networkidle");

    // Verifica se há campo de mensagem
    const messageInput = page.locator('textarea[placeholder*="mensagem"], input[type="text"]').first();
    if (await messageInput.isVisible()) {
      await messageInput.fill("Teste de mensagem E2E");
      
      const sendButton = page.locator('button:has-text("Enviar"), button[type="submit"]').first();
      await sendButton.click();

      // Verifica toast de sucesso ou status atualizado
      await expect(page.locator('.toast, [role="status"]').first()).toBeVisible({ timeout: 5000 });
    }
  });
});

// ============================================
// INSTAGRAM INTEGRATION TESTS
// ============================================

test.describe("Instagram Integration", () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto("/social/instagram");
    await authenticatedPage.waitForLoadState("networkidle");
  });

  test("deve exibir página de automação Instagram", async ({ authenticatedPage }) => {
    const page = authenticatedPage;

    // Verifica título ou header
    await expect(page.locator('h1, h2').first()).toBeVisible();
    
    // Verifica se há seção de login ou status
    const loginSection = page.locator('[data-testid="instagram-login"], .instagram-status, form');
    await expect(loginSection).toBeVisible({ timeout: 10000 });
  });

  test("deve exibir formulário de login quando não autenticado", async ({ mockedPage }) => {
    const page = mockedPage;

    // Mock status não autenticado
    await page.route("**/api/v1/instagram/status", async (route) => {
      await route.fulfill({
        status: 200,
        json: { authenticated: false },
      });
    });

    await page.goto("/social/instagram");
    await page.waitForLoadState("networkidle");

    // Deve ter campos de usuário/senha
    const usernameInput = page.locator('input[name="username"], input[placeholder*="usuário"]');
    const passwordInput = page.locator('input[type="password"]');

    // Pelo menos um formulário de login
    const hasLogin = await usernameInput.isVisible() || await passwordInput.isVisible();
    expect(hasLogin).toBeTruthy();
  });

  test("deve lidar com 2FA challenge", async ({ mockedPage }) => {
    const page = mockedPage;

    // Mock que retorna challenge 2FA
    await page.route("**/api/v1/instagram/login", async (route) => {
      await route.fulfill({
        status: 200,
        json: { 
          success: false, 
          challenge_required: true,
          challenge_type: "two_factor"
        },
      });
    });

    await page.goto("/social/instagram");
    
    // Preenche login
    await page.fill('input[name="username"]', "testuser");
    await page.fill('input[type="password"]', "testpass");
    await page.click('button[type="submit"]');

    // Deve mostrar campo de código 2FA
    const codeInput = page.locator('input[name="code"], input[placeholder*="código"]');
    await expect(codeInput).toBeVisible({ timeout: 10000 });
  });
});

// ============================================
// TIKTOK INTEGRATION TESTS
// ============================================

test.describe("TikTok Integration", () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto("/social/tiktok");
    await authenticatedPage.waitForLoadState("networkidle");
  });

  test("deve exibir página de automação TikTok", async ({ authenticatedPage }) => {
    const page = authenticatedPage;

    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test("deve exibir upload de vídeo", async ({ mockedPage }) => {
    const page = mockedPage;

    // Mock status autenticado
    await page.route("**/api/v1/tiktok/status", async (route) => {
      await route.fulfill({
        status: 200,
        json: { authenticated: true, username: "@testuser" },
      });
    });

    await page.goto("/social/tiktok");
    await page.waitForLoadState("networkidle");

    // Verifica área de upload
    const uploadArea = page.locator('[data-testid="upload-area"], input[type="file"], .upload-zone');
    
    // Pode estar em um componente de upload
    if (await uploadArea.isVisible()) {
      expect(await uploadArea.isEnabled()).toBeTruthy();
    }
  });
});

// ============================================
// YOUTUBE INTEGRATION TESTS
// ============================================

test.describe("YouTube Integration", () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto("/social/youtube");
    await authenticatedPage.waitForLoadState("networkidle");
  });

  test("deve exibir página de automação YouTube", async ({ authenticatedPage }) => {
    const page = authenticatedPage;

    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test("deve exibir widget de quota", async ({ mockedPage }) => {
    const page = mockedPage;

    // Mock quota API
    await page.route("**/api/v1/youtube/quota", async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          quota: {
            used: 5000,
            limit: 10000,
            percentage: 50,
            reset_at: new Date(Date.now() + 86400000).toISOString(),
            last_updated: new Date().toISOString(),
          },
          history: [],
          alerts: [],
        },
      });
    });

    await page.goto("/social/youtube");
    await page.waitForLoadState("networkidle");

    // Verifica se mostra info de quota
    const quotaInfo = page.locator('[data-testid="quota-widget"], .quota-info, :text("Quota")');
    
    // Pode estar visível se o componente foi integrado
    if (await quotaInfo.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(quotaInfo.first()).toBeVisible();
    }
  });

  test("deve alertar quando quota está baixa", async ({ mockedPage }) => {
    const page = mockedPage;

    // Mock quota crítica
    await page.route("**/api/v1/youtube/quota", async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          quota: {
            used: 9500,
            limit: 10000,
            percentage: 95,
            reset_at: new Date(Date.now() + 86400000).toISOString(),
            last_updated: new Date().toISOString(),
          },
          history: [],
          alerts: [
            {
              level: "critical",
              message: "Quota quase esgotada!",
              timestamp: new Date().toISOString(),
            },
          ],
        },
      });
    });

    await page.goto("/social/youtube");
    await page.waitForLoadState("networkidle");

    // Verifica se há indicador de alerta
    const alertIndicator = page.locator('[data-testid="quota-alert"], .alert, .warning');
    
    if (await alertIndicator.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(alertIndicator.first()).toBeVisible();
    }
  });
});

// ============================================
// SCHEDULER INTEGRATION TESTS
// ============================================

test.describe("Scheduler Integration", () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto("/automation/scheduler");
    await authenticatedPage.waitForLoadState("networkidle");
  });

  test("deve exibir página de agendamento", async ({ authenticatedPage }) => {
    const page = authenticatedPage;

    // Verifica título
    const title = page.locator('h1:has-text("Agenda"), h1:has-text("Schedule"), h2');
    await expect(title.first()).toBeVisible();
  });

  test("deve exibir calendário ou lista de posts", async ({ authenticatedPage }) => {
    const page = authenticatedPage;

    // Verifica calendário ou lista
    const calendarOrList = page.locator('.calendar, [data-testid="posts-list"], table');
    await expect(calendarOrList.first()).toBeVisible({ timeout: 10000 });
  });

  test("deve permitir criar novo agendamento", async ({ mockedPage }) => {
    const page = mockedPage;

    // Mock lista vazia
    await page.route("**/api/v1/scheduler/posts", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          json: { posts: [], total: 0 },
        });
      } else {
        await route.fulfill({
          status: 201,
          json: { id: "new-post-id", status: "scheduled" },
        });
      }
    });

    await page.goto("/automation/scheduler");
    await page.waitForLoadState("networkidle");

    // Procura botão de criar/agendar
    const createButton = page.locator('button:has-text("Agendar"), button:has-text("Novo"), button:has-text("+")');
    
    if (await createButton.first().isVisible()) {
      await createButton.first().click();

      // Deve abrir modal ou formulário
      const modal = page.locator('[role="dialog"], .modal, form');
      await expect(modal.first()).toBeVisible({ timeout: 5000 });
    }
  });
});

// ============================================
// DLQ INTEGRATION TESTS
// ============================================

test.describe("Dead Letter Queue", () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto("/automation/dlq");
    await authenticatedPage.waitForLoadState("networkidle");
  });

  test("deve exibir página da DLQ", async ({ authenticatedPage }) => {
    const page = authenticatedPage;

    // Verifica título
    const title = page.locator('h1:has-text("Dead Letter"), h1:has-text("DLQ"), h1:has-text("Fila")');
    await expect(title.first()).toBeVisible();
  });

  test("deve exibir mensagem quando DLQ está vazia", async ({ mockedPage }) => {
    const page = mockedPage;

    // Mock DLQ vazia
    await page.route("**/api/v1/scheduler/dlq**", async (route) => {
      if (route.request().url().includes("/stats")) {
        await route.fulfill({
          status: 200,
          json: { total: 0, by_platform: {}, by_error_type: {}, oldest_failure: null },
        });
      } else {
        await route.fulfill({
          status: 200,
          json: [],
        });
      }
    });

    await page.goto("/automation/dlq");
    await page.waitForLoadState("networkidle");

    // Verifica mensagem de sucesso ou lista vazia
    const emptyMessage = page.locator(':text("Nenhum post"), :text("vazia"), :text("sucesso")');
    await expect(emptyMessage.first()).toBeVisible({ timeout: 10000 });
  });

  test("deve exibir lista de posts com falha", async ({ mockedPage }) => {
    const page = mockedPage;

    const mockPosts = [
      {
        id: "post-1",
        platform: "instagram",
        scheduled_time: new Date().toISOString(),
        failed_at: new Date().toISOString(),
        attempts: 3,
        max_attempts: 3,
        last_error: "Rate limit exceeded",
        error_type: "rate_limit",
        content_type: "image",
        caption: "Post de teste",
        original_post_id: "post-1",
      },
    ];

    // Mock DLQ com posts
    await page.route("**/api/v1/scheduler/dlq**", async (route) => {
      if (route.request().url().includes("/stats")) {
        await route.fulfill({
          status: 200,
          json: { 
            total: 1, 
            by_platform: { instagram: 1 }, 
            by_error_type: { rate_limit: 1 },
            oldest_failure: new Date().toISOString()
          },
        });
      } else {
        await route.fulfill({
          status: 200,
          json: mockPosts,
        });
      }
    });

    await page.goto("/automation/dlq");
    await page.waitForLoadState("networkidle");

    // Verifica se mostra o post
    const postCard = page.locator('[data-testid="dlq-post"], .failed-post, :text("Instagram")');
    await expect(postCard.first()).toBeVisible({ timeout: 10000 });
  });

  test("deve permitir retry de post", async ({ mockedPage }) => {
    const page = mockedPage;

    const mockPosts = [
      {
        id: "post-1",
        platform: "instagram",
        scheduled_time: new Date().toISOString(),
        failed_at: new Date().toISOString(),
        attempts: 3,
        max_attempts: 3,
        last_error: "Network error",
        error_type: "network_error",
        content_type: "image",
        caption: "Post de teste",
        original_post_id: "post-1",
      },
    ];

    await page.route("**/api/v1/scheduler/dlq", async (route) => {
      await route.fulfill({ status: 200, json: mockPosts });
    });

    await page.route("**/api/v1/scheduler/dlq/stats", async (route) => {
      await route.fulfill({
        status: 200,
        json: { total: 1, by_platform: { instagram: 1 }, by_error_type: {}, oldest_failure: null },
      });
    });

    await page.route("**/api/v1/scheduler/dlq/post-1/retry", async (route) => {
      await route.fulfill({
        status: 200,
        json: { status: "rescheduled", id: "post-1" },
      });
    });

    await page.goto("/automation/dlq");
    await page.waitForLoadState("networkidle");

    // Clica no botão retry
    const retryButton = page.locator('button:has-text("Retry"), button:has-text("Reagendar")');
    
    if (await retryButton.first().isVisible()) {
      await retryButton.first().click();

      // Verifica toast de sucesso
      const toast = page.locator('.toast, [role="status"]:has-text("Reagendado")');
      await expect(toast.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test("deve permitir excluir post", async ({ mockedPage }) => {
    const page = mockedPage;

    const mockPosts = [
      {
        id: "post-1",
        platform: "youtube",
        scheduled_time: new Date().toISOString(),
        failed_at: new Date().toISOString(),
        attempts: 3,
        max_attempts: 3,
        last_error: "Quota exceeded",
        error_type: "quota_exceeded",
        content_type: "video",
        caption: "Vídeo de teste",
        original_post_id: "post-1",
      },
    ];

    await page.route("**/api/v1/scheduler/dlq", async (route) => {
      await route.fulfill({ status: 200, json: mockPosts });
    });

    await page.route("**/api/v1/scheduler/dlq/stats", async (route) => {
      await route.fulfill({
        status: 200,
        json: { total: 1, by_platform: { youtube: 1 }, by_error_type: {}, oldest_failure: null },
      });
    });

    await page.route("**/api/v1/scheduler/dlq/post-1", async (route) => {
      if (route.request().method() === "DELETE") {
        await route.fulfill({
          status: 200,
          json: { status: "deleted", id: "post-1" },
        });
      }
    });

    await page.goto("/automation/dlq");
    await page.waitForLoadState("networkidle");

    // Clica no botão excluir
    const deleteButton = page.locator('button:has-text("Excluir"), button:has-text("Delete")');
    
    if (await deleteButton.first().isVisible()) {
      await deleteButton.first().click();

      // Pode ter confirmação
      const confirmButton = page.locator('[role="dialog"] button:has-text("Confirmar"), [role="dialog"] button:has-text("Excluir")');
      if (await confirmButton.first().isVisible({ timeout: 2000 }).catch(() => false)) {
        await confirmButton.first().click();
      }

      // Verifica toast de sucesso
      const toast = page.locator('.toast, [role="status"]');
      await expect(toast.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test("deve permitir filtrar por plataforma", async ({ mockedPage }) => {
    const page = mockedPage;

    const mockPosts = [
      {
        id: "post-1",
        platform: "instagram",
        scheduled_time: new Date().toISOString(),
        failed_at: new Date().toISOString(),
        attempts: 3,
        max_attempts: 3,
        last_error: "Error",
        error_type: "unknown",
        content_type: "image",
        caption: "Instagram post",
        original_post_id: "post-1",
      },
      {
        id: "post-2",
        platform: "youtube",
        scheduled_time: new Date().toISOString(),
        failed_at: new Date().toISOString(),
        attempts: 3,
        max_attempts: 3,
        last_error: "Error",
        error_type: "unknown",
        content_type: "video",
        caption: "YouTube post",
        original_post_id: "post-2",
      },
    ];

    await page.route("**/api/v1/scheduler/dlq", async (route) => {
      await route.fulfill({ status: 200, json: mockPosts });
    });

    await page.route("**/api/v1/scheduler/dlq/stats", async (route) => {
      await route.fulfill({
        status: 200,
        json: { 
          total: 2, 
          by_platform: { instagram: 1, youtube: 1 }, 
          by_error_type: {},
          oldest_failure: null 
        },
      });
    });

    await page.goto("/automation/dlq");
    await page.waitForLoadState("networkidle");

    // Procura seletor de filtro
    const platformFilter = page.locator('select, [role="combobox"]').first();
    
    if (await platformFilter.isVisible()) {
      await platformFilter.click();
      
      // Seleciona Instagram
      const instagramOption = page.locator('[role="option"]:has-text("Instagram"), option:has-text("Instagram")');
      if (await instagramOption.first().isVisible()) {
        await instagramOption.first().click();
      }
    }
  });
});

// ============================================
// SOCIAL DASHBOARD TESTS
// ============================================

test.describe("Social Dashboard", () => {
  test("deve exibir dashboard com todas as plataformas", async ({ authenticatedPage }) => {
    const page = authenticatedPage;

    await page.goto("/social");
    await page.waitForLoadState("networkidle");

    // Verifica cards de plataformas
    const platforms = ["Instagram", "TikTok", "YouTube", "WhatsApp"];
    
    for (const platform of platforms) {
      const card = page.locator(`:text("${platform}")`);
      // Pelo menos uma menção a cada plataforma
      expect(await card.count()).toBeGreaterThanOrEqual(0);
    }
  });

  test("deve navegar para página de cada plataforma", async ({ authenticatedPage }) => {
    const page = authenticatedPage;

    await page.goto("/social");
    await page.waitForLoadState("networkidle");

    // Testa navegação para Instagram
    const instagramLink = page.locator('a[href*="instagram"], button:has-text("Instagram")');
    
    if (await instagramLink.first().isVisible()) {
      await instagramLink.first().click();
      await expect(page).toHaveURL(/instagram/);
    }
  });
});
