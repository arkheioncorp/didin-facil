/**
 * Tauri IPC Mock Helpers
 * Mock Tauri commands for testing
 */
import { vi } from "vitest";
import { mockProducts, mockUser, mockLicense, mockFavorites, mockFavoriteLists } from "../mocks/data";

// ============================================
// TAURI COMMAND RESPONSES
// ============================================

type TauriCommandHandler = (...args: unknown[]) => Promise<unknown>;

const commandHandlers: Record<string, TauriCommandHandler> = {
  // Database commands
  get_products: async (args) => {
    const { page = 1, limit = 20, search = "", category = "" } = args as Record<string, unknown> || {};
    let filtered = [...mockProducts];

    if (search) {
      filtered = filtered.filter(
        (p) =>
          p.title.toLowerCase().includes((search as string).toLowerCase()) ||
          p.description.toLowerCase().includes((search as string).toLowerCase())
      );
    }

    if (category) {
      filtered = filtered.filter((p) => p.category === category);
    }

    const start = ((page as number) - 1) * (limit as number);
    const end = start + (limit as number);

    return {
      products: filtered.slice(start, end),
      total: filtered.length,
      page,
      limit,
    };
  },

  get_product: async (args) => {
    const { id } = args as { id: string };
    return mockProducts.find((p) => p.id === id) || null;
  },

  // User commands
  get_current_user: async () => mockUser,

  update_user_preferences: async (args) => {
    const { preferences } = args as { preferences: Record<string, unknown> };
    return { ...mockUser, preferences: { ...mockUser.preferences, ...preferences } };
  },

  // License commands
  validate_license: async (args) => {
    const { key } = args as { key: string };
    if (key === "VALID-LICENSE-KEY-123") {
      return { valid: true, license: mockLicense };
    }
    return { valid: false, message: "Invalid license" };
  },

  get_license_info: async () => mockLicense,

  // Favorites commands
  get_favorites: async () => mockFavorites,

  get_favorite_lists: async () => mockFavoriteLists,

  add_favorite: async (args) => {
    const { product_id: _product_id, list_id } = args as { product_id: string; list_id: string };
    return {
      id: `fav-${Date.now()}`,
      product_id: _product_id,
      list_id,
      created_at: new Date().toISOString(),
    };
  },

  remove_favorite: async () => ({ success: true }),

  create_favorite_list: async (args) => {
    const { name, description, color } = args as { name: string; description?: string; color?: string };
    return {
      id: `list-${Date.now()}`,
      name,
      description: description || "",
      color: color || "#3B82F6",
      product_count: 0,
      created_at: new Date().toISOString(),
    };
  },

  // Search commands
  search_products: async (args) => {
    const { query, filters } = args as { query: string; filters?: Record<string, unknown> };
    let results = mockProducts.filter(
      (p) =>
        p.title.toLowerCase().includes(query.toLowerCase()) ||
        p.description.toLowerCase().includes(query.toLowerCase()) ||
        p.tags.some((t) => t.toLowerCase().includes(query.toLowerCase()))
    );

    if (filters) {
      if (filters.category) {
        results = results.filter((p) => p.category === filters.category);
      }
      if (filters.minPrice) {
        results = results.filter((p) => p.price >= (filters.minPrice as number));
      }
      if (filters.maxPrice) {
        results = results.filter((p) => p.price <= (filters.maxPrice as number));
      }
    }

    return {
      results,
      total: results.length,
      query,
    };
  },

  // HWID commands
  get_hwid: async () => "test-hwid-12345",

  // Storage commands
  get_stored_value: async (args) => {
    const { key } = args as { key: string };
    const storage: Record<string, unknown> = {
      "user-token": "mock-jwt-token",
      "user-preferences": mockUser.preferences,
    };
    return storage[key] || null;
  },

  set_stored_value: async () => ({ success: true }),

  // Export commands
  export_products: async (args) => {
    const { format, products } = args as { format: string; products: unknown[] };
    return {
      success: true,
      file_path: `/tmp/export-${Date.now()}.${format}`,
      count: (products as unknown[]).length,
    };
  },

  // Copy generation (local cache)
  get_cached_copy: async () => {
    // Return null to simulate cache miss
    return null;
  },

  cache_copy: async () => ({ success: true }),
};

// ============================================
// MOCK SETUP FUNCTIONS
// ============================================

/**
 * Setup Tauri invoke mock with default handlers
 */
export function setupTauriMock() {
  const invoke = vi.fn(async (command: string, args?: unknown) => {
    const handler = commandHandlers[command];
    if (handler) {
      return handler(args);
    }
    throw new Error(`Unknown command: ${command}`);
  });

  vi.doMock("@tauri-apps/api/core", () => ({
    invoke,
  }));

  return invoke;
}

