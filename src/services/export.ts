import { invoke } from "@tauri-apps/api/core";
import { save } from "@tauri-apps/plugin-dialog";

type ExportFormat = "csv" | "json" | "xlsx";

export async function exportProducts(
  productIds: string[],
  format: ExportFormat
): Promise<string> {
  try {
    const path = await save({
      filters: [
        {
          name: format.toUpperCase(),
          extensions: [format],
        },
      ],
    });

    if (!path) {
      return "";
    }

    return await invoke<string>("export_products", { productIds, format, path });
  } catch (error) {
    console.error("Error exporting products:", error);
    throw error;
  }
}
