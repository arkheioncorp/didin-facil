/**
 * E2E Fixtures
 * Custom fixtures for Playwright tests
 */
import { test as base, Page, BrowserContext } from "@playwright/test";

// ============================================
// CUSTOM FIXTURES
// ============================================

interface CustomFixtures {
  // Authenticated page
  authenticatedPage: Page;
  
  // Page with mocked APIs
  mockedPage: Page;
  
  // Page helpers
  pageHelpers: PageHelpers;
}

interface PageHelpers {
  // Wait for loading to complete
  waitForLoading: () => Promise<void>;
  
  // Take screenshot with timestamp
  screenshot: (name: string) => Promise<void>;
  
  // Get toast message
  getToastMessage: () => Promise<string | null>;
  
  // Close all dialogs
  closeDialogs: () => Promise<void>;
  
  // Simulate slow network
  simulateSlowNetwork: () => Promise<void>;
  
  // Reset to normal network
  resetNetwork: () => Promise<void>;
}

// ============================================
// EXTEND BASE TEST
// ============================================

export const test = base.extend<CustomFixtures>({
  // Authenticated page fixture
  authenticatedPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: "tests/e2e/.auth/user.json",
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },

  // Mocked page fixture (with API interception)
  mockedPage: async ({ page }, use) => {
    // Setup API mocks using route interception
    await setupApiMocks(page);
    await use(page);
  },

  // Page helpers fixture
  pageHelpers: async ({ page }, use) => {
    const helpers: PageHelpers = {
      waitForLoading: async () => {
        // Wait for skeleton loaders to disappear
        await page.waitForSelector('[data-testid="skeleton"]', {
          state: "hidden",
          timeout: 10000,
        }).catch(() => {});
        
        // Wait for spinners to disappear
        await page.waitForSelector('[data-testid="spinner"]', {
          state: "hidden",
          timeout: 10000,
        }).catch(() => {});
        
        // Wait for network to be idle
        await page.waitForLoadState("networkidle");
      },

      screenshot: async (name: string) => {
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        await page.screenshot({
          path: `test-results/screenshots/${name}-${timestamp}.png`,
          fullPage: true,
        });
      },

      getToastMessage: async () => {
        try {
          const toast = await page.waitForSelector('[role="alert"]', {
            timeout: 5000,
          });
          return toast ? await toast.textContent() : null;
        } catch {
          return null;
        }
      },

      closeDialogs: async () => {
        // Close any open dialogs
        const closeButtons = await page.$$('[data-testid="dialog-close"]');
        for (const button of closeButtons) {
          await button.click();
        }
        
        // Press Escape as fallback
        await page.keyboard.press("Escape");
      },

      simulateSlowNetwork: async () => {
        const context = page.context();
        await context.route("**/*", async (route) => {
          await new Promise((resolve) => setTimeout(resolve, 1000));
          await route.continue();
        });
      },

      resetNetwork: async () => {
        const context = page.context();
        await context.unroute("**/*");
      },
    };

    await use(helpers);
  },
});

// ============================================
// API MOCKS SETUP
// ============================================

async function setupApiMocks(page: Page) {
  const API_URL = "http://localhost:8000";

  // Mock auth endpoints
  await page.route(`${API_URL}/auth/**`, async (route) => {
    const url = route.request().url();
    
    if (url.includes("/login")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "mock-jwt-token",
          refresh_token: "mock-refresh-token",
          user: {
            id: "user-123",
            email: "test@example.com",
            name: "Test User",
          },
        }),
      });
    } else if (url.includes("/me")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "user-123",
          email: "test@example.com",
          name: "Test User",
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Mock products endpoint
  await page.route(`${API_URL}/products**`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        products: [
          {
            id: "prod-1",
            title: "Test Product 1",
            price: 99.90,
            image_url: "https://picsum.photos/400/400",
          },
          {
            id: "prod-2",
            title: "Test Product 2",
            price: 149.90,
            image_url: "https://picsum.photos/400/400",
          },
        ],
        total: 2,
        page: 1,
        limit: 20,
      }),
    });
  });

  // Mock copy endpoint
  await page.route(`${API_URL}/copy/**`, async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "copy-1",
          content: "This is a mock generated copy for testing purposes.",
          tokens_used: 100,
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Mock license endpoint
  await page.route(`${API_URL}/license/**`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        valid: true,
        license: {
          key: "VALID-KEY",
          plan: "premium",
          expires_at: "2025-12-31T23:59:59Z",
        },
      }),
    });
  });

  // Mock health endpoint
  await page.route(`${API_URL}/health`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "healthy",
        timestamp: new Date().toISOString(),
      }),
    });
  });
}

// ============================================
// EXPORTS
// ============================================

export { expect } from "@playwright/test";

// Export page object models
export * from "./pages";
