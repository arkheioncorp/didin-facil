"""
Product Cache Manager
Redis-based caching for TikTok products with TTL, invalidation, and metrics
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from shared.redis import get_redis


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    total_products: int = 0
    memory_usage_kb: float = 0.0
    oldest_entry: Optional[str] = None
    newest_entry: Optional[str] = None
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class ProductCache:
    """
    Redis-based product cache with intelligent TTL management.
    
    Features:
    - Automatic TTL based on product freshness
    - Batch operations for efficiency
    - Cache invalidation by category/seller
    - Hit/miss metrics
    - Memory-efficient storage
    """
    
    # Cache key prefixes
    PREFIX_PRODUCT = "cache:product:"
    PREFIX_TRENDING = "cache:trending:"
    PREFIX_SEARCH = "cache:search:"
    PREFIX_CATEGORY = "cache:category:"
    PREFIX_SELLER = "cache:seller:"
    PREFIX_STATS = "cache:stats:"
    
    # TTL values (in seconds)
    TTL_PRODUCT = 3600 * 6      # 6 hours for individual products
    TTL_TRENDING = 1800         # 30 minutes for trending
    TTL_SEARCH = 900            # 15 minutes for search results
    TTL_CATEGORY = 3600         # 1 hour for category listings
    
    def __init__(self):
        self._redis = None
    
    async def _get_redis(self):
        """Get Redis connection lazily"""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key with hash for long identifiers"""
        if len(identifier) > 100:
            identifier = hashlib.md5(identifier.encode()).hexdigest()
        return f"{prefix}{identifier}"
    
    async def get_product(self, product_id: str) -> Optional[Dict]:
        """
        Get a single product from cache.
        
        Args:
            product_id: TikTok product/video ID
            
        Returns:
            Product dict or None if not cached
        """
        redis = await self._get_redis()
        key = self._generate_key(self.PREFIX_PRODUCT, product_id)
        
        data = await redis.get(key)
        if data:
            await self._increment_hits()
            return json.loads(data)
        
        await self._increment_misses()
        return None
    
    async def set_product(
        self,
        product: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache a single product.
        
        Args:
            product: Product dict with 'tiktok_id' or 'video_id'
            ttl: Optional custom TTL
            
        Returns:
            True if successful
        """
        redis = await self._get_redis()
        
        product_id = product.get("tiktok_id") or product.get("video_id")
        if not product_id:
            return False
        
        key = self._generate_key(self.PREFIX_PRODUCT, str(product_id))
        
        # Add cache metadata
        product["_cached_at"] = datetime.now(timezone.utc).isoformat()
        
        await redis.set(
            key,
            json.dumps(product, ensure_ascii=False),
            ex=ttl or self.TTL_PRODUCT
        )
        
        # Index by seller for invalidation
        seller_id = product.get("seller_id")
        if seller_id:
            await self._add_to_seller_index(seller_id, product_id)
        
        # Index by category
        category = product.get("category")
        if category:
            await self._add_to_category_index(category, product_id)
        
        return True
    
    async def get_products_batch(
        self,
        product_ids: List[str]
    ) -> Dict[str, Optional[Dict]]:
        """
        Get multiple products in a single operation.
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            Dict mapping product_id -> product (or None)
        """
        if not product_ids:
            return {}
        
        redis = await self._get_redis()
        keys = [
            self._generate_key(self.PREFIX_PRODUCT, pid)
            for pid in product_ids
        ]
        
        values = await redis.mget(keys)
        
        result = {}
        hits = 0
        misses = 0
        
        for pid, value in zip(product_ids, values):
            if value:
                result[pid] = json.loads(value)
                hits += 1
            else:
                result[pid] = None
                misses += 1
        
        # Update stats
        if hits > 0:
            await self._increment_hits(hits)
        if misses > 0:
            await self._increment_misses(misses)
        
        return result
    
    async def set_products_batch(
        self,
        products: List[Dict],
        ttl: Optional[int] = None
    ) -> int:
        """
        Cache multiple products efficiently.
        
        Args:
            products: List of product dicts
            ttl: Optional custom TTL
            
        Returns:
            Number of products cached
        """
        if not products:
            return 0
        
        redis = await self._get_redis()
        pipe = redis.pipeline()
        
        cached = 0
        now = datetime.now(timezone.utc).isoformat()
        
        for product in products:
            product_id = product.get("tiktok_id") or product.get("video_id")
            if not product_id:
                continue
            
            key = self._generate_key(self.PREFIX_PRODUCT, str(product_id))
            product["_cached_at"] = now
            
            pipe.set(
                key,
                json.dumps(product, ensure_ascii=False),
                ex=ttl or self.TTL_PRODUCT
            )
            cached += 1
        
        await pipe.execute()
        return cached
    
    async def get_trending(self, limit: int = 50) -> Optional[List[Dict]]:
        """
        Get cached trending products.
        
        Args:
            limit: Maximum products to return
            
        Returns:
            List of products or None if not cached
        """
        redis = await self._get_redis()
        key = self._generate_key(self.PREFIX_TRENDING, f"latest:{limit}")
        
        data = await redis.get(key)
        if data:
            await self._increment_hits()
            return json.loads(data)
        
        await self._increment_misses()
        return None
    
    async def set_trending(
        self,
        products: List[Dict],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache trending products.
        
        Args:
            products: List of trending products
            ttl: Optional custom TTL
            
        Returns:
            True if successful
        """
        redis = await self._get_redis()
        
        # Cache the full list
        key = self._generate_key(
            self.PREFIX_TRENDING,
            f"latest:{len(products)}"
        )
        
        await redis.set(
            key,
            json.dumps(products, ensure_ascii=False),
            ex=ttl or self.TTL_TRENDING
        )
        
        # Also cache individual products
        await self.set_products_batch(products)
        
        return True
    
    async def get_search_results(
        self,
        keyword: str,
        limit: int = 20
    ) -> Optional[List[Dict]]:
        """
        Get cached search results.
        
        Args:
            keyword: Search keyword
            limit: Result limit
            
        Returns:
            List of products or None
        """
        redis = await self._get_redis()
        cache_key = f"{keyword.lower().strip()}:{limit}"
        key = self._generate_key(self.PREFIX_SEARCH, cache_key)
        
        data = await redis.get(key)
        if data:
            await self._increment_hits()
            return json.loads(data)
        
        await self._increment_misses()
        return None
    
    async def set_search_results(
        self,
        keyword: str,
        products: List[Dict],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache search results.
        
        Args:
            keyword: Search keyword
            products: Search results
            ttl: Optional custom TTL
            
        Returns:
            True if successful
        """
        redis = await self._get_redis()
        cache_key = f"{keyword.lower().strip()}:{len(products)}"
        key = self._generate_key(self.PREFIX_SEARCH, cache_key)
        
        await redis.set(
            key,
            json.dumps(products, ensure_ascii=False),
            ex=ttl or self.TTL_SEARCH
        )
        
        return True
    
    async def get_category(
        self,
        category: str,
        limit: int = 50
    ) -> Optional[List[Dict]]:
        """Get cached category products."""
        redis = await self._get_redis()
        cache_key = f"{category.lower()}:{limit}"
        key = self._generate_key(self.PREFIX_CATEGORY, cache_key)
        
        data = await redis.get(key)
        if data:
            await self._increment_hits()
            return json.loads(data)
        
        await self._increment_misses()
        return None
    
    async def set_category(
        self,
        category: str,
        products: List[Dict],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache category products."""
        redis = await self._get_redis()
        cache_key = f"{category.lower()}:{len(products)}"
        key = self._generate_key(self.PREFIX_CATEGORY, cache_key)
        
        await redis.set(
            key,
            json.dumps(products, ensure_ascii=False),
            ex=ttl or self.TTL_CATEGORY
        )
        
        return True
    
    # ============ Invalidation Methods ============
    
    async def invalidate_product(self, product_id: str) -> bool:
        """Remove a product from cache."""
        redis = await self._get_redis()
        key = self._generate_key(self.PREFIX_PRODUCT, product_id)
        return await redis.delete(key) > 0
    
    async def invalidate_trending(self) -> int:
        """Invalidate all trending caches."""
        redis = await self._get_redis()
        keys = await redis.keys(f"{self.PREFIX_TRENDING}*")
        if keys:
            return await redis.delete(*keys)
        return 0
    
    async def invalidate_search(self, keyword: Optional[str] = None) -> int:
        """
        Invalidate search caches.
        
        Args:
            keyword: Specific keyword or None for all
            
        Returns:
            Number of keys deleted
        """
        redis = await self._get_redis()
        
        if keyword:
            pattern = f"{self.PREFIX_SEARCH}{keyword.lower()}:*"
        else:
            pattern = f"{self.PREFIX_SEARCH}*"
        
        keys = await redis.keys(pattern)
        if keys:
            return await redis.delete(*keys)
        return 0
    
    async def invalidate_category(self, category: str) -> int:
        """Invalidate category cache."""
        redis = await self._get_redis()
        pattern = f"{self.PREFIX_CATEGORY}{category.lower()}:*"
        keys = await redis.keys(pattern)
        if keys:
            return await redis.delete(*keys)
        return 0
    
    async def invalidate_seller(self, seller_id: str) -> int:
        """
        Invalidate all products from a seller.
        
        Args:
            seller_id: Seller ID
            
        Returns:
            Number of products invalidated
        """
        redis = await self._get_redis()
        
        # Get product IDs for this seller
        index_key = f"{self.PREFIX_SELLER}{seller_id}"
        product_ids = await redis.smembers(index_key)
        
        if not product_ids:
            return 0
        
        # Delete products
        keys = [
            self._generate_key(self.PREFIX_PRODUCT, pid)
            for pid in product_ids
        ]
        deleted = await redis.delete(*keys)
        
        # Clean up index
        await redis.delete(index_key)
        
        return deleted
    
    async def invalidate_all(self) -> int:
        """
        Clear entire product cache.
        
        Returns:
            Number of keys deleted
        """
        redis = await self._get_redis()
        
        patterns = [
            f"{self.PREFIX_PRODUCT}*",
            f"{self.PREFIX_TRENDING}*",
            f"{self.PREFIX_SEARCH}*",
            f"{self.PREFIX_CATEGORY}*",
            f"{self.PREFIX_SELLER}*",
        ]
        
        total = 0
        for pattern in patterns:
            keys = await redis.keys(pattern)
            if keys:
                total += await redis.delete(*keys)
        
        # Reset stats
        await redis.delete(f"{self.PREFIX_STATS}hits")
        await redis.delete(f"{self.PREFIX_STATS}misses")
        
        return total
    
    # ============ Index Methods ============
    
    async def _add_to_seller_index(
        self,
        seller_id: str,
        product_id: str
    ):
        """Add product to seller index for invalidation."""
        redis = await self._get_redis()
        key = f"{self.PREFIX_SELLER}{seller_id}"
        await redis.sadd(key, product_id)
        await redis.expire(key, self.TTL_PRODUCT * 2)
    
    async def _add_to_category_index(
        self,
        category: str,
        product_id: str
    ):
        """Add product to category index."""
        redis = await self._get_redis()
        key = f"{self.PREFIX_CATEGORY}index:{category.lower()}"
        await redis.sadd(key, product_id)
        await redis.expire(key, self.TTL_CATEGORY * 2)
    
    # ============ Stats Methods ============
    
    async def _increment_hits(self, count: int = 1):
        """Increment cache hit counter."""
        redis = await self._get_redis()
        await redis.incrby(f"{self.PREFIX_STATS}hits", count)
    
    async def _increment_misses(self, count: int = 1):
        """Increment cache miss counter."""
        redis = await self._get_redis()
        await redis.incrby(f"{self.PREFIX_STATS}misses", count)
    
    async def get_stats(self) -> CacheStats:
        """
        Get cache statistics.
        
        Returns:
            CacheStats with hit/miss rates and memory usage
        """
        redis = await self._get_redis()
        
        # Get hit/miss counts
        hits = await redis.get(f"{self.PREFIX_STATS}hits")
        misses = await redis.get(f"{self.PREFIX_STATS}misses")
        
        # Count products
        product_keys = await redis.keys(f"{self.PREFIX_PRODUCT}*")
        
        # Get memory info (approximate)
        try:
            info = await redis.info("memory")
            memory_kb = info.get("used_memory", 0) / 1024
        except Exception:
            memory_kb = 0.0
        
        return CacheStats(
            hits=int(hits or 0),
            misses=int(misses or 0),
            total_products=len(product_keys),
            memory_usage_kb=memory_kb,
        )
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """
        Get detailed cache information.
        
        Returns:
            Dict with cache status and metrics
        """
        stats = await self.get_stats()
        redis = await self._get_redis()
        
        # Count by type
        trending_keys = await redis.keys(f"{self.PREFIX_TRENDING}*")
        search_keys = await redis.keys(f"{self.PREFIX_SEARCH}*")
        category_keys = await redis.keys(f"{self.PREFIX_CATEGORY}*")
        
        return {
            "status": "healthy",
            "stats": asdict(stats),
            "hit_rate": f"{stats.hit_rate:.1f}%",
            "counts": {
                "products": stats.total_products,
                "trending": len(trending_keys),
                "searches": len(search_keys),
                "categories": len(category_keys),
            },
            "ttl_settings": {
                "product": self.TTL_PRODUCT,
                "trending": self.TTL_TRENDING,
                "search": self.TTL_SEARCH,
                "category": self.TTL_CATEGORY,
            },
            "memory_kb": stats.memory_usage_kb,
        }


# Singleton instance
_cache_instance: Optional[ProductCache] = None


def get_product_cache() -> ProductCache:
    """Get the singleton ProductCache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ProductCache()
    return _cache_instance


class ProductCacheManager:
    """
    High-level cache manager for TikTok products.
    
    Provides simplified API for common caching operations
    used in API routes.
    """
    
    def __init__(self):
        self._cache = get_product_cache()
    
    async def get_search_results(
        self,
        query: str
    ) -> Optional[List[Dict]]:
        """Get cached search results."""
        return await self._cache.get_search_results(query)
    
    async def cache_search_results(
        self,
        query: str,
        products: List[Dict],
        ttl: int = 1800  # 30 minutes
    ) -> bool:
        """Cache search results."""
        return await self._cache.set_search_results(query, products, ttl)
    
    async def get_trending(
        self,
        category: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """Get cached trending products."""
        if category:
            return await self._cache.get_category(category)
        return await self._cache.get_trending()
    
    async def cache_trending(
        self,
        products: List[Dict],
        category: Optional[str] = None,
        ttl: int = 1800  # 30 minutes
    ) -> bool:
        """Cache trending products."""
        if category:
            return await self._cache.set_category(category, products, ttl)
        return await self._cache.set_trending(products, ttl)
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a cache key."""
        redis = await self._cache._get_redis()
        
        # Map logical key to actual cache key
        if key.startswith("search:"):
            query = key[7:]
            full_key = self._cache._generate_key(
                self._cache.PREFIX_SEARCH,
                f"{query.lower().strip()}:*"
            )
        elif key == "trending":
            full_key = f"{self._cache.PREFIX_TRENDING}latest:*"
        else:
            full_key = key
        
        # Get TTL
        ttl = await redis.ttl(full_key.replace("*", "50"))
        return ttl if ttl > 0 else None
    
    async def get_stats(self) -> Dict:
        """Get cache statistics."""
        cache_info = await self._cache.get_cache_info()
        stats = cache_info.get("stats", {})
        counts = cache_info.get("counts", {})
        
        return {
            "total_keys": (
                counts.get("products", 0) +
                counts.get("trending", 0) +
                counts.get("searches", 0) +
                counts.get("categories", 0)
            ),
            "hits": stats.get("hits", 0),
            "misses": stats.get("misses", 0),
            "hit_rate": stats.get("hit_rate", 0.0),
            "trending_cached": counts.get("trending", 0) > 0,
            "search_queries_cached": counts.get("searches", 0),
            "memory_used_mb": cache_info.get("memory_kb", 0) / 1024
        }
    
    async def clear_all(self) -> int:
        """Clear all product cache."""
        return await self._cache.invalidate_all()
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache by pattern."""
        if pattern.startswith("search:"):
            keyword = pattern[7:].replace("*", "")
            return await self._cache.invalidate_search(
                keyword if keyword else None
            )
        elif pattern.startswith("trending:"):
            return await self._cache.invalidate_trending()
        elif pattern.startswith("category:"):
            category = pattern[9:].replace("*", "")
            if category:
                return await self._cache.invalidate_category(category)
            return 0
        else:
            # Generic pattern clear
            redis = await self._cache._get_redis()
            keys = await redis.keys(f"cache:{pattern}")
            if keys:
                return await redis.delete(*keys)
            return 0
