import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  error?: string;
  success?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, icon, iconPosition = "left", error, success, ...props }, ref) => {
    const baseInputClass = cn(
      "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1.5 text-[13px] ring-offset-background transition-all duration-150",
      "file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground",
      "placeholder:text-muted-foreground/50",
      "hover:border-muted-foreground/40",
      "focus-visible:outline-none focus-visible:border-tiktrend-primary focus-visible:ring-2 focus-visible:ring-tiktrend-primary/10",
      "disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-input",
      error && "border-destructive focus-visible:border-destructive focus-visible:ring-destructive/10",
      success && "border-green-500 focus-visible:border-green-500 focus-visible:ring-green-500/10",
    );

    if (icon) {
      return (
        <div className="relative group">
          {iconPosition === "left" && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground/50 transition-colors group-focus-within:text-tiktrend-primary">
              {icon}
            </div>
          )}
          <input
            type={type}
            className={cn(
              baseInputClass,
              icon && iconPosition === "left" && "pl-9",
              icon && iconPosition === "right" && "pr-9",
              className
            )}
            ref={ref}
            {...props}
          />
          {iconPosition === "right" && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/50 transition-colors group-focus-within:text-tiktrend-primary">
              {icon}
            </div>
          )}
          {error && (
            <p className="mt-1.5 text-xs text-destructive flex items-center gap-1">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {error}
            </p>
          )}
        </div>
      );
    }

    return (
      <div>
        <input
          type={type}
          className={cn(baseInputClass, className)}
          ref={ref}
          {...props}
        />
        {error && (
          <p className="mt-1.5 text-xs text-destructive flex items-center gap-1">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };
