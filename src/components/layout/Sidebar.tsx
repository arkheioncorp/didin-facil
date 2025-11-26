import * as React from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
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

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const location = useLocation();
  const { t } = useTranslation();
  const { user, license, logout } = useUserStore();

  const menuItems = [
    {
      label: t("dashboard", "Dashboard"),
      icon: DashboardIcon,
      path: "/",
      testId: "nav-dashboard",
    },
    {
      label: t("search", "Buscar"),
      icon: SearchIcon,
      path: "/search",
      testId: "nav-search",
    },
    {
      label: t("products", "Produtos"),
      icon: ProductsIcon,
      path: "/products",
      testId: "nav-products",
    },
    {
      label: t("favorites", "Favoritos"),
      icon: FavoritesIcon,
      path: "/favorites",
      testId: "nav-favorites",
    },
    {
      label: t("copy_ai", "Copy AI"),
      icon: CopyIcon,
      path: "/copy",
      testId: "nav-copy",
    },
  ];

  const bottomItems = [
    {
      label: t("settings", "Configurações"),
      icon: SettingsIcon,
      path: "/settings",
      testId: "nav-settings",
    },
    {
      label: t("profile", "Perfil"),
      icon: UserIcon,
      path: "/profile",
      testId: "user-menu",
    },
  ];

  const isActive = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <TooltipProvider>
      <aside
        data-testid="sidebar"
        className={cn(
          "fixed left-0 top-0 z-40 h-screen border-r bg-card/95 backdrop-blur-md transition-all duration-300 ease-out",
          collapsed ? "w-[72px]" : "w-64"
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header - Melhoria #26: Micro-animações */}
          <div className="flex h-16 items-center justify-between border-b px-4">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="transition-transform duration-300 group-hover:scale-110">
                <TikTrendLogo size={36} />
              </div>
              {!collapsed && (
                <span className="text-xl font-bold bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary bg-clip-text text-transparent animate-gradient">
                  TikTrend
                </span>
              )}
            </Link>
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggle}
              className={cn(
                "h-8 w-8 rounded-lg hover:bg-accent transition-all duration-200",
                collapsed && "ml-auto"
              )}
            >
              {collapsed ? (
                <ChevronRightIcon size={16} />
              ) : (
                <ChevronLeftIcon size={16} />
              )}
            </Button>
          </div>

          {/* Navigation - Melhoria #12: Indicador ativo melhorado */}
          <ScrollArea className="flex-1 py-4">
            <nav className="space-y-1.5 px-3">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.path);

                return collapsed ? (
                  <Tooltip key={item.path} delayDuration={0}>
                    <TooltipTrigger asChild>
                      <Link to={item.path} data-testid={item.testId}>
                        <Button
                          variant={active ? "default" : "ghost"}
                          size="icon"
                          className={cn(
                            "w-full h-11 rounded-xl transition-all duration-200",
                            active && "bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary shadow-lg shadow-tiktrend-primary/25 hover:shadow-tiktrend-primary/40"
                          )}
                        >
                          <Icon size={20} />
                        </Button>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="font-medium">
                      {item.label}
                    </TooltipContent>
                  </Tooltip>
                ) : (
                  <Link key={item.path} to={item.path} data-testid={item.testId}>
                    <Button
                      variant={active ? "default" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-3 h-11 rounded-xl transition-all duration-200",
                        active && "bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary shadow-lg shadow-tiktrend-primary/25 hover:shadow-tiktrend-primary/40",
                        !active && "hover:bg-accent hover:translate-x-1"
                      )}
                    >
                      <Icon size={20} />
                      <span className="font-medium">{item.label}</span>
                      {active && (
                        <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                      )}
                    </Button>
                  </Link>
                );
              })}
            </nav>
          </ScrollArea>

          {/* Plan Badge - Melhoria visual */}
          {!collapsed && license && (
            <div className="mx-3 mb-4 rounded-xl bg-gradient-to-br from-tiktrend-primary/10 via-transparent to-tiktrend-secondary/10 p-4 border border-tiktrend-primary/10">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground font-medium">Plano Atual</span>
                <span className="text-xs font-bold uppercase px-2 py-0.5 rounded-full bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary text-white">
                  {license.plan}
                </span>
              </div>
              <div className="text-sm font-semibold truncate">
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
                          <Link to="/profile" className="cursor-pointer w-full flex items-center" data-testid="profile-link">
                            <UserIcon size={16} className="mr-2" />
                            <span data-testid="user-email">Perfil</span>
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