/**
 * Mock a specific Tauri command with custom response
 */
export function mockTauriCommand(
  invoke: ReturnType<typeof vi.fn>,
  command: string,
  response: unknown
) {
  invoke.mockImplementation(async (cmd: string, args?: unknown) => {
    if (cmd === command) {
      return typeof response === "function" ? response(args) : response;
    }
    const handler = commandHandlers[cmd];
    if (handler) {
      return handler(args);
    }
    throw new Error(`Unknown command: ${cmd}`);
  });
}

/**
 * Mock Tauri command to throw error
 */
export function mockTauriCommandError(
  invoke: ReturnType<typeof vi.fn>,
  command: string,
  errorMessage: string
) {
  invoke.mockImplementation(async (cmd: string, args?: unknown) => {
    if (cmd === command) {
      throw new Error(errorMessage);
    }
    const handler = commandHandlers[cmd];
    if (handler) {
      return handler(args);
    }
    throw new Error(`Unknown command: ${cmd}`);
  });
}

/**
 * Reset all Tauri mocks
 */
export function resetTauriMocks(invoke: ReturnType<typeof vi.fn>) {
  invoke.mockReset();
  invoke.mockImplementation(async (command: string, args?: unknown) => {
    const handler = commandHandlers[command];
    if (handler) {
      return handler(args);
    }
    throw new Error(`Unknown command: ${command}`);
  });
}

// ============================================
// TAURI EVENT MOCKS
// ============================================

type EventCallback = (event: { payload: unknown }) => void;

const eventListeners: Map<string, EventCallback[]> = new Map();

export const tauriEventMock = {
  listen: vi.fn((event: string, callback: EventCallback) => {
    const listeners = eventListeners.get(event) || [];
    listeners.push(callback);
    eventListeners.set(event, listeners);
    return Promise.resolve(() => {
      const updated = eventListeners.get(event)?.filter((cb) => cb !== callback) || [];
      eventListeners.set(event, updated);
    });
  }),

  emit: vi.fn((event: string, payload: unknown) => {
    const listeners = eventListeners.get(event) || [];
    listeners.forEach((callback) => callback({ payload }));
    return Promise.resolve();
  }),

  once: vi.fn((event: string, callback: EventCallback) => {
    const wrappedCallback: EventCallback = (e) => {
      callback(e);
      const listeners = eventListeners.get(event)?.filter((cb) => cb !== wrappedCallback) || [];
      eventListeners.set(event, listeners);
    };
    const listeners = eventListeners.get(event) || [];
    listeners.push(wrappedCallback);
    eventListeners.set(event, listeners);
    return Promise.resolve(() => {
      const updated = eventListeners.get(event)?.filter((cb) => cb !== wrappedCallback) || [];
      eventListeners.set(event, updated);
    });
  }),

  clearListeners: () => {
    eventListeners.clear();
  },
};

// ============================================
// CLIPBOARD MOCK
// ============================================

let clipboardContent = "";

export const clipboardMock = {
  writeText: vi.fn((text: string) => {
    clipboardContent = text;
    return Promise.resolve();
  }),

  readText: vi.fn(() => {
    return Promise.resolve(clipboardContent);
  }),

  getContent: () => clipboardContent,

  clear: () => {
    clipboardContent = "";
  },
};

// ============================================
// NOTIFICATION MOCK
// ============================================

const sentNotifications: Array<{ title: string; body?: string }> = [];

export const notificationMock = {
  isPermissionGranted: vi.fn(() => Promise.resolve(true)),

  requestPermission: vi.fn(() => Promise.resolve("granted" as const)),

  sendNotification: vi.fn((options: { title: string; body?: string }) => {
    sentNotifications.push(options);
    return Promise.resolve();
  }),

  getSentNotifications: () => [...sentNotifications],

  clear: () => {
    sentNotifications.length = 0;
  },
};

// ============================================
// DIALOG MOCK
// ============================================

export const dialogMock = {
  message: vi.fn(() => Promise.resolve()),

  ask: vi.fn(() => Promise.resolve(true)),

  confirm: vi.fn(() => Promise.resolve(true)),

  open: vi.fn(() => Promise.resolve(null as string | null)),

  save: vi.fn(() => Promise.resolve(null as string | null)),

  // Control mock responses
  setAskResponse: (response: boolean) => {
    dialogMock.ask.mockResolvedValue(response);
  },

  setConfirmResponse: (response: boolean) => {
    dialogMock.confirm.mockResolvedValue(response);
  },

  setOpenResponse: (response: string | null) => {
    dialogMock.open.mockResolvedValue(response);
  },

  setSaveResponse: (response: string | null) => {
    dialogMock.save.mockResolvedValue(response);
  },
};
