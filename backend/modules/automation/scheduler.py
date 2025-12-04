"""
Automation Scheduler Service.

Processa eventos de automação pendentes e agenda execuções futuras.
Integra com n8n Orchestrator para disparar workflows.

Autor: TikTrend Finder Team
Data: Novembro 2025
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .n8n_orchestrator import (AutomationEvent, AutomationPriority,
                               AutomationType, N8nOrchestrator)

logger = logging.getLogger(__name__)


# ============================================
# ENUMS & CONSTANTS
# ============================================

class ScheduleStatus(str, Enum):
    """Status de agendamento."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ScheduleType(str, Enum):
    """Tipos de agendamento."""
    ONE_TIME = "one_time"          # Execução única
    RECURRING = "recurring"        # Execução recorrente
    DELAYED = "delayed"            # Execução com delay
    BATCH = "batch"                # Execução em lote
    CONDITIONAL = "conditional"    # Execução condicional


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class ScheduledEvent:
    """Evento agendado para processamento."""
    id: str
    automation_type: AutomationType
    schedule_type: ScheduleType
    user_id: str
    data: Dict[str, Any]
    scheduled_for: datetime
    priority: AutomationPriority = AutomationPriority.NORMAL
    status: ScheduleStatus = ScheduleStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulerStats:
    """Estatísticas do scheduler."""
    total_pending: int = 0
    total_processing: int = 0
    total_completed: int = 0
    total_failed: int = 0
    events_per_type: Dict[str, int] = field(default_factory=dict)
    avg_processing_time_ms: float = 0.0
    last_run: Optional[datetime] = None


# ============================================
# SCHEDULER SERVICE
# ============================================

