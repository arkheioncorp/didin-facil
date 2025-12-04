"""
WhatsApp Webhook Handler - Evolution API
=========================================
Recebe mensagens em tempo real da Evolution API e responde automaticamente.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from api.database.connection import database
from api.services.cache import CacheService
from api.services.scraper import ScraperOrchestrator
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel
from shared.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp-webhook", tags=["WhatsApp Webhook"])

# Constants
EVOLUTION_API_URL = settings.EVOLUTION_API_URL or "http://tiktrend-whatsapp:8080"
EVOLUTION_API_KEY = settings.EVOLUTION_API_KEY or "429683C4C977415CAAFCCE10F7D57E11"
EVOLUTION_INSTANCE = settings.EVOLUTION_INSTANCE or "tiktrend-whatsapp"

# Services
cache = CacheService()
scraper = ScraperOrchestrator()


# ============================================
# MODELS
# ============================================

class EvolutionWebhookPayload(BaseModel):
    """Payload recebido da Evolution API."""
    event: str
    instance: str
    data: Dict[str, Any]
    sender: Optional[str] = None
    destination: Optional[str] = None
    date_time: Optional[str] = None


class WhatsAppMessage(BaseModel):
    """Mensagem estruturada do WhatsApp."""
    remote_jid: str
    message_id: str
    from_me: bool
    push_name: Optional[str] = None
    message_type: str  # text, image, audio, video, document
    text: Optional[str] = None
    media_url: Optional[str] = None
    timestamp: datetime


# ============================================
# CHATBOT LOGIC COM PRODUTOS REAIS
# ============================================

class RealProductChatbot:
    """Chatbot com busca de produtos reais do banco de dados."""
    
    def __init__(self):
        self.cache = cache
        self.scraper = scraper
    
    async def process_message(
        self,
        phone: str,
        message: str,
        push_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Processa mensagem e retorna resposta com produtos reais."""
        
        msg = message.strip().lower()
        name = push_name or "cliente"
        
        # Incrementa contador de mensagens recebidas
        await self._increment_metric("messages_received")
        
        # Check user state
        state_key = f"chatbot:state:{phone}"
        user_state = await self.cache.get(state_key)
        
        # Handle menu options
        if msg in ["1", "buscar", "produto", "produtos"]:
            return await self._handle_product_search_start(phone, name)
        
        elif msg in ["2", "comparar", "preço", "preços"]:
            return await self._handle_price_comparison(phone, name)
        
        elif msg in ["3", "alerta", "alertas"]:
            return await self._handle_alerts(phone, name)
        
        elif msg in ["4", "atendente", "humano", "ajuda"]:
            return await self._handle_human_transfer(phone, name)
        
        elif msg in ["0", "menu", "voltar", "inicio"]:
            return await self._show_main_menu(name)
        
        elif user_state and user_state.get("waiting_for") == "product_query":
            return await self._search_real_products(phone, message, name)
        
        else:
            return await self._show_welcome(name)
    
    async def _increment_metric(self, metric_name: str):
        """Incrementa métrica no Redis."""
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            key = f"whatsapp:metrics:{today}:{metric_name}"
            await self.cache.increment(key)
        except Exception as e:
            logger.warning(f"Failed to increment metric {metric_name}: {e}")
    
    async def _show_welcome(self, name: str) -> Dict[str, Any]:
        """Mostra mensagem de boas-vindas."""
        response = f"""👋 Olá, {name}! Bem-vindo ao *TikTrend Finder*!

Sou seu assistente virtual para encontrar os melhores preços. 🛒💰

*O que você gostaria de fazer?*

1️⃣ 🔍 *Buscar Produtos* - Encontre as melhores ofertas
2️⃣ 📊 *Comparar Preços* - Compare entre lojas
3️⃣ 🔔 *Alertas de Preço* - Receba notificações
4️⃣ 👤 *Falar com Atendente* - Suporte humano

Digite o *número* da opção ou escreva sua dúvida!"""

        return {"text": response, "action": "welcome"}
    
    async def _show_main_menu(self, name: str) -> Dict[str, Any]:
        """Mostra menu principal."""
        response = """📋 *Menu Principal*

1️⃣ 🔍 Buscar Produtos
2️⃣ 📊 Comparar Preços
3️⃣ 🔔 Alertas de Preço
4️⃣ 👤 Falar com Atendente

Digite o número da opção desejada."""

        return {"text": response, "action": "menu"}
    
    async def _handle_product_search_start(self, phone: str, name: str) -> Dict[str, Any]:
        """Inicia fluxo de busca de produtos."""
        
        await self.cache.set(
            f"chatbot:state:{phone}",
            {"waiting_for": "product_query", "timestamp": datetime.now(timezone.utc).isoformat()},
            ttl=300
        )
        
        response = f"""🔍 *Busca de Produtos*

{name}, o que você está procurando?

Digite o nome do produto, categoria ou marca.

_Exemplos:_
• fone bluetooth
• carregador portátil
• smartwatch

💡 Ou digite *0* para voltar ao menu."""

        return {"text": response, "action": "await_query"}
    
    async def _search_real_products(self, phone: str, query: str, name: str) -> Dict[str, Any]:
        """Busca produtos REAIS no banco de dados."""
        
        await self.cache.delete(f"chatbot:state:{phone}")
        await self._increment_metric("product_searches")
        
        try:
            # Busca no banco de dados real usando ScraperOrchestrator
            result = await self.scraper.search_products(
                query=query,
                page=1,
                per_page=5
            )
            
            products = result.get("products", [])
            total = result.get("total", 0)
            
            if products:
                products_text = ""
                for i, p in enumerate(products[:5], 1):
                    price = p.get("price", 0)
                    original_price = p.get("original_price")
                    rating = p.get("rating", 0)
                    sales = p.get("sales_count", 0)
                    shop = p.get("shop_name", "Loja")
                    
                    # Calculate discount
                    discount = ""
                    if original_price and original_price > price:
                        disc_pct = int(((original_price - price) / original_price) * 100)
                        discount = f"🏷️ -{disc_pct}%"
                    
                    products_text += f"""
*{i}. {p.get('title', 'Produto')[:50]}*
💰 R$ {price:.2f} {discount}
⭐ {rating:.1f} | 🛒 {sales:,} vendas
🏪 {shop}
"""
                
                response = f"""🔎 Encontrei *{total}* produtos para "{query}":

{products_text}
📱 Acesse nosso app para ver mais detalhes e comprar!

*Digite:*
• *1* para nova busca
• *0* para voltar ao menu"""

                await self._increment_metric("products_found")
                return {"text": response, "action": "products_found", "products": products}
            
            else:
                # Busca nos trending se não encontrar
                trending = await self.scraper.get_trending_products(page=1, per_page=3)
                trending_products = trending.get("products", [])
                
                suggestion_text = ""
                if trending_products:
                    suggestion_text = "\n\n🔥 *Produtos em Alta:*\n"
                    for p in trending_products[:3]:
                        suggestion_text += f"• {p.get('title', '')[:40]}\n"
                
                response = f"""😔 Não encontrei produtos para "{query}".
{suggestion_text}
*Tente:*
• Usar palavras-chave diferentes
• Verificar a ortografia
• Buscar por categoria

Digite *1* para tentar novamente ou *0* para o menu."""

                return {"text": response, "action": "no_results"}
                
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return {
                "text": "😔 Desculpe, ocorreu um erro na busca. Tente novamente em alguns segundos.",
                "action": "error"
            }
    
    async def _handle_price_comparison(self, phone: str, name: str) -> Dict[str, Any]:
        """Mostra comparação de preços."""
        
        try:
            # Busca produtos com maior desconto
            result = await self.scraper.get_products(
                page=1,
                per_page=5,
                sort_by="trending_score",
                sort_order="desc"
            )
            
            products = result.get("products", [])
            
            if products:
                comparison_text = ""
                for p in products[:5]:
                    price = p.get("price", 0)
                    original = p.get("original_price", price)
                    if original and original > price:
                        saving = original - price
                        comparison_text += f"""
• *{p.get('title', '')[:35]}*
  De ~~R${original:.2f}~~ por R${price:.2f}
  💰 Economia: R${saving:.2f}
"""
                
                response = f"""📊 *Comparação de Preços*

{name}, encontrei as melhores ofertas do momento:
{comparison_text}
🔥 Preços atualizados em tempo real!

*Opções:*
• *1* - Buscar produto específico
• *0* - Voltar ao menu"""

            else:
                response = """📊 *Comparação de Preços*

No momento não temos produtos em promoção.
Volte mais tarde para conferir as ofertas!

Digite *0* para voltar ao menu."""

        except Exception as e:
            logger.error(f"Error in price comparison: {e}")
            response = "😔 Erro ao buscar comparações. Digite *0* para voltar ao menu."
        
        return {"text": response, "action": "comparison"}
    
    async def _handle_alerts(self, phone: str, name: str) -> Dict[str, Any]:
        """Gerencia alertas de preço."""
        
        # Busca alertas do usuário no Redis
        alerts_key = f"user:alerts:{phone}"
        user_alerts = await self.cache.get(alerts_key) or []
        
        if user_alerts:
            alerts_text = ""
            for a in user_alerts[:5]:
                alerts_text += f"• {a.get('product', 'Produto')} - R${a.get('target_price', 0):.2f}\n"
            
            response = f"""🔔 *Seus Alertas de Preço*

{name}, você tem {len(user_alerts)} alertas ativos:

{alerts_text}
_Você será notificado quando o preço atingir sua meta!_

*Opções:*
• Digite o nome de um produto para criar novo alerta
• *0* - Voltar ao menu"""
        else:
            response = f"""🔔 *Alertas de Preço*

{name}, você ainda não tem alertas configurados.

Para criar um alerta, digite o nome do produto e o preço desejado.

_Exemplo: "fone bluetooth 50"_

💡 Você será notificado quando o preço baixar!

*0* - Voltar ao menu"""

        return {"text": response, "action": "alerts"}
    
    async def _handle_human_transfer(self, phone: str, name: str) -> Dict[str, Any]:
        """Transfere para atendente humano."""
        
        await self._increment_metric("human_transfers")
        
        response = f"""👤 *Transferência para Atendente*

{name}, estou transferindo você para um de nossos atendentes.

⏰ *Horário de atendimento:*
Segunda a Sexta: 9h às 18h
Sábado: 9h às 13h

Aguarde um momento, você será atendido em breve!

_Se preferir, continue navegando pelo menu:_
*0* - Voltar ao menu"""

        return {
            "text": response,
            "action": "transfer_human",
            "metadata": {"priority": "normal", "department": "support"}
        }


