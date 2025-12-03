from unittest.mock import AsyncMock, patch

import pytest
from shared.postgres import (DBSession, PostgresManager, Repository, close_db,
                             execute_raw, fetch_raw, get_database, get_db,
                             init_db)


@pytest.fixture
def mock_database():
    with patch("shared.postgres.Database") as mock:
        db_instance = AsyncMock()
        mock.return_value = db_instance
        yield db_instance

@pytest.fixture
async def postgres_manager(mock_database):
    # Reset singleton
    PostgresManager._instance = None
    manager = PostgresManager()
    manager._database = None
    yield manager
    # Cleanup
    if manager._database:
        await manager.close()
    PostgresManager._instance = None

@pytest.mark.asyncio
async def test_postgres_manager_singleton():
    m1 = PostgresManager()
    m2 = PostgresManager()
    assert m1 is m2

@pytest.mark.asyncio
async def test_postgres_manager_init(postgres_manager, mock_database):
    await postgres_manager.init()
    
    mock_database.connect.assert_called_once()
    assert postgres_manager._database is mock_database

@pytest.mark.asyncio
async def test_postgres_manager_init_already_initialized(postgres_manager, mock_database):
    postgres_manager._database = mock_database
    await postgres_manager.init()
    
    # Should not call connect again
    mock_database.connect.assert_not_called()

@pytest.mark.asyncio
async def test_postgres_manager_init_failure(postgres_manager, mock_database):
    mock_database.connect.side_effect = Exception("Connection error")
    
    with pytest.raises(Exception, match="Connection error"):
        await postgres_manager.init()

@pytest.mark.asyncio
async def test_postgres_manager_close(postgres_manager, mock_database):
    postgres_manager._database = mock_database
    await postgres_manager.close()
    
    mock_database.disconnect.assert_called_once()
    assert postgres_manager._database is None

@pytest.mark.asyncio
async def test_postgres_manager_get_database_not_initialized(postgres_manager):
    with pytest.raises(RuntimeError, match="Database not initialized"):
        _ = postgres_manager.database

@pytest.mark.asyncio
async def test_global_functions(postgres_manager, mock_database):
    # Mock the global _manager in the module
    with patch("shared.postgres._manager", postgres_manager):
        await init_db()
        mock_database.connect.assert_called_once()
        
        db = await get_database()
        assert db is mock_database
        
        await close_db()
        mock_database.disconnect.assert_called_once()

@pytest.mark.asyncio
async def test_get_db_context_manager(postgres_manager, mock_database):
    postgres_manager._database = mock_database
    with patch("shared.postgres._manager", postgres_manager):
        async with get_db() as db:
            assert db is mock_database

@pytest.mark.asyncio
async def test_dbsession(mock_database):
    session = DBSession(mock_database)
    
    # Test execute
    await session.execute("SELECT 1")
    mock_database.execute.assert_called_with(query="SELECT 1", values=None)
    
    # Test fetch_one
    mock_database.fetch_one.return_value = {"id": 1}
    result = await session.fetch_one("SELECT *")
    assert result == {"id": 1}
    
    # Test fetch_all
    mock_database.fetch_all.return_value = [{"id": 1}, {"id": 2}]
    result = await session.fetch_all("SELECT *")
    assert len(result) == 2
    
    # Test transaction
    transaction_mock = AsyncMock()
    mock_database.transaction.return_value = transaction_mock
    
    async with session:
        pass
        
    mock_database.transaction.assert_called_once()
    transaction_mock.start.assert_called_once()
    transaction_mock.commit.assert_called_once()

@pytest.mark.asyncio
async def test_dbsession_rollback(mock_database):
    session = DBSession(mock_database)
    transaction_mock = AsyncMock()
    mock_database.transaction.return_value = transaction_mock
    
    try:
        async with session:
            raise ValueError("Error")
    except ValueError:
        pass
        
    transaction_mock.rollback.assert_called_once()

class _TestRepo(Repository):
    """Helper class for testing Repository - named with underscore to avoid pytest collection"""
    table_name = "test_table"

@pytest.mark.asyncio
async def test_repository_methods(postgres_manager, mock_database):
    postgres_manager._database = mock_database
    repo = _TestRepo()
    
    with patch("shared.postgres._manager", postgres_manager):
        # Test find_by_id
        mock_database.fetch_one.return_value = {"id": "123", "name": "test"}
        result = await repo.find_by_id("123")
        assert result["id"] == "123"
        
        # Test find_all
        mock_database.fetch_all.return_value = [{"id": "1"}, {"id": "2"}]
        results = await repo.find_all(limit=10)
        assert len(results) == 2
        
        # Test create
        await repo.create({"name": "new"})
        mock_database.execute.assert_called()
        
        # Test update
        mock_database.execute.return_value = 1
        success = await repo.update("123", {"name": "updated"})
        assert success is True
        
        # Test delete
        mock_database.execute.return_value = 1
        success = await repo.delete("123")
        assert success is True

@pytest.mark.asyncio
async def test_execute_raw_fetch_raw(postgres_manager, mock_database):
    postgres_manager._database = mock_database
    with patch("shared.postgres._manager", postgres_manager):
        await execute_raw("UPDATE table SET x=1")
        mock_database.execute.assert_called()
        
        mock_database.fetch_all.return_value = [{"x": 1}]
        result = await fetch_raw("SELECT x FROM table")
        assert result == [{"x": 1}]
