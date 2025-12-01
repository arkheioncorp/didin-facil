import type { ScraperConfig, ScraperStatus } from "@/types";

// Check if running in Tauri environment
const isTauri = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
};

// Safe invoke wrapper for Tauri commands
async function safeInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (isTauri()) {
    const { invoke } = await import("@tauri-apps/api/core");
    return invoke<T>(cmd, args);
  }
  throw new Error(`Tauri command "${cmd}" not available in browser mode`);
}

// API base URL for browser mode - usa VITE_API_URL do .env
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Default scraper status for browser mode
const defaultScraperStatus: ScraperStatus = {
  isRunning: false,
  productsFound: 0,
  progress: 0,
  currentProduct: null,
  errors: [],
  startedAt: null,
  statusMessage: "Pronto para iniciar",
  logs: []
};

export async function startScraper(config: ScraperConfig): Promise<ScraperStatus> {
  try {
    if (isTauri()) {
      return await safeInvoke<ScraperStatus>("scrape_tiktok_shop", { config });
    }
    
    // Browser mode: call backend API
    const response = await fetch(`${API_BASE_URL}/scraper/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
      },
      body: JSON.stringify(config)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Error starting scraper:", error);
    throw error;
  }
}

export async function getScraperStatus(): Promise<ScraperStatus> {
  try {
    if (isTauri()) {
      return await safeInvoke<ScraperStatus>("get_scraper_status");
    }
    
    // Browser mode: call backend API
    const response = await fetch(`${API_BASE_URL}/scraper/status`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
      }
    });
    
    if (!response.ok) {
      return defaultScraperStatus;
    }
    
    return await response.json();
  } catch (error) {
    console.error("Error getting scraper status:", error);
    return defaultScraperStatus;
  }
}

export async function stopScraper(): Promise<boolean> {
  try {
    if (isTauri()) {
      return await safeInvoke<boolean>("stop_scraper");
    }
    
    // Browser mode: call backend API
    const response = await fetch(`${API_BASE_URL}/scraper/stop`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
      }
    });
    
    return response.ok;
  } catch (error) {
    console.error("Error stopping scraper:", error);
    throw error;
  }
}

export async function testProxy(proxy: string): Promise<boolean> {
  try {
    if (isTauri()) {
      return await safeInvoke<boolean>("test_proxy", { proxy });
    }
    
    // Browser mode: call backend API
    const response = await fetch(`${API_BASE_URL}/scraper/test-proxy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
      },
      body: JSON.stringify({ proxy })
    });
    
    return response.ok;
  } catch (error) {
    console.error("Error testing proxy:", error);
    return false;
  }
}

export async function syncProducts(): Promise<number> {
  try {
    if (isTauri()) {
      return await safeInvoke<number>("sync_products");
    }
    
    // Browser mode: call backend API
    const response = await fetch(`${API_BASE_URL}/scraper/sync`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.count || 0;
  } catch (error) {
    console.error("Error syncing products:", error);
    throw error;
  }
}

export async function updateSelectors(selectors: string[]): Promise<void> {
  try {
    if (isTauri()) {
      await safeInvoke("update_selectors", { selectors });
      return;
    }
    
    // Browser mode: call backend API
    await fetch(`${API_BASE_URL}/scraper/selectors`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
      },
      body: JSON.stringify({ selectors })
    });
  } catch (error) {
    console.error("Error updating selectors:", error);
    throw error;
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function fetchJob(): Promise<any | null> {
  try {
    if (isTauri()) {
      return await safeInvoke("fetch_job");
    }
    
    // Browser mode: call backend API
    const response = await fetch(`${API_BASE_URL}/scraper/job`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
      }
    });
    
    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching job:", error);
    return null;
  }
}
