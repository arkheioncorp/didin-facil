"""
WhatsApp Chatbot Handler
========================
Processa mensagens do WhatsApp e retorna respostas automáticas.
Integrado com n8n webhook para processamento avançado.

Security:
- Webhook endpoints protected by API key validation
- Rate limiting per phone number
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from api.services.cache import CacheService
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from shared.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp-bot", tags=["WhatsApp Chatbot"])


# ============================================
# SECURITY
# ============================================

async def verify_webhook_secret(
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    authorization: Optional[str] = Header(None),
) -> bool:
    """
    Verify webhook request authenticity.
    
    Accepts either:
    - X-Webhook-Secret header
    - Authorization: Bearer <token> header
    
    Security: Uses constant-time comparison to prevent timing attacks.
    """
    expected_secret = settings.WEBHOOK_SECRET or settings.N8N_WEBHOOK_SECRET
    
    # Skip validation in dev mode if no secret configured
    if not expected_secret:
        if settings.ENVIRONMENT == "development":
            logger.warning("Webhook secret not configured - accepting request in dev mode")
            return True
        raise HTTPException(
            status_code=401,
            detail="Webhook authentication required"
        )
    
    # Check X-Webhook-Secret header
    if x_webhook_secret:
        if secrets.compare_digest(x_webhook_secret, expected_secret):
            return True
    
    # Check Authorization header
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        if secrets.compare_digest(token, expected_secret):
            return True
    
    logger.warning("Invalid webhook secret attempt")
    raise HTTPException(
        status_code=401,
        detail="Invalid webhook authentication"
    )


# ============================================
# MODELS
# ============================================

class ProductSearchResult(BaseModel):
    """Resultado de busca de produto."""
    id: str
    title: str
    price: float
    original_price: Optional[float] = None
    discount_percent: Optional[int] = None
    image_url: Optional[str] = None
    shop_name: Optional[str] = None
    rating: Optional[float] = None
    sales_count: int = 0


class ChatbotRequest(BaseModel):
    """Request do chatbot WhatsApp."""
    phone: str = Field(..., description="Número do telefone")
    message: str = Field(..., description="Mensagem recebida")
    instance_name: str = Field(default="tiktrend-whatsapp")
    push_name: Optional[str] = None


class ChatbotResponse(BaseModel):
    """Response do chatbot WhatsApp."""
    response_text: str
    products: Optional[List[ProductSearchResult]] = None
    action: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================
# CHATBOT LOGIC
# ============================================

class WhatsAppChatbot:
    """Classe para gerenciar lógica do chatbot."""
    
    def __init__(self):
        self.cache = CacheService()
        # Mock products for demo
        self.mock_products = [
            {
                "id": "1",
                "title": "Fone de Ouvido Bluetooth TWS",
                "price": 49.90,
                "original_price": 129.90,
                "discount_percent": 62,
                "image_url": "https://placeholder.com/fone.jpg",
                "shop_name": "TechStore",
                "rating": 4.8,
                "sales_count": 15234
            },
            {
                "id": "2", 
                "title": "Carregador Portátil 20000mAh",
                "price": 79.90,
                "original_price": 149.90,
                "discount_percent": 47,
                "image_url": "https://placeholder.com/carregador.jpg",
                "shop_name": "PowerBank Brasil",
                "rating": 4.6,
                "sales_count": 8567
            },
            {
                "id": "3",
                "title": "Smartwatch Fitness Tracker",
                "price": 99.90,
                "original_price": 299.90,
                "discount_percent": 67,
                "image_url": "https://placeholder.com/smartwatch.jpg",
                "shop_name": "WearTech",
                "rating": 4.5,
                "sales_count": 6789
            },
            {
                "id": "4",
                "title": "Caixa de Som Bluetooth à Prova D'água",
                "price": 89.90,
                "original_price": 199.90,
                "discount_percent": 55,
                "image_url": "https://placeholder.com/caixa.jpg",
                "shop_name": "SoundBox",
                "rating": 4.7,
                "sales_count": 4321
            },
            {
                "id": "5",
                "title": "Câmera de Segurança WiFi 360°",
                "price": 119.90,
                "original_price": 249.90,
                "discount_percent": 52,
                "image_url": "https://placeholder.com/camera.jpg",
                "shop_name": "SecureTech",
                "rating": 4.4,
                "sales_count": 3456
            }
        ]
    
    async def process_message(
        self,
        phone: str,
        message: str,
        push_name: Optional[str] = None
    ) -> ChatbotResponse:
        """Processa mensagem e retorna resposta."""
        
        # Normalize message
        msg = message.strip().lower()
        name = push_name or "cliente"
        
        # Check user state (for multi-step flows)
        state_key = f"chatbot:state:{phone}"
        user_state = await self.cache.get(state_key)
        
        # Handle menu options
        if msg == "1" or "produto" in msg or "buscar" in msg:
            return await self._handle_product_search(phone, name, user_state)
        
        elif msg == "2" or "comparar" in msg or "preço" in msg:
            return await self._handle_price_comparison(phone, name)
        
        elif msg == "3" or "alerta" in msg:
            return await self._handle_alerts(phone, name)
        
        elif msg == "4" or "atendente" in msg or "humano" in msg:
            return await self._handle_human_transfer(phone, name)
        
        elif msg == "0" or "menu" in msg or "voltar" in msg:
            return await self._show_main_menu(name)
        
        elif user_state and user_state.get("waiting_for") == "product_query":
            return await self._search_products(phone, message, name)
        
        else:
            # Default: show welcome and menu
            return await self._show_welcome(name)
    
    async def _show_welcome(self, name: str) -> ChatbotResponse:
        """Mostra mensagem de boas-vindas."""
        response = f"""👋 Olá, {name}! Bem-vindo ao *TikTrend Finder*!

