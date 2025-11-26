import * as React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { TikTrendIcon, StarIcon } from "@/components/icons";
import { useUserStore } from "@/stores";
import { useNavigate } from "react-router-dom";
import { PLANS } from "@/lib/constants";

export const Subscription: React.FC = () => {
  const navigate = useNavigate();
  const { license, setLicense } = useUserStore();
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [selectedPlan, setSelectedPlan] = React.useState<"basic" | "pro" | null>(null);

  const handleSubscribe = async (plan: "basic" | "pro") => {
    setSelectedPlan(plan);
    setIsProcessing(true);

    // TODO: Integrate with Mercado Pago
    // For now, simulate subscription
    setTimeout(() => {
      const newLicense = {
        isValid: true,
        plan: plan,
        features: PLANS[plan].features,
        expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        usageThisMonth: {
          searches: 0,
          copies: 0,
        },
      };
      setLicense(newLicense);
      setIsProcessing(false);
      navigate("/");
    }, 2000);
  };

  const plans = [
    {
      id: "basic" as const,
      name: "Básico",
      price: 10,
      description: "Perfeito para começar",
      features: [
        { text: "100 buscas/mês", included: true },
        { text: "50 copies/mês", included: true },
        { text: "5 listas de favoritos", included: true },
        { text: "Exportação CSV/Excel", included: true },
        { text: "Agendador de coleta", included: false },
        { text: "Suporte prioritário", included: false },
      ],
      popular: true,
    },
    {
      id: "pro" as const,
      name: "Pro",
      price: 29,
      description: "Para profissionais",
      features: [
        { text: "Buscas ilimitadas", included: true },
        { text: "Copies ilimitadas", included: true },
        { text: "Listas ilimitadas", included: true },
        { text: "Exportação completa", included: true },
        { text: "Agendador de coleta", included: true },
        { text: "Suporte prioritário", included: true },
      ],
      popular: false,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-tiktrend-primary/5 p-4 py-12">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <TikTrendIcon size={40} />
            <span className="text-2xl font-bold bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary bg-clip-text text-transparent">
              TikTrend Finder
            </span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Escolha seu Plano</h1>
          <p className="text-muted-foreground">
            Desbloqueie todo o potencial do TikTrend Finder
          </p>
        </div>

        {/* Current plan info */}
        {license && (
          <Card className="mb-8">
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Plano Atual</p>
                  <p className="font-semibold">{PLANS[license.plan].name}</p>
                </div>
                {license.plan === "trial" && (
                  <Badge variant="secondary">
                    {Math.ceil(
                      (new Date(license.expiresAt).getTime() - Date.now()) /
                        (1000 * 60 * 60 * 24)
                    )}{" "}
                    dias restantes
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Plans grid */}
        <div className="grid md:grid-cols-2 gap-6">
          {plans.map((plan) => (
            <Card
              key={plan.id}
              className={`relative ${
                plan.popular
                  ? "border-tiktrend-primary shadow-lg shadow-tiktrend-primary/20"
                  : ""
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge variant="tiktrend" className="px-3">
                    <StarIcon size={12} className="mr-1" />
                    Mais Popular
                  </Badge>
                </div>
              )}
              <CardHeader className="text-center pb-2">
                <CardTitle className="text-xl">{plan.name}</CardTitle>
                <CardDescription>{plan.description}</CardDescription>
                <div className="mt-4">
                  <span className="text-4xl font-bold">R${plan.price}</span>
                  <span className="text-muted-foreground">/mês</span>
                </div>
              </CardHeader>
              <CardContent>
                <Separator className="my-4" />
                <ul className="space-y-3">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-2 text-sm">
                      {feature.included ? (
                        <svg
                          className="h-5 w-5 text-green-500 shrink-0"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      ) : (
                        <svg
                          className="h-5 w-5 text-muted-foreground shrink-0"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <line x1="18" y1="6" x2="6" y2="18" />
                          <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                      )}
                      <span
                        className={
                          feature.included ? "" : "text-muted-foreground"
                        }
                      >
                        {feature.text}
                      </span>
                    </li>
                  ))}
                </ul>
                <Button
                  variant={plan.popular ? "tiktrend" : "outline"}
                  className="w-full mt-6"
                  disabled={isProcessing}
                  onClick={() => handleSubscribe(plan.id)}
                >
                  {isProcessing && selectedPlan === plan.id ? (
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
                      Processando...
                    </span>
                  ) : license?.plan === plan.id ? (
                    "Plano Atual"
                  ) : (
                    `Assinar ${plan.name}`
                  )}
                </Button>
              </CardContent>
            </Card>
          ))}
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
              <span>💳 Cartão</span>
              <span>•</span>
              <span>📱 Pix</span>
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
                  Posso cancelar a qualquer momento?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Sim! Você pode cancelar sua assinatura a qualquer momento sem
                  taxas adicionais.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">
                  Como funciona o trial?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  O trial de 7 dias é gratuito e não requer cartão de crédito.
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
