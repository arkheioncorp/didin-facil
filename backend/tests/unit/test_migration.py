"""
Tests for Lifetime Migration Script
"""
# Import the migration module
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

sys.path.insert(0, '/home/jhonslife/TikTrend Finder/backend')

from scripts.migrate_lifetime_users import (MigrationResult,
                                            create_subscription,
                                            get_lifetime_users,
                                            mark_license_migrated,
                                            run_migration, verify_migration)


class TestMigrationResult:
    """Tests for MigrationResult class."""
    
    def test_initial_state(self):
        result = MigrationResult()
        assert result.total_users == 0
        assert result.migrated == 0
        assert result.skipped == 0
        assert result.errors == []
        assert result.migrated_users == []
    
    def test_add_success(self):
        result = MigrationResult()
        result.add_success("user-1", "test@example.com")
        
        assert result.migrated == 1
        assert len(result.migrated_users) == 1
        assert result.migrated_users[0]["id"] == "user-1"
        assert result.migrated_users[0]["email"] == "test@example.com"
    
    def test_add_skip(self):
        result = MigrationResult()
        result.add_skip("user-1", "Already migrated")
        
        assert result.skipped == 1
    
    def test_add_error(self):
        result = MigrationResult()
        result.add_error("user-1", "Database connection failed")
        
        assert len(result.errors) == 1
        assert result.errors[0]["user_id"] == "user-1"
        assert "Database" in result.errors[0]["error"]
    
    def test_summary(self):
        result = MigrationResult()
        result.total_users = 10
        result.migrated = 8
        result.skipped = 1
        result.errors.append({"user_id": "1", "error": "test"})
        
        summary = result.summary()
        assert "10" in summary
        assert "8" in summary
        assert "1" in summary


class TestMigrationFunctions:
    """Tests for migration functions."""
    
    @pytest.fixture
    def mock_pool(self):
        pool = AsyncMock()
        return pool
    
    @pytest.mark.asyncio
    async def test_get_lifetime_users(self, mock_pool):
        """Test fetching lifetime users."""
        mock_pool.fetch = AsyncMock(return_value=[
            {
                "id": uuid4(),
                "email": "user1@example.com",
                "name": "User 1",
                "license_id": uuid4(),
                "license_type": "lifetime",
                "license_created": datetime.now(timezone.utc),
                "features": {}
            }
        ])
        
        users = await get_lifetime_users(mock_pool)
        
        assert len(users) == 1
        assert users[0]["email"] == "user1@example.com"
        mock_pool.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_subscription_dry_run(self, mock_pool):
        """Test subscription creation in dry-run mode."""
        result = await create_subscription(
            mock_pool,
            "user-123",
            "enterprise",
            dry_run=True
        )
        
        assert result == "dry-run-id"
        mock_pool.fetchval.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_subscription_real(self, mock_pool):
        """Test actual subscription creation."""
        mock_pool.fetchval = AsyncMock(return_value="sub-123")
        
        result = await create_subscription(
            mock_pool,
            "user-123",
            "enterprise",
            dry_run=False
        )
        
        assert result == "sub-123"
        mock_pool.fetchval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_license_migrated_dry_run(self, mock_pool):
        """Test marking license as migrated in dry-run mode."""
        await mark_license_migrated(
            mock_pool,
            "license-123",
            "sub-123",
            dry_run=True
        )
        
        mock_pool.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_mark_license_migrated_real(self, mock_pool):
        """Test actually marking license as migrated."""
        mock_pool.execute = AsyncMock()
        
        await mark_license_migrated(
            mock_pool,
            "license-123",
            "sub-123",
            dry_run=False
        )
        
        mock_pool.execute.assert_called_once()


class TestVerifyMigration:
    """Tests for migration verification."""
    
    @pytest.mark.asyncio
    async def test_verify_migration(self):
        """Test verification returns correct stats."""
        mock_pool = AsyncMock()
        mock_pool.fetchval = AsyncMock(side_effect=[100, 80, 20, 80])
        
        stats = await verify_migration(mock_pool)
        
        assert stats["total_lifetime"] == 100
        assert stats["migrated"] == 80
        assert stats["pending"] == 20
        assert stats["active_subscriptions"] == 80
