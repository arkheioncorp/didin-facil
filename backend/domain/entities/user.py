"""
User Entity
===========

Entidade de usuário com regras de negócio relacionadas a autenticação,
licenciamento e créditos.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from domain.value_objects import Email


@dataclass
class User:
    """
    Entidade User - representa um usuário do sistema.
    
    Invariantes:
    - Email deve ser válido
    - Plano deve ser um dos valores permitidos
    - Créditos não podem ser negativos
    """
    
    id: UUID
    email: Email
    name: str
    password_hash: str
    plan: str = "free"
    is_active: bool = True
    is_admin: bool = False
    credits_balance: int = 0
    credits_purchased: int = 0
    credits_used: int = 0
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: Optional[datetime] = None
    
    # Planos válidos
    VALID_PLANS = ("free", "starter", "professional", "enterprise")
    
    def __post_init__(self):
        """Validar invariantes após criação."""
        if self.plan not in self.VALID_PLANS:
            raise ValueError(f"Invalid plan: {self.plan}")
        if self.credits_balance < 0:
            raise ValueError("Credits balance cannot be negative")
    
    @classmethod
    def create(
        cls,
        email: Email,
        name: str,
        password_hash: str,
        plan: str = "free",
    ) -> "User":
        """Factory method para criar novo usuário."""
        return cls(
            id=uuid4(),
            email=email,
            name=name,
            password_hash=password_hash,
            plan=plan,
            credits_balance=10 if plan == "free" else 0,  # Trial credits
        )
    
    def use_credits(self, amount: int) -> bool:
        """
        Usar créditos do usuário.
        
        Returns:
            True se créditos foram usados, False se saldo insuficiente.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if self.credits_balance < amount:
            return False
        
        self.credits_balance -= amount
        self.credits_used += amount
        self._touch()
        return True
    
    def add_credits(self, amount: int, is_purchase: bool = True) -> None:
        """Adicionar créditos ao usuário."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        self.credits_balance += amount
        if is_purchase:
            self.credits_purchased += amount
        self._touch()
    
    def upgrade_plan(self, new_plan: str) -> None:
        """Fazer upgrade do plano."""
        if new_plan not in self.VALID_PLANS:
            raise ValueError(f"Invalid plan: {new_plan}")
        
        plan_order = {p: i for i, p in enumerate(self.VALID_PLANS)}
        if plan_order[new_plan] <= plan_order[self.plan]:
            raise ValueError("Can only upgrade to a higher plan")
        
        self.plan = new_plan
        self._touch()
    
    def deactivate(self) -> None:
        """Desativar usuário."""
        self.is_active = False
        self._touch()
    
    def reactivate(self) -> None:
        """Reativar usuário."""
        self.is_active = True
        self._touch()
    
    def _touch(self) -> None:
        """Atualizar timestamp de modificação."""
        self.updated_at = datetime.now(timezone.utc)
    
    @property
    def has_credits(self) -> bool:
        """Verificar se usuário tem créditos disponíveis."""
        return self.credits_balance > 0
    
    @property
    def is_premium(self) -> bool:
        """Verificar se usuário tem plano premium."""
        return self.plan in ("professional", "enterprise")
