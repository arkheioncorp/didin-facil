import * as React from "react";
import { useTranslation } from "react-i18next";
import { Settings, Save, RotateCcw, Sparkles } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
  getUserPreferences,
  updateUserPreferences,
  getCopyStats,
  type CopyPreferences,
  type CopyStats,
} from "@/services/copy";
import { COPY_TYPES, COPY_TONES } from "@/lib/constants";

interface CopyPreferencesDialogProps {
  trigger?: React.ReactNode;
  onPreferencesUpdate?: (prefs: CopyPreferences) => void;
}

export function CopyPreferencesDialog({
  trigger,
  onPreferencesUpdate,
}: CopyPreferencesDialogProps) {
  const { t } = useTranslation();
  const { toast } = useToast();
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [preferences, setPreferences] = React.useState<CopyPreferences | null>(null);
  const [stats, setStats] = React.useState<CopyStats | null>(null);

  // Carregar preferências quando o dialog abre
  React.useEffect(() => {
    if (open) {
      loadData();
    }
  }, [open]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [prefs, statsData] = await Promise.all([
        getUserPreferences(),
        getCopyStats(),
      ]);
      setPreferences(prefs);
      setStats(statsData);
    } catch (error) {
      console.error("Error loading preferences:", error);
      toast({
        title: "Erro ao carregar preferências",
        description: "Não foi possível carregar suas preferências. Usando padrões.",
        variant: "destructive",
      });
      // Set defaults
      setPreferences({
        defaultCopyType: "tiktok_hook",
        defaultTone: "urgent",
        defaultPlatform: "instagram",
        defaultLanguage: "pt-BR",
        includeEmoji: true,
        includeHashtags: true,
        totalCopiesGenerated: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!preferences) return;
    
    setSaving(true);
    try {
      const updated = await updateUserPreferences(preferences);
      setPreferences(updated);
      onPreferencesUpdate?.(updated);
      toast({
        title: "✅ Preferências salvas!",
        description: "Suas configurações foram atualizadas com sucesso.",
      });
      setOpen(false);
    } catch (error) {
      console.error("Error saving preferences:", error);
      toast({
        title: "Erro ao salvar",
        description: "Não foi possível salvar suas preferências.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setPreferences({
      defaultCopyType: "tiktok_hook",
      defaultTone: "urgent",
      defaultPlatform: "instagram",
      defaultLanguage: "pt-BR",
      includeEmoji: true,
      includeHashtags: true,
      totalCopiesGenerated: preferences?.totalCopiesGenerated ?? 0,
      mostUsedCopyType: preferences?.mostUsedCopyType,
      mostUsedTone: preferences?.mostUsedTone,
    });
    toast({
      title: "Preferências resetadas",
      description: "Clique em Salvar para confirmar as alterações.",
    });
  };

  const updatePref = <K extends keyof CopyPreferences>(
    key: K,
    value: CopyPreferences[K]
  ) => {
    if (!preferences) return;
    setPreferences({ ...preferences, [key]: value });
  };

  const platforms = [
    { value: "instagram", label: "Instagram" },
    { value: "tiktok", label: "TikTok" },
    { value: "facebook", label: "Facebook" },
    { value: "whatsapp", label: "WhatsApp" },
    { value: "youtube", label: "YouTube" },
    { value: "email", label: "Email" },
    { value: "general", label: "Geral" },
  ];

  const languages = [
    { value: "pt-BR", label: "Português (Brasil)" },
    { value: "en-US", label: "English (US)" },
    { value: "es-ES", label: "Español" },
  ];

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm" className="gap-2">
            <Settings className="h-4 w-4" />
            Preferências
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            Preferências de Copy AI
          </DialogTitle>
          <DialogDescription>
            Configure suas preferências padrão para geração de copies.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : preferences ? (
          <div className="space-y-6 py-4">
            {/* Stats Card */}
            {stats && (
              <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">
                    Suas Estatísticas
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{stats.totalCopies}</div>
                    <div className="text-xs text-muted-foreground">
                      Copies Geradas
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{stats.totalCreditsUsed}</div>
                    <div className="text-xs text-muted-foreground">
                      Créditos Usados
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{stats.cacheHitRate}%</div>
                    <div className="text-xs text-muted-foreground">
                      Taxa de Cache
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{stats.copyTypesUsed}</div>
                    <div className="text-xs text-muted-foreground">
                      Tipos Usados
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Default Settings */}
            <div className="space-y-4">
              <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
                Padrões de Geração
              </h4>

              <div className="grid gap-4 md:grid-cols-2">
                {/* Copy Type */}
                <div className="space-y-2">
                  <Label>Tipo de Copy Padrão</Label>
                  <Select
                    value={preferences.defaultCopyType}
                    onValueChange={(v) => updatePref("defaultCopyType", v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione..." />
                    </SelectTrigger>
                    <SelectContent>
                      {COPY_TYPES.map((type) => (
                        <SelectItem key={type.id} value={type.id}>
                          {type.icon} {type.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {preferences.mostUsedCopyType && (
                    <p className="text-xs text-muted-foreground">
                      Mais usado: <Badge variant="secondary" className="ml-1">{preferences.mostUsedCopyType}</Badge>
                    </p>
                  )}
                </div>

                {/* Tone */}
                <div className="space-y-2">
                  <Label>Tom Padrão</Label>
                  <Select
                    value={preferences.defaultTone}
                    onValueChange={(v) => updatePref("defaultTone", v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione..." />
                    </SelectTrigger>
                    <SelectContent>
                      {COPY_TONES.map((tone) => (
                        <SelectItem key={tone.id} value={tone.id}>
                          {tone.icon} {tone.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {preferences.mostUsedTone && (
                    <p className="text-xs text-muted-foreground">
                      Mais usado: <Badge variant="secondary" className="ml-1">{preferences.mostUsedTone}</Badge>
                    </p>
                  )}
                </div>

                {/* Platform */}
                <div className="space-y-2">
                  <Label>Plataforma Padrão</Label>
                  <Select
                    value={preferences.defaultPlatform}
                    onValueChange={(v) => updatePref("defaultPlatform", v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione..." />
                    </SelectTrigger>
                    <SelectContent>
                      {platforms.map((p) => (
                        <SelectItem key={p.value} value={p.value}>
                          {p.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Language */}
                <div className="space-y-2">
                  <Label>Idioma Padrão</Label>
                  <Select
                    value={preferences.defaultLanguage}
                    onValueChange={(v) => updatePref("defaultLanguage", v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione..." />
                    </SelectTrigger>
                    <SelectContent>
                      {languages.map((lang) => (
                        <SelectItem key={lang.value} value={lang.value}>
                          {lang.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Toggles */}
            <div className="space-y-4">
              <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
                Opções de Formatação
              </h4>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Incluir Emojis</Label>
                    <p className="text-xs text-muted-foreground">
                      Adicionar emojis automaticamente nas copies
                    </p>
                  </div>
                  <Switch
                    checked={preferences.includeEmoji}
                    onCheckedChange={(v) => updatePref("includeEmoji", v)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Incluir Hashtags</Label>
                    <p className="text-xs text-muted-foreground">
                      Sugerir hashtags relevantes nas copies
                    </p>
                  </div>
                  <Switch
                    checked={preferences.includeHashtags}
                    onCheckedChange={(v) => updatePref("includeHashtags", v)}
                  />
                </div>
              </div>
            </div>
          </div>
        ) : null}

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={loading || saving}
            className="gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            Resetar
          </Button>
          <Button
            onClick={handleSave}
            disabled={loading || saving}
            className="gap-2"
          >
            <Save className="h-4 w-4" />
            {saving ? "Salvando..." : "Salvar Preferências"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default CopyPreferencesDialog;
