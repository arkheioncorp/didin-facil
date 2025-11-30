import * as React from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import {
  TikTrendLogo,
  DashboardIcon,
  SearchIcon,
  ProductsIcon,
  FavoritesIcon,
  CopyIcon,
  BotIcon,
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
import { 
  LogOut, 
  MessageCircle, 
  Crown, 
  Share2, 
  Instagram, 
  Video, 
  Youtube, 
  Bot, 
  BarChart3, 
  Kanban,
  Calendar,
  Download
} from "lucide-react";
import { useUserStore } from "@/stores";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const location = useLocation();
  const { t } = useTranslation();
  const { user, license, logout } = useUserStore();

  const menuSections = [
    {
      title: t("navigation.sections.core"),
      items: [
        {
          label: t("navigation.dashboard"),
          icon: DashboardIcon,
          path: "/",
          testId: "nav-dashboard",
        },
        {
          label: t("navigation.search"),
          icon: SearchIcon,
          path: "/search",
          testId: "nav-search",
        },
        {
          label: t("navigation.products"),
          icon: ProductsIcon,
          path: "/products",
          testId: "nav-products",
        },
        {
          label: t("navigation.coleta"),
          icon: Download,
          path: "/coleta",
          testId: "nav-coleta",
        },
        {
          label: t("navigation.favorites"),
          icon: FavoritesIcon,
          path: "/favorites",
          testId: "nav-favorites",
        },
      ]
    },
    {
      title: t("navigation.sections.social_suite"),
      items: [
        {
          label: t("navigation.social_hub"),
          icon: Share2,
          path: "/social",
          testId: "nav-social",
        },
        {
          label: t("navigation.instagram"),
          icon: Instagram,
          path: "/social/instagram",
          testId: "nav-instagram",
        },
        {
          label: t("navigation.tiktok"),
          icon: Video,
          path: "/social/tiktok",
          testId: "nav-tiktok",
        },
        {
          label: t("navigation.youtube"),
          icon: Youtube,
          path: "/social/youtube",
          testId: "nav-youtube",
        },
      ]
    },
    {
      title: t("navigation.sections.automation"),
      items: [
        {
          label: t("navigation.whatsapp"),
          icon: MessageCircle,
          path: "/whatsapp",
          testId: "nav-whatsapp",
        },
        {
          label: t("navigation.chatbot"),
          icon: Bot,
          path: "/automation/chatbot",
          testId: "nav-chatbot",
        },
        {
          label: t("navigation.scheduler"),
          icon: Calendar,
          path: "/automation/scheduler",
          testId: "nav-scheduler",
        },
        {
          label: t("navigation.copy_ai"),
          icon: CopyIcon,
          path: "/copy",
          testId: "nav-copy",
        },
        {
          label: t("navigation.seller_bot"),
          icon: BotIcon,
          path: "/seller-bot",
          testId: "nav-seller-bot",
          premium: true,
        },
      ]
    },
    {
      title: t("navigation.sections.crm_sales"),
      items: [
        {
          label: t("navigation.crm_dashboard"),
          icon: BarChart3,
          path: "/crm",
          testId: "nav-crm",
        },
        {
          label: t("navigation.pipeline"),
          icon: Kanban,
          path: "/crm/pipeline",
          testId: "nav-pipeline",
        },
      ]
    },
    {
      title: t("navigation.sections.admin", "Administração"),
      items: [
        {
          label: t("navigation.analytics", "Analytics"),
          icon: BarChart3,
          path: "/admin/analytics",
          testId: "nav-analytics",
        },
        {
          label: t("navigation.templates", "Templates"),
          icon: CopyIcon,
          path: "/admin/templates",
          testId: "nav-templates",
        },
        {
          label: t("navigation.accounts", "Contas"),
          icon: UserIcon,
          path: "/admin/accounts",
          testId: "nav-accounts",
        },
        {
          label: t("navigation.api_docs", "API Docs"),
          icon: SearchIcon,
          path: "/admin/docs",
          testId: "nav-api-docs",
        },
      ]
    }
  ];


  const bottomItems = [
    {
      label: t("navigation.settings"),
      icon: SettingsIcon,
      path: "/settings",
      testId: "nav-settings",
    },
    {
      label: t("navigation.profile"),
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
            <nav className="space-y-6 px-3">
              {menuSections.map((section, index) => (
                <div key={index} className="space-y-1.5">
                  {!collapsed && (
                    <h4 className="px-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                      {section.title}
                    </h4>
                  )}
                  {collapsed && index > 0 && <div className="h-px bg-border my-2 mx-2" />}
                  
                  {section.items.map((item) => {
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
                                "w-full h-11 rounded-xl transition-all duration-200 relative",
                                active && "bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary shadow-lg shadow-tiktrend-primary/25 hover:shadow-tiktrend-primary/40",
                                item.premium && "border border-yellow-500/30"
                              )}
                            >
                              <Icon size={20} />
                              {item.premium && (
                                <Crown className="absolute -top-1 -right-1 h-3 w-3 text-yellow-500" />
                              )}
                            </Button>
                          </Link>
                        </TooltipTrigger>
                        <TooltipContent side="right" className="font-medium">
                          <div className="flex items-center gap-1.5">
                            {item.label}
                            {item.premium && (
                              <Badge variant="outline" className="text-[10px] px-1 py-0 bg-yellow-500/10 text-yellow-600 border-yellow-500/30">
                                Premium
                              </Badge>
                            )}
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    ) : (
                      <Link key={item.path} to={item.path} data-testid={item.testId}>
                        <Button
                          variant={active ? "default" : "ghost"}
                          className={cn(
                            "w-full justify-start gap-3 h-11 rounded-xl transition-all duration-200",
                            active && "bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary shadow-lg shadow-tiktrend-primary/25 hover:shadow-tiktrend-primary/40",
                            !active && "hover:bg-accent hover:translate-x-1",
                            item.premium && !active && "border border-yellow-500/30"
                          )}
                        >
                          <Icon size={20} />
                          <span className="font-medium">{item.label}</span>
                          {item.premium && (
                            <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-yellow-500/10 text-yellow-600 border-yellow-500/30">
                              <Crown className="h-2.5 w-2.5 mr-0.5" />
                              Premium
                            </Badge>
                          )}
                          {active && !item.premium && (
                            <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                          )}
                        </Button>
                      </Link>
                    );
                  })}
                </div>
              ))}
            </nav>
          </ScrollArea>

          {/* License Badge - Licença Vitalícia + Créditos */}
          {!collapsed && license && (
            <div className="mx-3 mb-4 rounded-xl bg-gradient-to-br from-tiktrend-primary/10 via-transparent to-tiktrend-secondary/10 p-4 border border-tiktrend-primary/10">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground font-medium">
                  {license.isLifetime ? 'Licença Vitalícia' : 'Versão Gratuita'}
                </span>
                <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded-full ${
                  license.isLifetime
                    ? 'bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary text-white'
                    : 'bg-muted text-muted-foreground'
                }`}>
                  {license.isLifetime ? '✓ Ativa' : 'Free'}
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
