import * as React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "circular" | "text" | "card" | "avatar";
  shimmer?: boolean;
}

function Skeleton({ className, variant = "default", shimmer = true, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden bg-muted/60",
        variant === "circular" && "rounded-full",
        variant === "text" && "rounded-lg h-4 w-full",
        variant === "default" && "rounded-xl",
        variant === "card" && "rounded-xl aspect-square",
        variant === "avatar" && "rounded-full w-10 h-10",
        shimmer && [
          "before:absolute before:inset-0",
          "before:-translate-x-full",
          "before:animate-[shimmer_1.5s_infinite]",
          "before:bg-gradient-to-r",
          "before:from-transparent before:via-white/20 before:to-transparent",
        ],
        className
      )}
      {...props}
    />
  );
}

// Skeleton presets para uso comum
function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn("space-y-4", className)}>
      <Skeleton className="aspect-square w-full" />
      <div className="space-y-2 px-1">
        <Skeleton variant="text" className="w-3/4" />
        <Skeleton variant="text" className="w-1/2" />
        <Skeleton variant="text" className="w-1/4 h-6" />
      </div>
    </div>
  );
}

function SkeletonList({ count = 3, className }: { count?: number; className?: string }) {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton variant="avatar" />
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" className="w-3/4" />
            <Skeleton variant="text" className="w-1/2 h-3" />
          </div>
        </div>
      ))}
    </div>
  );
}

export { Skeleton, SkeletonCard, SkeletonList };
