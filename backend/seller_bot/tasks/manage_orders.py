# ============================================
# Manage Orders Task - Gestão de Pedidos
# ============================================

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class OrderAction(str, Enum):
    """Ações disponíveis para pedidos"""
    PRINT_LABEL = "print_label"           # Imprimir etiqueta
    MARK_SHIPPED = "mark_shipped"          # Marcar como enviado
    CANCEL_ORDER = "cancel_order"          # Cancelar pedido
    APPROVE_REFUND = "approve_refund"      # Aprovar reembolso
    EXPORT_ORDERS = "export_orders"        # Exportar lista de pedidos


class OrderFilter(BaseModel):
    """Filtros para seleção de pedidos"""
    status: Optional[str] = Field(None, description="Status: to_ship, shipped, completed, cancelled")
    date_from: Optional[str] = Field(None, description="Data inicial (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Data final (YYYY-MM-DD)")
    order_ids: Optional[list[str]] = Field(None, description="IDs específicos de pedidos")


class ManageOrdersTask:
    """
    Tarefa para gerenciar pedidos no TikTok Shop.
    
    Fluxos disponíveis:
    - Imprimir etiquetas de envio
    - Marcar pedidos como enviados
    - Processar devoluções/reembolsos
    - Exportar lista de pedidos
    """
    
    TASK_TYPE = "manage_orders"
    
    @staticmethod
    def build_print_labels_prompt(filters: Optional[OrderFilter] = None) -> str:
        """Prompt para imprimir etiquetas de todos os pedidos pendentes"""
        
        filter_text = ""
        if filters:
            if filters.status:
                filter_text += f"- Filtrar por status: {filters.status}\n"
            if filters.date_from:
                filter_text += f"- A partir de: {filters.date_from}\n"
            if filters.order_ids:
                filter_text += f"- Pedidos específicos: {', '.join(filters.order_ids)}\n"
        
        return f"""
Você está na Central do Vendedor do TikTok Shop.
Sua tarefa é imprimir as etiquetas de envio dos pedidos pendentes.

{f"FILTROS:{chr(10)}{filter_text}" if filter_text else ""}

INSTRUÇÕES:
1. No menu lateral, clique em "Pedidos" > "Gerenciar pedidos"
2. Clique na aba "Para enviar"
3. Se houver pedidos aguardando envio:
   a. Selecione todos os pedidos (checkbox "Selecionar todos")
   b. Clique em "Etiquetas de envio" ou "Imprimir etiqueta"
   c. Aguarde o PDF ser gerado
   d. Salve o arquivo PDF
4. Se não houver pedidos, informe "Nenhum pedido pendente"

IMPORTANTE:
- Conte quantos pedidos foram processados
- Se houver erro em algum pedido, anote e continue com os outros
- Retorne o caminho do arquivo PDF salvo
"""
    
    @staticmethod
    def build_mark_shipped_prompt(order_ids: list[str], tracking_codes: Optional[dict[str, str]] = None) -> str:
        """Prompt para marcar pedidos como enviados"""
        
        tracking_text = ""
        if tracking_codes:
            tracking_text = "\nCÓDIGOS DE RASTREIO:\n"
            for order_id, code in tracking_codes.items():
                tracking_text += f"- Pedido {order_id}: {code}\n"
        
        return f"""
Você está na Central do Vendedor do TikTok Shop.
Sua tarefa é marcar os seguintes pedidos como enviados:

PEDIDOS: {', '.join(order_ids)}
{tracking_text}

INSTRUÇÕES:
1. No menu lateral, clique em "Pedidos" > "Gerenciar pedidos"
2. Para cada pedido listado:
   a. Busque pelo ID do pedido no campo de pesquisa
   b. Clique no pedido para abrir detalhes
   c. Clique em "Marcar como enviado"
   d. Se houver código de rastreio, preencha-o
   e. Confirme a ação
3. Verifique se o status mudou para "Enviado"

IMPORTANTE:
- Confirme cada pedido individualmente
- Se algum pedido já estiver enviado, pule para o próximo
"""
    
    @staticmethod
    def build_export_orders_prompt(filters: Optional[OrderFilter] = None) -> str:
        """Prompt para exportar lista de pedidos"""
        
        return """
Você está na Central do Vendedor do TikTok Shop.
Sua tarefa é exportar a lista de pedidos para Excel/CSV.

INSTRUÇÕES:
1. No menu lateral, clique em "Pedidos" > "Gerenciar pedidos"
2. Aplique os filtros desejados (se houver)
3. Clique no botão "Exportar" (ícone de download ou texto)
4. Selecione o formato de exportação (Excel ou CSV)
5. Aguarde o download ser concluído
6. Informe o caminho do arquivo baixado

IMPORTANTE:
- O arquivo será salvo na pasta de Downloads padrão
- Verifique se o download foi concluído antes de finalizar
"""
    
    @staticmethod
    def build_process_returns_prompt() -> str:
        """Prompt para processar devoluções/reembolsos pendentes"""
        
        return """
Você está na Central do Vendedor do TikTok Shop.
Sua tarefa é processar as devoluções e reembolsos pendentes.

INSTRUÇÕES:
1. No menu lateral, clique em "Pedidos" > "Gerenciar devoluções"
2. Na aba "Aguardando sua ação", verifique se há itens pendentes
3. Para cada devolução/reembolso pendente:
   a. Clique para abrir os detalhes
   b. Analise o motivo da devolução
   c. Se for válido, clique em "Aprovar"
   d. Se não for válido, clique em "Recorrer" com justificativa
4. Registre quantas devoluções foram processadas

IMPORTANTE:
- Leia o motivo antes de aprovar
- Anote os pedidos que precisam de atenção especial
- Se a lista estiver vazia, informe "Nenhuma devolução pendente"
"""
