<template>
  <div class="automation-dashboard p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard de Automações
        </h1>
        <p class="text-gray-500 dark:text-gray-400">
          Monitoramento em tempo real do sistema n8n
        </p>
      </div>
      <div class="flex items-center gap-4">
        <Select v-model="timeRange" class="w-32">
          <SelectTrigger>
            <SelectValue placeholder="Período" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1h">1 hora</SelectItem>
            <SelectItem value="24h">24 horas</SelectItem>
            <SelectItem value="7d">7 dias</SelectItem>
            <SelectItem value="30d">30 dias</SelectItem>
          </SelectContent>
        </Select>
        <Button @click="refreshData" :disabled="loading">
          <RefreshCw
            :class="{ 'animate-spin': loading }"
            class="w-4 h-4 mr-2"
          />
          Atualizar
        </Button>
      </div>
    </div>

    <!-- Health Status -->
    <Card v-if="health" :class="healthClass">
      <CardContent class="flex items-center gap-4 p-4">
        <div :class="healthIconClass" class="p-2 rounded-full">
          <CheckCircle2 v-if="health.status === 'healthy'" class="w-6 h-6" />
          <AlertTriangle
            v-else-if="health.status === 'degraded'"
            class="w-6 h-6"
          />
          <XCircle v-else class="w-6 h-6" />
        </div>
        <div>
          <p class="font-semibold">Sistema {{ healthLabel }}</p>
          <p class="text-sm opacity-75">
            Última verificação: {{ formatDate(health.timestamp) }}
          </p>
        </div>
      </CardContent>
    </Card>

    <!-- Overview Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <CardTitle class="text-sm font-medium">Automações Ativas</CardTitle>
          <Zap class="w-4 h-4 text-yellow-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">
            {{ overview?.active_automations || 0 }}
          </div>
          <p class="text-xs text-muted-foreground">
            de {{ overview?.total_automations || 0 }} configuradas
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <CardTitle class="text-sm font-medium">Eventos Pendentes</CardTitle>
          <Clock class="w-4 h-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">
            {{ overview?.pending_events || 0 }}
          </div>
          <p class="text-xs text-muted-foreground">
            {{ overview?.processing_events || 0 }} em processamento
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <CardTitle class="text-sm font-medium">Completados Hoje</CardTitle>
          <CheckCircle class="w-4 h-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">
            {{ overview?.completed_today || 0 }}
          </div>
          <p class="text-xs text-muted-foreground">
            {{ overview?.failed_today || 0 }} falharam
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <CardTitle class="text-sm font-medium">Taxa de Sucesso</CardTitle>
          <TrendingUp class="w-4 h-4 text-purple-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">
            {{ overview?.success_rate?.toFixed(1) || 0 }}%
          </div>
          <p class="text-xs text-muted-foreground">
            Tempo médio: {{ formatMs(overview?.avg_processing_time_ms) }}
          </p>
        </CardContent>
      </Card>
    </div>

    <!-- Queue Depth Chart -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Profundidade da Fila</CardTitle>
          <CardDescription> Eventos por prioridade </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="space-y-4">
            <div class="flex items-center">
              <div class="w-20 text-sm font-medium">Alta</div>
              <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div
                  class="bg-red-500 h-4 rounded-full transition-all"
                  :style="{ width: queueWidthHigh }"
                ></div>
              </div>
              <div class="w-12 text-right text-sm">
                {{ queueDepth?.high || 0 }}
              </div>
            </div>
            <div class="flex items-center">
              <div class="w-20 text-sm font-medium">Normal</div>
              <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div
                  class="bg-blue-500 h-4 rounded-full transition-all"
                  :style="{ width: queueWidthNormal }"
                ></div>
              </div>
              <div class="w-12 text-right text-sm">
                {{ queueDepth?.normal || 0 }}
              </div>
            </div>
            <div class="flex items-center">
              <div class="w-20 text-sm font-medium">Baixa</div>
              <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div
                  class="bg-gray-400 h-4 rounded-full transition-all"
                  :style="{ width: queueWidthLow }"
                ></div>
              </div>
              <div class="w-12 text-right text-sm">
                {{ queueDepth?.low || 0 }}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Automações por Tipo</CardTitle>
          <CardDescription> Status de cada automação </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="space-y-2 max-h-64 overflow-y-auto">
            <div
              v-for="auto in automations"
              :key="auto.type"
              class="flex items-center justify-between p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <div class="flex items-center gap-2">
                <div
                  :class="auto.enabled ? 'bg-green-500' : 'bg-gray-400'"
                  class="w-2 h-2 rounded-full"
                ></div>
                <span class="text-sm">{{ auto.name }}</span>
              </div>
              <div class="flex items-center gap-2">
                <Badge :variant="auto.enabled ? 'default' : 'secondary'">
                  {{ auto.enabled ? "Ativo" : "Inativo" }}
                </Badge>
                <Button
                  size="sm"
                  variant="ghost"
                  @click="toggleAutomation(auto.type, !auto.enabled)"
                >
                  <Settings class="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Events Table -->
    <Card>
      <CardHeader>
        <div class="flex items-center justify-between">
          <div>
            <CardTitle>Eventos na Fila</CardTitle>
            <CardDescription>
              Eventos agendados para processamento
            </CardDescription>
          </div>
          <div class="flex gap-2">
            <Input
              v-model="eventFilter"
              placeholder="Filtrar eventos..."
              class="w-64"
            />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Usuário</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Agendado Para</TableHead>
              <TableHead>Prioridade</TableHead>
              <TableHead>Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="event in filteredEvents" :key="event.id">
              <TableCell class="font-mono text-xs">
                {{ event.id.slice(0, 8) }}...
              </TableCell>
              <TableCell>
                <Badge variant="outline">{{ event.automation_type }}</Badge>
              </TableCell>
              <TableCell>{{ event.user_id }}</TableCell>
              <TableCell>
                <Badge :variant="getStatusVariant(event.status)">
                  {{ event.status }}
                </Badge>
              </TableCell>
              <TableCell>{{ formatDate(event.scheduled_for) }}</TableCell>
              <TableCell>
                <Badge :variant="getPriorityVariant(event.priority)">
                  {{ event.priority }}
                </Badge>
              </TableCell>
              <TableCell>
                <div class="flex gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    @click="processNow(event.id)"
                    title="Processar agora"
                  >
                    <Play class="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    @click="cancelEvent(event.id)"
                    title="Cancelar"
                  >
                    <X class="w-4 h-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
            <TableRow v-if="!filteredEvents.length">
              <TableCell
                colspan="7"
                class="text-center text-muted-foreground py-8"
              >
                Nenhum evento na fila
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import {
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Zap,
  Clock,
  CheckCircle,
  TrendingUp,
  Settings,
  Play,
  X,
} from "lucide-vue-next";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";

