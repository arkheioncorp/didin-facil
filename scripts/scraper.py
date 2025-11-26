#!/usr/bin/env python3
"""
TikTrend Finder - TikTok Shop Scraper
=====================================

Scraper de produtos do TikTok Shop usando Playwright.
Projetado para funcionar como binário standalone via PyInstaller.

USO:
    tiktrend-scraper trending [--category CAT] [--limit N]
    tiktrend-scraper search "query" [--limit N]
    tiktrend-scraper --version
    tiktrend-scraper --help

SAÍDA:
    JSON com array de produtos para stdout
"""

import argparse
import asyncio
import json
import os
import random
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# Versão do scraper
__version__ = "1.0.0"

# Verificar Playwright
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class Product:
    """Product data model"""
    id: str
    tiktok_id: str
    title: str
    description: Optional[str]
    price: float
    original_price: Optional[float]
    currency: str
    category: Optional[str]
    subcategory: Optional[str]
    seller_name: Optional[str]
    seller_rating: Optional[float]
    product_rating: Optional[float]
    reviews_count: int
    sales_count: int
    sales_7d: int
    sales_30d: int
    commission_rate: Optional[float]
    image_url: Optional[str]
    images: List[str]
    video_url: Optional[str]
    product_url: str
    affiliate_url: Optional[str]
    has_free_shipping: bool
    is_trending: bool
    is_on_sale: bool
    in_stock: bool
    collected_at: str
    updated_at: str


