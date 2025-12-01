"""
Database Connection Manager
Async PostgreSQL connection pool
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from databases import Database
from shared.config import settings


# Database URL from environment
DATABASE_URL = settings.DATABASE_URL

# Database instance
database = Database(DATABASE_URL)


async def init_database():
    """Initialize database connection pool"""
    await database.connect()
    print("Database connected")


async def close_database():
    """Close database connection pool"""
    await database.disconnect()
    print("Database disconnected")


# Global asyncpg pool for CRM and other modules requiring raw asyncpg
_asyncpg_pool = None


async def get_asyncpg_pool():
    """Get or create asyncpg connection pool for CRM modules."""
    import asyncpg
    
    global _asyncpg_pool
    if _asyncpg_pool is None:
        _asyncpg_pool = await asyncpg.create_pool(
            settings.DATABASE_URL.replace("+asyncpg", ""),
            min_size=2,
            max_size=10
        )
    return _asyncpg_pool


async def get_db_pool():
    """Get the asyncpg connection pool (for CRM and other modules)."""
    return await get_asyncpg_pool()


async def get_db() -> Database:
    """Get database connection - FastAPI dependency"""
    return database


class DatabaseManager:
    """Database manager for transactions"""
    
    def __init__(self):
        self.db = database
    
    @asynccontextmanager
    async def transaction(self):
        """Create a database transaction"""
        async with self.db.transaction():
            yield self.db
    
    async def execute(self, query: str, values: dict = None):
        """Execute a query"""
        return await self.db.execute(query, values)
    
    async def fetch_one(self, query: str, values: dict = None):
        """Fetch one row"""
        return await self.db.fetch_one(query, values)
    
    async def fetch_all(self, query: str, values: dict = None):
        """Fetch all rows"""
        return await self.db.fetch_all(query, values)
