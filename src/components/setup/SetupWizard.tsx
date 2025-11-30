import * as React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { TikTrendLogo } from "@/components/icons";
import { useUserStore } from "@/stores";
import { useNavigate } from "react-router-dom";
import { invoke } from "@tauri-apps/api/core";
import type { AppSettings } from "@/types";
import { SUPPORTED_LANGUAGES, changeLanguage, type SupportedLanguage } from "@/lib/i18n";

const steps = [
  { id: "welcome", title: "Bem-vindo" },
  { id: "responsibility", title: "Responsabilidade" },
  { id: "license", title: "Licença" },
  { id: "preferences", title: "Preferências" },
  { id: "finish", title: "Concluir" },
];

export const SetupWizard: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [currentStep, setCurrentStep] = React.useState(0);
  const [licenseKey, setLicenseKey] = React.useState("");
  const [acceptedTerms, setAcceptedTerms] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(true);
  const [selectedLanguage, setSelectedLanguage] = React.useState<SupportedLanguage>(i18n.language as SupportedLanguage || "pt-BR");
  const { theme, setTheme } = useUserStore();
  const navigate = useNavigate();

  // Handle language change
  const handleLanguageSelect = async (lang: SupportedLanguage) => {
    setSelectedLanguage(lang);
    await changeLanguage(lang);
  };

  // Check if setup is already complete - redirect if so
  React.useEffect(() => {
    const checkSetupStatus = async () => {
      try {
        const settings = await invoke<AppSettings>("get_settings");
        if (settings.setupComplete) {
          // Setup already done, redirect to home
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
        return; // Block if terms not accepted
      }
      setCurrentStep(currentStep + 1);
    } else {
      handleFinish();
    }
  };

  const handleFinish = async () => {
    try {
      // Get current defaults
      const currentSettings = await invoke<AppSettings>("get_settings");

      // Get current timestamp for terms acceptance
      const now = new Date().toISOString();

      // Update with wizard data - forçando configurações obrigatórias
      const newSettings: AppSettings = {
        ...currentSettings,
        theme: theme,
        language: selectedLanguage, // Usar idioma selecionado
        notificationsEnabled: true, // Forçar notificações ativadas
        autoUpdate: true, // Forçar auto-update
        
        // Marcar setup como completo
        setupComplete: true,
        termsAccepted: acceptedTerms,
        termsAcceptedAt: acceptedTerms ? now : null,
        
        license: {
          ...currentSettings.license,
          key: licenseKey || null,
          plan: licenseKey ? "lifetime" : "trial",
          isActive: true,
          credits: 0,
          trialStarted: licenseKey ? null : now, // Iniciar trial se não tiver licença
        },
        
        // Configurações de sistema obrigatórias
        system: {
          ...currentSettings.system,
          autoUpdate: true,
          logsEnabled: true,
          analyticsEnabled: false, // Privacidade por padrão
        },
      };

      await invoke("save_settings", { settings: newSettings });
      
      // Limpar flag do tutorial para exibir na primeira visita
      localStorage.removeItem('tutorial_completed');
      
      navigate("/");
    } catch (error) {
      console.error("Setup failed:", error);
    }
  };

  const renderStepContent = () => {
    switch (steps[currentStep].id) {
      case "welcome":
        return (
          <div className="text-center space-y-4">
            <div className="flex justify-center mb-6">
              <TikTrendLogo size={64} />
            </div>
            <h2 className="text-2xl font-bold">Bem-vindo ao TikTrend Finder</h2>
            <p className="text-muted-foreground">
              Sua ferramenta definitiva para encontrar produtos vencedores no TikTok Shop.
              Vamos configurar seu ambiente em poucos passos.
            </p>
          </div>
        );
      case "responsibility":
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-red-600 flex items-center gap-2">
                ⚠️ Termo de Responsabilidade
              </h3>
              <p className="text-sm text-muted-foreground">
                O TikTrend Finder é uma ferramenta poderosa para análise de mercado.
                Para garantir a segurança da sua conta e a longevidade da ferramenta,
                você deve concordar com as seguintes práticas:
              </p>
            </div>

            <div className="bg-muted/50 p-4 rounded-lg text-sm space-y-3 border border-border">
              <div className="flex gap-2">
                <span>1.</span>
                <p>O scraping é limitado a <strong>1 requisição a cada 5-10 segundos</strong> para evitar bloqueios.</p>
              </div>
              <div className="flex gap-2">
                <span>2.</span>
                <p>O software se identifica de forma transparente como <strong>TikTrendFinder</strong>.</p>
              </div>
              <div className="flex gap-2">
                <span>3.</span>
                <p>Você é responsável pelo uso ético da ferramenta, respeitando os termos de serviço das plataformas.</p>
              </div>
            </div>

            <div className="flex items-center space-x-2 pt-4">
              <input
                type="checkbox"
                id="terms"
                className="h-4 w-4 rounded border-gray-300 text-tiktrend-primary focus:ring-tiktrend-primary"
                checked={acceptedTerms}
                onChange={(e) => setAcceptedTerms(e.target.checked)}
              />
              <label
                htmlFor="terms"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Li e concordo com os termos de responsabilidade e uso ético.
              </label>
            </div>
          </div>
        );
      case "license":
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <h3 className="text-lg font-medium">🔑 Ativação da Licença</h3>
              <p className="text-sm text-muted-foreground">
                Insira sua chave de licença para desbloquear buscas ilimitadas.
              </p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Chave de Licença</label>
              <Input
                placeholder="XXXX-XXXX-XXXX-XXXX"
                value={licenseKey}
                onChange={(e) => setLicenseKey(e.target.value)}
              />
            </div>
            
            {/* Licença Vitalícia */}
            <div className="bg-gradient-to-r from-tiktrend-primary/10 to-tiktrend-secondary/10 p-4 rounded-lg text-sm border border-tiktrend-primary/20">
              <p className="font-medium text-tiktrend-primary mb-2">✨ Licença Vitalícia</p>
              <ul className="space-y-1 text-muted-foreground">
                <li>✅ Buscas de produtos <strong>ilimitadas</strong></li>
                <li>✅ Todos os filtros avançados</li>
                <li>✅ Exportação completa (CSV, Excel)</li>
                <li>✅ Até 2 dispositivos simultâneos</li>
                <li>✅ Atualizações gratuitas para sempre</li>
              </ul>
            </div>

            {/* Créditos IA */}
            <div className="bg-muted p-4 rounded-lg text-sm">
              <p className="font-medium mb-2">🤖 Créditos IA (Opcional)</p>
              <p className="text-muted-foreground mb-2">
                Use créditos para gerar copies e análises com IA:
              </p>
              <ul className="space-y-1 text-muted-foreground text-xs">
                <li>• Copy simples: 1 crédito</li>
                <li>• Análise de tendência: 2 créditos</li>
                <li>• Lote de copies: 5 créditos</li>
              </ul>
              <p className="text-xs text-muted-foreground mt-2 italic">
                Compre créditos a qualquer momento no menu Perfil.
              </p>
            </div>

            {/* Trial */}
            <div className="bg-muted/50 p-3 rounded-lg text-sm border border-dashed">
              <p className="font-medium text-muted-foreground">📋 Versão Trial (7 dias)</p>
              <ul className="list-disc list-inside mt-1 space-y-0.5 text-muted-foreground text-xs">
                <li>50 produtos por busca</li>
                <li>Funcionalidades básicas</li>
                <li>Sem créditos IA inclusos</li>
              </ul>
            </div>
          </div>
        );
      case "preferences":
        return (
          <div className="space-y-6">
            {/* Idioma */}
            <div className="space-y-2">
              <h3 className="text-lg font-medium">{t("settings.appearance.language")}</h3>
              <div className="flex gap-2 flex-wrap">
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <Button
                    key={lang.code}
                    variant={selectedLanguage === lang.code ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleLanguageSelect(lang.code)}
                    className={selectedLanguage === lang.code ? "bg-tiktrend-primary hover:bg-tiktrend-primary/90" : ""}
                  >
                    {lang.flag} {lang.name}
                  </Button>
                ))}
              </div>
            </div>
            
            {/* Tema */}
            <div className="space-y-2">
              <h3 className="text-lg font-medium">{t("settings.appearance.theme")}</h3>
              <div className="flex gap-2">
                <Button 
                  variant={theme === "light" ? "default" : "outline"} 
                  onClick={() => setTheme("light")}
                  className={theme === "light" ? "bg-tiktrend-primary hover:bg-tiktrend-primary/90" : ""}
                >
                  ☀️ {t("settings.appearance.themes.light")}
                </Button>
                <Button 
                  variant={theme === "dark" ? "default" : "outline"} 
                  onClick={() => setTheme("dark")}
                  className={theme === "dark" ? "bg-tiktrend-primary hover:bg-tiktrend-primary/90" : ""}
                >
                  🌙 {t("settings.appearance.themes.dark")}
                </Button>
                <Button 
                  variant={theme === "system" ? "default" : "outline"} 
                  onClick={() => setTheme("system")}
                  className={theme === "system" ? "bg-tiktrend-primary hover:bg-tiktrend-primary/90" : ""}
                >
                  💻 {t("settings.appearance.themes.system")}
                </Button>
              </div>
            </div>
          </div>
        );
      case "finish":
        return (
          <div className="text-center space-y-4">
            <div className="text-4xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold">Tudo Pronto!</h2>
            <p className="text-muted-foreground mb-4">
              O TikTrend Finder está configurado e pronto para usar.
            </p>
            <div className="bg-muted p-4 rounded-lg text-left text-sm space-y-2">
              <p className="font-medium">🚀 Próximos passos:</p>
              <ul className="space-y-1 text-muted-foreground">
                <li>1. Faça sua primeira busca de produtos</li>
                <li>2. Salve os melhores nos favoritos</li>
                <li>3. Use a Copy AI para criar anúncios incríveis</li>
              </ul>
            </div>
            <p className="text-xs text-muted-foreground">
              Um tutorial interativo vai te guiar após clicar em "Começar"
            </p>
          </div>
        );
      default:
        return null;
    }
  };

  // Show loading while checking setup status
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <TikTrendLogo size={48} />
          <p className="text-muted-foreground">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <div className="flex justify-between items-center mb-4">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className={`h-2 flex-1 rounded-full mx-1 ${index <= currentStep ? "bg-tiktrend-primary" : "bg-muted"
                  }`}
              />
            ))}
          </div>
          <CardTitle>{steps[currentStep].title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="min-h-[300px] flex flex-col justify-between">
            <div className="py-4">
              {renderStepContent()}
            </div>
            <div className="flex justify-between pt-4 border-t">
              <Button
                variant="ghost"
                onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                disabled={currentStep === 0}
              >
                Voltar
              </Button>
              <Button
                onClick={handleNext}
                variant="tiktrend"
                disabled={steps[currentStep].id === "responsibility" && !acceptedTerms}
              >
                {currentStep === steps.length - 1 ? "Começar" : "Próximo"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
