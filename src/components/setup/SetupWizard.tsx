import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { TikTrendLogo } from "@/components/icons";
import { useUserStore } from "@/stores";
import { useNavigate } from "react-router-dom";
import { invoke } from "@tauri-apps/api/core";
import type { AppSettings } from "@/types";

const steps = [
  { id: "welcome", title: "Bem-vindo" },
  { id: "responsibility", title: "Responsabilidade" },
  { id: "license", title: "Licença" },
  { id: "preferences", title: "Preferências" },
  { id: "finish", title: "Concluir" },
];

export const SetupWizard: React.FC = () => {
  const [currentStep, setCurrentStep] = React.useState(0);
  const [licenseKey, setLicenseKey] = React.useState("");
  const [acceptedTerms, setAcceptedTerms] = React.useState(false);
  const { theme, setTheme } = useUserStore();
  const navigate = useNavigate();

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

      // Update with wizard data
      const newSettings: AppSettings = {
        ...currentSettings,
        theme: theme,
        license: {
          ...currentSettings.license,
          key: licenseKey || null,
          plan: licenseKey ? "starter" : "trial",
          isActive: true
        }
      };

      await invoke("save_settings", { settings: newSettings });
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
              <h3 className="text-lg font-medium">Ativação</h3>
              <p className="text-sm text-muted-foreground">
                Insira sua chave de licença ou continue com a versão de avaliação.
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
            <div className="bg-muted p-4 rounded-lg text-sm">
              <p className="font-medium">Versão Trial</p>
              <ul className="list-disc list-inside mt-2 space-y-1 text-muted-foreground">
                <li>7 dias de acesso gratuito</li>
                <li>50 produtos por busca</li>
                <li>Funcionalidades básicas</li>
              </ul>
            </div>
          </div>
        );
      case "preferences":
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h3 className="text-lg font-medium">Aparência</h3>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setTheme("light")}>☀️ Claro</Button>
                <Button variant="outline" onClick={() => setTheme("dark")}>🌙 Escuro</Button>
                <Button variant="outline" onClick={() => setTheme("system")}>💻 Sistema</Button>
              </div>
            </div>
          </div>
        );
      case "finish":
        return (
          <div className="text-center space-y-4">
            <div className="text-4xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold">Tudo Pronto!</h2>
            <p className="text-muted-foreground">
              O TikTrend Finder está configurado e pronto para usar.
            </p>
          </div>
        );
      default:
        return null;
    }
  };

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
