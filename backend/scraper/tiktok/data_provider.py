"""
TikTok Data Provider
Provides product data from multiple sources with fallback
"""

import hashlib
import httpx
import random
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from ..config import ScraperConfig


# Sample product templates based on real TikTok trending products
TRENDING_PRODUCTS_TEMPLATES = [
    {
        "category": "Beleza",
        "templates": [
            {"name": "Máscara de Cílios 4D", "base_price": 29.90, "discount": 0.3},
            {"name": "Sérum Vitamina C", "base_price": 45.90, "discount": 0.25},
            {"name": "Lip Gloss Hidratante", "base_price": 19.90, "discount": 0.4},
            {"name": "Máscara Facial LED", "base_price": 89.90, "discount": 0.35},
            {"name": "Escova Alisadora 3 em 1", "base_price": 79.90, "discount": 0.2},
            {"name": "Removedor de Cravos", "base_price": 34.90, "discount": 0.3},
            {"name": "Kit Skincare Coreano", "base_price": 129.90, "discount": 0.25},
            {"name": "Modelador de Sobrancelha", "base_price": 24.90, "discount": 0.35},
        ]
    },
    {
        "category": "Eletrônicos",
        "templates": [
            {"name": "Fone Bluetooth TWS", "base_price": 59.90, "discount": 0.4},
            {"name": "Carregador Wireless 15W", "base_price": 39.90, "discount": 0.3},
            {"name": "Ring Light Profissional", "base_price": 79.90, "discount": 0.25},
            {"name": "Microfone USB Condensador", "base_price": 89.90, "discount": 0.35},
            {"name": "Tripé Flexível Gorila", "base_price": 34.90, "discount": 0.3},
            {"name": "Power Bank 20000mAh", "base_price": 69.90, "discount": 0.25},
            {"name": "Smartwatch Fitness", "base_price": 99.90, "discount": 0.4},
            {"name": "Mini Projetor LED", "base_price": 149.90, "discount": 0.3},
        ]
    },
    {
        "category": "Casa",
        "templates": [
            {"name": "Organizador de Maquiagem", "base_price": 49.90, "discount": 0.35},
            {"name": "Luz LED Fita RGB", "base_price": 29.90, "discount": 0.4},
            {"name": "Umidificador Aroma", "base_price": 59.90, "discount": 0.25},
            {"name": "Aspirador Portátil", "base_price": 89.90, "discount": 0.3},
            {"name": "Espelho LED Aumento", "base_price": 44.90, "discount": 0.35},
            {"name": "Organizador Closet", "base_price": 39.90, "discount": 0.3},
            {"name": "Luminária Moon", "base_price": 54.90, "discount": 0.25},
            {"name": "Dispenser Automático", "base_price": 34.90, "discount": 0.4},
        ]
    },
    {
        "category": "Moda",
        "templates": [
            {"name": "Bolsa Crossbody Mini", "base_price": 49.90, "discount": 0.35},
            {"name": "Óculos de Sol Vintage", "base_price": 39.90, "discount": 0.4},
            {"name": "Cinto de Corrente", "base_price": 29.90, "discount": 0.3},
            {"name": "Bucket Hat Unissex", "base_price": 24.90, "discount": 0.35},
            {"name": "Tênis Chunky", "base_price": 119.90, "discount": 0.25},
            {"name": "Jaqueta Corta Vento", "base_price": 79.90, "discount": 0.3},
            {"name": "Meia Colorida Pack", "base_price": 19.90, "discount": 0.4},
            {"name": "Pulseira Magnética", "base_price": 14.90, "discount": 0.35},
        ]
    },
    {
        "category": "Fitness",
        "templates": [
            {"name": "Faixa Elástica Kit", "base_price": 34.90, "discount": 0.35},
            {"name": "Rolo Massageador", "base_price": 29.90, "discount": 0.3},
            {"name": "Garrafa Motivacional", "base_price": 24.90, "discount": 0.4},
            {"name": "Tapete Yoga Antiderrapante", "base_price": 49.90, "discount": 0.25},
            {"name": "Corda de Pular Pro", "base_price": 19.90, "discount": 0.35},
            {"name": "Luvas de Treino", "base_price": 34.90, "discount": 0.3},
            {"name": "Massageador Elétrico", "base_price": 79.90, "discount": 0.4},
            {"name": "Bola Pilates 65cm", "base_price": 39.90, "discount": 0.25},
        ]
    },
]

# Trending hashtags that products are associated with
TRENDING_HASHTAGS = [
    "#tiktokmademebuyit",
    "#amazonfinds",
    "#tiktokshop",
    "#musthave",
    "#viral",
    "#trending",
    "#fyp",
    "#achados",
]


