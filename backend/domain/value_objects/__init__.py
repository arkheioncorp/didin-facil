"""
Value Objects
=============

Value Objects são objetos imutáveis identificados pelo seu valor,
não por identidade. Eles encapsulam validação e comportamento
relacionado a conceitos de domínio.

Value Objects planejados:
- Money: Representação de valores monetários
- Email: Email validado
- DeviceId: Identificador de dispositivo (HWID)
- PhoneNumber: Número de telefone validado
"""

from .device_id import DeviceId
from .email import Email
from .money import Money

__all__ = ["Money", "Email", "DeviceId"]
