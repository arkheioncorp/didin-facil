# ============================================
# Analytics Task - Extração de Dados e Métricas
# ============================================

from datetime import date, timedelta
from typing import Optional
from pydantic import BaseModel, Field


class DateRange(BaseModel):
    """Período para análise"""
    start_date: date = Field(default_factory=lambda: date.today() - timedelta(days=30))
    end_date: date = Field(default_factory=date.today)


class AnalyticsResult(BaseModel):
    """Resultado da extração de analytics"""
    
    # Visão geral
    total_revenue: Optional[float] = None
    total_orders: Optional[int] = None
    total_visitors: Optional[int] = None
    conversion_rate: Optional[float] = None
    
    # Top produtos
    top_products: Optional[list[dict]] = None
    
    # Pedidos por status
    orders_by_status: Optional[dict[str, int]] = None
    
    # Dados brutos extraídos
    raw_data: Optional[dict] = None


class AnalyticsTask:
    """
    Tarefa para extrair dados e métricas do TikTok Seller Center.
    
    Fluxos:
    - Extrair resumo de vendas
    - Listar produtos mais vendidos
    - Obter métricas de tráfego
    - Exportar relatórios
    """
    
    TASK_TYPE = "analytics"
    
    @staticmethod
    def build_extract_overview_prompt(date_range: Optional[DateRange] = None) -> str:
        """Prompt para extrair visão geral de vendas"""
        
        date_range = date_range or DateRange()
        
        return f"""
Você está na Central do Vendedor do TikTok Shop.
Sua tarefa é extrair as métricas de vendas do período especificado.

PERÍODO: {date_range.start_date.strftime('%d/%m/%Y')} até {date_range.end_date.strftime('%d/%m/%Y')}

INSTRUÇÕES:
1. Vá para "Página inicial" (Dashboard)
2. Se necessário, ajuste o período no seletor de datas
3. Extraia as seguintes informações:
   - Receita total (R$)
   - Número de pedidos
   - Número de visitantes
   - Taxa de conversão (%)
   - Ticket médio (R$)
4. Se houver gráficos, descreva a tendência (subindo, caindo, estável)

FORMATO DE RETORNO (JSON):
{{
    "total_revenue": [valor em R$],
    "total_orders": [número],
    "total_visitors": [número],
    "conversion_rate": [percentual],
    "average_ticket": [valor em R$],
    "trend": "[subindo/caindo/estável]"
}}

IMPORTANTE:
- Se algum dado não estiver disponível, retorne null
- Certifique-se de que o período está correto antes de extrair
"""
    
    @staticmethod
    def build_top_products_prompt(limit: int = 10) -> str:
        """Prompt para listar produtos mais vendidos"""
        
        return f"""
Você está na Central do Vendedor do TikTok Shop.
Sua tarefa é listar os {limit} produtos mais vendidos.

INSTRUÇÕES:
1. Vá para "Produtos" > "Gerenciar produtos"
2. Ou acesse a seção de "Bússola de dados" se disponível
3. Ordene por "Mais vendidos" ou "Vendas"
4. Para os primeiros {limit} produtos, extraia:
   - Nome do produto
   - Quantidade vendida
   - Receita gerada
   - Estoque atual

FORMATO DE RETORNO (JSON):
{{
    "top_products": [
        {{
            "name": "[nome]",
            "sold": [quantidade],
            "revenue": [R$],
            "stock": [estoque]
        }}
    ]
}}
"""
    
    @staticmethod
    def build_orders_summary_prompt() -> str:
        """Prompt para resumo de pedidos por status"""
        
        return """
Você está na Central do Vendedor do TikTok Shop.
Sua tarefa é extrair o resumo de pedidos por status.

INSTRUÇÕES:
1. Vá para "Pedidos" > "Gerenciar pedidos"
2. Observe os contadores em cada aba:
   - Todos
   - Para enviar
   - Enviado
   - Concluído
   - Cancelado
   - Pendente
3. Extraia também da seção "Ação necessária":
   - Envio em 24 horas ou menos
   - Cancelamento automático em 24 horas ou menos
   - Envio atrasado
   - Cancelamento solicitado
   - Devolução/reembolso solicitado

FORMATO DE RETORNO (JSON):
{
    "orders_by_status": {
        "all": [número],
        "to_ship": [número],
        "shipped": [número],
        "completed": [número],
        "cancelled": [número],
        "pending": [número]
    },
    "action_required": {
        "ship_24h": [número],
        "auto_cancel_24h": [número],
        "delayed": [número],
        "cancel_requested": [número],
        "refund_requested": [número]
    }
}
"""
    
    @staticmethod
    def build_financial_report_prompt(date_range: Optional[DateRange] = None) -> str:
        """Prompt para extrair relatório financeiro"""
        
        date_range = date_range or DateRange()
        
        return f"""
Você está na Central do Vendedor do TikTok Shop.
Sua tarefa é extrair o relatório financeiro.

PERÍODO: {date_range.start_date.strftime('%d/%m/%Y')} até {date_range.end_date.strftime('%d/%m/%Y')}

INSTRUÇÕES:
1. No menu lateral, clique em "Finanças"
2. Ajuste o período se necessário
3. Extraia:
   - Saldo disponível
   - Vendas totais
   - Taxas da plataforma
   - Valor líquido
   - Próximo repasse (data e valor)
4. Se possível, exporte o relatório detalhado

FORMATO DE RETORNO (JSON):
{{
    "available_balance": [R$],
    "total_sales": [R$],
    "platform_fees": [R$],
    "net_amount": [R$],
    "next_payout": {{
        "date": "[data]",
        "amount": [R$]
    }}
}}
"""
    
    @staticmethod
    def build_competitor_analysis_prompt(product_name: str) -> str:
        """Prompt para análise de concorrência"""
        
        return f"""
Você está no TikTok Shop (não na Central do Vendedor).
Sua tarefa é analisar a concorrência para o produto: "{product_name}"

INSTRUÇÕES:
1. Abra uma nova aba e vá para shop.tiktok.com
2. Pesquise por "{product_name}"
3. Para os 5 primeiros resultados, extraia:
   - Nome do vendedor
   - Título do produto
   - Preço
   - Quantidade vendida (se visível)
   - Avaliação
4. Identifique o preço mais baixo e mais alto

FORMATO DE RETORNO (JSON):
{{
    "search_term": "{product_name}",
    "competitors": [
        {{
            "seller": "[nome]",
            "product_title": "[título]",
            "price": [R$],
            "sold": [quantidade ou null],
            "rating": [nota]
        }}
    ],
    "price_range": {{
        "min": [R$],
        "max": [R$],
        "average": [R$]
    }}
}}

IMPORTANTE:
- Esta análise é para referência de mercado
- Volte para a Central do Vendedor após concluir
"""
