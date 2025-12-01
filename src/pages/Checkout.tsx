import * as React from "react";
import { useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Separator,
} from "@/components/ui";
import { TikTrendIcon, CheckIcon, CopyIcon } from "@/components/icons";
import { useToast } from "@/hooks/use-toast";
import {
  getCreditPackages,
  getCreditBalance,
  purchaseCredits,
  pollPaymentStatus,
  type CreditPackage,
  type CreditBalance,
  type CreditPurchase,
} from "@/services/credits";

type CheckoutStep = "packages" | "payment" | "success";

export const Checkout: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // State
  const [step, setStep] = React.useState<CheckoutStep>("packages");
  const [packages, setPackages] = React.useState<CreditPackage[]>([]);
  const [balance, setBalance] = React.useState<CreditBalance | null>(null);
  const [selectedPackage, setSelectedPackage] = React.useState<CreditPackage | null>(null);
  const [purchase, setPurchase] = React.useState<CreditPurchase | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  // Load packages and balance on mount
  React.useEffect(() => {
    const loadData = async () => {
      try {
        const [pkgs, bal] = await Promise.all([
          getCreditPackages(),
          getCreditBalance(),
        ]);
        setPackages(pkgs);
        setBalance(bal);
      } catch (error) {
        console.error("Error loading checkout data:", error);
        toast({
          title: "Erro ao carregar dados",
          description: "Tente novamente mais tarde",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, [toast]);

  // Handle package selection and purchase
  const handlePurchase = async (pkg: CreditPackage) => {
    setSelectedPackage(pkg);
    
    // TODO: Implement proper CPF input modal
    const cpf = window.prompt("Digite seu CPF para o PIX (apenas números):");
    if (!cpf) return;

    setIsProcessing(true);

    try {
      const result = await purchaseCredits(pkg.slug, "pix", cpf);
      setPurchase(result);
      setStep("payment");

      // Start polling for payment status
      pollPaymentStatus(
        result.purchase_id,
        (status) => {
          setPurchase(status);
          if (status.status === "approved") {
            setStep("success");
            toast({
              title: "Pagamento aprovado! 🎉",
              description: `${pkg.credits} créditos adicionados à sua conta`,
            });
          }
        },
        300000, // 5 min timeout
        3000 // Poll every 3 seconds
      ).catch((error) => {
        if (error.message !== "Payment timeout") {
          toast({
            title: "Pagamento não aprovado",
            description: error.message,
            variant: "destructive",
          });
        }
      });
    } catch (error) {
      console.error("Error initiating purchase:", error);
      toast({
        title: "Erro ao iniciar compra",
        description: error instanceof Error ? error.message : "Tente novamente",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Copy PIX code
  const handleCopyPix = async () => {
    if (purchase?.pix_copy_paste) {
      await navigator.clipboard.writeText(purchase.pix_copy_paste);
      setCopied(true);
      toast({
        title: "Código copiado!",
        description: "Cole no seu app de banco",
      });
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Format price
  const formatPrice = (value: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-tiktrend-primary" />
      </div>
    );
  }

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
          <h1 className="text-3xl font-bold mb-2">Comprar Créditos</h1>
          <p className="text-muted-foreground">
            Use créditos para gerar copies IA, análises de tendência e relatórios
          </p>
        </div>

        {/* Current Balance */}
        {balance && (
          <Card className="mb-8 border-tiktrend-primary/20" data-testid="credit-balance-card">
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Seu saldo atual</p>
                  <p className="text-2xl font-bold text-tiktrend-primary" data-testid="credit-balance-value">
                    {balance.credits_balance} créditos
                  </p>
                </div>
                <div className="text-right text-sm text-muted-foreground">
                  <p data-testid="credits-purchased">Comprados: {balance.credits_purchased}</p>
                  <p data-testid="credits-used">Usados: {balance.credits_used}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step: Package Selection */}
        {step === "packages" && (
          <>
            <div className="grid gap-6 md:grid-cols-3" data-testid="credit-packages-grid">
              {packages.map((pkg) => (
                <Card
                  key={pkg.id}
                  data-testid={`credit-package-${pkg.slug}`}
                  className={`relative cursor-pointer transition-all hover:shadow-lg hover:border-tiktrend-primary/50 ${
                    pkg.is_popular ? "border-tiktrend-primary ring-2 ring-tiktrend-primary/20" : ""
                  }`}
                  onClick={() => handlePurchase(pkg)}
                >
                  {pkg.is_popular && (
                    <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-tiktrend-primary" data-testid="popular-badge">
                      Mais Popular
                    </Badge>
                  )}
                  {pkg.discount_percent > 0 && (
                    <Badge 
                      variant="secondary" 
                      className="absolute -top-3 right-4 bg-green-500 text-white"
                      data-testid="discount-badge"
                    >
                      -{pkg.discount_percent}%
                    </Badge>
                  )}
                  
                  <CardHeader className="text-center pb-2">
                    <CardTitle className="text-xl" data-testid="package-name">{pkg.name}</CardTitle>
                    <CardDescription data-testid="package-credits">
                      {pkg.credits} créditos
                    </CardDescription>
                  </CardHeader>
                  
                  <CardContent className="text-center">
                    <div className="mb-4">
                      <span className="text-3xl font-bold" data-testid="package-price">
                        {formatPrice(pkg.price_brl)}
                      </span>
                    </div>
                    
                    <p className="text-sm text-muted-foreground mb-4">
                      {formatPrice(pkg.price_per_credit)} por crédito
                    </p>
                    
                    <Separator className="my-4" />
                    
                    <ul className="space-y-2 text-sm">
                      <li className="flex items-center gap-2">
                        <CheckIcon className="h-4 w-4 text-green-500" />
                        <span>Copy IA: {Math.floor(pkg.credits / 1)} gerações</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckIcon className="h-4 w-4 text-green-500" />
                        <span>Análise: {Math.floor(pkg.credits / 2)} análises</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckIcon className="h-4 w-4 text-green-500" />
                        <span>Relatório: {Math.floor(pkg.credits / 5)} relatórios</span>
                      </li>
                    </ul>
                    
                    <Button 
                      className="w-full mt-6" 
                      size="lg"
                      disabled={isProcessing}
                    >
                      {isProcessing && selectedPackage?.id === pkg.id ? (
                        <span className="flex items-center gap-2">
                          <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                          Processando...
                        </span>
                      ) : (
                        "Comprar Agora"
                      )}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Credit costs info */}
            <Card className="mt-8">
              <CardHeader>
                <CardTitle className="text-lg">Como funcionam os créditos?</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="flex items-start gap-3">
                    <div className="rounded-full bg-tiktrend-primary/10 p-2">
                      <span className="text-lg">📝</span>
                    </div>
                    <div>
                      <p className="font-medium">Copy IA</p>
                      <p className="text-sm text-muted-foreground">
                        1 crédito por copy gerada
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="rounded-full bg-tiktrend-primary/10 p-2">
                      <span className="text-lg">📊</span>
                    </div>
                    <div>
                      <p className="font-medium">Análise de Tendência</p>
                      <p className="text-sm text-muted-foreground">
                        2 créditos por análise
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="rounded-full bg-tiktrend-primary/10 p-2">
                      <span className="text-lg">📑</span>
                    </div>
                    <div>
                      <p className="font-medium">Relatório de Nicho</p>
                      <p className="text-sm text-muted-foreground">
                        5 créditos por relatório
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {/* Step: Payment (PIX) */}
        {step === "payment" && purchase && (
          <Card className="max-w-lg mx-auto" data-testid="pix-payment-card">
            <CardHeader className="text-center">
              <CardTitle data-testid="pix-payment-title">Pagamento via PIX</CardTitle>
              <CardDescription>
                Escaneie o QR Code ou copie o código PIX
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* QR Code */}
              {purchase.qr_code_base64 && (
                <div className="flex justify-center" data-testid="pix-qr-container">
                  <div className="bg-white p-4 rounded-lg shadow-lg border border-border">
                    <img
                      src={`data:image/png;base64,${purchase.qr_code_base64}`}
                      alt="QR Code PIX"
                      className="w-48 h-48"
                      data-testid="pix-qr-code"
                    />
                  </div>
                </div>
              )}

              {/* PIX Copy & Paste */}
              {purchase.pix_copy_paste && (
                <div data-testid="pix-copy-section">
                  <p className="text-sm text-muted-foreground mb-2 text-center">
                    Ou copie o código:
                  </p>
                  <div className="flex gap-2">
                    <div className="flex-1 p-3 bg-muted rounded-lg text-xs break-all font-mono" data-testid="pix-code-display">
                      {purchase.pix_copy_paste.substring(0, 50)}...
                    </div>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={handleCopyPix}
                      data-testid="pix-copy-button"
                    >
                      {copied ? (
                        <CheckIcon className="h-4 w-4 text-green-500" />
                      ) : (
                        <CopyIcon className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              )}

              <Separator />

              {/* Purchase details */}
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Pacote:</span>
                  <span className="font-medium">{selectedPackage?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Créditos:</span>
                  <span className="font-medium">{selectedPackage?.credits}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Valor:</span>
                  <span className="font-bold text-tiktrend-primary">
                    {formatPrice(purchase.amount_brl)}
                  </span>
                </div>
              </div>

              <Separator />

              {/* Status */}
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">
                  Status do pagamento
                </p>
                <div className="flex items-center justify-center gap-2">
                  <span className="animate-pulse h-2 w-2 rounded-full bg-yellow-500" />
                  <span className="font-medium text-yellow-600">
                    Aguardando pagamento...
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  O pagamento será confirmado automaticamente
                </p>
              </div>

              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  setStep("packages");
                  setPurchase(null);
                }}
              >
                Voltar para pacotes
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step: Success */}
        {step === "success" && selectedPackage && (
          <Card className="max-w-lg mx-auto text-center">
            <CardContent className="py-12">
              <div className="mb-6">
                <div className="mx-auto w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckIcon className="h-8 w-8 text-green-600" />
                </div>
              </div>
              
              <h2 className="text-2xl font-bold mb-2">Pagamento Aprovado!</h2>
              <p className="text-muted-foreground mb-6">
                {selectedPackage.credits} créditos foram adicionados à sua conta
              </p>
              
              <div className="bg-tiktrend-primary/10 rounded-lg p-4 mb-6">
                <p className="text-sm text-muted-foreground">Novo saldo</p>
                <p className="text-3xl font-bold text-tiktrend-primary">
                  {(balance?.credits_balance || 0) + selectedPackage.credits} créditos
                </p>
              </div>
              
              <div className="space-y-3">
                <Button className="w-full" size="lg" onClick={() => navigate("/copy")}>
                  Gerar Copy IA
                </Button>
                <Button variant="outline" className="w-full" onClick={() => navigate("/")}>
                  Voltar ao Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

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

export default Checkout;