const { toast } = useToast();

// State
const loading = ref(false);
const timeRange = ref("24h");
const eventFilter = ref("");
const health = ref<any>(null);
const overview = ref<any>(null);
const queueDepth = ref<any>(null);
const automations = ref<any[]>([]);
const events = ref<any[]>([]);

let refreshInterval: ReturnType<typeof setInterval> | null = null;

// Computed
const healthClass = computed(() => {
  if (!health.value) return "";
  switch (health.value.status) {
    case "healthy":
      return "border-green-500 bg-green-50 dark:bg-green-950";
    case "degraded":
      return "border-yellow-500 bg-yellow-50 dark:bg-yellow-950";
    default:
      return "border-red-500 bg-red-50 dark:bg-red-950";
  }
});

const healthIconClass = computed(() => {
  if (!health.value) return "";
  switch (health.value.status) {
    case "healthy":
      return "bg-green-500 text-white";
    case "degraded":
      return "bg-yellow-500 text-white";
    default:
      return "bg-red-500 text-white";
  }
});

const healthLabel = computed(() => {
  if (!health.value) return "";
  switch (health.value.status) {
    case "healthy":
      return "Operacional";
    case "degraded":
      return "Degradado";
    default:
      return "Indisponível";
  }
});

const queueTotal = computed(() => {
  if (!queueDepth.value) return 1;
  return queueDepth.value.total || 1;
});

