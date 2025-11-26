import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SearchIcon, MenuIcon } from "@/components/icons";


interface HeaderProps {
  title?: string;
  onMenuClick?: () => void;
  showSearch?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  onMenuClick,
  showSearch = true,
}) => {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={onMenuClick}
      >
        <MenuIcon size={20} />
      </Button>

      {/* Title */}
      {title && (
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Search */}
      {showSearch && (
        <div className="hidden md:block">
          <Input
            placeholder="Buscar produtos..."
            className="w-64"
            icon={<SearchIcon size={16} />}
          />
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        {/* Notifications, etc can go here */}
      </div>
    </header>
  );
};
