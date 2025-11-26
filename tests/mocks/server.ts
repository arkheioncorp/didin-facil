/**
 * MSW Server Setup for API Mocking
 * Used in Node.js environment (Vitest)
 */
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

// Setup MSW server with default handlers
export const server = setupServer(...handlers);
