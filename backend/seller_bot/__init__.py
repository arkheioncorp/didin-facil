# ============================================
# Seller Bot - TikTok Shop Automation Module
# ============================================
# 
# Este módulo implementa automação completa da Central do Vendedor
# TikTok Shop usando browser-use para controle de navegador via IA.
#
# Arquitetura:
# - profiles/: Gestão de perfis Chrome persistentes
# - tasks/: Tarefas automatizadas (postagem, pedidos, mensagens)
# - queue/: Sistema de filas para execução assíncrona
#
# Preço: R$149,90/mês (Plano Premium Bot)

from .config import SellerBotConfig
from .agent import SellerBotAgent
from .queue.manager import TaskQueueManager

__all__ = [
    "SellerBotConfig",
    "SellerBotAgent", 
    "TaskQueueManager",
]

__version__ = "1.0.0"
