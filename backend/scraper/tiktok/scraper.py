"""
TikTok Shop Scraper
Main scraper implementation using Playwright with API fallback
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from ..config import ScraperConfig
from ..utils.proxy import ProxyPool
from .parser import TikTokParser
from .antibot import AntiDetection
from .data_provider import get_data_provider
from .api_scraper import TikTokAPIScraper

# Import redis for state persistence
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
from shared.redis import get_redis  # noqa: E402


class TikTokScraper:
    """TikTok Shop scraper with anti-detection and API fallback"""
    
    BASE_URL = "https://shop.tiktok.com"
    AFFILIATE_URL = "https://affiliate.tiktok.com"
    
    def __init__(self, proxy_pool: ProxyPool, config: ScraperConfig):
        self.proxy_pool = proxy_pool
        self.config = config
        self.parser = TikTokParser()
        self.anti_detection = AntiDetection()
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.contexts: List[BrowserContext] = []
        
        # API Scraper (primary method - no browser needed)
        self.api_scraper: Optional[TikTokAPIScraper] = None
        
        # Safety Switch State - Now using Redis
        self.redis_key_safety = "scraper:safety_mode"
        self.redis_key_failures = "scraper:consecutive_failures"
    
    async def check_safety(self) -> bool:
        """Check if safety mode is active using Redis"""
        if not self.config.safety_switch_enabled:
            return True
            
        try:
            redis = await get_redis()
            
            # Check if safety mode is active
            safety_until = await redis.get(self.redis_key_safety)
            if safety_until:
                if datetime.fromisoformat(safety_until) > datetime.now(timezone.utc):
                    return False
                else:
                    # Expired, clear it
                    await redis.delete(self.redis_key_safety)
                    await redis.delete(self.redis_key_failures)
            
            return True
        except Exception as e:
            print(f"[TikTok Scraper] Error checking safety state: {e}")
            return True # Fail open if redis fails

    async def record_result(self, success: bool):
        """Record success/failure to Redis"""
        if not self.config.safety_switch_enabled:
            return

        try:
            redis = await get_redis()
            
            if success:
                # Reset failures on success
                await redis.delete(self.redis_key_failures)
            else:
                # Increment failure count
                failures = await redis.incr(self.redis_key_failures)
                
                if failures >= self.config.consecutive_failures_threshold:
                    # Trigger safety mode
                    cooldown = self.config.safety_cooldown
                    safety_until = (datetime.now(timezone.utc) + timedelta(seconds=cooldown)).isoformat()
                    await redis.set(self.redis_key_safety, safety_until)
                    print(f"[TikTok Scraper] Safety mode triggered until {safety_until}")
        except Exception as e:
            print(f"[TikTok Scraper] Error recording result: {e}")

    async def start(self):
        """Initialize the browser"""
        self.playwright = await async_playwright().start()
        
        launch_options = {
            "headless": self.config.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--window-size=1920,1080",
            ]
        }
        
        self.browser = await self.playwright.chromium.launch(**launch_options)
        print("[TikTok Scraper] Browser started")
    
    async def stop(self):
        """Close browser and cleanup"""
        for context in self.contexts:
            try:
                await context.close()
            except Exception:
                pass
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        print("[TikTok Scraper] Browser stopped")
    
    async def _create_context(self) -> BrowserContext:
        """Create a new browser context with anti-detection"""
        # Get random fingerprint
        fingerprint = self.anti_detection.generate_fingerprint()
        proxy = self.proxy_pool.get_next() if self.proxy_pool.has_proxies() else None
        
        context_options = {
            "viewport": {
                "width": fingerprint["screen"]["width"],
                "height": fingerprint["screen"]["height"]
            },
            "user_agent": fingerprint["user_agent"],
            "locale": fingerprint["locale"],
            "timezone_id": fingerprint["timezone"],
            "geolocation": fingerprint.get("geolocation"),
            "permissions": ["geolocation"],
        }
        
        if proxy:
            context_options["proxy"] = proxy
        
        context = await self.browser.new_context(**context_options)
        
        # Inject anti-detection scripts
        await context.add_init_script(self.anti_detection.get_stealth_script())
        
        self.contexts.append(context)
        return context
    
    async def scrape_products(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """Scrape products from TikTok Shop"""
        is_safe = await self.check_safety()
        if not is_safe:
            print("[TikTok Scraper] Safety mode active. Skipping scrape.")
            return []

        context = await self._create_context()
        page = await context.new_page()
        
        products = []
        
        try:
            # Build URL
            url = f"{self.BASE_URL}/browse"
            if category:
                url = f"{url}?category={category}"
            
            # Navigate with human-like behavior
            await self._navigate_with_delay(page, url)
            
            # Wait for products to load
            await page.wait_for_selector("[data-e2e='product-card']", timeout=10000)
            
            # Simulate human scrolling
            await self._simulate_scrolling(page)
            
            # Extract product data
            page_products = await self._extract_products(page)
            products.extend(page_products)
            
            # Paginate if needed
            while len(products) < limit:
                has_more = await self._load_more_products(page)
                if not has_more:
                    break
                
                await self._simulate_scrolling(page)
                page_products = await self._extract_products(page)
                
                # Only add new products
                existing_ids = {p["tiktok_id"] for p in products}
                new_products = [p for p in page_products if p["tiktok_id"] not in existing_ids]
                
                if not new_products:
                    break
                
                products.extend(new_products)
                
                # Respect rate limits
                await self._random_delay()
            
            await self.record_result(True)
            return products[:limit]
            
        except Exception as e:
            print(f"[TikTok Scraper] Error: {e}")
            await self.record_result(False)
            raise
            
        finally:
            # Ensure context is closed
            try:
                await page.close()
            except Exception:
                pass
            
            try:
                await context.close()
            except Exception:
                pass
            
            if context in self.contexts:
                self.contexts.remove(context)
    
    async def scrape_category(self, category: str, limit: int = 50) -> List[dict]:
        """Scrape products from a specific category"""
        return await self.scrape_products(category=category, limit=limit)
    
    async def scrape_trending(self, limit: int = 50) -> List[dict]:
        """
        Scrape trending products with intelligent multi-tier fallback.
        
        Priority order:
        1. API Scraper (httpx with cookies - fastest, no CAPTCHA)
        2. Playwright browser (if API fails)
        3. Data Provider (curated fallback data)
        """
        is_safe = await self.check_safety()
        if not is_safe:
            print("[TikTok Scraper] Safety mode active. Using data provider.")
            provider = get_data_provider(self.config)
            return await provider.get_trending_products(limit=limit)

        # TIER 1: Try API Scraper first (fastest, bypasses CAPTCHA)
        try:
            print("[TikTok Scraper] Trying API scraper (httpx)...")
            if not self.api_scraper:
                self.api_scraper = TikTokAPIScraper(config=self.config)
            
            products = await self.api_scraper.get_trending_products(limit=limit)
            
            if products and len(products) >= 5:
                print(f"[TikTok Scraper] API returned {len(products)} products")
                await self.record_result(True)
                return products
            else:
                print("[TikTok Scraper] API returned few products, trying browser...")
                
        except Exception as e:
            print(f"[TikTok Scraper] API scraper failed: {e}")

        # TIER 2: Fallback to Playwright browser
        try:
            products = await self._scrape_trending_browser(limit=limit)
            if products:
                return products
        except Exception as e:
            print(f"[TikTok Scraper] Browser scraping failed: {e}")
        
        # TIER 3: Use data provider as last resort
        print("[TikTok Scraper] All methods failed. Using data provider.")
        await self.record_result(False)
        provider = get_data_provider(self.config)
        return await provider.get_trending_products(limit=limit)

    async def _scrape_trending_browser(self, limit: int = 50) -> List[dict]:
        """Scrape trending using Playwright browser (legacy method)"""
        # Start browser if not already running
        if not self.browser:
            await self.start()

        context = await self._create_context()
        page = await context.new_page()

        products = []

        try:
            # Try TikTok search
            url = "https://www.tiktok.com/search?q=tiktokmademebuyit"
            print(f"[TikTok Scraper] Browser navigating to {url}")
            await self._navigate_with_delay(page, url)

            # Check for CAPTCHA or blocks
            content = await page.content()
            if self._is_blocked(content):
                print("[TikTok Scraper] CAPTCHA/Block detected in browser.")
                return []  # Return empty to trigger next fallback

            # Wait for network idle to ensure dynamic content loads
            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except Exception as e:
                print(f"[TikTok Scraper] Network idle timeout: {e}")

            # Scroll to trigger lazy loading
            try:
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 1000)")
                    await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"[TikTok Scraper] Scroll failed: {e}")

            # Debug info
            title = await page.title()
            print(f"[TikTok Scraper] Page title: {title}")

            # Extract items
            page_products = await self._extract_video_products(page)
            products.extend(page_products)

            print(f"[TikTok Scraper] Browser found {len(products)} products")

            await self.record_result(len(products) > 0)
            return products[:limit]

        except Exception as e:
            print(f"[TikTok Scraper] Browser error: {e}")
            return []

        finally:
            try:
                await page.close()
            except Exception:
                pass

            try:
                await context.close()
            except Exception:
                pass

            if context in self.contexts:
                self.contexts.remove(context)

    def _is_blocked(self, content: str) -> bool:
        """Check if page content indicates a block or CAPTCHA"""
        content_lower = content.lower()
        block_indicators = [
            'captcha',
            'verify you are human',
            'access denied',
            'blocked',
            'unusual traffic',
            'robot',
            'automated',
            'recaptcha',
            'hcaptcha',
        ]
        return any(indicator in content_lower for indicator in block_indicators)

    async def _extract_video_products(self, page) -> List[dict]:
        """Extract product info from video links"""
        products = []
        elements = await page.query_selector_all("a")

        for el in elements:
            try:
                href = await el.get_attribute("href")
                if not href or "/video/" not in href:
                    continue

                video_id = href.split("/")[-1].split("?")[0]

                # Avoid duplicates
                if any(p["tiktok_id"] == video_id for p in products):
                    continue

                products.append({
                    "id": str(uuid.uuid4()),
                    "tiktok_id": video_id,
                    "title": f"Trending Video {video_id}",
                    "description": "Trending from #tiktokmademebuyit",
                    "price": 0.0,
                    "currency": "BRL",
                    "category": "Trending",
                    "product_url": href,
                    "image_url": "",
                    "is_trending": True,
                    "collected_at": datetime.now(timezone.utc),
                    "sales_count": 0
                })
            except Exception:
                continue

        return products
    
    async def scrape_product_details(self, product_id: str) -> Optional[dict]:
        """Scrape detailed information for a single product"""
        is_safe = await self.check_safety()
        if not is_safe:
            print("[TikTok Scraper] Safety mode active. Skipping scrape.")
            return None

        context = await self._create_context()
        page = await context.new_page()
        
        try:
            url = f"{self.BASE_URL}/product/{product_id}"
            await self._navigate_with_delay(page, url)
            
            await page.wait_for_selector("[data-e2e='product-detail']", timeout=10000)
            
            # Extract detailed product info
            product = await self.parser.parse_product_detail(page)
            
            await self.record_result(True)
            return product
            
        except Exception as e:
            print(f"[TikTok Scraper] Error getting product details: {e}")
            await self.record_result(False)
            return None
            
        finally:
            try:
                await page.close()
            except Exception:
                pass
            
            try:
                await context.close()
            except Exception:
                pass
            
            if context in self.contexts:
                self.contexts.remove(context)
    
    async def _navigate_with_delay(self, page: Page, url: str):
        """Navigate to URL with human-like delays"""
        await self._random_delay(0.5, 1.5)
        await page.goto(url, wait_until="networkidle", timeout=self.config.page_load_timeout)
    
    async def _simulate_scrolling(self, page: Page):
        """Simulate human-like scrolling behavior"""
        viewport_height = page.viewport_size["height"]
        
        # Random scroll positions
        scroll_positions = [
            viewport_height * 0.3,
            viewport_height * 0.6,
            viewport_height * 1.0,
            viewport_height * 1.5,
        ]
        
        for position in scroll_positions:
            await page.evaluate(f"window.scrollTo(0, {position})")
            await self._random_delay(0.3, 0.8)
        
        # Scroll back up a bit (human behavior)
        await page.evaluate(f"window.scrollTo(0, {viewport_height * 0.5})")
        await self._random_delay(0.2, 0.5)
    
    async def _extract_products(self, page: Page) -> List[dict]:
        """Extract product data from current page"""
        return await self.parser.parse_product_list(page)
    
    async def _load_more_products(self, page: Page) -> bool:
        """Try to load more products (infinite scroll or button)"""
        try:
            # Look for "Load More" button
            load_more = await page.query_selector("[data-e2e='load-more']")
            if load_more:
                await load_more.click()
                await self._random_delay(1, 2)
                return True
            
            # Try infinite scroll
            prev_height = await page.evaluate("document.body.scrollHeight")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self._random_delay(1, 2)
            
            new_height = await page.evaluate("document.body.scrollHeight")
            return new_height > prev_height
            
        except Exception:
            return False
    
    async def _random_delay(self, min_delay: float = None, max_delay: float = None):
        """Wait for a random amount of time"""
        min_d = min_delay or self.config.min_delay_between_requests
        max_d = max_delay or self.config.max_delay_between_requests
        
        delay = random.uniform(min_d, max_d)
        await asyncio.sleep(delay)