class AutomationScheduler:
    """
    Serviço de agendamento de automações.
    
    Responsabilidades:
    - Agendar eventos para execução futura
    - Processar eventos pendentes
    - Gerenciar retries de eventos falhados
    - Executar jobs recorrentes
    - Coletar métricas de execução
    """

    # Configurações padrão
    DEFAULT_BATCH_SIZE = 50
    DEFAULT_POLL_INTERVAL = 30  # segundos
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 60  # segundos
    
    # Delays padrão por tipo de automação (em minutos)
    DEFAULT_DELAYS = {
        AutomationType.NEW_USER_WELCOME: 1,
        AutomationType.NEW_LEAD_NURTURING: 60,   # 1 hora
        AutomationType.CART_ABANDONED: 30,       # 30 min
        AutomationType.PRICE_DROP_ALERT: 0,      # Imediato
        AutomationType.POST_PURCHASE_THANKS: 5,
        AutomationType.REVIEW_REQUEST: 1440,     # 24 horas
        AutomationType.COMPLAINT_ALERT: 0,       # Imediato
        AutomationType.HUMAN_HANDOFF: 0,         # Imediato
        AutomationType.INACTIVE_USER: 4320,      # 3 dias
    }

    def __init__(
        self,
        orchestrator: N8nOrchestrator,
        batch_size: int = DEFAULT_BATCH_SIZE,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ):
        """
        Inicializa o scheduler.
        
        Args:
            orchestrator: Instância do N8nOrchestrator
            batch_size: Tamanho do lote para processamento
            poll_interval: Intervalo de polling em segundos
        """
        self.orchestrator = orchestrator
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        
        # Armazenamento em memória (substituir por DB em produção)
        self._pending_events: Dict[str, ScheduledEvent] = {}
        self._processing_events: Dict[str, ScheduledEvent] = {}
        self._completed_events: List[ScheduledEvent] = []
        self._failed_events: List[ScheduledEvent] = []
        
        # Controle
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._stats = SchedulerStats()
        
        # Callbacks
        self._on_event_completed: List[callable] = []
        self._on_event_failed: List[callable] = []
        
        logger.info(
            f"AutomationScheduler inicializado "
            f"(batch_size={batch_size}, poll_interval={poll_interval}s)"
        )

    # ========================================
    # AGENDAMENTO
    # ========================================

    async def schedule(
        self,
        automation_type: AutomationType,
        user_id: str,
        data: Dict[str, Any],
        schedule_type: ScheduleType = ScheduleType.DELAYED,
        delay_minutes: Optional[int] = None,
        scheduled_for: Optional[datetime] = None,
        priority: AutomationPriority = AutomationPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScheduledEvent:
        """
        Agenda um evento para execução.
        
        Args:
            automation_type: Tipo de automação
            user_id: ID do usuário
            data: Dados do evento
            schedule_type: Tipo de agendamento
            delay_minutes: Delay em minutos (usa padrão se None)
            scheduled_for: Data/hora específica (sobrescreve delay)
            priority: Prioridade do evento
            metadata: Metadados adicionais
            
        Returns:
            ScheduledEvent criado
        """
        import uuid

        # Calcular data de execução
        if scheduled_for:
            exec_time = scheduled_for
        elif delay_minutes is not None:
            exec_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
        else:
            default_delay = self.DEFAULT_DELAYS.get(automation_type, 0)
            exec_time = datetime.now(timezone.utc) + timedelta(minutes=default_delay)
        
        event = ScheduledEvent(
            id=str(uuid.uuid4()),
            automation_type=automation_type,
            schedule_type=schedule_type,
            user_id=user_id,
            data=data,
            scheduled_for=exec_time,
            priority=priority,
            metadata=metadata or {},
        )
        
        self._pending_events[event.id] = event
        self._stats.total_pending += 1
        
        logger.info(
            f"Evento agendado: {event.id} "
            f"({automation_type.value}) para {exec_time}"
        )
        
        return event

    async def schedule_batch(
        self,
        events: List[Dict[str, Any]]
    ) -> List[ScheduledEvent]:
        """
        Agenda múltiplos eventos em lote.
        
        Args:
            events: Lista de eventos com dados necessários
            
        Returns:
            Lista de ScheduledEvent criados
        """
        scheduled = []
        for event_data in events:
            event = await self.schedule(
                automation_type=event_data["automation_type"],
                user_id=event_data["user_id"],
                data=event_data.get("data", {}),
                schedule_type=event_data.get(
                    "schedule_type", ScheduleType.DELAYED
                ),
                delay_minutes=event_data.get("delay_minutes"),
                scheduled_for=event_data.get("scheduled_for"),
                priority=event_data.get(
                    "priority", AutomationPriority.NORMAL
                ),
                metadata=event_data.get("metadata"),
            )
            scheduled.append(event)
        
        logger.info(f"Batch de {len(scheduled)} eventos agendados")
        return scheduled

    async def cancel(self, event_id: str) -> bool:
        """
        Cancela um evento agendado.
        
        Args:
            event_id: ID do evento
            
        Returns:
            True se cancelado com sucesso
        """
        if event_id in self._pending_events:
            event = self._pending_events.pop(event_id)
            event.status = ScheduleStatus.CANCELLED
            self._stats.total_pending -= 1
            logger.info(f"Evento cancelado: {event_id}")
            return True
        
        logger.warning(f"Evento não encontrado para cancelar: {event_id}")
        return False

    async def reschedule(
        self,
        event_id: str,
        new_time: datetime
    ) -> Optional[ScheduledEvent]:
        """
        Reagenda um evento para nova data/hora.
        
        Args:
            event_id: ID do evento
            new_time: Nova data/hora de execução
            
        Returns:
            Evento reagendado ou None se não encontrado
        """
        if event_id in self._pending_events:
            event = self._pending_events[event_id]
            event.scheduled_for = new_time
            logger.info(f"Evento reagendado: {event_id} para {new_time}")
            return event
        
        return None

    # ========================================
    # PROCESSAMENTO
    # ========================================

    async def start(self):
        """Inicia o loop de processamento."""
        if self._running:
            logger.warning("Scheduler já está rodando")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("Scheduler iniciado")

    async def stop(self):
        """Para o loop de processamento."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler parado")

    async def _process_loop(self):
        """Loop principal de processamento."""
        logger.info("Loop de processamento iniciado")
        
        while self._running:
            try:
                await self._process_pending_events()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de processamento: {e}")
                await asyncio.sleep(self.poll_interval)

    async def _process_pending_events(self):
        """Processa eventos pendentes prontos para execução."""
        now = datetime.now(timezone.utc)
        self._stats.last_run = now
        
        # Encontrar eventos prontos (ordenados por prioridade)
        ready_events = [
            e for e in self._pending_events.values()
            if e.scheduled_for <= now and e.status == ScheduleStatus.PENDING
        ]
        
        # Ordenar por prioridade (HIGH primeiro)
        priority_order = {
            AutomationPriority.HIGH: 0,
            AutomationPriority.NORMAL: 1,
            AutomationPriority.LOW: 2,
        }
        ready_events.sort(key=lambda e: priority_order[e.priority])
        
        # Limitar ao batch size
        batch = ready_events[:self.batch_size]
        
        if batch:
            logger.info(f"Processando batch de {len(batch)} eventos")
        
        for event in batch:
            await self._process_event(event)

    async def _process_event(self, event: ScheduledEvent):
        """
        Processa um evento individual.
        
        Args:
            event: Evento a processar
        """
        event.status = ScheduleStatus.PROCESSING
        self._pending_events.pop(event.id, None)
        self._processing_events[event.id] = event
        self._stats.total_processing += 1
        self._stats.total_pending -= 1
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Disparar automação via orchestrator
            automation_event = AutomationEvent(
                event_type=event.automation_type.value,
                user_id=event.user_id,
                data=event.data,
                source="scheduler",
                priority=event.priority,
            )
            
            result = await self.orchestrator.process_event(automation_event)
            
            if result.get("success"):
                await self._mark_completed(event, start_time)
            else:
                error = result.get("error", "Unknown error")
                await self._handle_failure(event, error, start_time)
                
        except Exception as e:
            await self._handle_failure(event, str(e), start_time)

    async def _mark_completed(
        self,
        event: ScheduledEvent,
        start_time: datetime
    ):
        """Marca evento como completado."""
        event.status = ScheduleStatus.COMPLETED
        event.processed_at = datetime.now(timezone.utc)
        
        self._processing_events.pop(event.id, None)
        self._completed_events.append(event)
        
        self._stats.total_processing -= 1
        self._stats.total_completed += 1
        
        # Calcular tempo de processamento
        duration = (event.processed_at - start_time).total_seconds() * 1000
        self._update_avg_processing_time(duration)
        
        # Executar callbacks
        for callback in self._on_event_completed:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Erro em callback de conclusão: {e}")
        
        logger.info(
            f"Evento completado: {event.id} "
            f"({event.automation_type.value}) em {duration:.0f}ms"
        )

    async def _handle_failure(
        self,
        event: ScheduledEvent,
        error: str,
        start_time: datetime
    ):
        """Trata falha de processamento."""
        event.retry_count += 1
        event.error_message = error
        
        self._processing_events.pop(event.id, None)
        
        if event.retry_count < event.max_retries:
            # Reagendar para retry
            event.status = ScheduleStatus.RETRYING
            event.scheduled_for = datetime.now(timezone.utc) + timedelta(
                seconds=self.DEFAULT_RETRY_DELAY * event.retry_count
            )
            self._pending_events[event.id] = event
            self._stats.total_pending += 1
            
            logger.warning(
                f"Evento falhou, retry {event.retry_count}/{event.max_retries}: "
                f"{event.id} - {error}"
            )
        else:
            # Marcar como falho definitivo
            event.status = ScheduleStatus.FAILED
            event.processed_at = datetime.now(timezone.utc)
            self._failed_events.append(event)
            self._stats.total_failed += 1
            
            # Executar callbacks
            for callback in self._on_event_failed:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Erro em callback de falha: {e}")
            
            logger.error(
                f"Evento falhou definitivamente: {event.id} - {error}"
            )
        
        self._stats.total_processing -= 1

    def _update_avg_processing_time(self, duration_ms: float):
        """Atualiza tempo médio de processamento."""
        if self._stats.avg_processing_time_ms == 0:
            self._stats.avg_processing_time_ms = duration_ms
        else:
            # Média móvel
            self._stats.avg_processing_time_ms = (
                self._stats.avg_processing_time_ms * 0.9 + duration_ms * 0.1
            )

    # ========================================
    # PROCESSAMENTO MANUAL
    # ========================================

    async def process_now(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Processa um evento imediatamente.
        
        Args:
            event_id: ID do evento
            
        Returns:
            Resultado do processamento
        """
        if event_id not in self._pending_events:
            return {"success": False, "error": "Evento não encontrado"}
        
        event = self._pending_events[event_id]
        await self._process_event(event)
        
        return {
            "success": event.status == ScheduleStatus.COMPLETED,
            "status": event.status.value,
            "error": event.error_message,
        }

    async def process_all_pending(self) -> Dict[str, Any]:
        """
        Processa todos os eventos pendentes imediatamente.
        
        Returns:
            Resumo do processamento
        """
        total = len(self._pending_events)
        
        for event in list(self._pending_events.values()):
            event.scheduled_for = datetime.now(timezone.utc)
        
        await self._process_pending_events()
        
        return {
            "processed": total,
            "completed": self._stats.total_completed,
            "failed": self._stats.total_failed,
        }

    # ========================================
    # QUERIES
    # ========================================

    def get_pending_events(
        self,
        user_id: Optional[str] = None,
        automation_type: Optional[AutomationType] = None,
    ) -> List[ScheduledEvent]:
        """
        Retorna eventos pendentes com filtros opcionais.
        
        Args:
            user_id: Filtrar por usuário
            automation_type: Filtrar por tipo de automação
            
        Returns:
            Lista de eventos pendentes
        """
        events = list(self._pending_events.values())
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if automation_type:
            events = [e for e in events if e.automation_type == automation_type]
        
        return events

    def get_event(self, event_id: str) -> Optional[ScheduledEvent]:
        """
        Busca um evento por ID.
        
        Args:
            event_id: ID do evento
            
        Returns:
            Evento ou None
        """
        if event_id in self._pending_events:
            return self._pending_events[event_id]
        if event_id in self._processing_events:
            return self._processing_events[event_id]
        
        for e in self._completed_events + self._failed_events:
            if e.id == event_id:
                return e
        
        return None

    def get_stats(self) -> SchedulerStats:
        """Retorna estatísticas do scheduler."""
        # Atualizar contagem por tipo
        type_counts: Dict[str, int] = defaultdict(int)
        for event in self._pending_events.values():
            type_counts[event.automation_type.value] += 1
        
        self._stats.events_per_type = dict(type_counts)
        return self._stats

    def get_queue_depth(self) -> Dict[str, int]:
        """Retorna profundidade da fila por prioridade."""
        depths = {
            "high": 0,
            "normal": 0,
            "low": 0,
        }
        
        for event in self._pending_events.values():
            if event.priority == AutomationPriority.HIGH:
                depths["high"] += 1
            elif event.priority == AutomationPriority.NORMAL:
                depths["normal"] += 1
            else:
                depths["low"] += 1
        
        return depths

    # ========================================
    # CALLBACKS
    # ========================================

    def on_event_completed(self, callback: callable):
        """Registra callback para eventos completados."""
        self._on_event_completed.append(callback)

    def on_event_failed(self, callback: callable):
        """Registra callback para eventos falhados."""
        self._on_event_failed.append(callback)

    # ========================================
    # JOBS RECORRENTES
    # ========================================

    async def schedule_recurring(
        self,
        automation_type: AutomationType,
        user_id: str,
        data: Dict[str, Any],
        interval_hours: int,
        max_occurrences: int = 10,
    ) -> List[ScheduledEvent]:
        """
        Agenda eventos recorrentes.
        
        Args:
            automation_type: Tipo de automação
            user_id: ID do usuário
            data: Dados do evento
            interval_hours: Intervalo entre execuções
            max_occurrences: Número máximo de ocorrências
            
        Returns:
            Lista de eventos agendados
        """
        events = []
        
        for i in range(max_occurrences):
            scheduled_for = datetime.now(timezone.utc) + timedelta(
                hours=interval_hours * (i + 1)
            )
            
            event = await self.schedule(
                automation_type=automation_type,
                user_id=user_id,
                data={**data, "occurrence": i + 1},
                schedule_type=ScheduleType.RECURRING,
                scheduled_for=scheduled_for,
                metadata={"recurring_series": True, "total": max_occurrences},
            )
            events.append(event)
        
        logger.info(
            f"Série recorrente agendada: {len(events)} eventos "
            f"a cada {interval_hours}h"
        )
        return events


# ============================================
# FACTORY & SINGLETON
# ============================================

_scheduler_instance: Optional[AutomationScheduler] = None


def get_scheduler(
    orchestrator: Optional[N8nOrchestrator] = None
) -> AutomationScheduler:
    """
    Retorna instância singleton do scheduler.
    
    Args:
        orchestrator: Instância do orchestrator (necessário na 1ª chamada)
        
    Returns:
        AutomationScheduler instance
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        if orchestrator is None:
            raise ValueError(
                "orchestrator é obrigatório na primeira chamada"
            )
        _scheduler_instance = AutomationScheduler(orchestrator)
    
    return _scheduler_instance


async def start_scheduler(orchestrator: N8nOrchestrator):
    """
    Inicia o scheduler como serviço.
    
    Args:
        orchestrator: Instância do N8nOrchestrator
    """
    scheduler = get_scheduler(orchestrator)
    await scheduler.start()
    logger.info("Scheduler service started")
    return scheduler


async def stop_scheduler():
    """Para o scheduler."""
    global _scheduler_instance
    if _scheduler_instance:
        await _scheduler_instance.stop()
        _scheduler_instance = None
        logger.info("Scheduler service stopped")
