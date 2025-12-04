"""
PostgreSQL Connection Manager
Async database connection pool and utilities
"""

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union

from databases import Database
from sqlalchemy import MetaData

from .config import settings


class PostgresManager:
    """Manage PostgreSQL connections"""
    
    _instance: Optional["PostgresManager"] = None
    _database: Optional[Database] = None
    _metadata: Optional[MetaData] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def init(self):
        """Initialize database connection pool"""
        if self._database is not None:
            return
        
        self._database = Database(
            settings.database.url,
            min_size=settings.database.min_connections,
            max_size=settings.database.max_connections,
        )
        
        try:
            await self._database.connect()
            print(
                f"[PostgreSQL] Connected to "
                f"{settings.database.host}:{settings.database.port}"
                f"/{settings.database.name}"
            )
        except Exception as e:
            print(f"[PostgreSQL] Connection failed: {e}")
            raise
    
    async def close(self):
        """Close database connections"""
        if self._database:
            await self._database.disconnect()
            self._database = None
        
        print("[PostgreSQL] Connection closed")
    
    @property
    def database(self) -> Database:
        """Get database instance"""
        if self._database is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._database


# Global manager instance
_manager = PostgresManager()


async def init_db():
    """Initialize database connection"""
    await _manager.init()


async def close_db():
    """Close database connection"""
    await _manager.close()


async def get_database() -> Database:
    """Get database instance"""
    if _manager._database is None:
        await _manager.init()
    return _manager.database


@asynccontextmanager
async def get_db():
    """Context manager for database access"""
    db = await get_database()
    try:
        yield db
    finally:
        pass  # Pool manages connections


class DBSession:
    """Database session with transaction support"""
    
    def __init__(self, database: Database):
        self.db = database
        self._transaction = None
    
    async def execute(
        self,
        query: str,
        values: Dict[str, Any] = None,
    ) -> Any:
        """Execute a query"""
        return await self.db.execute(query=query, values=values)
    
    async def execute_many(
        self,
        query: str,
        values: List[Dict[str, Any]],
    ) -> None:
        """Execute query for multiple rows"""
        await self.db.execute_many(query=query, values=values)
    
    async def fetch_one(
        self,
        query: str,
        values: Dict[str, Any] = None,
    ) -> Optional[Dict]:
        """Fetch a single row"""
        row = await self.db.fetch_one(query=query, values=values)
        return dict(row) if row else None
    
    async def fetch_all(
        self,
        query: str,
        values: Dict[str, Any] = None,
    ) -> List[Dict]:
        """Fetch all rows"""
        rows = await self.db.fetch_all(query=query, values=values)
        return [dict(row) for row in rows]
    
    async def fetch_val(
        self,
        query: str,
        values: Dict[str, Any] = None,
        column: Union[int, str] = 0,
    ) -> Any:
        """Fetch a single value"""
        return await self.db.fetch_val(
            query=query,
            values=values,
            column=column
        )
    
    async def begin(self):
        """Begin a transaction"""
        self._transaction = await self.db.transaction()
        await self._transaction.start()
    
    async def commit(self):
        """Commit the transaction"""
        if self._transaction:
            await self._transaction.commit()
            self._transaction = None
    
    async def rollback(self):
        """Rollback the transaction"""
        if self._transaction:
            await self._transaction.rollback()
            self._transaction = None
    
    async def __aenter__(self):
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()


@asynccontextmanager
async def transaction():
    """Context manager for database transactions"""
    db = await get_database()
    session = DBSession(db)
    
    async with session:
        yield session


# Allowed column names for ORDER BY (whitelist for SQL injection prevention)
ALLOWED_ORDER_COLUMNS = {
    "created_at", "updated_at", "id", "name", "email", "status",
    "price", "sales_count", "sales_7d", "sales_30d", "priority",
    "collected_at", "timestamp", "amount", "credits"
}

ALLOWED_ORDER_DIRECTIONS = {"ASC", "DESC", "asc", "desc"}


