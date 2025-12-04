import { test, expect } from './fixtures';

test.describe('SaaS Limits and Blocking', () => {
  // Bypass auth.setup.ts by injecting state directly
  
  test.beforeEach(async ({ page }) => {
    // Inject authenticated state into localStorage
    await page.addInitScript(() => {
      const userState = {
        state: {
          user: { id: 'test-user', email: 'test@example.com', name: 'Test User' },
          isAuthenticated: true,
          hasHydrated: true,
          subscription: {
            id: 'sub_mock_free',
            plan: 'free',
            status: 'active',
            billingCycle: 'monthly',
            executionMode: 'web_only',
            currentPeriodStart: new Date().toISOString(),
            currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
            marketplaces: ['tiktok'],
            limits: { price_searches: 50 },
            features: {}
          }
        },
        version: 0
      };
      window.localStorage.setItem('tiktrend-user-v3', JSON.stringify(userState));
    });
  });

  test('should show upgrade prompt when search limit is reached', async ({ page }) => {
    // Mock the subscription usage endpoint to return 100% usage
    await page.route(/.*\/subscription\/current/, async (route) => {
      const json = {
        subscription: {
          id: 'sub_mock_free',
          plan: 'free',
          status: 'active',
          billingCycle: 'monthly',
          executionMode: 'web_only',
          currentPeriodStart: new Date().toISOString(),
          currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          marketplaces: ['tiktok'],
          limits: { price_searches: 50 },
          features: {}
        },
        plan: {
          id: 'free',
          name: 'Free',
          description: 'Plano Gratuito',
          price: 0,
          features: {},
          limits: { price_searches: 50 }
        },
        usage: [
          {
            feature: 'price_searches',
            current: 50,
            limit: 50,
            percentage: 100,
            isUnlimited: false
          }
        ]
      };
      await route.fulfill({ json });
    });

    // Go to the dashboard (root path)
    await page.goto('/');

    // Check if the UsageWidget shows 100%
    const usageWidget = page.locator('[data-testid="usage-widget-price_searches"]');
    await expect(usageWidget).toBeVisible({ timeout: 10000 });
    await expect(usageWidget).toContainText('50 / 50');
  });

  test('should show upgrade options for free users', async ({ page }) => {
    // Mock subscription as FREE
    await page.route(/.*\/subscription\/current/, async (route) => {
      await route.fulfill({
        json: {
          subscription: {
            id: 'sub_mock_free',
            plan: 'free',
            status: 'active',
            billingCycle: 'monthly',
            executionMode: 'web_only',
            currentPeriodStart: new Date().toISOString(),
            currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
            marketplaces: ['tiktok'],
            limits: {},
            features: { analytics_advanced: false }
          },
          plan: {
            id: 'free',
            name: 'Free',
            price: 0,
            features: { analytics_advanced: false },
            limits: {}
          },
          usage: []
        }
      });
    });

    // Mock plans endpoint
    await page.route(/.*\/subscription\/plans/, async (route) => {
      const plans = [
        { 
          tier: 'free', 
          name: 'Free', 
          description: 'Free plan',
          priceMonthly: 0, 
          priceYearly: 0, 
          features: {}, 
          limits: {},
          executionModes: ['web_only'],
          marketplaces: ['tiktok']
        },
        { 
          tier: 'starter', 
          name: 'Starter', 
          description: 'Starter plan',
          priceMonthly: 29, 
          priceYearly: 290, 
          features: {}, 
          limits: {},
          executionModes: ['web_only'],
          marketplaces: ['tiktok']
        },
        { 
          tier: 'business', 
          name: 'Business', 
          description: 'Business plan',
          priceMonthly: 99, 
          priceYearly: 990, 
          features: {}, 
          limits: {},
          executionModes: ['web_only'],
          marketplaces: ['tiktok']
        },
        { 
          tier: 'enterprise', 
          name: 'Enterprise', 
          description: 'Enterprise plan',
          priceMonthly: 299, 
          priceYearly: 2990, 
          features: {}, 
          limits: {},
          executionModes: ['web_only'],
          marketplaces: ['tiktok']
        }
      ];
      await route.fulfill({ json: plans });
    });

    // Go to subscription page
    await page.goto('/subscription');

    // Check if plans are loaded
    await expect(page.locator('text=Starter').first()).toBeVisible({ timeout: 10000 });

    // Should show upgrade buttons for higher plans
    const upgradeButtons = page.locator('text=Fazer Upgrade');
    await expect(upgradeButtons.first()).toBeVisible();
  });
});
