# ============================================
# Seller Bot Agent - Orquestrador Principal
# ============================================

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from enum import Enum

from pydantic import BaseModel

from .config import SellerBotConfig

# Configurar logging
logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Status de execução de uma tarefa"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskResult(BaseModel):
    """Resultado de uma tarefa executada"""
    task_id: str
    task_type: str
    status: TaskStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    screenshots: list[str] = []
    steps_executed: int = 0
    logs: list[str] = []


class SellerBotAgent:
    """
    Agente principal do Seller Bot.
    
    Orquestra a execução de tarefas usando browser-use,
    gerenciando o navegador e comunicando progresso ao frontend.
    """
    
    def __init__(
        self,
        config: Optional[SellerBotConfig] = None,
        on_step_callback: Optional[Callable[[dict], None]] = None,
        on_screenshot_callback: Optional[Callable[[str], None]] = None,
    ):
        self.config = config or SellerBotConfig.from_env()
        self.on_step_callback = on_step_callback
        self.on_screenshot_callback = on_screenshot_callback
        
        self._browser = None
        self._agent = None
        self._current_task: Optional[TaskResult] = None
        self._is_running = False
        self._should_stop = False
        
        # Criar diretório de screenshots
        Path(self.config.task.screenshot_dir).mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> None:
        """Inicializa o navegador e o agente browser-use"""
        try:
            from browser_use import Browser, BrowserProfile
            
            # Configurar perfil do navegador
            profile = BrowserProfile(
                executable_path=self.config.browser.executable_path,
                user_data_dir=self.config.browser.user_data_dir,
                profile_directory=self.config.browser.profile_directory,
                headless=self.config.browser.headless,
                keep_alive=self.config.browser.keep_alive,
            )
            
            # Criar sessão do navegador
            self._browser = Browser(browser_profile=profile)
            
            logger.info("SellerBot inicializado com sucesso")
            self._log("✅ Navegador inicializado com perfil persistente")
            
        except ImportError:
            logger.error("browser-use não instalado. Execute: pip install browser-use")
            raise RuntimeError("Dependência browser-use não encontrada")
        except Exception as e:
            logger.error(f"Erro ao inicializar navegador: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Encerra o navegador e limpa recursos"""
        if self._browser:
            try:
                await self._browser.close()
                logger.info("Navegador encerrado")
            except Exception as e:
                logger.error(f"Erro ao encerrar navegador: {e}")
        
        self._browser = None
        self._agent = None
        self._is_running = False
    
    def _log(self, message: str) -> None:
        """Adiciona log e notifica callback"""
        if self._current_task:
            self._current_task.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
        logger.info(message)
        
        if self.on_step_callback:
            self.on_step_callback({
                "type": "log",
                "message": message,
                "timestamp": datetime.now().isoformat(),
            })
    
    async def _capture_screenshot(self, name: str) -> Optional[str]:
        """Captura screenshot e retorna o path"""
        if not self._browser:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = Path(self.config.task.screenshot_dir) / filename
            
            # Capturar screenshot via browser-use
            # await self._browser.screenshot(str(filepath))
            
            if self._current_task:
                self._current_task.screenshots.append(str(filepath))
            
            if self.on_screenshot_callback:
                self.on_screenshot_callback(str(filepath))
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Erro ao capturar screenshot: {e}")
            return None
    
    async def run_task(
        self,
        task_id: str,
        task_type: str,
        task_description: str,
        task_data: Optional[dict] = None,
    ) -> TaskResult:
        """
        Executa uma tarefa usando o agente browser-use.
        
        Args:
            task_id: ID único da tarefa
            task_type: Tipo da tarefa (post_product, manage_orders, etc.)
            task_description: Descrição em linguagem natural da tarefa
            task_data: Dados adicionais para a tarefa (ex: dados do produto)
        
        Returns:
            TaskResult com status e resultados
        """
        if self._is_running:
            raise RuntimeError("Já existe uma tarefa em execução")
        
        self._is_running = True
        self._should_stop = False
        
        # Inicializar resultado da tarefa
        self._current_task = TaskResult(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(),
        )
        
        try:
            # Garantir que o navegador está inicializado
            if not self._browser:
                await self.initialize()
            
            self._log(f"🚀 Iniciando tarefa: {task_type}")
            self._log(f"📋 Descrição: {task_description}")
            
            # Importar e configurar o agente
            from browser_use import Agent
            
            # Configurar LLM baseado no provider
            llm = await self._get_llm()
            
            # Criar agente browser-use
            self._agent = Agent(
                task=task_description,
                llm=llm,
                browser=self._browser,
                use_vision=self.config.llm.use_vision,
                max_actions_per_step=self.config.task.max_actions_per_step,
            )
            
            # Callback para cada passo
            async def on_step(step_info: dict):
                if self._should_stop:
                    raise asyncio.CancelledError("Tarefa cancelada pelo usuário")
                
                self._current_task.steps_executed += 1
                self._log(f"📍 Passo {self._current_task.steps_executed}: {step_info.get('action', 'N/A')}")
                
                if self.config.task.auto_screenshot:
                    await self._capture_screenshot(f"step_{self._current_task.steps_executed}")
                
                # Delay para parecer humano
                await asyncio.sleep(self.config.task.action_delay_ms / 1000)
            
            # Executar agente
            history = await self._agent.run(max_steps=self.config.task.max_steps)
            
            # Processar resultado
            self._current_task.status = TaskStatus.COMPLETED
            self._current_task.result = {
                "final_result": history.final_result() if hasattr(history, 'final_result') else None,
                "steps": self._current_task.steps_executed,
            }
            
            self._log("✅ Tarefa concluída com sucesso!")
            
        except asyncio.CancelledError:
            self._current_task.status = TaskStatus.CANCELLED
            self._current_task.error = "Tarefa cancelada pelo usuário"
            self._log("⚠️ Tarefa cancelada")
            
        except Exception as e:
            self._current_task.status = TaskStatus.FAILED
            self._current_task.error = str(e)
            self._log(f"❌ Erro: {e}")
            logger.exception("Erro durante execução da tarefa")
            
        finally:
            self._current_task.completed_at = datetime.now()
            self._is_running = False
            self._agent = None
        
        return self._current_task
    
    async def _get_llm(self):
        """Retorna o LLM configurado baseado no provider"""
        provider = self.config.llm.provider.lower()
        model = self.config.llm.model
        
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model,
                temperature=self.config.llm.temperature,
                api_key=self.config.llm.api_key,
            )
        
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=model,
                temperature=self.config.llm.temperature,
                api_key=self.config.llm.api_key,
            )
        
        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=model,
                temperature=self.config.llm.temperature,
            )
        
        elif provider == "browser_use":
            from browser_use import ChatBrowserUse
            return ChatBrowserUse()
        
        else:
            raise ValueError(f"Provider LLM não suportado: {provider}")
    
    def stop(self) -> None:
        """Solicita parada da tarefa atual"""
        if self._is_running:
            self._should_stop = True
            self._log("🛑 Solicitando parada...")
    
    @property
    def is_running(self) -> bool:
        """Retorna se há tarefa em execução"""
        return self._is_running
    
    @property
    def current_task(self) -> Optional[TaskResult]:
        """Retorna a tarefa atual"""
        return self._current_task
