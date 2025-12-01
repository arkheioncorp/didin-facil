import * as React from "react";
import { useFavoriteActionsStore, useFavoriteAction, type FavoriteActionId } from "@/stores";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { 
  Star, 
  StarOff, 
  Sparkles,
  Calendar,
  MessageCircle,
  Instagram,
  Youtube,
  Copy,
  ExternalLink,
  Download,
  Bot,
  Mail,
  ShoppingCart,
} from "lucide-react";

// ============================================
// ICON MAP
// ============================================

const ACTION_ICONS: Record<FavoriteActionId, React.ReactNode> = {
  "copy-info": <Copy className="h-4 w-4" />,
  "copy-link": <ExternalLink className="h-4 w-4" />,
  "generate-copy": <Sparkles className="h-4 w-4" />,
  "whatsapp": <MessageCircle className="h-4 w-4" />,
  "schedule": <Calendar className="h-4 w-4" />,
  "instagram": <Instagram className="h-4 w-4" />,
  "tiktok": (
    <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current">
      <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
    </svg>
  ),
  "youtube": <Youtube className="h-4 w-4" />,
  "seller-bot": <Bot className="h-4 w-4" />,
  "crm": <ShoppingCart className="h-4 w-4" />,
  "email": <Mail className="h-4 w-4" />,
  "export": <Download className="h-4 w-4" />,
};

// ============================================
// FAVORITE BUTTON COMPONENT
// ============================================

interface FavoriteActionButtonProps {
  actionId: FavoriteActionId;
  size?: "sm" | "default" | "icon";
  showLabel?: boolean;
  className?: string;
}

export const FavoriteActionButton: React.FC<FavoriteActionButtonProps> = ({
  actionId,
  size = "icon",
  showLabel = false,
  className,
}) => {
  const { isFavorite, toggle, label } = useFavoriteAction(actionId);
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size={size}
            onClick={(e) => {
              e.stopPropagation();
              toggle();
            }}
            className={cn(
              "transition-colors",
              isFavorite && "text-yellow-500 hover:text-yellow-600",
              className
            )}
          >
            {isFavorite ? (
              <Star className="h-4 w-4 fill-current" />
            ) : (
              <StarOff className="h-4 w-4" />
            )}
            {showLabel && <span className="ml-1">{isFavorite ? "Favorito" : "Favoritar"}</span>}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>{isFavorite ? `Remover "${label}" dos favoritos` : `Adicionar "${label}" aos favoritos`}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

// ============================================
// FAVORITES LIST COMPONENT
// ============================================

interface FavoriteActionsListProps {
  onActionClick: (actionId: FavoriteActionId) => void;
  maxItems?: number;
  showEmpty?: boolean;
  compact?: boolean;
}

export const FavoriteActionsList: React.FC<FavoriteActionsListProps> = ({
  onActionClick,
  maxItems = 5,
  showEmpty = true,
  compact = false,
}) => {
  const { favorites, getMostUsed, incrementUsage } = useFavoriteActionsStore();
  
  // Show most used favorites first - favorites.length forces recalculation
  const sortedFavorites = React.useMemo(() => {
    return getMostUsed(maxItems);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getMostUsed, maxItems, favorites.length]);
  
  const handleClick = (actionId: FavoriteActionId) => {
    incrementUsage(actionId);
    onActionClick(actionId);
  };
  
  if (sortedFavorites.length === 0) {
    if (!showEmpty) return null;
    
    return (
      <div className="flex flex-col items-center justify-center py-4 text-muted-foreground">
        <Star className="h-6 w-6 mb-2 opacity-50" />
        <p className="text-sm">Nenhuma ação favorita</p>
        <p className="text-xs">Clique na estrela para favoritar ações</p>
      </div>
    );
  }
  
  if (compact) {
    return (
      <div className="flex flex-wrap gap-2">
        {sortedFavorites.map((fav) => (
          <TooltipProvider key={fav.id}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => handleClick(fav.id)}
                >
                  {ACTION_ICONS[fav.id]}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{fav.label}</p>
                {fav.usageCount > 0 && (
                  <p className="text-xs text-muted-foreground">Usado {fav.usageCount}x</p>
                )}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ))}
      </div>
    );
  }
  
  return (
    <div className="space-y-2">
      {sortedFavorites.map((fav) => (
        <button
          key={fav.id}
          onClick={() => handleClick(fav.id)}
          className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-muted/50 transition-colors text-left"
        >
          <div className="p-1.5 rounded bg-yellow-500/10 text-yellow-600">
            {ACTION_ICONS[fav.id]}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{fav.label}</p>
          </div>
          {fav.usageCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {fav.usageCount}x
            </Badge>
          )}
        </button>
      ))}
    </div>
  );
};

// ============================================
// FAVORITES QUICK ACCESS
// ============================================

interface FavoriteActionsQuickAccessProps {
  onActionClick: (actionId: FavoriteActionId) => void;
}

export const FavoriteActionsQuickAccess: React.FC<FavoriteActionsQuickAccessProps> = ({
  onActionClick,
}) => {
  const { favorites } = useFavoriteActionsStore();
  
  if (favorites.length === 0) return null;
  
  return (
    <div className="p-3 rounded-lg bg-yellow-500/5 border border-yellow-500/20 space-y-2">
      <div className="flex items-center gap-2 text-sm font-medium text-yellow-600">
        <Star className="h-4 w-4 fill-current" />
        <span>Ações Favoritas</span>
      </div>
      <FavoriteActionsList 
        onActionClick={onActionClick} 
        maxItems={4}
        showEmpty={false}
        compact 
      />
    </div>
  );
};

export default FavoriteActionsList;
