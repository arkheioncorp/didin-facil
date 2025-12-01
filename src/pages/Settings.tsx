import * as React from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, InfoTooltip, SettingLabel, HelpSection } from "@/components/ui";
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
import { HelpCircle, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
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
import { whatsappService, youtubeService, tiktokService } from "@/services";

// Check if running in Tauri
const isTauri = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
};

// Safe invoke wrapper
const safeInvoke = async <T,>(cmd: string, args?: Record<string, unknown>): Promise<T | null> => {
  if (isTauri()) {
    const { invoke } = await import("@tauri-apps/api/core");
    return invoke<T>(cmd, args);
  }
  // Browser fallback - use localStorage
  if (cmd === "save_settings" && args?.settings) {
    localStorage.setItem("app_settings", JSON.stringify(args.settings));
    return null;
  }
  return null;
};
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

      await safeInvoke("save_settings", { settings: fullSettings });

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
      <Card className={`border-l-4 ${whatsappStatus === "connected" ? "border-l-green-500" : "border-l-gray-300"}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-green-500">📱</span> {tFunc("settings.integrations.whatsapp.title")}
            {whatsappStatus === "connected" && (
              <Badge variant="tiktrend" className="ml-2">
                <CheckCircle2 className="h-3 w-3 mr-1" /> {tFunc("settings.integrations.whatsapp.status.connected")}
              </Badge>
            )}
            {whatsappStatus === "disconnected" && (
              <Badge variant="outline" className="ml-2">
                <XCircle className="h-3 w-3 mr-1" /> {tFunc("settings.integrations.whatsapp.status.disconnected")}
              </Badge>
            )}
            {whatsappStatus === "connecting" && (
              <Badge variant="secondary" className="ml-2 animate-pulse">
                {tFunc("settings.integrations.whatsapp.status.connecting")}
              </Badge>
            )}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.integrations.whatsapp.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {whatsappStatus === "disconnected" && !whatsappQr && (
            <Button onClick={handleConnectWhatsapp} className="w-full bg-green-600 hover:bg-green-700">
              <CheckCircle2 className="h-4 w-4 mr-2" /> {tFunc("settings.integrations.whatsapp.connect")}
            </Button>
          )}

          {whatsappStatus === "connecting" && whatsappQr && (
            <div className="flex flex-col items-center gap-4 p-4 border-2 border-dashed border-green-200 rounded-lg bg-green-50/50 dark:bg-green-950/20">
              <div className="w-48 h-48 bg-white rounded-lg shadow-lg flex items-center justify-center p-2">
                <img src={`data:image/png;base64,${whatsappQr}`} alt="WhatsApp QR Code" className="w-full h-full object-contain" />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-foreground mb-1">📱 Escaneie o QR Code</p>
                <p className="text-xs text-muted-foreground">
                  {tFunc("settings.integrations.whatsapp.scan_qr")}
                </p>
              </div>
            </div>
          )}

          {whatsappStatus === "connected" && (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-900 rounded-lg">
                <p className="font-medium text-green-800 dark:text-green-200 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5" />
                  {tFunc("settings.integrations.whatsapp.connected_as")}: (11) 99999-9999
                </p>
              </div>
              <Button variant="destructive" onClick={handleDisconnectWhatsapp} className="w-full">
                <XCircle className="h-4 w-4 mr-2" /> {tFunc("settings.integrations.whatsapp.disconnect")}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* YouTube */}
      <Card className={`border-l-4 ${youtubeAccounts.length > 0 ? "border-l-red-500" : "border-l-gray-300"}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-red-500">▶️</span> {tFunc("settings.integrations.youtube.title")}
            {youtubeAccounts.length > 0 && (
              <Badge variant="outline" className="ml-2 border-red-200 text-red-600">
                {youtubeAccounts.length} conta(s)
              </Badge>
            )}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.integrations.youtube.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            {youtubeAccounts.length === 0 ? (
              <div className="p-4 text-center bg-muted/30 rounded-lg border border-dashed">
                <p className="text-sm text-muted-foreground italic">{tFunc("settings.integrations.youtube.no_accounts")}</p>
              </div>
            ) : (
              youtubeAccounts.map(acc => (
                <div key={acc} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center">
                      <span className="text-red-600 dark:text-red-400 text-sm">▶️</span>
                    </div>
                    <span className="font-medium">{acc}</span>
                  </div>
                  <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700 hover:bg-red-100">
                    {tFunc("settings.integrations.youtube.remove")}
                  </Button>
                </div>
              ))
            )}
          </div>
          <Button variant="outline" className="w-full border-red-200 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30">
            + {tFunc("settings.integrations.youtube.add_account")}
          </Button>
        </CardContent>
      </Card>

      {/* Instagram */}
      <Card className="border-l-4 border-l-pink-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-pink-500">📸</span> {tFunc("settings.integrations.instagram.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.integrations.instagram.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-muted/30 rounded-lg border border-dashed">
            <p className="text-sm text-muted-foreground italic flex items-center gap-2">
              <HelpCircle className="h-4 w-4" />
              {tFunc("settings.integrations.instagram.via_whatsapp")}
            </p>
          </div>
          <Button 
            variant="outline" 
            className="w-full border-pink-200 text-pink-600 hover:bg-pink-50 dark:hover:bg-pink-950/30"
            onClick={() => window.location.href = '/social/instagram'}
          >
            📸 {tFunc("settings.integrations.instagram.manage")}
          </Button>
        </CardContent>
      </Card>

      {/* TikTok */}
      <Card className={`border-l-4 ${tiktokAccounts.length > 0 ? "border-l-black" : "border-l-gray-300"}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🎵</span> {tFunc("settings.integrations.tiktok.title")}
            {tiktokAccounts.length > 0 && (
              <Badge variant="outline" className="ml-2">
                {tiktokAccounts.length} sessão(ões)
              </Badge>
            )}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.integrations.tiktok.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            {tiktokAccounts.length === 0 ? (
              <div className="p-4 text-center bg-muted/30 rounded-lg border border-dashed">
                <p className="text-sm text-muted-foreground italic">{tFunc("settings.integrations.tiktok.no_accounts")}</p>
              </div>
            ) : (
              tiktokAccounts.map(acc => (
                <div key={acc} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                      <span className="text-sm">🎵</span>
                    </div>
                    <span className="font-medium">{acc}</span>
                  </div>
                  <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700 hover:bg-red-100">
                    {tFunc("settings.integrations.tiktok.remove")}
                  </Button>
                </div>
              ))
            )}
          </div>
          <Button 
            variant="outline" 
            className="w-full"
            onClick={() => window.location.href = '/social/tiktok'}
          >
            + {tFunc("settings.integrations.tiktok.add_account")}
          </Button>
        </CardContent>
      </Card>

      {/* API Configuration */}
      <Card className="lg:col-span-2 border-l-4 border-l-cyan-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>⚙️</span> {tFunc("settings.integrations.api_config.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.integrations.api_config.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <SettingLabel
                label={tFunc("settings.integrations.api_config.evolution_url.label")}
                description={tFunc("settings.integrations.api_config.evolution_url.description")}
              />
              <Input 
                placeholder={tFunc("settings.integrations.api_config.evolution_url.placeholder")}
                value={systemConfig.evolutionApiUrl || ''}
                onChange={(e) => setSystemConfig({...systemConfig, evolutionApiUrl: e.target.value})}
                className="font-mono"
              />
            </div>
            <div className="space-y-3">
              <SettingLabel
                label={tFunc("settings.integrations.api_config.evolution_key.label")}
                description={tFunc("settings.integrations.api_config.evolution_key.description")}
              />
              <Input 
                type="password"
                placeholder={tFunc("settings.integrations.api_config.evolution_key.placeholder")}
                value={systemConfig.evolutionApiKey || ''}
                onChange={(e) => setSystemConfig({...systemConfig, evolutionApiKey: e.target.value})}
                className="font-mono"
              />
            </div>
          </div>
          <div className="pt-4 border-t mt-4">
            <Button onClick={handleSave} disabled={isSaving} className="bg-tiktrend-primary hover:bg-tiktrend-primary/90">
              {isSaving ? tFunc("settings.saving") : tFunc("settings.save_button")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderGeneralSettings = () => (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Aparência */}
      <Card className="border-l-4 border-l-tiktrend-primary/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🎨 {tFunc("settings.appearance.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.appearance.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-3">
            <SettingLabel
              label={tFunc("settings.appearance.theme")}
              tooltip={tFunc("settings.appearance.theme_tooltip")}
            />
            <div className="flex gap-2 flex-wrap">
              {(["light", "dark", "system"] as const).map((themeOption) => (
                <Button
                  key={themeOption}
                  variant={theme === themeOption ? "default" : "outline"}
                  onClick={() => handleThemeChange(themeOption)}
                  className={`transition-all ${theme === themeOption ? "bg-tiktrend-primary hover:bg-tiktrend-primary/90 ring-2 ring-tiktrend-primary/30" : "hover:border-tiktrend-primary/50"}`}
                >
                  {themeOption === "light" ? `☀️ ${tFunc("settings.appearance.themes.light")}` : themeOption === "dark" ? `🌙 ${tFunc("settings.appearance.themes.dark")}` : `💻 ${tFunc("settings.appearance.themes.system")}`}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <SettingLabel
              label={tFunc("settings.appearance.language")}
              tooltip={tFunc("settings.appearance.language_tooltip")}
            />
            <div className="flex gap-2 flex-wrap">
              {SUPPORTED_LANGUAGES.map((lang) => (
                <Button
                  key={lang.code}
                  variant={settings.language === lang.code ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleLanguageChange(lang.code)}
                  className={`transition-all ${settings.language === lang.code ? "bg-tiktrend-primary hover:bg-tiktrend-primary/90 ring-2 ring-tiktrend-primary/30" : "hover:border-tiktrend-primary/50"}`}
                >
                  {lang.flag} {lang.name}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notificações */}
      <Card className="border-l-4 border-l-blue-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🔔 {tFunc("settings.notifications.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.notifications.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors">
            <div className="flex-1">
              <div className="font-medium flex items-center gap-2">
                {tFunc("settings.notifications.desktop.title")}
                <InfoTooltip content={tFunc("settings.notifications.desktop.tooltip")} />
              </div>
              <div className="text-sm text-muted-foreground">
                {tFunc("settings.notifications.desktop.description")}
              </div>
            </div>
            <Button
              variant={settings.notificationsEnabled ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSettings((prev) => ({ ...prev, notificationsEnabled: !prev.notificationsEnabled }))
              }
              className={settings.notificationsEnabled ? "bg-green-600 hover:bg-green-700" : ""}
            >
              {settings.notificationsEnabled ? <><CheckCircle2 className="h-4 w-4 mr-1" /> Ativado</> : <><XCircle className="h-4 w-4 mr-1" /> Desativado</>}
            </Button>
          </div>

          <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors">
            <div className="flex-1">
              <div className="font-medium flex items-center gap-2">
                {tFunc("settings.notifications.cache_images.title")}
                <InfoTooltip content={tFunc("settings.notifications.cache_images.tooltip")} />
              </div>
              <div className="text-sm text-muted-foreground">
                {tFunc("settings.notifications.cache_images.description")}
              </div>
            </div>
            <Button
              variant={settings.cacheImages ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSettings((prev) => ({ ...prev, cacheImages: !prev.cacheImages }))
              }
              className={settings.cacheImages ? "bg-green-600 hover:bg-green-700" : ""}
            >
              {settings.cacheImages ? <><CheckCircle2 className="h-4 w-4 mr-1" /> Ativado</> : <><XCircle className="h-4 w-4 mr-1" /> Desativado</>}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Busca */}
      <Card className="border-l-4 border-l-purple-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🔍 {tFunc("settings.search.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.search.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <SettingLabel
              label={tFunc("settings.search.products_per_search.label")}
              description={tFunc("settings.search.products_per_search.description")}
              tooltip={tFunc("settings.search.products_per_search.tooltip")}
            />
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
              className="max-w-[120px]"
            />
          </div>
        </CardContent>
      </Card>

      {/* Tutorial */}
      <Card className="border-l-4 border-l-amber-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📚 {tFunc("settings.tutorial.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.tutorial.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              className="border-tiktrend-primary/50 hover:bg-tiktrend-primary/10"
              onClick={() => {
                localStorage.removeItem('tutorial_completed');
                window.dispatchEvent(new Event('restart_tutorial'));
              }}
            >
              🔄 {tFunc("settings.tutorial.restart_tutorial")}
            </Button>
            <Button
              variant="outline"
              className="text-destructive border-destructive/50 hover:bg-destructive/10"
              onClick={async () => {
                if (confirm(tFunc("settings.tutorial.reset_setup_warning"))) {
                  const { resetSetup } = await import('@/services/settings');
                  await resetSetup();
                  window.location.href = '/setup';
                }
              }}
            >
              ⚙️ {tFunc("settings.tutorial.reset_setup")}
            </Button>
          </div>
          <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 rounded-lg">
            <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-amber-700 dark:text-amber-300">
              {tFunc("settings.tutorial.reset_setup_description")}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Copy Settings */}
      <Card className="border-l-4 border-l-green-500/50 lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            ✍️ {tFunc("settings.copy_generation.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.copy_generation.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <SettingLabel
                label={tFunc("settings.copy_generation.default_type")}
                tooltip={tFunc("settings.copy_generation.default_type_tooltip")}
              />
              <div className="flex flex-wrap gap-2">
                {[
                  { value: "tiktok_hook", label: `🎬 ${tFunc("settings.copy_generation.types.tiktok_hook")}` },
                  { value: "product_description", label: `📝 ${tFunc("settings.copy_generation.types.product_description")}` },
                  { value: "carousel", label: `📱 ${tFunc("settings.copy_generation.types.carousel")}` },
                ].map((type) => (
                  <Button
                    key={type.value}
                    variant={settings.defaultCopyType === type.value ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSettings((prev) => ({ ...prev, defaultCopyType: type.value as CopyType }))}
                    className={settings.defaultCopyType === type.value ? "ring-2 ring-tiktrend-primary/30" : ""}
                  >
                    {type.label}
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <SettingLabel
                label={tFunc("settings.copy_generation.default_tone")}
                tooltip={tFunc("settings.copy_generation.default_tone_tooltip")}
              />
              <div className="flex flex-wrap gap-2">
                {[
                  { value: "urgent", label: `🔥 ${tFunc("settings.copy_generation.tones.urgent")}` },
                  { value: "professional", label: `💼 ${tFunc("settings.copy_generation.tones.professional")}` },
                  { value: "fun", label: `🎉 ${tFunc("settings.copy_generation.tones.fun")}` },
                ].map((tone) => (
                  <Button
                    key={tone.value}
                    variant={settings.defaultCopyTone === tone.value ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSettings((prev) => ({ ...prev, defaultCopyTone: tone.value as CopyTone }))}
                    className={settings.defaultCopyTone === tone.value ? "ring-2 ring-tiktrend-primary/30" : ""}
                  >
                    {tone.label}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Seção de Ajuda */}
      <Card className="lg:col-span-2 bg-muted/30">
        <CardContent className="pt-6">
          <HelpSection
            title={tFunc("settings.help.title")}
            items={[
              {
                question: tFunc("settings.help.faq.proxy_q"),
                answer: tFunc("settings.help.faq.proxy_a"),
              },
              {
                question: tFunc("settings.help.faq.openai_q"),
                answer: tFunc("settings.help.faq.openai_a"),
              },
              {
                question: tFunc("settings.help.faq.license_q"),
                answer: tFunc("settings.help.faq.license_a"),
              },
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );

  const renderCredentialsSettings = () => (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* OpenAI API */}
      <Card className="border-l-4 border-l-emerald-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🤖 {tFunc("settings.credentials.openai.title")}
            <Badge variant="outline" className="ml-2 text-xs">{tFunc("settings.credentials.openai.badge")}</Badge>
          </CardTitle>
          <CardDescription>
            {tFunc("settings.credentials.openai.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <SettingLabel label={tFunc("settings.credentials.openai.api_key")} />
            <Input
              type="password"
              placeholder={tFunc("settings.credentials.openai.api_key_placeholder")}
              value={credentials.openaiKey}
              onChange={(e) => setCredentials(prev => ({ ...prev, openaiKey: e.target.value }))}
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              🔒 {tFunc("settings.credentials.openai.api_key_secure")}
            </p>
          </div>

          <div className="space-y-2">
            <SettingLabel
              label={tFunc("settings.credentials.openai.model")}
              tooltip={tFunc("settings.credentials.openai.model_tooltip")}
            />
            <div className="flex gap-2 flex-wrap">
              {["gpt-4o", "gpt-4", "gpt-3.5-turbo"].map((model) => (
                <Button
                  key={model}
                  variant={settings.openaiModel === model ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSettings((prev) => ({ ...prev, openaiModel: model }))}
                  className={`font-mono text-xs ${settings.openaiModel === model ? "ring-2 ring-tiktrend-primary/30" : ""}`}
                >
                  {model}
                </Button>
              ))}
            </div>
          </div>

          <div className="pt-3 border-t">
            <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-lg">
              <HelpCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <span className="text-xs text-blue-700 dark:text-blue-300">{tFunc("settings.credentials.openai.info")}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Proxies */}
      <Card className="border-l-4 border-l-orange-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🌐 {tFunc("settings.credentials.proxy.title")}
            <Badge variant="outline" className="ml-2 text-xs">{tFunc("settings.credentials.proxy.badge")}</Badge>
          </CardTitle>
          <CardDescription>
            {tFunc("settings.credentials.proxy.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
            <div className="flex-1">
              <div className="font-medium flex items-center gap-2">
                {tFunc("settings.credentials.proxy.enable")}
                <InfoTooltip content={tFunc("settings.credentials.proxy.enable_tooltip")} />
              </div>
              <div className="text-sm text-muted-foreground">
                {tFunc("settings.credentials.proxy.enable_description")}
              </div>
            </div>
            <Button
              variant={settings.proxyEnabled ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSettings((prev) => ({ ...prev, proxyEnabled: !prev.proxyEnabled }))
              }
              className={settings.proxyEnabled ? "bg-green-600 hover:bg-green-700" : ""}
            >
              {settings.proxyEnabled ? <><CheckCircle2 className="h-4 w-4 mr-1" /> Ativado</> : "Desativado"}
            </Button>
          </div>

          {settings.proxyEnabled && (
            <div className="space-y-2 animate-in fade-in slide-in-from-top-2">
              <label className="text-sm font-medium">{tFunc("settings.credentials.proxy.list")}</label>
              <textarea
                className="w-full h-32 rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                placeholder={tFunc("settings.credentials.proxy.list_placeholder")}
                value={credentials.proxies.join("\n")}
                onChange={(e) => setCredentials(prev => ({
                  ...prev,
                  proxies: e.target.value.split("\n").filter(p => p.trim())
                }))}
              />
              <p className="text-xs text-muted-foreground">
                {tFunc("settings.credentials.proxy.count", { count: credentials.proxies.length })}
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
      <Card className="border-l-4 border-l-cyan-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            ⚙️ {tFunc("settings.scraper.collection.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.scraper.collection.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <SettingLabel
              label={tFunc("settings.scraper.collection.max_products.label")}
              tooltip={tFunc("settings.scraper.collection.max_products.tooltip")}
            />
            <Input
              type="number"
              value={scraperConfig.maxProducts}
              onChange={(e) => setScraperConfig(prev => ({
                ...prev,
                maxProducts: parseInt(e.target.value) || 50
              }))}
              min={10}
              max={200}
              className="max-w-[120px]"
            />
          </div>

          <div className="space-y-2">
            <SettingLabel
              label={tFunc("settings.scraper.collection.interval.label")}
              description={tFunc("settings.scraper.collection.interval.description")}
              tooltip={tFunc("settings.scraper.collection.interval.tooltip")}
            />
            <Input
              type="number"
              value={scraperConfig.intervalMinutes}
              onChange={(e) => setScraperConfig(prev => ({
                ...prev,
                intervalMinutes: parseInt(e.target.value) || 60
              }))}
              min={15}
              max={1440}
              className="max-w-[120px]"
            />
          </div>

          <div className="space-y-2">
            <SettingLabel
              label={tFunc("settings.scraper.collection.timeout.label")}
              tooltip={tFunc("settings.scraper.collection.timeout.tooltip")}
            />
            <Input
              type="number"
              value={scraperConfig.timeout / 1000}
              onChange={(e) => setScraperConfig(prev => ({
                ...prev,
                timeout: (parseInt(e.target.value) || 30) * 1000
              }))}
              min={10}
              max={120}
              className="max-w-[120px]"
            />
          </div>
        </CardContent>
      </Card>

      {/* Modo */}
      <Card className="border-l-4 border-l-indigo-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🖥️ {tFunc("settings.scraper.execution.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.scraper.execution.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
            <div className="flex-1">
              <div className="font-medium flex items-center gap-2">
                {tFunc("settings.scraper.execution.headless.title")}
                <InfoTooltip content={tFunc("settings.scraper.execution.headless.tooltip")} />
              </div>
              <div className="text-sm text-muted-foreground">
                {tFunc("settings.scraper.execution.headless.description")}
              </div>
            </div>
            <Button
              variant={scraperConfig.headless ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setScraperConfig((prev) => ({ ...prev, headless: !prev.headless }))
              }
              className={scraperConfig.headless ? "bg-green-600 hover:bg-green-700" : ""}
            >
              {scraperConfig.headless ? <><CheckCircle2 className="h-4 w-4 mr-1" /> Ativado</> : "Desativado"}
            </Button>
          </div>

          <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
            <div className="flex-1">
              <div className="font-medium flex items-center gap-2">
                {tFunc("settings.scraper.execution.use_proxy.title")}
                <InfoTooltip content={tFunc("settings.scraper.execution.use_proxy.tooltip")} />
              </div>
              <div className="text-sm text-muted-foreground">
                {tFunc("settings.scraper.execution.use_proxy.description")}
              </div>
            </div>
            <Button
              variant={scraperConfig.useProxy ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setScraperConfig((prev) => ({ ...prev, useProxy: !prev.useProxy }))
              }
              className={scraperConfig.useProxy ? "bg-green-600 hover:bg-green-700" : ""}
            >
              {scraperConfig.useProxy ? <><CheckCircle2 className="h-4 w-4 mr-1" /> Ativado</> : "Desativado"}
            </Button>
          </div>

          <div className="pt-4 border-t">
            <Button variant="outline" className="w-full border-tiktrend-primary/50 hover:bg-tiktrend-primary/10">
              🧪 {tFunc("settings.scraper.execution.test")}
            </Button>
            <p className="text-xs text-muted-foreground mt-2 text-center">
              {tFunc("settings.scraper.execution.test_description")}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Categorias */}
      <Card className="lg:col-span-2 border-l-4 border-l-pink-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📂 {tFunc("settings.scraper.categories.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.scraper.categories.description")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {[
              { key: "electronics", icon: "📱" },
              { key: "fashion", icon: "👗" },
              { key: "beauty", icon: "💄" },
              { key: "home", icon: "🏠" },
              { key: "sports", icon: "⚽" },
              { key: "toys", icon: "🧸" },
              { key: "health", icon: "💊" },
              { key: "automotive", icon: "🚗" },
              { key: "food", icon: "🍔" },
              { key: "pets", icon: "🐕" },
            ].map((category) => {
              const isSelected = scraperConfig.categories.includes(category.key);
              return (
                <Button
                  key={category.key}
                  variant={isSelected ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    setScraperConfig(prev => ({
                      ...prev,
                      categories: isSelected
                        ? prev.categories.filter(c => c !== category.key)
                        : [...prev.categories, category.key]
                    }));
                  }}
                  className={`transition-all ${isSelected ? "ring-2 ring-tiktrend-primary/30" : "hover:border-tiktrend-primary/50"}`}
                >
                  {category.icon} {tFunc(`settings.scraper.categories.${category.key}`)}
                </Button>
              );
            })}
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            {tFunc("settings.scraper.categories.count", { count: scraperConfig.categories.length })}
          </p>
        </CardContent>
      </Card>

      {/* FAQ do Scraper */}
      <Card className="lg:col-span-2 bg-muted/30">
        <CardContent className="pt-6">
          <HelpSection
            title={tFunc("settings.help.title")}
            items={[
              {
                question: tFunc("settings.help.faq.scraper_q"),
                answer: tFunc("settings.help.faq.scraper_a"),
              },
              {
                question: tFunc("settings.help.faq.proxy_q"),
                answer: tFunc("settings.help.faq.proxy_a"),
              },
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );

  const renderLicenseSettings = () => {
    // Novo modelo: Licença vitalícia + pacotes de créditos
    const hasLicense = licenseConfig.isActive && licenseConfig.plan === "lifetime";

    const creditPacks = [
      {
        name: tFunc("settings.license.credits.packs.starter.name"),
        credits: 50,
        price: tFunc("settings.license.credits.packs.starter.price"),
        perCredit: tFunc("settings.license.credits.packs.starter.per_credit"),
      },
      {
        name: tFunc("settings.license.credits.packs.pro.name"),
        credits: 200,
        price: tFunc("settings.license.credits.packs.pro.price"),
        perCredit: tFunc("settings.license.credits.packs.pro.per_credit"),
        recommended: true,
        badge: tFunc("settings.license.credits.packs.pro.badge"),
      },
      {
        name: tFunc("settings.license.credits.packs.ultra.name"),
        credits: 500,
        price: tFunc("settings.license.credits.packs.ultra.price"),
        perCredit: tFunc("settings.license.credits.packs.ultra.per_credit"),
      },
    ];

    return (
      <div className="space-y-6">
        {/* Licença Vitalícia */}
        <Card className={`border-2 ${hasLicense ? "border-green-500/50 bg-green-50/30 dark:bg-green-950/20" : "border-tiktrend-primary/50"}`}>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                🎫 {tFunc("settings.license.lifetime.title")}
              </span>
              {hasLicense ? (
                <Badge variant="tiktrend" className="text-sm px-3 py-1">
                  <CheckCircle2 className="h-4 w-4 mr-1" /> {tFunc("settings.license.lifetime.active")}
                </Badge>
              ) : (
                <Badge variant="secondary" className="text-sm px-3 py-1">
                  {tFunc("settings.license.lifetime.price")}
                </Badge>
              )}
            </CardTitle>
            <CardDescription>
              {tFunc("settings.license.lifetime.description")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {hasLicense ? (
              <div className="text-sm p-4 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-900">
                <div className="space-y-2">
                  <p className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-600" /> {tFunc("settings.license.lifetime.features.unlimited_access")}</p>
                  <p className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-600" /> {tFunc("settings.license.lifetime.features.unlimited_searches")}</p>
                  <p className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-600" /> {tFunc("settings.license.lifetime.features.unlimited_favorites")}</p>
                  <p className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-600" /> {tFunc("settings.license.lifetime.features.export")}</p>
                </div>
                <p className="mt-3 text-xs text-muted-foreground">{tFunc("settings.license.lifetime.features.credits_separate")}</p>
              </div>
            ) : (
              <>
                <ul className="space-y-3 text-sm">
                  <li className="flex items-center gap-3 p-2 bg-muted/30 rounded-lg">
                    <span className="text-green-500 text-lg">✓</span>
                    <span>{tFunc("settings.license.lifetime.benefits.unlimited")}</span>
                  </li>
                  <li className="flex items-center gap-3 p-2 bg-muted/30 rounded-lg">
                    <span className="text-green-500 text-lg">✓</span>
                    <span>{tFunc("settings.license.lifetime.benefits.searches")}</span>
                  </li>
                  <li className="flex items-center gap-3 p-2 bg-muted/30 rounded-lg">
                    <span className="text-green-500 text-lg">✓</span>
                    <span>{tFunc("settings.license.lifetime.benefits.export")}</span>
                  </li>
                  <li className="flex items-center gap-3 p-2 bg-muted/30 rounded-lg">
                    <span className="text-green-500 text-lg">✓</span>
                    <span>{tFunc("settings.license.lifetime.benefits.updates")}</span>
                  </li>
                </ul>
                <Button variant="tiktrend" className="w-full text-lg py-6">
                  🎫 {tFunc("settings.license.lifetime.buy")} - {tFunc("settings.license.lifetime.price")}
                </Button>
              </>
            )}

            <div className="pt-4 border-t space-y-3">
              <SettingLabel label={tFunc("settings.license.lifetime.activate")} />
              <div className="flex gap-2">
                <Input
                  placeholder={tFunc("settings.license.lifetime.activate_placeholder")}
                  value={licenseConfig.key || ""}
                  onChange={(e) => setLicenseConfig(prev => ({ ...prev, key: e.target.value }))}
                  className="font-mono"
                />
                <Button
                  variant="tiktrend"
                  onClick={handleActivateLicense}
                  disabled={!licenseConfig.key}
                >
                  {tFunc("settings.license.lifetime.activate_button")}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Pacotes de Créditos IA */}
        <Card className="border-l-4 border-l-purple-500/50" data-testid="settings-credits-section">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              🤖 {tFunc("settings.license.credits.title")}
            </CardTitle>
            <CardDescription>
              {tFunc("settings.license.credits.description")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950/30 dark:to-pink-950/30 rounded-lg border border-purple-200 dark:border-purple-900" data-testid="settings-credits-balance">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">{tFunc("settings.license.credits.your_credits")}:</span>
                <span className="text-3xl font-bold text-tiktrend-primary" data-testid="settings-credits-value">{licenseConfig.credits}</span>
              </div>
              <div className="text-xs text-muted-foreground mt-2 space-y-1">
                <p>• {tFunc("settings.license.credits.usage.simple")}</p>
                <p>• {tFunc("settings.license.credits.usage.analysis")}</p>
                <p>• {tFunc("settings.license.credits.usage.batch")}</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3" data-testid="settings-credit-packs">
              {creditPacks.map((pack, index) => (
                <Card
                  key={pack.name}
                  data-testid={`settings-credit-pack-${index}`}
                  className={`relative overflow-hidden transition-all hover:shadow-lg ${pack.recommended ? "ring-2 ring-tiktrend-primary ring-offset-2" : ""}`}
                >
                  {pack.recommended && pack.badge && (
                    <Badge className="absolute -top-1 left-1/2 -translate-x-1/2 bg-tiktrend-primary text-xs px-3" data-testid="recommended-badge">
                      ⭐ {pack.badge}
                    </Badge>
                  )}
                  <CardHeader className="pb-2 pt-6">
                    <CardTitle className="text-lg text-center" data-testid="pack-name">{pack.name}</CardTitle>
                    <div className="flex items-baseline justify-center">
                      <span className="text-3xl font-bold" data-testid="pack-credits">{pack.credits}</span>
                      <span className="text-muted-foreground text-sm ml-1">créditos</span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center mb-4">
                      <span className="text-2xl font-bold" data-testid="pack-price">{pack.price}</span>
                      <p className="text-xs text-muted-foreground">{pack.perCredit}{tFunc("settings.license.credits.per_credit")}</p>
                    </div>
                    <Button className="w-full" variant={pack.recommended ? "tiktrend" : "outline"} data-testid="buy-pack-button">
                      {tFunc("settings.license.credits.buy")}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="text-center text-sm text-muted-foreground p-4 bg-muted/30 rounded-lg">
          <p className="font-medium">{tFunc("settings.license.payment_info")}</p>
          <p className="mt-1">{tFunc("settings.license.support")}</p>
        </div>
      </div>
    );
  };

  const renderSystemSettings = () => (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Atualizações */}
      <Card className="border-l-4 border-l-blue-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🔄 {tFunc("settings.system.updates.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.system.updates.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
            <div className="flex-1">
              <div className="font-medium flex items-center gap-2">
                {tFunc("settings.system.updates.auto_update.title")}
                <InfoTooltip content={tFunc("settings.system.updates.auto_update.tooltip")} />
              </div>
              <div className="text-sm text-muted-foreground">
                {tFunc("settings.system.updates.auto_update.description")}
              </div>
            </div>
            <Button
              variant={systemConfig.autoUpdate ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSystemConfig((prev) => ({ ...prev, autoUpdate: !prev.autoUpdate }))
              }
              className={systemConfig.autoUpdate ? "bg-green-600 hover:bg-green-700" : ""}
            >
              {systemConfig.autoUpdate ? <><CheckCircle2 className="h-4 w-4 mr-1" /> Ativado</> : "Desativado"}
            </Button>
          </div>

          <div className="space-y-2">
            <SettingLabel
              label={tFunc("settings.system.updates.check_interval.label")}
              tooltip={tFunc("settings.system.updates.check_interval.tooltip")}
            />
            <Input
              type="number"
              value={systemConfig.checkInterval}
              onChange={(e) => setSystemConfig(prev => ({
                ...prev,
                checkInterval: parseInt(e.target.value) || 24
              }))}
              min={1}
              max={168}
              className="max-w-[120px]"
            />
          </div>

          <div className="pt-4 border-t">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{tFunc("settings.system.updates.current_version")}:</span>
              <Badge variant="outline" className="font-mono">v1.0.0</Badge>
            </div>
            <Button variant="outline" className="w-full mt-3 border-tiktrend-primary/50 hover:bg-tiktrend-primary/10">
              🔍 {tFunc("settings.system.updates.check_now")}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs */}
      <Card className="border-l-4 border-l-gray-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📋 {tFunc("settings.system.logs.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.system.logs.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
            <div className="flex-1">
              <div className="font-medium flex items-center gap-2">
                {tFunc("settings.system.logs.enable.title")}
                <InfoTooltip content={tFunc("settings.system.logs.enable.tooltip")} />
              </div>
              <div className="text-sm text-muted-foreground">
                {tFunc("settings.system.logs.enable.description")}
              </div>
            </div>
            <Button
              variant={systemConfig.logsEnabled ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSystemConfig((prev) => ({ ...prev, logsEnabled: !prev.logsEnabled }))
              }
              className={systemConfig.logsEnabled ? "bg-green-600 hover:bg-green-700" : ""}
            >
              {systemConfig.logsEnabled ? <><CheckCircle2 className="h-4 w-4 mr-1" /> Ativado</> : "Desativado"}
            </Button>
          </div>

          <div className="space-y-2">
            <SettingLabel
              label={tFunc("settings.system.logs.max_size.label")}
              tooltip={tFunc("settings.system.logs.max_size.tooltip")}
            />
            <Input
              type="number"
              value={systemConfig.maxLogSize}
              onChange={(e) => setSystemConfig(prev => ({
                ...prev,
                maxLogSize: parseInt(e.target.value) || 10
              }))}
              min={1}
              max={100}
              className="max-w-[120px]"
            />
          </div>

          <div className="flex gap-2 pt-2">
            <Button variant="outline" className="flex-1 hover:bg-muted">
              📂 {tFunc("settings.system.logs.open_folder")}
            </Button>
            <Button variant="outline" className="flex-1 hover:bg-muted">
              🗑️ {tFunc("settings.system.logs.clear")}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Analytics */}
      <Card className="border-l-4 border-l-purple-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📊 {tFunc("settings.system.analytics.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.system.analytics.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
            <div className="flex-1">
              <div className="font-medium">{tFunc("settings.system.analytics.enable.title")}</div>
              <div className="text-sm text-muted-foreground">
                {tFunc("settings.system.analytics.enable.description")}
              </div>
            </div>
            <Button
              variant={systemConfig.analyticsEnabled ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setSystemConfig((prev) => ({ ...prev, analyticsEnabled: !prev.analyticsEnabled }))
              }
              className={systemConfig.analyticsEnabled ? "bg-green-600 hover:bg-green-700" : ""}
            >
              {systemConfig.analyticsEnabled ? <><CheckCircle2 className="h-4 w-4 mr-1" /> Ativado</> : "Desativado"}
            </Button>
          </div>

          <div className="text-xs text-muted-foreground bg-muted/50 p-4 rounded-lg border">
            <p className="font-medium mb-2 flex items-center gap-2">
              <HelpCircle className="h-4 w-4" />
              {tFunc("settings.system.analytics.collected_data")}
            </p>
            <ul className="space-y-1 ml-6">
              <li>• {tFunc("settings.system.analytics.data_items.version")}</li>
              <li>• {tFunc("settings.system.analytics.data_items.features")}</li>
              <li>• {tFunc("settings.system.analytics.data_items.errors")}</li>
            </ul>
            <p className="mt-3 text-green-600 dark:text-green-400 font-medium">
              🔒 {tFunc("settings.system.analytics.privacy_note")}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Data */}
      <Card className="border-l-4 border-l-red-500/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            💾 {tFunc("settings.system.data.title")}
          </CardTitle>
          <CardDescription>
            {tFunc("settings.system.data.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="p-4 bg-muted/50 rounded-lg border">
              <div className="text-muted-foreground text-xs">{tFunc("settings.system.data.database")}</div>
              <div className="font-bold text-lg mt-1">12.4 MB</div>
            </div>
            <div className="p-4 bg-muted/50 rounded-lg border">
              <div className="text-muted-foreground text-xs">{tFunc("settings.system.data.image_cache")}</div>
              <div className="font-bold text-lg mt-1">45.2 MB</div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" className="flex-1 hover:bg-muted">
              📤 {tFunc("settings.system.data.export")}
            </Button>
            <Button variant="outline" className="flex-1 hover:bg-muted">
              📥 {tFunc("settings.system.data.import")}
            </Button>
          </div>

          <div className="pt-4 border-t">
            <Button variant="destructive" className="w-full">
              🗑️ {tFunc("settings.system.data.clear_all")}
            </Button>
            <div className="flex items-start gap-2 mt-2 p-2 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded">
              <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-red-700 dark:text-red-300">
                {tFunc("settings.system.data.clear_warning")}
              </p>
            </div>
          </div>
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
          {tFunc("settings.title")}
        </h1>
        <p className="text-muted-foreground">
          {tFunc("settings.subtitle")}
        </p>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b pb-4 overflow-x-auto">
        <TabButton
          tab="general"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<SettingsIcon size={18} />}
          label={tFunc("settings.general")}
        />
        <TabButton
          tab="credentials"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<CopyIcon size={18} />}
          label={tFunc("settings.credentials.title")}
        />
        <TabButton
          tab="scraper"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<SearchIcon size={18} />}
          label={tFunc("settings.scraper.title")}
        />
        <TabButton
          tab="license"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<StarIcon size={18} />}
          label={tFunc("settings.license.title")}
        />
        <TabButton
          tab="system"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<ChartIcon size={18} />}
          label={tFunc("settings.system.title")}
        />
        <TabButton
          tab="integrations"
          currentTab={activeTab}
          onClick={setActiveTab}
          icon={<span className="text-lg">🔗</span>}
          label={tFunc("settings.integrations.title")}
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

export default Settings;
