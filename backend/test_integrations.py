#!/usr/bin/env python3
"""
Script de teste para verificar todas as integrações do TikTrend Finder.
"""

import asyncio
import os
import sys
from pathlib import Path

# Adicionar backend ao path
sys.path.insert(0, str(Path(__file__).parent))

# Resultados
results = []

def log_result(name: str, success: bool, message: str = ""):
    status = "✅" if success else "❌"
    results.append((name, success, message))
    print(f"{status} {name}: {message}")


async def test_imports():
    """Testa importações dos módulos"""
    print("\n" + "="*50)
    print("📦 TESTANDO IMPORTAÇÕES")
    print("="*50)
    
    # Módulo Chatbot
    try:
        from modules.chatbot import ProfessionalSellerBot, create_seller_bot
        log_result("Chatbot Module", True, "Imports OK")
    except Exception as e:
        log_result("Chatbot Module", False, str(e))
    
    # Channel Integrations
    try:
        from modules.chatbot import ChannelRouter, ChatwootAdapter, EvolutionAdapter
        log_result("Channel Integrations", True, "Imports OK")
    except Exception as e:
        log_result("Channel Integrations", False, str(e))
    
    # CRM
    try:
        from modules.crm import CRMService, ContactService, LeadService
        log_result("CRM Module", True, "Imports OK")
    except Exception as e:
        log_result("CRM Module", False, str(e))
    
    # Analytics
    try:
        from modules.analytics import SocialAnalyticsService
        log_result("Analytics Module", True, "Imports OK")
    except Exception as e:
        log_result("Analytics Module", False, str(e))
    
    # Templates
    try:
        from modules.templates import AutomationTemplateService
        log_result("Templates Module", True, "Imports OK")
    except Exception as e:
        log_result("Templates Module", False, str(e))
    
    # Integrations
    try:
        from integrations.n8n import N8nClient
        from integrations.typebot import TypebotClient
        log_result("N8N/Typebot Integration", True, "Imports OK")
    except Exception as e:
        log_result("N8N/Typebot Integration", False, str(e))
    
    # API Routes
    try:
        from api.routes.seller_bot import router
        log_result("Seller Bot API", True, "Router OK")
    except Exception as e:
        log_result("Seller Bot API", False, str(e))


async def test_n8n_connection():
    """Testa conexão com n8n"""
    print("\n" + "="*50)
    print("🔗 TESTANDO N8N")
    print("="*50)
    
    try:
        import httpx
        from shared.config import settings
        
        api_url = getattr(settings, 'N8N_API_URL', 'http://localhost:5678')
        api_key = getattr(settings, 'N8N_API_KEY', '')
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Health check
            resp = await client.get(f"{api_url}/healthz")
            if resp.status_code == 200:
                log_result("N8N Health", True, resp.json().get('status', 'ok'))
            else:
                log_result("N8N Health", False, f"Status {resp.status_code}")
            
            # API check
            if api_key:
                headers = {"X-N8N-API-KEY": api_key}
                resp = await client.get(f"{api_url}/api/v1/workflows", headers=headers)
                if resp.status_code == 200:
                    workflows = resp.json().get('data', [])
                    log_result("N8N API", True, f"{len(workflows)} workflows")
                else:
                    log_result("N8N API", False, f"Status {resp.status_code}")
            else:
                log_result("N8N API", False, "API Key não configurada")
                
    except Exception as e:
        log_result("N8N Connection", False, str(e))


async def test_chatwoot_connection():
    """Testa conexão com Chatwoot"""
    print("\n" + "="*50)
    print("💬 TESTANDO CHATWOOT")
    print("="*50)
    
    try:
        import httpx
        
        # Usar URL local do docker
        api_url = "http://localhost:3000"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{api_url}/api")
            if resp.status_code == 200:
                data = resp.json()
                log_result("Chatwoot Health", True, f"v{data.get('version', 'unknown')}")
            else:
                log_result("Chatwoot Health", False, f"Status {resp.status_code}")
                
    except Exception as e:
        log_result("Chatwoot Connection", False, str(e))


async def test_redis_connection():
    """Testa conexão com Redis"""
    print("\n" + "="*50)
    print("📮 TESTANDO REDIS")
    print("="*50)
    
    try:
        import redis.asyncio as redis
        
        client = redis.from_url("redis://localhost:6379/0")
        await client.ping()
        log_result("Redis Connection", True, "PONG")
        await client.close()
    except Exception as e:
        log_result("Redis Connection", False, str(e))


