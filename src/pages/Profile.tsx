import * as React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  UserIcon, 
  StarIcon, 
  CreditCardIcon,
  ShieldCheckIcon,
  DeviceIcon,
  EditIcon,
  SaveIcon,
} from "@/components/icons";
import { useUserStore } from "@/stores";
import type { User, License, Credits } from "@/types";

// Mock data for development
const createMockUser = (): User => ({
  id: "usr_demo_12345",
  email: "usuario@exemplo.com",
  name: "Usuário Demo",
  avatarUrl: null,
  phone: null,
  hasLifetimeLicense: true,
  licenseActivatedAt: new Date().toISOString(),
  isActive: true,
  isEmailVerified: true,
  language: "pt-BR",
  timezone: "America/Sao_Paulo",
  createdAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
  updatedAt: new Date().toISOString(),
  lastLoginAt: new Date().toISOString(),
});

const createMockLicense = (): License => ({
  id: "lic_demo_12345",
  isValid: true,
  isLifetime: true,
  plan: 'lifetime',
  activatedAt: new Date().toISOString(),
  expiresAt: null,
  maxDevices: 2,
  activeDevices: 1,
  currentDeviceId: "device_123",
  isCurrentDeviceAuthorized: true,
});

const createMockCredits = (): Credits => ({
  balance: 45,
  totalPurchased: 100,
  totalUsed: 55,
  lastPurchaseAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
  bonusBalance: 5,
  bonusExpiresAt: new Date(Date.now() + 23 * 24 * 60 * 60 * 1000).toISOString(),
});

