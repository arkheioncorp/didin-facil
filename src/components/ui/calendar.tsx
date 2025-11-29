"use client";

import * as React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { 
  format, 
  addMonths, 
  subMonths, 
  startOfMonth, 
  endOfMonth, 
  eachDayOfInterval, 
  isSameMonth, 
  isSameDay, 
  startOfWeek, 
  endOfWeek,
  isToday
} from "date-fns";
import { ptBR, Locale } from "date-fns/locale";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export type CalendarProps = {
  mode?: "single";
  selected?: Date;
  onSelect?: (date: Date | undefined) => void;
  month?: Date;
  onMonthChange?: (date: Date) => void;
  disabled?: (date: Date) => boolean;
  locale?: Locale;
  className?: string;
  modifiers?: Record<string, (date: Date) => boolean>;
  modifiersClassNames?: Record<string, string>;
};

function Calendar({
  className,
  selected,
  onSelect,
  month: controlledMonth,
  onMonthChange,
  disabled,
  locale = ptBR,
  modifiers = {},
  modifiersClassNames = {},
}: CalendarProps) {
  const [internalMonth, setInternalMonth] = React.useState(selected || new Date());
  
  const currentMonth = controlledMonth || internalMonth;
  
  const handleMonthChange = (newMonth: Date) => {
    if (onMonthChange) {
      onMonthChange(newMonth);
    } else {
      setInternalMonth(newMonth);
    }
  };

  const handlePreviousMonth = () => {
    handleMonthChange(subMonths(currentMonth, 1));
  };

  const handleNextMonth = () => {
    handleMonthChange(addMonths(currentMonth, 1));
  };

  const handleDayClick = (day: Date) => {
    if (disabled && disabled(day)) return;
    onSelect?.(day);
  };

  // Get all days to display (including days from previous/next month to fill the grid)
  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const calendarStart = startOfWeek(monthStart, { locale });
  const calendarEnd = endOfWeek(monthEnd, { locale });
  
  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

  // Day names
  const weekDays = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

  return (
    <div className={cn("p-3", className)}>
      {/* Header with month navigation */}
      <div className="flex items-center justify-between mb-4">
        <Button
          variant="outline"
          size="icon"
          className="h-7 w-7"
          onClick={handlePreviousMonth}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <div className="font-medium">
          {format(currentMonth, "MMMM yyyy", { locale })}
        </div>
        <Button
          variant="outline"
          size="icon"
          className="h-7 w-7"
          onClick={handleNextMonth}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Weekday headers */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {weekDays.map((day) => (
          <div
            key={day}
            className="text-center text-xs text-muted-foreground font-medium py-1"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Days grid */}
      <div className="grid grid-cols-7 gap-1">
        {days.map((day, idx) => {
          const isSelected = selected && isSameDay(day, selected);
          const isCurrentMonth = isSameMonth(day, currentMonth);
          const isDayToday = isToday(day);
          const isDisabled = disabled && disabled(day);
          
          // Check custom modifiers
          let modifierClasses = "";
          Object.entries(modifiers).forEach(([key, fn]) => {
            if (fn(day) && modifiersClassNames[key]) {
              modifierClasses += ` ${modifiersClassNames[key]}`;
            }
          });

          return (
            <button
              key={idx}
              type="button"
              onClick={() => handleDayClick(day)}
              disabled={isDisabled}
              className={cn(
                "h-9 w-9 p-0 font-normal inline-flex items-center justify-center rounded-md text-sm transition-colors",
                "hover:bg-accent hover:text-accent-foreground",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                !isCurrentMonth && "text-muted-foreground opacity-50",
                isSelected && "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground",
                isDayToday && !isSelected && "bg-accent text-accent-foreground",
                isDisabled && "opacity-50 cursor-not-allowed hover:bg-transparent",
                modifierClasses
              )}
            >
              {format(day, "d")}
            </button>
          );
        })}
      </div>
    </div>
  );
}

Calendar.displayName = "Calendar";

export { Calendar };
