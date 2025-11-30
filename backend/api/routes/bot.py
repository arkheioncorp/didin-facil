# ============================================
# Seller Bot API Routes
# ============================================
#
# Endpoints para controle do bot de automação.
# Requer licença Premium (R$149,90/mês)

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field

# Adiciona o diretório pai ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.middleware.auth import get_current_user
from api.services.license import LicenseService
from seller_bot import TaskQueueManager
from seller_bot.profiles import ProfileManager
from seller_bot.queue.models import TaskPriority, TaskState
from seller_bot.tasks import (
    AnalyticsTask,
    ManageOrdersTask,
    PostProductTask,
    ReplyMessagesTask,
)

router = APIRouter(prefix="/bot", tags=["Seller Bot"])

# Instâncias globais (em produção, usar dependency injection)
_queue_manager: Optional[TaskQueueManager] = None
_profile_manager: Optional[ProfileManager] = None


# ============================================
# Dependencies
# ============================================


async def verify_premium_access(
    current_user: dict = Depends(get_current_user)
):
    """
    Verifica se o usuário tem acesso Premium Bot.
    Lança HTTPException 402 se não tiver.
    """
    license_service = LicenseService()
    email = current_user["email"]
    license_info = await license_service.get_license_by_email(email)

    if not license_info:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": "Requer assinatura Premium Bot",
                "plan_required": "premium_bot",
                "price": "R$149,90/mês",
                "features": [
                    "Publicar produtos automaticamente",
                    "Gerenciar pedidos e envios",
                    "Responder mensagens com IA",
                    "Extrair analytics em tempo real"
                ]
            }
        )

    features = LicenseService.get_plan_features(license_info["plan"])

    if not features.get("seller_bot", False):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": "Seu plano não inclui o Seller Bot",
                "current_plan": license_info["plan"],
                "plan_required": "premium_bot",
                "price": "R$149,90/mês",
                "upgrade_url": "/subscription?upgrade=premium_bot"
            }
        )

    return current_user