const queueWidthHigh = computed(
  () => `${((queueDepth.value?.high || 0) / queueTotal.value) * 100}%`,
);

const queueWidthNormal = computed(
  () => `${((queueDepth.value?.normal || 0) / queueTotal.value) * 100}%`,
);

const queueWidthLow = computed(
  () => `${((queueDepth.value?.low || 0) / queueTotal.value) * 100}%`,
);

const filteredEvents = computed(() => {
  if (!eventFilter.value) return events.value;
  const filter = eventFilter.value.toLowerCase();
  return events.value.filter(
    (e) =>
      e.automation_type.toLowerCase().includes(filter) ||
      e.user_id.toLowerCase().includes(filter) ||
      e.status.toLowerCase().includes(filter),
  );
});

// Methods
async function fetchHealth() {
  try {
    const { data } = await api.get("/automation/dashboard/health");
    health.value = data;
  } catch (error) {
    console.error("Error fetching health:", error);
  }
}

async function fetchOverview() {
  try {
    const { data } = await api.get("/automation/dashboard/overview");
    overview.value = data;
  } catch (error) {
    console.error("Error fetching overview:", error);
  }
}

async function fetchQueueDepth() {
  try {
    const { data } = await api.get("/automation/dashboard/queue/depth");
    queueDepth.value = data;
  } catch (error) {
    console.error("Error fetching queue depth:", error);
  }
}

async function fetchAutomations() {
  try {
    const { data } = await api.get("/automation/dashboard/automations");
    automations.value = data.automations || [];
  } catch (error) {
    console.error("Error fetching automations:", error);
  }
}

async function fetchEvents() {
  try {
    const { data } = await api.get("/automation/dashboard/queue/events", {
      params: { limit: 50 },
    });
    events.value = data.events || [];
  } catch (error) {
    console.error("Error fetching events:", error);
  }
}

async function refreshData() {
  loading.value = true;
  try {
    await Promise.all([
      fetchHealth(),
      fetchOverview(),
      fetchQueueDepth(),
      fetchAutomations(),
      fetchEvents(),
    ]);
  } finally {
    loading.value = false;
  }
}

async function toggleAutomation(type: string, enabled: boolean) {
  try {
    await api.patch(`/automation/dashboard/automations/${type}/toggle`, null, {
      params: { enabled },
    });
    toast({
      title: enabled ? "Automação Ativada" : "Automação Desativada",
      description: `${type} foi ${enabled ? "ativada" : "desativada"}`,
    });
    await fetchAutomations();
  } catch (error) {
    toast({
      title: "Erro",
      description: "Não foi possível alterar a automação",
      variant: "destructive",
    });
  }
}

async function processNow(eventId: string) {
  try {
    await api.post(`/automation/dashboard/schedule/${eventId}/process`);
    toast({
      title: "Evento Processado",
      description: "O evento foi processado com sucesso",
    });
    await fetchEvents();
  } catch (error) {
    toast({
      title: "Erro",
      description: "Não foi possível processar o evento",
      variant: "destructive",
    });
  }
}

async function cancelEvent(eventId: string) {
  try {
    await api.delete(`/automation/dashboard/schedule/${eventId}`);
    toast({
      title: "Evento Cancelado",
      description: "O evento foi removido da fila",
    });
    await fetchEvents();
  } catch (error) {
    toast({
      title: "Erro",
      description: "Não foi possível cancelar o evento",
      variant: "destructive",
    });
  }
}

function getStatusVariant(status: string) {
  switch (status) {
    case "completed":
      return "default";
    case "pending":
      return "secondary";
    case "processing":
      return "outline";
    case "failed":
      return "destructive";
    default:
      return "secondary";
  }
}

function getPriorityVariant(priority: string) {
  switch (priority) {
    case "high":
      return "destructive";
    case "normal":
      return "default";
    case "low":
      return "secondary";
    default:
      return "secondary";
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleString("pt-BR");
}

function formatMs(ms?: number) {
  if (!ms) return "0ms";
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

// Lifecycle
onMounted(() => {
  refreshData();
  // Auto-refresh every 30 seconds
  refreshInterval = setInterval(refreshData, 30000);
});

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});
</script>

<style scoped>
.automation-dashboard {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
