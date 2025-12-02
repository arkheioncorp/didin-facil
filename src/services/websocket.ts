/**
 * WebSocket Service
 * =================
 * Serviço de notificações em tempo real via WebSocket
 * - Notificações de publicações
 * - Status de contas
 * - Alertas de erros
 * - Atualizações de métricas
 */

// ==================== Types ====================

export type NotificationType =
  | "post_published"
  | "post_failed"
  | "post_scheduled"
  | "account_connected"
  | "account_disconnected"
  | "account_expired"
  | "challenge_required"
  | "quota_warning"
  | "error"
  | "info"
  // Bot automation notifications
  | "bot_task_started"
  | "bot_task_completed"
  | "bot_task_failed"
  | "bot_task_progress"
  | "bot_stats_update"
  | "bot_screenshot"
  | "bot_worker_started"
  | "bot_worker_stopped";

export interface WebSocketNotification {
  id: string;
  type: NotificationType;
  platform?: "instagram" | "tiktok" | "youtube" | "whatsapp";
  title: string;
  message: string;
  timestamp: string;
  data?: Record<string, unknown>;
  read: boolean;
}

export interface WebSocketMessage {
  event: string;
  data: unknown;
  timestamp: string;
}

type EventCallback = (data: unknown) => void;

// ==================== WebSocket Service ====================

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private eventListeners: Map<string, Set<EventCallback>> = new Map();
  private pendingMessages: WebSocketMessage[] = [];
  private isConnecting = false;
  private _isConnected = false;

  constructor() {
    // Get WebSocket URL from environment or derive from API URL
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    const wsProtocol = apiUrl.startsWith("https") ? "wss" : "ws";
    const wsHost = apiUrl.replace(/^https?:\/\//, "");
    this.url = `${wsProtocol}://${wsHost}/ws/notifications`;
  }

  // ==================== Connection Management ====================

  connect(token?: string): void {
    if (this.isConnecting || this._isConnected) {
      console.log("[WS] Already connected or connecting");
      return;
    }

    this.isConnecting = true;

    try {
      const url = token ? `${this.url}?token=${token}` : this.url;
      this.ws = new WebSocket(url);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
    } catch (error) {
      console.error("[WS] Connection error:", error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    this.clearTimers();
    this.reconnectAttempts = 0;
    
    if (this.ws) {
      this.ws.onclose = null; // Prevent reconnect
      this.ws.close();
      this.ws = null;
    }
    
    this._isConnected = false;
    this.isConnecting = false;
    this.emit("disconnected", {});
  }

  get isConnected(): boolean {
    return this._isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  // ==================== Event Handlers ====================

  private handleOpen(): void {
    console.log("[WS] Connected to notification server");
    this._isConnected = true;
    this.isConnecting = false;
    this.reconnectAttempts = 0;

    // Start heartbeat
    this.startHeartbeat();

    // Send pending messages
    this.flushPendingMessages();

    // Emit connection event
    this.emit("connected", {});
  }

  private handleClose(event: CloseEvent): void {
    console.log("[WS] Connection closed:", event.code, event.reason);
    this._isConnected = false;
    this.isConnecting = false;
    this.clearTimers();

    // Emit disconnection event
    this.emit("disconnected", { code: event.code, reason: event.reason });

    // Attempt reconnect if not intentional
    if (event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  private handleError(event: Event): void {
    console.error("[WS] WebSocket error:", event);
    this.emit("error", { error: event });
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // Handle ping/pong
      if (message.event === "ping") {
        this.send({ event: "pong", data: {}, timestamp: new Date().toISOString() });
        return;
      }

      // Emit event to listeners
      this.emit(message.event, message.data);
      
      // Also emit to generic "message" handler
      this.emit("message", message);

    } catch (error) {
      console.error("[WS] Failed to parse message:", error);
    }
  }

  // ==================== Heartbeat ====================

  private startHeartbeat(): void {
    this.clearHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send({ event: "ping", data: {}, timestamp: new Date().toISOString() });
      }
    }, 30000); // Ping every 30 seconds
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  // ==================== Reconnection ====================

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("[WS] Max reconnection attempts reached");
      this.emit("reconnect_failed", { attempts: this.reconnectAttempts });
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    this.reconnectTimer = setTimeout(() => {
      this.emit("reconnecting", { attempt: this.reconnectAttempts });
      this.connect();
    }, delay);
  }

  private clearTimers(): void {
    this.clearHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // ==================== Message Sending ====================

  send(message: WebSocketMessage): void {
    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message for later
      this.pendingMessages.push(message);
    }
  }

  private flushPendingMessages(): void {
    while (this.pendingMessages.length > 0 && this.isConnected) {
      const message = this.pendingMessages.shift();
      if (message && this.ws) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  // ==================== Event Emitter ====================

  on(event: string, callback: EventCallback): () => void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event)!.add(callback);

    // Return unsubscribe function
    return () => {
      this.off(event, callback);
    };
  }

  off(event: string, callback: EventCallback): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.delete(callback);
    }
  }

  private emit(event: string, data: unknown): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[WS] Error in event listener for "${event}":`, error);
        }
      });
    }
  }

  // ==================== Convenience Methods ====================

  /**
   * Subscribe to notification events
   */
  onNotification(callback: (notification: WebSocketNotification) => void): () => void {
    return this.on("notification", callback as EventCallback);
  }

  /**
   * Subscribe to post status updates
   */
  onPostUpdate(callback: (data: { postId: string; status: string; platform: string }) => void): () => void {
    return this.on("post_update", callback as EventCallback);
  }

  /**
   * Subscribe to account status changes
   */
  onAccountUpdate(callback: (data: { platform: string; status: string; accountName: string }) => void): () => void {
    return this.on("account_update", callback as EventCallback);
  }

  /**
   * Subscribe to scheduler updates
   */
  onSchedulerUpdate(callback: (data: { action: string; postId?: string }) => void): () => void {
    return this.on("scheduler_update", callback as EventCallback);
  }

  /**
   * Mark notification as read
   */
  markAsRead(notificationId: string): void {
    this.send({
      event: "mark_read",
      data: { notificationId },
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Subscribe to specific platform updates
   */
  subscribeToPlatform(platform: string): void {
    this.send({
      event: "subscribe",
      data: { platform },
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Unsubscribe from platform updates
   */
  unsubscribeFromPlatform(platform: string): void {
    this.send({
      event: "unsubscribe",
      data: { platform },
      timestamp: new Date().toISOString(),
    });
  }
}

// ==================== Singleton Instance ====================

export const websocketService = new WebSocketService();

// ==================== React Hook ====================

import { useEffect, useState, useCallback } from "react";

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  token?: string;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  notifications: WebSocketNotification[];
  unreadCount: number;
  connect: () => void;
  disconnect: () => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearNotifications: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { autoConnect = true, token } = options;
  const [isConnected, setIsConnected] = useState(websocketService.isConnected);
  const [notifications, setNotifications] = useState<WebSocketNotification[]>([]);

  useEffect(() => {
    // Event handlers
    const handleConnected = () => setIsConnected(true);
    const handleDisconnected = () => setIsConnected(false);
    const handleNotification = (data: unknown) => {
      const notification = data as WebSocketNotification;
      setNotifications((prev) => [notification, ...prev].slice(0, 100)); // Keep last 100
    };

    // Subscribe to events
    const unsubConnected = websocketService.on("connected", handleConnected);
    const unsubDisconnected = websocketService.on("disconnected", handleDisconnected);
    const unsubNotification = websocketService.on("notification", handleNotification);

    // Auto connect
    if (autoConnect && !websocketService.isConnected) {
      websocketService.connect(token);
    }

    return () => {
      unsubConnected();
      unsubDisconnected();
      unsubNotification();
    };
  }, [autoConnect, token]);

  const connect = useCallback(() => {
    websocketService.connect(token);
  }, [token]);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  const markAsRead = useCallback((id: string) => {
    websocketService.markAsRead(id);
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    websocketService.send({
      event: "mark_all_read",
      data: {},
      timestamp: new Date().toISOString(),
    });
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return {
    isConnected,
    notifications,
    unreadCount,
    connect,
    disconnect,
    markAsRead,
    markAllAsRead,
    clearNotifications,
  };
}

export default websocketService;
