"""
Redis Context Store for Seller Bot
===================================
Persiste contextos de conversa no Redis para:
- Persistência entre reinícios
- Compartilhamento entre workers
- Expiração automática (30 min inatividade)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from pydantic import BaseModel
from shared.redis import get_redis

logger = logging.getLogger(__name__)

# TTL padrão: 30 minutos de inatividade
DEFAULT_CONTEXT_TTL = 30 * 60  # segundos


class ContextStore:
    """
    Store de contextos de conversa usando Redis.
    
    Chave: context:{channel}:{user_id}
    Valor: JSON serializado do ConversationContext
    TTL: 30 minutos (renovado a cada interação)
    """
    
    PREFIX = "context"
    
    def __init__(self, ttl: int = DEFAULT_CONTEXT_TTL):
        self.ttl = ttl
    
    def _make_key(self, channel: str, user_id: str) -> str:
        """Gera chave Redis para o contexto."""
        return f"{self.PREFIX}:{channel}:{user_id}"
    
    async def get(
        self, 
        channel: str, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Recupera contexto do Redis.
        
        Args:
            channel: Canal de origem (whatsapp, instagram, etc)
            user_id: ID do usuário
            
        Returns:
            Dict com contexto ou None se não existir/expirado
        """
        try:
            redis = await get_redis()
            if not redis:
                logger.warning("Redis not available, using in-memory")
                return None
            
            key = self._make_key(channel, user_id)
            data = await redis.get(key)
            
            if not data:
                return None
            
            context = json.loads(data)
            
            # Verificar expiração lógica (30 min inatividade)
            last_interaction = datetime.fromisoformat(
                context.get("last_interaction", datetime.utcnow().isoformat())
            )
            if datetime.utcnow() - last_interaction > timedelta(seconds=self.ttl):
                # Contexto expirado logicamente
                await self.delete(channel, user_id)
                return None
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting context from Redis: {e}")
            return None
    
    async def set(
        self, 
        channel: str, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> bool:
        """
        Salva contexto no Redis.
        
        Args:
            channel: Canal de origem
            user_id: ID do usuário
            context: Dict do contexto (já serializado de Pydantic)
            
        Returns:
            True se salvou com sucesso
        """
        try:
            redis = await get_redis()
            if not redis:
                logger.warning("Redis not available")
                return False
            
            key = self._make_key(channel, user_id)
            
            # Atualizar timestamp
            context["updated_at"] = datetime.utcnow().isoformat()
            context["last_interaction"] = datetime.utcnow().isoformat()
            
            # Salvar com TTL (Redis expira automaticamente)
            await redis.set(key, json.dumps(context), ex=self.ttl)
            
            logger.debug(f"Context saved: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving context to Redis: {e}")
            return False
    
    async def delete(self, channel: str, user_id: str) -> bool:
        """Remove contexto do Redis."""
        try:
            redis = await get_redis()
            if not redis:
                return False
            
            key = self._make_key(channel, user_id)
            await redis.delete(key)
            logger.debug(f"Context deleted: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting context from Redis: {e}")
            return False
    
    async def list_all(
        self, 
        channel: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Lista todos os contextos ativos.
        
        Args:
            channel: Filtrar por canal (opcional)
            
        Returns:
            Lista de contextos
        """
        try:
            redis = await get_redis()
            if not redis:
                return []
            
            pattern = f"{self.PREFIX}:{channel or '*'}:*"
            keys = await redis.keys(pattern)
            
            contexts = []
            for key in keys:
                data = await redis.get(key)
                if data:
                    ctx = json.loads(data)
                    ctx["_key"] = key
                    contexts.append(ctx)
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error listing contexts from Redis: {e}")
            return []
    
    async def count(self, channel: Optional[str] = None) -> int:
        """Conta contextos ativos."""
        try:
            redis = await get_redis()
            if not redis:
                return 0
            
            pattern = f"{self.PREFIX}:{channel or '*'}:*"
            keys = await redis.keys(pattern)
            return len(keys)
            
        except Exception as e:
            logger.error(f"Error counting contexts: {e}")
            return 0
    
    async def cleanup_expired(self) -> int:
        """
        Limpa contextos expirados (backup - Redis já expira por TTL).
        
        Returns:
            Número de contextos removidos
        """
        try:
            redis = await get_redis()
            if not redis:
                return 0
            
            pattern = f"{self.PREFIX}:*"
            keys = await redis.keys(pattern)
            
            removed = 0
            now = datetime.utcnow()
            
            for key in keys:
                data = await redis.get(key)
                if data:
                    ctx = json.loads(data)
                    last = datetime.fromisoformat(
                        ctx.get("last_interaction", now.isoformat())
                    )
                    if now - last > timedelta(seconds=self.ttl):
                        await redis.delete(key)
                        removed += 1
            
            if removed > 0:
                logger.info(f"Cleaned up {removed} expired contexts")
            
            return removed
            
        except Exception as e:
            logger.error(f"Error cleaning up contexts: {e}")
            return 0


# Instância global
context_store = ContextStore()


async def get_context_store() -> ContextStore:
    """Dependency para obter o context store."""
    return context_store
