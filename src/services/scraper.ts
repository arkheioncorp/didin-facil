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

export async function stopScraper(): Promise<boolean> {
  try {
    return await invoke<boolean>("stop_scraper");
  } catch (error) {
    console.error("Error stopping scraper:", error);
    throw error;
  }
}

export async function testProxy(proxy: string): Promise<boolean> {
  try {
    return await invoke<boolean>("test_proxy", { proxy });
  } catch (error) {
    console.error("Error testing proxy:", error);
    return false;
  }
}

export async function syncProducts(): Promise<number> {
  try {
    return await invoke<number>("sync_products");
  } catch (error) {
    console.error("Error syncing products:", error);
    throw error;
  }
}

export async function updateSelectors(selectors: string[]): Promise<void> {
  try {
    await invoke("update_selectors", { selectors });
  } catch (error) {
    console.error("Error updating selectors:", error);
    throw error;
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function fetchJob(): Promise<any | null> {
  try {
    return await invoke("fetch_job");
  } catch (error) {
    console.error("Error fetching job:", error);
    return null;
  }
}
