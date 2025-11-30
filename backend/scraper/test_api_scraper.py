#!/usr/bin/env python3
"""
Teste do TikTok API Scraper
Valida as funcionalidades do scraper baseado em API
"""

import asyncio
import json
from datetime import datetime

# Add parent to path
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scraper.tiktok.api_scraper import get_api_scraper  # noqa: E402


async def main():
    print("=" * 60)
    print("🚀 TESTE DO TIKTOK API SCRAPER")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Create scraper instance
    scraper = get_api_scraper()
    
    # Test 1: Health Check
    print("📋 TESTE 1: Health Check")
    print("-" * 40)
    
    try:
        health = await scraper.health_check()
        print(f"   Saudável: {'✅' if health['healthy'] else '❌'}")
        print(f"   Autenticado: {'✅' if health['authenticated'] else '❌'}")
        print(f"   Cookies válidos: {'✅' if health['cookies_valid'] else '❌'}")
        print(f"   Endpoints funcionando: {health['endpoints_working']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print()
    
    # Test 2: Search Products
    print("📋 TESTE 2: Busca de Produtos")
    print("-" * 40)
    
    try:
        products = await scraper.search_products("moda feminina", limit=5)
        print(f"   Produtos encontrados: {len(products)}")
        
        for i, p in enumerate(products[:3], 1):
            title = p.get('title', '')[:50]
            seller = p.get('seller_name', 'N/A')
            views = p.get('stats', {}).get('views', 0)
            print(f"   {i}. {title}...")
            print(f"      Seller: {seller} | Views: {views:,}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print()
    
    # Test 3: Trending Products
    print("📋 TESTE 3: Produtos em Tendência")
    print("-" * 40)
    
    try:
        trending = await scraper.get_trending_products(limit=10)
        print(f"   Produtos em alta: {len(trending)}")
        
        # Show categories distribution
        categories = {}
        for p in trending:
            cat = p.get('category', 'Geral')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("   Categorias:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"      - {cat}: {count}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print()
    
    # Test 4: User Videos
    print("📋 TESTE 4: Vídeos de Usuário")
    print("-" * 40)
    
    try:
        # Test with a known TikTok Shop account
        videos = await scraper.get_user_videos("tiktokshop_brasil", limit=5)
        print(f"   Vídeos encontrados: {len(videos)}")
        
        for i, v in enumerate(videos[:3], 1):
            title = v.get('title', '')[:40]
            likes = v.get('stats', {}).get('likes', 0)
            print(f"   {i}. {title}... ({likes:,} likes)")
            
    except Exception as e:
        print(f"   ⚠️ Usuário não acessível: {e}")
    
    print()
    
    # Test 5: Hashtag Search
    print("📋 TESTE 5: Busca por Hashtag")
    print("-" * 40)
    
    try:
        hashtag_videos = await scraper.get_hashtag_videos("tiktokmademebuyit", limit=5)
        print(f"   Vídeos com hashtag: {len(hashtag_videos)}")
        
        commerce_count = sum(1 for v in hashtag_videos if v.get('is_commerce'))
        print(f"   Conteúdo de comércio: {commerce_count}/{len(hashtag_videos)}")
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print()
    
    # Summary
    print("=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    
    stats = scraper.get_stats()
    print(f"   Total de requisições: {stats['total_requests']}")
    print(f"   Erros: {stats['error_count']}")
    print(f"   Taxa de sucesso: {stats['success_rate']:.1f}%")
    
    print()
    print("✅ Teste concluído!")
    
    # Save sample data
    if trending:
        sample_file = Path(__file__).parent / "sample_api_products.json"
        with open(sample_file, "w", encoding="utf-8") as f:
            json.dump(trending[:5], f, ensure_ascii=False, indent=2)
        print(f"📁 Amostra salva em: {sample_file}")


if __name__ == "__main__":
    asyncio.run(main())