class TikTokShopScraper:
    """TikTok Shop product scraper using Playwright"""

    BASE_URL = "https://shop.tiktok.com"
    
    def __init__(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
        max_products: int = 50,
    ):
        self.headless = headless
        self.proxy = proxy
        self.max_products = max_products
        self.browser: Optional[Browser] = None
        self.products: List[Product] = []
        
    async def start(self):
        """Initialize browser"""
        playwright = await async_playwright().start()
        
        launch_options = {
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
        }
        
        if self.proxy:
            launch_options["proxy"] = {"server": self.proxy}
            
        self.browser = await playwright.chromium.launch(**launch_options)
        
    async def stop(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            
    async def scrape_trending(self, category: Optional[str] = None) -> List[Product]:
        """Scrape trending products"""
        if not self.browser:
            await self.start()
            
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to trending page
            url = f"{self.BASE_URL}/browse"
            if category:
                url += f"/{category}"
                
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(random.uniform(2, 4))
            
            # Scroll to load more products
            await self._scroll_page(page)
            
            # Extract product data
            products = await self._extract_products(page)
            
            return products[:self.max_products]
            
        finally:
            await context.close()
            
    async def scrape_search(self, query: str) -> List[Product]:
        """Scrape products by search query"""
        if not self.browser:
            await self.start()
            
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        
        page = await context.new_page()
        
        try:
            url = f"{self.BASE_URL}/search?q={query}"
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(random.uniform(2, 4))
            
            await self._scroll_page(page)
            products = await self._extract_products(page)
            
            return products[:self.max_products]
            
        finally:
            await context.close()
            
    async def _scroll_page(self, page: Page, max_scrolls: int = 10):
        """Scroll page to load more products"""
        for _ in range(max_scrolls):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
    async def _extract_products(self, page: Page) -> List[Product]:
        """Extract product data from page"""
        products = []
        
        # Wait for product cards to load
        await page.wait_for_selector("[data-e2e='product-card']", timeout=10000)
        
        product_cards = await page.query_selector_all("[data-e2e='product-card']")
        
        for card in product_cards:
            try:
                product = await self._parse_product_card(card, page)
                if product:
                    products.append(product)
            except Exception as e:
                print(f"Error parsing product: {e}")
                continue
                
        return products
        
    async def _parse_product_card(self, card, page: Page) -> Optional[Product]:
        """Parse product data from card element"""
        try:
            # Extract basic info
            title_el = await card.query_selector("[data-e2e='product-title']")
            title = await title_el.inner_text() if title_el else "Unknown"
            
            price_el = await card.query_selector("[data-e2e='product-price']")
            price_text = await price_el.inner_text() if price_el else "0"
            price = self._parse_price(price_text)
            
            image_el = await card.query_selector("img")
            image_url = await image_el.get_attribute("src") if image_el else None
            
            link_el = await card.query_selector("a")
            product_url = await link_el.get_attribute("href") if link_el else ""
            
            # Generate unique ID
            tiktok_id = self._extract_id_from_url(product_url)
            
            now = datetime.utcnow().isoformat()
            
            return Product(
                id=f"prod_{tiktok_id}",
                tiktok_id=tiktok_id,
                title=title.strip(),
                description=None,
                price=price,
                original_price=None,
                currency="BRL",
                category=None,
                subcategory=None,
                seller_name=None,
                seller_rating=None,
                product_rating=None,
                reviews_count=0,
                sales_count=0,
                sales_7d=0,
                sales_30d=0,
                commission_rate=None,
                image_url=image_url,
                images=[],
                video_url=None,
                product_url=product_url,
                affiliate_url=None,
                has_free_shipping=False,
                is_trending=True,
                is_on_sale=False,
                in_stock=True,
                collected_at=now,
                updated_at=now,
            )
            
        except Exception as e:
            print(f"Error parsing product card: {e}")
            return None
            
    def _parse_price(self, text: str) -> float:
        """Parse price from text"""
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[^\d,.]', '', text)
        # Handle Brazilian format (comma as decimal separator)
        cleaned = cleaned.replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
            
    def _extract_id_from_url(self, url: str) -> str:
        """Extract product ID from URL"""
        match = re.search(r'/product/(\d+)', url)
        return match.group(1) if match else str(hash(url))[:12]
        
    def to_json(self) -> str:
        """Export products to JSON"""
        return json.dumps([asdict(p) for p in self.products], indent=2)
        
    def save_to_file(self, filepath: str):
        """Save products to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())


# =============================================================================
# CLI Interface
# =============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos CLI."""
    parser = argparse.ArgumentParser(
        prog="tiktrend-scraper",
        description="TikTrend Finder - Scraper de produtos TikTok Shop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  tiktrend-scraper trending --limit 50
  tiktrend-scraper search "celular" --limit 20
  tiktrend-scraper trending --category electronics --output produtos.json
"""
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Modo teste: retorna dados simulados sem acessar a web"
    )
    
    # Subcomandos
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    # Comando: trending
    trending_parser = subparsers.add_parser(
        "trending",
        help="Buscar produtos em tendência"
    )
    trending_parser.add_argument(
        "--category", "-c",
        type=str,
        default=None,
        help="Categoria para filtrar (ex: electronics, fashion, beauty)"
    )
    trending_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=50,
        help="Número máximo de produtos (padrão: 50)"
    )
    trending_parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Arquivo de saída (padrão: stdout)"
    )
    trending_parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Executar navegador em modo headless (padrão: True)"
    )
    trending_parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="Servidor proxy (ex: http://proxy:8080)"
    )
    
    # Comando: search
    search_parser = subparsers.add_parser(
        "search",
        help="Buscar produtos por termo"
    )
    search_parser.add_argument(
        "query",
        type=str,
        help="Termo de busca"
    )
    search_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=50,
        help="Número máximo de produtos (padrão: 50)"
    )
    search_parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Arquivo de saída (padrão: stdout)"
    )
    search_parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Executar navegador em modo headless"
    )
    search_parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="Servidor proxy"
    )
    
    return parser


def generate_mock_products(count: int = 10, category: str = None) -> List[dict]:
    """Gera produtos mock para modo dry-run ou testes."""
    categories = ["electronics", "fashion", "beauty", "home", "sports"]
    
    if category is None:
        category = random.choice(categories)
    
    products = []
    now = datetime.utcnow().isoformat()
    
    product_names = [
        "Fone Bluetooth TWS Pro",
        "Smartwatch Fitness Band",
        "Ring Light 26cm LED",
        "Carregador Turbo 65W",
        "Capa iPhone Premium",
        "Mouse Gamer RGB 12000DPI",
        "Teclado Mecânico Compacto",
        "Webcam Full HD 1080p",
        "Hub USB-C 7 em 1",
        "Tripé Selfie Profissional",
        "Caixa de Som Portátil",
        "Power Bank 20000mAh",
        "Cabo USB-C Magnético",
        "Suporte Celular Carro",
        "Luminária LED Touch",
    ]
    
    for i in range(min(count, len(product_names))):
        price = round(random.uniform(29.90, 299.90), 2)
        original = round(price * random.uniform(1.2, 1.8), 2)
        sales = random.randint(100, 50000)
        
        products.append({
            "id": f"prod_mock_{i+1}",
            "tiktok_id": f"mock_{random.randint(100000, 999999)}",
            "title": product_names[i],
            "description": f"Produto de alta qualidade - {product_names[i]}",
            "price": price,
            "original_price": original,
            "currency": "BRL",
            "category": category,
            "subcategory": None,
            "seller_name": f"Loja_{random.randint(1, 100)}",
            "seller_rating": round(random.uniform(4.0, 5.0), 1),
            "product_rating": round(random.uniform(4.0, 5.0), 1),
            "reviews_count": random.randint(50, 5000),
            "sales_count": sales,
            "sales_7d": int(sales * random.uniform(0.05, 0.15)),
            "sales_30d": int(sales * random.uniform(0.2, 0.4)),
            "commission_rate": round(random.uniform(5.0, 20.0), 1),
            "image_url": f"https://via.placeholder.com/300x300?text=Product{i+1}",
            "images": [],
            "video_url": None,
            "product_url": f"https://shop.tiktok.com/product/mock_{i+1}",
            "affiliate_url": None,
            "has_free_shipping": random.choice([True, False]),
            "is_trending": True,
            "is_on_sale": original > price,
            "in_stock": True,
            "collected_at": now,
            "updated_at": now,
        })
    
    return products


def output_result(products: List[dict], output_file: str = None):
    """Formata e exibe o resultado."""
    result = {
        "success": True,
        "count": len(products),
        "timestamp": datetime.utcnow().isoformat(),
        "products": products
    }
    
    json_output = json.dumps(result, indent=2, ensure_ascii=False)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_output)
        # Ainda imprime confirmação no stdout
        print(json.dumps({
            "success": True,
            "message": f"Saved {len(products)} products to {output_file}",
            "count": len(products)
        }))
    else:
        print(json_output)


async def run_scraper(args) -> List[dict]:
    """Executa o scraper baseado nos argumentos."""
    if not PLAYWRIGHT_AVAILABLE:
        return {
            "success": False,
            "error": "Playwright não instalado",
            "message": "Execute: pip install playwright && playwright install chromium"
        }
    
    scraper = TikTokShopScraper(
        headless=getattr(args, 'headless', True),
        proxy=getattr(args, 'proxy', None),
        max_products=getattr(args, 'limit', 50),
    )
    
    try:
        await scraper.start()
        
        if args.command == "trending":
            products = await scraper.scrape_trending(
                category=getattr(args, 'category', None)
            )
        elif args.command == "search":
            products = await scraper.scrape_search(args.query)
        else:
            products = []
        
        return [asdict(p) for p in products]
        
    finally:
        await scraper.stop()


def main():
    """Entry point principal."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Sem comando = mostrar ajuda
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    try:
        # Modo dry-run: retornar dados mock
        if args.dry_run:
            category = getattr(args, 'category', None)
            limit = getattr(args, 'limit', 10)
            products = generate_mock_products(limit, category)
            output_result(products, getattr(args, 'output', None))
            sys.exit(0)
        
        # Verificar Playwright
        if not PLAYWRIGHT_AVAILABLE:
            error_result = {
                "success": False,
                "error": "playwright_not_installed",
                "message": "Playwright não está instalado. Execute: pip install playwright && playwright install chromium"
            }
            print(json.dumps(error_result))
            sys.exit(1)
        
        # Executar scraper
        products = asyncio.run(run_scraper(args))
        
        if isinstance(products, dict) and not products.get("success", True):
            print(json.dumps(products))
            sys.exit(1)
        
        output_result(products, getattr(args, 'output', None))
        
    except KeyboardInterrupt:
        error_result = {
            "success": False,
            "error": "interrupted",
            "message": "Operação cancelada pelo usuário"
        }
        print(json.dumps(error_result))
        sys.exit(130)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": "unexpected_error",
            "message": str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()
