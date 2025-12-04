#!/usr/bin/env python3
"""
Test Upload Script
==================

Script para testar upload de vídeos para YouTube e TikTok.

Uso:
    python scripts/test_upload.py --platform youtube --file video.mp4 --account my_account
    python scripts/test_upload.py --platform tiktok --file video.mp4 --account my_account
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime

# Adicionar diretório raiz ao path para importar módulos do backend
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from shared.config import settings
from vendor.tiktok.client import (Privacy, TikTokClient, TikTokConfig,
                                  VideoConfig)
from vendor.youtube.client import (Category, PrivacyStatus, VideoMetadata,
                                   YouTubeClient, YouTubeConfig)


async def run_youtube_upload(file_path: str, account_name: str, user_id: str = "user_123"):
    """Execute YouTube upload test - not a pytest test function."""
    print(f"🎥 Iniciando teste de upload para YouTube (Conta: {account_name})...")

    # Verificar credenciais
    creds_file = os.path.join(settings.DATA_DIR, "youtube_credentials.json")
    tokens_dir = os.path.join(settings.DATA_DIR, "youtube_tokens")
    token_file = os.path.join(tokens_dir, f"{user_id}_{account_name}.json")

    if not os.path.exists(creds_file):
        print(f"❌ Erro: Arquivo de credenciais não encontrado: {creds_file}")
        return

    if not os.path.exists(token_file):
        print(
            f"❌ Erro: Token de autenticação não encontrado para conta '{account_name}'"
        )
        print(f"   Esperado em: {token_file}")
        return

    try:
        config = YouTubeConfig(client_secrets_file=creds_file, token_file=token_file)
        client = YouTubeClient(config)
        await client.authenticate()
        print("✅ Autenticado com sucesso!")

        metadata = VideoMetadata(
            title=f"Test Upload {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description="This is a test upload from Didin Facil automation.",
            tags=["test", "automation"],
            category=Category.HOWTO_STYLE,
            privacy=PrivacyStatus.PRIVATE,
            is_short=False,
        )

        print(f"📤 Enviando arquivo: {file_path}")
        result = await client.upload_video(file_path, metadata)

        if result.success:
            print(f"✅ Upload concluído! Video ID: {result.video_id}")
            print(f"🔗 URL: {result.url}")
        else:
            print(f"❌ Falha no upload: {result.error}")

    except Exception as e:
        print(f"❌ Erro durante execução: {str(e)}")


async def run_tiktok_upload(file_path: str, account_name: str, user_id: str = "user_123"):
    """Execute TikTok upload test - not a pytest test function."""
    print(f"🎵 Iniciando teste de upload para TikTok (Conta: {account_name})...")

    # Verificar sessão
    sessions_dir = os.path.join(settings.DATA_DIR, "tiktok_sessions")
    cookies_file = os.path.join(sessions_dir, f"{user_id}_{account_name}.json")

    if not os.path.exists(cookies_file):
        print(f"❌ Erro: Arquivo de cookies não encontrado para conta '{account_name}'")
        print(f"   Esperado em: {cookies_file}")
        return

    try:
        config = TikTokConfig(cookies_file=cookies_file, headless=True)
        client = TikTokClient(config)

        video_config = VideoConfig(
            caption=f"Test Upload {datetime.now().strftime('%Y-%m-%d %H:%M')} #test #automation",
            privacy=Privacy.PRIVATE,
        )

        print(f"📤 Enviando arquivo: {file_path}")
        result = await client.upload_video(file_path, video_config)

        if result.status.value == "success":
            print(f"✅ Upload concluído! Video ID: {result.video_id}")
            print(f"🔗 URL: {result.url}")
        else:
            print(f"❌ Falha no upload: {result.error}")

    except Exception as e:
        print(f"❌ Erro durante execução: {str(e)}")
    finally:
        # Tentar fechar o driver se foi criado
        try:
            if "client" in locals() and hasattr(client, "_driver") and client._driver:
                client._driver.quit()
        except:
            pass


async def main():
    parser = argparse.ArgumentParser(description="Test Upload Script")
    parser.add_argument(
        "--platform",
        choices=["youtube", "tiktok"],
        required=True,
        help="Platform to test",
    )
    parser.add_argument("--file", required=True, help="Path to video file")
    parser.add_argument(
        "--account",
        required=True,
        help="Account name (used for looking up credentials)",
    )
    parser.add_argument(
        "--user-id",
        default="user_123",
        help="User ID for file lookup (default: user_123)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ Erro: Arquivo de vídeo não encontrado: {args.file}")
        return

    if args.platform == "youtube":
        await run_youtube_upload(args.file, args.account, args.user_id)
    elif args.platform == "tiktok":
        await run_tiktok_upload(args.file, args.account, args.user_id)


if __name__ == "__main__":
    asyncio.run(main())
