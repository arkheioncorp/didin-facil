import { invoke } from "@tauri-apps/api/core";
import type { ScraperConfig, ScraperStatus } from "@/types";

export async function startScraper(config: ScraperConfig): Promise<ScraperStatus> {
  try {
    return await invoke<ScraperStatus>("scrape_tiktok_shop", { config });
  } catch (error) {
    console.error("Error starting scraper:", error);
    throw error;
  }
}

export async function getScraperStatus(): Promise<ScraperStatus> {
  try {
    return await invoke<ScraperStatus>("get_scraper_status");
  } catch (error) {
    console.error("Error getting scraper status:", error);
    throw error;
  }
}
