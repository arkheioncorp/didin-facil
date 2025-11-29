/**
 * Vitest Global Setup
 * This file runs before all tests
 */
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { vi, beforeAll, afterEach, afterAll, expect } from "vitest";
import { server } from "./mocks/server";

// ============================================
// MOCK SETUP
// ============================================

// Mock Tauri API
vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(),
}));

vi.mock("@tauri-apps/api/event", () => ({
  listen: vi.fn(() => Promise.resolve(() => { })),
  emit: vi.fn(),
  once: vi.fn(),
}));

vi.mock("@tauri-apps/plugin-clipboard-manager", () => ({
  writeText: vi.fn(() => Promise.resolve()),
  readText: vi.fn(() => Promise.resolve("")),
}));

vi.mock("@tauri-apps/plugin-dialog", () => ({
  message: vi.fn(() => Promise.resolve()),
  ask: vi.fn(() => Promise.resolve(true)),
  confirm: vi.fn(() => Promise.resolve(true)),
  open: vi.fn(() => Promise.resolve(null)),
  save: vi.fn(() => Promise.resolve(null)),
}));

vi.mock("@tauri-apps/plugin-notification", () => ({
  isPermissionGranted: vi.fn(() => Promise.resolve(true)),
  requestPermission: vi.fn(() => Promise.resolve("granted")),
  sendNotification: vi.fn(() => Promise.resolve()),
}));

vi.mock("@tauri-apps/plugin-store", () => ({
  Store: vi.fn().mockImplementation(() => ({
    get: vi.fn(() => Promise.resolve(null)),
    set: vi.fn(() => Promise.resolve()),
    delete: vi.fn(() => Promise.resolve()),
    clear: vi.fn(() => Promise.resolve()),
    keys: vi.fn(() => Promise.resolve([])),
    values: vi.fn(() => Promise.resolve([])),
    entries: vi.fn(() => Promise.resolve([])),
    length: vi.fn(() => Promise.resolve(0)),
    load: vi.fn(() => Promise.resolve()),
    save: vi.fn(() => Promise.resolve()),
  })),
}));

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
const mockIntersectionObserver = vi.fn();
mockIntersectionObserver.mockReturnValue({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null,
});
window.IntersectionObserver = mockIntersectionObserver;

// Mock ResizeObserver
const mockResizeObserver = vi.fn();
mockResizeObserver.mockReturnValue({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null,
});
window.ResizeObserver = mockResizeObserver;

// Mock scrollTo
window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(() => null),
};
Object.defineProperty(window, "localStorage", { 
  value: localStorageMock,
  writable: true,
  configurable: true
});

// ============================================
// MSW SETUP
// ============================================

beforeAll(() => {
  // Start MSW server before all tests
  server.listen({ onUnhandledRequest: "warn" });
});

afterEach(() => {
  // Reset handlers after each test
  server.resetHandlers();
  // Cleanup React Testing Library
  cleanup();
  // Clear all mocks
  vi.clearAllMocks();
});

afterAll(() => {
  // Close MSW server after all tests
  server.close();
});

// ============================================
// CUSTOM MATCHERS
// ============================================

expect.extend({
  toBeWithinRange(received: number, floor: number, ceiling: number) {
    const pass = received >= floor && received <= ceiling;
    if (pass) {
      return {
        message: () =>
          `expected ${received} not to be within range ${floor} - ${ceiling}`,
        pass: true,
      };
    } else {
      return {
        message: () =>
          `expected ${received} to be within range ${floor} - ${ceiling}`,
        pass: false,
      };
    }
  },
});

// ============================================
// GLOBAL TEST HELPERS
// ============================================

// Set testing environment
process.env.TESTING_MODE = "true";
process.env.VITE_API_URL = "http://localhost:8000";

// Console error handler for debugging
const originalError = console.error;
console.error = (...args: unknown[]) => {
  // Suppress specific React warnings in tests
  const suppressedWarnings = [
    "Warning: ReactDOM.render is no longer supported",
    "Warning: An update to",
  ];

  const message = args[0]?.toString() || "";
  if (!suppressedWarnings.some((warning) => message.includes(warning))) {
    originalError.apply(console, args);
  }
};
