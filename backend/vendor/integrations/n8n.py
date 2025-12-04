"""
n8n Integration
===============
Integração com n8n para automação de workflows.

n8n: https://github.com/n8n-io/n8n
License: Fair-code (Apache 2.0 with Commons Clause)

Este módulo permite:
- Disparar workflows via webhook
- Executar workflows programaticamente
- Gerenciar credenciais e execuções
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import httpx
import logging

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ExecutionStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    RUNNING = "running"
    WAITING = "waiting"


@dataclass
class N8nConfig:
    """Configuração para n8n."""
    api_url: str  # Ex: http://localhost:5678
    api_key: str  # API key do n8n
    

@dataclass
class WorkflowExecution:
    """Resultado de execução de workflow."""
    execution_id: str
    status: ExecutionStatus
    data: Dict[str, Any]
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None


class N8nClient:
    """
    Cliente para API do n8n.
    
    Uso:
        config = N8nConfig(
            api_url="http://localhost:5678",
            api_key="n8n_api_key_here"
        )
        
        client = N8nClient(config)
        
        # Listar workflows
        workflows = await client.list_workflows()
        
        # Executar workflow
        result = await client.execute_workflow("workflow-id", {"name": "João"})
        
        # Disparar webhook
        await client.trigger_webhook("webhook-path", {"event": "new_order"})
    """
    
    def __init__(self, config: N8nConfig):
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.api_url.rstrip('/'),
            headers={"X-N8N-API-KEY": config.api_key},
            timeout=60.0  # Workflows podem demorar
        )
    
    async def close(self):
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    # ==================== Workflows ====================
    
    async def list_workflows(
        self,
        active_only: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Lista todos os workflows.
        
        Args:
            active_only: Se True, retorna apenas workflows ativos
            limit: Número máximo de resultados
        """
        params = {"limit": limit}
        if active_only:
            params["active"] = "true"
        
        response = await self._client.get("/api/v1/workflows", params=params)
        response.raise_for_status()
        data = response.json()
        
        return [
            {
                "id": wf["id"],
                "name": wf["name"],
                "active": wf["active"],
                "created_at": wf.get("createdAt"),
                "updated_at": wf.get("updatedAt")
            }
            for wf in data.get("data", [])
        ]
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Obtém detalhes de um workflow."""
        response = await self._client.get(f"/api/v1/workflows/{workflow_id}")
        response.raise_for_status()
        return response.json()
    
    async def activate_workflow(self, workflow_id: str) -> bool:
        """Ativa um workflow."""
        response = await self._client.post(
            f"/api/v1/workflows/{workflow_id}/activate"
        )
        response.raise_for_status()
        return True
    
    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """Desativa um workflow."""
        response = await self._client.post(
            f"/api/v1/workflows/{workflow_id}/deactivate"
        )
        response.raise_for_status()
        return True
    
    async def execute_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Executa um workflow programaticamente.
        
        Args:
            workflow_id: ID do workflow
            data: Dados de entrada para o workflow
            
        Returns:
            Resultado da execução
        """
        payload = {}
        if data:
            payload["data"] = data
        
        response = await self._client.post(
            f"/api/v1/workflows/{workflow_id}/run",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        
        return WorkflowExecution(
            execution_id=result.get("executionId", ""),
            status=ExecutionStatus.SUCCESS if result.get("finished") else ExecutionStatus.RUNNING,
            data=result.get("data", {}),
            started_at=result.get("startedAt"),
            finished_at=result.get("stoppedAt")
        )
    
    # ==================== Executions ====================
    
    async def get_execution(self, execution_id: str) -> WorkflowExecution:
        """Obtém status de uma execução."""
        response = await self._client.get(f"/api/v1/executions/{execution_id}")
        response.raise_for_status()
        result = response.json()
        
        status = ExecutionStatus.SUCCESS
        if result.get("status") == "error":
            status = ExecutionStatus.ERROR
        elif result.get("status") == "running":
            status = ExecutionStatus.RUNNING
        elif result.get("status") == "waiting":
            status = ExecutionStatus.WAITING
        
        return WorkflowExecution(
            execution_id=execution_id,
            status=status,
            data=result.get("data", {}),
            started_at=result.get("startedAt"),
            finished_at=result.get("stoppedAt"),
            error=result.get("data", {}).get("error", {}).get("message")
        )
    
    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
        limit: int = 50
    ) -> List[WorkflowExecution]:
        """Lista execuções."""
        params = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id
        if status:
            params["status"] = status.value
        
        response = await self._client.get("/api/v1/executions", params=params)
        response.raise_for_status()
        data = response.json()
        
        executions = []
        for ex in data.get("data", []):
            ex_status = ExecutionStatus.SUCCESS
            if ex.get("status") == "error":
                ex_status = ExecutionStatus.ERROR
            elif ex.get("status") == "running":
                ex_status = ExecutionStatus.RUNNING
            
            executions.append(WorkflowExecution(
                execution_id=ex["id"],
                status=ex_status,
                data={},
                started_at=ex.get("startedAt"),
                finished_at=ex.get("stoppedAt")
            ))
        
        return executions
    
    async def retry_execution(self, execution_id: str) -> WorkflowExecution:
        """Reexecuta uma execução que falhou."""
        response = await self._client.post(
            f"/api/v1/executions/{execution_id}/retry"
        )
        response.raise_for_status()
        result = response.json()
        
        return WorkflowExecution(
            execution_id=result.get("executionId", execution_id),
            status=ExecutionStatus.RUNNING,
            data={}
        )
    
    # ==================== Webhooks ====================
    
    async def trigger_webhook(
        self,
        webhook_path: str,
        data: Dict[str, Any],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Dispara um webhook do n8n.
        
        Args:
            webhook_path: Caminho do webhook (ex: "my-webhook" ou UUID)
            data: Dados a enviar
            method: Método HTTP (POST, GET)
            
        Returns:
            Resposta do webhook
        """
        # Webhooks usam URL diferente
        webhook_url = f"{self.config.api_url}/webhook/{webhook_path}"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            if method.upper() == "POST":
                response = await client.post(webhook_url, json=data)
            else:
                response = await client.get(webhook_url, params=data)
            
            response.raise_for_status()
            
            # Tentar parsear JSON, senão retornar texto
            try:
                return response.json()
            except Exception:
                return {"response": response.text}
    
    async def trigger_webhook_test(
        self,
        webhook_path: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispara webhook de teste."""
        webhook_url = f"{self.config.api_url}/webhook-test/{webhook_path}"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(webhook_url, json=data)
            response.raise_for_status()
            
            try:
                return response.json()
            except Exception:
                return {"response": response.text}


# ==================== Workflow Templates ====================

class N8nWorkflowBuilder:
    """
    Builder para criar workflows n8n programaticamente.
    
    Uso:
        builder = N8nWorkflowBuilder("Novo Lead")
        
        # Adicionar trigger de webhook
        builder.add_webhook_trigger("lead-webhook")
        
        # Adicionar ação de enviar email
        builder.add_email_node(
            to="{{ $json.email }}",
            subject="Bem-vindo!",
            body="Olá {{ $json.name }}!"
        )
        
        # Adicionar ação de WhatsApp
        builder.add_http_request_node(
            url="http://api.whatsapp.com/send",
            method="POST",
            body={"to": "{{ $json.phone }}", "message": "Olá!"}
        )
        
        # Exportar
        workflow_json = builder.build()
    """
    
    def __init__(self, name: str):
        self.name = name
        self.nodes = []
        self.connections = {}
        self._node_counter = 0
    
    def _add_node(
        self,
        type_name: str,
        name: str,
        parameters: Dict[str, Any],
        position: Optional[List[int]] = None
    ) -> str:
        """Adiciona um nó ao workflow."""
        self._node_counter += 1
        node_name = f"{name}_{self._node_counter}"
        
        if position is None:
            position = [250 * self._node_counter, 300]
        
        self.nodes.append({
            "parameters": parameters,
            "name": node_name,
            "type": type_name,
            "typeVersion": 1,
            "position": position
        })
        
        return node_name
    
    def add_webhook_trigger(
        self,
        path: str,
        method: str = "POST"
    ) -> str:
        """Adiciona trigger de webhook."""
        return self._add_node(
            "n8n-nodes-base.webhook",
            "Webhook",
            {
                "path": path,
                "httpMethod": method
            },
            [250, 300]
        )
    
    def add_schedule_trigger(
        self,
        cron: str = "0 * * * *"  # A cada hora
    ) -> str:
        """Adiciona trigger agendado."""
        return self._add_node(
            "n8n-nodes-base.scheduleTrigger",
            "Schedule",
            {"rule": {"interval": [{"field": "cronExpression", "expression": cron}]}},
            [250, 300]
        )
    
    def add_http_request_node(
        self,
        url: str,
        method: str = "POST",
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        previous_node: Optional[str] = None
    ) -> str:
        """Adiciona requisição HTTP."""
        params = {
            "url": url,
            "method": method
        }
        
        if body:
            params["sendBody"] = True
            params["bodyParameters"] = {
                "parameters": [
                    {"name": k, "value": v}
                    for k, v in body.items()
                ]
            }
        
        if headers:
            params["sendHeaders"] = True
            params["headerParameters"] = {
                "parameters": [
                    {"name": k, "value": v}
                    for k, v in headers.items()
                ]
            }
        
        node_name = self._add_node(
            "n8n-nodes-base.httpRequest",
            "HTTP_Request",
            params
        )
        
        if previous_node:
            self._connect(previous_node, node_name)
        
        return node_name
    
    def add_set_node(
        self,
        values: Dict[str, Any],
        previous_node: Optional[str] = None
    ) -> str:
        """Adiciona nó para definir valores."""
        node_name = self._add_node(
            "n8n-nodes-base.set",
            "Set",
            {
                "values": {
                    "string": [
                        {"name": k, "value": v}
                        for k, v in values.items()
                    ]
                }
            }
        )
        
        if previous_node:
            self._connect(previous_node, node_name)
        
        return node_name
    
    def add_if_node(
        self,
        condition_field: str,
        condition_value: str,
        operation: str = "equal",
        previous_node: Optional[str] = None
    ) -> str:
        """Adiciona nó condicional."""
        node_name = self._add_node(
            "n8n-nodes-base.if",
            "If",
            {
                "conditions": {
                    "string": [{
                        "value1": f"={{{{$json[\"{condition_field}\"]}}}}",
                        "operation": operation,
                        "value2": condition_value
                    }]
                }
            }
        )
        
        if previous_node:
            self._connect(previous_node, node_name)
        
        return node_name
    
    def add_code_node(
        self,
        code: str,
        previous_node: Optional[str] = None
    ) -> str:
        """Adiciona nó de código JavaScript."""
        node_name = self._add_node(
            "n8n-nodes-base.code",
            "Code",
            {
                "jsCode": code
            }
        )
        
        if previous_node:
            self._connect(previous_node, node_name)
        
        return node_name
    
    def _connect(self, from_node: str, to_node: str, output_index: int = 0):
        """Conecta dois nós."""
        if from_node not in self.connections:
            self.connections[from_node] = {"main": [[]]}
        
        while len(self.connections[from_node]["main"]) <= output_index:
            self.connections[from_node]["main"].append([])
        
        self.connections[from_node]["main"][output_index].append({
            "node": to_node,
            "type": "main",
            "index": 0
        })
    
    def connect(self, from_node: str, to_node: str, output_index: int = 0):
        """Conecta dois nós (public API)."""
        self._connect(from_node, to_node, output_index)
    
    def build(self) -> Dict[str, Any]:
        """Constrói o workflow JSON."""
        return {
            "name": self.name,
            "nodes": self.nodes,
            "connections": self.connections,
            "active": False,
            "settings": {}
        }
    
    def to_json(self) -> str:
        """Exporta como JSON string."""
        import json
        return json.dumps(self.build(), indent=2)


# ==================== Pre-built Workflows ====================

def create_lead_notification_workflow(
    webhook_path: str,
    whatsapp_api_url: str,
    notification_number: str
) -> Dict[str, Any]:
    """
    Cria workflow para notificar sobre novos leads.
    
    Quando receber dados no webhook, envia notificação WhatsApp.
    """
    builder = N8nWorkflowBuilder("Lead Notification")
    
    # Trigger
    webhook = builder.add_webhook_trigger(webhook_path)
    
    # Formatar mensagem
    format_code = """
const lead = $input.first().json;
return {
    json: {
        message: `🔔 Novo Lead!
        
Nome: ${lead.name || 'N/A'}
Email: ${lead.email || 'N/A'}
Telefone: ${lead.phone || 'N/A'}
Origem: ${lead.source || 'Website'}
`,
        to: '""" + notification_number + """'
    }
};
"""
    code_node = builder.add_code_node(format_code, webhook)
    
    # Enviar WhatsApp
    builder.add_http_request_node(
        url=f"{whatsapp_api_url}/message/sendText/tiktrend-facil",
        method="POST",
        body={
            "number": "={{ $json.to }}",
            "text": "={{ $json.message }}"
        },
        previous_node=code_node
    )
    
    return builder.build()


def create_price_alert_workflow(
    schedule_cron: str,
    api_base_url: str,
    whatsapp_api_url: str
) -> Dict[str, Any]:
    """
    Cria workflow para alertas de preço automáticos.
    
    Executa periodicamente e notifica sobre quedas de preço.
    """
    builder = N8nWorkflowBuilder("Price Alert")
    
    # Trigger agendado
    schedule = builder.add_schedule_trigger(schedule_cron)
    
    # Buscar alertas pendentes
    fetch = builder.add_http_request_node(
        url=f"{api_base_url}/api/v1/alerts/pending",
        method="GET",
        previous_node=schedule
    )
    
    # Loop e enviar notificações
    code = """
const alerts = $input.first().json;
const results = [];

for (const alert of alerts) {
    if (alert.current_price < alert.target_price) {
        results.push({
            json: {
                to: alert.user_phone,
                message: `🔔 Alerta de Preço!
                
${alert.product_name}
Preço atual: R$ ${alert.current_price}
Seu alvo: R$ ${alert.target_price}

Economize R$ ${(alert.target_price - alert.current_price).toFixed(2)}!
`
            }
        });
    }
}

return results;
"""
    
    process = builder.add_code_node(code, fetch)
    
    # Enviar notificações
    builder.add_http_request_node(
        url=f"{whatsapp_api_url}/message/sendText/tiktrend-facil",
        method="POST",
        body={
            "number": "={{ $json.to }}",
            "text": "={{ $json.message }}"
        },
        previous_node=process
    )
    
    return builder.build()
