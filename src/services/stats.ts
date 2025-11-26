import { invoke } from "@tauri-apps/api/core";
import type { DashboardStats } from "@/types";

export async function getUserStats(): Promise<DashboardStats> {
  try {
    return await invoke<DashboardStats>("get_user_stats");
  } catch (error) {
    console.error("Error getting user stats:", error);
    throw error;
  }
}
