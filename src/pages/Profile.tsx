import * as React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { UserIcon, StarIcon } from "@/components/icons";
import { useUserStore } from "@/stores";
import { PLANS } from "@/lib/constants";

export const Profile: React.FC = () => {
  const { user, license, logout } = useUserStore();

  // Mock user for demo
  const mockUser = user || {
    id: "1",
    email: "usuario@exemplo.com",
    name: "Usuário Demo",
    plan: "trial" as const,
    planExpiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    createdAt: new Date().toISOString(),
  };

  const mockLicense = license || {
    isValid: true,
    plan: "trial" as const,
    features: PLANS.trial.features,
    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    usageThisMonth: {
      searches: 3,
      copies: 2,
    },
  };

  const daysRemaining = Math.ceil(
    (new Date(mockLicense.expiresAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <UserIcon size={32} className="text-tiktrend-primary" />
          Meu Perfil
        </h1>
        <p className="text-muted-foreground">
          Gerencie sua conta e assinatura
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
                <span className="text-sm text-muted-foreground">Membro desde</span>
                <p className="font-medium">{new Date(mockUser.createdAt).toLocaleDateString("pt-BR")}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">ID da conta</span>
                <p className="font-mono text-sm truncate">{mockUser.id}</p>
              </div>
            </div>

            <Button variant="outline" className="w-full gap-2" onClick={logout}>
              Sair da Conta
            </Button>
          </CardContent>
        </Card>

        {/* Subscription */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Assinatura</CardTitle>
              <Badge variant={mockLicense.plan === "trial" ? "secondary" : "tiktrend"}>
                {PLANS[mockLicense.plan].name}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 rounded-lg bg-gradient-to-r from-tiktrend-primary/10 to-tiktrend-secondary/10">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">Plano Atual</span>
                <span className="text-2xl font-bold">
                  R${PLANS[mockLicense.plan].price}/mês
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                {daysRemaining > 0
                  ? `${daysRemaining} dias restantes`
                  : "Expirado"}
              </div>
            </div>

            {/* Usage Stats */}
            <div className="space-y-3">
              <h4 className="font-medium">Uso este mês</h4>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Buscas</span>
                  <span>
                    {mockLicense.usageThisMonth.searches} / {mockLicense.features.searchesPerMonth}
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-tiktrend-primary rounded-full"
                    style={{
                      width: `${(mockLicense.usageThisMonth.searches / mockLicense.features.searchesPerMonth) * 100}%`,
                    }}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Copies geradas</span>
                  <span>
                    {mockLicense.usageThisMonth.copies} / {mockLicense.features.copiesPerMonth}
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-tiktrend-secondary rounded-full"
                    style={{
                      width: `${(mockLicense.usageThisMonth.copies / mockLicense.features.copiesPerMonth) * 100}%`,
                    }}
                  />
                </div>
              </div>
            </div>

            {mockLicense.plan === "trial" && (
              <Button variant="tiktrend" className="w-full">
                <StarIcon size={16} className="mr-2" />
                Assinar por R$10/mês
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Features */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recursos do Plano</CardTitle>
            <CardDescription>
              Compare os recursos disponíveis em cada plano
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              {/* Trial */}
              <div className="p-4 rounded-lg border">
                <h4 className="font-medium mb-4">Trial (Grátis)</h4>
                <ul className="space-y-2 text-sm">
                  <li>✅ {PLANS.trial.features.searchesPerMonth} buscas/mês</li>
                  <li>✅ {PLANS.trial.features.copiesPerMonth} copies/mês</li>
                  <li>✅ {PLANS.trial.features.favoriteLists} listas de favoritos</li>
                  <li>❌ Exportação de dados</li>
                  <li>❌ Agendador de coleta</li>
                </ul>
              </div>

              {/* Basic */}
              <div className="p-4 rounded-lg border border-tiktrend-primary bg-tiktrend-primary/5">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-medium">Básico</h4>
                  <Badge variant="tiktrend">R$10/mês</Badge>
                </div>
                <ul className="space-y-2 text-sm">
                  <li>✅ {PLANS.basic.features.searchesPerMonth} buscas/mês</li>
                  <li>✅ {PLANS.basic.features.copiesPerMonth} copies/mês</li>
                  <li>✅ {PLANS.basic.features.favoriteLists} listas de favoritos</li>
                  <li>✅ Exportação de dados (CSV, Excel)</li>
                  <li>⏳ Agendador de coleta (em breve)</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
