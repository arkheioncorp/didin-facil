"""
DeviceId Value Object
=====================

Representa um identificador único de dispositivo (HWID) para binding de licenças.
"""

import hashlib
import re
from dataclasses import dataclass

# Regex para validação de HWID (hex string)
HWID_REGEX = re.compile(r"^[a-fA-F0-9]{32,64}$")


@dataclass(frozen=True)
class DeviceId:
    """
    Value Object para representação de ID de dispositivo.
    
    Usado para vincular licenças a dispositivos específicos.
    
    Exemplo:
        device = DeviceId.from_components("CPU123", "MB456", "DISK789")
        print(device.value)  # hash hex
        print(device.short)  # primeiros 8 caracteres
    """
    
    value: str
    
    def __post_init__(self):
        """Validar HWID após criação."""
        if not self.value:
            raise ValueError("DeviceId cannot be empty")
        
        normalized = self.value.lower().strip()
        object.__setattr__(self, "value", normalized)
        
        if not HWID_REGEX.match(normalized):
            raise ValueError(f"Invalid DeviceId format: {self.value}")
    
    @classmethod
    def from_components(cls, *components: str) -> "DeviceId":
        """
        Criar DeviceId a partir de componentes de hardware.
        
        Args:
            components: Identificadores de hardware (CPU, MB, etc.)
        
        Returns:
            DeviceId gerado via hash dos componentes
        """
        combined = "|".join(str(c) for c in components if c)
        if not combined:
            raise ValueError("At least one component is required")
        
        # Gerar hash SHA256 dos componentes
        hash_value = hashlib.sha256(combined.encode()).hexdigest()
        return cls(hash_value)
    
    @classmethod
    def from_machine_id(cls, machine_id: str) -> "DeviceId":
        """
        Criar DeviceId a partir de machine-id do sistema.
        
        Args:
            machine_id: ID único da máquina (ex: /etc/machine-id no Linux)
        
        Returns:
            DeviceId normalizado
        """
        # Remover hífens e normalizar
        normalized = machine_id.replace("-", "").lower().strip()
        
        if len(normalized) < 32:
            # Se muito curto, fazer hash para garantir tamanho
            normalized = hashlib.md5(normalized.encode()).hexdigest()
        
        return cls(normalized[:64])
    
    @property
    def short(self) -> str:
        """Retornar versão curta do DeviceId (primeiros 8 chars)."""
        return self.value[:8]
    
    @property
    def display(self) -> str:
        """Retornar versão formatada para exibição."""
        return f"{self.value[:8]}...{self.value[-8:]}"
    
    def matches(self, other: "DeviceId") -> bool:
        """
        Verificar se este DeviceId corresponde a outro.
        
        Args:
            other: Outro DeviceId para comparar
        
        Returns:
            True se são iguais
        """
        return self.value == other.value
    
    def __str__(self) -> str:
        """Representação string."""
        return self.value
    
    def __repr__(self) -> str:
        """Representação para debug."""
        return f"DeviceId('{self.short}...')"
    
    def __eq__(self, other: object) -> bool:
        """Comparar DeviceIds."""
        if isinstance(other, DeviceId):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.lower().strip()
        return False
    
    def __hash__(self) -> int:
        """Hash para uso em sets e dicts."""
        return hash(self.value)
