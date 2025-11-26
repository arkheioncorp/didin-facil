import { Skeleton } from "./skeleton";

interface LoadingStateProps {
  count?: number;
  className?: string;
}

export function LoadingGrid({ count = 8, className = "" }: LoadingStateProps) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="space-y-4">
          <Skeleton className="h-[200px] w-full rounded-xl" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-[250px]" />
            <Skeleton className="h-4 w-[200px]" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function LoadingRow({ count = 5 }: LoadingStateProps) {
    return (
        <div className="space-y-4 w-full">
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                    <Skeleton className="h-12 w-12 rounded-full" />
                    <div className="space-y-2">
                        <Skeleton className="h-4 w-[250px]" />
                        <Skeleton className="h-4 w-[200px]" />
                    </div>
                </div>
            ))}
        </div>
    )
}
