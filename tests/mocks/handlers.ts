/**
 * MSW Request Handlers
 * Mock all external API calls for testing
 */
import { http, HttpResponse, delay } from "msw";
import { mockProducts, mockUser, mockLicense, mockCopyHistory } from "./data";

const API_URL = "http://localhost:8000";

// ============================================
// AUTH HANDLERS
// ============================================

export const authHandlers = [
  // Login
  http.post(`${API_URL}/auth/login`, async ({ request }) => {
    await delay(100);
    const body = (await request.json()) as { email?: string; password?: string };

    if (body.email === "test@example.com" && body.password === "password123") {
      return HttpResponse.json({
        access_token: "mock-jwt-token-12345",
        refresh_token: "mock-refresh-token-12345",
        token_type: "bearer",
        expires_in: 3600,
        user: mockUser,
      });
    }

    return HttpResponse.json(
      { detail: "Invalid credentials" },
      { status: 401 }
    );
  }),

  // Register
  http.post(`${API_URL}/auth/register`, async ({ request }) => {
    await delay(100);
    const body = (await request.json()) as { email?: string };

    if (body.email === "existing@example.com") {
      return HttpResponse.json(
        { detail: "Email already registered" },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      message: "User registered successfully",
      user: { ...mockUser, ...(body as Record<string, unknown>) },
    });
  }),

  // Refresh token
  http.post(`${API_URL}/auth/refresh`, async () => {
    await delay(50);
    return HttpResponse.json({
      access_token: "new-mock-jwt-token-12345",
      expires_in: 3600,
    });
  }),

  // Get current user
  http.get(`${API_URL}/auth/me`, async () => {
    await delay(50);
    return HttpResponse.json(mockUser);
  }),
];

// ============================================
// PRODUCTS HANDLERS
// ============================================

export const productsHandlers = [
  // List products with pagination
  http.get(`${API_URL}/products`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get("page") || "1");
    const limit = parseInt(url.searchParams.get("limit") || "20");
    const search = url.searchParams.get("search") || "";
    const category = url.searchParams.get("category") || "";
    const minPrice = parseFloat(url.searchParams.get("min_price") || "0");
    const maxPrice = parseFloat(url.searchParams.get("max_price") || "999999");

    let filtered = [...mockProducts];

    // Apply filters
    if (search) {
      filtered = filtered.filter(
        (p) =>
          p.title.toLowerCase().includes(search.toLowerCase()) ||
          p.description.toLowerCase().includes(search.toLowerCase())
      );
    }

    if (category) {
      filtered = filtered.filter((p) => p.category === category);
    }

    filtered = filtered.filter(
      (p) => p.price >= minPrice && p.price <= maxPrice
    );

    // Pagination
    const start = (page - 1) * limit;
    const end = start + limit;
    const paginated = filtered.slice(start, end);

    return HttpResponse.json({
      products: paginated,
      total: filtered.length,
      page,
      limit,
      total_pages: Math.ceil(filtered.length / limit),
    });
  }),

  // Get single product
  http.get(`${API_URL}/products/:id`, async ({ params }) => {
    await delay(50);
    const product = mockProducts.find((p) => p.id === params.id);

    if (!product) {
      return HttpResponse.json(
        { detail: "Product not found" },
        { status: 404 }
      );
    }

    return HttpResponse.json(product);
  }),
];

// ============================================
// COPY HANDLERS
// ============================================

export const copyHandlers = [
  // Generate copy
  http.post(`${API_URL}/copy/generate`, async ({ request }) => {
    await delay(500); // Simulate AI generation time
    const body = (await request.json()) as {
      product_id?: string;
      type?: string;
      tone?: string;
    };

    return HttpResponse.json({
      id: `copy-${Date.now()}`,
      product_id: body.product_id,
      type: body.type || "product_description",
      tone: body.tone || "professional",
      content: `Este é um copy mockado para teste. Produto incrível com qualidade excepcional. 
        Não perca essa oportunidade única de adquirir este produto que vai transformar sua vida.
        Compre agora e aproveite condições especiais!`,
      tokens_used: 150,
      created_at: new Date().toISOString(),
    });
  }),

  // Get copy history
  http.get(`${API_URL}/copy/history`, async () => {
    await delay(100);
    return HttpResponse.json({
      copies: mockCopyHistory,
      total: mockCopyHistory.length,
    });
  }),

  // Get quota status
  http.get(`${API_URL}/copy/quota`, async () => {
    await delay(50);
    return HttpResponse.json({
      used: 50,
      limit: 100,
      remaining: 50,
      reset_at: new Date(Date.now() + 86400000).toISOString(), // 24h from now
    });
  }),
];

