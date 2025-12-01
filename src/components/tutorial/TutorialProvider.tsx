/**
 * Tutorial System - TikTrend
 * =============================
 * Sistema de tutorial moderno com spotlight e design consistente.
 * Suporta tutoriais globais e específicos por página.
 */

import * as React from "react";
import { createContext, useContext, useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ChevronLeft, ChevronRight, SkipForward, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// ============================================
// TYPES
// ============================================

export interface TutorialStep {
  id: string;
  title: string;
  content: string;
  target?: string; // CSS selector for spotlight
  position?: "top" | "bottom" | "left" | "right" | "center";
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
  page?: string; // Página onde o step deve aparecer
}

export interface Tutorial {
  id: string;
  name: string;
  description: string;
  steps: TutorialStep[];
  triggerOnPage?: string; // Auto-trigger quando visitar página
}

interface TutorialContextType {
  // State
  isActive: boolean;
  currentTutorial: Tutorial | null;
  currentStepIndex: number;
  completedTutorials: string[];
  
  // Actions
  startTutorial: (tutorialId: string) => void;
  endTutorial: () => void;
  nextStep: () => void;
  prevStep: () => void;
  skipTutorial: () => void;
  markCompleted: (tutorialId: string) => void;
  resetTutorials: () => void;
  
  // Helpers
  getTutorialProgress: () => { current: number; total: number };
  isStepVisible: (stepId: string) => boolean;
}

const TutorialContext = createContext<TutorialContextType | null>(null);

// ============================================
// TUTORIALS DATA
// ============================================

export const TUTORIALS: Tutorial[] = [
  // ========== TUTORIAL PRINCIPAL (Onboarding) ==========
  {
    id: "main-onboarding",
    name: "Bem-vindo ao TikTrend",
    description: "Conheça as principais funcionalidades",
    steps: [
      {
        id: "welcome",
        title: "🎉 Bem-vindo ao TikTrend!",
        content: "Sua plataforma completa para encontrar produtos vencedores, automatizar vendas e gerenciar seu negócio. Vamos fazer um tour rápido!",
        position: "center",
        icon: <Sparkles className="w-6 h-6 text-primary" />,
      },
      {
        id: "sidebar-core",
        title: "📊 Menu Principal",
        content: "Aqui você encontra as ferramentas essenciais: Dashboard, Busca de Produtos, Catálogo, Coleta e Favoritos.",
        target: "[data-testid='nav-dashboard']",
        position: "right",
      },
      {
        id: "sidebar-social",
        title: "📱 Social Suite",
        content: "Gerencie todas as suas redes sociais: Instagram, TikTok e YouTube. Agende posts e analise métricas.",
        target: "[data-testid='nav-social']",
        position: "right",
      },
      {
        id: "sidebar-automation",
        title: "🤖 Automação",
        content: "WhatsApp, Chatbots, Agendamentos e Copy AI. Automatize seu atendimento e vendas 24/7.",
        target: "[data-testid='nav-whatsapp']",
        position: "right",
      },
      {
        id: "sidebar-crm",
        title: "💼 CRM & Vendas",
        content: "Gerencie seus leads e clientes com pipeline visual. Acompanhe cada oportunidade de venda.",
        target: "[data-testid='nav-crm']",
        position: "right",
      },
      {
        id: "license-info",
        title: "🔑 Licença & Créditos",
        content: "Sua Licença Vitalícia garante buscas ilimitadas para sempre. Créditos IA são usados para copies e análises avançadas.",
        target: "[data-testid='nav-checkout']",
        position: "right",
      },
      {
        id: "settings",
        title: "⚙️ Configurações",
        content: "Personalize tema, idioma e notificações. Acesse seu perfil para gerenciar conta e créditos.",
        target: "[data-testid='nav-settings']",
        position: "right",
      },
      {
        id: "complete",
        title: "🚀 Pronto para começar!",
        content: "Você pode acessar tutoriais específicos de cada página pelo ícone de ajuda (?) no topo. Boa sorte nas vendas!",
        position: "center",
      },
    ],
  },

  // ========== TUTORIAL: DASHBOARD ==========
  {
    id: "dashboard-tutorial",
    name: "Dashboard",
    description: "Visão geral do seu negócio",
    triggerOnPage: "/",
    steps: [
      {
        id: "dash-overview",
        title: "📈 Visão Geral",
        content: "O Dashboard mostra métricas importantes: vendas, produtos, leads e performance das automações.",
        position: "center",
        page: "/",
      },
      {
        id: "dash-stats",
        title: "📊 Estatísticas Rápidas",
        content: "Cards com números-chave atualizados em tempo real. Clique em qualquer card para ver detalhes.",
        target: ".stats-grid, .dashboard-stats",
        position: "bottom",
        page: "/",
      },
      {
        id: "dash-charts",
        title: "📉 Gráficos de Tendência",
        content: "Acompanhe a evolução de vendas, leads e engajamento ao longo do tempo.",
        target: ".chart-container, .recharts-wrapper",
        position: "top",
        page: "/",
      },
    ],
  },

  // ========== TUTORIAL: BUSCA DE PRODUTOS ==========
  {
    id: "search-tutorial",
    name: "Busca de Produtos",
    description: "Encontre produtos vencedores",
    triggerOnPage: "/search",
    steps: [
      {
        id: "search-intro",
        title: "🔍 Busca Inteligente",
        content: "Encontre produtos virais do TikTok Shop, AliExpress e outras plataformas. Use filtros avançados para refinar.",
        position: "center",
        page: "/search",
      },
      {
        id: "search-bar",
        title: "🔎 Barra de Busca",
        content: "Digite palavras-chave, categorias ou até links de produtos. A IA entende o que você procura.",
        target: "input[type='search'], input[placeholder*='busca'], .search-input",
        position: "bottom",
        page: "/search",
      },
      {
        id: "search-filters",
        title: "⚡ Filtros Avançados",
        content: "Filtre por preço, avaliação, vendas, categoria e muito mais. Combine filtros para resultados precisos.",
        target: ".filters-container, [data-testid='filters']",
        position: "right",
        page: "/search",
      },
      {
        id: "search-results",
        title: "📦 Resultados",
        content: "Cada produto mostra: preço, avaliação, vendas e potencial de lucro. Clique para ver detalhes ou adicionar aos favoritos.",
        target: ".product-grid, .products-list",
        position: "top",
        page: "/search",
      },
    ],
  },

  // ========== TUTORIAL: COLETA ==========
  {
    id: "coleta-tutorial",
    name: "Coleta de Produtos",
    description: "Extraia produtos automaticamente",
    triggerOnPage: "/coleta",
    steps: [
      {
        id: "coleta-intro",
        title: "📥 Coleta Automatizada",
        content: "Extraia produtos em massa de URLs, perfis ou categorias. Ideal para alimentar seu catálogo rapidamente.",
        position: "center",
        page: "/coleta",
      },
      {
        id: "coleta-url",
        title: "🔗 Cole URLs",
        content: "Cole links de produtos, lojas ou categorias. Suportamos TikTok Shop, AliExpress, Shopee e mais.",
        target: "textarea, .url-input",
        position: "bottom",
        page: "/coleta",
      },
      {
        id: "coleta-start",
        title: "▶️ Iniciar Coleta",
        content: "Clique para começar a extração. O progresso aparece em tempo real com estimativa de conclusão.",
        target: "button[type='submit'], .start-button",
        position: "top",
        page: "/coleta",
      },
    ],
  },

  // ========== TUTORIAL: WHATSAPP ==========
  {
    id: "whatsapp-tutorial",
    name: "WhatsApp Automation",
    description: "Automatize seu atendimento",
    triggerOnPage: "/whatsapp",
    steps: [
      {
        id: "whats-intro",
        title: "💬 WhatsApp Business",
        content: "Conecte seu WhatsApp e automatize atendimento, envio de catálogos e follow-up de vendas.",
        position: "center",
        page: "/whatsapp",
      },
      {
        id: "whats-connect",
        title: "📱 Conectar WhatsApp",
        content: "Escaneie o QR Code com seu WhatsApp para conectar. A conexão é segura e criptografada.",
        target: ".qr-code, [data-testid='qr-code']",
        position: "bottom",
        page: "/whatsapp",
      },
      {
        id: "whats-conversations",
        title: "💭 Conversas",
        content: "Veja todas as conversas em um só lugar. O bot responde automaticamente ou transfira para atendimento humano.",
        target: ".conversations-list, .chat-list",
        position: "right",
        page: "/whatsapp",
      },
      {
        id: "whats-bot",
        title: "🤖 Bot Inteligente",
        content: "O chatbot responde perguntas, envia produtos e qualifica leads automaticamente.",
        target: ".bot-toggle, [data-testid='bot-toggle']",
        position: "left",
        page: "/whatsapp",
      },
    ],
  },

  // ========== TUTORIAL: COPY AI ==========
  {
    id: "copy-tutorial",
    name: "Copy AI",
    description: "Gere copies com inteligência artificial",
    triggerOnPage: "/copy",
    steps: [
      {
        id: "copy-intro",
        title: "✍️ Copy AI",
        content: "Gere textos persuasivos para anúncios, posts e descrições usando inteligência artificial.",
        position: "center",
        page: "/copy",
      },
      {
        id: "copy-select",
        title: "📦 Selecione um Produto",
        content: "Escolha um produto dos seus favoritos ou cole uma URL. A IA analisa e cria copies otimizados.",
        target: ".product-selector, [data-testid='product-select']",
        position: "bottom",
        page: "/copy",
      },
      {
        id: "copy-types",
        title: "📝 Tipos de Copy",
        content: "Escolha o tipo: anúncio, descrição, post para redes sociais, email marketing e mais.",
        target: ".copy-types, .type-selector",
        position: "right",
        page: "/copy",
      },
      {
        id: "copy-generate",
        title: "⚡ Gerar Copy",
        content: "Clique para gerar. Cada geração usa créditos IA. Você pode regenerar ou editar o resultado.",
        target: "button[type='submit'], .generate-button",
        position: "top",
        page: "/copy",
      },
      {
        id: "copy-credits",
        title: "💎 Créditos IA",
        content: "Copies simples usam 1 crédito, análises 2 créditos. Compre mais créditos no menu lateral.",
        position: "center",
        page: "/copy",
      },
    ],
  },

  // ========== TUTORIAL: CRM ==========
  {
    id: "crm-tutorial",
    name: "CRM & Pipeline",
    description: "Gerencie seus leads e vendas",
    triggerOnPage: "/crm",
    steps: [
      {
        id: "crm-intro",
        title: "💼 CRM de Vendas",
        content: "Gerencie todo seu funil de vendas. Acompanhe leads desde o primeiro contato até a conversão.",
        position: "center",
        page: "/crm",
      },
      {
        id: "crm-pipeline",
        title: "📊 Pipeline Visual",
        content: "Arraste cards entre colunas para mover leads no funil. Personalize etapas conforme seu processo.",
        target: ".pipeline-board, .kanban-board",
        position: "top",
        page: "/crm",
      },
      {
        id: "crm-lead",
        title: "👤 Detalhes do Lead",
        content: "Clique em um lead para ver histórico completo: conversas, produtos vistos e próximos passos.",
        target: ".lead-card, .contact-card",
        position: "right",
        page: "/crm",
      },
    ],
  },

  // ========== TUTORIAL: SOCIAL SUITE ==========
  {
    id: "social-tutorial",
    name: "Social Suite",
    description: "Gerencie suas redes sociais",
    triggerOnPage: "/social",
    steps: [
      {
        id: "social-intro",
        title: "📱 Central de Redes Sociais",
        content: "Gerencie Instagram, TikTok e YouTube em um só lugar. Agende posts, analise métricas e cresça sua audiência.",
        position: "center",
        page: "/social",
      },
      {
        id: "social-accounts",
        title: "🔗 Contas Conectadas",
        content: "Conecte suas contas de redes sociais. Suportamos múltiplas contas por plataforma.",
        target: ".accounts-list, .connected-accounts",
        position: "bottom",
        page: "/social",
      },
      {
        id: "social-schedule",
        title: "📅 Agendamento",
        content: "Agende posts para horários de maior engajamento. A IA sugere os melhores horários.",
        target: ".scheduler, .calendar",
        position: "right",
        page: "/social",
      },
      {
        id: "social-analytics",
        title: "📊 Analytics",
        content: "Acompanhe seguidores, engajamento e crescimento. Compare performance entre plataformas.",
        target: ".analytics-cards, .metrics",
        position: "top",
        page: "/social",
      },
    ],
  },

  // ========== TUTORIAL: SELLER BOT ==========
  {
    id: "seller-bot-tutorial",
    name: "Seller Bot",
    description: "Automação de vendas avançada",
    triggerOnPage: "/seller-bot",
    steps: [
      {
        id: "bot-intro",
        title: "🤖 Seller Bot Premium",
        content: "Automatize todo seu processo de vendas com IA. Do primeiro contato ao pós-venda.",
        position: "center",
        page: "/seller-bot",
      },
      {
        id: "bot-flows",
        title: "🔄 Fluxos de Automação",
        content: "Configure sequências: boas-vindas, carrinho abandonado, follow-up e cross-sell.",
        target: ".flows-list, .automations",
        position: "right",
        page: "/seller-bot",
      },
      {
        id: "bot-triggers",
        title: "⚡ Gatilhos Inteligentes",
        content: "O bot age baseado em comportamento: visita produto, abandona carrinho, não responde há X dias.",
        target: ".triggers, .conditions",
        position: "bottom",
        page: "/seller-bot",
      },
    ],
  },

  // ========== TUTORIAL: CONFIGURAÇÕES ==========
  {
    id: "settings-tutorial",
    name: "Configurações",
    description: "Personalize sua experiência",
    triggerOnPage: "/settings",
    steps: [
      {
        id: "settings-intro",
        title: "⚙️ Configurações",
        content: "Personalize o TikTrend do seu jeito. Tema, idioma, notificações e integrações.",
        position: "center",
        page: "/settings",
      },
      {
        id: "settings-theme",
        title: "🎨 Aparência",
        content: "Escolha entre tema claro, escuro ou automático (segue o sistema).",
        target: ".theme-selector, [data-testid='theme']",
        position: "bottom",
        page: "/settings",
      },
      {
        id: "settings-notifications",
        title: "🔔 Notificações",
        content: "Configure alertas de preço, novos leads, mensagens do WhatsApp e mais.",
        target: ".notifications-settings",
        position: "right",
        page: "/settings",
      },
      {
        id: "settings-integrations",
        title: "🔌 Integrações",
        content: "Conecte com plataformas externas: Shopify, WooCommerce, Mercado Livre e mais.",
        target: ".integrations-list",
        position: "top",
        page: "/settings",
      },
    ],
  },
];

// ============================================
// PROVIDER
// ============================================

export const TutorialProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isActive, setIsActive] = useState(false);
  const [currentTutorial, setCurrentTutorial] = useState<Tutorial | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedTutorials, setCompletedTutorials] = useState<string[]>([]);

  // Load completed tutorials from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("completed_tutorials");
    if (saved) {
      setCompletedTutorials(JSON.parse(saved));
    }
  }, []);

  // Save completed tutorials
  useEffect(() => {
    localStorage.setItem("completed_tutorials", JSON.stringify(completedTutorials));
  }, [completedTutorials]);

  const startTutorial = useCallback((tutorialId: string) => {
    const tutorial = TUTORIALS.find((t) => t.id === tutorialId);
    if (tutorial) {
      setCurrentTutorial(tutorial);
      setCurrentStepIndex(0);
      setIsActive(true);
    }
  }, []);

  const endTutorial = useCallback(() => {
    if (currentTutorial) {
      setCompletedTutorials((prev) => 
        prev.includes(currentTutorial.id) ? prev : [...prev, currentTutorial.id]
      );
    }
    setIsActive(false);
    setCurrentTutorial(null);
    setCurrentStepIndex(0);
  }, [currentTutorial]);

  const nextStep = useCallback(() => {
    if (currentTutorial && currentStepIndex < currentTutorial.steps.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    } else {
      endTutorial();
    }
  }, [currentTutorial, currentStepIndex, endTutorial]);

  const prevStep = useCallback(() => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  }, [currentStepIndex]);

  const skipTutorial = useCallback(() => {
    endTutorial();
  }, [endTutorial]);

  const markCompleted = useCallback((tutorialId: string) => {
    setCompletedTutorials((prev) => 
      prev.includes(tutorialId) ? prev : [...prev, tutorialId]
    );
  }, []);

  const resetTutorials = useCallback(() => {
    setCompletedTutorials([]);
    localStorage.removeItem("completed_tutorials");
  }, []);

  const getTutorialProgress = useCallback(() => ({
    current: currentStepIndex + 1,
    total: currentTutorial?.steps.length || 0,
  }), [currentStepIndex, currentTutorial]);

  const isStepVisible = useCallback((stepId: string) => {
    return currentTutorial?.steps[currentStepIndex]?.id === stepId;
  }, [currentTutorial, currentStepIndex]);

  return (
    <TutorialContext.Provider
      value={{
        isActive,
        currentTutorial,
        currentStepIndex,
        completedTutorials,
        startTutorial,
        endTutorial,
        nextStep,
        prevStep,
        skipTutorial,
        markCompleted,
        resetTutorials,
        getTutorialProgress,
        isStepVisible,
      }}
    >
      {children}
      <TutorialOverlay />
    </TutorialContext.Provider>
  );
};

