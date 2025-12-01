"""
Sentry Integration
Monitoramento de erros e performance
"""

import logging
from functools import wraps
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations import DidNotEnable
from sentry_sdk.integrations.logging import LoggingIntegration

# Optional integrations (not available in all contexts)
# These may raise DidNotEnable if dependencies are missing
try:
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    HAS_FASTAPI = True
except (ImportError, DidNotEnable):
    HAS_FASTAPI = False
    FastApiIntegration = None

try:
    from sentry_sdk.integrations.starlette import StarletteIntegration
    HAS_STARLETTE = True
except (ImportError, DidNotEnable):
    HAS_STARLETTE = False
    StarletteIntegration = None

try:
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    HAS_SQLALCHEMY = True
except (ImportError, DidNotEnable):
    HAS_SQLALCHEMY = False
    SqlalchemyIntegration = None

try:
    from sentry_sdk.integrations.redis import RedisIntegration
    HAS_REDIS = True
except (ImportError, DidNotEnable):
    HAS_REDIS = False
    RedisIntegration = None

try:
    from sentry_sdk.integrations.httpx import HttpxIntegration
    HAS_HTTPX = True
except (ImportError, DidNotEnable):
    HAS_HTTPX = False
    HttpxIntegration = None

from .config import settings

logger = logging.getLogger(__name__)


