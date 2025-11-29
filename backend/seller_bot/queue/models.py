# ============================================
# Queue Models - Modelos para Fila de Tarefas
# ============================================

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


class TaskPriority(int, Enum):
    """Prioridade de execução"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    URGENT = 20


class TaskState(str, Enum):
    """Estado da tarefa na fila"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class QueuedTask(BaseModel):
    """Tarefa na fila de execução"""
    
    # Identificação
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ID do usuário dono da tarefa")
    
    # Tipo e dados
    task_type: str = Field(..., description="Tipo da tarefa (post_product, manage_orders, etc.)")
    task_description: str = Field(..., description="Descrição em linguagem natural")
    task_data: Optional[dict[str, Any]] = Field(None, description="Dados adicionais")
    
    # Estado
    state: TaskState = Field(default=TaskState.QUEUED)
    priority: TaskPriority = Field(default=TaskPriority.NORMAL)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Execução
    retries: int = Field(default=0)
    max_retries: int = Field(default=3)
    error_message: Optional[str] = None
    
    # Resultado
    result: Optional[dict[str, Any]] = None
    screenshots: list[str] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class QueueStats(BaseModel):
    """Estatísticas da fila"""
    
    total_queued: int = 0
    total_running: int = 0
    total_completed: int = 0
    total_failed: int = 0
    
    # Por tipo de tarefa
    by_task_type: dict[str, int] = Field(default_factory=dict)
    
    # Tempos
    avg_execution_time_seconds: Optional[float] = None
    oldest_queued_at: Optional[datetime] = None
