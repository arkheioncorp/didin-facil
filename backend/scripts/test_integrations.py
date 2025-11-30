#!/usr/bin/env python3
"""
Script de Teste de Integrações
===============================
Valida conectividade e configuração das APIs externas.

Uso:
    python -m scripts.test_integrations
    python -m scripts.test_integrations --only whatsapp
    python -m scripts.test_integrations --verbose
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import argparse

import httpx

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import settings


class Status(Enum):
    OK = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    SKIP = "⏭️"


@dataclass
class TestResult:
    name: str
    status: Status
    message: str
    details: Optional[dict] = None


async def test_evolution_api() -> TestResult:
    """Testa conexão com Evolution API (WhatsApp)."""
    if not settings.EVOLUTION_API_URL or not settings.EVOLUTION_API_KEY:
        return TestResult(
            name="Evolution API",
            status=Status.SKIP,
            message="Variáveis EVOLUTION_API_URL/KEY não configuradas"
        )
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Tentar endpoint de instâncias
            response = await client.get(
                f"{settings.EVOLUTION_API_URL}/instance/fetchInstances",
                headers={"apikey": settings.EVOLUTION_API_KEY}
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else 0
                    return TestResult(
                        name="Evolution API",
                        status=Status.OK,
                        message=f"Conectado ({count} instâncias)",
                        details=data if isinstance(data, dict) else None
                    )
                except ValueError:
                    return TestResult(
                        name="Evolution API",
                        status=Status.WARNING,
                        message="Resposta não-JSON (servidor pode estar em manutenção)"
                    )
            elif response.status_code == 401:
                return TestResult(
                    name="Evolution API",
                    status=Status.ERROR,
                    message="API Key inválida"
                )
            else:
                return TestResult(
                    name="Evolution API",
                    status=Status.WARNING,
                    message=f"HTTP {response.status_code}"
                )
    except httpx.ConnectError:
        return TestResult(
            name="Evolution API",
            status=Status.ERROR,
            message="Servidor não acessível"
        )
    except Exception as e:
        return TestResult(
            name="Evolution API",
            status=Status.WARNING,
            message=f"Erro: {str(e)[:50]}"
        )


async def test_chatwoot_api() -> TestResult:
    """Testa conexão com Chatwoot."""
    if not settings.CHATWOOT_API_URL or not settings.CHATWOOT_ACCESS_TOKEN:
        return TestResult(
            name="Chatwoot",
            status=Status.SKIP,
            message="Variáveis CHATWOOT não configuradas"
        )
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.CHATWOOT_API_URL}/api/v1/profile",
                headers={"api_access_token": settings.CHATWOOT_ACCESS_TOKEN}
            )
            
            if response.status_code == 200:
                data = response.json()
                return TestResult(
                    name="Chatwoot",
                    status=Status.OK,
                    message=f"Conectado como {data.get('name', 'N/A')}",
                    details=data
                )
            else:
                return TestResult(
                    name="Chatwoot",
                    status=Status.ERROR,
                    message=f"HTTP {response.status_code}"
                )
    except Exception as e:
        return TestResult(
            name="Chatwoot",
            status=Status.ERROR,
            message=str(e)
        )


async def test_openai_api() -> TestResult:
    """Testa conexão com OpenAI."""
    if not settings.OPENAI_API_KEY:
        return TestResult(
            name="OpenAI",
            status=Status.SKIP,
            message="OPENAI_API_KEY não configurada"
        )
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("data", []))
                return TestResult(
                    name="OpenAI",
                    status=Status.OK,
                    message=f"Conectado ({model_count} modelos disponíveis)"
                )
            elif response.status_code == 401:
                return TestResult(
                    name="OpenAI",
                    status=Status.ERROR,
                    message="API Key inválida"
                )
            else:
                return TestResult(
                    name="OpenAI",
                    status=Status.ERROR,
                    message=f"HTTP {response.status_code}"
                )
    except Exception as e:
        return TestResult(
            name="OpenAI",
            status=Status.ERROR,
            message=str(e)
        )


async def test_mercadopago_api() -> TestResult:
    """Testa conexão com Mercado Pago."""
    token = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', None) or \
            getattr(settings, 'MP_ACCESS_TOKEN', None)
    
    if not token:
        return TestResult(
            name="Mercado Pago",
            status=Status.SKIP,
            message="MP_ACCESS_TOKEN não configurado"
        )
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.mercadopago.com/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return TestResult(
                    name="Mercado Pago",
                    status=Status.OK,
                    message=f"Conta: {data.get('nickname', 'N/A')}",
                    details={"id": data.get("id"), "nickname": data.get("nickname")}
                )
            else:
                return TestResult(
                    name="Mercado Pago",
                    status=Status.ERROR,
                    message=f"HTTP {response.status_code}"
                )
    except Exception as e:
        return TestResult(
            name="Mercado Pago",
            status=Status.ERROR,
            message=str(e)
        )


async def test_google_oauth() -> TestResult:
    """Testa configuração do Google OAuth."""
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
    
    if not client_id or not client_secret:
        return TestResult(
            name="Google OAuth",
            status=Status.SKIP,
            message="GOOGLE_CLIENT_ID/SECRET não configurados"
        )
    
    # Não podemos testar OAuth sem flow completo
    # Apenas verificamos se parecem válidos
    if client_id.endswith(".apps.googleusercontent.com"):
        return TestResult(
            name="Google OAuth",
            status=Status.OK,
            message="Client ID parece válido (formato correto)"
        )
    else:
        return TestResult(
            name="Google OAuth",
            status=Status.WARNING,
            message="Client ID não tem formato esperado"
        )


async def test_tiktok_oauth() -> TestResult:
    """Testa configuração do TikTok OAuth."""
    client_key = getattr(settings, 'TIKTOK_CLIENT_KEY', None)
    
    if not client_key:
        return TestResult(
            name="TikTok OAuth",
            status=Status.SKIP,
            message="TIKTOK_CLIENT_KEY não configurado"
        )
    
    return TestResult(
        name="TikTok OAuth",
        status=Status.OK,
        message="Client Key configurada"
    )


async def test_instagram_oauth() -> TestResult:
    """Testa configuração do Instagram OAuth."""
    client_id = getattr(settings, 'INSTAGRAM_CLIENT_ID', None)
    
    if not client_id:
        return TestResult(
            name="Instagram OAuth",
            status=Status.SKIP,
            message="INSTAGRAM_CLIENT_ID não configurado"
        )
    
    return TestResult(
        name="Instagram OAuth",
        status=Status.OK,
        message="Client ID configurada"
    )


async def test_redis() -> TestResult:
    """Testa conexão com Redis."""
    redis_url = getattr(settings, 'REDIS_URL', None)
    
    if not redis_url:
        return TestResult(
            name="Redis",
            status=Status.SKIP,
            message="REDIS_URL não configurada"
        )
    
    try:
        import redis.asyncio as redis
        client = redis.from_url(redis_url)
        await client.ping()
        info = await client.info("server")
        await client.close()
        
        return TestResult(
            name="Redis",
            status=Status.OK,
            message=f"Versão {info.get('redis_version', 'N/A')}",
            details={"version": info.get("redis_version")}
        )
    except ImportError:
        return TestResult(
            name="Redis",
            status=Status.WARNING,
            message="redis package não instalado"
        )
    except Exception as e:
        return TestResult(
            name="Redis",
            status=Status.ERROR,
            message=str(e)
        )


async def test_database() -> TestResult:
    """Testa conexão com PostgreSQL."""
    db_url = getattr(settings, 'DATABASE_URL', None)
    
    if not db_url:
        return TestResult(
            name="PostgreSQL",
            status=Status.SKIP,
            message="DATABASE_URL não configurada"
        )
    
    try:
        import asyncpg
        
        # Parse connection string
        conn = await asyncpg.connect(db_url)
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        
        return TestResult(
            name="PostgreSQL",
            status=Status.OK,
            message="Conectado",
            details={"version": version[:50] if version else None}
        )
    except ImportError:
        return TestResult(
            name="PostgreSQL",
            status=Status.WARNING,
            message="asyncpg não instalado"
        )
    except Exception as e:
        return TestResult(
            name="PostgreSQL",
            status=Status.ERROR,
            message=str(e)
        )


async def test_n8n() -> TestResult:
    """Testa conexão com n8n."""
    n8n_url = getattr(settings, 'N8N_API_URL', None)
    n8n_key = getattr(settings, 'N8N_API_KEY', None)
    
    if not n8n_url:
        return TestResult(
            name="n8n",
            status=Status.SKIP,
            message="N8N_API_URL não configurada"
        )
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {}
            if n8n_key:
                headers["X-N8N-API-KEY"] = n8n_key
            
            response = await client.get(
                f"{n8n_url}/healthz",
                headers=headers
            )
            
            if response.status_code == 200:
                return TestResult(
                    name="n8n",
                    status=Status.OK,
                    message="Serviço disponível"
                )
            else:
                return TestResult(
                    name="n8n",
                    status=Status.WARNING,
                    message=f"HTTP {response.status_code}"
                )
    except Exception as e:
        return TestResult(
            name="n8n",
            status=Status.ERROR,
            message=str(e)
        )


async def test_mercado_livre_api() -> TestResult:
    """Testa API pública do Mercado Livre."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Usar endpoint de sites que é mais permissivo
            response = await client.get(
                "https://api.mercadolibre.com/sites",
                headers={
                    "User-Agent": "DidinFacil/1.0",
                    "Accept": "application/json",
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return TestResult(
                    name="Mercado Livre API",
                    status=Status.OK,
                    message=f"{len(data)} sites disponíveis (MLB = Brasil)"
                )
            elif response.status_code == 403:
                return TestResult(
                    name="Mercado Livre API",
                    status=Status.WARNING,
                    message="Acesso bloqueado (IP/rate limit) - normal em dev"
                )
            else:
                return TestResult(
                    name="Mercado Livre API",
                    status=Status.ERROR,
                    message=f"HTTP {response.status_code}"
                )
    except Exception as e:
        return TestResult(
            name="Mercado Livre API",
            status=Status.ERROR,
            message=str(e)
        )


async def run_all_tests(only: Optional[str] = None, verbose: bool = False) -> list[TestResult]:
    """Executa todos os testes."""
    
    tests = {
        "database": test_database,
        "redis": test_redis,
        "openai": test_openai_api,
        "mercadopago": test_mercadopago_api,
        "whatsapp": test_evolution_api,
        "chatwoot": test_chatwoot_api,
        "google": test_google_oauth,
        "tiktok": test_tiktok_oauth,
        "instagram": test_instagram_oauth,
        "n8n": test_n8n,
        "mercadolivre": test_mercado_livre_api,
    }
    
    if only:
        if only not in tests:
            print(f"❌ Teste '{only}' não encontrado.")
            print(f"   Disponíveis: {', '.join(tests.keys())}")
            sys.exit(1)
        tests = {only: tests[only]}
    
    results = []
    
    print("\n" + "=" * 60)
    print("🔧 TESTE DE INTEGRAÇÕES - Didin Fácil")
    print("=" * 60 + "\n")
    
    for name, test_fn in tests.items():
        print(f"  Testando {name}...", end=" ", flush=True)
        try:
            result = await test_fn()
            results.append(result)
            print(f"{result.status.value} {result.message}")
            
            if verbose and result.details:
                for k, v in result.details.items():
                    print(f"      └─ {k}: {v}")
        except Exception as e:
            result = TestResult(name=name, status=Status.ERROR, message=str(e))
            results.append(result)
            print(f"❌ Erro: {e}")
    
    return results


def print_summary(results: list[TestResult]):
    """Imprime resumo dos testes."""
    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    
    ok = sum(1 for r in results if r.status == Status.OK)
    error = sum(1 for r in results if r.status == Status.ERROR)
    warning = sum(1 for r in results if r.status == Status.WARNING)
    skip = sum(1 for r in results if r.status == Status.SKIP)
    
    print(f"  ✅ OK:       {ok}")
    print(f"  ❌ Erro:     {error}")
    print(f"  ⚠️  Warning:  {warning}")
    print(f"  ⏭️  Skip:     {skip}")
    print(f"  📊 Total:    {len(results)}")
    
    if error > 0:
        print("\n⚠️  Algumas integrações falharam. Verifique as variáveis de ambiente.")
        return 1
    elif skip == len(results):
        print("\n⚠️  Nenhuma integração configurada. Configure as variáveis de ambiente.")
        return 0
    else:
        print("\n✅ Integrações testadas com sucesso!")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Testa integrações do Didin Fácil")
    parser.add_argument("--only", "-o", help="Testar apenas uma integração")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    parser.add_argument("--list", "-l", action="store_true", help="Lista integrações")
    
    args = parser.parse_args()
    
    if args.list:
        print("\nIntegrações disponíveis:")
        print("  - database    : PostgreSQL")
        print("  - redis       : Redis Cache")
        print("  - openai      : OpenAI API (GPT)")
        print("  - mercadopago : Mercado Pago (Pagamentos)")
        print("  - whatsapp    : Evolution API (WhatsApp)")
        print("  - chatwoot    : Chatwoot (Suporte)")
        print("  - google      : Google OAuth (YouTube)")
        print("  - tiktok      : TikTok OAuth")
        print("  - instagram   : Instagram OAuth")
        print("  - n8n         : n8n (Workflows)")
        print("  - mercadolivre: Mercado Livre API")
        return 0
    
    results = asyncio.run(run_all_tests(only=args.only, verbose=args.verbose))
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())