// ============================================
// LICENSE HANDLERS
// ============================================

export const licenseHandlers = [
  // Validate license
  http.post(`${API_URL}/license/validate`, async ({ request }) => {
    await delay(100);
    const body = (await request.json()) as { license_key?: string; hwid?: string };

    if (body.license_key === "VALID-LICENSE-KEY-123") {
      return HttpResponse.json({
        valid: true,
        license: mockLicense,
      });
    }

    return HttpResponse.json({
      valid: false,
      message: "Invalid license key",
    });
  }),

  // Activate license
  http.post(`${API_URL}/license/activate`, async ({ request }) => {
    await delay(100);
    const body = (await request.json()) as { license_key?: string };

    if (body.license_key === "VALID-LICENSE-KEY-123") {
      return HttpResponse.json({
        success: true,
        license: mockLicense,
      });
    }

    return HttpResponse.json(
      { detail: "Invalid or expired license" },
      { status: 400 }
    );
  }),

  // Deactivate license
  http.post(`${API_URL}/license/deactivate`, async () => {
    await delay(100);
    return HttpResponse.json({
      success: true,
      message: "License deactivated successfully",
    });
  }),
];

// ============================================
// WEBHOOK HANDLERS
// ============================================

export const webhookHandlers = [
  // Mercado Pago webhook
  http.post(`${API_URL}/webhooks/mercadopago`, async () => {
    await delay(50);
    return HttpResponse.json({ received: true });
  }),
];

// ============================================
// EXTERNAL API HANDLERS (MOCKS)
// ============================================

export const externalHandlers = [
  // OpenAI API Mock
  http.post("https://api.openai.com/v1/chat/completions", async () => {
    await delay(300);
    return HttpResponse.json({
      id: "chatcmpl-mock-123",
      object: "chat.completion",
      created: Math.floor(Date.now() / 1000),
      model: "gpt-4",
      choices: [
        {
          index: 0,
          message: {
            role: "assistant",
            content:
              "Este é um texto mockado da OpenAI para testes. Produto incrível!",
          },
          finish_reason: "stop",
        },
      ],
      usage: {
        prompt_tokens: 50,
        completion_tokens: 100,
        total_tokens: 150,
      },
    });
  }),

  // Mercado Pago API Mock
  http.post("https://api.mercadopago.com/v1/payments", async () => {
    await delay(200);
    return HttpResponse.json({
      id: 123456789,
      status: "approved",
      status_detail: "accredited",
      payment_method_id: "pix",
      transaction_amount: 29.9,
    });
  }),

  // Mercado Pago Preference Mock
  http.post("https://api.mercadopago.com/checkout/preferences", async () => {
    await delay(200);
    return HttpResponse.json({
      id: "pref-mock-123",
      init_point: "https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=pref-mock-123",
      sandbox_init_point: "https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id=pref-mock-123",
    });
  }),
];

// ============================================
// UTILITY HANDLERS
// ============================================

export const utilityHandlers = [
  // Health check
  http.get(`${API_URL}/health`, async () => {
    return HttpResponse.json({
      status: "healthy",
      timestamp: new Date().toISOString(),
      version: "1.0.0",
    });
  }),

  // API info
  http.get(`${API_URL}/`, async () => {
    return HttpResponse.json({
      name: "TikTrend Finder API",
      version: "1.0.0",
      environment: "test",
    });
  }),
];

// ============================================
// COMBINED HANDLERS
// ============================================

export const handlers = [
  ...authHandlers,
  ...productsHandlers,
  ...copyHandlers,
  ...licenseHandlers,
  ...webhookHandlers,
  ...externalHandlers,
  ...utilityHandlers,
];
