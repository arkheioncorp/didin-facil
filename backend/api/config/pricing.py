"""
Pricing Configuration - Single Source of Truth
==============================================
Toda configuração de preços, pacotes e custos em um único lugar.

Modelo de Negócio:
- Usuário compra créditos
- Créditos são consumidos por operações (Copy IA, Análises, etc.)
- Não existe mais "licença" separada - app é gratuito, cobra-se créditos
- Primeiro pacote = ativação do usuário

Referência de Custos:
- OpenAI GPT-4-turbo: ~$0.01/1K input, ~$0.03/1K output
- Custo médio por copy: ~R$ 0.08
- Margem alvo: 60-70%
"""

from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OperationType(str, Enum):
    """Tipos de operações que consomem créditos"""
    COPY_SIMPLE = "copy_simple"           # Copy única de produto
    COPY_BATCH = "copy_batch"             # Lote de copies
    TREND_ANALYSIS = "trend_analysis"     # Análise de tendência
    NICHE_REPORT = "niche_report"         # Relatório de nicho
    PRODUCT_ANALYSIS = "product_analysis" # Análise detalhada de produto
    AI_CHAT = "ai_chat"                   # Chat com IA
    IMAGE_CAPTION = "image_caption"       # Legenda para imagem


# =============================================================================
# CUSTOS DE OPERAÇÃO (nosso custo real)
# =============================================================================

@dataclass
class OperationCost:
    """Custo interno de cada operação"""
    credits_charged: int       # Créditos cobrados do usuário
    openai_cost_brl: Decimal   # Custo OpenAI em BRL
    other_costs_brl: Decimal   # Proxy, infra, etc.
    
    @property
    def total_cost(self) -> Decimal:
        return self.openai_cost_brl + self.other_costs_brl
    
    @property
    def revenue_per_operation(self) -> Decimal:
        """Receita por operação (baseado em R$ 0.10/crédito médio)"""
        return Decimal(str(self.credits_charged)) * Decimal("0.10")
    
    @property
    def margin_percent(self) -> float:
        """Margem de lucro em %"""
        if self.total_cost == 0:
            return 100.0
        revenue = self.revenue_per_operation
        profit = revenue - self.total_cost
        return float((profit / revenue) * 100)


OPERATION_COSTS = {
    OperationType.COPY_SIMPLE: OperationCost(
        credits_charged=1,
        openai_cost_brl=Decimal("0.04"),   # ~500 tokens
        other_costs_brl=Decimal("0.01"),
    ),
    OperationType.COPY_BATCH: OperationCost(
        credits_charged=5,
        openai_cost_brl=Decimal("0.15"),   # ~5 copies
        other_costs_brl=Decimal("0.03"),
    ),
    OperationType.TREND_ANALYSIS: OperationCost(
        credits_charged=2,
        openai_cost_brl=Decimal("0.08"),   # ~1000 tokens
        other_costs_brl=Decimal("0.02"),
    ),
    OperationType.NICHE_REPORT: OperationCost(
        credits_charged=5,
        openai_cost_brl=Decimal("0.20"),   # ~2500 tokens
        other_costs_brl=Decimal("0.05"),
    ),
    OperationType.PRODUCT_ANALYSIS: OperationCost(
        credits_charged=3,
        openai_cost_brl=Decimal("0.12"),   # ~1500 tokens
        other_costs_brl=Decimal("0.03"),
    ),
    OperationType.AI_CHAT: OperationCost(
        credits_charged=1,
        openai_cost_brl=Decimal("0.05"),   # ~600 tokens avg
        other_costs_brl=Decimal("0.01"),
    ),
    OperationType.IMAGE_CAPTION: OperationCost(
        credits_charged=1,
        openai_cost_brl=Decimal("0.03"),   # GPT-4 vision
        other_costs_brl=Decimal("0.01"),
    ),
}


# =============================================================================
# PACOTES DE CRÉDITOS
# =============================================================================

@dataclass
class CreditPackage:
    """Pacote de créditos para venda"""
    slug: str
    name: str
    credits: int
    price_brl: Decimal
    original_price: Optional[Decimal] = None
    badge: Optional[str] = None
    description: Optional[str] = None
    is_featured: bool = False
    sort_order: int = 0
    
    @property
    def price_per_credit(self) -> Decimal:
        return self.price_brl / self.credits
    
    @property
    def discount_percent(self) -> int:
        if self.original_price and self.original_price > self.price_brl:
            discount = (self.original_price - self.price_brl) / self.original_price
            return int(discount * 100)
        return 0
    
    @property
    def savings(self) -> Optional[Decimal]:
        if self.original_price:
            return self.original_price - self.price_brl
        return None


