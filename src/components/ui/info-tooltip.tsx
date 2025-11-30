import * as React from "react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./tooltip";
import { HelpCircle, Info, AlertTriangle, CheckCircle } from "lucide-react";

interface InfoTooltipProps {
  content: React.ReactNode;
  children?: React.ReactNode;
  variant?: "info" | "help" | "warning" | "success";
  side?: "top" | "right" | "bottom" | "left";
  className?: string;
  iconClassName?: string;
}

const variantIcons = {
  info: Info,
  help: HelpCircle,
  warning: AlertTriangle,
  success: CheckCircle,
};

const variantStyles = {
  info: "text-blue-500 hover:text-blue-600",
  help: "text-muted-foreground hover:text-foreground",
  warning: "text-amber-500 hover:text-amber-600",
  success: "text-green-500 hover:text-green-600",
};

/**
 * InfoTooltip - Componente para exibir informações contextuais
 * 
 * @example
 * <InfoTooltip content="Texto de ajuda" />
 * 
 * @example
 * <InfoTooltip content="Aviso importante" variant="warning" />
 */
export function InfoTooltip({
  content,
  children,
  variant = "help",
  side = "top",
  className,
  iconClassName,
}: InfoTooltipProps) {
  const Icon = variantIcons[variant];

  return (
    <TooltipProvider>
      <Tooltip delayDuration={100}>
        <TooltipTrigger asChild>
          <span
            className={cn(
              "inline-flex cursor-help transition-colors",
              variantStyles[variant],
              className
            )}
          >
            {children || <Icon className={cn("h-4 w-4", iconClassName)} />}
          </span>
        </TooltipTrigger>
        <TooltipContent
          side={side}
          className={cn(
            "max-w-xs text-sm",
            variant === "warning" && "border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-900"
          )}
        >
          {content}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * SettingHelp - Componente para descrição de configurações com ícone de ajuda
 */
interface SettingHelpProps {
  label: string;
  description?: string;
  tooltip?: string;
  required?: boolean;
  className?: string;
}

export function SettingLabel({
  label,
  description,
  tooltip,
  required,
  className,
}: SettingHelpProps) {
  return (
    <div className={cn("space-y-1", className)}>
      <div className="flex items-center gap-1.5">
        <label className="text-sm font-medium">
          {label}
          {required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
        {tooltip && (
          <InfoTooltip content={tooltip} variant="help" />
        )}
      </div>
      {description && (
        <p className="text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  );
}

/**
 * SettingCard - Card para configuração com status visual
 */
interface SettingCardProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  status?: "active" | "inactive" | "warning" | "error";
  statusText?: string;
  children: React.ReactNode;
  className?: string;
}

const statusStyles = {
  active: "border-green-500/30 bg-green-50/50 dark:bg-green-950/20",
  inactive: "",
  warning: "border-amber-500/30 bg-amber-50/50 dark:bg-amber-950/20",
  error: "border-red-500/30 bg-red-50/50 dark:bg-red-950/20",
};

const statusBadgeStyles = {
  active: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  inactive: "bg-muted text-muted-foreground",
  warning: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  error: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
};

export function SettingCard({
  icon,
  title,
  description,
  status,
  statusText,
  children,
  className,
}: SettingCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border p-4 transition-colors",
        status && statusStyles[status],
        className
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          {icon && <span className="text-xl">{icon}</span>}
          <div>
            <h4 className="font-medium">{title}</h4>
            {description && (
              <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
            )}
          </div>
        </div>
        {status && statusText && (
          <span
            className={cn(
              "text-xs px-2 py-0.5 rounded-full font-medium",
              statusBadgeStyles[status]
            )}
          >
            {statusText}
          </span>
        )}
      </div>
      {children}
    </div>
  );
}

/**
 * HelpSection - Seção de ajuda colapsável
 */
interface HelpSectionProps {
  title?: string;
  items: {
    question: string;
    answer: string;
  }[];
  className?: string;
}

export function HelpSection({ title, items, className }: HelpSectionProps) {
  const [openIndex, setOpenIndex] = React.useState<number | null>(null);

  return (
    <div className={cn("space-y-2", className)}>
      {title && (
        <h4 className="text-sm font-medium flex items-center gap-2">
          <HelpCircle className="h-4 w-4 text-tiktrend-primary" />
          {title}
        </h4>
      )}
      <div className="space-y-1">
        {items.map((item, index) => (
          <div key={index} className="border rounded-md overflow-hidden">
            <button
              onClick={() => setOpenIndex(openIndex === index ? null : index)}
              className="w-full text-left text-sm px-3 py-2 bg-muted/50 hover:bg-muted flex items-center justify-between"
            >
              <span className="font-medium">{item.question}</span>
              <span className="text-muted-foreground">
                {openIndex === index ? "−" : "+"}
              </span>
            </button>
            {openIndex === index && (
              <div className="px-3 py-2 text-sm text-muted-foreground bg-background">
                {item.answer}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * FeatureHighlight - Destaque visual para recursos importantes
 */
interface FeatureHighlightProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  variant?: "default" | "premium" | "new" | "beta";
}

const highlightStyles = {
  default: "border-border",
  premium: "border-amber-500/50 bg-gradient-to-r from-amber-50/50 to-yellow-50/50 dark:from-amber-950/30 dark:to-yellow-950/30",
  new: "border-green-500/50 bg-gradient-to-r from-green-50/50 to-emerald-50/50 dark:from-green-950/30 dark:to-emerald-950/30",
  beta: "border-blue-500/50 bg-gradient-to-r from-blue-50/50 to-cyan-50/50 dark:from-blue-950/30 dark:to-cyan-950/30",
};

const badgeText = {
  default: null,
  premium: "Premium",
  new: "Novo",
  beta: "Beta",
};

export function FeatureHighlight({
  icon,
  title,
  description,
  variant = "default",
}: FeatureHighlightProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 p-3 rounded-lg border",
        highlightStyles[variant]
      )}
    >
      <span className="text-xl flex-shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{title}</span>
          {variant !== "default" && badgeText[variant] && (
            <span
              className={cn(
                "text-[10px] px-1.5 py-0.5 rounded font-bold uppercase",
                variant === "premium" && "bg-amber-500 text-white",
                variant === "new" && "bg-green-500 text-white",
                variant === "beta" && "bg-blue-500 text-white"
              )}
            >
              {badgeText[variant]}
            </span>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
      </div>
    </div>
  );
}

export default InfoTooltip;
