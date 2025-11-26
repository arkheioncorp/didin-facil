import { invoke } from "@tauri-apps/api/core";
import type { Setting } from "@/types";

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
