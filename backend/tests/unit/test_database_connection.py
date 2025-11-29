"""
Testes unitários para api/database/connection.py
Cobertura: init, close, get_db, DatabaseManager
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestDatabaseConnection:
    """Testes para funções de conexão"""
    
    @pytest.mark.asyncio
    async def test_init_database(self):
        """Deve conectar ao banco"""
        with patch('api.database.connection.database') as mock_db:
            mock_db.connect = AsyncMock()
            
            from api.database.connection import init_database
            
            await init_database()
            
            mock_db.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_database(self):
        """Deve desconectar do banco"""
        with patch('api.database.connection.database') as mock_db:
            mock_db.disconnect = AsyncMock()
            
            from api.database.connection import close_database
            
            await close_database()
            
            mock_db.disconnect.assert_called_once()


class TestGetDb:
    """Testes para get_db context manager"""
    
    @pytest.mark.asyncio
    async def test_get_db_yields_database(self):
        """Deve retornar instância do database"""
        from api.database.connection import get_db, database
        
        async with get_db() as db:
            assert db == database


class TestDatabaseManager:
    """Testes para DatabaseManager"""
    
    def test_manager_init(self):
        """Deve inicializar com database"""
        from api.database.connection import DatabaseManager, database
        
        manager = DatabaseManager()
        assert manager.db == database
    
    @pytest.mark.asyncio
    async def test_manager_transaction(self):
        """Deve criar transação"""
        with patch('api.database.connection.database') as mock_db:
            mock_transaction = AsyncMock()
            mock_transaction.__aenter__ = AsyncMock(return_value=None)
            mock_transaction.__aexit__ = AsyncMock(return_value=None)
            mock_db.transaction = MagicMock(return_value=mock_transaction)
            
            from api.database.connection import DatabaseManager
            
            manager = DatabaseManager()
            async with manager.transaction():
                pass
            
            mock_db.transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_manager_execute(self):
        """Deve executar query"""
        with patch('api.database.connection.database') as mock_db:
            mock_db.execute = AsyncMock(return_value=1)
            
            from api.database.connection import DatabaseManager
            
            manager = DatabaseManager()
            await manager.execute("INSERT INTO test", {"val": 1})
            
            mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_manager_fetch_one(self):
        """Deve buscar uma linha"""
        with patch('api.database.connection.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value={"id": 1})
            
            from api.database.connection import DatabaseManager
            
            manager = DatabaseManager()
            result = await manager.fetch_one("SELECT * FROM test")
            
            assert result["id"] == 1
    
    @pytest.mark.asyncio
    async def test_manager_fetch_all(self):
        """Deve buscar todas as linhas"""
        with patch('api.database.connection.database') as mock_db:
            mock_db.fetch_all = AsyncMock(return_value=[
                {"id": 1}, {"id": 2}
            ])
            
            from api.database.connection import DatabaseManager
            
            manager = DatabaseManager()
            result = await manager.fetch_all("SELECT * FROM test")
            
            assert len(result) == 2
