import type { Setting, AppSettings } from "@/types";

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

// Local storage key for browser mode
const SETTINGS_STORAGE_KEY = 'app_settings';

// Default settings for browser mode
const DEFAULT_APP_SETTINGS: Partial<AppSettings> = {
  setupComplete: false,
  termsAccepted: false,
  termsAcceptedAt: null,
  language: 'pt-BR',
  theme: 'system',
  notificationsEnabled: true,
  autoUpdate: true,
};

// Get settings from localStorage (browser mode)
function getLocalSettings(): Partial<AppSettings> {
  try {
    const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_APP_SETTINGS, ...JSON.parse(stored) };
    }
  } catch (e) {
    console.error("Error reading local settings:", e);
  }
  return DEFAULT_APP_SETTINGS;
}

// Save settings to localStorage (browser mode)
function saveLocalSettings(settings: Partial<AppSettings>): void {
  try {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  } catch (e) {
    console.error("Error saving local settings:", e);
  }
}

export async function saveSettings(settings: Record<string, string>): Promise<boolean> {
  try {
    if (!isTauri()) {
      const current = getLocalSettings();
      saveLocalSettings({ ...current, ...settings } as Partial<AppSettings>);
      return true;
    }
    return await safeInvoke<boolean>("save_settings", { settings });
  } catch (error) {
    console.error("Error saving settings:", error);
    return false;
  }
}

export async function getSettings(): Promise<Setting[]> {
  try {
    if (!isTauri()) {
      const settings = getLocalSettings();
      const now = new Date().toISOString();
      return Object.entries(settings).map(([key, value]) => ({
        key,
        value: String(value),
        category: 'general',
        updatedAt: now,
      }));
    }
    return await safeInvoke<Setting[]>("get_settings");
  } catch (error) {
    console.error("Error getting settings:", error);
    return [];
  }
}

/**
 * Get full app settings
 */
export async function getAppSettings(): Promise<AppSettings> {
  try {
    if (!isTauri()) {
      return getLocalSettings() as AppSettings;
    }
    return await safeInvoke<AppSettings>("get_settings");
  } catch (error) {
    console.error("Error getting app settings:", error);
    return DEFAULT_APP_SETTINGS as AppSettings;
  }
}

/**
 * Save full app settings
 */
export async function saveAppSettings(settings: AppSettings): Promise<void> {
  try {
    if (!isTauri()) {
      saveLocalSettings(settings);
      return;
    }
    await safeInvoke("save_settings", { settings });
  } catch (error) {
    console.error("Error saving app settings:", error);
    throw error;
  }
}

/**
 * Check if initial setup has been completed
 */
export async function isSetupComplete(): Promise<boolean> {
  try {
    const settings = await getAppSettings();
    return settings.setupComplete ?? false;
  } catch (error) {
    console.error("Error checking setup status:", error);
    return false;
  }
}

/**
 * Reset setup to force the wizard to run again
 * Useful for testing and support scenarios
 */
export async function resetSetup(): Promise<void> {
  try {
    const settings = await getAppSettings();
    const resetSettings: AppSettings = {
      ...settings,
      setupComplete: false,
      termsAccepted: false,
      termsAcceptedAt: null,
    };
    await saveAppSettings(resetSettings);
    // Also clear tutorial flag
    localStorage.removeItem('tutorial_completed');
  } catch (error) {
    console.error("Error resetting setup:", error);
    throw error;
  }
}
