/**
 * useNotifications Hook
 * ======================
 * Sistema de notificações push em tempo real para:
 * - Posts com falha (DLQ)
 * - Quota YouTube baixa
 * - WhatsApp desconectado
 */
import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from "react";
import { api } from "@/lib/api";

// Tipos de notificação
export type NotificationType = "dlq" | "quota" | "whatsapp" | "success" | "warning" | "error" | "info";

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionUrl?: string;
  actionLabel?: string;
  data?: Record<string, unknown>;
}

interface NotificationsState {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
}

interface NotificationsContextType extends NotificationsState {
  addNotification: (notification: Omit<Notification, "id" | "timestamp" | "read">) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  refreshAlerts: () => Promise<void>;
}

const NotificationsContext = createContext<NotificationsContextType | null>(null);

// Gera ID único
const generateId = () => `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// Provider
export function NotificationsProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Unread count
  const unreadCount = notifications.filter((n) => !n.read).length;

  // Adiciona notificação
  const addNotification = useCallback(
    (notification: Omit<Notification, "id" | "timestamp" | "read">) => {
      const newNotif: Notification = {
        ...notification,
        id: generateId(),
        timestamp: new Date(),
        read: false,
      };

      setNotifications((prev) => {
        // Evita duplicatas por tipo + message
        const isDuplicate = prev.some(
          (n) => n.type === notification.type && n.message === notification.message && !n.read
        );
        if (isDuplicate) return prev;

        return [newNotif, ...prev].slice(0, 50); // Max 50 notificações
      });

      // Browser notification se permitido
      if (Notification.permission === "granted") {
        new Notification(newNotif.title, {
          body: newNotif.message,
          icon: "/favicon.ico",
          tag: newNotif.id,
        });
      }
    },
    []
  );

  // Marca como lida
  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  }, []);

  // Marca todas como lidas
  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  // Remove notificação
  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  // Limpa todas
  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Busca alertas do backend
  const refreshAlerts = useCallback(async () => {
    setIsLoading(true);
    try {
      // Fetch DLQ stats
      const dlqResponse = await api.get<{ total: number }>("/scheduler/dlq/stats").catch(() => null);
      if (dlqResponse?.data?.total && dlqResponse.data.total > 0) {
        addNotification({
          type: "dlq",
          title: "Posts com Falha",
          message: `${dlqResponse.data.total} post(s) aguardando revisão na Dead Letter Queue`,
          actionUrl: "/automation/dlq",
          actionLabel: "Ver DLQ",
        });
      }

      // Fetch YouTube quota
      const quotaResponse = await api
        .get<{ quota: { percentage: number; used: number; limit: number } }>("/youtube/quota")
        .catch(() => null);
      if (quotaResponse?.data?.quota) {
        const { percentage, used, limit } = quotaResponse.data.quota;
        if (percentage >= 90) {
          addNotification({
            type: "quota",
            title: "Quota YouTube Crítica",
            message: `${percentage.toFixed(1)}% usado (${used.toLocaleString()}/${limit.toLocaleString()})`,
            actionUrl: "/social/youtube",
            actionLabel: "Ver Quota",
          });
        } else if (percentage >= 75) {
          addNotification({
            type: "quota",
            title: "Quota YouTube Alta",
            message: `${percentage.toFixed(1)}% usado. Considere pausar uploads.`,
            actionUrl: "/social/youtube",
            actionLabel: "Ver Quota",
          });
        }
      }

      // Fetch WhatsApp status
      const waResponse = await api
        .get<{ status: string }>("/whatsapp/status")
        .catch(() => null);
      if (waResponse?.data?.status && waResponse.data.status !== "connected") {
        addNotification({
          type: "whatsapp",
          title: "WhatsApp Desconectado",
          message: "Sua sessão do WhatsApp foi desconectada. Reconecte para continuar enviando mensagens.",
          actionUrl: "/whatsapp",
          actionLabel: "Reconectar",
        });
      }
    } catch (error) {
      console.error("Error fetching alerts:", error);
    } finally {
      setIsLoading(false);
    }
  }, [addNotification]);

  // Fetch inicial e polling
  useEffect(() => {
    // Solicita permissão para notificações do browser
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }

    // Fetch inicial
    refreshAlerts();

    // Polling a cada 2 minutos
    const interval = setInterval(refreshAlerts, 2 * 60 * 1000);
    return () => clearInterval(interval);
  }, [refreshAlerts]);

  return (
    <NotificationsContext.Provider
      value={{
        notifications,
        unreadCount,
        isLoading,
        addNotification,
        markAsRead,
        markAllAsRead,
        removeNotification,
        clearAll,
        refreshAlerts,
      }}
    >
      {children}
    </NotificationsContext.Provider>
  );
}

// Hook
export function useNotifications() {
  const context = useContext(NotificationsContext);
  if (!context) {
    throw new Error("useNotifications must be used within NotificationsProvider");
  }
  return context;
}

// Tipo de ícone por notificação
export function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case "dlq":
      return "AlertTriangle";
    case "quota":
      return "BarChart3";
    case "whatsapp":
      return "MessageCircle";
    case "success":
      return "CheckCircle2";
    case "warning":
      return "AlertCircle";
    case "error":
      return "XCircle";
    default:
      return "Bell";
  }
}

// Cor por tipo
export function getNotificationColor(type: NotificationType) {
  switch (type) {
    case "dlq":
    case "error":
      return "text-red-500";
    case "quota":
    case "warning":
      return "text-yellow-500";
    case "whatsapp":
      return "text-green-500";
    case "success":
      return "text-green-500";
    default:
      return "text-blue-500";
  }
}