def get_queue_manager() -> TaskQueueManager:
    """Dependency para obter o gerenciador de filas"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = TaskQueueManager()
    return _queue_manager


def get_profile_manager() -> ProfileManager:
    """Dependency para obter o gerenciador de perfis"""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager


# ============================================
# Request/Response Models
# ============================================


class StartTaskRequest(BaseModel):
    """Request para iniciar uma tarefa"""

    task_type: str = Field(
        ...,
        description="Tipo da tarefa",
        examples=["post_product", "manage_orders", "reply_messages"]
    )
    task_description: Optional[str] = Field(
        None,
        description="Descrição customizada (opcional)"
    )
    task_data: Optional[dict] = Field(
        None,
        description="Dados da tarefa"
    )
    priority: TaskPriority = Field(default=TaskPriority.NORMAL)


class TaskResponse(BaseModel):
    """Response com informações da tarefa"""

    id: str
    task_type: str
    state: TaskState
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    screenshots: list[str] = []
    logs: list[str] = []


class QueueStatsResponse(BaseModel):
    """Response com estatísticas da fila"""

    total_queued: int
    total_running: int
    total_completed: int
    total_failed: int
    by_task_type: dict[str, int]


class ProfileRequest(BaseModel):
    """Request para criar/clonar perfil"""

    name: str = Field(..., description="Nome do perfil")
    clone_from_system: bool = Field(
        default=False,
        description="Clonar do Chrome do sistema"
    )


class ProfileResponse(BaseModel):
    """Response com informações do perfil"""

    id: str
    name: str
    is_logged_in: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime


# ============================================
# Endpoints de Tarefas
# ============================================


@router.post("/tasks", response_model=TaskResponse)
async def start_task(
    request: StartTaskRequest,
    queue: TaskQueueManager = Depends(get_queue_manager),
    user: dict = Depends(verify_premium_access),
):
    """
    Inicia uma nova tarefa de automação.

    Requer licença Premium (R$149,90/mês).

    Tipos de tarefa:
    - post_product: Publicar produto
    - manage_orders: Gerenciar pedidos (etiquetas, envios)
    - reply_messages: Responder mensagens
    - analytics: Extrair métricas
    """
    user_id = user.get("id", user.get("email", "unknown"))
    description = request.task_description

    if not description:
        description = _build_task_description(request)

    # Enfileirar tarefa
    task = await queue.enqueue(
        user_id=user_id,
        task_type=request.task_type,
        task_description=description,
        task_data=request.task_data,
        priority=request.priority,
    )

    return TaskResponse(
        id=task.id,
        task_type=task.task_type,
        state=task.state,
        created_at=task.created_at,
        screenshots=task.screenshots,
        logs=task.logs,
    )


def _build_task_description(request: StartTaskRequest) -> str:
    """Constrói descrição da tarefa baseado no tipo"""
    if request.task_type == "post_product":
        if not request.task_data:
            raise HTTPException(
                status_code=400,
                detail="task_data é obrigatório para post_product"
            )
        from seller_bot.tasks.post_product import ProductData
        product = ProductData(**request.task_data)
        return PostProductTask.build_prompt(product)

    if request.task_type == "manage_orders":
        action = "print_labels"
        if request.task_data:
            action = request.task_data.get("action", "print_labels")
        if action == "print_labels":
            return ManageOrdersTask.build_print_labels_prompt()
        if action == "process_returns":
            return ManageOrdersTask.build_process_returns_prompt()
        return ManageOrdersTask.build_export_orders_prompt()

    if request.task_type == "reply_messages":
        return ReplyMessagesTask.build_reply_prompt()

    if request.task_type == "analytics":
        action = "overview"
        if request.task_data:
            action = request.task_data.get("action", "overview")
        if action == "top_products":
            return AnalyticsTask.build_top_products_prompt()
        if action == "orders_summary":
            return AnalyticsTask.build_orders_summary_prompt()
        return AnalyticsTask.build_extract_overview_prompt()

    raise HTTPException(
        status_code=400,
        detail=f"Tipo de tarefa desconhecido: {request.task_type}"
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    queue: TaskQueueManager = Depends(get_queue_manager),
    user: dict = Depends(verify_premium_access),
):
    """Obtém status de uma tarefa"""
    task = await queue.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Tarefa não encontrada"
        )

    return TaskResponse(
        id=task.id,
        task_type=task.task_type,
        state=task.state,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        error_message=task.error_message,
        screenshots=task.screenshots,
        logs=task.logs,
    )


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    queue: TaskQueueManager = Depends(get_queue_manager),
    user: dict = Depends(verify_premium_access),
):
    """Lista todas as tarefas do usuário"""
    user_id = user.get("id", user.get("email", "unknown"))
    tasks = await queue.get_user_tasks(user_id)

    return [
        TaskResponse(
            id=t.id,
            task_type=t.task_type,
            state=t.state,
            created_at=t.created_at,
            started_at=t.started_at,
            completed_at=t.completed_at,
            error_message=t.error_message,
            screenshots=t.screenshots,
            logs=t.logs,
        )
        for t in tasks
    ]


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    queue: TaskQueueManager = Depends(get_queue_manager),
    user: dict = Depends(verify_premium_access),
):
    """Cancela uma tarefa"""
    success = await queue.cancel(task_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Tarefa não encontrada ou já finalizada"
        )

    return {"message": "Tarefa cancelada", "task_id": task_id}


@router.get("/stats", response_model=QueueStatsResponse)
async def get_stats(
    queue: TaskQueueManager = Depends(get_queue_manager),
    user: dict = Depends(verify_premium_access),
):
    """Obtém estatísticas da fila"""
    stats = await queue.get_stats()

    return QueueStatsResponse(
        total_queued=stats.total_queued,
        total_running=stats.total_running,
        total_completed=stats.total_completed,
        total_failed=stats.total_failed,
        by_task_type=stats.by_task_type,
    )


# ============================================
# Endpoints de Perfis
# ============================================


@router.post("/profiles", response_model=ProfileResponse)
async def create_profile(
    request: ProfileRequest,
    profiles: ProfileManager = Depends(get_profile_manager),
    user: dict = Depends(verify_premium_access),
):
    """
    Cria um novo perfil de navegador.

    Se clone_from_system=True, clona cookies do Chrome do sistema.
    """
    user_id = user.get("id", user.get("email", "unknown"))

    clone_from = None
    if request.clone_from_system:
        clone_from = profiles.detect_system_chrome_profile()
        if not clone_from:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível detectar perfil Chrome"
            )

    profile = profiles.create_profile(
        user_id=user_id,
        name=request.name,
        clone_from=clone_from,
    )

    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        is_logged_in=profile.is_logged_in,
        last_used_at=profile.last_used_at,
        created_at=profile.created_at,
    )


@router.get("/profiles", response_model=list[ProfileResponse])
async def list_profiles(
    profiles: ProfileManager = Depends(get_profile_manager),
    user: dict = Depends(verify_premium_access),
):
    """Lista todos os perfis do usuário"""
    user_id = user.get("id", user.get("email", "unknown"))
    user_profiles = profiles.get_user_profiles(user_id)

    return [
        ProfileResponse(
            id=p.id,
            name=p.name,
            is_logged_in=p.is_logged_in,
            last_used_at=p.last_used_at,
            created_at=p.created_at,
        )
        for p in user_profiles
    ]


@router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: str,
    profiles: ProfileManager = Depends(get_profile_manager),
    user: dict = Depends(verify_premium_access),
):
    """Deleta um perfil"""
    success = profiles.delete_profile(profile_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Perfil não encontrado"
        )

    return {"message": "Perfil deletado", "profile_id": profile_id}


@router.post("/profiles/{profile_id}/verify")
async def verify_profile_login(
    profile_id: str,
    profiles: ProfileManager = Depends(get_profile_manager),
    user: dict = Depends(verify_premium_access),
):
    """Verifica se o perfil está logado no TikTok Seller"""
    profile = profiles.get_profile(profile_id)

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Perfil não encontrado"
        )

    is_logged = await profiles.verify_login_status(profile_id)

    return {
        "profile_id": profile_id,
        "is_logged_in": is_logged,
        "message": (
            "Logado no TikTok Seller"
            if is_logged
            else "Não logado - faça login manualmente"
        ),
    }


# ============================================
# Endpoints de Controle do Bot
# ============================================


@router.post("/start")
async def start_bot(
    background_tasks: BackgroundTasks,
    queue: TaskQueueManager = Depends(get_queue_manager),
    user: dict = Depends(verify_premium_access),
):
    """Inicia o worker do bot"""
    background_tasks.add_task(queue.start)
    return {"message": "Bot iniciado", "status": "running"}


@router.post("/stop")
async def stop_bot(
    queue: TaskQueueManager = Depends(get_queue_manager),
    user: dict = Depends(verify_premium_access),
):
    """Para o worker do bot"""
    await queue.stop()
    return {"message": "Bot parado", "status": "stopped"}
