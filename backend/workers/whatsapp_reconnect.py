"""
WhatsApp Reconnect Worker
=========================
Monitora e reconecta sessões WhatsApp desconectadas.

Uso:
    python -m workers.whatsapp_reconnect
"""

import asyncio
import logging
import os
import signal
import sys

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("whatsapp_reconnect")


class WhatsAppReconnectWorker:
    """Worker que monitora e reconecta sessões WhatsApp."""

    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.check_interval = int(os.getenv("RECONNECT_CHECK_INTERVAL", "60"))
        self.redis = None

    async def start(self):
        """Inicia o worker de reconexão."""
        logger.info("🚀 Iniciando WhatsApp Reconnect Worker...")

        try:
            from shared.redis import get_redis

            self.redis = await get_redis()
            logger.info("✅ Conexão Redis estabelecida")
        except Exception as e:
            logger.error(f"❌ Falha ao conectar no Redis: {e}")
            raise

        logger.info(
            f"✅ Worker iniciado (intervalo: {self.check_interval}s)"
        )

        try:
            await self._run_loop()
        except asyncio.CancelledError:
            logger.info("🛑 Worker cancelado")
        finally:
            await self._cleanup()

    async def _run_loop(self):
        """Loop principal de monitoramento."""
        while not self.shutdown_event.is_set():
            try:
                await self._check_and_reconnect()

                # Aguarda próximo ciclo ou shutdown
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(),
                        timeout=self.check_interval
                    )
                except asyncio.TimeoutError:
                    pass

            except Exception as e:
                logger.error(f"❌ Erro no loop: {e}", exc_info=True)
                await asyncio.sleep(10)

    async def _check_and_reconnect(self):
        """Verifica sessões e tenta reconectar as desconectadas."""
        try:
            # Busca todas as sessões WhatsApp registradas
            sessions = await self._get_registered_sessions()

            if not sessions:
                logger.debug("Nenhuma sessão registrada")
                return

            for session_id in sessions:
                try:
                    status = await self._get_session_status(session_id)

                    if status in ["disconnected", "close", "qrcode"]:
                        logger.warning(
                            f"📱 Sessão {session_id} desconectada: {status}"
                        )
                        await self._attempt_reconnect(session_id)

                except Exception as e:
                    logger.error(
                        f"❌ Erro ao verificar sessão {session_id}: {e}"
                    )

        except Exception as e:
            logger.error(f"❌ Erro ao buscar sessões: {e}")

    async def _get_registered_sessions(self) -> list:
        """Obtém lista de sessões WhatsApp registradas."""
        try:
            # Busca chaves de sessão no Redis
            keys = await self.redis.keys("whatsapp:session:*")
            return [
                k.decode().replace("whatsapp:session:", "")
                for k in keys
            ]
        except Exception:
            return []

    async def _get_session_status(self, session_id: str) -> str:
        """Obtém status atual da sessão."""
        try:
            import httpx
            from api.config import get_settings

            settings = get_settings()
            evolution_url = settings.EVOLUTION_API_URL

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{evolution_url}/instance/connectionState/{session_id}",
                    headers={"apikey": settings.EVOLUTION_API_KEY}
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("instance", {}).get("state", "unknown")

                return "unknown"

        except Exception as e:
            logger.debug(f"Não foi possível obter status: {e}")
            return "unknown"

    async def _attempt_reconnect(self, session_id: str):
        """Tenta reconectar uma sessão."""
        try:
            import httpx
            from api.config import get_settings

            settings = get_settings()
            evolution_url = settings.EVOLUTION_API_URL

            logger.info(f"🔄 Tentando reconectar sessão {session_id}...")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{evolution_url}/instance/connect/{session_id}",
                    headers={"apikey": settings.EVOLUTION_API_KEY}
                )

                if response.status_code == 200:
                    logger.info(f"✅ Reconexão iniciada: {session_id}")

                    # Registra tentativa no Redis
                    await self.redis.hincrby(
                        f"whatsapp:reconnect:{session_id}",
                        "attempts",
                        1
                    )
                    await self.redis.hset(
                        f"whatsapp:reconnect:{session_id}",
                        "last_attempt",
                        str(asyncio.get_event_loop().time())
                    )
                else:
                    logger.warning(
                        f"⚠️ Falha na reconexão {session_id}: "
                        f"{response.status_code}"
                    )

        except Exception as e:
            logger.error(f"❌ Erro ao reconectar {session_id}: {e}")

    async def _cleanup(self):
        """Limpeza antes de encerrar."""
        logger.info("🧹 Executando cleanup...")
        logger.info("✅ Cleanup concluído")

    def request_shutdown(self):
        """Solicita graceful shutdown."""
        logger.info("📨 Shutdown solicitado")
        self.shutdown_event.set()


def setup_signal_handlers(
    worker: WhatsAppReconnectWorker,
    loop: asyncio.AbstractEventLoop
):
    """Configura handlers para SIGTERM e SIGINT."""

    def handle_signal(sig):
        logger.info(f"📡 Sinal {sig.name} recebido")
        worker.request_shutdown()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))


def main():
    """Entry point principal."""
    logger.info("=" * 50)
    logger.info("Didin Fácil - WhatsApp Reconnect Worker")
    logger.info("=" * 50)

    worker = WhatsAppReconnectWorker()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    setup_signal_handlers(worker, loop)

    try:
        loop.run_until_complete(worker.start())
    except KeyboardInterrupt:
        logger.info("⌨️ Interrompido pelo usuário")
    except Exception as e:
        logger.error(f"💥 Erro fatal: {e}", exc_info=True)
        sys.exit(1)
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        except Exception:
            pass

    logger.info("👋 Worker encerrado")
    sys.exit(0)


if __name__ == "__main__":
    main()
