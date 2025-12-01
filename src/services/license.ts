import { api } from "@/lib/api";
import type { License } from "@/types";

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

// Default invalid license for browser mode
const DEFAULT_LICENSE: License = {
  id: null,
  isValid: false,
  isLifetime: false,
  plan: 'free',
  activatedAt: null,
  expiresAt: null,
  maxDevices: 1,
  activeDevices: 0,
  currentDeviceId: null,
  isCurrentDeviceAuthorized: false,
};

export async function validateLicense(licenseKey: string): Promise<License> {
  try {
    // In Tauri, use native invoke
    if (isTauri()) {
      return await safeInvoke<License>("validate_license", { licenseKey });
    }
    
    // In browser, try HTTP API
    try {
      const response = await api.post<License>("/licenses/validate", {
        license_key: licenseKey,
      });
      return response.data;
    } catch (e) {
      console.info("[License] Running in browser mode with default license");
      return DEFAULT_LICENSE;
    }
  } catch (error) {
    console.error("Error validating license:", error);
    return DEFAULT_LICENSE;
  }
}
