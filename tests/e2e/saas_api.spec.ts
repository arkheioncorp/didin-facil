/**
 * E2E Tests - SaaS Subscription API
 * Tests for the new SaaS Hybrid model - API only
 */

import { test, expect } from "@playwright/test";

test.describe("SaaS Subscription API", () => {

  test("should fetch plans from API successfully", async ({ request }) => {
    const response = await request.get("http://localhost:8000/subscription/plans");
    expect(response.ok()).toBeTruthy();
    
    const plans = await response.json();
    expect(Array.isArray(plans)).toBeTruthy();
    expect(plans.length).toBeGreaterThanOrEqual(1);
    
    const freePlan = plans.find((p: any) => p.tier === "free");
    expect(freePlan).toBeDefined();
    expect(freePlan.name).toBe("Free");
  });

  test("should show correct plan tiers from API", async ({ request }) => {
    const response = await request.get("http://localhost:8000/subscription/plans");
    const plans = await response.json();
    
    const tiers = plans.map((p: any) => p.tier);
    expect(tiers).toContain("free");
    expect(tiers).toContain("starter");
    expect(tiers).toContain("business");
  });

  test("should have execution modes per plan", async ({ request }) => {
    const response = await request.get("http://localhost:8000/subscription/plans");
    const plans = await response.json();
    
    const freePlan = plans.find((p: any) => p.tier === "free");
    expect(freePlan.execution_modes).toContain("web_only");
    
    const businessPlan = plans.find((p: any) => p.tier === "business");
    expect(businessPlan.execution_modes).toContain("local_first");
  });

  test("should have correct pricing", async ({ request }) => {
    const response = await request.get("http://localhost:8000/subscription/plans");
    const plans = await response.json();
    
    const freePlan = plans.find((p: any) => p.tier === "free");
    expect(freePlan.price_monthly).toBe(0);
    
    const starterPlan = plans.find((p: any) => p.tier === "starter");
    expect(starterPlan.price_monthly).toBeGreaterThan(0);
  });

  test("should have plan features and limits", async ({ request }) => {
    const response = await request.get("http://localhost:8000/subscription/plans");
    const plans = await response.json();
    
    const starterPlan = plans.find((p: any) => p.tier === "starter");
    expect(starterPlan.features).toBeDefined();
    expect(starterPlan.limits).toBeDefined();
    expect(starterPlan.highlights).toBeDefined();
  });
});
