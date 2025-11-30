import * as React from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  SettingsIcon,
  SearchIcon,
  CopyIcon,
  ChartIcon,
  StarIcon
} from "@/components/icons";
import { useUserStore } from "@/stores";
import type {
  AppSettings,
  CredentialsConfig,
  ScraperConfig,
  LicenseConfig,
  SystemConfig,
  CopyType,
  CopyTone
} from "@/types";
import { invoke } from "@tauri-apps/api/core";
import { whatsappService, youtubeService, tiktokService } from "@/services";
import { SUPPORTED_LANGUAGES, changeLanguage, type SupportedLanguage } from "@/lib/i18n";

// =============================================================================
// Tipos
// =============================================================================

// Interfaces imported from @/types

const defaultCredentials: CredentialsConfig = {
  openaiKey: "",
  proxies: [],
};

const defaultScraperConfig: ScraperConfig = {
  maxProducts: 50,
  intervalMinutes: 60,
  categories: [],
  useProxy: false,
  headless: true,
  timeout: 30000,
};

const defaultLicenseConfig: LicenseConfig = {
  key: null,
  plan: "lifetime",
  expiresAt: null,
  trialStarted: null,
  isActive: true,
  credits: 0,
};

const defaultSystemConfig: SystemConfig = {
  autoUpdate: true,
  checkInterval: 24,
  logsEnabled: true,
  maxLogSize: 10,
  analyticsEnabled: false,
};

const defaultSettings: AppSettings = {
  theme: "system",
  language: "pt-BR",
  notificationsEnabled: true,
  autoUpdate: true,
  maxProductsPerSearch: 50,
  cacheImages: true,
  proxyEnabled: false,
  proxyList: [],
  openaiModel: "gpt-4",
  defaultCopyType: "tiktok_hook",
  defaultCopyTone: "urgent",
  setupComplete: false,
  termsAccepted: false,
  termsAcceptedAt: null,
  credentials: defaultCredentials,
  scraper: defaultScraperConfig,
  license: defaultLicenseConfig,
  system: defaultSystemConfig,
};

// ... existing imports

// =============================================================================
// Seções de Tabs
// =============================================================================

type SettingsTab = "general" | "credentials" | "scraper" | "license" | "system" | "integrations";

interface TabButtonProps {
  tab: SettingsTab;
  currentTab: SettingsTab;
  onClick: (tab: SettingsTab) => void;
  icon: React.ReactNode;
  label: string;
}

