#!/usr/bin/env python3
"""
Script para importar/atualizar workflow do Seller Bot Profissional no n8n.

Uso:
    python import_seller_bot_workflow.py
    
Requisitos:
    - N8N_API_URL configurado no .env
    - N8N_API_KEY configurado no .env
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

N8N_API_URL = os.getenv("N8N_API_URL", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

# Path do workflow
WORKFLOW_FILE = Path(__file__).parent / "data" / "n8n_workflows" / "professional_seller_bot.json"


async def import_workflow():
    """Importa ou atualiza o workflow no n8n."""
    
    if not N8N_API_KEY:
        print("❌ N8N_API_KEY não configurada!")
        sys.exit(1)
    
    if not WORKFLOW_FILE.exists():
        print(f"❌ Arquivo não encontrado: {WORKFLOW_FILE}")
        sys.exit(1)
    
    # Ler workflow
    with open(WORKFLOW_FILE) as f:
        workflow_data = json.load(f)
    
    workflow_name = workflow_data.get("name", "Unnamed Workflow")
    print(f"📦 Importando workflow: {workflow_name}")
    
    headers = {
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Verificar se workflow já existe
        print("🔍 Verificando workflows existentes...")
        
        resp = await client.get(
            f"{N8N_API_URL}/api/v1/workflows",
            headers=headers
        )
        
        if resp.status_code != 200:
            print(f"❌ Erro ao listar workflows: {resp.status_code}")
            print(resp.text)
            sys.exit(1)
        
        existing_workflows = resp.json().get("data", [])
        existing_id = None
        
        for wf in existing_workflows:
            if wf.get("name") == workflow_name:
                existing_id = wf.get("id")
                print(f"✅ Workflow encontrado: {existing_id}")
                break
        
        # 2. Criar ou atualizar
        if existing_id:
            print(f"🔄 Atualizando workflow {existing_id}...")
            
            resp = await client.patch(
                f"{N8N_API_URL}/api/v1/workflows/{existing_id}",
                headers=headers,
                json=workflow_data
            )
            
            if resp.status_code == 200:
                print(f"✅ Workflow atualizado com sucesso!")
            else:
                print(f"❌ Erro ao atualizar: {resp.status_code}")
                print(resp.text)
                sys.exit(1)
        else:
            print("📝 Criando novo workflow...")
            
            resp = await client.post(
                f"{N8N_API_URL}/api/v1/workflows",
                headers=headers,
                json=workflow_data
            )
            
            if resp.status_code == 200:
                new_id = resp.json().get("id")
                print(f"✅ Workflow criado: {new_id}")
            else:
                print(f"❌ Erro ao criar: {resp.status_code}")
                print(resp.text)
                sys.exit(1)
        
        # 3. Ativar workflow
        workflow_id = existing_id or resp.json().get("id")
        
        print(f"⚡ Ativando workflow {workflow_id}...")
        
        resp = await client.patch(
            f"{N8N_API_URL}/api/v1/workflows/{workflow_id}",
            headers=headers,
            json={"active": True}
        )
        
        if resp.status_code == 200:
            print("✅ Workflow ativado!")
        else:
            print(f"⚠️ Erro ao ativar (pode precisar ativar manualmente)")
        
        # 4. Mostrar informações
        print("\n" + "="*50)
        print("📋 RESUMO DO WORKFLOW")
        print("="*50)
        print(f"Nome: {workflow_name}")
        print(f"ID: {workflow_id}")
        print(f"\n🔗 Webhooks disponíveis:")
        print(f"  - POST {N8N_API_URL}/webhook/seller-bot")
        print(f"  - POST {N8N_API_URL}/webhook/seller-bot/product-alert")
        print(f"  - POST {N8N_API_URL}/webhook/seller-bot/daily-report")
        print("\n⚙️ Variáveis de ambiente necessárias:")
        print("  - DIDIN_API_URL: URL da API TikTrend Finder")
        print("  - DIDIN_API_KEY: API Key da TikTrend Finder")
        print("  - CHATWOOT_URL: URL do Chatwoot")
        print("  - CHATWOOT_ACCOUNT_ID: ID da conta Chatwoot")
        print("  - CHATWOOT_API_TOKEN: Token API do Chatwoot")
        print("  - EVOLUTION_API_URL: URL da Evolution API")
        print("  - EVOLUTION_INSTANCE: Nome da instância")
        print("  - EVOLUTION_API_KEY: API Key da Evolution")
        print("="*50)


if __name__ == "__main__":
    asyncio.run(import_workflow())
