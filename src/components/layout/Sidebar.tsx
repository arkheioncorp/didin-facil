import * as React from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";
import {
  TikTrendLogo,
  DashboardIcon,
  SearchIcon,
  ProductsIcon,
  FavoritesIcon,
  CopyIcon,
  SettingsIcon,
  UserIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from "@/components/icons";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOut } from "lucide-react";
import { useUserStore } from "@/stores";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const menuItems = [
  {
    label: "Dashboard",
    icon: DashboardIcon,
    path: "/",
  },
  {
    label: "Buscar",
    icon: SearchIcon,
    path: "/search",
  },
  {
    label: "Produtos",
    icon: ProductsIcon,
    path: "/products",
  },
  {
    label: "Favoritos",
    icon: FavoritesIcon,
    path: "/favorites",
  },
  {
    label: "Copy AI",
    icon: CopyIcon,
    path: "/copy",
  },
];

const bottomItems = [
  {
    label: "Configurações",
    icon: SettingsIcon,
    path: "/settings",
  },
  {
    label: "Perfil",
    icon: UserIcon,
    path: "/profile",
    testId: "user-menu",
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const location = useLocation();
  const { user, license, logout } = useUserStore();

  const isActive = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <TooltipProvider>
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 h-screen border-r bg-card transition-all duration-300",
          collapsed ? "w-16" : "w-64"
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex h-16 items-center justify-between border-b px-4">
            <Link to="/" className="flex items-center gap-3">
              <TikTrendLogo size={32} />
              {!collapsed && (
                <span className="text-lg font-bold bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary bg-clip-text text-transparent">
                  TikTrend
                </span>
              )}
            </Link>
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggle}
              className={cn("h-8 w-8", collapsed && "ml-auto")}
            >
              {collapsed ? (
                <ChevronRightIcon size={16} />
              ) : (
                <ChevronLeftIcon size={16} />
              )}
            </Button>
          </div>

          {/* Navigation */}
          <ScrollArea className="flex-1 py-4">
            <nav className="space-y-1 px-2">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.path);

                return collapsed ? (
                  <Tooltip key={item.path} delayDuration={0}>
                    <TooltipTrigger asChild>
                      <Link to={item.path}>
                        <Button
                          variant={active ? "default" : "ghost"}
                          size="icon"
                          className={cn(
                            "w-full",
                            active && "bg-tiktrend-primary hover:bg-tiktrend-primary/90"
                          )}
                        >
                          <Icon size={20} />
                        </Button>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      {item.label}
                    </TooltipContent>
                  </Tooltip>
                ) : (
                  <Link key={item.path} to={item.path}>
                    <Button
                      variant={active ? "default" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-3",
                        active && "bg-tiktrend-primary hover:bg-tiktrend-primary/90"
                      )}
                    >
                      <Icon size={20} />
                      <span>{item.label}</span>
                    </Button>
                  </Link>
                );
              })}
            </nav>
          </ScrollArea>

          {/* Plan Badge */}
          {!collapsed && license && (
            <div className="mx-4 mb-4 rounded-lg bg-gradient-to-r from-tiktrend-primary/10 to-tiktrend-secondary/10 p-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Plano</span>
                <span className="text-xs font-medium uppercase text-tiktrend-primary">
                  {license.plan}
                </span>
              </div>
              <div className="mt-1 text-sm font-medium">
                {user?.name || user?.email || "Usuário"}
              </div>
            </div>
          )}

          {/* Bottom Navigation */}
          <div className="border-t py-4">
            <nav className="space-y-1 px-2">
              {bottomItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.path);
                // @ts-ignore
                const testId = item.testId;

                if (testId === "user-menu") {
                  return (
                    <DropdownMenu key={item.path}>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant={active ? "secondary" : "ghost"}
                          size={collapsed ? "icon" : "default"}
                          className={cn(
                            "w-full",
                            !collapsed && "justify-start gap-3"
                          )}
                          data-testid="user-menu"
                        >
                          <Icon size={20} />
                          {!collapsed && <span>{item.label}</span>}
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent side="right" align="end" className="w-56" data-testid="user-dropdown">
                        <DropdownMenuLabel>Minha Conta</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem asChild>
                          <Link to="/profile" className="cursor-pointer w-full flex items-center">
                            <UserIcon size={16} className="mr-2" />
                            <span>Perfil</span>
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={logout} className="text-red-600 cursor-pointer" data-testid="logout-button">
                          <LogOut size={16} className="mr-2" />
                          <span>Sair</span>
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  );
                }

                return collapsed ? (
                  <Tooltip key={item.path} delayDuration={0}>
                    <TooltipTrigger asChild>
                      <Link to={item.path} data-testid={testId}>
                        <Button
                          variant={active ? "secondary" : "ghost"}
                          size="icon"
                          className="w-full"
                        >
                          <Icon size={20} />
                        </Button>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      {item.label}
                    </TooltipContent>
                  </Tooltip>
                ) : (
                  <Link key={item.path} to={item.path} data-testid={testId}>
                    <Button
                      variant={active ? "secondary" : "ghost"}
                      className="w-full justify-start gap-3"
                    >
                      <Icon size={20} />
                      <span>{item.label}</span>
                    </Button>
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      </aside>
    </TooltipProvider>
  );
};
