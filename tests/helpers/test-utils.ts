/**
 * General Test Utilities
 * Common helpers for testing
 */
import { vi } from "vitest";

// ============================================
// ASYNC UTILITIES
// ============================================

/**
 * Wait for a condition to be true
 */
export async function waitUntil(
  condition: () => boolean | Promise<boolean>,
  options: { timeout?: number; interval?: number } = {}
): Promise<void> {
  const { timeout = 5000, interval = 50 } = options;
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    if (await condition()) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  throw new Error(`Condition not met within ${timeout}ms`);
}

/**
 * Wait for a specific amount of time
 */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Flush all pending promises
 */
export async function flushPromises(): Promise<void> {
  await new Promise((resolve) => setImmediate(resolve));
}

// ============================================
// DOM UTILITIES
// ============================================

/**
 * Simulate a scroll event
 */
export function simulateScroll(element: Element, scrollTop: number): void {
  Object.defineProperty(element, "scrollTop", {
    writable: true,
    value: scrollTop,
  });
  element.dispatchEvent(new Event("scroll", { bubbles: true }));
}

/**
 * Simulate window resize
 */
export function simulateResize(width: number, height: number): void {
  Object.defineProperty(window, "innerWidth", {
    writable: true,
    value: width,
  });
  Object.defineProperty(window, "innerHeight", {
    writable: true,
    value: height,
  });
  window.dispatchEvent(new Event("resize"));
}

/**
 * Simulate keyboard event
 */
export function simulateKeyPress(
  element: Element,
  key: string,
  options: Partial<KeyboardEventInit> = {}
): void {
  const event = new KeyboardEvent("keydown", {
    key,
    bubbles: true,
    cancelable: true,
    ...options,
  });
  element.dispatchEvent(event);
}

// ============================================
// STORE UTILITIES
// ============================================

/**
 * Reset all Zustand stores to initial state
 */
export function resetAllStores(): void {
  // Import stores dynamically to avoid circular dependencies
  const stores = [
    "@/stores/userStore",
    "@/stores/productsStore",
    "@/stores/searchStore",
    "@/stores/favoritesStore",
  ];

  stores.forEach(async (storePath) => {
    try {
      const module = await import(storePath);
      const store = module.default || Object.values(module)[0];
      if (store?.getState && store?.setState) {
        const initialState = store.getState();
        store.setState(initialState, true);
      }
    } catch {
      // Store not found, skip
    }
  });
}

/**
 * Create a mock store state
 */
export function createMockStoreState<T extends object>(
  initialState: T,
  overrides: Partial<T> = {}
): T {
  return { ...initialState, ...overrides };
}

// ============================================
// API UTILITIES
// ============================================

/**
 * Create a mock API response
 */
export function createMockResponse<T>(
  data: T,
  options: { status?: number; headers?: Record<string, string> } = {}
): Response {
  const { status = 200, headers = {} } = options;

  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  });
}

/**
 * Create a mock error response
 */
export function createMockErrorResponse(
  message: string,
  status = 400
): Response {
  return new Response(JSON.stringify({ detail: message }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// ============================================
// DATE UTILITIES
// ============================================

/**
 * Mock the current date
 */
export function mockDate(date: Date | string | number): () => void {
  const originalDate = global.Date;
  const mockDateInstance = new originalDate(date);

  vi.useFakeTimers();
  vi.setSystemTime(mockDateInstance);

  return () => {
    vi.useRealTimers();
  };
}

/**
 * Create a date relative to now
 */
export function createRelativeDate(
  amount: number,
  unit: "days" | "hours" | "minutes" | "seconds" = "days"
): Date {
  const now = new Date();
  const multipliers = {
    days: 24 * 60 * 60 * 1000,
    hours: 60 * 60 * 1000,
    minutes: 60 * 1000,
    seconds: 1000,
  };

  return new Date(now.getTime() + amount * multipliers[unit]);
}

// ============================================
// VALIDATION UTILITIES
// ============================================

/**
 * Check if an element is visible in the viewport
 */
export function isElementVisible(element: Element): boolean {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

/**
 * Check if an element has specific styles
 */
export function hasStyles(
  element: Element,
  styles: Record<string, string>
): boolean {
  const computedStyle = window.getComputedStyle(element);
  return Object.entries(styles).every(
    ([property, value]) =>
      computedStyle.getPropertyValue(property) === value
  );
}

// ============================================
// ACCESSIBILITY UTILITIES
// ============================================

/**
 * Get all focusable elements within a container
 */
export function getFocusableElements(container: Element): Element[] {
  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ];

  return Array.from(container.querySelectorAll(focusableSelectors.join(", ")));
}

/**
 * Check if element has proper ARIA attributes
 */
export function hasAriaAttributes(
  element: Element,
  attributes: Record<string, string>
): boolean {
  return Object.entries(attributes).every(
    ([attr, value]) => element.getAttribute(attr) === value
  );
}

// ============================================
// SNAPSHOT UTILITIES
// ============================================

/**
 * Create a serializable snapshot of component props
 */
export function createPropsSnapshot<T extends object>(props: T): string {
  return JSON.stringify(props, null, 2);
}

/**
 * Compare two objects for equality (deep)
 */
export function deepEqual(obj1: unknown, obj2: unknown): boolean {
  if (obj1 === obj2) return true;

  if (
    typeof obj1 !== "object" ||
    typeof obj2 !== "object" ||
    obj1 === null ||
    obj2 === null
  ) {
    return false;
  }

  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);

  if (keys1.length !== keys2.length) return false;

  return keys1.every((key) =>
    deepEqual(
      (obj1 as Record<string, unknown>)[key],
      (obj2 as Record<string, unknown>)[key]
    )
  );
}

// ============================================
// DEBUG UTILITIES
// ============================================

/**
 * Log component tree for debugging
 */
export function logComponentTree(container: Element, indent = 0): void {
  const prefix = "  ".repeat(indent);
  const tagName = container.tagName.toLowerCase();
  const id = container.id ? `#${container.id}` : "";
  const classes = container.className ? `.${container.className.split(" ").join(".")}` : "";

  console.log(`${prefix}<${tagName}${id}${classes}>`);

  Array.from(container.children).forEach((child) => {
    logComponentTree(child, indent + 1);
  });
}

/**
 * Get all text content from an element
 */
export function getAllTextContent(element: Element): string[] {
  const texts: string[] = [];

  function traverse(node: Node): void {
    if (node.nodeType === Node.TEXT_NODE && node.textContent?.trim()) {
      texts.push(node.textContent.trim());
    }

    node.childNodes.forEach(traverse);
  }

  traverse(element);
  return texts;
}
