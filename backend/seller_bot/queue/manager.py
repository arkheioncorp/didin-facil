# ============================================
# Task Queue Manager - Gerenciador de Filas
# ============================================

import asyncio
import logging
from datetime import datetime
from typing import Callable, Optional
from collections import deque

from .models import QueuedTask, TaskState, TaskPriority, QueueStats

logger = logging.getLogger(__name__)


class TaskQueueManager:
    """
    Gerenciador de fila de tarefas do Seller Bot.
    
    Implementa uma fila em memória com prioridades.
    Para produção, pode ser substituído por Redis Queue ou Celery.
    """
    
    def __init__(
        self,
        max_concurrent: int = 1,  # Uma tarefa por vez (seguro)
        on_task_start: Optional[Callable[[QueuedTask], None]] = None,
        on_task_complete: Optional[Callable[[QueuedTask], None]] = None,
        on_task_error: Optional[
            Callable[[QueuedTask, Exception], None]
        ] = None,
    ):
        self.max_concurrent = max_concurrent
        self.on_task_start = on_task_start
        self.on_task_complete = on_task_complete
        self.on_task_error = on_task_error
        
        # Filas por prioridade
        self._queues: dict[TaskPriority, deque[QueuedTask]] = {
            priority: deque() for priority in TaskPriority
        }
        
        # Tarefas em execução
        self._running: dict[str, QueuedTask] = {}
        
        # Histórico de tarefas completadas
        self._history: list[QueuedTask] = []
        self._max_history = 100
        
        # Lock para operações thread-safe
        self._lock = asyncio.Lock()
        
        # Worker loop
        self._worker_task: Optional[asyncio.Task] = None
        self._should_stop = False
    
    async def start(self) -> None:
        """Inicia o worker de processamento"""
        if self._worker_task is None:
            self._should_stop = False
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("TaskQueueManager iniciado")
    
    async def stop(self) -> None:
        """Para o worker de processamento"""
        self._should_stop = True
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        logger.info("TaskQueueManager parado")
    
    async def enqueue(
        self,
        user_id: str,
        task_type: str,
        task_description: str,
        task_data: Optional[dict] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> QueuedTask:
        """Adiciona uma tarefa à fila"""
        
        task = QueuedTask(
            user_id=user_id,
            task_type=task_type,
            task_description=task_description,
            task_data=task_data,
            priority=priority,
        )
        
        async with self._lock:
            self._queues[priority].append(task)
        
        logger.info(
            f"Tarefa {task.id} adicionada à fila (prioridade: {priority.name})"
        )
        return task
    
    async def cancel(self, task_id: str) -> bool:
        """Cancela uma tarefa na fila ou em execução"""
        
        async with self._lock:
            # Procurar nas filas
            for priority, queue in self._queues.items():
                for task in queue:
                    if task.id == task_id:
                        queue.remove(task)
                        task.state = TaskState.CANCELLED
                        self._add_to_history(task)
                        logger.info(
                            f"Tarefa {task_id} cancelada (estava na fila)"
                        )
                        return True
            
            # Procurar nas em execução
            if task_id in self._running:
                task = self._running[task_id]
                task.state = TaskState.CANCELLED
                # A tarefa em execução será parada pelo agente
                logger.info(
                    f"Tarefa {task_id} marcada para cancelamento (em execução)"
                )
                return True
        
        return False
    
    async def get_task(self, task_id: str) -> Optional[QueuedTask]:
        """Obtém uma tarefa pelo ID"""
        
        async with self._lock:
            # Procurar nas filas
            for queue in self._queues.values():
                for task in queue:
                    if task.id == task_id:
                        return task
            
            # Procurar nas em execução
            if task_id in self._running:
                return self._running[task_id]
            
            # Procurar no histórico
            for task in self._history:
                if task.id == task_id:
                    return task
        
        return None
    
    async def get_user_tasks(self, user_id: str) -> list[QueuedTask]:
        """Obtém todas as tarefas de um usuário"""
        
        tasks = []
        
        async with self._lock:
            # Tarefas na fila
            for queue in self._queues.values():
                for task in queue:
                    if task.user_id == user_id:
                        tasks.append(task)
            
            # Tarefas em execução
            for task in self._running.values():
                if task.user_id == user_id:
                    tasks.append(task)
            
            # Histórico recente
            for task in self._history:
                if task.user_id == user_id:
                    tasks.append(task)
        
        return tasks
    
    async def get_stats(self) -> QueueStats:
        """Retorna estatísticas da fila"""
        
        stats = QueueStats()
        
        async with self._lock:
            # Contagem de tarefas na fila
            for queue in self._queues.values():
                stats.total_queued += len(queue)
            
            # Tarefas em execução
            stats.total_running = len(self._running)
            
            # Contagem do histórico
            for task in self._history:
                if task.state == TaskState.COMPLETED:
                    stats.total_completed += 1
                elif task.state == TaskState.FAILED:
                    stats.total_failed += 1
                
                # Por tipo
                task_type = task.task_type
                stats.by_task_type[task_type] = (
                    stats.by_task_type.get(task_type, 0) + 1
                )
        
        return stats
    
    async def _worker_loop(self) -> None:
        """Loop principal do worker"""
        
        while not self._should_stop:
            try:
                # Verificar se pode pegar mais tarefas
                if len(self._running) >= self.max_concurrent:
                    await asyncio.sleep(1)
                    continue
                
                # Pegar próxima tarefa (maior prioridade primeiro)
                task = await self._dequeue_next()
                
                if task is None:
                    await asyncio.sleep(1)
                    continue
                
                # Executar tarefa
                await self._execute_task(task)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Erro no worker loop: {e}")
                await asyncio.sleep(5)
    
    async def _dequeue_next(self) -> Optional[QueuedTask]:
        """Remove e retorna a próxima tarefa da fila"""
        
        async with self._lock:
            # Verificar filas por prioridade (maior primeiro)
            for priority in sorted(
                TaskPriority, key=lambda p: p.value, reverse=True
            ):
                queue = self._queues[priority]
                if queue:
                    return queue.popleft()
        
        return None
    
    async def _execute_task(self, task: QueuedTask) -> None:
        """Executa uma tarefa"""
        
        task.state = TaskState.RUNNING
        task.started_at = datetime.now()
        
        async with self._lock:
            self._running[task.id] = task
        
        if self.on_task_start:
            self.on_task_start(task)
        
        try:
            # Determinar qual agente usar baseado no tipo da tarefa
            is_social_task = any(
                task.task_type.startswith(prefix)
                for prefix in [
                    "instagram_", "whatsapp_", "tiktok_", "youtube_"
                ]
            )
            
            if is_social_task:
                from ..social_agent import SocialMediaAgent
                agent = SocialMediaAgent()
                result = await agent.run_task(
                    task_id=task.id,
                    task_type=task.task_type,
                    task_description=task.task_description,
                    task_data=task.task_data
                )
            else:
                # Default: SellerBotAgent (Browser Use)
                from ..agent import SellerBotAgent
                agent = SellerBotAgent()
                result = await agent.run_task(
                    task_id=task.id,
                    task_type=task.task_type,
                    task_description=task.task_description,
                    task_data=task.task_data,
                )
            
            # Atualizar tarefa com resultado
            task.result = result.result
            task.screenshots = result.screenshots
            task.logs = result.logs
            task.state = (
                TaskState.COMPLETED
                if result.status == "completed"
                else TaskState.FAILED
            )
            task.error_message = result.error
            
            if self.on_task_complete:
                self.on_task_complete(task)
            
        except Exception as e:
            task.state = TaskState.FAILED
            task.error_message = str(e)
            
            if self.on_task_error:
                self.on_task_error(task, e)
            
            # Retry se permitido
            if task.retries < task.max_retries:
                task.retries += 1
                task.state = TaskState.RETRY
                async with self._lock:
                    self._queues[TaskPriority.NORMAL].append(task)
                logger.info(
                    f"Tarefa {task.id} será reexecutada "
                    f"(tentativa {task.retries})"
                )
            
        finally:
            task.completed_at = datetime.now()
            
            async with self._lock:
                if task.id in self._running:
                    del self._running[task.id]
            
            self._add_to_history(task)
    
    def _add_to_history(self, task: QueuedTask) -> None:
        """Adiciona tarefa ao histórico"""
        self._history.append(task)
        
        # Limitar tamanho do histórico
        while len(self._history) > self._max_history:
            self._history.pop(0)