// ============================================
// OVERLAY COMPONENT
// ============================================

const TutorialOverlay: React.FC = () => {
  const context = useContext(TutorialContext);
  if (!context) return null;

  const {
    isActive,
    currentTutorial,
    currentStepIndex,
    nextStep,
    prevStep,
    skipTutorial,
    getTutorialProgress,
  } = context;

  if (!isActive || !currentTutorial) return null;

  const currentStep = currentTutorial.steps[currentStepIndex];
  const progress = getTutorialProgress();
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === currentTutorial.steps.length - 1;

  // Get target element position for spotlight
  const [targetRect, setTargetRect] = React.useState<DOMRect | null>(null);

  React.useEffect(() => {
    if (currentStep.target) {
      const element = document.querySelector(currentStep.target);
      if (element) {
        const rect = element.getBoundingClientRect();
        setTargetRect(rect);
        element.scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        setTargetRect(null);
      }
    } else {
      setTargetRect(null);
    }
  }, [currentStep]);

  // Calculate tooltip position
  const getTooltipPosition = () => {
    if (!targetRect || currentStep.position === "center") {
      return {
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
      };
    }

    const padding = 20;
    const tooltipWidth = 380;
    const tooltipHeight = 200;

    switch (currentStep.position) {
      case "top":
        return {
          top: `${targetRect.top - tooltipHeight - padding}px`,
          left: `${targetRect.left + targetRect.width / 2}px`,
          transform: "translateX(-50%)",
        };
      case "bottom":
        return {
          top: `${targetRect.bottom + padding}px`,
          left: `${targetRect.left + targetRect.width / 2}px`,
          transform: "translateX(-50%)",
        };
      case "left":
        return {
          top: `${targetRect.top + targetRect.height / 2}px`,
          left: `${targetRect.left - tooltipWidth - padding}px`,
          transform: "translateY(-50%)",
        };
      case "right":
        return {
          top: `${targetRect.top + targetRect.height / 2}px`,
          left: `${targetRect.right + padding}px`,
          transform: "translateY(-50%)",
        };
      default:
        return {
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
        };
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] pointer-events-none"
      >
        {/* SVG Mask for spotlight effect - no blur on highlighted area */}
        <svg className="absolute inset-0 w-full h-full">
          <defs>
            <mask id="spotlight-mask">
              {/* White = visible (darkened), Black = hidden (clear) */}
              <rect x="0" y="0" width="100%" height="100%" fill="white" />
              {targetRect && (
                <rect
                  x={targetRect.left - 8}
                  y={targetRect.top - 8}
                  width={targetRect.width + 16}
                  height={targetRect.height + 16}
                  rx="8"
                  fill="black"
                />
              )}
            </mask>
          </defs>
          {/* Dark overlay with mask cutout */}
          <rect
            x="0"
            y="0"
            width="100%"
            height="100%"
            fill="rgba(0, 0, 0, 0.85)"
            mask="url(#spotlight-mask)"
          />
        </svg>

        {/* Highlight ring around target */}
        {targetRect && (
          <div
            className="absolute rounded-lg ring-4 ring-primary/80 ring-offset-4 ring-offset-background/50 pointer-events-none"
            style={{
              top: targetRect.top - 8,
              left: targetRect.left - 8,
              width: targetRect.width + 16,
              height: targetRect.height + 16,
              zIndex: 102,
            }}
          />
        )}

        {/* Tooltip Card */}
        <motion.div
          key={currentStep.id}
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          transition={{ duration: 0.2 }}
          className={cn(
            "absolute w-[380px] max-w-[90vw] z-[103]",
            "bg-card border border-border rounded-xl shadow-2xl",
            "overflow-hidden pointer-events-auto"
          )}
          style={getTooltipPosition()}
        >
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-primary/20 via-primary/10 to-transparent p-4 border-b border-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {currentStep.icon && (
                  <div className="p-2 rounded-lg bg-primary/10">
                    {currentStep.icon}
                  </div>
                )}
                <div>
                  <h3 className="font-semibold text-foreground">
                    {currentStep.title}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Passo {progress.current} de {progress.total}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 rounded-full hover:bg-destructive/10 hover:text-destructive"
                onClick={skipTutorial}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="p-4">
            <p className="text-sm text-muted-foreground leading-relaxed">
              {currentStep.content}
            </p>

            {currentStep.action && (
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={currentStep.action.onClick}
              >
                {currentStep.action.label}
              </Button>
            )}
          </div>

          {/* Progress bar */}
          <div className="px-4 pb-2">
            <div className="h-1 bg-muted rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-primary to-primary/60"
                initial={{ width: 0 }}
                animate={{ width: `${(progress.current / progress.total) * 100}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-4 pt-2 border-t border-border/50">
            <Button
              variant="ghost"
              size="sm"
              onClick={skipTutorial}
              className="text-muted-foreground hover:text-foreground"
            >
              <SkipForward className="h-4 w-4 mr-1" />
              Pular
            </Button>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={prevStep}
                disabled={isFirstStep}
              >
                <ChevronLeft className="h-4 w-4" />
                Voltar
              </Button>
              <Button
                size="sm"
                onClick={nextStep}
                className="bg-primary hover:bg-primary/90"
              >
                {isLastStep ? "Concluir" : "Próximo"}
                {!isLastStep && <ChevronRight className="h-4 w-4 ml-1" />}
              </Button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// ============================================
// HOOK
// ============================================

export const useTutorial = () => {
  const context = useContext(TutorialContext);
  if (!context) {
    throw new Error("useTutorial must be used within TutorialProvider");
  }
  return context;
};

export default TutorialProvider;
