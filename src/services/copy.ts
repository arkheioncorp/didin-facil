import { invoke } from "@tauri-apps/api/core";
import type { CopyHistory, CopyRequest, CopyResponse } from "@/types";

export async function generateCopy(request: CopyRequest): Promise<CopyResponse> {
  try {
    return await invoke<CopyResponse>("generate_copy", { request });
  } catch (error) {
    console.error("Error generating copy:", error);
    throw error;
  }
}

export async function getCopyHistory(limit = 50): Promise<CopyHistory[]> {
  try {
    return await invoke<CopyHistory[]>("get_copy_history", { limit });
  } catch (error) {
    console.error("Error getting copy history:", error);
    throw error;
  }
}
