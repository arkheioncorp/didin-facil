"""
Email Value Object
==================

Representa um endereço de email validado.
"""

import re
from dataclasses import dataclass

# Regex para validação de email (RFC 5322 simplificado)
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


@dataclass(frozen=True)
class Email:
    """
    Value Object para representação de email validado.
    
    Imutável e sempre válido após criação.
    
    Exemplo:
        email = Email("user@example.com")
        print(email.domain)  # "example.com"
        print(email.local_part)  # "user"
    """
    
    value: str
    
    def __post_init__(self):
        """Validar email após criação."""
        if not self.value:
            raise ValueError("Email cannot be empty")
        
        normalized = self.value.lower().strip()
        object.__setattr__(self, "value", normalized)
        
        if not EMAIL_REGEX.match(normalized):
            raise ValueError(f"Invalid email format: {self.value}")
        
        if len(normalized) > 254:
            raise ValueError("Email too long (max 254 characters)")
    
    @property
    def domain(self) -> str:
        """Retornar domínio do email."""
        return self.value.split("@")[1]
    
    @property
    def local_part(self) -> str:
        """Retornar parte local do email (antes do @)."""
        return self.value.split("@")[0]
    
    def is_corporate(self) -> bool:
        """
        Verificar se email é corporativo (não é de provedor gratuito).
        
        Returns:
            True se não for de provedor gratuito comum
        """
        free_providers = {
            "gmail.com", "googlemail.com",
            "outlook.com", "hotmail.com", "live.com", "msn.com",
            "yahoo.com", "yahoo.com.br",
            "icloud.com", "me.com", "mac.com",
            "protonmail.com", "proton.me",
            "aol.com",
            "uol.com.br", "bol.com.br",
            "terra.com.br",
            "ig.com.br",
        }
        return self.domain not in free_providers
    
    def obfuscate(self) -> str:
        """
        Retornar versão ofuscada do email para exibição.
        
        Exemplo: "u***r@example.com"
        """
        local = self.local_part
        if len(local) <= 2:
            masked = local[0] + "***"
        else:
            masked = local[0] + "***" + local[-1]
        return f"{masked}@{self.domain}"
    
    def __str__(self) -> str:
        """Representação string."""
        return self.value
    
    def __repr__(self) -> str:
        """Representação para debug."""
        return f"Email('{self.value}')"
    
    def __eq__(self, other: object) -> bool:
        """Comparar emails (case-insensitive)."""
        if isinstance(other, Email):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.lower().strip()
        return False
    
    def __hash__(self) -> int:
        """Hash para uso em sets e dicts."""
        return hash(self.value)
