import { api } from "@/lib/api";

export interface WhatsAppStatus {
    instance_name: string;
    status: "connected" | "disconnected" | "connecting" | "awaiting_scan" | "error" | "unknown";
    qr_code?: string;
    reconnection?: {
        attempts: number;
        instance_name: string;
    };
    updated_at?: string;
}

export const whatsappService = {
    /**
     * Create a new WhatsApp instance
     */
    async createInstance(instanceName: string, webhookUrl?: string) {
        return api.post("/whatsapp/instances", {
            instance_name: instanceName,
            webhook_url: webhookUrl,
        });
    },

    /**
     * Get QR Code for instance
     */
    async getQrCode(instanceName: string) {
        return api.get<{ base64: string }>(`/whatsapp/instances/${instanceName}/qrcode`);
    },

    /**
     * Get real-time status of instance
     */
    async getStatus(instanceName: string) {
        return api.get<WhatsAppStatus>(`/whatsapp/instances/${instanceName}/status`);
    },

    /**
     * Force reconnection attempt
     */
    async reconnect(instanceName: string) {
        return api.post(`/whatsapp/instances/${instanceName}/reconnect`);
    },
};