def _validate_order_by(order_by: str) -> str:
    """
    Validate and sanitize ORDER BY clause to prevent SQL injection.
    
    Args:
        order_by: String like "created_at DESC" or "name ASC"
    
    Returns:
        Sanitized order_by string
    
    Raises:
        ValueError: If column or direction is not allowed
    """
    parts = order_by.strip().split()
    
    if len(parts) == 1:
        column = parts[0]
        direction = "ASC"
    elif len(parts) == 2:
        column, direction = parts
    else:
        raise ValueError(f"Invalid order_by format: {order_by}")
    
    if column.lower() not in {c.lower() for c in ALLOWED_ORDER_COLUMNS}:
        raise ValueError(f"Column '{column}' not allowed in ORDER BY")
    
    if direction.upper() not in ALLOWED_ORDER_DIRECTIONS:
        raise ValueError(f"Direction '{direction}' not allowed")
    
    return f"{column} {direction.upper()}"


def _validate_column_names(columns: list) -> bool:
    """
    Validate that all column names are allowed.
    Only alphanumeric characters and underscores allowed.
    """
    import re
    pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    return all(pattern.match(col) for col in columns)


class Repository:
    """Base repository class for database operations"""
    
    table_name: str = ""
    
    def __init__(self):
        if not self.table_name:
            raise ValueError("table_name must be set")
        # Validate table name format
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.table_name):
            raise ValueError(f"Invalid table name: {self.table_name}")
    
    async def find_by_id(self, id: str) -> Optional[Dict]:
        """Find record by ID"""
        async with get_db() as db:
            return await db.fetch_one(
                f"SELECT * FROM {self.table_name} WHERE id = :id",
                {"id": id}
            )
    
    async def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at DESC",
    ) -> List[Dict]:
        """Find all records with pagination"""
        # Validate and sanitize order_by
        safe_order_by = _validate_order_by(order_by)
        
        async with get_db() as db:
            rows = await db.fetch_all(
                f"""
                SELECT * FROM {self.table_name}
                ORDER BY {safe_order_by}
                LIMIT :limit OFFSET :offset
                """,
                {"limit": limit, "offset": offset}
            )
            return [dict(row) for row in rows]
    
    async def find_by(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
    ) -> List[Dict]:
        """Find records by filters"""
        # Validate column names to prevent SQL injection
        if not _validate_column_names(list(filters.keys())):
            raise ValueError("Invalid column names in filters")
        
        conditions = " AND ".join([f"{k} = :{k}" for k in filters.keys()])
        
        async with get_db() as db:
            rows = await db.fetch_all(
                f"""
                SELECT * FROM {self.table_name}
                WHERE {conditions}
                LIMIT :limit
                """,
                {**filters, "limit": limit}
            )
            return [dict(row) for row in rows]
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count records"""
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        values = {}
        
        if filters:
            # Validate column names
            if not _validate_column_names(list(filters.keys())):
                raise ValueError("Invalid column names in filters")
            conditions = " AND ".join([f"{k} = :{k}" for k in filters.keys()])
            query += f" WHERE {conditions}"
            values = filters
        
        async with get_db() as db:
            return await db.fetch_val(query, values)
    
    async def create(self, data: Dict[str, Any]) -> str:
        """Create a new record"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f":{k}" for k in data.keys()])
        
        async with get_db() as db:
            await db.execute(
                f"""
                INSERT INTO {self.table_name} ({columns})
                VALUES ({placeholders})
                """,
                data
            )
            return data.get("id")
    
    async def update(
        self,
        id: str,
        data: Dict[str, Any],
    ) -> bool:
        """Update a record"""
        set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
        
        async with get_db() as db:
            result = await db.execute(
                f"""
                UPDATE {self.table_name}
                SET {set_clause}, updated_at = NOW()
                WHERE id = :id
                """,
                {**data, "id": id}
            )
            return result > 0
    
    async def delete(self, id: str) -> bool:
        """Delete a record"""
        async with get_db() as db:
            result = await db.execute(
                f"DELETE FROM {self.table_name} WHERE id = :id",
                {"id": id}
            )
            return result > 0
    
    async def exists(self, id: str) -> bool:
        """Check if record exists"""
        async with get_db() as db:
            count = await db.fetch_val(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE id = :id",
                {"id": id}
            )
            return count > 0


# Utility functions
async def execute_raw(query: str, values: Dict = None) -> Any:
    """Execute raw SQL query"""
    async with get_db() as db:
        return await db.execute(query, values)


async def fetch_raw(query: str, values: Dict = None) -> List[Dict]:
    """Fetch results from raw SQL query"""
    async with get_db() as db:
        rows = await db.fetch_all(query, values)
        return [dict(row) for row in rows]
