"""
Domain Exceptions
=================

Exceções específicas do domínio para comunicar erros de negócio.
"""


class DomainError(Exception):
    """Exceção base para erros de domínio."""
    
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(DomainError):
    """Erro de validação de dados."""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class NotFoundError(DomainError):
    """Entidade não encontrada."""
    
    def __init__(self, entity: str, identifier: str):
        self.entity = entity
        self.identifier = identifier
        super().__init__(
            f"{entity} with id '{identifier}' not found",
            "NOT_FOUND"
        )


class AlreadyExistsError(DomainError):
    """Entidade já existe."""
    
    def __init__(self, entity: str, field: str, value: str):
        self.entity = entity
        self.field = field
        self.value = value
        super().__init__(
            f"{entity} with {field} '{value}' already exists",
            "ALREADY_EXISTS"
        )


class UnauthorizedError(DomainError):
    """Acesso não autorizado."""
    
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message, "UNAUTHORIZED")


class ForbiddenError(DomainError):
    """Acesso proibido."""
    
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, "FORBIDDEN")


class InsufficientCreditsError(DomainError):
    """Créditos insuficientes."""
    
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient credits: required {required}, available {available}",
            "INSUFFICIENT_CREDITS"
        )


class DeviceNotAuthorizedError(DomainError):
    """Dispositivo não autorizado."""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        super().__init__(
            f"Device '{device_id[:8]}...' is not authorized for this license",
            "DEVICE_NOT_AUTHORIZED"
        )


class LicenseExpiredError(DomainError):
    """Licença expirada."""
    
    def __init__(self, expired_at: str):
        self.expired_at = expired_at
        super().__init__(
            f"License expired at {expired_at}",
            "LICENSE_EXPIRED"
        )


class QuotaExceededError(DomainError):
    """Quota excedida."""
    
    def __init__(self, resource: str, limit: int, current: int):
        self.resource = resource
        self.limit = limit
        self.current = current
        super().__init__(
            f"Quota exceeded for {resource}: limit {limit}, current {current}",
            "QUOTA_EXCEEDED"
        )


class RateLimitError(DomainError):
    """Rate limit atingido."""
    
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after} seconds",
            "RATE_LIMIT"
        )


class ExternalServiceError(DomainError):
    """Erro em serviço externo."""
    
    def __init__(self, service: str, message: str):
        self.service = service
        super().__init__(
            f"Error in external service '{service}': {message}",
            "EXTERNAL_SERVICE_ERROR"
        )