class SentryService:
    """Serviço de integração com Sentry para monitoramento"""
    
    def __init__(self):
        self._initialized = False
        self._configured = False
        self._check_configuration()
    
    def _check_configuration(self) -> bool:
        """Verifica se Sentry está configurado"""
        self._configured = bool(
            settings.SENTRY_DSN and 
            not settings.SENTRY_DSN.startswith("INSERIR_")
        )
        
        if not self._configured:
            logger.warning(
                "⚠️ Sentry DSN não configurado. "
                "Monitoramento de erros desabilitado."
            )
        
        return self._configured
    
    @property
    def is_configured(self) -> bool:
        """Verifica se o serviço está configurado"""
        return self._configured
    
    @property
    def is_initialized(self) -> bool:
        """Verifica se o SDK foi inicializado"""
        return self._initialized
    
    def _get_integrations(self) -> list:
        """
        Retorna lista de integrações disponíveis.
        Algumas integrações só estão disponíveis em certos contextos.
        """
        integrations = [
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ]
        
        # Adicionar integrações opcionais se disponíveis
        if HAS_REDIS and RedisIntegration is not None:
            integrations.append(RedisIntegration())
        if HAS_HTTPX and HttpxIntegration is not None:
            integrations.append(HttpxIntegration())
        if HAS_FASTAPI and FastApiIntegration is not None:
            integrations.append(
                FastApiIntegration(transaction_style="endpoint")
            )
        if HAS_SQLALCHEMY and SqlalchemyIntegration is not None:
            integrations.append(SqlalchemyIntegration())
        
        return integrations
    
    def init(self) -> bool:
        """
        Inicializa o Sentry SDK
        
        Returns:
            True se inicializado com sucesso
        """
        if self._initialized:
            logger.debug("Sentry já inicializado")
            return True
        
        if not self._configured:
            logger.info("Sentry não configurado - pulando inicialização")
            return False
        
        try:
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                
                # Ambiente
                environment=settings.ENVIRONMENT,
                release="tiktrend-api@2.0.0",
                
                # Sampling
                traces_sample_rate=0.2 if settings.is_production else 1.0,
                profiles_sample_rate=0.1 if settings.is_production else 0.5,
                
                # Integrações - apenas as disponíveis
                integrations=self._get_integrations(),
                
                # Configurações de dados
                send_default_pii=False,  # LGPD compliance
                max_breadcrumbs=50,
                attach_stacktrace=True,
                
                # Filtros
                before_send=self._before_send,
                before_send_transaction=self._before_send_transaction,
                
                # Debug (apenas em dev)
                debug=settings.DEBUG,
            )
            
            self._initialized = True
            logger.info("✅ Sentry SDK inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Sentry: {e}")
            return False
    
    def _before_send(self, event: dict, hint: dict) -> Optional[dict]:
        """
        Processa evento antes de enviar ao Sentry
        Remove dados sensíveis para LGPD compliance
        """
        # Remover dados sensíveis de request
        if 'request' in event:
            request = event['request']
            
            # Remover cookies
            if 'cookies' in request:
                request['cookies'] = "[FILTERED]"
            
            # Filtrar headers sensíveis
            if 'headers' in request:
                sensitive_headers = [
                    'authorization', 'cookie', 'x-api-key',
                    'x-auth-token', 'x-csrf-token'
                ]
                for header in sensitive_headers:
                    if header in request['headers']:
                        request['headers'][header] = "[FILTERED]"
            
            # Filtrar dados de body
            if 'data' in request:
                sensitive_fields = [
                    'password', 'token', 'secret', 'api_key',
                    'access_token', 'refresh_token', 'credit_card',
                    'cpf', 'rg', 'phone', 'email'
                ]
                data = request.get('data', {})
                if isinstance(data, dict):
                    for field in sensitive_fields:
                        if field in data:
                            data[field] = "[FILTERED]"
        
        # Remover dados de usuário sensíveis
        if 'user' in event:
            user = event['user']
            # Manter apenas ID e IP (anonimizado)
            allowed_fields = ['id', 'ip_address']
            event['user'] = {
                k: v for k, v in user.items() 
                if k in allowed_fields
            }
        
        return event
    
    def _before_send_transaction(
        self, 
        event: dict, 
        hint: dict
    ) -> Optional[dict]:
        """
        Processa transaction antes de enviar
        Filtra transactions não interessantes
        """
        transaction = event.get('transaction', '')
        
        # Ignorar health checks
        if transaction in ['/health', '/healthz', '/ready', '/']:
            return None
        
        # Ignorar assets estáticos
        if transaction.startswith('/static/'):
            return None
        
        return event
    
    def capture_exception(
        self,
        exception: Exception,
        **extra_context
    ) -> Optional[str]:
        """
        Captura exceção e envia ao Sentry
        
        Args:
            exception: Exceção a ser capturada
            **extra_context: Contexto adicional
        
        Returns:
            Event ID ou None
        """
        if not self._initialized:
            logger.error(f"Exceção não enviada (Sentry não inicializado): {exception}")
            return None
        
        with sentry_sdk.push_scope() as scope:
            for key, value in extra_context.items():
                scope.set_extra(key, value)
            
            event_id = sentry_sdk.capture_exception(exception)
            logger.debug(f"Exceção capturada: {event_id}")
            return event_id
    
    def capture_message(
        self,
        message: str,
        level: str = "info",
        **extra_context
    ) -> Optional[str]:
        """
        Captura mensagem e envia ao Sentry
        
        Args:
            message: Mensagem a ser capturada
            level: Nível (info, warning, error)
            **extra_context: Contexto adicional
        
        Returns:
            Event ID ou None
        """
        if not self._initialized:
            return None
        
        with sentry_sdk.push_scope() as scope:
            for key, value in extra_context.items():
                scope.set_extra(key, value)
            
            event_id = sentry_sdk.capture_message(message, level=level)
            return event_id
    
    def set_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        **extra
    ) -> None:
        """
        Define contexto do usuário para eventos subsequentes
        
        Args:
            user_id: ID do usuário
            email: Email (será filtrado em produção)
            **extra: Dados adicionais
        """
        if not self._initialized:
            return
        
        user_data = {"id": user_id}
        
        # Em dev, incluir mais dados para debug
        if settings.DEBUG and email:
            user_data["email"] = email
        
        user_data.update(extra)
        sentry_sdk.set_user(user_data)
    
    def set_tag(self, key: str, value: str) -> None:
        """Define tag para eventos subsequentes"""
        if not self._initialized:
            return
        sentry_sdk.set_tag(key, value)
    
    def set_context(self, name: str, data: dict) -> None:
        """Define contexto adicional"""
        if not self._initialized:
            return
        sentry_sdk.set_context(name, data)
    
    def add_breadcrumb(
        self,
        message: str,
        category: str = "custom",
        level: str = "info",
        data: Optional[dict] = None
    ) -> None:
        """
        Adiciona breadcrumb para rastreamento
        
        Args:
            message: Mensagem do breadcrumb
            category: Categoria (http, navigation, custom)
            level: Nível (debug, info, warning, error)
            data: Dados adicionais
        """
        if not self._initialized:
            return
        
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )
    
    def start_transaction(
        self,
        name: str,
        op: str = "task"
    ):
        """
        Inicia transaction para performance monitoring
        
        Args:
            name: Nome da transaction
            op: Operação (http.server, task, etc)
        
        Returns:
            Transaction context manager
        """
        if not self._initialized:
            # Retornar no-op context manager
            from contextlib import nullcontext
            return nullcontext()
        
        return sentry_sdk.start_transaction(name=name, op=op)
    
    def flush(self, timeout: float = 2.0) -> None:
        """
        Força envio de eventos pendentes
        Útil antes de shutdown
        
        Args:
            timeout: Tempo máximo de espera em segundos
        """
        if self._initialized:
            sentry_sdk.flush(timeout=timeout)


def sentry_trace(op: str = "function"):
    """
    Decorator para tracing automático de funções
    
    Usage:
        @sentry_trace("db.query")
        async def fetch_products():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not sentry.is_initialized:
                return await func(*args, **kwargs)
            
            with sentry_sdk.start_span(op=op, description=func.__name__):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not sentry.is_initialized:
                return func(*args, **kwargs)
            
            with sentry_sdk.start_span(op=op, description=func.__name__):
                return func(*args, **kwargs)
        
        if asyncio_is_async(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def asyncio_is_async(func) -> bool:
    """Verifica se função é assíncrona"""
    import asyncio
    return asyncio.iscoroutinefunction(func)


# Singleton instance
sentry = SentryService()
