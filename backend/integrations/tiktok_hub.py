"""
TikTok Integration Hub
======================
Ponto central de integração do TikTok para o Didin Fácil.

Este módulo consolida todas as integrações com TikTok:
- Gerenciamento de Sessões (Cookies)
- Upload de Vídeos
- Analytics (futuro)
- Mensagens (futuro)

Autor: Didin Fácil
Versão: 1.1.0 (com alertas e métricas)
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from api.services.tiktok_session import TikTokSessionManager, TikTokSession
from vendor.tiktok.client import (
    TikTokClient, TikTokConfig, VideoConfig, Privacy, UploadStatus
)
from .resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    retry_with_backoff,
    RetryConfig
)
from .metrics import get_metrics_registry
from .alerts import get_alert_manager

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

@dataclass
class TikTokHubConfig:
    """Configuração centralizada do TikTok Hub."""
    headless: bool = True
    upload_timeout: int = 300
    
    # Resilience config
    max_retries: int = 3
    retry_delay: float = 2.0  # TikTok é mais lento
    circuit_breaker_threshold: int = 3  # Mais sensível pois usa browser
    circuit_breaker_timeout: float = 60.0

# ============================================
# HUB CLASS
# ============================================

class TikTokHub:
    """
    Hub central para operações do TikTok.
    """
    
    def __init__(self, config: Optional[TikTokHubConfig] = None):
        self.config = config or TikTokHubConfig()
        self.session_manager = TikTokSessionManager()
        
        # Resiliência: Circuit Breaker para TikTok API/Browser
        cb_config = CircuitBreakerConfig(
            failure_threshold=self.config.circuit_breaker_threshold,
            timeout_seconds=self.config.circuit_breaker_timeout,
            half_open_max_calls=2  # Menos chamadas de teste pois é pesado
        )
        self._circuit_breaker = CircuitBreaker(
            name="tiktok_hub",
            config=cb_config
        )
        
    # ============================================
    # SESSION MANAGEMENT
    # ============================================
    
    async def save_session(self, user_id: str, account_name: str, cookies: List[Dict]) -> TikTokSession:
        """Salva uma nova sessão (cookies)."""
        return await self.session_manager.save_session(
            user_id=user_id,
            account_name=account_name,
            cookies=cookies,
            metadata={"source": "hub_import"}
        )
        
    async def get_session(self, user_id: str, account_name: str) -> Optional[TikTokSession]:
        """Recupera uma sessão."""
        return await self.session_manager.get_session(user_id, account_name)
        
    async def list_sessions(self, user_id: str) -> List[TikTokSession]:
        """Lista sessões de um usuário."""
        return await self.session_manager.list_sessions(user_id)

    # ============================================
    # UPLOAD OPERATIONS
    # ============================================

    async def upload_video(
        self,
        user_id: str,
        account_name: str,
        video_path: str,
        caption: str,
        privacy: str = "public",
        schedule_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Realiza upload de vídeo usando a sessão salva.
        Aplica circuit breaker para evitar sobrecarga.
        Inclui métricas e alertas automáticos.
        """
        metrics = get_metrics_registry()
        start_time = asyncio.get_event_loop().time()
        state_before = self._circuit_breaker.state
        
        # Verifica circuit breaker antes de iniciar operação pesada
        if not await self._circuit_breaker.can_execute():
            stats = self._circuit_breaker.stats
            raise CircuitBreakerOpenError(
                f"TikTok Hub circuit breaker is open "
                f"(failures: {stats.failure_count})"
            )
        
        try:
            session = await self.get_session(user_id, account_name)
            if not session:
                raise ValueError(f"Sessão não encontrada: {account_name}")
            
            # TODO: Implementar upload real com retry
            # Por hora, retorna status pendente
            result = {
                "status": "pending",
                "message": "Upload agendado (integração pendente)"
            }
            
            await self._circuit_breaker.record_success()
            
            # Verifica recuperação
            state_after = self._circuit_breaker.state
            if state_before.value != "closed" and state_after.value == "closed":
                await get_alert_manager().send_circuit_breaker_closed("tiktok")
            
            # Registra métrica de sucesso
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            metrics.record_request("tiktok", True, elapsed)
            
            return result
            
        except Exception as e:
            state_before = self._circuit_breaker.state
            await self._circuit_breaker.record_failure()
            state_after = self._circuit_breaker.state
            
            # Registra métrica de falha
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            metrics.record_request("tiktok", False, elapsed)
            
            # Alertas para mudança de estado
            if state_before.value != "open" and state_after.value == "open":
                await get_alert_manager().send_circuit_breaker_open(
                    hub="tiktok",
                    failure_count=self._circuit_breaker.stats.failure_count,
                    threshold=self._circuit_breaker.config.failure_threshold
                )
            
            logger.error(f"Erro no upload TikTok: {e}")
            raise

    # ============================================
    # MESSAGING (Placeholder)
    # ============================================
    
    async def send_message(self, recipient_id: str, text: str):
        """
        Envia mensagem direta (DM).
        Nota: Requer automação via browser ou API privada, não suportado oficialmente.
        """
        raise NotImplementedError("Envio de mensagens TikTok ainda não implementado")


# Singleton global
_tiktok_hub: Optional[TikTokHub] = None

def get_tiktok_hub() -> TikTokHub:
    """Retorna instância singleton do TikTok Hub."""
    global _tiktok_hub
    if _tiktok_hub is None:
        _tiktok_hub = TikTokHub()
    return _tiktok_hub
