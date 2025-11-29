"""
Scraper Orchestration Service
Manages scraping jobs and product data
"""

import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional

from api.database.connection import database
from api.services.redis import get_redis_pool


def format_product(row) -> dict:
    """Format product row to dict with proper types"""
    product = dict(row)
    product["id"] = str(product["id"])  # Convert UUID to string
    
    # Parse JSONB fields if they are strings
    if isinstance(product.get("images"), str):
        try:
            product["images"] = json.loads(product["images"])
        except Exception:
            product["images"] = []
    elif product.get("images") is None:
        product["images"] = []
        
    if isinstance(product.get("metadata"), str):
        try:
            product["metadata"] = json.loads(product["metadata"])
        except Exception:
            product["metadata"] = {}
    elif product.get("metadata") is None:
        product["metadata"] = {}
        
    return product


class ScraperOrchestrator:
    """Orchestrates scraping jobs and manages product data"""
    
    def __init__(self):
        self.job_queue = "scraper:jobs"
        self.db = database
    
    async def get_products(
        self,
        page: int = 1,
        per_page: int = 20,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_sales: Optional[int] = None,
        sort_by: str = "sales_30d",
        sort_order: str = "desc"
    ) -> dict:
        """Get paginated products with filters"""
        
        conditions = ["deleted_at IS NULL"]
        count_params = {}
        query_params = {"limit": per_page, "offset": (page - 1) * per_page}
        
        if category:
            conditions.append("category = :category")
            count_params["category"] = category
            query_params["category"] = category
    
        if min_price is not None:
            conditions.append("price >= :min_price")
            count_params["min_price"] = min_price
            query_params["min_price"] = min_price
        
        if max_price is not None:
            conditions.append("price <= :max_price")
            count_params["max_price"] = max_price
            query_params["max_price"] = max_price
        
        if min_sales is not None:
            conditions.append("sales_count >= :min_sales")
            count_params["min_sales"] = min_sales
            query_params["min_sales"] = min_sales
        
        where_clause = " AND ".join(conditions)
        
        # Validate sort column
        valid_sorts = [
            "sales_count", "price", "rating", 
            "trending_score", "created_at", "sales_30d"
        ]
        if sort_by not in valid_sorts:
            sort_by = "sales_30d"
        
        order = "DESC" if sort_order.lower() == "desc" else "ASC"
        
        # Get total count
        count_result = await self.db.fetch_one(
            f"SELECT COUNT(*) as total FROM products WHERE {where_clause}",
            count_params if count_params else None
        )
        total = count_result["total"] if count_result else 0
        
        # Get products
        results = await self.db.fetch_all(
            f"""
            SELECT * FROM products 
            WHERE {where_clause}
            ORDER BY {sort_by} {order}
            LIMIT :limit OFFSET :offset
            """,
            query_params
        )
        
        products = [format_product(r) for r in results]
        
        return {
            "products": products,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_more": (page * per_page) < total
        }
    
    async def search_products(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """Search products by keyword"""
        
        search_term = f"%{query}%"
        
        # Get total count
        count_result = await self.db.fetch_one(
            """
            SELECT COUNT(*) as total FROM products 
            WHERE (title ILIKE :query OR description ILIKE :query) 
            AND deleted_at IS NULL
            """,
            {"query": search_term}
        )
        total = count_result["total"] if count_result else 0
        
        # Get products
        results = await self.db.fetch_all(
            """
            SELECT * FROM products 
            WHERE (title ILIKE :query OR description ILIKE :query) 
            AND deleted_at IS NULL
            ORDER BY sales_count DESC
            LIMIT :limit OFFSET :offset
            """,
            {
                "query": search_term,
                "limit": per_page,
                "offset": (page - 1) * per_page
            }
        )
        
        products = [format_product(r) for r in results]
        
        return {
            "products": products,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_more": (page * per_page) < total
        }
    
    async def get_trending_products(
        self,
        page: int = 1,
        per_page: int = 20,
        category: Optional[str] = None
    ) -> dict:
        """Get trending products (high sales velocity)"""
        
        conditions = ["deleted_at IS NULL"]
        count_params = {}
        query_params = {"limit": per_page, "offset": (page - 1) * per_page}
        
        if category:
            conditions.append("category = :category")
            count_params["category"] = category
            query_params["category"] = category
        
        where_clause = " AND ".join(conditions)
        
        count_result = await self.db.fetch_one(
            f"SELECT COUNT(*) as total FROM products WHERE {where_clause}",
            count_params if count_params else None
        )
        total = count_result["total"] if count_result else 0
        
        results = await self.db.fetch_all(
            f"""
            SELECT * FROM products 
            WHERE {where_clause}
            ORDER BY trending_score DESC, sales_count DESC
            LIMIT :limit OFFSET :offset
            """,
            query_params
        )
        
        products = [format_product(r) for r in results]
        
        return {
            "products": products,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_more": (page * per_page) < total
        }
    
    async def get_categories(self) -> List[dict]:
        """Get list of product categories with counts"""
        
        results = await self.db.fetch_all(
            """
            SELECT category, COUNT(*) as count
            FROM products
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            """
        )
        
        return [
            {"name": r["category"], "count": r["count"]}
            for r in results
        ]
    
    async def get_product_by_id(self, product_id: str) -> Optional[dict]:
        """Get single product by ID"""
        
        result = await self.db.fetch_one(
            "SELECT * FROM products WHERE id = :id",
            {"id": product_id}
        )
        
        return dict(result) if result else None
    
    async def enqueue_refresh_job(
        self,
        category: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Enqueue a product refresh job"""
        
        job_id = str(uuid.uuid4())
        
        job_data = {
            "id": job_id,
            "type": "refresh_products",
            "category": category,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending"
        }
        
        redis_client = await get_redis_pool()
        
        # Add to job queue
        await redis_client.lpush(self.job_queue, json.dumps(job_data))
        
        # Store job status
        await redis_client.hset(f"job:{job_id}", mapping={
            "status": "pending",
            "created_at": job_data["created_at"]
        })
        
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get status of a scraping job"""
        
        redis_client = await get_redis_pool()
        data = await redis_client.hgetall(f"job:{job_id}")
        
        if not data:
            return None
        
        return data
    
    async def save_products(self, products: List[dict]) -> int:
        """Save products to database (upsert) in batches"""
        if not products:
            return 0
            
        query = """
            INSERT INTO products (
                id, tiktok_id, title, description, price, original_price,
                currency, category, subcategory, seller_name, seller_rating,
                product_rating, reviews_count, sales_count, sales_7d,
                sales_30d, commission_rate, image_url, images, video_url,
                product_url, affiliate_url, has_free_shipping, is_trending,
                is_on_sale, in_stock, collected_at, updated_at
            ) VALUES (
                :id, :tiktok_id, :title, :description, :price,
                :original_price, :currency, :category, :subcategory,
                :seller_name, :seller_rating, :product_rating,
                :reviews_count, :sales_count, :sales_7d, :sales_30d,
                :commission_rate, :image_url, :images, :video_url,
                :product_url, :affiliate_url, :has_free_shipping,
                :is_trending, :is_on_sale, :in_stock, :collected_at, NOW()
            )
            ON CONFLICT (tiktok_id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                price = EXCLUDED.price,
                original_price = EXCLUDED.original_price,
                sales_count = EXCLUDED.sales_count,
                sales_7d = EXCLUDED.sales_7d,
                sales_30d = EXCLUDED.sales_30d,
                product_rating = EXCLUDED.product_rating,
                reviews_count = EXCLUDED.reviews_count,
                is_trending = EXCLUDED.is_trending,
                is_on_sale = EXCLUDED.is_on_sale,
                in_stock = EXCLUDED.in_stock,
                updated_at = NOW()
        """
        
        # Process in batches of 100
        batch_size = 100
        total_saved = 0
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            await self.db.execute_many(query, batch)
            total_saved += len(batch)
            
        return total_saved
