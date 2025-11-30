"""
TikTok Data Parser
Extract product data from TikTok Shop pages
"""

import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from playwright.async_api import Page


class TikTokParser:
    """Parse TikTok Shop HTML/JSON to extract product data"""
    
    async def parse_product_list(self, page: Page) -> List[dict]:
        """Extract products from a product listing page"""
        products = []
        
        try:
            # Try to get data from window.__INITIAL_STATE__
            # Added try-catch block inside evaluate to prevent crashes if window object is restricted
            initial_state = await page.evaluate("""
                () => {
                    try {
                        if (window.__INITIAL_STATE__) {
                            return JSON.stringify(window.__INITIAL_STATE__);
                        }
                        // Try alternative state variables often used by frameworks
                        if (window.__NEXT_DATA__) return JSON.stringify(window.__NEXT_DATA__);
                        if (window.__NUXT__) return JSON.stringify(window.__NUXT__);
                    } catch (e) { return null; }
                    return null;
                }
            """)
            
            if initial_state:
                import json
                data = json.loads(initial_state)
                products = self._extract_from_initial_state(data)
            
            # Fallback to DOM extraction if state extraction failed or returned empty
            if not products:
                products = await self._extract_from_dom(page)
            
            return products
            
        except Exception as e:
            print(f"[Parser] Error parsing products: {e}")
            # Last resort fallback
            try:
                return await self._extract_from_dom(page)
            except Exception:
                return []
    
    async def parse_product_detail(self, page: Page) -> Optional[dict]:
        """Extract detailed product information"""
        try:
            # Try window state first
            product_data = await page.evaluate("""
                () => {
                    if (window.__INITIAL_STATE__?.product) {
                        return JSON.stringify(window.__INITIAL_STATE__.product);
                    }
                    return null;
                }
            """)
            
            if product_data:
                import json
                data = json.loads(product_data)
                return self._parse_product_json(data)
            
            # Fallback to DOM
            return await self._extract_detail_from_dom(page)
            
        except Exception as e:
            print(f"[Parser] Error parsing product detail: {e}")
            return None
    
    def _extract_from_initial_state(self, data: dict) -> List[dict]:
        """Extract products from __INITIAL_STATE__"""
        products = []
        
        # Navigate through possible data structures
        product_list = (
            data.get("products", []) or
            data.get("productList", {}).get("products", []) or
            data.get("search", {}).get("products", []) or
            []
        )
        
        for item in product_list:
            try:
                product = self._parse_product_json(item)
                if product:
                    products.append(product)
            except Exception:
                continue
        
        return products
    
    def _parse_product_json(self, data: dict) -> Optional[dict]:
        """Parse a single product from JSON data"""
        try:
            tiktok_id = str(data.get("id") or data.get("productId") or data.get("product_id", ""))
            
            if not tiktok_id:
                return None
            
            # Price handling
            price_data = data.get("price", {})
            if isinstance(price_data, dict):
                price = float(price_data.get("value", 0) or price_data.get("min", 0) or 0)
                original_price = float(price_data.get("original", 0) or price_data.get("max", 0) or 0)
                currency = price_data.get("currency", "BRL")
            else:
                price = float(price_data or 0)
                original_price = float(data.get("originalPrice", 0) or 0)
                currency = "BRL"
            
            # Images
            images = []
            image_data = data.get("images", []) or data.get("image", [])
            if isinstance(image_data, list):
                images = [img.get("url", img) if isinstance(img, dict) else img for img in image_data]
            elif isinstance(image_data, str):
                images = [image_data]
            
            image_url = images[0] if images else data.get("imageUrl") or data.get("cover", {}).get("url")
            
            # Sales data
            sales_count = self._parse_sales(data.get("salesCount") or data.get("sold", 0))
            sales_7d = self._parse_sales(data.get("sales7d", 0))
            sales_30d = self._parse_sales(data.get("sales30d", 0))
            
            # Rating
            rating_data = data.get("rating", {})
            if isinstance(rating_data, dict):
                product_rating = float(rating_data.get("average", 0) or 0)
                reviews_count = int(rating_data.get("count", 0) or 0)
            else:
                product_rating = float(rating_data or 0)
                reviews_count = int(data.get("reviewCount", 0) or 0)
            
            # Seller info
            seller = data.get("seller", {}) or data.get("shop", {})
            seller_name = seller.get("name") or seller.get("shopName")
            seller_rating = float(seller.get("rating", 0) or 0)
            
            return {
                "id": str(uuid.uuid4()),
                "tiktok_id": tiktok_id,
                "title": data.get("title") or data.get("name", ""),
                "description": data.get("description") or data.get("desc"),
                "price": price,
                "original_price": original_price if original_price > price else None,
                "currency": currency,
                "category": data.get("category") or data.get("categoryName"),
                "subcategory": data.get("subcategory") or data.get("subCategoryName"),
                "seller_name": seller_name,
                "seller_rating": seller_rating if seller_rating > 0 else None,
                "product_rating": product_rating if product_rating > 0 else None,
                "reviews_count": reviews_count,
                "sales_count": sales_count,
                "sales_7d": sales_7d,
                "sales_30d": sales_30d,
                "commission_rate": float(data.get("commissionRate", 0) or 0) or None,
                "image_url": image_url,
                "images": images,
                "video_url": data.get("videoUrl") or data.get("video", {}).get("url"),
                "product_url": data.get("url") or f"https://shop.tiktok.com/product/{tiktok_id}",
                "affiliate_url": data.get("affiliateUrl"),
                "has_free_shipping": bool(data.get("freeShipping") or data.get("hasFreeShipping")),
                "is_trending": bool(data.get("isTrending") or data.get("trending")),
                "is_on_sale": original_price > price if original_price else False,
                "in_stock": data.get("inStock", True) if "inStock" in data else data.get("stock", 1) > 0,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            print(f"[Parser] Error parsing product JSON: {e}")
            return None
    
    async def _extract_from_dom(self, page: Page) -> List[dict]:
        """Extract products directly from DOM elements"""
        products = []
        
        product_cards = await page.query_selector_all("[data-e2e='product-card'], .product-card, .product-item")
        
        for card in product_cards:
            try:
                product = await self._parse_product_card(card)
                if product:
                    products.append(product)
            except Exception:
                continue
        
        return products
    
    async def _parse_product_card(self, card) -> Optional[dict]:
        """Parse a single product card element"""
        try:
            # Extract basic info
            title_el = await card.query_selector("[data-e2e='product-title'], .product-title, h3, h4")
            title = await title_el.inner_text() if title_el else ""
            
            price_el = await card.query_selector("[data-e2e='product-price'], .product-price, .price")
            price_text = await price_el.inner_text() if price_el else "0"
            price = self._parse_price(price_text)
            
            image_el = await card.query_selector("img")
            image_url = await image_el.get_attribute("src") if image_el else None
            
            link_el = await card.query_selector("a")
            product_url = await link_el.get_attribute("href") if link_el else None
            
            # Try to extract ID from URL
            tiktok_id = ""
            if product_url:
                match = re.search(r'/product/(\d+)', product_url)
                if match:
                    tiktok_id = match.group(1)
            
            if not tiktok_id:
                tiktok_id = str(uuid.uuid4())[:8]
            
            # Sales/rating if available
            sales_el = await card.query_selector("[data-e2e='product-sales'], .sales-count")
            sales_text = await sales_el.inner_text() if sales_el else "0"
            sales_count = self._parse_sales(sales_text)
            
            rating_el = await card.query_selector("[data-e2e='product-rating'], .rating")
            rating_text = await rating_el.inner_text() if rating_el else "0"
            rating = self._parse_rating(rating_text)
            
            return {
                "id": str(uuid.uuid4()),
                "tiktok_id": tiktok_id,
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
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            print(f"[Parser] Error parsing product card: {e}")
            return None
    
    async def _extract_detail_from_dom(self, page: Page) -> Optional[dict]:
        """Extract product detail from DOM"""
        try:
            title_el = await page.query_selector("[data-e2e='product-title'], h1")
            title = await title_el.inner_text() if title_el else ""
            
            desc_el = await page.query_selector("[data-e2e='product-description'], .description")
            description = await desc_el.inner_text() if desc_el else None
            
            price_el = await page.query_selector("[data-e2e='product-price'], .price")
            price_text = await price_el.inner_text() if price_el else "0"
            price = self._parse_price(price_text)
            
            # Get all images
            images = []
            image_els = await page.query_selector_all("[data-e2e='product-image'] img, .product-images img")
            for img in image_els:
                src = await img.get_attribute("src")
                if src:
                    images.append(src)
            
            # Get product ID from URL
            url = page.url
            match = re.search(r'/product/(\d+)', url)
            tiktok_id = match.group(1) if match else str(uuid.uuid4())[:8]
            
            return {
                "id": str(uuid.uuid4()),
                "tiktok_id": tiktok_id,
                "title": title.strip(),
                "description": description,
                "price": price,
                "original_price": None,
                "currency": "BRL",
                "category": None,
                "subcategory": None,
                "seller_name": None,
                "seller_rating": None,
                "product_rating": None,
                "reviews_count": 0,
                "sales_count": 0,
                "sales_7d": 0,
                "sales_30d": 0,
                "commission_rate": None,
                "image_url": images[0] if images else None,
                "images": images,
                "video_url": None,
                "product_url": url,
                "affiliate_url": None,
                "has_free_shipping": False,
                "is_trending": False,
                "is_on_sale": False,
                "in_stock": True,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            print(f"[Parser] Error extracting detail from DOM: {e}")
            return None
    
    def _parse_price(self, text: str) -> float:
        """Parse price from text"""
        if not text:
            return 0.0
        
        # Remove currency symbols and text
        cleaned = re.sub(r'[R$\s]', '', str(text))
        cleaned = cleaned.replace('.', '').replace(',', '.')
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def _parse_sales(self, value) -> int:
        """Parse sales count from various formats"""
        if isinstance(value, int):
            return value
        
        if not value:
            return 0
        
        text = str(value).lower().strip()
        
        # Handle "1.2k", "3.5M" formats
        multipliers = {'k': 1000, 'm': 1000000}
        
        for suffix, mult in multipliers.items():
            if text.endswith(suffix):
                try:
                    return int(float(text[:-1]) * mult)
                except ValueError:
                    pass
        
        # Remove non-numeric
        cleaned = re.sub(r'[^\d]', '', text)
        
        try:
            return int(cleaned)
        except ValueError:
            return 0
    
    def _parse_rating(self, text: str) -> Optional[float]:
        """Parse rating from text"""
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
