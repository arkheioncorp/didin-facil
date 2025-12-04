"""
Money Value Object
==================

Representa valores monetários com precisão decimal
e suporte a múltiplas moedas.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Union


@dataclass(frozen=True)
class Money:
    """
    Value Object para representação de valores monetários.
    
    Imutável e com suporte a operações aritméticas.
    
    Exemplo:
        price = Money(Decimal("49.90"), "BRL")
        discounted = price.apply_discount(Decimal("10"))  # 10% off
        print(discounted.format())  # "R$ 44,91"
    """
    
    amount: Decimal
    currency: str = "BRL"
    
    def __post_init__(self):
        """Validar valor após criação."""
        if not isinstance(self.amount, Decimal):
            # Converter para Decimal se necessário
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
        
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        
        if len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
    
    @classmethod
    def from_float(cls, amount: float, currency: str = "BRL") -> "Money":
        """Criar Money a partir de float."""
        return cls(Decimal(str(amount)), currency)
    
    @classmethod
    def from_cents(cls, cents: int, currency: str = "BRL") -> "Money":
        """Criar Money a partir de centavos."""
        return cls(Decimal(cents) / 100, currency)
    
    @classmethod
    def zero(cls, currency: str = "BRL") -> "Money":
        """Criar Money com valor zero."""
        return cls(Decimal("0"), currency)
    
    def __add__(self, other: "Money") -> "Money":
        """Somar dois valores monetários."""
        self._check_same_currency(other)
        return Money(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: "Money") -> "Money":
        """Subtrair dois valores monetários."""
        self._check_same_currency(other)
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Result cannot be negative")
        return Money(result, self.currency)
    
    def __mul__(self, factor: Union[int, float, Decimal]) -> "Money":
        """Multiplicar valor por um fator."""
        if isinstance(factor, float):
            factor = Decimal(str(factor))
        result = self.amount * Decimal(factor)
        return Money(result.quantize(Decimal("0.01"), ROUND_HALF_UP), self.currency)
    
    def __truediv__(self, divisor: Union[int, float, Decimal]) -> "Money":
        """Dividir valor por um divisor."""
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        if isinstance(divisor, float):
            divisor = Decimal(str(divisor))
        result = self.amount / Decimal(divisor)
        return Money(result.quantize(Decimal("0.01"), ROUND_HALF_UP), self.currency)
    
    def __lt__(self, other: "Money") -> bool:
        """Comparar se menor que."""
        self._check_same_currency(other)
        return self.amount < other.amount
    
    def __le__(self, other: "Money") -> bool:
        """Comparar se menor ou igual."""
        self._check_same_currency(other)
        return self.amount <= other.amount
    
    def __gt__(self, other: "Money") -> bool:
        """Comparar se maior que."""
        self._check_same_currency(other)
        return self.amount > other.amount
    
    def __ge__(self, other: "Money") -> bool:
        """Comparar se maior ou igual."""
        self._check_same_currency(other)
        return self.amount >= other.amount
    
    def _check_same_currency(self, other: "Money") -> None:
        """Verificar se moedas são iguais."""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot operate on different currencies: {self.currency} vs {other.currency}"
            )
    
    def apply_discount(self, percentage: Decimal) -> "Money":
        """
        Aplicar desconto percentual.
        
        Args:
            percentage: Porcentagem de desconto (0-100)
        
        Returns:
            Novo Money com desconto aplicado
        """
        if not (0 <= percentage <= 100):
            raise ValueError("Percentage must be between 0 and 100")
        
        discount = self.amount * (percentage / 100)
        new_amount = self.amount - discount
        return Money(new_amount.quantize(Decimal("0.01"), ROUND_HALF_UP), self.currency)
    
    def to_cents(self) -> int:
        """Converter para centavos (inteiro)."""
        return int(self.amount * 100)
    
    def format(self, locale: str = "pt_BR") -> str:
        """
        Formatar valor para exibição.
        
        Args:
            locale: Localização para formatação
        
        Returns:
            String formatada (ex: "R$ 49,90")
        """
        currency_symbols = {
            "BRL": "R$",
            "USD": "$",
            "EUR": "€",
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        
        if locale.startswith("pt"):
            # Formato brasileiro: R$ 1.234,56
            formatted = f"{self.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            # Formato americano: R$ 1,234.56
            formatted = f"{self.amount:,.2f}"
        
        return f"{symbol} {formatted}"
    
    def __str__(self) -> str:
        """Representação string."""
        return self.format()
    
    def __repr__(self) -> str:
        """Representação para debug."""
        return f"Money({self.amount}, '{self.currency}')"
