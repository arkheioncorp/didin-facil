import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// Cleanup after each test
afterEach(() => {
    cleanup();
});

// Mock Tauri API
const mockTauriApi = {
    invoke: vi.fn(),
    event: {
        listen: vi.fn(),
        emit: vi.fn(),
    },
};

// Mock window.__TAURI__
// global.window = Object.create(window); // This line might be causing issues with JSDOM
Object.defineProperty(window, '__TAURI__', {
    value: mockTauriApi,
    writable: true,
});

// Mock Tauri commands
vi.mock('@tauri-apps/api', () => ({
    invoke: vi.fn(),
}));

vi.mock('@tauri-apps/api/tauri', () => ({
    invoke: vi.fn(),
}));

// Mock window.matchMedia
vi.stubGlobal('matchMedia', vi.fn((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
})));

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
    constructor() { }
    disconnect() { }
    observe() { }
    takeRecords() {
        return [];
    }
    unobserve() { }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
} as any;

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
    constructor() { }
    disconnect() { }
    observe() { }
    unobserve() { }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
} as any;

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
  configurable: true,
});
