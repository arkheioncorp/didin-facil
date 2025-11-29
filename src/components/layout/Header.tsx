import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SearchIcon, MenuIcon } from "@/components/icons";
import { NotificationBell } from "@/components/NotificationBell";


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
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = React.useState("");

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header
      data-testid="header"
      className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60 px-6 transition-all duration-200"
    >
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden hover:bg-accent"
        onClick={onMenuClick}
        data-testid="menu-toggle"
      >
        <MenuIcon size={20} />
      </Button>

      {/* Title */}
      {title && (
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Search - Melhoria #16 */}
      {showSearch && (
        <div className="hidden md:block">
          <div className="relative group">
            <Input
              placeholder="Buscar produtos..."
              className="w-72 transition-all duration-300 focus:w-80"
              icon={<SearchIcon size={16} />}
              data-testid="search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
            />
            {/* Search shortcut hint */}
            <div className="absolute right-3 top-1/2 -translate-y-1/2 hidden group-focus-within:hidden md:flex items-center gap-1 text-xs text-muted-foreground/60">
              <kbd className="px-1.5 py-0.5 rounded bg-muted text-[10px] font-mono">⌘</kbd>
              <kbd className="px-1.5 py-0.5 rounded bg-muted text-[10px] font-mono">K</kbd>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        {/* Notification Bell */}
        <NotificationBell />
      </div>
    </header>
  );
};
