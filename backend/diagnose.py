#!/usr/bin/env python3
"""Diagnóstico das integrações do Seller Bot."""
import sys
import os

# Adicionar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

results = []

def log(msg):
    results.append(msg)
    print(msg)

log("=" * 60)
log("DIAGNÓSTICO DAS INTEGRAÇÕES - SELLER BOT")
log("=" * 60)

# 1. Teste de imports
log("\n[1/6] Testando imports dos módulos...")
try:
    from modules.chatbot import ProfessionalSellerBot, ConversationContext, Intent
    log("  ✅ Módulo chatbot importado com sucesso")
except Exception as e:
    log(f"  ❌ Erro no chatbot: {e}")

try:
    from api.routes.seller_bot import router
    log("  ✅ Router seller_bot importado")
except Exception as e:
    log(f"  ❌ Erro no seller_bot router: {e}")

try:
    from modules.crm.services import CRMService
    log("  ✅ CRMService importado")
except Exception as e:
    log(f"  ❌ Erro no CRM: {e}")

# 2. Teste Redis
log("\n[2/6] Testando Redis...")
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    log("  ✅ Redis conectado")
except Exception as e:
    log(f"  ❌ Redis: {e}")

# 3. Teste PostgreSQL
log("\n[3/6] Testando PostgreSQL...")
try:
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        port=5434,
        user='tiktrend',
        password='tiktrend_secret',
        database='tiktrend'
    )
    cur = conn.cursor()
    cur.execute("SELECT 1")
    log("  ✅ PostgreSQL conectado")
    conn.close()
except Exception as e:
    log(f"  ❌ PostgreSQL: {e}")

# 4. Teste n8n
log("\n[4/6] Testando n8n...")
try:
    import urllib.request
    req = urllib.request.Request("http://localhost:5678/healthz")
    resp = urllib.request.urlopen(req, timeout=5)
    log(f"  ✅ n8n: {resp.read().decode()}")
except Exception as e:
    log(f"  ❌ n8n: {e}")

# 5. Teste Chatwoot
log("\n[5/6] Testando Chatwoot...")
try:
    import urllib.request
    req = urllib.request.Request("http://localhost:3000/api")
    resp = urllib.request.urlopen(req, timeout=5)
    data = resp.read().decode()
    log(f"  ✅ Chatwoot: OK (versão encontrada)")
except Exception as e:
    log(f"  ❌ Chatwoot: {e}")

# 6. Teste Evolution API
log("\n[6/6] Testando Evolution API...")
try:
    import urllib.request
    req = urllib.request.Request("http://localhost:8082/")
    resp = urllib.request.urlopen(req, timeout=5)
    log(f"  ✅ Evolution API: responde na porta 8082")
except Exception as e:
    log(f"  ⚠️ Evolution API: {e}")

log("\n" + "=" * 60)
log("DIAGNÓSTICO COMPLETO")
log("=" * 60)

# Salvar resultado
with open("diagnose_result.txt", "w") as f:
    f.write("\n".join(results))
print("\nResultado salvo em diagnose_result.txt")
