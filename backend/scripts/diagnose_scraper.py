#!/usr/bin/env python3
"""
🔍 DIAGNÓSTICO COMPLETO DO SISTEMA DE SCRAPING
Script para verificar todo o workflow de coleta de produtos passo a passo.

Uso: python -m scripts.diagnose_scraper
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text: str):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


async def test_redis_connection():
    """Teste 1: Verificar conexão Redis"""
    print_header("TESTE 1: CONEXÃO REDIS")
    
    try:
        from shared.redis import get_redis
        
        redis = await get_redis()
        await redis.ping()
        print_success("Redis conectado com sucesso!")
        
        # Verificar jobs na fila
        queue_len = await redis.llen("scraper:jobs")
        print_info(f"Jobs pendentes na fila: {queue_len}")
        
        # Verificar status do worker
        worker_status = await redis.get("worker:scraper:status")
        if worker_status:
            print_info(f"Status do worker: {worker_status}")
        else:
            print_warning("Worker status não encontrado (pode não estar rodando)")
        
        return True
    except Exception as e:
        print_error(f"Falha na conexão Redis: {e}")
        return False


async def test_database_connection():
    """Teste 2: Verificar conexão PostgreSQL"""
    print_header("TESTE 2: CONEXÃO POSTGRESQL")
    
    try:
        from api.database.connection import database

        # Conectar
        if not database.is_connected:
            await database.connect()
        
        # Testar query
        result = await database.fetch_one("SELECT COUNT(*) as count FROM products")
        product_count = result["count"] if result else 0
        
        print_success("PostgreSQL conectado com sucesso!")
        print_info(f"Total de produtos no banco: {product_count}")
        
        # Verificar últimos produtos
        latest = await database.fetch_all(
            """
            SELECT title, category, price, updated_at 
            FROM products 
            ORDER BY updated_at DESC NULLS LAST
            LIMIT 5
            """
        )
        
        if latest:
            print_info("Últimos 5 produtos coletados:")
            for p in latest:
                updated = p['updated_at'].strftime('%Y-%m-%d %H:%M') if p['updated_at'] else 'N/A'
                print(f"    - {p['title'][:50]}... | {p['category']} | R${p['price'] or 0:.2f} | {updated}")
        else:
            print_warning("Nenhum produto encontrado no banco")
        
        return True
    except Exception as e:
        print_error(f"Falha na conexão PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tiktok_api_scraper():
    """Teste 3: Verificar TikTok API Scraper (cookies e endpoints)"""
    print_header("TESTE 3: TIKTOK API SCRAPER")
    
    try:
        from scraper.tiktok.api_scraper import (TikTokAPIScraper,
                                                get_api_scraper)
        
        scraper = get_api_scraper()
        
        # Health check
        print_info("Executando health check...")
        health = await scraper.health_check()
        
        print_info(f"Status de saúde:")
        print(f"    - Healthy: {health.get('healthy', False)}")
        print(f"    - Authenticated: {health.get('authenticated', False)}")
        print(f"    - Cookies válidos: {health.get('cookies_valid', False)}")
        print(f"    - Endpoints funcionando: {health.get('endpoints_working', 0)}")
        
        if not health.get('healthy'):
            print_error("API não está saudável!")
            print_warning("Os cookies podem estar expirados - precisa atualizar!")
            return False
        
        print_success("Health check passou!")
        
        # Testar busca
        print_info("Testando busca por 'moda feminina'...")
        products = await scraper.search_products("moda feminina", limit=5)
        
        if products:
            print_success(f"Busca retornou {len(products)} produtos!")
            for p in products[:3]:
                print(f"    - {p.get('title', 'Sem título')[:50]}...")
                print(f"      Imagem: {p.get('image_url', 'N/A')[:60]}...")
                print(f"      URL: {p.get('product_url', 'N/A')[:60]}...")
        else:
            print_error("Busca não retornou produtos!")
            print_warning("Possíveis causas:")
            print_warning("  1. Cookies expirados")
            print_warning("  2. Rate limiting")
            print_warning("  3. CAPTCHA ativado")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Falha no TikTok API Scraper: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scraper_route():
    """Teste 4: Testar rota de scraping diretamente"""
    print_header("TESTE 4: ROTA DE SCRAPING")
    
    try:
        import httpx

        # Tentar conectar na API local
        base_url = "http://localhost:8000"  # Ajuste se necessário
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Testar status
            print_info(f"Testando {base_url}/api/v1/scraper/status...")
            response = await client.get(f"{base_url}/api/v1/scraper/status")
            
            if response.status_code == 200:
                status = response.json()
                print_success(f"Rota de status funcionando!")
                print_info(f"isRunning: {status.get('isRunning', False)}")
                print_info(f"statusMessage: {status.get('statusMessage', 'N/A')}")
            else:
                print_error(f"Status code: {response.status_code}")
                print(response.text[:500])
                
        return True
        
    except httpx.ConnectError:
        print_warning("API não está rodando em localhost:8000")
        print_info("Inicie a API com: uvicorn api.main:app --reload")
        return False
    except Exception as e:
        print_error(f"Erro ao testar rota: {e}")
        return False


async def test_cache_system():
    """Teste 5: Verificar sistema de cache"""
    print_header("TESTE 5: SISTEMA DE CACHE")
    
    try:
        from scraper.cache import get_product_cache
        
        cache = get_product_cache()
        
        # Testar stats
        stats = await cache.get_stats()
        
        print_success("Cache funcionando!")
        print_info(f"Hits: {stats.hits}")
        print_info(f"Misses: {stats.misses}")
        print_info(f"Hit rate: {stats.hit_rate:.1f}%")
        print_info(f"Total produtos em cache: {stats.total_products}")
        
        return True
        
    except Exception as e:
        print_error(f"Erro no cache: {e}")
        return False


async def test_full_scraping_workflow():
    """Teste 6: Teste completo de scraping (coleta real)"""
    print_header("TESTE 6: WORKFLOW COMPLETO DE SCRAPING")
    
    print_warning("Este teste vai fazer uma coleta REAL de produtos")
    print_info("Serão coletados apenas 5 produtos para teste")
    
    try:
        from api.database.connection import database
        from scraper.cache import get_product_cache
        from scraper.tiktok.api_scraper import get_api_scraper

        # 1. Inicializar scraper
        print_info("\n1. Inicializando scraper...")
        scraper = get_api_scraper()
        
        # 2. Buscar produtos
        print_info("2. Buscando produtos...")
        products = await scraper.search_products("produtos virais tiktok", limit=5)
        
        if not products:
            print_error("Nenhum produto encontrado!")
            return False
        
        print_success(f"Encontrados {len(products)} produtos")
        
        # 3. Verificar estrutura dos produtos
        print_info("\n3. Verificando estrutura dos dados...")
        
        required_fields = [
            "tiktok_id", "title", "description", "price", 
            "image_url", "product_url", "seller_name", "category"
        ]
        
        for i, product in enumerate(products):
            print(f"\n   Produto {i+1}:")
            missing = []
            for field in required_fields:
                value = product.get(field)
                if value:
                    # Truncar valores longos
                    display_value = str(value)[:50] + "..." if len(str(value)) > 50 else value
                    print(f"      {Colors.GREEN}✓{Colors.END} {field}: {display_value}")
                else:
                    missing.append(field)
                    print(f"      {Colors.RED}✗{Colors.END} {field}: FALTANDO")
            
            if missing:
                print_warning(f"   Campos faltando: {missing}")
        
        # 4. Salvar no cache
        print_info("\n4. Salvando em cache...")
        cache = get_product_cache()
        cached = 0
        for product in products:
            if await cache.set_product(product):
                cached += 1
        print_success(f"Salvos {cached}/{len(products)} produtos no cache")
        
        # 5. Verificar se podemos salvar no banco
        print_info("\n5. Verificando compatibilidade com banco de dados...")
        
        sample = products[0]
        db_fields = {
            "tiktok_id": sample.get("tiktok_id"),
            "title": sample.get("title", "")[:500],  # Limite do campo
            "description": sample.get("description"),
            "price": sample.get("price"),
            "original_price": sample.get("original_price"),
            "category": sample.get("category"),
            "seller_name": sample.get("seller_name"),
            "image_url": sample.get("image_url"),
            "product_url": sample.get("product_url"),
            "sales_count": sample.get("sold_count", 0),
        }
        
        missing_required = []
        if not db_fields["tiktok_id"]:
            missing_required.append("tiktok_id")
        if not db_fields["title"]:
            missing_required.append("title")
        if not db_fields["product_url"]:
            missing_required.append("product_url")
        
        if missing_required:
            print_error(f"Campos obrigatórios faltando para salvar no banco: {missing_required}")
            return False
        
        print_success("Dados compatíveis com o banco de dados!")
        
        return True
        
    except Exception as e:
        print_error(f"Erro no workflow: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_worker_status():
    """Verificar se o worker de scraping está rodando"""
    print_header("VERIFICAÇÃO DO WORKER")
    
    try:
        from shared.redis import get_redis
        
        redis = await get_redis()
        
        # Verificar se há worker ativo
        worker_key = "worker:scraper:status"
        worker_status = await redis.get(worker_key)
        
        # Verificar última atividade
        last_activity = await redis.get("worker:scraper:last_activity")
        
        if worker_status == "running":
            print_success("Worker está marcado como rodando")
            if last_activity:
                print_info(f"Última atividade: {last_activity}")
        else:
            print_warning("Worker NÃO está rodando!")
            print_info("Para iniciar o worker, execute:")
            print(f"   cd {backend_dir}")
            print("   python -m workers.scraping_worker")
        
        # Verificar jobs pendentes
        pending_jobs = await redis.llen("scraper:jobs")
        if pending_jobs > 0:
            print_warning(f"Há {pending_jobs} jobs pendentes na fila!")
        
        return worker_status == "running"
        
    except Exception as e:
        print_error(f"Erro ao verificar worker: {e}")
        return False


async def generate_report(results: dict):
    """Gerar relatório final"""
    print_header("📊 RELATÓRIO FINAL")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nResultados: {passed}/{total} testes passaram\n")
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASSOU{Colors.END}" if passed else f"{Colors.RED}FALHOU{Colors.END}"
        print(f"  {test_name}: {status}")
    
    print("\n" + "="*60)
    
    # Recomendações
    if not results.get("redis"):
        print(f"\n{Colors.RED}🔧 AÇÃO NECESSÁRIA:{Colors.END}")
        print("   Verifique se o Redis está rodando:")
        print("   docker-compose up -d redis")
    
    if not results.get("database"):
        print(f"\n{Colors.RED}🔧 AÇÃO NECESSÁRIA:{Colors.END}")
        print("   Verifique se o PostgreSQL está rodando:")
        print("   docker-compose up -d db")
    
    if not results.get("tiktok_api"):
        print(f"\n{Colors.RED}🔧 AÇÃO NECESSÁRIA:{Colors.END}")
        print("   Os cookies do TikTok podem estar expirados!")
        print("   Atualize os cookies em: backend/scraper/tiktok/api_scraper.py")
        print("   Ou configure via variável de ambiente TIKTOK_COOKIES")
    
    if not results.get("worker"):
        print(f"\n{Colors.YELLOW}⚠️ RECOMENDAÇÃO:{Colors.END}")
        print("   Inicie o worker de scraping:")
        print("   python -m workers.scraping_worker")
    
    print("\n" + "="*60)


async def main():
    """Executar todos os testes"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║      🔍 DIAGNÓSTICO DO SISTEMA DE SCRAPING              ║")
    print("║         Didin Fácil - Coleta de Produtos                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(Colors.END)
    
    print(f"\n📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    
    # Executar testes
    results["redis"] = await test_redis_connection()
    results["database"] = await test_database_connection()
    results["tiktok_api"] = await test_tiktok_api_scraper()
    results["cache"] = await test_cache_system()
    results["scraper_route"] = await test_scraper_route()
    results["worker"] = await check_worker_status()
    
    # Teste completo apenas se os anteriores passaram
    if all([results["redis"], results["tiktok_api"]]):
        results["full_workflow"] = await test_full_scraping_workflow()
    else:
        print_header("TESTE 6: WORKFLOW COMPLETO DE SCRAPING")
        print_warning("Pulado - dependências falharam")
        results["full_workflow"] = False
    
    # Relatório final
    await generate_report(results)
    
    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
