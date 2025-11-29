"""
PostgreSQL Shared Module Unit Tests
Tests for Singleton behavior and reconnection logic
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestPostgresManagerSingleton:
    """Test PostgresManager Singleton pattern"""
    
    def test_singleton_returns_same_instance(self):
        """Test that PostgresManager returns the same instance"""
        from shared.postgres import PostgresManager
        
        # Reset singleton for test isolation
        PostgresManager._instance = None
        PostgresManager._database = None
        
        manager1 = PostgresManager()
        manager2 = PostgresManager()
        
        assert manager1 is manager2
    
    def test_singleton_maintains_state(self):
        """Test that singleton maintains state across instances"""
        from shared.postgres import PostgresManager
        
        PostgresManager._instance = None
        PostgresManager._database = None
        
        manager1 = PostgresManager()
        manager1._test_attribute = "test_value"
        
        manager2 = PostgresManager()
        
        assert hasattr(manager2, '_test_attribute')
        assert manager2._test_attribute == "test_value"


class TestPostgresManagerInit:
    """Test PostgresManager initialization"""
    
    @pytest.fixture
    def fresh_manager(self):
        """Create a fresh manager with reset state"""
        from shared.postgres import PostgresManager
        PostgresManager._instance = None
        PostgresManager._database = None
        return PostgresManager()
    
    @pytest.mark.asyncio
    async def test_init_creates_connection(self, fresh_manager):
        """Test init creates database connection"""
        mock_db = AsyncMock()
        mock_db.connect = AsyncMock()
        
        with patch('shared.postgres.Database', return_value=mock_db):
            with patch('shared.postgres.settings') as mock_settings:
                mock_settings.database.url = "postgresql://test@localhost/test"
                mock_settings.database.min_connections = 1
                mock_settings.database.max_connections = 5
                mock_settings.database.host = "localhost"
                mock_settings.database.port = 5432
                mock_settings.database.name = "test"
                
                await fresh_manager.init()
        
        mock_db.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_init_skips_if_already_connected(self, fresh_manager):
        """Test init does nothing if already connected"""
        # Simulate existing connection
        fresh_manager._database = AsyncMock()
        
        with patch('shared.postgres.Database') as mock_db_class:
            await fresh_manager.init()
        
        # Should not create new Database
        mock_db_class.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_init_raises_on_connection_failure(self, fresh_manager):
        """Test init raises exception on connection failure"""
        mock_db = AsyncMock()
        mock_db.connect = AsyncMock(side_effect=Exception("Connection refused"))
        
        with patch('shared.postgres.Database', return_value=mock_db):
            with patch('shared.postgres.settings') as mock_settings:
                mock_settings.database.url = "postgresql://test@localhost/test"
                mock_settings.database.min_connections = 1
                mock_settings.database.max_connections = 5
                
                with pytest.raises(Exception, match="Connection refused"):
                    await fresh_manager.init()


class TestPostgresManagerClose:
    """Test PostgresManager close behavior"""
    
    @pytest.fixture
    def manager_with_connection(self):
        """Create manager with mocked connection"""
        from shared.postgres import PostgresManager
        PostgresManager._instance = None
        PostgresManager._database = None
        
        manager = PostgresManager()
        manager._database = AsyncMock()
        manager._database.disconnect = AsyncMock()
        return manager
    
    @pytest.mark.asyncio
    async def test_close_disconnects_database(self, manager_with_connection):
        """Test close properly disconnects"""
        # Store reference before close (which sets _database to None)
        db_ref = manager_with_connection._database
        
        await manager_with_connection.close()
        
        db_ref.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_sets_database_to_none(self, manager_with_connection):
        """Test close resets database reference"""
        await manager_with_connection.close()
        
        assert manager_with_connection._database is None


class TestPostgresManagerDatabase:
    """Test database property access"""
    
    def test_database_raises_when_not_initialized(self):
        """Test accessing database before init raises RuntimeError"""
        from shared.postgres import PostgresManager
        PostgresManager._instance = None
        PostgresManager._database = None
        
        manager = PostgresManager()
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            _ = manager.database
    
    def test_database_returns_connection_when_initialized(self):
        """Test database returns connection when available"""
        from shared.postgres import PostgresManager
        PostgresManager._instance = None
        PostgresManager._database = None
        
        manager = PostgresManager()
        mock_db = MagicMock()
        manager._database = mock_db
        
        assert manager.database is mock_db


class TestModuleFunctions:
    """Test module-level utility functions"""
    
    @pytest.fixture(autouse=True)
    def reset_manager(self):
        """Reset manager before each test"""
        from shared.postgres import PostgresManager
        PostgresManager._instance = None
        PostgresManager._database = None
        yield
    
    @pytest.mark.asyncio
    async def test_init_db_calls_manager_init(self):
        """Test init_db function calls manager.init()"""
        from shared.postgres import init_db
        
        mock_db = AsyncMock()
        mock_db.connect = AsyncMock()
        
        with patch('shared.postgres.Database', return_value=mock_db):
            with patch('shared.postgres.settings') as mock_settings:
                mock_settings.database.url = "postgresql://test@localhost/test"
                mock_settings.database.min_connections = 1
                mock_settings.database.max_connections = 5
                mock_settings.database.host = "localhost"
                mock_settings.database.port = 5432
                mock_settings.database.name = "test"
                
                await init_db()
        
        mock_db.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_db_calls_manager_close(self):
        """Test close_db function calls manager.close()"""
        from shared.postgres import close_db, _manager
        
        mock_db = AsyncMock()
        mock_db.disconnect = AsyncMock()
        _manager._database = mock_db
        
        await close_db()
        
        mock_db.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_database_returns_database(self):
        """Test get_database returns the database instance"""
        from shared.postgres import get_database, _manager
        
        mock_db = AsyncMock()
        mock_db.connect = AsyncMock()
        _manager._database = mock_db
        
        result = await get_database()
        
        assert result is mock_db


class TestDBSession:
    """Test DBSession transaction support"""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database for session"""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.execute_many = AsyncMock()
        db.fetch_one = AsyncMock(return_value={"id": 1})
        db.fetch_all = AsyncMock(return_value=[{"id": 1}, {"id": 2}])
        db.fetch_val = AsyncMock(return_value=42)
        db.transaction = MagicMock()
        return db
    
    @pytest.fixture
    def session(self, mock_database):
        """Create DBSession instance"""
        from shared.postgres import DBSession
        return DBSession(mock_database)
    
    @pytest.mark.asyncio
    async def test_execute_query(self, session, mock_database):
        """Test execute runs query"""
        await session.execute("INSERT INTO test VALUES (:val)", {"val": 1})
        
        mock_database.execute.assert_called_once_with(
            query="INSERT INTO test VALUES (:val)",
            values={"val": 1}
        )
    
    @pytest.mark.asyncio
    async def test_execute_many(self, session, mock_database):
        """Test execute_many runs batch queries"""
        values = [{"val": 1}, {"val": 2}]
        await session.execute_many("INSERT INTO test VALUES (:val)", values)
        
        mock_database.execute_many.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_one(self, session, mock_database):
        """Test fetch_one returns dict or None"""
        result = await session.fetch_one("SELECT * FROM test WHERE id = :id", {"id": 1})
        
        assert result == {"id": 1}
    
    @pytest.mark.asyncio
    async def test_fetch_one_returns_none(self, session, mock_database):
        """Test fetch_one returns None when no result"""
        mock_database.fetch_one = AsyncMock(return_value=None)
        
        result = await session.fetch_one("SELECT * FROM test WHERE id = :id", {"id": 999})
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_all(self, session, mock_database):
        """Test fetch_all returns list of dicts"""
        result = await session.fetch_all("SELECT * FROM test")
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_fetch_val(self, session, mock_database):
        """Test fetch_val returns single value"""
        result = await session.fetch_val("SELECT COUNT(*) FROM test")
        
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_begin_starts_transaction(self, session, mock_database):
        """Test begin starts a transaction"""
        mock_tx = AsyncMock()
        mock_tx.start = AsyncMock()
        # transaction() returns awaitable that resolves to mock_tx
        mock_database.transaction = AsyncMock(return_value=mock_tx)
        
        await session.begin()
        
        mock_tx.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_commit_commits_transaction(self, session, mock_database):
        """Test commit commits the transaction"""
        mock_tx = AsyncMock()
        mock_tx.start = AsyncMock()
        mock_tx.commit = AsyncMock()
        mock_database.transaction = AsyncMock(return_value=mock_tx)
        
        await session.begin()
        await session.commit()
        
        mock_tx.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback_rolls_back_transaction(self, session, mock_database):
        """Test rollback rolls back the transaction"""
        mock_tx = AsyncMock()
        mock_tx.start = AsyncMock()
        mock_tx.rollback = AsyncMock()
        mock_database.transaction = AsyncMock(return_value=mock_tx)
        
        await session.begin()
        await session.rollback()
        
        mock_tx.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_commits_on_success(self, session, mock_database):
        """Test context manager commits on success"""
        mock_tx = AsyncMock()
        mock_tx.start = AsyncMock()
        mock_tx.commit = AsyncMock()
        mock_database.transaction = AsyncMock(return_value=mock_tx)
        
        async with session:
            pass  # Success path
        
        mock_tx.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_rollback_on_exception(self, session, mock_database):
        """Test context manager rolls back on exception"""
        mock_tx = AsyncMock()
        mock_tx.start = AsyncMock()
        mock_tx.rollback = AsyncMock()
        mock_database.transaction = AsyncMock(return_value=mock_tx)
        
        with pytest.raises(ValueError):
            async with session:
                raise ValueError("Test error")
        
        mock_tx.rollback.assert_called_once()


class TestRepository:
    """Test base Repository class"""
    
    @pytest.fixture
    def mock_db_context(self):
        """Create mock for get_db context manager"""
        mock_db = AsyncMock()
        mock_db.fetch_one = AsyncMock()
        mock_db.fetch_all = AsyncMock(return_value=[])
        mock_db.fetch_val = AsyncMock(return_value=0)
        mock_db.execute = AsyncMock()
        return mock_db
    
    def test_repository_requires_table_name(self):
        """Test Repository raises error without table_name"""
        from shared.postgres import Repository
        
        class BadRepo(Repository):
            pass
        
        with pytest.raises(ValueError, match="table_name must be set"):
            BadRepo()
    
    def test_repository_with_table_name(self):
        """Test Repository works with table_name set"""
        from shared.postgres import Repository
        
        class GoodRepo(Repository):
            table_name = "users"
        
        repo = GoodRepo()
        assert repo.table_name == "users"