# Singleton
chatbot = RealProductChatbot()


# ============================================
# WEBHOOK ROUTES
# ============================================

@router.post("/evolution")
async def evolution_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Webhook principal para receber eventos da Evolution API.
    
    Eventos suportados:
    - MESSAGES_UPSERT: Nova mensagem recebida
    - MESSAGES_UPDATE: Mensagem atualizada (lida, entregue)
    - CONNECTION_UPDATE: Status da conexão
    """
    try:
        body = await request.json()
        event = body.get("event", "")
        instance = body.get("instance", "")
        data = body.get("data", {})
        
        logger.info(f"Evolution webhook received: {event} for instance {instance}")
        
        if event == "MESSAGES_UPSERT":
            # Processar mensagem em background para não bloquear
            background_tasks.add_task(
                process_incoming_message,
                data,
                instance
            )
            return {"status": "processing", "event": event}
        
        elif event == "CONNECTION_UPDATE":
            state = data.get("state", "unknown")
            logger.info(f"Connection update: {state}")
            
            # Salva estado no cache
            await cache.set(
                f"whatsapp:connection:{instance}",
                {"state": state, "updated_at": datetime.now(timezone.utc).isoformat()},
                ttl=3600
            )
            return {"status": "ok", "state": state}
        
        elif event == "MESSAGES_UPDATE":
            # Atualização de status (lida, entregue)
            logger.debug(f"Message update: {data}")
            return {"status": "ok", "event": event}
        
        return {"status": "ignored", "event": event}
        
    except Exception as e:
        logger.error(f"Error processing Evolution webhook: {e}")
        return {"status": "error", "message": str(e)}


async def process_incoming_message(data: Dict[str, Any], instance: str):
    """
    Processa mensagem recebida e envia resposta automática.
    Executado em background para não bloquear o webhook.
    """
    try:
        # Extrair dados da mensagem
        key = data.get("key", {})
        remote_jid = key.get("remoteJid", "")
        from_me = key.get("fromMe", False)
        message_id = key.get("id", "")
        
        # Ignorar mensagens enviadas por nós
        if from_me:
            logger.debug(f"Ignoring own message: {message_id}")
            return
        
        # Ignorar grupos por enquanto
        if "@g.us" in remote_jid:
            logger.debug(f"Ignoring group message: {remote_jid}")
            return
        
        # Extrair número de telefone
        phone = remote_jid.replace("@s.whatsapp.net", "")
        
        # Extrair conteúdo da mensagem
        message_content = data.get("message", {})
        push_name = data.get("pushName", "")
        
        # Extrair texto (suporta diferentes tipos)
        text = None
        if "conversation" in message_content:
            text = message_content["conversation"]
        elif "extendedTextMessage" in message_content:
            text = message_content["extendedTextMessage"].get("text", "")
        elif "imageMessage" in message_content:
            text = message_content["imageMessage"].get("caption", "imagem")
        elif "audioMessage" in message_content:
            text = "audio"
        elif "documentMessage" in message_content:
            text = "documento"
        
        if not text:
            logger.debug(f"No text content in message from {phone}")
            return
        
        logger.info(f"Processing message from {phone}: {text[:50]}...")
        
        # Processa com o chatbot
        response = await chatbot.process_message(
            phone=phone,
            message=text,
            push_name=push_name
        )
        
        # Envia resposta via Evolution API
        await send_whatsapp_message(
            instance=instance,
            phone=phone,
            text=response["text"]
        )
        
        # Salva interação para analytics
        await save_interaction(phone, text, response)
        
        logger.info(f"Response sent to {phone}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")


async def send_whatsapp_message(instance: str, phone: str, text: str):
    """Envia mensagem via Evolution API."""
    try:
        url = f"{EVOLUTION_API_URL}/message/sendText/{instance}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                headers={
                    "apikey": EVOLUTION_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "number": phone,
                    "textMessage": {
                        "text": text
                    }
                }
            )
            
            if response.status_code == 200 or response.status_code == 201:
                logger.info(f"Message sent successfully to {phone}")
                await cache.increment(f"whatsapp:metrics:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}:messages_sent")
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")


async def save_interaction(phone: str, user_message: str, bot_response: Dict[str, Any]):
    """Salva interação no banco para analytics."""
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Incrementa métricas no Redis
        await cache.increment(f"whatsapp:metrics:{today}:total_interactions")
        
        # Salva conversa recente
        conversation_key = f"whatsapp:conversation:{phone}"
        conversation = await cache.get(conversation_key) or []
        
        conversation.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_message": user_message[:500],
            "bot_action": bot_response.get("action", "unknown")
        })
        
        # Mantém apenas últimas 50 mensagens
        conversation = conversation[-50:]
        
        await cache.set(conversation_key, conversation, ttl=86400 * 7)  # 7 dias
        
        # Atualiza lista de contatos ativos
        contacts_key = f"whatsapp:active_contacts:{today}"
        await cache.sadd(contacts_key, phone)
        
    except Exception as e:
        logger.warning(f"Error saving interaction: {e}")


# ============================================
# UTILITY ROUTES
# ============================================

@router.get("/status")
async def webhook_status():
    """Status do webhook e conexão WhatsApp."""
    try:
        # Verifica conexão
        connection = await cache.get(f"whatsapp:connection:{EVOLUTION_INSTANCE}")
        
        # Métricas do dia
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        received = await cache.get(f"whatsapp:metrics:{today}:messages_received") or 0
        sent = await cache.get(f"whatsapp:metrics:{today}:messages_sent") or 0
        
        return {
            "status": "healthy",
            "instance": EVOLUTION_INSTANCE,
            "connection": connection,
            "today_metrics": {
                "messages_received": received,
                "messages_sent": sent
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/test")
async def test_chatbot(phone: str, message: str, push_name: str = "Teste"):
    """Endpoint de teste do chatbot (sem enviar WhatsApp real)."""
    try:
        response = await chatbot.process_message(
            phone=phone,
            message=message,
            push_name=push_name
        )
        return {
            "success": True,
            "response": response
        }
    except Exception as e:
        logger.error(f"Test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
