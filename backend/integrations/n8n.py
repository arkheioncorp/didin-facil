"""
n8n Integration
===============
Integração com n8n para automações avançadas via webhooks.

Repository: https://github.com/n8n-io/n8n
License: Sustainable Use License (Self-hosted OK)

Funcionalidades:
- Trigger de workflows via webhook
- Receber dados de workflows
- Gerenciar workflows via API
- Monitorar execuções
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import httpx
import logging

from shared.config import settings

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Status de execução de workflow."""
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELED = "canceled"


class TriggerType(str, Enum):
    """Tipos de trigger disponíveis."""
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    EVENT = "event"


@dataclass
class WorkflowExecution:
    """Representa uma execução de workflow."""
    id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class N8nWorkflow:
    """Representa um workflow do n8n."""
    id: str
    name: str
    active: bool
    created_at: datetime
    updated_at: datetime
    nodes: List[Dict[str, Any]] = None
    connections: Dict[str, Any] = None


class N8nClient:
    """
    Cliente para integração com n8n.
    
    Uso:
        client = N8nClient()
        
        # Trigger webhook
        result = await client.trigger_webhook(
            webhook_path="/didin/new-deal",
            data={"product": "iPhone 15", "price": 4999}
        )
        
        # Listar workflows
        workflows = await client.list_workflows()
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        webhook_url: Optional[str] = None
    ):
        self.api_url = api_url or settings.N8N_API_URL or "http://localhost:5678"
        self.api_key = api_key or settings.N8N_API_KEY
        self.webhook_url = webhook_url or settings.N8N_WEBHOOK_URL or f"{self.api_url}/webhook"
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtém cliente HTTP com configuração."""
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            if self.api_key:
                headers["X-N8N-API-KEY"] = self.api_key
            
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=headers,
                timeout=60.0
            )
        return self._client
    
    async def close(self):
        """Fecha cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # ========================================
    # WEBHOOK TRIGGERS
    # ========================================
    
    async def trigger_webhook(
        self,
        webhook_path: str,
        data: Dict[str, Any],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Dispara um webhook do n8n.
        
        Args:
            webhook_path: Caminho do webhook (ex: /didin/new-deal)
            data: Dados a enviar
            method: Método HTTP (POST, GET)
        
        Returns:
            Resposta do workflow
        """
        url = f"{self.webhook_url}{webhook_path}"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                if method.upper() == "POST":
                    response = await client.post(url, json=data)
                else:
                    response = await client.get(url, params=data)
                
                response.raise_for_status()
                
                # Tentar parsear JSON, senão retornar texto
                try:
                    return response.json()
                except ValueError:
                    return {"response": response.text}
                    
            except httpx.HTTPError as e:
                logger.error(f"Failed to trigger n8n webhook: {e}")
                raise
    
    async def trigger_workflow_by_id(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Executa um workflow diretamente por ID.
        
        Args:
            workflow_id: ID do workflow
            data: Dados de entrada
        
        Returns:
            WorkflowExecution com resultado
        """
        client = await self._get_client()
        
        payload = {"data": data or {}}
        
        try:
            response = await client.post(
                f"/api/v1/workflows/{workflow_id}/execute",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            return WorkflowExecution(
                id=result.get("executionId", ""),
                workflow_id=workflow_id,
                status=WorkflowStatus.SUCCESS if result.get("success") else WorkflowStatus.ERROR,
                started_at=datetime.utcnow(),
                finished_at=datetime.utcnow(),
                data=result.get("data")
            )
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to execute n8n workflow: {e}")
            raise
    
    # ========================================
    # WORKFLOW MANAGEMENT
    # ========================================
    
    async def list_workflows(
        self,
        active: Optional[bool] = None,
        limit: int = 50
    ) -> List[N8nWorkflow]:
        """Lista todos os workflows."""
        client = await self._get_client()
        
        params = {"limit": limit}
        if active is not None:
            params["active"] = str(active).lower()
        
        try:
            response = await client.get("/api/v1/workflows", params=params)
            response.raise_for_status()
            data = response.json()
            
            workflows = []
            for wf in data.get("data", []):
                workflows.append(N8nWorkflow(
                    id=wf.get("id", ""),
                    name=wf.get("name", ""),
                    active=wf.get("active", False),
                    created_at=datetime.fromisoformat(wf.get("createdAt", "2024-01-01")),
                    updated_at=datetime.fromisoformat(wf.get("updatedAt", "2024-01-01")),
                    nodes=wf.get("nodes"),
                    connections=wf.get("connections")
                ))
            
            return workflows
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to list n8n workflows: {e}")
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[N8nWorkflow]:
        """Obtém detalhes de um workflow."""
        client = await self._get_client()
        
        try:
            response = await client.get(f"/api/v1/workflows/{workflow_id}")
            response.raise_for_status()
            wf = response.json()
            
            return N8nWorkflow(
                id=wf.get("id", ""),
                name=wf.get("name", ""),
                active=wf.get("active", False),
                created_at=datetime.fromisoformat(wf.get("createdAt", "2024-01-01")),
                updated_at=datetime.fromisoformat(wf.get("updatedAt", "2024-01-01")),
                nodes=wf.get("nodes"),
                connections=wf.get("connections")
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def activate_workflow(self, workflow_id: str) -> bool:
        """Ativa um workflow."""
        client = await self._get_client()
        
        try:
            response = await client.post(f"/api/v1/workflows/{workflow_id}/activate")
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to activate workflow: {e}")
            return False
    
    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """Desativa um workflow."""
        client = await self._get_client()
        
        try:
            response = await client.post(f"/api/v1/workflows/{workflow_id}/deactivate")
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to deactivate workflow: {e}")
            return False
    
    # ========================================
    # EXECUTIONS
    # ========================================
    
    async def get_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 20
    ) -> List[WorkflowExecution]:
        """Lista execuções de workflows."""
        client = await self._get_client()
        
        params = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id
        if status:
            params["status"] = status.value
        
        try:
            response = await client.get("/api/v1/executions", params=params)
            response.raise_for_status()
            data = response.json()
            
            executions = []
            for ex in data.get("data", []):
                executions.append(WorkflowExecution(
                    id=ex.get("id", ""),
                    workflow_id=ex.get("workflowId", ""),
                    status=WorkflowStatus(ex.get("status", "error")),
                    started_at=datetime.fromisoformat(ex.get("startedAt", "2024-01-01")),
                    finished_at=datetime.fromisoformat(ex.get("finishedAt")) if ex.get("finishedAt") else None,
                    data=ex.get("data"),
                    error=ex.get("stoppedAt")
                ))
            
            return executions
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get executions: {e}")
            raise


# ============================================
# WORKFLOWS PRÉ-DEFINIDOS PARA DIDIN FÁCIL
# ============================================

DIDIN_N8N_WORKFLOWS = {
    "price_drop_alert": {
        "name": "Alerta de Queda de Preço",
        "description": "Envia notificação quando um produto monitorado baixa de preço",
        "trigger": TriggerType.WEBHOOK,
        "webhook_path": "/didin/price-drop",
        "actions": [
            "Verificar usuários interessados",
            "Enviar WhatsApp via Evolution API",
            "Enviar Email",
            "Atualizar banco de dados"
        ]
    },
    "daily_deals_digest": {
        "name": "Resumo Diário de Ofertas",
        "description": "Envia resumo diário das melhores ofertas",
        "trigger": TriggerType.SCHEDULE,
        "schedule": "0 9 * * *",  # 9h todos os dias
        "actions": [
            "Buscar melhores ofertas do dia",
            "Gerar conteúdo com IA",
            "Postar no Instagram",
            "Postar no TikTok",
            "Enviar newsletter"
        ]
    },
    "new_user_onboarding": {
        "name": "Onboarding de Novo Usuário",
        "description": "Sequência de boas-vindas para novos usuários",
        "trigger": TriggerType.WEBHOOK,
        "webhook_path": "/didin/new-user",
        "actions": [
            "Enviar email de boas-vindas",
            "Enviar WhatsApp de apresentação",
            "Agendar follow-up em 3 dias",
            "Adicionar ao CRM"
        ]
    },
    "social_post_scheduler": {
        "name": "Agendador de Posts",
        "description": "Publica posts agendados nas redes sociais",
        "trigger": TriggerType.SCHEDULE,
        "schedule": "*/5 * * * *",  # A cada 5 minutos
        "actions": [
            "Verificar posts agendados para agora",
            "Publicar no Instagram",
            "Publicar no TikTok",
            "Publicar no YouTube",
            "Atualizar status no banco"
        ]
    },
    "lead_qualification": {
        "name": "Qualificação de Leads",
        "description": "Qualifica leads automaticamente com base em interações",
        "trigger": TriggerType.WEBHOOK,
        "webhook_path": "/didin/lead-action",
        "actions": [
            "Calcular score do lead",
            "Atualizar status no CRM",
            "Notificar vendedor se score alto",
            "Adicionar a sequência de nurturing"
        ]
    }
}


# Factory function para obter cliente configurado
_n8n_client: Optional[N8nClient] = None


def get_n8n_client() -> N8nClient:
    """
    Obtém instância singleton do cliente n8n.

    Returns:
        N8nClient configurado
    """
    global _n8n_client

    if _n8n_client is None:
        _n8n_client = N8nClient(
            api_url=getattr(settings, 'N8N_URL', 'http://localhost:5678'),
            api_key=getattr(settings, 'N8N_API_KEY', None),
        )

    return _n8n_client
