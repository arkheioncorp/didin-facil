"""
Unit tests for Multi-Account Management Routes
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
import json


class MockUser:
    id = "user_123"
    email = "test@example.com"


@pytest.fixture
def mock_current_user():
    return MockUser()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.get.return_value = None
    redis.set.return_value = True
    redis.hgetall.return_value = {}
    redis.hset.return_value = True
    redis.delete.return_value = 1
    redis.keys.return_value = []
    redis.smembers.return_value = set()
    redis.sadd.return_value = 1
    redis.srem.return_value = 1
    return redis


class TestMultiAccountService:
    """Tests for MultiAccountService"""
    
    @pytest.mark.asyncio
    async def test_create_account(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service, AccountCreate, Platform
        
        mock_redis.smembers.return_value = set()  # No existing accounts
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            data = AccountCreate(
                platform=Platform.INSTAGRAM,
                username="test_account",
                display_name="Test Account",
                is_primary=True
            )
            
            account = await account_service.create(str(mock_current_user.id), data)
            
            assert account.username == "test_account"
            assert account.platform == "instagram"
            assert account.is_primary is True
            mock_redis.hset.assert_called()
            mock_redis.sadd.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_duplicate_account(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service, AccountCreate, Platform
        
        # Existing account
        mock_redis.smembers.return_value = {"account-1"}
        mock_redis.hgetall.return_value = {
            "id": "account-1",
            "platform": "instagram",
            "username": "test_account",
            "display_name": "Test",
            "status": "active",
            "is_primary": "True",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metrics": "{}",
            "metadata": "{}"
        }
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            data = AccountCreate(
                platform=Platform.INSTAGRAM,
                username="test_account",
                is_primary=False
            )
            
            with pytest.raises(ValueError) as exc:
                await account_service.create(str(mock_current_user.id), data)
            
            assert "already exists" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_get_account(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service
        
        mock_redis.hgetall.return_value = {
            "id": "account-123",
            "platform": "instagram",
            "username": "my_account",
            "display_name": "My Account",
            "profile_url": "https://instagram.com/my_account",
            "profile_image": "",
            "status": "active",
            "is_primary": "True",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_used_at": "",
            "metrics": json.dumps({"followers": 1000}),
            "metadata": "{}"
        }
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            account = await account_service.get(str(mock_current_user.id), "account-123")
            
            assert account is not None
            assert account.id == "account-123"
            assert account.username == "my_account"
            assert account.metrics["followers"] == 1000
    
    @pytest.mark.asyncio
    async def test_get_account_not_found(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service
        
        mock_redis.hgetall.return_value = {}
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            account = await account_service.get(str(mock_current_user.id), "nonexistent")
            assert account is None
    
    @pytest.mark.asyncio
    async def test_list_accounts(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service
        
        mock_redis.smembers.return_value = {"account-1", "account-2"}
        mock_redis.hgetall.side_effect = [
            {
                "id": "account-1",
                "platform": "instagram",
                "username": "account1",
                "display_name": "Account 1",
                "status": "active",
                "is_primary": "True",
                "user_id": "user_123",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metrics": "{}",
                "metadata": "{}"
            },
            {
                "id": "account-2",
                "platform": "tiktok",
                "username": "account2",
                "display_name": "Account 2",
                "status": "active",
                "is_primary": "False",
                "user_id": "user_123",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metrics": "{}",
                "metadata": "{}"
            }
        ]
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            accounts = await account_service.list(str(mock_current_user.id))
            
            assert len(accounts) == 2
            # Primary should come first
            assert accounts[0].is_primary is True
    
    @pytest.mark.asyncio
    async def test_list_accounts_by_platform(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service
        
        mock_redis.smembers.return_value = {"account-1"}
        mock_redis.hgetall.return_value = {
            "id": "account-1",
            "platform": "instagram",
            "username": "insta_account",
            "display_name": "Instagram Account",
            "status": "active",
            "is_primary": "True",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metrics": "{}",
            "metadata": "{}"
        }
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            accounts = await account_service.list_by_platform(
                str(mock_current_user.id),
                "instagram"
            )
            
            assert len(accounts) == 1
            assert accounts[0].platform == "instagram"
    
    @pytest.mark.asyncio
    async def test_update_account(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service, AccountUpdate, AccountStatus
        
        mock_redis.hgetall.return_value = {
            "id": "account-123",
            "platform": "instagram",
            "username": "old_name",
            "display_name": "Old Display",
            "status": "active",
            "is_primary": "False",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metrics": "{}",
            "metadata": "{}"
        }
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            update_data = AccountUpdate(
                display_name="New Display",
                status=AccountStatus.INACTIVE
            )
            
            await account_service.update(
                str(mock_current_user.id),
                "account-123",
                update_data
            )
            
            mock_redis.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_account(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service
        
        mock_redis.hgetall.return_value = {
            "id": "account-123",
            "platform": "instagram",
            "username": "to_delete",
            "display_name": "Delete Me",
            "status": "active",
            "is_primary": "False",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metrics": "{}",
            "metadata": "{}"
        }
        mock_redis.delete.return_value = 1
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            result = await account_service.delete(str(mock_current_user.id), "account-123")
            
            assert result is True
            mock_redis.delete.assert_called()
            mock_redis.srem.assert_called()
    
    @pytest.mark.asyncio
    async def test_switch_account(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service
        
        mock_redis.hgetall.return_value = {
            "id": "account-123",
            "platform": "instagram",
            "username": "switch_to",
            "display_name": "Switch To",
            "status": "active",
            "is_primary": "False",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_used_at": "",
            "metrics": "{}",
            "metadata": "{}"
        }
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            await account_service.switch(str(mock_current_user.id), "account-123")
            
            # Should update last_used_at
            mock_redis.hset.assert_called()
            # Should set active account
            mock_redis.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_active_account(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service
        
        mock_redis.get.return_value = "account-123"
        mock_redis.hgetall.return_value = {
            "id": "account-123",
            "platform": "instagram",
            "username": "active_account",
            "display_name": "Active Account",
            "status": "active",
            "is_primary": "True",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metrics": "{}",
            "metadata": "{}"
        }
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            account = await account_service.get_active(str(mock_current_user.id), "instagram")
            
            assert account is not None
            assert account.id == "account-123"
    
    @pytest.mark.asyncio
    async def test_get_active_fallback_to_primary(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service
        
        mock_redis.get.return_value = None  # No active account set
        mock_redis.smembers.return_value = {"account-1"}
        mock_redis.hgetall.return_value = {
            "id": "account-1",
            "platform": "instagram",
            "username": "primary_account",
            "display_name": "Primary",
            "status": "active",
            "is_primary": "True",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metrics": "{}",
            "metadata": "{}"
        }
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            account = await account_service.get_active(str(mock_current_user.id), "instagram")
            
            # Should fallback to primary
            assert account is not None
            assert account.is_primary is True
    
    @pytest.mark.asyncio
    async def test_update_metrics(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service, AccountMetrics
        
        mock_redis.hgetall.return_value = {
            "id": "account-123",
            "platform": "instagram",
            "username": "metrics_account",
            "display_name": "Metrics",
            "status": "active",
            "is_primary": "False",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metrics": "{}",
            "metadata": "{}"
        }
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            metrics = AccountMetrics(
                followers=5000,
                following=500,
                posts=100,
                engagement_rate=5.5
            )
            
            await account_service.update_metrics(
                str(mock_current_user.id),
                "account-123",
                metrics
            )
            
            mock_redis.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_summary(self, mock_current_user, mock_redis):
        from api.routes.accounts import account_service
        
        mock_redis.smembers.return_value = {"account-1", "account-2"}
        mock_redis.hgetall.side_effect = [
            {
                "id": "account-1",
                "platform": "instagram",
                "username": "insta1",
                "display_name": "Instagram 1",
                "status": "active",
                "is_primary": "True",
                "user_id": "user_123",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metrics": json.dumps({"followers": 1000}),
                "metadata": "{}"
            },
            {
                "id": "account-2",
                "platform": "tiktok",
                "username": "tiktok1",
                "display_name": "TikTok 1",
                "status": "needs_reauth",
                "is_primary": "True",
                "user_id": "user_123",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metrics": json.dumps({"followers": 2000}),
                "metadata": "{}"
            }
        ]
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            summary = await account_service.get_summary(str(mock_current_user.id))
            
            assert summary["total_accounts"] == 2
            assert summary["total_followers"] == 3000
            assert "instagram" in summary["by_platform"]
            assert "tiktok" in summary["by_platform"]
            assert summary["by_platform"]["instagram"]["active"] == 1
            assert summary["by_platform"]["tiktok"]["needs_reauth"] == 1


class TestAccountRoutes:
    """Tests for account HTTP endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_accounts_endpoint(self, mock_current_user, mock_redis):
        from api.routes.accounts import list_accounts
        
        mock_redis.smembers.return_value = set()
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            result = await list_accounts(
                platform=None,
                current_user=mock_current_user
            )
            
            assert "accounts" in result
    
    @pytest.mark.asyncio
    async def test_get_summary_endpoint(self, mock_current_user, mock_redis):
        from api.routes.accounts import get_accounts_summary
        
        mock_redis.smembers.return_value = set()
        
        with patch("api.routes.accounts.redis_client", mock_redis):
            result = await get_accounts_summary(current_user=mock_current_user)
            
            assert "total_accounts" in result
            assert "by_platform" in result


class TestAccountValidation:
    """Tests for account validation"""
    
    def test_account_create_validation(self):
        from api.routes.accounts import AccountCreate, Platform
        
        # Valid account
        account = AccountCreate(
            platform=Platform.INSTAGRAM,
            username="valid_user"
        )
        assert account.username == "valid_user"
    
    def test_account_username_too_long(self):
        from api.routes.accounts import AccountCreate, Platform
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            AccountCreate(
                platform=Platform.INSTAGRAM,
                username="a" * 101  # Max is 100
            )
    
    def test_account_status_enum(self):
        from api.routes.accounts import AccountStatus
        
        assert AccountStatus.ACTIVE.value == "active"
        assert AccountStatus.INACTIVE.value == "inactive"
        assert AccountStatus.SUSPENDED.value == "suspended"
        assert AccountStatus.NEEDS_REAUTH.value == "needs_reauth"
