import * as React from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { UserIcon, StarIcon } from "@/components/icons";
import { useUserStore } from "@/stores";

export const Profile: React.FC = () => {
  const { t } = useTranslation();
  const { user, license, credits, logout } = useUserStore();

  // Mock user for demo - novo modelo lifetime + credits
  const mockUser = user || {
    id: "1",
    email: "usuario@exemplo.com",
    name: "Usuário Demo",
    hasLifetimeLicense: true,
    licenseActivatedAt: new Date().toISOString(),
    createdAt: new Date().toISOString(),
  };

  const mockLicense = license || {
    isValid: true,
    isLifetime: true,
    activatedAt: new Date().toISOString(),
    maxDevices: 2,
    activeDevices: 1,
  };

  const mockCredits = credits || {
    balance: 10,
    totalPurchased: 0,
    totalUsed: 0,
    lastPurchaseAt: null,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <UserIcon size={32} className="text-tiktrend-primary" />
          {t("profile.title")}
        </h1>
        <p className="text-muted-foreground">
          {t("profile.subtitle")}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* User Info - Melhoria #18: Avatar gradiente */}
        <Card className="overflow-hidden">
          <div className="h-24 bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary" />
          <CardHeader className="-mt-12">
            <div className="flex items-end gap-4">
              {/* Avatar with gradient border */}
              <div className="avatar-gradient rounded-full p-1 shadow-xl">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-tiktrend-primary to-tiktrend-secondary flex items-center justify-center text-white text-3xl font-bold">
                  {mockUser.name?.charAt(0) || "U"}
                </div>
              </div>
              <div className="pb-2">
                <div className="font-bold text-xl">{mockUser.name || "Usuário"}</div>
                <div className="text-muted-foreground">{mockUser.email}</div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-muted/50">
              <div>
                <span className="text-sm text-muted-foreground">{t("profile.member_since")}</span>
                <p className="font-medium">{new Date(mockUser.createdAt).toLocaleDateString("pt-BR")}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">{t("profile.account_id")}</span>
                <p className="font-mono text-sm truncate">{mockUser.id}</p>
              </div>
            </div>

            <Button variant="outline" className="w-full gap-2" onClick={logout}>
              {t("auth.logout")}
            </Button>
          </CardContent>
        </Card>

        {/* Licença e Créditos */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Licença & Créditos</CardTitle>
              <Badge variant={mockLicense.isLifetime ? "tiktrend" : "secondary"}>
                {mockLicense.isLifetime ? "Vitalícia ✓" : "Trial"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Licença Info */}
            <div className="p-4 rounded-lg bg-gradient-to-r from-tiktrend-primary/10 to-tiktrend-secondary/10">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">Licença Vitalícia</span>
                {mockLicense.isLifetime ? (
                  <span className="text-green-500 font-bold">Ativa</span>
                ) : (
                  <span className="text-2xl font-bold">R$ 49,90</span>
                )}
              </div>
              {mockLicense.isLifetime && mockLicense.activatedAt && (
                <div className="text-sm text-muted-foreground">
                  Ativada em {new Date(mockLicense.activatedAt).toLocaleDateString("pt-BR")}
                </div>
              )}
            </div>

            {/* Credits Stats */}
            <div className="space-y-3">
              <h4 className="font-medium">Créditos IA</h4>

              <div className="p-4 rounded-lg bg-muted/50">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-muted-foreground">Saldo atual</span>
                  <span className="text-3xl font-bold text-tiktrend-primary">
                    {mockCredits.balance}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Total comprado</span>
                    <p className="font-medium">{mockCredits.totalPurchased}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Total usado</span>
                    <p className="font-medium">{mockCredits.totalUsed}</p>
                  </div>
                </div>
              </div>

              <div className="text-xs text-muted-foreground space-y-1">
                <p>• Copy simples: 1 crédito</p>
                <p>• Análise de produto: 2 créditos</p>
                <p>• Lote de copies: 5 créditos</p>
              </div>
            </div>

            {!mockLicense.isLifetime && (
              <Button variant="tiktrend" className="w-full">
                <StarIcon size={16} className="mr-2" />
                Comprar Licença - R$ 49,90
              </Button>
            )}

            <Button variant="outline" className="w-full">
              Comprar Créditos IA
            </Button>
          </CardContent>
        </Card>

        {/* Features */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recursos Disponíveis</CardTitle>
            <CardDescription>
              Compare os recursos entre versão gratuita e licença vitalícia
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              {/* Free */}
              <div className="p-4 rounded-lg border">
                <h4 className="font-medium mb-4">Versão Gratuita</h4>
                <ul className="space-y-2 text-sm">
                  <li>✅ Busca de produtos</li>
                  <li>✅ 3 listas de favoritos</li>
                  <li>✅ 10 créditos de cortesia</li>
                  <li>❌ Exportação de dados</li>
                  <li>❌ Comparação avançada</li>
                </ul>
              </div>

              {/* Lifetime License */}
              <div className="p-4 rounded-lg border border-tiktrend-primary bg-tiktrend-primary/5">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-medium">Licença Vitalícia</h4>
                  <Badge variant="tiktrend">R$ 49,90</Badge>
                </div>
                <ul className="space-y-2 text-sm">
                  <li>✅ Todas as funcionalidades</li>
                  <li>✅ Listas ilimitadas</li>
                  <li>✅ Exportação (CSV, Excel)</li>
                  <li>✅ Comparação avançada</li>
                  <li>✅ Até 2 dispositivos</li>
                  <li>✅ Atualizações para sempre</li>
                </ul>
              </div>

              {/* Credits */}
              <div className="p-4 rounded-lg border border-tiktrend-secondary bg-tiktrend-secondary/5">
                <h4 className="font-medium mb-4">Pacotes de Créditos IA</h4>
                <ul className="space-y-2 text-sm">
                  <li className="flex justify-between">
                    <span>Starter (50)</span>
                    <span className="font-medium">R$ 19,90</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Pro (200)</span>
                    <span className="font-medium">R$ 49,90</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Ultra (500)</span>
                    <span className="font-medium">R$ 99,90</span>
                  </li>
                </ul>
                <p className="text-xs text-muted-foreground mt-3">
                  Créditos nunca expiram
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Profile;
