import * as React from "react";
import { cn } from "@/lib/utils";
import { Heart, MessageCircle, Send, Bookmark, MoreHorizontal, Music, Share2, ThumbsUp, ThumbsDown, Eye, Clock } from "lucide-react";

// ============================================
// INSTAGRAM PREVIEW
// ============================================

interface InstagramPreviewProps {
  imageUrl: string;
  caption: string;
  hashtags?: string;
  username?: string;
  profilePic?: string;
  likes?: number;
  className?: string;
}

export const InstagramPreview: React.FC<InstagramPreviewProps> = ({
  imageUrl,
  caption,
  hashtags = "",
  username = "seu_perfil",
  profilePic,
  likes = Math.floor(Math.random() * 1000) + 100,
  className,
}) => {
  const [isLiked, setIsLiked] = React.useState(false);
  const [isSaved, setIsSaved] = React.useState(false);

  const combinedCaption = hashtags 
    ? `${caption}\n\n${hashtags}` 
    : caption;

  return (
    <div className={cn("bg-white dark:bg-zinc-900 rounded-lg border shadow-lg max-w-[350px] mx-auto", className)}>
      {/* Header */}
      <div className="flex items-center gap-3 p-3 border-b">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-500 via-red-500 to-yellow-500 p-[2px]">
          <div className="w-full h-full rounded-full bg-white dark:bg-zinc-900 p-[2px]">
            {profilePic ? (
              <img src={profilePic} alt={username} className="w-full h-full rounded-full object-cover" />
            ) : (
              <div className="w-full h-full rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white text-xs font-bold">
                {username[0].toUpperCase()}
              </div>
            )}
          </div>
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold">{username}</p>
          <p className="text-xs text-muted-foreground">Local • Original</p>
        </div>
        <button className="p-1 hover:bg-muted rounded">
          <MoreHorizontal className="h-5 w-5" />
        </button>
      </div>

      {/* Image */}
      <div className="relative aspect-square bg-black">
        <img 
          src={imageUrl} 
          alt="Preview" 
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).src = "https://placehold.co/400x400/1a1a1a/666?text=Imagem";
          }}
        />
      </div>

      {/* Actions */}
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setIsLiked(!isLiked)}
              className="hover:opacity-70 transition-opacity"
            >
              <Heart className={cn("h-6 w-6", isLiked && "fill-red-500 text-red-500")} />
            </button>
            <button className="hover:opacity-70 transition-opacity">
              <MessageCircle className="h-6 w-6" />
            </button>
            <button className="hover:opacity-70 transition-opacity">
              <Send className="h-6 w-6" />
            </button>
          </div>
          <button 
            onClick={() => setIsSaved(!isSaved)}
            className="hover:opacity-70 transition-opacity"
          >
            <Bookmark className={cn("h-6 w-6", isSaved && "fill-current")} />
          </button>
        </div>

        {/* Likes */}
        <p className="text-sm font-semibold">
          {(isLiked ? likes + 1 : likes).toLocaleString()} curtidas
        </p>

        {/* Caption */}
        <div className="text-sm">
          <span className="font-semibold mr-1">{username}</span>
          <span className="whitespace-pre-wrap break-words">
            {combinedCaption.length > 150 
              ? `${combinedCaption.slice(0, 150)}...` 
              : combinedCaption
            }
          </span>
        </div>

        {/* Comments */}
        <button className="text-sm text-muted-foreground hover:opacity-70">
          Ver todos os 24 comentários
        </button>

        {/* Time */}
        <p className="text-xs text-muted-foreground uppercase">
          Há 2 horas
        </p>
      </div>
    </div>
  );
};

// ============================================
// TIKTOK PREVIEW
// ============================================

interface TikTokPreviewProps {
  imageUrl: string;
  caption: string;
  username?: string;
  profilePic?: string;
  soundName?: string;
  likes?: number;
  comments?: number;
  shares?: number;
  className?: string;
}