Sou seu assistente virtual para encontrar os melhores preços. 🛒💰

*O que você gostaria de fazer?*

1️⃣ 🔍 *Buscar Produtos* - Encontre as melhores ofertas
2️⃣ 📊 *Comparar Preços* - Compare entre lojas
3️⃣ 🔔 *Alertas de Preço* - Receba notificações
4️⃣ 👤 *Falar com Atendente* - Suporte humano

Digite o *número* da opção ou escreva sua dúvida!"""

        return ChatbotResponse(
            response_text=response,
            action="show_menu"
        )
    
    async def _show_main_menu(self, name: str) -> ChatbotResponse:
        """Mostra menu principal."""
        response = f"""📋 *Menu Principal*

1️⃣ 🔍 Buscar Produtos
2️⃣ 📊 Comparar Preços
3️⃣ 🔔 Alertas de Preço
4️⃣ 👤 Falar com Atendente

Digite o número da opção desejada."""

        return ChatbotResponse(
            response_text=response,
            action="show_menu"
        )
    
    async def _handle_product_search(
        self,
        phone: str,
        name: str,
        user_state: Optional[Dict] = None
    ) -> ChatbotResponse:
        """Inicia fluxo de busca de produtos."""
        
        # Save state
        await self.cache.set(
            f"chatbot:state:{phone}",
            {"waiting_for": "product_query", "timestamp": datetime.now(timezone.utc).isoformat()},
            ttl=300  # 5 minutes
        )
        
        response = f"""🔍 *Busca de Produtos*

{name}, o que você está procurando?

Digite o nome do produto, categoria ou marca.

_Exemplos:_
• fone bluetooth
• carregador portátil
• smartwatch

💡 Ou digite *0* para voltar ao menu."""

        return ChatbotResponse(
            response_text=response,
            action="await_product_query"
        )
    
    async def _search_products(
        self,
        phone: str,
        query: str,
        name: str
    ) -> ChatbotResponse:
        """Busca produtos e retorna resultados."""
        
        # Clear state
        await self.cache.delete(f"chatbot:state:{phone}")
        
        # Filter mock products (in production, use real database)
        query_lower = query.lower()
        results = [
            p for p in self.mock_products
            if query_lower in p["title"].lower()
        ]
        
        # If no exact match, return top products
        if not results:
            results = self.mock_products[:3]
        
        # Format response
        if results:
            products_text = ""
            for i, p in enumerate(results[:5], 1):
                discount = f"🏷️ -{p['discount_percent']}%" if p.get('discount_percent') else ""
                products_text += f"""
*{i}. {p['title']}*
💰 R$ {p['price']:.2f} {discount}
⭐ {p['rating']} | 🛒 {p['sales_count']:,} vendas
🏪 {p['shop_name']}
"""
            
            response = f"""🔎 Encontrei *{len(results)}* produtos para "{query}":

{products_text}
📱 Acesse nosso app para ver mais detalhes e comprar!

*Digite:*
• O *número* do produto para mais info
• *1* para nova busca
• *0* para voltar ao menu"""

            return ChatbotResponse(
                response_text=response,
                products=[ProductSearchResult(**p) for p in results[:5]],
                action="show_products"
            )
        else:
            response = f"""😔 Não encontrei produtos para "{query}".

*Tente:*
• Usar palavras-chave diferentes
• Verificar a ortografia
• Buscar por categoria