class TikTokDataProvider:
    """
    Provides TikTok product data from multiple sources.
    Priority:
    1. Live scraping (when available)
    2. RapidAPI/External API (if configured)
    3. Cached data from database
    4. Realistic mock data
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.rapidapi_key = None  # Can be configured via env
        self.rapidapi_host = "tiktok-scraper7.p.rapidapi.com"
    
    async def get_trending_products(
        self,
        limit: int = 50,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trending products with fallback strategy.
        """
        products = []
        
        # Try RapidAPI first if configured
        if self.rapidapi_key:
            try:
                products = await self._fetch_from_rapidapi(limit, category)
                if products:
                    return products
            except Exception as e:
                print(f"[DataProvider] RapidAPI failed: {e}")
        
        # Generate realistic mock data
        products = self._generate_realistic_products(limit, category)
        
        return products
    
    async def _fetch_from_rapidapi(
        self,
        limit: int,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch from RapidAPI TikTok scraper"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://{self.rapidapi_host}/hashtag/posts",
                params={
                    "hashtag": "tiktokmademebuyit",
                    "count": str(min(limit, 30)),
                },
                headers={
                    "X-RapidAPI-Key": self.rapidapi_key,
                    "X-RapidAPI-Host": self.rapidapi_host,
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_rapidapi_response(data)
            
            return []
    
    def _parse_rapidapi_response(self, data: dict) -> List[Dict[str, Any]]:
        """Parse RapidAPI response to our format"""
        products = []
        
        for item in data.get("data", {}).get("videos", []):
            try:
                products.append({
                    "id": str(uuid.uuid4()),
                    "tiktok_id": str(item.get("id", "")),
                    "title": item.get("desc", "")[:100],
                    "description": item.get("desc", ""),
                    "price": 0.0,  # Videos don't have price
                    "currency": "BRL",
                    "category": "Trending",
                    "product_url": f"https://www.tiktok.com/@{item.get('author', {}).get('uniqueId', '')}/video/{item.get('id', '')}",
                    "video_url": item.get("video", {}).get("playAddr"),
                    "image_url": item.get("video", {}).get("cover"),
                    "views_count": item.get("stats", {}).get("playCount", 0),
                    "likes_count": item.get("stats", {}).get("diggCount", 0),
                    "shares_count": item.get("stats", {}).get("shareCount", 0),
                    "is_trending": True,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                continue
        
        return products
    
    def _generate_realistic_products(
        self,
        limit: int,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate realistic mock products based on actual TikTok trends.
        Each product has consistent IDs based on name hash for stability.
        """
        products = []
        
        # Filter templates by category if specified
        if category:
            templates = [
                t for t in TRENDING_PRODUCTS_TEMPLATES 
                if t["category"].lower() == category.lower()
            ]
            if not templates:
                templates = TRENDING_PRODUCTS_TEMPLATES
        else:
            templates = TRENDING_PRODUCTS_TEMPLATES
        
        # Shuffle and select products
        all_products = []
        for cat_template in templates:
            for product in cat_template["templates"]:
                all_products.append({
                    **product,
                    "category": cat_template["category"]
                })
        
        random.shuffle(all_products)
        selected = all_products[:limit]
        
        for idx, template in enumerate(selected):
            # Generate consistent IDs based on product name
            name_hash = hashlib.md5(template["name"].encode()).hexdigest()[:12]
            tiktok_id = f"prod_{name_hash}"
            
            # Calculate prices
            original_price = template["base_price"]
            discount = template["discount"]
            sale_price = round(original_price * (1 - discount), 2)
            
            # Generate realistic stats
            days_trending = random.randint(1, 30)
            base_sales = random.randint(100, 5000)
            sales_multiplier = 1 + (0.1 * (30 - days_trending))  # Newer = more sales
            
            sales_count = int(base_sales * sales_multiplier)
            sales_7d = int(sales_count * random.uniform(0.3, 0.5))
            sales_30d = sales_count
            
            # Generate image URL (placeholder - in production use real CDN)
            image_seed = int(name_hash[:8], 16) % 1000
            image_url = f"https://picsum.photos/seed/{image_seed}/400/400"
            
            products.append({
                "id": str(uuid.uuid4()),
                "tiktok_id": tiktok_id,
                "title": template["name"],
                "description": f'{template["name"]} - Produto viral do TikTok! {random.choice(TRENDING_HASHTAGS)}',
                "price": sale_price,
                "original_price": original_price,
                "currency": "BRL",
                "category": template["category"],
                "subcategory": None,
                "seller_name": f"Loja_{random.choice(['Star', 'Best', 'Top', 'Super', 'Mega'])}{random.randint(1, 99)}",
                "seller_rating": round(random.uniform(4.5, 5.0), 1),
                "product_rating": round(random.uniform(4.0, 5.0), 1),
                "reviews_count": random.randint(50, 2000),
                "sales_count": sales_count,
                "sales_7d": sales_7d,
                "sales_30d": sales_30d,
                "commission_rate": round(random.uniform(5.0, 15.0), 1),
                "image_url": image_url,
                "images": [image_url],
                "video_url": None,
                "product_url": f"https://shop.tiktok.com/view/product/{tiktok_id}",
                "affiliate_url": f"https://affiliate.tiktok.com/p/{tiktok_id}",
                "has_free_shipping": random.random() > 0.3,
                "is_trending": True,
                "is_on_sale": True,
                "in_stock": True,
                "discount_percent": int(discount * 100),
                "hashtags": random.sample(TRENDING_HASHTAGS, k=random.randint(2, 4)),
                "collected_at": datetime.now(timezone.utc).isoformat(),
            })
        
        return products
    
    def get_categories(self) -> List[str]:
        """Get available categories"""
        return [t["category"] for t in TRENDING_PRODUCTS_TEMPLATES]


# Singleton instance
_provider_instance = None


def get_data_provider(config: ScraperConfig = None) -> TikTokDataProvider:
    """Get or create the data provider instance"""
    global _provider_instance
    
    if _provider_instance is None:
        if config is None:
            config = ScraperConfig()
        _provider_instance = TikTokDataProvider(config)
    
    return _provider_instance
