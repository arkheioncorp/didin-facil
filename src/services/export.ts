type ExportFormat = "csv" | "json" | "xlsx";

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

export async function exportProducts(
  productIds: string[],
  format: ExportFormat
): Promise<string> {
  try {
    // In browser, use blob download
    if (!isTauri()) {
      console.info("[Export] Running in browser mode, using blob download");
      // Create a mock export for browser - in real app, call API
      const blob = new Blob(
        [JSON.stringify({ productIds, format, timestamp: new Date().toISOString() })],
        { type: format === 'json' ? 'application/json' : 'text/csv' }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `export.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      return `browser-export.${format}`;
    }

    // In Tauri, use native dialog
    const { save } = await import("@tauri-apps/plugin-dialog");
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

    return await safeInvoke<string>("export_products", { productIds, format, path });
  } catch (error) {
    console.error("Error exporting products:", error);
    throw error;
  }
}
