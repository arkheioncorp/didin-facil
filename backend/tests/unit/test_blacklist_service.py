import pytest
from unittest.mock import AsyncMock, patch
from api.services.blacklist import BlacklistService


@pytest.fixture
def blacklist_service():
    return BlacklistService()


@pytest.mark.asyncio
async def test_blacklist_service_init(blacklist_service):
    assert blacklist_service.prefix == "blacklist:"


@pytest.mark.asyncio
async def test_blacklist_add(blacklist_service):
    mock_redis = AsyncMock()
    
    with patch("api.services.blacklist.get_redis_pool", return_value=mock_redis):
        token = "test_token"
        ttl = 3600
        
        result = await blacklist_service.add(token, ttl)
        
        assert result is True
        mock_redis.setex.assert_called_once_with(
            f"blacklist:{token}",
            ttl,
            "revoked"
        )


@pytest.mark.asyncio
async def test_blacklist_is_blacklisted_true(blacklist_service):
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = 1
    
    with patch("api.services.blacklist.get_redis_pool", return_value=mock_redis):
        token = "test_token"
        
        result = await blacklist_service.is_blacklisted(token)
        
        assert result is True
        mock_redis.exists.assert_called_once_with(f"blacklist:{token}")


@pytest.mark.asyncio
async def test_blacklist_is_blacklisted_false(blacklist_service):
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = 0
    
    with patch("api.services.blacklist.get_redis_pool", return_value=mock_redis):
        token = "valid_token"
        
        result = await blacklist_service.is_blacklisted(token)
        
        assert result is False
        mock_redis.exists.assert_called_once_with(f"blacklist:{token}")


@pytest.mark.asyncio
async def test_add_multiple_tokens(blacklist_service):
    mock_redis = AsyncMock()
    
    with patch("api.services.blacklist.get_redis_pool", return_value=mock_redis):
        await blacklist_service.add("token1", 3600)
        await blacklist_service.add("token2", 7200)
        
        assert mock_redis.setex.call_count == 2
        mock_redis.setex.assert_any_call("blacklist:token1", 3600, "revoked")
        mock_redis.setex.assert_any_call("blacklist:token2", 7200, "revoked")
