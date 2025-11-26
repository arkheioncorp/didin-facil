/**
 * Playwright Global Teardown
 * Runs once after all tests
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function globalTeardown() {
  console.log("🧹 Starting global teardown...");

  // Clean up test artifacts if needed
  const testResultsDir = path.join(__dirname, "../../test-results");
  
  // Keep test results but clean up temporary files
  const tempFiles = ["temp-*.json", "*.tmp"];
  
  try {
    if (fs.existsSync(testResultsDir)) {
      const files = fs.readdirSync(testResultsDir);
      files.forEach((file) => {
        if (tempFiles.some((pattern) => {
          const regex = new RegExp(pattern.replace("*", ".*"));
          return regex.test(file);
        })) {
          fs.unlinkSync(path.join(testResultsDir, file));
        }
      });
    }
  } catch (error) {
    console.warn("Warning during cleanup:", error);
  }

  console.log("✅ Global teardown complete");
}

export default globalTeardown;
