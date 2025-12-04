"""
Comprehensive tests for BlacklistService
Tests for JWT token blacklisting functionality
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestBlacklistService:
    """Test suite for BlacklistService"""
    
    @pytest.fixture
    def blacklist_service(self):
        """Create BlacklistService instance"""
        from api.services.blacklist import BlacklistService
        return BlacklistService()
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        mock = AsyncMock()
        mock.setex = AsyncMock(return_value=True)
        mock.exists = AsyncMock(return_value=0)
        mock.get = AsyncMock(return_value=None)
        mock.delete = AsyncMock(return_value=1)
        return mock

    @pytest.mark.asyncio
    async def test_init_sets_prefix(self, blacklist_service):
        """Test that BlacklistService initializes with correct prefix"""
        assert blacklist_service.prefix == "blacklist:"
    
    @pytest.mark.asyncio
    async def test_add_token_to_blacklist(self, blacklist_service, mock_redis):
        """Test adding a token to the blacklist"""
        with patch('api.services.blacklist.get_redis_pool', return_value=mock_redis):
            token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_token"
            ttl = 3600
            
            result = await blacklist_service.add(token, ttl)
            
            assert result is True
            mock_redis.setex.assert_called_once_with(
                f"blacklist:{token}",
                ttl,
                "revoked"
            )
    
    @pytest.mark.asyncio
    async def test_add_token_with_different_ttl(self, blacklist_service, mock_redis):
        """Test adding tokens with different TTLs"""
        with patch('api.services.blacklist.get_redis_pool', return_value=mock_redis):
            # Short TTL (access token)
            result1 = await blacklist_service.add("token1", 900)  # 15 min
            assert result1 is True
            
            # Long TTL (refresh token)
            result2 = await blacklist_service.add("token2", 86400)  # 1 day
            assert result2 is True
            
            assert mock_redis.setex.call_count == 2
    
    @pytest.mark.asyncio
    async def test_is_blacklisted_returns_true_for_blacklisted_token(
        self, blacklist_service, mock_redis
    ):
        """Test that is_blacklisted returns True for blacklisted tokens"""
        mock_redis.exists = AsyncMock(return_value=1)
        
        with patch('api.services.blacklist.get_redis_pool', return_value=mock_redis):
            token = "blacklisted_token"
            
            result = await blacklist_service.is_blacklisted(token)
            
            assert result is True
            mock_redis.exists.assert_called_once_with(f"blacklist:{token}")
    
    @pytest.mark.asyncio
    async def test_is_blacklisted_returns_false_for_valid_token(
        self, blacklist_service, mock_redis
    ):
        """Test that is_blacklisted returns False for valid tokens"""
        mock_redis.exists = AsyncMock(return_value=0)
        
        with patch('api.services.blacklist.get_redis_pool', return_value=mock_redis):
            token = "valid_token"
            
            result = await blacklist_service.is_blacklisted(token)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_prefix_is_applied_correctly(self, blacklist_service, mock_redis):
        """Test that prefix is correctly applied to all operations"""
        mock_redis.exists = AsyncMock(return_value=0)
        
        with patch('api.services.blacklist.get_redis_pool', return_value=mock_redis):
            token = "test_token"
            
            # Test add
            await blacklist_service.add(token, 3600)
            assert mock_redis.setex.call_args[0][0].startswith("blacklist:")
            
            # Test is_blacklisted
            await blacklist_service.is_blacklisted(token)
            assert mock_redis.exists.call_args[0][0].startswith("blacklist:")
    
    @pytest.mark.asyncio
    async def test_add_and_check_integration(self, blacklist_service, mock_redis):
        """Test adding and checking a token in sequence"""
        # Track added tokens
        blacklisted_tokens = set()
        
        async def mock_setex(key, ttl, value):
            blacklisted_tokens.add(key)
            return True
        
        async def mock_exists(key):
            return 1 if key in blacklisted_tokens else 0
        
        mock_redis.setex = mock_setex
        mock_redis.exists = mock_exists
        
        with patch('api.services.blacklist.get_redis_pool', return_value=mock_redis):
            token = "new_token"
            
            # Initially not blacklisted
            assert await blacklist_service.is_blacklisted(token) is False
            
            # Add to blacklist
            await blacklist_service.add(token, 3600)
            
            # Now should be blacklisted
            assert await blacklist_service.is_blacklisted(token) is True


class TestBlacklistServiceEdgeCases:
    """Edge cases and error handling tests"""
    
    @pytest.fixture
    def blacklist_service(self):
        from api.services.blacklist import BlacklistService
        return BlacklistService()
    
    @pytest.mark.asyncio
    async def test_empty_token(self):
        """Test handling of empty token"""
        from api.services.blacklist import BlacklistService
        service = BlacklistService()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.exists = AsyncMock(return_value=0)
        
        with patch('api.services.blacklist.get_redis_pool', return_value=mock_redis):
            # Empty string token should still work (Redis allows it)
            result = await service.add("", 3600)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_very_long_token(self):
        """Test handling of very long token"""
        from api.services.blacklist import BlacklistService
        service = BlacklistService()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)
        
        with patch('api.services.blacklist.get_redis_pool', return_value=mock_redis):
            long_token = "x" * 10000
            result = await service.add(long_token, 3600)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_special_characters_in_token(self):
        """Test handling of special characters in token"""
        from api.services.blacklist import BlacklistService
        service = BlacklistService()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.exists = AsyncMock(return_value=1)
        
        with patch('api.services.blacklist.get_redis_pool', return_value=mock_redis):
            special_token = "token:with:colons:and.dots!special@chars#123"
            
            result = await service.add(special_token, 3600)
            assert result is True
            
            is_blocked = await service.is_blacklisted(special_token)
            assert is_blocked is True
    
    @pytest.mark.asyncio
    async def test_zero_ttl(self):
        """Test handling of zero TTL"""
        from api.services.blacklist import BlacklistService
        service = BlacklistService()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)
        
        with patch('api.services.blacklist.get_redis_pool', return_value=mock_redis):
            result = await service.add("token", 0)
            assert result is True
            mock_redis.setex.assert_called_with("blacklist:token", 0, "revoked")
    
    @pytest.mark.asyncio
    async def test_negative_ttl(self):
        """Test handling of negative TTL (Redis behavior)"""
        from api.services.blacklist import BlacklistService
        service = BlacklistService()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)
        
        with patch('api.services.blacklist.get_redis_pool', return_value=mock_redis):
            # Negative TTL - Redis will handle this
            result = await service.add("token", -1)
            assert result is True
