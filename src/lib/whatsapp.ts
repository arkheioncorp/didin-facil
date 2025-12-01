/**
 * WhatsApp Service
 * Integration with Evolution API and Backend
 */

import { 
  EVOLUTION_API_URL, 
  EVOLUTION_API_KEY, 
  EVOLUTION_INSTANCE 
} from "./constants";

// Types
export interface InstanceInfo {
  instanceName: string;
  instanceId: string;
  owner: string | null;
  profileName: string;
  profilePictureUrl: string | null;
  status: "open" | "close" | "connecting";
  phone?: string;
  chatwoot?: {
    enabled: boolean;
    account_id: string;
    url: string;
  };
}

export interface ConnectionState {
  instance: {
    instanceName: string;
    state: "open" | "close" | "connecting";
  };
}

export interface QRCodeResponse {
  pairingCode?: string;
  code?: string;
  base64?: string;
  count?: number;
}

export interface MessageSent {
  key: {
    remoteJid: string;
    fromMe: boolean;
    id: string;
  };
  message: {
    extendedTextMessage?: {
      text: string;
    };
  };
  messageTimestamp: string;
  status: string;
}

export interface Contact {
  id: string;
  pushName?: string;
  profilePictureUrl?: string;
  owner?: string;
}

export interface ChatMessage {
  key: {
    remoteJid: string;
    fromMe: boolean;
    id: string;
    participant?: string;
  };
  pushName?: string;
  message?: {
    conversation?: string;
    extendedTextMessage?: {
      text: string;
    };
    imageMessage?: {
      caption?: string;
      url?: string;
    };
    audioMessage?: {
      url?: string;
    };
    documentMessage?: {
      fileName?: string;
      url?: string;
    };
  };
  messageTimestamp?: number;
  messageType?: string;
}

// WhatsApp Service Class
class WhatsAppService {
  private baseURL: string;
  private apiKey: string;
  private instanceName: string;

  constructor() {
    this.baseURL = EVOLUTION_API_URL;
    this.apiKey = EVOLUTION_API_KEY;
    this.instanceName = EVOLUTION_INSTANCE;
  }