# Pacotes oficiais - SINGLE SOURCE OF TRUTH
CREDIT_PACKAGES = {
    "starter": CreditPackage(
        slug="starter",
        name="Iniciante",
        credits=50,
        price_brl=Decimal("9.90"),
        description="Ideal para testar",
        sort_order=1,
    ),
    "basic": CreditPackage(
        slug="basic",
        name="Básico",
        credits=100,
        price_brl=Decimal("17.90"),
        original_price=Decimal("19.90"),
        description="Para uso ocasional",
        sort_order=2,
    ),
    "popular": CreditPackage(
        slug="popular",
        name="Popular",
        credits=250,
        price_brl=Decimal("39.90"),
        original_price=Decimal("49.90"),
        badge="Mais Vendido",
        description="Melhor custo-benefício",
        is_featured=True,
        sort_order=3,
    ),
    "pro": CreditPackage(
        slug="pro",
        name="Profissional",
        credits=500,
        price_brl=Decimal("69.90"),
        original_price=Decimal("99.90"),
        badge="30% OFF",
        description="Para vendedores ativos",
        sort_order=4,
    ),
    "enterprise": CreditPackage(
        slug="enterprise",
        name="Enterprise",
        credits=1500,
        price_brl=Decimal("149.90"),
        original_price=Decimal("299.90"),
        badge="50% OFF",
        description="Para operações de escala",
        sort_order=5,
    ),
}


# =============================================================================
# BÔNUS E PROMOÇÕES
# =============================================================================

# Bônus de primeiro acesso
FIRST_PURCHASE_BONUS = {
    "starter": 10,    # +10 créditos grátis
    "basic": 20,      # +20 créditos grátis
    "popular": 50,    # +50 créditos grátis
    "pro": 100,       # +100 créditos grátis
    "enterprise": 300, # +300 créditos grátis
}

# Cupons ativos
ACTIVE_COUPONS = {
    "BEMVINDO": {
        "discount_percent": 10,
        "first_purchase_only": True,
        "expires": "2025-12-31",
    },
    "LANCAMENTO": {
        "discount_percent": 15,
        "first_purchase_only": False,
        "expires": "2025-02-28",
    },
}

# Desconto PIX
PIX_DISCOUNT_PERCENT = 5


# =============================================================================
# ANÁLISE DE MARGEM
# =============================================================================

def print_margin_analysis():
    """Imprime análise de margem para cada pacote"""
    print("\n" + "=" * 70)
    print("ANÁLISE DE MARGEM POR PACOTE")
    print("=" * 70)
    
    # Custo médio ponderado por crédito
    avg_cost_per_credit = Decimal("0.06")  # R$ 0.06 custo médio
    
    for slug, pkg in CREDIT_PACKAGES.items():
        cost = avg_cost_per_credit * pkg.credits
        revenue = pkg.price_brl
        profit = revenue - cost
        margin = (profit / revenue) * 100
        
        print(f"\n{pkg.name} ({pkg.credits} créditos)")
        print(f"  Preço: R$ {pkg.price_brl:.2f}")
        print(f"  Custo: R$ {cost:.2f}")
        print(f"  Lucro: R$ {profit:.2f}")
        print(f"  Margem: {margin:.1f}%")
        print(f"  Por crédito: R$ {pkg.price_per_credit:.3f}")


def print_operation_costs():
    """Imprime custos por operação"""
    print("\n" + "=" * 70)
    print("CUSTO POR OPERAÇÃO")
    print("=" * 70)
    
    for op_type, cost in OPERATION_COSTS.items():
        print(f"\n{op_type.value}")
        print(f"  Créditos: {cost.credits_charged}")
        print(f"  Custo OpenAI: R$ {cost.openai_cost_brl:.3f}")
        print(f"  Outros custos: R$ {cost.other_costs_brl:.3f}")
        print(f"  Custo total: R$ {cost.total_cost:.3f}")
        print(f"  Receita: R$ {cost.revenue_per_operation:.3f}")
        print(f"  Margem: {cost.margin_percent:.1f}%")


if __name__ == "__main__":
    print_margin_analysis()
    print_operation_costs()
