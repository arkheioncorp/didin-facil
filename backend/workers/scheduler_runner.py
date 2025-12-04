"""
Scheduler Runner
================
Entry point para o PostSchedulerService gerenciado por PM2/systemd.

Uso:
    python -m workers.scheduler_runner
    
Sinais:
    SIGTERM: Graceful shutdown
    SIGINT: Graceful shutdown (Ctrl+C)
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.post_scheduler import PostSchedulerService, SchedulerConfig
from shared.redis import get_redis

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("scheduler_runner")


class SchedulerRunner:
    """Runner com suporte a graceful shutdown e health checks."""
    
    def __init__(self):
        self.scheduler: Optional[PostSchedulerService] = None
        self.shutdown_event = asyncio.Event()
        self.is_healthy = False
        
    async def start(self):
        """Inicia o scheduler com configurações de ambiente."""
        logger.info("🚀 Iniciando Post Scheduler Worker...")
        
        # Configuração via environment variables
        config = SchedulerConfig(
            check_interval=int(os.getenv("SCHEDULER_CHECK_INTERVAL", "30")),
            max_retries=int(os.getenv("SCHEDULER_MAX_RETRIES", "3")),
            retry_delay_base=int(os.getenv("SCHEDULER_RETRY_DELAY", "60")),
            batch_size=int(os.getenv("SCHEDULER_BATCH_SIZE", "10")),
        )
        
        # Obtém conexão Redis
        try:
            redis = await get_redis()
            logger.info("✅ Conexão Redis estabelecida")
        except Exception as e:
            logger.error(f"❌ Falha ao conectar no Redis: {e}")
            raise
        
        # Inicializa scheduler
        self.scheduler = PostSchedulerService(redis=redis, config=config)
        self.is_healthy = True
        
        # Notifica PM2 que estamos prontos
        self._send_ready_signal()
        
        logger.info(f"✅ Scheduler iniciado com config: {config}")
        
        # Mantém rodando até shutdown
        try:
            await self._run_loop()
        except asyncio.CancelledError:
            logger.info("🛑 Scheduler cancelado")
        finally:
            await self._cleanup()
    
    async def _run_loop(self):
        """Loop principal que processa posts agendados."""
        while not self.shutdown_event.is_set():
            try:
                # Processa posts pendentes
                await self.scheduler.process_pending_posts()
                
                # Aguarda próximo ciclo ou shutdown
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(),
                        timeout=self.scheduler.config.check_interval
                    )
                except asyncio.TimeoutError:
                    pass  # Timeout normal, continua loop
                    
            except Exception as e:
                logger.error(f"❌ Erro no loop do scheduler: {e}", exc_info=True)
                # Aguarda um pouco antes de retry
                await asyncio.sleep(5)
    
    async def _cleanup(self):
        """Limpeza antes de encerrar."""
        logger.info("🧹 Executando cleanup...")
        self.is_healthy = False
        
        if self.scheduler:
            # Aqui podemos adicionar lógica de cleanup
            pass
        
        logger.info("✅ Cleanup concluído")
    
    def _send_ready_signal(self):
        """Envia sinal para PM2 indicando que está pronto."""
        # PM2 wait_ready feature
        if os.getenv("PM2_HOME"):
            try:
                # Envia para stdout que PM2 monitora
                print("ready")
                sys.stdout.flush()
            except Exception:
                pass
    
    def request_shutdown(self):
        """Solicita graceful shutdown."""
        logger.info("📨 Shutdown solicitado")
        self.shutdown_event.set()


def setup_signal_handlers(runner: SchedulerRunner, loop: asyncio.AbstractEventLoop):
    """Configura handlers para SIGTERM e SIGINT."""
    
    def handle_signal(sig):
        logger.info(f"📡 Sinal {sig.name} recebido")
        runner.request_shutdown()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))


async def health_check_server(runner: SchedulerRunner, port: int = 8001):
    """Servidor HTTP simples para health checks."""
    from aiohttp import web
    
    async def health_handler(request):
        if runner.is_healthy:
            return web.Response(text="OK", status=200)
        return web.Response(text="UNHEALTHY", status=503)
    
    async def readiness_handler(request):
        if runner.scheduler is not None:
            return web.Response(text="READY", status=200)
        return web.Response(text="NOT READY", status=503)
    
    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/ready", readiness_handler)
    
    runner_web = web.AppRunner(app)
    await runner_web.setup()
    site = web.TCPSite(runner_web, "0.0.0.0", port)
    await site.start()
    logger.info(f"🏥 Health check server em http://0.0.0.0:{port}")
    
    return runner_web


def main():
    """Entry point principal."""
    logger.info("=" * 50)
    logger.info("TikTrend Finder - Post Scheduler Worker")
    logger.info("=" * 50)
    
    # Cria runner
    runner = SchedulerRunner()
    
    # Event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Configura signal handlers
    setup_signal_handlers(runner, loop)
    
    try:
        # Inicia health check se habilitado
        health_port = os.getenv("SCHEDULER_HEALTH_PORT")
        if health_port:
            loop.run_until_complete(
                health_check_server(runner, int(health_port))
            )
        
        # Roda scheduler
        loop.run_until_complete(runner.start())
        
    except KeyboardInterrupt:
        logger.info("⌨️ Interrompido pelo usuário")
    except Exception as e:
        logger.error(f"💥 Erro fatal: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup do event loop
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        except Exception:
            pass
    
    logger.info("👋 Scheduler encerrado")
    sys.exit(0)


if __name__ == "__main__":
    main()
