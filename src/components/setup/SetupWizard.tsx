import * as React from "react";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TikTrendLogo } from "@/components/icons";
import { useUserStore } from "@/stores";
import { useNavigate } from "react-router-dom";
import type { AppSettings } from "@/types";
import { SUPPORTED_LANGUAGES, changeLanguage, type SupportedLanguage } from "@/lib/i18n";
import { 
  ChevronRight, 
  ChevronLeft, 
  Sparkles, 
  Shield, 
  Key, 
  Palette, 
  Rocket,
  Check,
  Globe,
  Moon,
  Sun,
  Monitor,
  Zap,
  Gift,
  Crown,
  MessageCircle,
  BarChart3,
  Bot,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Check if running in Tauri
const isTauri = typeof window !== 'undefined' && '__TAURI__' in window;

// Safe invoke wrapper that works in browser too
const safeInvoke = async <T,>(cmd: string, args?: Record<string, unknown>): Promise<T> => {
  if (isTauri) {
    const { invoke } = await import("@tauri-apps/api/core");
    return invoke<T>(cmd, args);
  }
  // Browser fallback - use localStorage
  if (cmd === "get_settings") {
    const stored = localStorage.getItem("app_settings");
    return (stored ? JSON.parse(stored) : {
      setupComplete: false,
      theme: "dark",
      language: "pt-BR",
      notificationsEnabled: true,
      autoUpdate: true,
      termsAccepted: false,
      termsAcceptedAt: null,
      license: { key: null, plan: "trial", isActive: true, credits: 0 },
      system: { autoUpdate: true, logsEnabled: true, analyticsEnabled: false }
    }) as T;
  }
  if (cmd === "save_settings" && args?.settings) {
    localStorage.setItem("app_settings", JSON.stringify(args.settings));
    return {} as T;
  }
  throw new Error(`Unknown command: ${cmd}`);
};

// ============================================
// TYPES
// ============================================

interface Step {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ReactNode;
}

const steps: Step[] = [
  { 
    id: "welcome", 
    title: "Bem-vindo", 
    subtitle: "Conheça o TikTrend",
    icon: <Sparkles className="w-5 h-5" />,
  },
  { 
    id: "features", 
    title: "Funcionalidades", 
    subtitle: "O que você pode fazer",
    icon: <Zap className="w-5 h-5" />,
  },
  { 
    id: "responsibility", 
    title: "Termos", 
    subtitle: "Aceite os termos",
    icon: <Shield className="w-5 h-5" />,
  },
  { 
    id: "license", 
    title: "Licença", 
    subtitle: "Ative sua conta",
    icon: <Key className="w-5 h-5" />,
  },
  { 
    id: "preferences", 
    title: "Preferências", 
    subtitle: "Personalize",
    icon: <Palette className="w-5 h-5" />,
  },
  { 
    id: "finish", 
    title: "Pronto!", 
    subtitle: "Vamos começar",
    icon: <Rocket className="w-5 h-5" />,
  },
];

// ============================================
// MAIN COMPONENT
// ============================================

export const SetupWizard: React.FC = () => {
  const { i18n } = useTranslation();
  const [currentStep, setCurrentStep] = React.useState(0);
  const [licenseKey, setLicenseKey] = React.useState("");
  const [acceptedTerms, setAcceptedTerms] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(true);
  const [selectedLanguage, setSelectedLanguage] = React.useState<SupportedLanguage>(
    i18n.language as SupportedLanguage || "pt-BR"
  );
  const { theme, setTheme } = useUserStore();
  const navigate = useNavigate();

  // Handle language change
  const handleLanguageSelect = async (lang: SupportedLanguage) => {
    setSelectedLanguage(lang);
    await changeLanguage(lang);
  };

  // Check if setup is already complete
  React.useEffect(() => {
    const checkSetupStatus = async () => {
      try {
        const settings = await safeInvoke<AppSettings>("get_settings");
        if (settings.setupComplete) {
          navigate("/", { replace: true });
          return;
        }
      } catch (error) {
        console.error("Failed to check setup status:", error);
      }
      setIsLoading(false);
    };

    checkSetupStatus();
  }, [navigate]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      if (steps[currentStep].id === "responsibility" && !acceptedTerms) {
        return;
      }
      setCurrentStep(currentStep + 1);
    } else {
      handleFinish();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleFinish = async () => {
    try {
      const currentSettings = await safeInvoke<AppSettings>("get_settings");
      const now = new Date().toISOString();

      const newSettings: AppSettings = {
        ...currentSettings,
        theme: theme,
        language: selectedLanguage,
        notificationsEnabled: true,
        autoUpdate: true,
        setupComplete: true,
        termsAccepted: acceptedTerms,
        termsAcceptedAt: acceptedTerms ? now : null,
        license: {
          ...currentSettings.license,
          key: licenseKey || null,
          plan: licenseKey ? "lifetime" : "trial",
          isActive: true,
          credits: 0,
          trialStarted: licenseKey ? null : now,
        },
        system: {
          ...currentSettings.system,
          autoUpdate: true,
          logsEnabled: true,
          analyticsEnabled: false,
        },
      };

      await safeInvoke("save_settings", { settings: newSettings });
      localStorage.removeItem('tutorial_completed');
      navigate("/");
    } catch (error) {
      console.error("Setup failed:", error);
    }
  };

  const canProceed = () => {
    if (steps[currentStep].id === "responsibility" && !acceptedTerms) {
      return false;
    }
    return true;
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <TikTrendLogo size={48} />
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
            <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
            <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left Panel - Progress */}
      <div className="hidden lg:flex w-80 bg-card border-r border-border flex-col p-6">
        <div className="flex items-center gap-3 mb-10">
          <TikTrendLogo size={36} />
          <span className="text-xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            TikTrend
          </span>
        </div>

        {/* Steps Progress */}
        <div className="flex-1 space-y-2">
          {steps.map((step, index) => (
            <motion.div
              key={step.id}
              initial={false}
              animate={{
                opacity: index <= currentStep ? 1 : 0.5,
              }}
              className={cn(
                "flex items-center gap-4 p-3 rounded-lg transition-colors",
                index === currentStep && "bg-primary/10 border border-primary/20",
                index < currentStep && "text-muted-foreground"
              )}
            >
              <div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center transition-colors",
                  index === currentStep && "bg-primary text-primary-foreground",
                  index < currentStep && "bg-green-500/20 text-green-500",
                  index > currentStep && "bg-muted text-muted-foreground"
                )}
              >
                {index < currentStep ? (
                  <Check className="w-5 h-5" />
                ) : (
                  step.icon
                )}
              </div>
              <div>
                <p className={cn(
                  "font-medium text-sm",
                  index === currentStep && "text-foreground",
                  index !== currentStep && "text-muted-foreground"
                )}>
                  {step.title}
                </p>
                <p className="text-xs text-muted-foreground">{step.subtitle}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Bottom info */}
        <div className="pt-6 border-t border-border">
          <p className="text-xs text-muted-foreground text-center">
            Passo {currentStep + 1} de {steps.length}
          </p>
        </div>
      </div>

      {/* Right Panel - Content */}
      <div className="flex-1 flex flex-col">
        {/* Mobile Header */}
        <div className="lg:hidden flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <TikTrendLogo size={28} />
            <span className="font-semibold text-primary">TikTrend</span>
          </div>
          <span className="text-sm text-muted-foreground">
            {currentStep + 1}/{steps.length}
          </span>
        </div>

        {/* Progress bar mobile */}
        <div className="lg:hidden h-1 bg-muted">
          <motion.div
            className="h-full bg-gradient-to-r from-primary to-primary/60"
            initial={{ width: 0 }}
            animate={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
          <div className="w-full max-w-2xl">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                {renderStepContent(
                  steps[currentStep].id,
                  {
                    acceptedTerms,
                    setAcceptedTerms,
                    licenseKey,
                    setLicenseKey,
                    selectedLanguage,
                    handleLanguageSelect,
                    theme,
                    setTheme,
                  }
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-border p-4 lg:p-6">
          <div className="max-w-2xl mx-auto flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={handlePrev}
              disabled={currentStep === 0}
              className="gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Voltar</span>
            </Button>

            <div className="flex items-center gap-2">
              {currentStep < steps.length - 1 && (
                <Button
                  variant="ghost"
                  onClick={() => setCurrentStep(steps.length - 1)}
                  className="text-muted-foreground text-sm"
                >
                  Pular
                </Button>
              )}
              <Button
                onClick={handleNext}
                disabled={!canProceed()}
                className="gap-2 bg-primary hover:bg-primary/90 min-w-[120px]"
              >
                {currentStep === steps.length - 1 ? (
                  <>
                    <Rocket className="w-4 h-4" />
                    Começar
                  </>
                ) : (
                  <>
                    Próximo
                    <ChevronRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================
// STEP CONTENT RENDERER
// ============================================

interface StepProps {
  acceptedTerms: boolean;
  setAcceptedTerms: (v: boolean) => void;
  licenseKey: string;
  setLicenseKey: (v: string) => void;
  selectedLanguage: SupportedLanguage;
  handleLanguageSelect: (lang: SupportedLanguage) => void;
  theme: string;
  setTheme: (v: "light" | "dark" | "system") => void;
}

function renderStepContent(stepId: string, props: StepProps) {
  switch (stepId) {
    case "welcome":
      return <WelcomeStep />;
    case "features":
      return <FeaturesStep />;
    case "responsibility":
      return <ResponsibilityStep {...props} />;
    case "license":
      return <LicenseStep {...props} />;
    case "preferences":
      return <PreferencesStep {...props} />;
    case "finish":
      return <FinishStep />;
    default:
      return null;
  }
}

// ============================================
// INDIVIDUAL STEPS
// ============================================

const WelcomeStep: React.FC = () => (
  <div className="text-center space-y-6">
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: "spring", duration: 0.6 }}
      className="w-24 h-24 mx-auto rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center"
    >
      <TikTrendLogo size={56} />
    </motion.div>
    
    <div className="space-y-2">
      <h1 className="text-3xl lg:text-4xl font-bold">
        Bem-vindo ao{" "}
        <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
          TikTrend
        </span>
      </h1>
      <p className="text-lg text-muted-foreground max-w-md mx-auto">
        Sua plataforma completa para encontrar produtos vencedores e automatizar suas vendas.
      </p>
    </div>

    <div className="grid grid-cols-3 gap-4 max-w-md mx-auto pt-4">
      {[
        { icon: Search, label: "Busca Inteligente" },
        { icon: Bot, label: "Automação" },
        { icon: BarChart3, label: "Analytics" },
      ].map((item, i) => (
        <motion.div
          key={item.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 + i * 0.1 }}
          className="p-4 rounded-xl bg-card border border-border text-center"
        >
          <item.icon className="w-6 h-6 mx-auto text-primary mb-2" />
          <p className="text-xs text-muted-foreground">{item.label}</p>
        </motion.div>
      ))}
    </div>
  </div>
);

const FeaturesStep: React.FC = () => (
  <div className="space-y-6">
    <div className="text-center space-y-2">
      <h2 className="text-2xl lg:text-3xl font-bold">O que você pode fazer</h2>
      <p className="text-muted-foreground">
        Conheça as principais funcionalidades do TikTrend
      </p>
    </div>

    <div className="grid sm:grid-cols-2 gap-4">
      {[
        {
          icon: Search,
          title: "Busca de Produtos",
          description: "Encontre produtos virais do TikTok Shop, AliExpress e mais.",
          color: "text-blue-500",
          bg: "bg-blue-500/10",
        },
        {
          icon: MessageCircle,
          title: "WhatsApp Automation",
          description: "Chatbot inteligente para atendimento e vendas 24/7.",
          color: "text-green-500",
          bg: "bg-green-500/10",
        },
        {
          icon: Bot,
          title: "Seller Bot",
          description: "Automação completa: follow-up, carrinho abandonado, cross-sell.",
          color: "text-purple-500",
          bg: "bg-purple-500/10",
        },
        {
          icon: BarChart3,
          title: "CRM & Pipeline",
          description: "Gerencie leads e acompanhe cada oportunidade de venda.",
          color: "text-orange-500",
          bg: "bg-orange-500/10",
        },
      ].map((feature, i) => (
        <motion.div
          key={feature.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="p-5 rounded-xl bg-card border border-border hover:border-primary/30 transition-colors"
        >
          <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center mb-3", feature.bg)}>
            <feature.icon className={cn("w-5 h-5", feature.color)} />
          </div>
          <h3 className="font-semibold mb-1">{feature.title}</h3>
          <p className="text-sm text-muted-foreground">{feature.description}</p>
        </motion.div>
      ))}
    </div>
  </div>
);

const ResponsibilityStep: React.FC<Pick<StepProps, "acceptedTerms" | "setAcceptedTerms">> = ({
  acceptedTerms,
  setAcceptedTerms,
}) => (
  <div className="space-y-6">
    <div className="text-center space-y-2">
      <div className="w-16 h-16 mx-auto rounded-full bg-amber-500/10 flex items-center justify-center mb-4">
        <Shield className="w-8 h-8 text-amber-500" />
      </div>
      <h2 className="text-2xl lg:text-3xl font-bold">Termo de Responsabilidade</h2>
      <p className="text-muted-foreground">
        Para usar o TikTrend, você precisa concordar com nossas práticas
      </p>
    </div>

    <div className="bg-card rounded-xl border border-border p-6 space-y-4">
      {[
        "O scraping é limitado para evitar bloqueios (1 requisição a cada 5-10 segundos)",
        "O software se identifica de forma transparente como TikTrend",
        "Você é responsável pelo uso ético, respeitando os termos das plataformas",
        "Dados coletados são usados apenas para sua análise pessoal",
      ].map((term, i) => (
        <div key={i} className="flex items-start gap-3">
          <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
            <span className="text-xs font-bold text-primary">{i + 1}</span>
          </div>
          <p className="text-sm text-muted-foreground">{term}</p>
        </div>
      ))}
    </div>

    <label className="flex items-center gap-3 cursor-pointer p-4 rounded-xl bg-card border border-border hover:border-primary/30 transition-colors">
      <input
        type="checkbox"
        checked={acceptedTerms}
        onChange={(e) => setAcceptedTerms(e.target.checked)}
        className="w-5 h-5 rounded border-2 border-primary text-primary focus:ring-primary"
      />
      <span className="text-sm">
        Li e concordo com os termos de responsabilidade e uso ético
      </span>
    </label>
  </div>
);

const LicenseStep: React.FC<Pick<StepProps, "licenseKey" | "setLicenseKey">> = ({
  licenseKey,
  setLicenseKey,
}) => (
  <div className="space-y-6">
    <div className="text-center space-y-2">
      <h2 className="text-2xl lg:text-3xl font-bold">Licença & Créditos</h2>
      <p className="text-muted-foreground">
        Seu acesso funciona assim
      </p>
    </div>

    {/* License Key Input */}
    <div className="space-y-2">
      <label className="text-sm font-medium">Chave de Licença (opcional)</label>
      <Input
        placeholder="XXXX-XXXX-XXXX-XXXX"
        value={licenseKey}
        onChange={(e) => setLicenseKey(e.target.value)}
        className="text-center text-lg tracking-wider"
      />
    </div>

    <div className="grid sm:grid-cols-2 gap-4">
      {/* Lifetime License */}
      <div className="p-5 rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20">
        <div className="flex items-center gap-2 mb-3">
          <Crown className="w-5 h-5 text-primary" />
          <span className="font-semibold">Licença Vitalícia</span>
        </div>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li className="flex items-center gap-2">
            <Check className="w-4 h-4 text-green-500" />
            Buscas ilimitadas para sempre
          </li>
          <li className="flex items-center gap-2">
            <Check className="w-4 h-4 text-green-500" />
            Todos os filtros avançados
          </li>
          <li className="flex items-center gap-2">
            <Check className="w-4 h-4 text-green-500" />
            Exportação completa
          </li>
          <li className="flex items-center gap-2">
            <Check className="w-4 h-4 text-green-500" />
            Atualizações gratuitas
          </li>
        </ul>
      </div>

      {/* AI Credits */}
      <div className="p-5 rounded-xl bg-card border border-border">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-5 h-5 text-purple-500" />
          <span className="font-semibold">Créditos IA</span>
        </div>
        <p className="text-sm text-muted-foreground mb-3">
          Para gerar copies e análises
        </p>
        <ul className="space-y-1 text-xs text-muted-foreground">
          <li>• Copy simples: 1 crédito</li>
          <li>• Análise de tendência: 2 créditos</li>
          <li>• Lote de copies: 5 créditos</li>
        </ul>
        <p className="text-xs text-muted-foreground mt-3 italic">
          Compre no menu Perfil
        </p>
      </div>
    </div>

    {/* Trial info */}
    <div className="p-4 rounded-xl bg-muted/30 border border-dashed border-border text-center">
      <Gift className="w-6 h-6 mx-auto text-muted-foreground mb-2" />
      <p className="text-sm font-medium">Sem licença? Teste grátis por 7 dias</p>
      <p className="text-xs text-muted-foreground">50 produtos por busca • Funcionalidades básicas</p>
    </div>
  </div>
);

const PreferencesStep: React.FC<Pick<StepProps, "selectedLanguage" | "handleLanguageSelect" | "theme" | "setTheme">> = ({
  selectedLanguage,
  handleLanguageSelect,
  theme,
  setTheme,
}) => (
  <div className="space-y-8">
    <div className="text-center space-y-2">
      <h2 className="text-2xl lg:text-3xl font-bold">Preferências</h2>
      <p className="text-muted-foreground">
        Personalize sua experiência
      </p>
    </div>

    {/* Language */}
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Globe className="w-5 h-5 text-primary" />
        <span className="font-medium">Idioma</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {SUPPORTED_LANGUAGES.map((lang) => (
          <Button
            key={lang.code}
            variant={selectedLanguage === lang.code ? "default" : "outline"}
            size="sm"
            onClick={() => handleLanguageSelect(lang.code)}
            className={cn(
              "gap-2",
              selectedLanguage === lang.code && "bg-primary hover:bg-primary/90"
            )}
          >
            {lang.flag} {lang.name}
          </Button>
        ))}
      </div>
    </div>

    {/* Theme */}
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Palette className="w-5 h-5 text-primary" />
        <span className="font-medium">Tema</span>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {[
          { id: "light", label: "Claro", icon: Sun },
          { id: "dark", label: "Escuro", icon: Moon },
          { id: "system", label: "Sistema", icon: Monitor },
        ].map((option) => (
          <button
            key={option.id}
            onClick={() => setTheme(option.id as "light" | "dark" | "system")}
            className={cn(
              "p-4 rounded-xl border transition-all text-center",
              theme === option.id
                ? "border-primary bg-primary/10"
                : "border-border bg-card hover:border-primary/30"
            )}
          >
            <option.icon className={cn(
              "w-6 h-6 mx-auto mb-2",
              theme === option.id ? "text-primary" : "text-muted-foreground"
            )} />
            <span className="text-sm">{option.label}</span>
          </button>
        ))}
      </div>
    </div>
  </div>
);

const FinishStep: React.FC = () => (
  <div className="text-center space-y-6">
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: "spring", duration: 0.6 }}
      className="text-6xl"
    >
      🎉
    </motion.div>
    
    <div className="space-y-2">
      <h2 className="text-3xl font-bold">Tudo Pronto!</h2>
      <p className="text-muted-foreground">
        O TikTrend está configurado e pronto para usar
      </p>
    </div>

    <div className="bg-card rounded-xl border border-border p-6 text-left max-w-md mx-auto">
      <p className="font-semibold mb-4 flex items-center gap-2">
        <Rocket className="w-5 h-5 text-primary" />
        Próximos passos:
      </p>
      <div className="space-y-3">
        {[
          "Faça sua primeira busca de produtos",
          "Salve os melhores nos favoritos",
          "Conecte seu WhatsApp",
          "Use a Copy AI para criar anúncios",
        ].map((step, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-primary">{i + 1}</span>
            </div>
            <span className="text-sm text-muted-foreground">{step}</span>
          </div>
        ))}
      </div>
    </div>

    <p className="text-sm text-muted-foreground">
      Um tutorial interativo vai te guiar após clicar em "Começar"
    </p>
  </div>
);

export default SetupWizard;