const TabButton: React.FC<TabButtonProps> = ({ tab, currentTab, onClick, icon, label }) => (
  <button
    onClick={() => onClick(tab)}
    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${currentTab === tab
      ? "bg-tiktrend-primary text-white"
      : "hover:bg-muted text-muted-foreground hover:text-foreground"
      }`}
  >
    {icon}
    <span className="font-medium">{label}</span>
  </button>
);

// =============================================================================
// Componente Principal
// =============================================================================

export const Settings: React.FC = () => {
  const { t: tFunc } = useTranslation();
  const { theme, setTheme } = useUserStore();
  const [activeTab, setActiveTab] = React.useState<SettingsTab>("general");
  const [settings, setSettings] = React.useState<AppSettings>(defaultSettings);
  const [credentials, setCredentials] = React.useState<CredentialsConfig>(defaultCredentials);
  const [scraperConfig, setScraperConfig] = React.useState<ScraperConfig>(defaultScraperConfig);
  const [licenseConfig, setLicenseConfig] = React.useState<LicenseConfig>(defaultLicenseConfig);
  const [systemConfig, setSystemConfig] = React.useState<SystemConfig>(defaultSystemConfig);
  const [isSaving, setIsSaving] = React.useState(false);
  const [saveMessage, setSaveMessage] = React.useState<string | null>(null);

  // Integration States
  const [whatsappStatus, setWhatsappStatus] = React.useState<"connected" | "disconnected" | "connecting">("disconnected");
  const [whatsappQr, setWhatsappQr] = React.useState<string | null>(null);
  const [whatsappInstanceName] = React.useState("default");
  const [youtubeAccounts, setYoutubeAccounts] = React.useState<string[]>([]);
  const [tiktokAccounts, setTiktokAccounts] = React.useState<string[]>([]);

  // Polling ref
  const pollInterval = React.useRef<NodeJS.Timeout | null>(null);

  // Check status on mount
  React.useEffect(() => {
    checkWhatsappStatus();
    fetchConnectedAccounts();
    return () => stopPolling();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchConnectedAccounts = async () => {
    try {
      const yt = await youtubeService.listAccounts();
      setYoutubeAccounts(yt.accounts.map(a => a.accountName));

      const tt = await tiktokService.listSessions();
      setTiktokAccounts(tt.sessions.map(s => s.accountName));
    } catch (error) {
      console.error("Error fetching accounts:", error);
    }
  };

  const stopPolling = () => {
    if (pollInterval.current) {
      clearInterval(pollInterval.current);
      pollInterval.current = null;
    }
  };

  const startPolling = () => {
    stopPolling();
    pollInterval.current = setInterval(checkWhatsappStatus, 3000);
  };

  const checkWhatsappStatus = async () => {
    try {
      const { data } = await whatsappService.getStatus(whatsappInstanceName);

      if (data.status === "connected") {
        setWhatsappStatus("connected");
        setWhatsappQr(null);
        // Keep polling but slower to detect disconnects
        if (pollInterval.current) {
          clearInterval(pollInterval.current);
          pollInterval.current = setInterval(checkWhatsappStatus, 10000);
        }
      } else if (data.status === "awaiting_scan") {
        setWhatsappStatus("connecting");
        if (data.qr_code) {
          setWhatsappQr(data.qr_code);
        }
      } else {
        setWhatsappStatus("disconnected");
      }
    } catch (error) {
      // Instance might not exist or error
      // setWhatsappStatus("disconnected");
    }
  };

  // Handlers
  const handleThemeChange = (newTheme: "light" | "dark" | "system") => {
    setTheme(newTheme);
    setSettings((prev) => ({ ...prev, theme: newTheme }));
  };

  const handleLanguageChange = async (lang: SupportedLanguage) => {
    try {
      await changeLanguage(lang);
      setSettings((prev) => ({ ...prev, language: lang }));
      setSaveMessage(tFunc("settings.saved"));
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      console.error("Error changing language:", error);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage(null);

    try {
      const fullSettings: AppSettings = {
        ...settings,
        credentials,
        scraper: scraperConfig,
        license: licenseConfig,
        system: systemConfig,
      };

      await invoke("save_settings", { settings: fullSettings });

      // Simular delay
      await new Promise(resolve => setTimeout(resolve, 500));

      setSaveMessage("Configurações salvas com sucesso!");
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      console.error("Error saving settings:", error);
      setSaveMessage("Erro ao salvar configurações");
    } finally {
      setIsSaving(false);
    }
  };

  const handleActivateLicense = async () => {
    if (!licenseConfig.key) return;

    try {
      // TODO: Validar licença via API
      // const result = await invoke("validate_license", { key: licenseConfig.key });

      setLicenseConfig(prev => ({
        ...prev,
        isActive: true,
        plan: "lifetime", // Licença vitalícia
      }));

      setSaveMessage("Licença ativada com sucesso!");
    } catch {
      setSaveMessage("Chave de licença inválida");
    }
  };

  // Integration Handlers
  const handleConnectWhatsapp = async () => {
    setWhatsappStatus("connecting");
    try {
      // 1. Create instance (ignore error if exists)
      try {
        await whatsappService.createInstance(whatsappInstanceName);
      } catch (e) {
        // Ignore
      }

      // 2. Get QR Code
      const { data } = await whatsappService.getQrCode(whatsappInstanceName);
      if (data.base64) {
        setWhatsappQr(data.base64);
      }

      // 3. Start polling
      startPolling();

    } catch (error) {
      console.error("Error connecting WhatsApp:", error);
      setWhatsappStatus("disconnected");
      setSaveMessage("Erro ao conectar WhatsApp");
    }
  };

  const handleDisconnectWhatsapp = async () => {
    try {
      // For now just stop polling and reset UI
      stopPolling();
      setWhatsappStatus("disconnected");
      setWhatsappQr(null);

      // Optional: Call reconnect to force disconnect/reset if needed
      // await whatsappService.reconnect(whatsappInstanceName);
    } catch (error) {
      console.error("Error disconnecting WhatsApp:", error);
    }
  };

  // ==========================================================================
  // Render Tabs
  // ==========================================================================

  const renderIntegrationsSettings = () => (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* WhatsApp */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-green-500">📱</span> WhatsApp
            {whatsappStatus === "connected" && <Badge variant="tiktrend" className="ml-2">Conectado</Badge>}
            {whatsappStatus === "disconnected" && <Badge variant="outline" className="ml-2">Desconectado</Badge>}
          </CardTitle>
          <CardDescription>
            Conecte seu WhatsApp para enviar notificações e mensagens
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {whatsappStatus === "disconnected" && !whatsappQr && (
            <Button onClick={handleConnectWhatsapp} className="w-full bg-green-600 hover:bg-green-700">
              Conectar WhatsApp
            </Button>
          )}

          {whatsappStatus === "connecting" && whatsappQr && (
            <div className="flex flex-col items-center gap-4 p-4 border rounded-lg bg-white">
              <div className="w-48 h-48 bg-white flex items-center justify-center">
                <img src={`data:image/png;base64,${whatsappQr}`} alt="WhatsApp QR Code" className="w-full h-full object-contain" />
              </div>
              <p className="text-sm text-center text-gray-600">
                Abra o WhatsApp no seu celular &gt; Menu &gt; Aparelhos conectados &gt; Conectar aparelho
              </p>
            </div>
          )}

          {whatsappStatus === "connected" && (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
                <p className="font-medium">✅ Conectado como: (11) 99999-9999</p>
              </div>
              <Button variant="destructive" onClick={handleDisconnectWhatsapp} className="w-full">
                Desconectar
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* YouTube */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-red-500">▶️</span> YouTube
          </CardTitle>
          <CardDescription>
            Gerencie suas contas do YouTube para upload de vídeos
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            {youtubeAccounts.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">Nenhuma conta conectada</p>
            ) : (
              youtubeAccounts.map(acc => (
                <div key={acc} className="flex items-center justify-between p-2 border rounded">
                  <span className="font-medium">{acc}</span>
                  <Button variant="ghost" size="sm" className="text-red-500">Remover</Button>
                </div>
              ))
            )}
          </div>
          <Button variant="outline" className="w-full border-red-200 text-red-600 hover:bg-red-50">
            + Adicionar Conta YouTube
          </Button>
        </CardContent>
      </Card>

      {/* TikTok */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-black">🎵</span> TikTok
          </CardTitle>
          <CardDescription>
            Gerencie suas sessões do TikTok para upload
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            {tiktokAccounts.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">Nenhuma conta conectada</p>
            ) : (
              tiktokAccounts.map(acc => (
                <div key={acc} className="flex items-center justify-between p-2 border rounded">
                  <span className="font-medium">{acc}</span>
                  <Button variant="ghost" size="sm" className="text-red-500">Remover</Button>
                </div>
              ))
            )}
          </div>
          <Button variant="outline" className="w-full border-black text-black hover:bg-gray-50">
            + Adicionar Conta TikTok (Cookies)
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  const renderGeneralSettings = () => (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Aparência */}
      <Card>
        <CardHeader>
          <CardTitle>{tFunc("settings.appearance.title")}</CardTitle>
          <CardDescription>
            {tFunc("settings.appearance.theme")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">{tFunc("settings.appearance.theme")}</label>
            <div className="flex gap-2">
              {(["light", "dark", "system"] as const).map((themeOption) => (
                <Button
                  key={themeOption}
                  variant={theme === themeOption ? "default" : "outline"}
                  onClick={() => handleThemeChange(themeOption)}
                  className={theme === themeOption ? "bg-tiktrend-primary hover:bg-tiktrend-primary/90" : ""}
                >
                  {themeOption === "light" ? `☀️ ${tFunc("settings.appearance.themes.light")}` : themeOption === "dark" ? `🌙 ${tFunc("settings.appearance.themes.dark")}` : `💻 ${tFunc("settings.appearance.themes.system")}`}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">{tFunc("settings.appearance.language")}</label>
            <div className="flex gap-2 flex-wrap">
              {SUPPORTED_LANGUAGES.map((lang) => (
                <Button
                  key={lang.code}
                  variant={settings.language === lang.code ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleLanguageChange(lang.code)}
                  className={settings.language === lang.code ? "bg-tiktrend-primary hover:bg-tiktrend-primary/90" : ""}
                >
                  {lang.flag} {lang.name}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notificações */}
      <Card>
        <CardHeader>
          <CardTitle>Notificações</CardTitle>
          <CardDescription>
            Configure alertas e notificações
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Notificações Desktop</div>
              <div className="text-sm text-muted-foreground">
                Receber alertas de novos produtos em tendência
              </div>
            </div>
            <Button
              variant={settings.notificationsEnabled ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSettings((prev) => ({ ...prev, notificationsEnabled: !prev.notificationsEnabled }))
              }
            >
              {settings.notificationsEnabled ? "Ativado" : "Desativado"}
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Cache de imagens</div>
              <div className="text-sm text-muted-foreground">
                Salvar imagens localmente para carregamento rápido
              </div>
            </div>
            <Button
              variant={settings.cacheImages ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSettings((prev) => ({ ...prev, cacheImages: !prev.cacheImages }))
              }
            >
              {settings.cacheImages ? "Ativado" : "Desativado"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Busca */}
      <Card>
        <CardHeader>
          <CardTitle>Busca</CardTitle>
          <CardDescription>
            Configure os parâmetros de busca padrão
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Produtos por busca</label>
            <Input
              type="number"
              value={settings.maxProductsPerSearch}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setSettings((prev) => ({
                  ...prev,
                  maxProductsPerSearch: parseInt(e.target.value) || 50,
                }))
              }
              min={10}
              max={100}
            />
            <p className="text-xs text-muted-foreground">
              Máximo de produtos retornados por busca (10-100)
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Tutorial */}
      <Card>
        <CardHeader>
          <CardTitle>Tutorial & Setup</CardTitle>
          <CardDescription>
            Reveja o tutorial interativo ou reconfigure a plataforma
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => {
                localStorage.removeItem('tutorial_completed');
                window.dispatchEvent(new Event('restart_tutorial'));
              }}
            >
              🔄 Reiniciar Tutorial
            </Button>
            <Button
              variant="outline"
              className="text-destructive hover:text-destructive"
              onClick={async () => {
                if (confirm('Isso vai resetar todas as configurações iniciais e reabrir o assistente de configuração. Deseja continuar?')) {
                  const { resetSetup } = await import('@/services/settings');
                  await resetSetup();
                  window.location.href = '/setup';
                }
              }}
            >
              ⚙️ Refazer Setup Inicial
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Use "Refazer Setup" apenas se precisar reconfigurar a licença ou termos.
          </p>
        </CardContent>
      </Card>

      {/* Copy Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Geração de Copy</CardTitle>
          <CardDescription>
            Configure padrões para geração de copies
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Tipo padrão</label>
            <div className="flex flex-wrap gap-2">
              {[
                { value: "tiktok_hook", label: "🎬 TikTok Hook" },
                { value: "product_description", label: "📝 Descrição" },
                { value: "carousel", label: "📱 Carrossel" },
              ].map((type) => (
                <Button
                  key={type.value}
                  variant={settings.defaultCopyType === type.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSettings((prev) => ({ ...prev, defaultCopyType: type.value as CopyType }))}
                >
                  {type.label}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Tom padrão</label>
            <div className="flex flex-wrap gap-2">
              {[
                { value: "urgent", label: "🔥 Urgente" },
                { value: "professional", label: "💼 Profissional" },
                { value: "fun", label: "🎉 Divertido" },
              ].map((tone) => (
                <Button
                  key={tone.value}
                  variant={settings.defaultCopyTone === tone.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSettings((prev) => ({ ...prev, defaultCopyTone: tone.value as CopyTone }))}
                >
                  {tone.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderCredentialsSettings = () => (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* OpenAI API */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🤖 API OpenAI
            <Badge variant="outline" className="ml-2">Opcional</Badge>
          </CardTitle>
          <CardDescription>
            Configure a integração com OpenAI para geração de copies com IA
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Chave API</label>
            <Input
              type="password"
              placeholder="sk-..."
              value={credentials.openaiKey}
              onChange={(e) => setCredentials(prev => ({ ...prev, openaiKey: e.target.value }))}
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">
              Sua chave é armazenada localmente de forma criptografada
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Modelo</label>
            <div className="flex gap-2">
              {["gpt-4o", "gpt-4", "gpt-3.5-turbo"].map((model) => (
                <Button
                  key={model}
                  variant={settings.openaiModel === model ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSettings((prev) => ({ ...prev, openaiModel: model }))}
                >
                  {model}
                </Button>
              ))}
            </div>
          </div>

          <div className="pt-2 border-t">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>💡</span>
              <span>A geração de copies por IA é um recurso adicional. O app funciona 100% sem ela.</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Proxies */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🌐 Proxies
            <Badge variant="outline" className="ml-2">Avançado</Badge>
          </CardTitle>
          <CardDescription>
            Configure proxies para coleta de dados (recomendado para uso intensivo)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Usar Proxies</div>
              <div className="text-sm text-muted-foreground">
                Rotacionar IPs durante a coleta
              </div>
            </div>
            <Button
              variant={settings.proxyEnabled ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSettings((prev) => ({ ...prev, proxyEnabled: !prev.proxyEnabled }))
              }
            >
              {settings.proxyEnabled ? "Ativado" : "Desativado"}
            </Button>
          </div>

          {settings.proxyEnabled && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Lista de Proxies</label>
              <textarea
                className="w-full h-32 rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                placeholder="Formato: ip:porta:usuario:senha (um por linha)&#10;&#10;Exemplo:&#10;192.168.1.1:8080:user:pass&#10;proxy.example.com:3128"
                value={credentials.proxies.join("\n")}
                onChange={(e) => setCredentials(prev => ({
                  ...prev,
                  proxies: e.target.value.split("\n").filter(p => p.trim())
                }))}
              />
              <p className="text-xs text-muted-foreground">
                {credentials.proxies.length} proxy(ies) configurado(s)
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );

  const renderScraperSettings = () => (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Coleta */}
      <Card>
        <CardHeader>
          <CardTitle>⚙️ Configurações de Coleta</CardTitle>
          <CardDescription>
            Configure como o scraper coleta produtos do TikTok Shop
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Máximo de produtos por coleta</label>
            <Input
              type="number"
              value={scraperConfig.maxProducts}
              onChange={(e) => setScraperConfig(prev => ({
                ...prev,
                maxProducts: parseInt(e.target.value) || 50
              }))}
              min={10}
              max={200}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Intervalo entre coletas (minutos)</label>
            <Input
              type="number"
              value={scraperConfig.intervalMinutes}
              onChange={(e) => setScraperConfig(prev => ({
                ...prev,
                intervalMinutes: parseInt(e.target.value) || 60
              }))}
              min={15}
              max={1440}
            />
            <p className="text-xs text-muted-foreground">
              Mínimo: 15 minutos. Recomendado: 60 minutos.
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Timeout (segundos)</label>
            <Input
              type="number"
              value={scraperConfig.timeout / 1000}
              onChange={(e) => setScraperConfig(prev => ({
                ...prev,
                timeout: (parseInt(e.target.value) || 30) * 1000
              }))}
              min={10}
              max={120}
            />
          </div>
        </CardContent>
      </Card>

      {/* Modo */}
      <Card>
        <CardHeader>
          <CardTitle>🖥️ Modo de Execução</CardTitle>
          <CardDescription>
            Configure como o navegador é executado durante a coleta
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Modo Headless</div>
              <div className="text-sm text-muted-foreground">
                Executar navegador sem interface gráfica
              </div>
            </div>
            <Button
              variant={scraperConfig.headless ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setScraperConfig((prev) => ({ ...prev, headless: !prev.headless }))
              }
            >
              {scraperConfig.headless ? "Ativado" : "Desativado"}
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Usar Proxy no Scraper</div>
              <div className="text-sm text-muted-foreground">
                Aplicar proxies configurados na coleta
              </div>
            </div>
            <Button
              variant={scraperConfig.useProxy ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setScraperConfig((prev) => ({ ...prev, useProxy: !prev.useProxy }))
              }
            >
              {scraperConfig.useProxy ? "Ativado" : "Desativado"}
            </Button>
          </div>

          <div className="pt-4 border-t">
            <Button variant="outline" className="w-full">
              🧪 Testar Scraper
            </Button>
            <p className="text-xs text-muted-foreground mt-2 text-center">
              Executa uma coleta teste com 5 produtos
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Categorias */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>📂 Categorias Monitoradas</CardTitle>
          <CardDescription>
            Selecione as categorias que deseja monitorar automaticamente
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {[
              "electronics", "fashion", "beauty", "home", "sports",
              "toys", "health", "automotive", "food", "pets"
            ].map((category) => {
              const isSelected = scraperConfig.categories.includes(category);
              const labels: Record<string, string> = {
                electronics: "📱 Eletrônicos",
                fashion: "👗 Moda",
                beauty: "💄 Beleza",
                home: "🏠 Casa",
                sports: "⚽ Esportes",
                toys: "🧸 Brinquedos",
                health: "💊 Saúde",
                automotive: "🚗 Automotivo",
                food: "🍔 Alimentos",
                pets: "🐕 Pets",
              };

              return (
                <Button
                  key={category}
                  variant={isSelected ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    setScraperConfig(prev => ({
                      ...prev,
                      categories: isSelected
                        ? prev.categories.filter(c => c !== category)
                        : [...prev.categories, category]
                    }));
                  }}
                >
                  {labels[category] || category}
                </Button>
              );
            })}
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            {scraperConfig.categories.length} categoria(s) selecionada(s).
            Deixe vazio para monitorar todas.
          </p>
        </CardContent>
      </Card>
    </div>
  );

  const renderLicenseSettings = () => {
    // Novo modelo: Licença vitalícia + pacotes de créditos
    const hasLicense = licenseConfig.isActive && licenseConfig.plan === "lifetime";

    const creditPacks = [
      {
        name: "Starter",
        credits: 50,
        price: "R$ 19,90",
        perCredit: "R$ 0,40",
      },
      {
        name: "Pro",
        credits: 200,
        price: "R$ 49,90",
        perCredit: "R$ 0,25",
        recommended: true,
      },
      {
        name: "Ultra",
        credits: 500,
        price: "R$ 99,90",
        perCredit: "R$ 0,20",
      },
    ];

    return (
      <div className="space-y-6">
        {/* Licença Vitalícia */}
        <Card className={hasLicense ? "border-green-500/50" : "border-tiktrend-primary/50"}>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>🎫 Licença Vitalícia</span>
              {hasLicense ? (
                <Badge variant="tiktrend">Ativa ✓</Badge>
              ) : (
                <Badge variant="secondary">R$ 49,90</Badge>
              )}
            </CardTitle>
            <CardDescription>
              Pague uma vez, use para sempre. Sem mensalidades!
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {hasLicense ? (
              <div className="text-sm text-muted-foreground">
                <p>✅ Acesso ilimitado a todas as funcionalidades</p>
                <p>✅ Buscas ilimitadas de produtos</p>
                <p>✅ Favoritos e listas ilimitadas</p>
                <p>✅ Exportação de dados</p>
                <p className="mt-2 text-xs">Créditos IA são cobrados separadamente</p>
              </div>
            ) : (
              <>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>
                    Acesso ilimitado para sempre
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>
                    Buscas e favoritos ilimitados
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>
                    Exportação de dados
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>
                    Atualizações gratuitas
                  </li>
                </ul>
                <Button variant="tiktrend" className="w-full">
                  Comprar Licença - R$ 49,90
                </Button>
              </>
            )}

            <div className="pt-4 border-t space-y-2">
              <label className="text-sm font-medium">Ativar Chave de Licença</label>
              <div className="flex gap-2">
                <Input
                  placeholder="XXXX-XXXX-XXXX-XXXX"
                  value={licenseConfig.key || ""}
                  onChange={(e) => setLicenseConfig(prev => ({ ...prev, key: e.target.value }))}
                  className="font-mono"
                />
                <Button
                  variant="tiktrend"
                  onClick={handleActivateLicense}
                  disabled={!licenseConfig.key}
                >
                  Ativar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Pacotes de Créditos IA */}
        <Card>
          <CardHeader>
            <CardTitle>🤖 Créditos IA</CardTitle>
            <CardDescription>
              Use créditos para gerar copies com inteligência artificial
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4 p-3 bg-muted rounded-lg">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Seus créditos:</span>
                <span className="text-2xl font-bold text-tiktrend-primary">{licenseConfig.credits}</span>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Copy simples: 1 crédito | Análise: 2 créditos | Lote: 5 créditos
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {creditPacks.map((pack) => (
                <Card
                  key={pack.name}
                  className={pack.recommended ? "ring-2 ring-tiktrend-primary ring-offset-2" : ""}
                >
                  {pack.recommended && (
                    <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-tiktrend-primary">
                      Melhor Valor
                    </Badge>
                  )}
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg">{pack.name}</CardTitle>
                    <div className="flex items-baseline">
                      <span className="text-2xl font-bold">{pack.credits}</span>
                      <span className="text-muted-foreground text-sm ml-1">créditos</span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center mb-4">
                      <span className="text-xl font-bold">{pack.price}</span>
                      <p className="text-xs text-muted-foreground">{pack.perCredit}/crédito</p>
                    </div>
                    <Button className="w-full" variant={pack.recommended ? "tiktrend" : "default"}>
                      Comprar
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="text-center text-sm text-muted-foreground">
          <p>Pagamentos processados com segurança via Mercado Pago 🔒</p>
          <p className="mt-1">Dúvidas? Entre em contato: suporte@didinfacil.com</p>
        </div>
      </div>
    );
  };

  const renderSystemSettings = () => (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Atualizações */}
      <Card>
        <CardHeader>
          <CardTitle>🔄 Atualizações</CardTitle>
          <CardDescription>
            Configure atualizações automáticas do aplicativo
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Atualização Automática</div>
              <div className="text-sm text-muted-foreground">
                Baixar e instalar atualizações automaticamente
              </div>
            </div>
            <Button
              variant={systemConfig.autoUpdate ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSystemConfig((prev) => ({ ...prev, autoUpdate: !prev.autoUpdate }))
              }
            >
              {systemConfig.autoUpdate ? "Ativado" : "Desativado"}
            </Button>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Verificar a cada (horas)</label>
            <Input
              type="number"
              value={systemConfig.checkInterval}
              onChange={(e) => setSystemConfig(prev => ({
                ...prev,
                checkInterval: parseInt(e.target.value) || 24
              }))}
              min={1}
              max={168}
            />
          </div>

          <div className="pt-4 border-t">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Versão atual:</span>
              <Badge variant="outline">v1.0.0</Badge>
            </div>
            <Button variant="outline" className="w-full mt-3">
              🔍 Verificar Atualizações
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs */}
      <Card>
        <CardHeader>
          <CardTitle>📋 Logs e Diagnóstico</CardTitle>
          <CardDescription>
            Configure logs para troubleshooting
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Logs Ativados</div>
              <div className="text-sm text-muted-foreground">
                Salvar logs de operações do sistema
              </div>
            </div>
            <Button
              variant={systemConfig.logsEnabled ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSystemConfig((prev) => ({ ...prev, logsEnabled: !prev.logsEnabled }))
              }
            >
              {systemConfig.logsEnabled ? "Ativado" : "Desativado"}
            </Button>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Tamanho máximo de log (MB)</label>
            <Input
              type="number"
              value={systemConfig.maxLogSize}
              onChange={(e) => setSystemConfig(prev => ({
                ...prev,
                maxLogSize: parseInt(e.target.value) || 10
              }))}
              min={1}
              max={100}
            />
          </div>

          <div className="flex gap-2 pt-2">
            <Button variant="outline" className="flex-1">
              📂 Abrir Pasta de Logs
            </Button>
            <Button variant="outline" className="flex-1">
              🗑️ Limpar Logs
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Analytics */}
      <Card>
        <CardHeader>
          <CardTitle>📊 Analytics</CardTitle>
          <CardDescription>
            Ajude a melhorar o TikTrend Finder (opcional)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Analytics Anônimos</div>
              <div className="text-sm text-muted-foreground">
                Enviar dados de uso anônimos para melhorias
              </div>
            </div>
            <Button
              variant={systemConfig.analyticsEnabled ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSystemConfig((prev) => ({ ...prev, analyticsEnabled: !prev.analyticsEnabled }))
              }
            >
              {systemConfig.analyticsEnabled ? "Ativado" : "Desativado"}
            </Button>
          </div>

          <div className="text-xs text-muted-foreground bg-muted p-3 rounded-md">
            <p className="font-medium mb-1">Dados coletados (se ativado):</p>
            <ul className="space-y-1">
              <li>• Versão do app e sistema operacional</li>
              <li>• Funcionalidades mais usadas</li>
              <li>• Erros encontrados</li>
            </ul>
            <p className="mt-2">Nenhum dado pessoal ou de produtos é coletado.</p>
          </div>
        </CardContent>
      </Card>

      {/* Data */}
      <Card>
        <CardHeader>
          <CardTitle>💾 Dados e Armazenamento</CardTitle>
          <CardDescription>
            Gerencie os dados armazenados localmente
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="p-3 bg-muted rounded-md">
              <div className="text-muted-foreground">Banco de dados</div>
              <div className="font-medium">12.4 MB</div>
            </div>
            <div className="p-3 bg-muted rounded-md">
              <div className="text-muted-foreground">Cache de imagens</div>
              <div className="font-medium">45.2 MB</div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" className="flex-1">
              📤 Exportar Dados
            </Button>
            <Button variant="outline" className="flex-1">
              📥 Importar Dados
            </Button>
          </div>

          <Button variant="destructive" className="w-full">
            🗑️ Limpar Todos os Dados
          </Button>
          <p className="text-xs text-muted-foreground text-center">
            Esta ação não pode ser desfeita. Faça backup antes.
          </p>
        </CardContent>
      </Card>
    </div>
  );

  // ==========================================================================
  // Render Principal
  // ==========================================================================

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <SettingsIcon size={32} className="text-tiktrend-primary" />
          Configurações
        </h1>
        <p className="text-muted-foreground">
          Personalize o TikTrend Finder de acordo com suas preferências
        </p>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b pb-4">
        <TabButton
          tab="general"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<SettingsIcon size={18} />}
          label="Geral"
        />
        <TabButton
          tab="credentials"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<CopyIcon size={18} />}
          label="Credenciais"
        />
        <TabButton
          tab="scraper"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<SearchIcon size={18} />}
          label="Scraper"
        />
        <TabButton
          tab="license"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<StarIcon size={18} />}
          label="Licença"
        />
        <TabButton
          tab="system"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<ChartIcon size={18} />}
          label="Sistema"
        />
        <TabButton
          tab="integrations"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<span className="text-lg">🔗</span>}
          label="Integrações"
        />
      </div>

      {/* Content */}
      <div className="min-h-[500px]">
        {activeTab === "general" && renderGeneralSettings()}
        {activeTab === "credentials" && renderCredentialsSettings()}
        {activeTab === "scraper" && renderScraperSettings()}
        {activeTab === "license" && renderLicenseSettings()}
        {activeTab === "system" && renderSystemSettings()}
        {activeTab === "integrations" && renderIntegrationsSettings()}
      </div>

      {/* Save Bar */}
      <div className="flex items-center justify-between pt-6 border-t">
        <div>
          {saveMessage && (
            <span className={`text-sm ${saveMessage.includes("Erro") ? "text-red-500" : "text-green-500"}`}>
              {saveMessage}
            </span>
          )}
        </div>
        <Button
          variant="tiktrend"
          size="lg"
          onClick={handleSave}
          disabled={isSaving}
        >
          {isSaving ? "Salvando..." : "Salvar Configurações"}
        </Button>
      </div>
    </div>
  );
};