  private async request<T>(
    method: string,
    endpoint: string,
    data?: unknown
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        "apikey": this.apiKey,
      },
      body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: "Unknown error" }));
      throw new Error(error.message || error.error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Instance Management
  async getConnectionState(): Promise<ConnectionState> {
    return this.request<ConnectionState>(
      "GET",
      `/instance/connectionState/${this.instanceName}`
    );
  }

  async fetchInstances(): Promise<{ instance: InstanceInfo }[]> {
    return this.request<{ instance: InstanceInfo }[]>(
      "GET",
      "/instance/fetchInstances"
    );
  }

  async getCurrentInstance(): Promise<InstanceInfo | null> {
    const instances = await this.fetchInstances();
    const current = instances.find(
      (i) => i.instance.instanceName === this.instanceName
    );
    return current?.instance || null;
  }

  async createInstance(name?: string): Promise<{ instance: InstanceInfo; qrcode: QRCodeResponse }> {
    const instanceName = name || this.instanceName;
    return this.request(
      "POST",
      "/instance/create",
      {
        instanceName,
        qrcode: true,
        integration: "WHATSAPP-BAILEYS",
      }
    );
  }

  async connectInstance(): Promise<QRCodeResponse> {
    return this.request<QRCodeResponse>(
      "GET",
      `/instance/connect/${this.instanceName}`
    );
  }

  async disconnectInstance(): Promise<{ status: string }> {
    return this.request(
      "DELETE",
      `/instance/logout/${this.instanceName}`
    );
  }

  async deleteInstance(): Promise<{ status: string }> {
    return this.request(
      "DELETE",
      `/instance/delete/${this.instanceName}`
    );
  }

  async restartInstance(): Promise<{ status: string }> {
    return this.request(
      "PUT",
      `/instance/restart/${this.instanceName}`
    );
  }

  // Messaging
  async sendText(to: string, text: string): Promise<MessageSent> {
    // Format phone number - remove non-digits
    const phone = to.replace(/\D/g, "");
    
    return this.request(
      "POST",
      `/message/sendText/${this.instanceName}`,
      {
        number: phone,
        textMessage: { text },
      }
    );
  }

  async sendImage(
    to: string,
    imageUrl: string,
    caption?: string
  ): Promise<MessageSent> {
    const phone = to.replace(/\D/g, "");
    
    return this.request(
      "POST",
      `/message/sendMedia/${this.instanceName}`,
      {
        number: phone,
        mediaMessage: {
          mediatype: "image",
          media: imageUrl,
          caption,
        },
      }
    );
  }

  async sendDocument(
    to: string,
    documentUrl: string,
    fileName: string
  ): Promise<MessageSent> {
    const phone = to.replace(/\D/g, "");
    
    return this.request(
      "POST",
      `/message/sendMedia/${this.instanceName}`,
      {
        number: phone,
        mediaMessage: {
          mediatype: "document",
          media: documentUrl,
          fileName,
        },
      }
    );
  }

  async sendButtons(
    to: string,
    title: string,
    description: string,
    buttons: Array<{ buttonId: string; buttonText: { displayText: string } }>,
    footer?: string
  ): Promise<MessageSent> {
    const phone = to.replace(/\D/g, "");
    
    return this.request(
      "POST",
      `/message/sendButtons/${this.instanceName}`,
      {
        number: phone,
        buttonMessage: {
          title,
          description,
          footerText: footer,
          buttons,
        },
      }
    );
  }

  async sendList(
    to: string,
    title: string,
    description: string,
    buttonText: string,
    sections: Array<{
      title: string;
      rows: Array<{
        title: string;
        description?: string;
        rowId: string;
      }>;
    }>,
    footer?: string
  ): Promise<MessageSent> {
    const phone = to.replace(/\D/g, "");
    
    return this.request(
      "POST",
      `/message/sendList/${this.instanceName}`,
      {
        number: phone,
        listMessage: {
          title,
          description,
          footerText: footer,
          buttonText,
          sections,
        },
      }
    );
  }

  // Contacts
  async fetchContacts(): Promise<Contact[]> {
    return this.request<Contact[]>(
      "POST",
      `/chat/fetchContacts/${this.instanceName}`,
      {}
    );
  }

  async checkNumber(phone: string): Promise<{ exists: boolean; jid?: string }> {
    const number = phone.replace(/\D/g, "");
    
    const result = await this.request<Array<{ exists: boolean; jid: string }>>(
      "POST",
      `/chat/whatsappNumbers/${this.instanceName}`,
      { numbers: [number] }
    );
    
    return result[0] || { exists: false };
  }

  // Messages History
  async fetchMessages(
    remoteJid: string,
    limit = 50
  ): Promise<{ messages: ChatMessage[] }> {
    return this.request(
      "POST",
      `/chat/fetchMessages/${this.instanceName}`,
      {
        where: {
          key: {
            remoteJid: remoteJid.includes("@") ? remoteJid : `${remoteJid}@s.whatsapp.net`,
          },
        },
        limit,
      }
    );
  }

  // Profile
  async getProfilePicture(phone: string): Promise<{ profilePictureUrl?: string }> {
    const number = phone.replace(/\D/g, "");
    
    return this.request(
      "POST",
      `/chat/fetchProfilePictureUrl/${this.instanceName}`,
      {
        number,
      }
    );
  }

  // Utility
  formatJidToPhone(jid: string): string {
    return jid.split("@")[0];
  }

  formatPhoneToJid(phone: string): string {
    const cleaned = phone.replace(/\D/g, "");
    return `${cleaned}@s.whatsapp.net`;
  }

  isGroupJid(jid: string): boolean {
    return jid.includes("@g.us");
  }

  // Get Message Text from any message type
  getMessageText(message: ChatMessage["message"]): string {
    if (!message) return "";
    
    if (message.conversation) return message.conversation;
    if (message.extendedTextMessage?.text) return message.extendedTextMessage.text;
    if (message.imageMessage?.caption) return `📷 ${message.imageMessage.caption}`;
    if (message.imageMessage) return "📷 Imagem";
    if (message.audioMessage) return "🎵 Áudio";
    if (message.documentMessage?.fileName) return `📄 ${message.documentMessage.fileName}`;
    if (message.documentMessage) return "📄 Documento";
    
    return "";
  }

  // Set instance name (for multi-instance support)
  setInstance(instanceName: string) {
    this.instanceName = instanceName;
  }

  getInstanceName(): string {
    return this.instanceName;
  }
}

// Export singleton
export const whatsappService = new WhatsAppService();
