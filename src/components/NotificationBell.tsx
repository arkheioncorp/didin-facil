/**
 * NotificationBell Component
 * ==========================
 * Sino de notificações para o header com dropdown de alertas
 */
import React from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  useNotifications,
  Notification,
  getNotificationColor,
} from "@/hooks/use-notifications";
import { formatDistanceToNow } from "date-fns";
import { ptBR } from "date-fns/locale";
import {
  Bell,
  AlertTriangle,
  BarChart3,
  MessageCircle,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Loader2,
  Trash2,
  Check,
  ExternalLink,
} from "lucide-react";

// Mapeia tipo para ícone
function NotificationIcon({ type }: { type: string }) {
  const className = `h-4 w-4 ${getNotificationColor(type as never)}`;

  switch (type) {
    case "dlq":
      return <AlertTriangle className={className} />;
    case "quota":
      return <BarChart3 className={className} />;
    case "whatsapp":
      return <MessageCircle className={className} />;
    case "success":
      return <CheckCircle2 className={className} />;
    case "warning":
      return <AlertCircle className={className} />;
    case "error":
      return <XCircle className={className} />;
    default:
      return <Bell className={className} />;
  }
}

// Item de notificação
function NotificationItem({
  notification,
  onMarkRead,
  onRemove,
}: {
  notification: Notification;
  onMarkRead: (id: string) => void;
  onRemove: (id: string) => void;
}) {
  return (
    <div
      className={`p-3 hover:bg-accent rounded-md transition-colors ${
        notification.read ? "opacity-60" : ""
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5">
          <NotificationIcon type={notification.type} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <p className="font-medium text-sm truncate">{notification.title}</p>
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {formatDistanceToNow(notification.timestamp, {
                locale: ptBR,
                addSuffix: true,
              })}
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5 line-clamp-2">
            {notification.message}
          </p>
          <div className="flex items-center gap-2 mt-2">
            {notification.actionUrl && (
              <Link to={notification.actionUrl}>
                <Button variant="outline" size="sm" className="h-7 text-xs">
                  <ExternalLink className="h-3 w-3 mr-1" />
                  {notification.actionLabel || "Ver"}
                </Button>
              </Link>
            )}
            {!notification.read && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs"
                onClick={() => onMarkRead(notification.id)}
              >
                <Check className="h-3 w-3 mr-1" />
                Marcar lida
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs text-destructive hover:text-destructive"
              onClick={() => onRemove(notification.id)}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Componente principal
export function NotificationBell() {
  const {
    notifications,
    unreadCount,
    isLoading,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll,
    refreshAlerts,
  } = useNotifications();

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center text-xs"
            >
              {unreadCount > 9 ? "9+" : unreadCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96 p-0" align="end">
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold">Notificações</h4>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs"
                onClick={refreshAlerts}
                disabled={isLoading}
              >
                {isLoading ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  "Atualizar"
                )}
              </Button>
              {notifications.length > 0 && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs"
                    onClick={markAllAsRead}
                  >
                    Marcar todas
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs text-destructive hover:text-destructive"
                    onClick={clearAll}
                  >
                    Limpar
                  </Button>
                </>
              )}
            </div>
          </div>
          {unreadCount > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              {unreadCount} não lida{unreadCount > 1 ? "s" : ""}
            </p>
          )}
        </div>

        {/* Lista de notificações */}
        <ScrollArea className="h-[400px]">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Bell className="h-10 w-10 mb-3 opacity-50" />
              <p className="font-medium">Nenhuma notificação</p>
              <p className="text-xs">Você está em dia!</p>
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {notifications.map((notification) => (
                <React.Fragment key={notification.id}>
                  <NotificationItem
                    notification={notification}
                    onMarkRead={markAsRead}
                    onRemove={removeNotification}
                  />
                  <Separator className="my-1" />
                </React.Fragment>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Footer com links rápidos */}
        <div className="p-3 border-t bg-muted/50">
          <div className="flex items-center justify-around text-xs">
            <Link
              to="/automation/dlq"
              className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
            >
              <AlertTriangle className="h-3 w-3" />
              Ver DLQ
            </Link>
            <Link
              to="/social/youtube"
              className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
            >
              <BarChart3 className="h-3 w-3" />
              Quota YouTube
            </Link>
            <Link
              to="/whatsapp"
              className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
            >
              <MessageCircle className="h-3 w-3" />
              WhatsApp
            </Link>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

export default NotificationBell;