async def test_postgres_connection():
    """Testa conexão com PostgreSQL"""
    print("\n" + "="*50)
    print("🐘 TESTANDO POSTGRESQL")
    print("="*50)
    
    try:
        import asyncpg
        
        conn = await asyncpg.connect(
            "postgresql://tiktrend:tiktrend_dev@localhost:5434/tiktrend"
        )
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        log_result("PostgreSQL Connection", True, version.split(",")[0])
    except Exception as e:
        log_result("PostgreSQL Connection", False, str(e))


async def test_evolution_connection():
    """Testa conexão com Evolution API"""
    print("\n" + "="*50)
    print("📱 TESTANDO EVOLUTION API (WHATSAPP)")
    print("="*50)
    
    try:
        import httpx
        
        api_url = "http://localhost:8082"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{api_url}/instance/fetchInstances")
            # 401 é esperado sem API key, mas indica que está rodando
            if resp.status_code in [200, 401]:
                log_result("Evolution API", True, "Rodando (precisa API key)")
            else:
                log_result("Evolution API", False, f"Status {resp.status_code}")
                
    except Exception as e:
        log_result("Evolution API", False, str(e))


async def test_seller_bot():
    """Testa o Seller Bot"""
    print("\n" + "="*50)
    print("🤖 TESTANDO SELLER BOT")
    print("="*50)
    
    try:
        from modules.chatbot import (
            ProfessionalSellerBot,
            IncomingMessage,
            MessageChannel,
            create_seller_bot
        )
        
        # Criar bot
        bot = create_seller_bot()
        log_result("Bot Creation", True, "Instância criada")
        
        # Testar detecção de intent
        from modules.chatbot import IntentDetector
        detector = IntentDetector()
        
        test_messages = [
            ("Olá, bom dia!", "greeting"),
            ("Quero um iPhone barato", "product_search"),
            ("Quanto custa?", "price_check"),
            ("Quero falar com atendente", "talk_to_human"),
        ]
        
        for msg, expected in test_messages:
            result = detector.detect(msg)
            status = result.intent.value == expected
            log_result(
                f"Intent: '{msg[:20]}...'",
                status,
                f"{result.intent.value} (conf: {result.confidence:.2f})"
            )
        
        # Testar processamento de mensagem
        message = IncomingMessage(
            channel=MessageChannel.WEBCHAT,
            sender_id="test_user",
            sender_name="Teste",
            content="Olá, preciso de ajuda"
        )
        
        responses = await bot.process_message(message)
        log_result(
            "Message Processing",
            len(responses) > 0,
            f"{len(responses)} respostas geradas"
        )
        
    except Exception as e:
        import traceback
        log_result("Seller Bot", False, str(e))
        traceback.print_exc()


async def test_api_routes():
    """Testa as rotas da API"""
    print("\n" + "="*50)
    print("🌐 TESTANDO API ROUTES")
    print("="*50)
    
    try:
        from fastapi.testclient import TestClient
        from api.main import app
        
        client = TestClient(app)
        
        # Health check
        resp = client.get("/health")
        log_result("API /health", resp.status_code == 200, resp.json())
        
        # Seller bot health
        resp = client.get("/seller-bot/health")
        if resp.status_code == 200:
            log_result("API /seller-bot/health", True, resp.json().get("status"))
        else:
            log_result("API /seller-bot/health", False, f"Status {resp.status_code}")
        
        # Seller bot stats
        resp = client.get("/seller-bot/stats")
        if resp.status_code == 200:
            log_result("API /seller-bot/stats", True, "Stats OK")
        else:
            log_result("API /seller-bot/stats", False, f"Status {resp.status_code}")
        
        # Test message
        resp = client.post("/seller-bot/message", json={
            "channel": "webchat",
            "sender_id": "test123",
            "content": "Olá!"
        })
        if resp.status_code == 200:
            data = resp.json()
            log_result(
                "API /seller-bot/message",
                True,
                f"{len(data.get('responses', []))} respostas"
            )
        else:
            log_result("API /seller-bot/message", False, resp.text[:100])
            
    except Exception as e:
        import traceback
        log_result("API Routes", False, str(e))
        traceback.print_exc()


async def main():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("🧪 TESTES DE INTEGRAÇÃO - DIDIN FÁCIL")
    print("="*60)
    
    await test_imports()
    await test_postgres_connection()
    await test_redis_connection()
    await test_n8n_connection()
    await test_chatwoot_connection()
    await test_evolution_connection()
    await test_seller_bot()
    await test_api_routes()
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    passed = sum(1 for _, success, _ in results if success)
    failed = sum(1 for _, success, _ in results if not success)
    
    print(f"\n✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    print(f"📈 Taxa de sucesso: {passed/(passed+failed)*100:.1f}%")
    
    if failed > 0:
        print("\n⚠️ Testes que falharam:")
        for name, success, msg in results:
            if not success:
                print(f"   - {name}: {msg}")
    
    print("\n" + "="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
