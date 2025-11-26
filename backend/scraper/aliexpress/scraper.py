"""
AliExpress Scraper (Fallback)
Backup scraper when TikTok scraping fails
"""

import asyncio
import re
import uuid
import hashlib
from datetime import datetime
from typing import List, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from ..config import ScraperConfig
from ..utils.proxy import ProxyPool


class AliExpressScraper:
    """AliExpress product scraper as fallback"""
    
    BASE_URL = "https://www.aliexpress.com"
    
    def __init__(self, proxy_pool: ProxyPool, config: ScraperConfig):
        self.proxy_pool = proxy_pool
        self.config = config
        
        self.playwright = None
        self.browser: Optional[Browser] = None
    
    async def start(self):
        """Initialize the browser"""
        self.playwright = await async_playwright().start()
        
        launch_options = {
            "headless": self.config.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        }
        
        self.browser = await self.playwright.chromium.launch(**launch_options)
        print("[AliExpress Scraper] Browser started")
    
    async def stop(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        print("[AliExpress Scraper] Browser stopped")
    
    async def _create_context(self) -> BrowserContext:
        """Create browser context"""
        from ..config import get_random_user_agent
        user_agent = get_random_user_agent()
        proxy = self.proxy_pool.get_next() if self.proxy_pool.has_proxies() else None
        
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": user_agent,
            "locale": "pt-BR",
        }
        
        if proxy:
            context_options["proxy"] = proxy
        
        return await self.browser.new_context(**context_options)
    
    async def scrape_products(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """Scrape products from AliExpress"""
        context = await self._create_context()
        page = await context.new_page()
        
        products = []
        
        try:
            # Build search URL
            if category:
                url = f"{self.BASE_URL}/wholesale?SearchText={category}"
            else:
                url = f"{self.BASE_URL}/category/200003482/cell-phones.html"
            
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)
            
            # Wait for products
            try:
                await page.wait_for_selector(
                    ".search-item-card-wrapper-gallery, .product-card",
                    timeout=10000
                )
            except Exception:
                print("[AliExpress] No products found")
                return []
            
            # Extract products
            products = await self._extract_products(page)
            
            return products[:limit]
            
        except Exception as e:
            print(f"[AliExpress Scraper] Error: {e}")
            raise
            
        finally:
            await page.close()
            await context.close()
    
    async def _extract_products(self, page: Page) -> List[dict]:
        """Extract product data from page"""
        products = []
        
        # Try different selectors - Updated for robustness
        selectors = [
            ".search-item-card-wrapper-gallery",
            ".product-card",
            "[data-pl='product-card']",
            ".list-item", # Generic fallback
            "div[class*='product-container']", # Partial match
            "a[href*='/item/']" # Link based fallback
        ]
        
        product_cards = []
        for selector in selectors:
            product_cards = await page.query_selector_all(selector)
            if product_cards and len(product_cards) > 0:
                # Verify if these are actual product cards by checking size/content
                first_card = product_cards[0]
                if await first_card.query_selector("img") and await first_card.query_selector("a"):
                    break
        
        for card in product_cards:
            try:
                product = await self._parse_product_card(card, page)
                if product:
                    products.append(product)
            except Exception as e:
                print(f"[AliExpress] Error parsing card: {e}")
                continue
        
        return products
    
    async def _parse_product_card(self, card, page: Page) -> Optional[dict]:
        """Parse a product card"""
        try:
            # Title
            title_el = await card.query_selector("h3, .title, .product-title")
            title = await title_el.inner_text() if title_el else ""
            
            if not title:
                return None
            
            # Price
            price_el = await card.query_selector(
                ".price-current, .product-price, [class*='price']"
            )
            price_text = await price_el.inner_text() if price_el else "0"
            price = self._parse_price(price_text)
            
            # Image
            image_el = await card.query_selector("img")
            image_url = None
            if image_el:
                image_url = await image_el.get_attribute("src")
                if not image_url:
                    image_url = await image_el.get_attribute("data-src")
            
            # Link
            link_el = await card.query_selector("a")
            product_url = None
            if link_el:
                href = await link_el.get_attribute("href")
                if href:
                    if href.startswith("//"):
                        product_url = f"https:{href}"
                    elif href.startswith("/"):
                        product_url = f"{self.BASE_URL}{href}"
                    else:
                        product_url = href
            
            # Extract product ID from URL
            ali_id = ""
            if product_url:
                match = re.search(r'/item/(\d+)', product_url)
                if match:
                    ali_id = match.group(1)
            
            if not ali_id:
                # Generate deterministic ID based on URL or Title to prevent duplicates
                source_string = product_url or title
                ali_id = hashlib.md5(source_string.encode()).hexdigest()[:12]
            
            # Sales
            sales_el = await card.query_selector(
                ".sale-num, .product-sold, [class*='sold']"
            )
            sales_text = await sales_el.inner_text() if sales_el else "0"
            sales_count = self._parse_sales(sales_text)
            
            # Rating
            rating_el = await card.query_selector(
                ".star-rating, .product-rating, [class*='rating']"
            )
            rating = None
            if rating_el:
                rating_text = await rating_el.inner_text()
                rating = self._parse_rating(rating_text)
            
            return {
                "id": str(uuid.uuid4()),
                "tiktok_id": f"ali_{ali_id}",  # Prefix to distinguish source
                "title": title.strip(),
                "description": None,
                "price": price,
                "original_price": None,
                "currency": "BRL",
                "category": None,
                "subcategory": None,
                "seller_name": None,
                "seller_rating": None,
                "product_rating": rating,
                "reviews_count": 0,
                "sales_count": sales_count,
                "sales_7d": 0,
                "sales_30d": 0,
                "commission_rate": None,
                "image_url": image_url,
                "images": [image_url] if image_url else [],
                "video_url": None,
                "product_url": product_url or "",
                "affiliate_url": None,
                "has_free_shipping": False,
                "is_trending": False,
                "is_on_sale": False,
                "in_stock": True,
                "collected_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            print(f"[AliExpress] Error parsing product: {e}")
            return None
    
    def _parse_price(self, text: str) -> float:
        """Parse price from text"""
        if not text:
            return 0.0
        
        # Remove currency and text
        cleaned = re.sub(r'[R$USD€\s]', '', str(text))
        cleaned = cleaned.replace('.', '').replace(',', '.')
        
        # Get first number
        match = re.search(r'[\d.]+', cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        
        return 0.0
    
    def _parse_sales(self, text: str) -> int:
        """Parse sales count"""
        if not text:
            return 0
        
        text = str(text).lower()
        
        # Handle "1.2k", "3.5K+" formats
        match = re.search(r'([\d.]+)\s*k', text)
        if match:
            try:
                return int(float(match.group(1)) * 1000)
            except ValueError:
                pass
        
        # Extract just numbers
        cleaned = re.sub(r'[^\d]', '', text)
        
        try:
            return int(cleaned)
        except ValueError:
            return 0
    
    def _parse_rating(self, text: str) -> Optional[float]:
        """Parse rating"""
        if not text:
            return None
        
        match = re.search(r'(\d+\.?\d*)', str(text))
        if match:
            try:
                rating = float(match.group(1))
                return rating if 0 <= rating <= 5 else None
            except ValueError:
                pass
        
        return None
