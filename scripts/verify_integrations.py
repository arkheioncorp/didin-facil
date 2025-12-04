import sys
import os
import asyncio
import json
import requests
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from shared.config import settings

async def verify_whatsapp():
    print("\n📱 Verificando WhatsApp (Evolution API)...")
    url = f"{settings.EVOLUTION_API_URL}/instance/fetchInstances"
    headers = {"apikey": settings.EVOLUTION_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            instances = response.json()
            if isinstance(instances, list) and len(instances) > 0:
                print(f"✅ {len(instances)} instância(s) encontrada(s):")
                for inst in instances:
                    name = inst.get('name') or inst.get('instance', {}).get('instanceName')
                    status = inst.get('connectionStatus') or inst.get('instance', {}).get('status')
                    print(f"  - Nome: {name} | Status: {status}")
            else:
                print("❌ Nenhuma instância do WhatsApp encontrada.")
        else:
            print(f"❌ Erro ao conectar na Evolution API: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro de conexão com WhatsApp: {str(e)}")

async def verify_youtube():
    print("\n🎥 Verificando YouTube...")
    creds_path = Path("backend/data/youtube_credentials.json")
    if creds_path.exists():
        try:
            with open(creds_path) as f:
                data = json.load(f)
                if 'installed' in data or 'web' in data:
                    print("✅ Credenciais do YouTube encontradas e válidas (JSON).")
                else:
                    print("❌ Arquivo de credenciais do YouTube inválido.")
        except Exception as e:
            print(f"❌ Erro ao ler credenciais do YouTube: {str(e)}")
    else:
        print(f"❌ Arquivo não encontrado: {creds_path}")

async def verify_tiktok():
    print("\n🎵 Verificando TikTok...")
    session_dir = Path("backend/data/tiktok_sessions")
    if session_dir.exists():
        files = list(session_dir.glob("*_main.json"))
        if files:
            print(f"✅ {len(files)} sessão(ões) do TikTok encontrada(s).")
            for f in files:
                try:
                    with open(f) as json_file:
                        json.load(json_file)
                    print(f"  - {f.name}: JSON Válido")
                except:
                    print(f"  - {f.name}: ❌ JSON Inválido")
        else:
            print("❌ Nenhuma sessão do TikTok encontrada.")
    else:
        print("❌ Diretório de sessões do TikTok não encontrado.")

async def verify_instagram():
    print("\n📸 Verificando Instagram...")
    if settings.INSTAGRAM_USERNAME and settings.INSTAGRAM_PASSWORD:
        print(f"✅ Credenciais configuradas para usuário: {settings.INSTAGRAM_USERNAME}")
    else:
        print("❌ Credenciais do Instagram ausentes no .env")

async def main():
    print("🚀 Iniciando Verificação de Integrações do TikTrend Finder\n")
    await verify_whatsapp()
    await verify_youtube()
    await verify_tiktok()
    await verify_instagram()
    print("\n🏁 Verificação concluída.")

if __name__ == "__main__":
    asyncio.run(main())
