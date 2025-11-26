import { invoke } from "@tauri-apps/api/core";
import type { License } from "@/types";

export async function validateLicense(licenseKey: string): Promise<License> {
  try {
    return await invoke<License>("validate_license", { licenseKey });
  } catch (error) {
    console.error("Error validating license:", error);
    throw error;
  }
}
