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


async def get_db_pool() -> Database:
    """Get the database connection pool (for CRM and other modules)."""
    return database


@asynccontextmanager
async def get_db() -> AsyncGenerator[Database, None]:
    """Get database connection from pool"""
    try:
        yield database
    finally:
        pass  # Connection is managed by the pool


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
