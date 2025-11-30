import { invoke } from "@tauri-apps/api/core";
import type { Setting, AppSettings } from "@/types";

export async function saveSettings(settings: Record<string, string>): Promise<boolean> {
  try {
    return await invoke<boolean>("save_settings", { settings });
  } catch (error) {
    console.error("Error saving settings:", error);
    throw error;
  }
}

export async function getSettings(): Promise<Setting[]> {
  try {
    return await invoke<Setting[]>("get_settings");
  } catch (error) {
    console.error("Error getting settings:", error);
    throw error;
  }
}

/**
 * Get full app settings
 */
export async function getAppSettings(): Promise<AppSettings> {
  try {
    return await invoke<AppSettings>("get_settings");
  } catch (error) {
    console.error("Error getting app settings:", error);
    throw error;
  }
}

/**
 * Save full app settings
 */
export async function saveAppSettings(settings: AppSettings): Promise<void> {
  try {
    await invoke("save_settings", { settings });
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