export const Profile: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, license, credits, logout, updateUser } = useUserStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  // Use real data or mock for demo
  const currentUser = user || createMockUser();
  const currentLicense = license || createMockLicense();
  const currentCredits = credits || createMockCredits();

  // Edit mode state
  const [isEditing, setIsEditing] = React.useState(false);
  const [editForm, setEditForm] = React.useState({
    name: currentUser.name || "",
    phone: currentUser.phone || "",
  });

  const handleSaveProfile = () => {
    updateUser({
      name: editForm.name || null,
      phone: editForm.phone || null,
      updatedAt: new Date().toISOString(),
    });
    setIsEditing(false);
  };

  const totalCredits = currentCredits.balance + currentCredits.bonusBalance;
  const daysUntilBonusExpires = currentCredits.bonusExpiresAt 
    ? Math.ceil((new Date(currentCredits.bonusExpiresAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <UserIcon size={32} className="text-tiktrend-primary" />
          {t("profile.title", "Meu Perfil")}
        </h1>
        <p className="text-muted-foreground">
          {t("profile.subtitle", "Gerencie sua conta, licença e créditos")}
        </p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:inline-flex">
          <TabsTrigger value="profile" className="gap-2">
            <UserIcon size={16} />
            <span className="hidden sm:inline">Perfil</span>
          </TabsTrigger>
          <TabsTrigger value="license" className="gap-2">
            <ShieldCheckIcon size={16} />
            <span className="hidden sm:inline">Licença</span>
          </TabsTrigger>
          <TabsTrigger value="credits" className="gap-2">
            <StarIcon size={16} />
            <span className="hidden sm:inline">Créditos</span>
          </TabsTrigger>
          <TabsTrigger value="devices" className="gap-2">
            <DeviceIcon size={16} />
            <span className="hidden sm:inline">Dispositivos</span>
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* User Info Card */}
            <Card className="overflow-hidden">
              <div className="h-24 bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary" />
              <CardHeader className="-mt-12">
                <div className="flex items-end justify-between">
                  <div className="flex items-end gap-4">
                    <div className="avatar-gradient rounded-full p-1 shadow-xl">
                      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-tiktrend-primary to-tiktrend-secondary flex items-center justify-center text-white text-3xl font-bold">
                        {currentUser.name?.charAt(0) || currentUser.email.charAt(0).toUpperCase()}
                      </div>
                    </div>
                    <div className="pb-2">
                      <div className="font-bold text-xl">{currentUser.name || "Usuário"}</div>
                      <div className="text-muted-foreground text-sm">{currentUser.email}</div>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => isEditing ? handleSaveProfile() : setIsEditing(true)}
                  >
                    {isEditing ? (
                      <><SaveIcon size={16} className="mr-2" /> Salvar</>
                    ) : (
                      <><EditIcon size={16} className="mr-2" /> Editar</>
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {isEditing ? (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Nome</Label>
                      <Input 
                        id="name"
                        value={editForm.name}
                        onChange={(e) => setEditForm({...editForm, name: e.target.value})}
                        placeholder="Seu nome"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Telefone</Label>
                      <Input 
                        id="phone"
                        value={editForm.phone}
                        onChange={(e) => setEditForm({...editForm, phone: e.target.value})}
                        placeholder="+55 11 99999-9999"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-muted/50">
                    <div>
                      <span className="text-sm text-muted-foreground">Membro desde</span>
                      <p className="font-medium">
                        {new Date(currentUser.createdAt).toLocaleDateString("pt-BR")}
                      </p>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Último acesso</span>
                      <p className="font-medium">
                        {currentUser.lastLoginAt 
                          ? new Date(currentUser.lastLoginAt).toLocaleDateString("pt-BR")
                          : "-"
                        }
                      </p>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Status</span>
                      <p className="font-medium flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${currentUser.isActive ? 'bg-green-500' : 'bg-red-500'}`} />
                        {currentUser.isActive ? 'Ativo' : 'Inativo'}
                      </p>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Email verificado</span>
                      <p className="font-medium">
                        {currentUser.isEmailVerified ? '✓ Verificado' : '⚠ Pendente'}
                      </p>
                    </div>
                  </div>
                )}

                <Separator />

                <Button variant="outline" className="w-full" onClick={handleLogout}>
                  Sair da conta
                </Button>
              </CardContent>
            </Card>

            {/* Quick Stats Card */}
            <Card>
              <CardHeader>
                <CardTitle>Resumo da Conta</CardTitle>
                <CardDescription>Visão geral do seu plano e uso</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* License Status */}
                <div className="p-4 rounded-lg bg-gradient-to-r from-tiktrend-primary/10 to-tiktrend-secondary/10">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">Plano Atual</span>
                    <Badge variant={currentLicense.isLifetime ? "tiktrend" : "secondary"}>
                      {currentLicense.isLifetime ? "Vitalício ✓" : currentLicense.plan === 'trial' ? "Trial" : "Free"}
                    </Badge>
                  </div>
                  {currentLicense.activatedAt && (
                    <p className="text-sm text-muted-foreground">
                      Ativado em {new Date(currentLicense.activatedAt).toLocaleDateString("pt-BR")}
                    </p>
                  )}
                </div>

                {/* Credits Summary */}
                <div className="p-4 rounded-lg bg-muted/50">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-muted-foreground">Créditos IA</span>
                    <span className="text-3xl font-bold text-tiktrend-primary">
                      {totalCredits}
                    </span>
                  </div>
                  {currentCredits.bonusBalance > 0 && daysUntilBonusExpires && (
                    <p className="text-xs text-amber-600 dark:text-amber-400">
                      ⚡ {currentCredits.bonusBalance} bônus expira em {daysUntilBonusExpires} dias
                    </p>
                  )}
                </div>

                {/* Devices */}
                <div className="p-4 rounded-lg bg-muted/50">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Dispositivos</span>
                    <span className="font-medium">
                      {currentLicense.activeDevices} / {currentLicense.maxDevices}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* License Tab */}
        <TabsContent value="license" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Licença</CardTitle>
                  <CardDescription>Detalhes da sua licença e recursos disponíveis</CardDescription>
                </div>
                <Badge variant={currentLicense.isLifetime ? "tiktrend" : "outline"} className="text-lg px-4 py-1">
                  {currentLicense.isLifetime ? "Vitalícia ✓" : "Free"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* License Info */}
              {currentLicense.isLifetime ? (
                <div className="p-6 rounded-xl bg-gradient-to-r from-tiktrend-primary/10 to-tiktrend-secondary/10 border border-tiktrend-primary/20">
                  <div className="flex items-center gap-3 mb-4">
                    <ShieldCheckIcon size={32} className="text-tiktrend-primary" />
                    <div>
                      <h3 className="text-xl font-bold">Licença Vitalícia Ativa</h3>
                      <p className="text-muted-foreground">Acesso completo a todas as funcionalidades</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">ID da Licença</span>
                      <p className="font-mono text-xs">{currentLicense.id}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Ativada em</span>
                      <p>{currentLicense.activatedAt ? new Date(currentLicense.activatedAt).toLocaleDateString("pt-BR") : "-"}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-6 rounded-xl border-2 border-dashed border-muted-foreground/20">
                  <div className="text-center space-y-4">
                    <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                      <StarIcon size={32} className="text-muted-foreground" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold">Atualize para Vitalício</h3>
                      <p className="text-muted-foreground">Desbloqueie todas as funcionalidades</p>
                    </div>
                    <Button variant="tiktrend" size="lg">
                      Comprar Licença - R$ 49,90
                    </Button>
                  </div>
                </div>
              )}

              <Separator />

              {/* Features Comparison */}
              <div className="grid md:grid-cols-2 gap-6">
                <div className="p-4 rounded-lg border">
                  <h4 className="font-medium mb-4">Versão Gratuita</h4>
                  <ul className="space-y-2 text-sm">
                    <li>✅ Busca de produtos</li>
                    <li>✅ 3 listas de favoritos</li>
                    <li>✅ 10 créditos de cortesia</li>
                    <li>❌ Exportação de dados</li>
                    <li>❌ Comparação avançada</li>
                    <li>❌ Prioridade no suporte</li>
                  </ul>
                </div>

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
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Credits Tab */}
        <TabsContent value="credits" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Balance Card */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <StarIcon size={24} className="text-tiktrend-primary" />
                  Créditos IA
                </CardTitle>
                <CardDescription>Use créditos para gerar copies e análises com IA</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-gradient-to-br from-tiktrend-primary/20 to-tiktrend-primary/5 text-center">
                    <p className="text-4xl font-bold text-tiktrend-primary">{currentCredits.balance}</p>
                    <p className="text-sm text-muted-foreground">Saldo</p>
                  </div>
                  <div className="p-4 rounded-lg bg-amber-500/10 text-center">
                    <p className="text-4xl font-bold text-amber-600">{currentCredits.bonusBalance}</p>
                    <p className="text-sm text-muted-foreground">Bônus</p>
                  </div>
                  <div className="p-4 rounded-lg bg-muted text-center">
                    <p className="text-4xl font-bold">{currentCredits.totalUsed}</p>
                    <p className="text-sm text-muted-foreground">Usados</p>
                  </div>
                </div>

                <Separator />

                <div className="space-y-2">
                  <h4 className="font-medium">Consumo por Ação</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex justify-between p-2 rounded bg-muted/50">
                      <span>Copy simples</span>
                      <span className="font-medium">1 crédito</span>
                    </div>
                    <div className="flex justify-between p-2 rounded bg-muted/50">
                      <span>Análise de produto</span>
                      <span className="font-medium">2 créditos</span>
                    </div>
                    <div className="flex justify-between p-2 rounded bg-muted/50">
                      <span>Lote de copies</span>
                      <span className="font-medium">5 créditos</span>
                    </div>
                    <div className="flex justify-between p-2 rounded bg-muted/50">
                      <span>Landing page</span>
                      <span className="font-medium">10 créditos</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Buy Credits Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CreditCardIcon size={20} />
                  Comprar Créditos
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 rounded-lg border hover:border-tiktrend-primary cursor-pointer transition-colors">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">Starter</p>
                      <p className="text-sm text-muted-foreground">50 créditos</p>
                    </div>
                    <Badge variant="outline">R$ 19,90</Badge>
                  </div>
                </div>
                <div className="p-3 rounded-lg border border-tiktrend-primary bg-tiktrend-primary/5 cursor-pointer">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">Pro</p>
                      <p className="text-sm text-muted-foreground">200 créditos</p>
                    </div>
                    <Badge variant="tiktrend">R$ 49,90</Badge>
                  </div>
                  <p className="text-xs text-tiktrend-primary mt-1">Mais popular</p>
                </div>
                <div className="p-3 rounded-lg border hover:border-tiktrend-primary cursor-pointer transition-colors">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">Ultra</p>
                      <p className="text-sm text-muted-foreground">500 créditos</p>
                    </div>
                    <Badge variant="outline">R$ 99,90</Badge>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground text-center mt-2">
                  Créditos nunca expiram
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Devices Tab */}
        <TabsContent value="devices" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DeviceIcon size={24} />
                Dispositivos Autorizados
              </CardTitle>
              <CardDescription>
                Gerencie os dispositivos conectados à sua conta ({currentLicense.activeDevices}/{currentLicense.maxDevices})
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Current Device */}
              <div className="p-4 rounded-lg border border-green-500/50 bg-green-500/5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                      <DeviceIcon size={20} className="text-green-600" />
                    </div>
                    <div>
                      <p className="font-medium">Este dispositivo</p>
                      <p className="text-xs text-muted-foreground font-mono">
                        {currentLicense.currentDeviceId || "device_123"}
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-green-600 border-green-500">
                    Atual
                  </Badge>
                </div>
              </div>

              {currentLicense.activeDevices > 1 && (
                <div className="p-4 rounded-lg border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
                        <DeviceIcon size={20} className="text-muted-foreground" />
                      </div>
                      <div>
                        <p className="font-medium">Outro dispositivo</p>
                        <p className="text-xs text-muted-foreground">Último acesso: há 3 dias</p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">Desconectar</Button>
                  </div>
                </div>
              )}

              {currentLicense.activeDevices < currentLicense.maxDevices && (
                <div className="p-4 rounded-lg border border-dashed border-muted-foreground/30 text-center">
                  <p className="text-sm text-muted-foreground">
                    Você pode conectar mais {currentLicense.maxDevices - currentLicense.activeDevices} dispositivo(s)
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Profile;
