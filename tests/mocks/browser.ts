/**
 * MSW Browser Setup for API Mocking
 * Used in browser environment (Development/E2E)
 */
import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

// Setup MSW worker with default handlers
export const worker = setupWorker(...handlers);
