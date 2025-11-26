/**
 * Playwright Global Setup
 * Runs once before all tests
 */
import { chromium, FullConfig } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function globalSetup(config: FullConfig) {
  console.log("🚀 Starting global setup...");

  // Create auth directory if it doesn't exist
  const authDir = path.join(__dirname, ".auth");
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  // Create empty auth file for unauthenticated tests
  const emptyAuthPath = path.join(authDir, "user.json");
  if (!fs.existsSync(emptyAuthPath)) {
    fs.writeFileSync(
      emptyAuthPath,
      JSON.stringify({ cookies: [], origins: [] })
    );
  }

  // Setup browser for authentication
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Wait for the dev server to be ready
    const baseURL = config.projects[0]?.use?.baseURL || "http://localhost:5173";
    await page.goto(baseURL, { timeout: 30000 });
    console.log(`✅ Dev server is ready at ${baseURL}`);

    // Perform login for authenticated tests (if needed)
    // This creates a logged-in state that can be reused
    
    // Save storage state for authenticated tests
    await context.storageState({ path: emptyAuthPath });
    console.log("✅ Auth state saved");
  } catch (error) {
    console.error("❌ Global setup failed:", error);
    throw error;
  } finally {
    await browser.close();
  }

  // Set environment variables for tests
  process.env.TESTING_MODE = "true";
  process.env.TEST_HWID = "test-hwid-e2e-12345";

  console.log("✅ Global setup complete");
}

export default globalSetup;
