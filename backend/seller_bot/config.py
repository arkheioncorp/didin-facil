# ============================================
# Seller Bot Configuration
# ============================================

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class BrowserProfileConfig(BaseModel):
    """Configuração do perfil do navegador Chrome"""
    
    # Caminho do Chrome instalado
    executable_path: str = Field(
        default="/usr/bin/google-chrome",
        description="Caminho para o executável do Chrome/Chromium"
    )
    
    # Diretório de dados do usuário Chrome
    user_data_dir: str = Field(
        default=str(Path.home() / ".config" / "google-chrome"),
        description="Diretório de perfil do Chrome (mantém cookies/login)"
    )
    
    # Nome do perfil dentro do user_data_dir
    profile_directory: str = Field(
        default="Default",
        description="Nome do perfil (Default, Profile 1, etc.)"
    )
    
    # Modo headless ou headed
    headless: bool = Field(
        default=False,
        description="Se True, navegador roda sem interface visual"
    )
    
    # Manter navegador aberto após execução
    keep_alive: bool = Field(
        default=True,
        description="Manter navegador aberto entre tarefas"
    )
    
    # Timeout para carregamento de páginas (ms)
    page_load_timeout: int = Field(
        default=30000,
        description="Timeout para carregamento de páginas em ms"
    )


class LLMConfig(BaseModel):
    """Configuração do modelo de linguagem"""
    
    # Provider: openai, anthropic, ollama, browser_use
    provider: str = Field(
        default="openai",
        description="Provedor do LLM"
    )
    
    # Nome do modelo
    model: str = Field(
        default="gpt-4o-mini",
        description="Nome do modelo a ser usado"
    )
    
    # API Key (será lida de variável de ambiente se não fornecida)
    api_key: Optional[str] = Field(
        default=None,
        description="API Key do provedor"
    )
    
    # Temperatura para geração
    temperature: float = Field(
        default=0.1,
        description="Temperatura do modelo (0.0-1.0)"
    )
    
    # Usar visão (screenshots) nas decisões
    use_vision: bool = Field(
        default=True,
        description="Incluir screenshots nas decisões do LLM"
    )


class TaskConfig(BaseModel):
    """Configuração de execução de tarefas"""
    
    # Máximo de passos por tarefa
    max_steps: int = Field(
        default=50,
        description="Máximo de passos antes de abortar"
    )
    
    # Máximo de ações por passo
    max_actions_per_step: int = Field(
        default=4,
        description="Máximo de ações em cada passo"
    )
    
    # Intervalo entre ações (ms)
    action_delay_ms: int = Field(
        default=1000,
        description="Delay entre ações para parecer humano"
    )
    
    # Modo demo (mostra painel de logs no navegador)
    demo_mode: bool = Field(
        default=True,
        description="Mostrar painel de debug no navegador"
    )
    
    # Capturar screenshots automaticamente
    auto_screenshot: bool = Field(
        default=True,
        description="Capturar screenshot a cada passo"
    )
    
    # Diretório para salvar screenshots
    screenshot_dir: str = Field(
        default="./screenshots",
        description="Diretório para salvar capturas de tela"
    )


class SellerBotConfig(BaseModel):
    """Configuração principal do Seller Bot"""
    
    browser: BrowserProfileConfig = Field(default_factory=BrowserProfileConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    task: TaskConfig = Field(default_factory=TaskConfig)
    
    # URLs base do TikTok Seller Center
    tiktok_seller_url: str = Field(
        default="https://seller-br.tiktok.com",
        description="URL base da Central do Vendedor"
    )
    
    # Habilitar logging detalhado
    verbose: bool = Field(
        default=True,
        description="Log detalhado de execução"
    )
    
    @classmethod
    def from_env(cls) -> "SellerBotConfig":
        """Carrega configuração de variáveis de ambiente"""
        return cls(
            browser=BrowserProfileConfig(
                executable_path=os.getenv("CHROME_PATH", "/usr/bin/google-chrome"),
                user_data_dir=os.getenv("CHROME_USER_DATA", str(Path.home() / ".config" / "google-chrome")),
                profile_directory=os.getenv("CHROME_PROFILE", "Default"),
                headless=os.getenv("BOT_HEADLESS", "false").lower() == "true",
            ),
            llm=LLMConfig(
                provider=os.getenv("LLM_PROVIDER", "openai"),
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY"),
            ),
        )
