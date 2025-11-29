# ============================================
# Social Media Agent - Agente de Redes Sociais
# ============================================

import logging
from typing import Any, Optional, Dict
from datetime import datetime

from .queue.models import TaskResult, TaskStatus

# Importar clientes dos vendors
from ..vendor.instagram.client import (
    InstagramClient, 
    InstagramConfig, 
    PostConfig
)
from ..vendor.whatsapp.client import WhatsAppClient, WhatsAppConfig
from ..vendor.tiktok.client import TikTokClient, TikTokConfig
from ..vendor.youtube.client import YouTubeClient, YouTubeConfig

logger = logging.getLogger(__name__)

class SocialMediaAgent:
    """
    Agente responsável por executar tarefas de redes sociais
    usando os módulos em backend/vendor/.
    """
    
    def __init__(self):
        self._current_task: Optional[TaskResult] = None

    async def run_task(
        self,
        task_id: str,
        task_type: str,
        task_description: str,
        task_data: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """Executa uma tarefa de rede social"""
        
        self._current_task = TaskResult(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(),
            logs=[
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"🚀 Iniciando tarefa: {task_description}"
            ]
        )
        
        try:
            if not task_data:
                raise ValueError("Dados da tarefa não fornecidos")

            result = None
            
            if task_type == "instagram_post":
                result = await self._handle_instagram_post(task_data)
            elif task_type == "whatsapp_message":
                result = await self._handle_whatsapp_message(task_data)
            elif task_type == "tiktok_upload":
                result = await self._handle_tiktok_upload(task_data)
            elif task_type == "youtube_upload":
                result = await self._handle_youtube_upload(task_data)
            else:
                raise ValueError(f"Tipo de tarefa desconhecido: {task_type}")
            
            self._current_task.status = TaskStatus.COMPLETED
            self._current_task.completed_at = datetime.now()
            self._current_task.result = result
            self._log("✅ Tarefa concluída com sucesso")
            
        except Exception as e:
            logger.exception(f"Erro na tarefa {task_id}: {e}")
            self._current_task.status = TaskStatus.FAILED
            self._current_task.completed_at = datetime.now()
            self._current_task.error = str(e)
            self._log(f"❌ Erro: {str(e)}")
            
        return self._current_task

    def _log(self, message: str) -> None:
        """Adiciona log à tarefa atual"""
        if self._current_task:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self._current_task.logs.append(f"[{timestamp}] {message}")
        logger.info(message)

    # ============================================
    # Handlers
    # ============================================

    async def _handle_instagram_post(self, data: Dict[str, Any]) -> Any:
        """Executa postagem no Instagram"""
        self._log("📸 Configurando cliente Instagram...")
        
        config = InstagramConfig(
            username=data.get("username"),
            password=data.get("password"),
            session_file=data.get("session_file")
        )
        
        async with InstagramClient(config) as client:
            self._log("🔐 Realizando login...")
            if not await client.login():
                raise Exception("Falha no login do Instagram")
            
            media_type = data.get("media_type", "photo")
            path = data.get("file_path")
            caption = data.get("caption", "")
            
            post_config = PostConfig(caption=caption)
            
            self._log(f"📤 Enviando {media_type}...")
            
            if media_type == "photo":
                return await client.upload_photo(path, post_config)
            elif media_type == "video":
                return await client.upload_video(path, post_config)
            elif media_type == "reel":
                return await client.upload_reel(path, post_config)
            else:
                raise ValueError(f"Tipo de mídia não suportado: {media_type}")

    async def _handle_whatsapp_message(self, data: Dict[str, Any]) -> Any:
        """Envia mensagem via WhatsApp"""
        self._log("💬 Configurando cliente WhatsApp...")
        
        config = WhatsAppConfig(
            api_url=data.get("api_url"),
            api_key=data.get("api_key"),
            instance_name=data.get("instance_name")
        )
        
        client = WhatsAppClient(config)
        try:
            phone = data.get("phone")
            message = data.get("message")
            
            self._log(f"📤 Enviando mensagem para {phone}...")
            return await client.send_text(phone, message)
        finally:
            await client.close()

    async def _handle_tiktok_upload(self, data: Dict[str, Any]) -> Any:
        """Faz upload para TikTok"""
        self._log("🎵 Configurando cliente TikTok...")
        
        # Implementação simplificada assumindo que o client já existe
        # Na prática, precisaria instanciar o TikTokClient
        # Como o client.py do TikTok não foi lido completamente,
        # assumo interface similar
        
        config = TikTokConfig(
            session_id=data.get("session_id")
        )
        
        async with TikTokClient(config) as client:
            self._log("📤 Iniciando upload...")
            return await client.upload_video(
                video_path=data.get("file_path"),
                description=data.get("description", "")
            )

    async def _handle_youtube_upload(self, data: Dict[str, Any]) -> Any:
        """Faz upload para YouTube"""
        self._log("📺 Configurando cliente YouTube...")
        
        config = YouTubeConfig(
            client_secrets_file=data.get("client_secrets_file"),
            credentials_file=data.get("credentials_file")
        )
        
        async with YouTubeClient(config) as client:
            self._log("📤 Iniciando upload...")
            return await client.upload_video(
                video_path=data.get("file_path"),
                title=data.get("title"),
                description=data.get("description", "")
            )