export const TikTokPreview: React.FC<TikTokPreviewProps> = ({
  imageUrl,
  caption,
  username = "@seu_perfil",
  profilePic,
  soundName = "Som original",
  likes = Math.floor(Math.random() * 50000) + 5000,
  comments = Math.floor(Math.random() * 1000) + 100,
  shares = Math.floor(Math.random() * 500) + 50,
  className,
}) => {
  const [isLiked, setIsLiked] = React.useState(false);
  const [isFollowing, setIsFollowing] = React.useState(false);

  const formatCount = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className={cn("relative bg-black rounded-xl overflow-hidden max-w-[280px] mx-auto aspect-[9/16]", className)}>
      {/* Background Image/Video */}
      <img 
        src={imageUrl} 
        alt="Preview" 
        className="absolute inset-0 w-full h-full object-cover"
        onError={(e) => {
          (e.target as HTMLImageElement).src = "https://placehold.co/270x480/1a1a1a/666?text=Video";
        }}
      />

      {/* Overlay gradient */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />

      {/* Play button in center */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
          <svg className="w-8 h-8 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        </div>
      </div>

      {/* Right side actions */}
      <div className="absolute right-3 bottom-24 flex flex-col items-center gap-5">
        {/* Profile */}
        <div className="relative">
          <div className="w-12 h-12 rounded-full border-2 border-white overflow-hidden">
            {profilePic ? (
              <img src={profilePic} alt={username} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-white font-bold">
                {username.replace("@", "")[0].toUpperCase()}
              </div>
            )}
          </div>
          <button 
            onClick={() => setIsFollowing(!isFollowing)}
            className={cn(
              "absolute -bottom-2 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full flex items-center justify-center text-white text-lg font-bold",
              isFollowing ? "bg-gray-500" : "bg-red-500"
            )}
          >
            {isFollowing ? "✓" : "+"}
          </button>
        </div>

        {/* Like */}
        <button 
          onClick={() => setIsLiked(!isLiked)}
          className="flex flex-col items-center gap-1"
        >
          <Heart className={cn("h-8 w-8 text-white", isLiked && "fill-red-500 text-red-500")} />
          <span className="text-white text-xs font-semibold">
            {formatCount(isLiked ? likes + 1 : likes)}
          </span>
        </button>

        {/* Comment */}
        <button className="flex flex-col items-center gap-1">
          <MessageCircle className="h-8 w-8 text-white" />
          <span className="text-white text-xs font-semibold">{formatCount(comments)}</span>
        </button>

        {/* Bookmark */}
        <button className="flex flex-col items-center gap-1">
          <Bookmark className="h-8 w-8 text-white" />
          <span className="text-white text-xs font-semibold">{formatCount(Math.floor(shares / 2))}</span>
        </button>

        {/* Share */}
        <button className="flex flex-col items-center gap-1">
          <Share2 className="h-8 w-8 text-white" />
          <span className="text-white text-xs font-semibold">{formatCount(shares)}</span>
        </button>

        {/* Sound disc */}
        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-gray-800 to-gray-600 border-2 border-gray-500 animate-spin flex items-center justify-center" style={{ animationDuration: "3s" }}>
          <div className="w-4 h-4 rounded-full bg-gray-300" />
        </div>
      </div>

      {/* Bottom content */}
      <div className="absolute bottom-4 left-3 right-16 text-white">
        <p className="font-semibold text-base mb-1">{username}</p>
        <p className="text-sm leading-tight mb-2 line-clamp-2">{caption}</p>
        <div className="flex items-center gap-2">
          <Music className="h-4 w-4" />
          <p className="text-xs truncate">{soundName}</p>
        </div>
      </div>

      {/* TikTok logo */}
      <div className="absolute top-4 right-4">
        <svg viewBox="0 0 24 24" className="h-6 w-6 fill-white">
          <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
        </svg>
      </div>
    </div>
  );
};

// ============================================
// YOUTUBE PREVIEW
// ============================================

interface YouTubePreviewProps {
  imageUrl: string;
  title: string;
  description?: string;
  channelName?: string;
  channelPic?: string;
  views?: number;
  duration?: string;
  className?: string;
  variant?: "card" | "watch";
}

export const YouTubePreview: React.FC<YouTubePreviewProps> = ({
  imageUrl,
  title,
  description = "",
  channelName = "Seu Canal",
  channelPic,
  views = Math.floor(Math.random() * 100000) + 10000,
  duration = "0:00",
  className,
  variant = "card",
}) => {
  const [isLiked, setIsLiked] = React.useState(false);
  const [isSubscribed, setIsSubscribed] = React.useState(false);

  const formatViews = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${Math.floor(num / 1000)}K`;
    return num.toString();
  };

  if (variant === "watch") {
    return (
      <div className={cn("bg-white dark:bg-zinc-900 rounded-lg border shadow-lg max-w-[450px] mx-auto overflow-hidden", className)}>
        {/* Video Player */}
        <div className="relative aspect-video bg-black">
          <img 
            src={imageUrl} 
            alt="Preview" 
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = "https://placehold.co/640x360/1a1a1a/666?text=Video";
            }}
          />
          {/* Play button */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-16 h-16 rounded-full bg-red-600/90 flex items-center justify-center">
              <svg className="w-8 h-8 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          </div>
          {/* Duration */}
          <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded">
            {duration}
          </div>
          {/* Progress bar */}
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-600">
            <div className="h-full w-0 bg-red-600" />
          </div>
        </div>

        {/* Video Info */}
        <div className="p-4 space-y-3">
          <h3 className="font-semibold text-lg leading-tight line-clamp-2">{title}</h3>
          
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>{formatViews(views)} visualizações</span>
            <span>•</span>
            <span>Há 2 horas</span>
          </div>

          {/* Channel */}
          <div className="flex items-center justify-between py-3 border-y">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full overflow-hidden bg-gray-200">
                {channelPic ? (
                  <img src={channelPic} alt={channelName} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-red-500 flex items-center justify-center text-white font-bold">
                    {channelName[0].toUpperCase()}
                  </div>
                )}
              </div>
              <div>
                <p className="font-medium text-sm">{channelName}</p>
                <p className="text-xs text-muted-foreground">1.2M inscritos</p>
              </div>
            </div>
            <button 
              onClick={() => setIsSubscribed(!isSubscribed)}
              className={cn(
                "px-4 py-2 rounded-full text-sm font-medium transition-colors",
                isSubscribed 
                  ? "bg-muted text-foreground" 
                  : "bg-red-600 text-white hover:bg-red-700"
              )}
            >
              {isSubscribed ? "Inscrito" : "Inscrever"}
            </button>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setIsLiked(!isLiked)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors",
                isLiked ? "bg-blue-100 text-blue-600 dark:bg-blue-900/30" : "bg-muted hover:bg-muted/80"
              )}
            >
              <ThumbsUp className={cn("h-4 w-4", isLiked && "fill-current")} />
              {formatViews(Math.floor(views * 0.05))}
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-full bg-muted hover:bg-muted/80 text-sm font-medium">
              <ThumbsDown className="h-4 w-4" />
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-full bg-muted hover:bg-muted/80 text-sm font-medium">
              <Share2 className="h-4 w-4" />
              Compartilhar
            </button>
          </div>

          {/* Description */}
          {description && (
            <div className="p-3 rounded-lg bg-muted/50 text-sm">
              <p className="line-clamp-3 whitespace-pre-wrap">{description}</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Card variant (default)
  return (
    <div className={cn("bg-white dark:bg-zinc-900 rounded-lg overflow-hidden max-w-[300px] mx-auto group cursor-pointer", className)}>
      {/* Thumbnail */}
      <div className="relative aspect-video bg-black">
        <img 
          src={imageUrl} 
          alt="Preview" 
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
          onError={(e) => {
            (e.target as HTMLImageElement).src = "https://placehold.co/320x180/1a1a1a/666?text=Video";
          }}
        />
        {/* Duration */}
        <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded">
          {duration}
        </div>
        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
          <div className="w-12 h-12 rounded-full bg-black/60 flex items-center justify-center">
            <svg className="w-6 h-6 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
        </div>
        {/* Watch later */}
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="p-1.5 rounded bg-black/60 hover:bg-black/80">
            <Clock className="h-4 w-4 text-white" />
          </button>
        </div>
      </div>

      {/* Info */}
      <div className="p-3 flex gap-3">
        <div className="w-9 h-9 rounded-full overflow-hidden bg-gray-200 flex-shrink-0">
          {channelPic ? (
            <img src={channelPic} alt={channelName} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-red-500 flex items-center justify-center text-white text-sm font-bold">
              {channelName[0].toUpperCase()}
            </div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm leading-tight line-clamp-2 mb-1">{title}</h4>
          <p className="text-xs text-muted-foreground">{channelName}</p>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Eye className="h-3 w-3" />
            <span>{formatViews(views)} visualizações</span>
            <span>•</span>
            <span>Há 2 horas</span>
          </div>
        </div>
        <button className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-muted rounded self-start">
          <MoreHorizontal className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
};

// ============================================
// EXPORT ALL
// ============================================

export default {
  InstagramPreview,
  TikTokPreview,
  YouTubePreview,
};