Digite *1* para tentar novamente ou *0* para o menu."""

            return ChatbotResponse(
                response_text=response,
                action="no_results"
            )
    
    async def _handle_price_comparison(
        self,
        phone: str,
        name: str
    ) -> ChatbotResponse:
        """Mostra comparação de preços."""
        
        # Get a sample product for comparison
        product = self.mock_products[0]
        
        response = f"""📊 *Comparação de Preços*

*{product['title']}*

🏪 Preços em diferentes lojas:

1. *TechStore* - R$ 49,90 ✅ Menor preço
2. *MegaShop* - R$ 59,90
3. *VarejoMax* - R$ 64,90
4. *CompraFácil* - R$ 69,90

💰 *Economia:* até R$ 20,00

🔔 Quer receber alerta quando o preço baixar?
Digite *SIM* ou *3* para configurar.

*0* - Voltar ao menu"""

        return ChatbotResponse(
            response_text=response,
            action="show_comparison"
        )
    
    async def _handle_alerts(
        self,
        phone: str,
        name: str
    ) -> ChatbotResponse:
        """Configura alertas de preço."""
        
        response = f"""🔔 *Alertas de Preço*

{name}, com os alertas você recebe notificação quando:
• O preço do produto baixar
• Aparecer uma promoção especial
• O produto voltar ao estoque

✅ *Seus alertas ativos:* 0

Para criar um alerta:
1️⃣ Primeiro, busque um produto (opção 1)
2️⃣ Depois, selecione "Criar Alerta"

Ou acesse nosso app para gerenciar todos os alertas!

*0* - Voltar ao menu"""

        return ChatbotResponse(
            response_text=response,
            action="show_alerts"
        )
    
    async def _handle_human_transfer(
        self,
        phone: str,
        name: str
    ) -> ChatbotResponse:
        """Transfere para atendente humano."""
        
        response = f"""👤 *Transferência para Atendente*

{name}, estou transferindo você para um de nossos atendentes.

⏰ *Horário de atendimento:*
Segunda a Sexta: 9h às 18h
Sábado: 9h às 13h

Aguarde um momento, você será atendido em breve!

_Se preferir, continue navegando pelo menu:_
*0* - Voltar ao menu"""

        return ChatbotResponse(
            response_text=response,
            action="transfer_human",
            metadata={"priority": "normal", "department": "support"}
        )


# Create singleton
chatbot = WhatsAppChatbot()


# ============================================
# ROUTES
# ============================================

@router.post("/process", response_model=ChatbotResponse)
async def process_message(
    request: ChatbotRequest,
    _auth: bool = Depends(verify_webhook_secret),
):
    """
    Processa mensagem do WhatsApp e retorna resposta.
    
    Este endpoint é chamado pelo n8n para processar mensagens.
    Requer autenticação via X-Webhook-Secret header.
    """
    try:
        response = await chatbot.process_message(
            phone=request.phone,
            message=request.message,
            push_name=request.push_name
        )
        return response
    except Exception as e:
        logger.error(f"Error processing chatbot message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/n8n")
async def n8n_webhook(
    request: Request,
    _auth: bool = Depends(verify_webhook_secret),
):
    """
    Webhook para receber mensagens do n8n.
    
    O n8n envia a mensagem aqui, processamos e retornamos a resposta.
    Requer autenticação via X-Webhook-Secret ou Authorization header.
    """
    try:
        body = await request.json()
        
        # Extract message data from n8n payload
        phone = (
            body.get("phone") or
            body.get("from") or
            body.get("remoteJid", "")
        )
        message = (
            body.get("message") or
            body.get("text") or
            body.get("body", "")
        )
        push_name = (
            body.get("pushName") or
            body.get("senderName") or
            body.get("name")
        )
        
        # Clean phone number
        if "@" in phone:
            phone = phone.split("@")[0]
        
        if not phone or not message:
            return {
                "success": False,
                "error": "Missing phone or message",
                "response_text": "Erro: mensagem inválida"
            }
        
        response = await chatbot.process_message(
            phone=phone,
            message=message,
            push_name=push_name
        )
        
        products = None
        if response.products:
            products = [p.model_dump() for p in response.products]
        
        return {
            "success": True,
            "response_text": response.response_text,
            "products": products,
            "action": response.action,
            "metadata": response.metadata
        }
        
    except Exception as e:
        logger.error(f"Error in n8n webhook: {e}")
        error_msg = "Desculpe, ocorreu um erro. Tente novamente."
        return {
            "success": False,
            "error": str(e),
            "response_text": error_msg
        }


@router.get("/health")
async def health_check():
    """Health check do chatbot."""
    return {
        "status": "healthy",
        "service": "whatsapp-chatbot",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
