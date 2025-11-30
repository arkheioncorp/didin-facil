import * as React from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { TikTrendIcon, StarIcon } from "@/components/icons";
import { useUserStore } from "@/stores";
import { useNavigate } from "react-router-dom";
import { LICENSE_PRICE, CREDIT_PACKS, CREDIT_COSTS } from "@/lib/constants";

export const Subscription: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { license, setLicense } = useUserStore();
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [selectedItem, setSelectedItem] = React.useState<string | null>(null);

  const handlePurchaseLicense = async () => {
    setSelectedItem("license");
    setIsProcessing(true);

    // TODO: Integrate with Mercado Pago
    // Simulating purchase
    setTimeout(() => {
      const newLicense = {
        isValid: true,
        isLifetime: true,
        activatedAt: new Date().toISOString(),
        maxDevices: 2,
        activeDevices: 1,
      };
      setLicense(newLicense);
      setIsProcessing(false);
      navigate("/");
    }, 2000);
  };

  const handlePurchaseCredits = async (packId: string) => {
    setSelectedItem(packId);
    setIsProcessing(true);

    // TODO: Integrate with Mercado Pago
    setTimeout(() => {
      // Update credits balance
      setIsProcessing(false);
      alert(`Pacote ${CREDIT_PACKS[packId as keyof typeof CREDIT_PACKS].name} comprado com sucesso!`);
    }, 2000);
  };

  const hasLicense = license?.isValid && license?.isLifetime;

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-tiktrend-primary/5 p-4 py-12">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <TikTrendIcon size={40} />
            <span className="text-2xl font-bold bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary bg-clip-text text-transparent">
              TikTrend Finder
            </span>
          </div>
          <h1 className="text-3xl font-bold mb-2">
            {hasLicense ? t("subscription.buy_credits") : t("subscription.get_license")}
          </h1>
          <p className="text-muted-foreground">
            {hasLicense 
              ? t("subscription.credits_description")
              : t("subscription.pay_once")
            }
          </p>
        </div>

        {/* Current status */}
        {license && (
          <Card className="mb-8">
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  <p className="font-semibold flex items-center gap-2">
                    {hasLicense ? (
                      <>
                        <span className="text-green-500">✓</span>
                        Licença Vitalícia Ativa
                      </>
                    ) : (
                      <>
                        <span className="text-yellow-500">⚠</span>
                        Sem Licença
                      </>
                    )}
                  </p>
                </div>
                {hasLicense && (
                  <Badge variant="secondary">
                    {license.activeDevices}/{license.maxDevices} dispositivos
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Lifetime License Card */}
        {!hasLicense && (
          <Card className="mb-12 border-tiktrend-primary shadow-lg shadow-tiktrend-primary/20 relative">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2">
              <Badge variant="tiktrend" className="px-3">
                <StarIcon size={12} className="mr-1" />
                Pagamento Único
              </Badge>
            </div>
            <CardHeader className="text-center pb-2">
              <CardTitle className="text-2xl">Licença Vitalícia</CardTitle>
              <CardDescription>Pague uma vez, use para sempre</CardDescription>
              <div className="mt-4">
                <span className="text-5xl font-bold">R$ {LICENSE_PRICE.toFixed(2).replace(".", ",")}</span>
                <span className="text-muted-foreground ml-2">pagamento único</span>
              </div>
            </CardHeader>
            <CardContent>
              <Separator className="my-6" />
              <div className="grid md:grid-cols-2 gap-4 mb-6">
                <div className="space-y-3">
                  <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
                    Recursos Inclusos
                  </h4>
                  <ul className="space-y-2">
                    <FeatureItem icon="🔍" text="Busca de produtos ilimitada" />
                    <FeatureItem icon="🌐" text="Multi-fonte (TikTok, AliExpress)" />
                    <FeatureItem icon="🎯" text="Filtros avançados" />
                    <FeatureItem icon="⭐" text="Favoritos ilimitados" />
                  </ul>
                </div>
                <div className="space-y-3">
                  <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
                    Benefícios
                  </h4>
                  <ul className="space-y-2">
                    <FeatureItem icon="📤" text="Exportação completa (CSV, Excel, JSON)" />
                    <FeatureItem icon="🔄" text="Atualizações gratuitas" />
                    <FeatureItem icon="💻" text="Até 2 dispositivos" />
                    <FeatureItem icon="♾️" text="Sem mensalidades" />
                  </ul>
                </div>
              </div>
              <Button
                variant="tiktrend"
                size="lg"
                className="w-full"
                disabled={isProcessing}
                onClick={handlePurchaseLicense}
              >
                {isProcessing && selectedItem === "license" ? (
                  <LoadingSpinner text="Processando..." />
                ) : (
                  "Comprar Licença Vitalícia"
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Credit Packs */}
        <div className="mb-12">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold mb-2">Pacotes de Créditos IA</h2>
            <p className="text-muted-foreground">
              {hasLicense 
                ? "Use créditos para gerar copies e análises com IA"
                : "Adquira a licença para desbloquear créditos IA"
              }
            </p>
          </div>

          {/* Credit costs info */}
          <Card className="mb-6 bg-muted/50">
            <CardContent className="py-4">
              <div className="flex flex-wrap items-center justify-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-tiktrend-primary font-bold">{CREDIT_COSTS.copy}</span>
                  <span className="text-muted-foreground">crédito = 1 copy</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-tiktrend-primary font-bold">{CREDIT_COSTS.trendAnalysis}</span>
                  <span className="text-muted-foreground">créditos = análise de tendência</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-tiktrend-primary font-bold">{CREDIT_COSTS.nicheReport}</span>
                  <span className="text-muted-foreground">créditos = relatório de nicho</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Credit packs grid */}
          <div className="grid md:grid-cols-3 gap-6">
            {Object.entries(CREDIT_PACKS).map(([id, pack]) => (
              <Card 
                key={id} 
                className={`relative ${id === "pro" ? "border-tiktrend-primary" : ""} ${!hasLicense ? "opacity-60" : ""}`}
              >
                {id === "pro" && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge variant="tiktrend" className="px-3">
                      Melhor Custo
                    </Badge>
                  </div>
                )}
                <CardHeader className="text-center pb-2">
                  <CardTitle className="text-xl">{pack.name}</CardTitle>
                  <div className="mt-2">
                    <span className="text-3xl font-bold text-tiktrend-primary">{pack.credits}</span>
                    <span className="text-muted-foreground ml-1">créditos</span>
                  </div>
                  <div className="mt-2">
                    <span className="text-2xl font-bold">R$ {pack.price.toFixed(2).replace(".", ",")}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    R$ {pack.pricePerCredit.toFixed(2).replace(".", ",")} por crédito
                  </p>
                </CardHeader>
                <CardContent>
                  <Button
                    variant={id === "pro" ? "tiktrend" : "outline"}
                    className="w-full"
                    disabled={isProcessing || !hasLicense}
                    onClick={() => handlePurchaseCredits(id)}
                  >
                    {isProcessing && selectedItem === id ? (
                      <LoadingSpinner text="Processando..." />
                    ) : !hasLicense ? (
                      "Requer Licença"
                    ) : (
                      "Comprar Créditos"
                    )}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
          
          <p className="text-center text-sm text-muted-foreground mt-4">
            ℹ️ Créditos não expiram. Use quando precisar.
          </p>
        </div>

        {/* Payment methods */}
        <div className="mt-12 text-center">
          <p className="text-sm text-muted-foreground mb-4">
            Pagamento seguro via
          </p>
          <div className="flex items-center justify-center gap-4">
            <div className="px-4 py-2 rounded-lg border bg-background">
              <span className="font-semibold text-blue-600">Mercado Pago</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>📱 Pix</span>
              <span>•</span>
              <span>💳 Cartão (3x sem juros)</span>
              <span>•</span>
              <span>🏦 Boleto</span>
            </div>
          </div>
        </div>

        {/* FAQ */}
        <div className="mt-12">
          <h2 className="text-xl font-semibold text-center mb-6">
            Perguntas Frequentes
          </h2>
          <div className="grid md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">
                  A licença é realmente vitalícia?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Sim! Você paga R$ 49,90 uma única vez e tem acesso ao app para sempre. 
                  Sem mensalidades ou taxas recorrentes.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">
                  Preciso de créditos para usar o app?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Não! A busca de produtos é ilimitada. Créditos são apenas para 
                  gerar copies com IA, um recurso opcional.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">
                  Os créditos expiram?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Não! Seus créditos nunca expiram. Use quando precisar.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">
                  Posso usar em mais de um computador?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Sim! A licença permite uso em até 2 dispositivos simultaneamente.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Back button */}
        <div className="mt-8 text-center">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            ← Voltar
          </Button>
        </div>
      </div>
    </div>
  );
};

// Helper components
const FeatureItem: React.FC<{ icon: string; text: string }> = ({ icon, text }) => (
  <li className="flex items-center gap-2 text-sm">
    <span>{icon}</span>
    <span>{text}</span>
  </li>
);

const LoadingSpinner: React.FC<{ text: string }> = ({ text }) => (
  <span className="flex items-center gap-2">
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
        fill="none"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
    {text}
  </span>
);
