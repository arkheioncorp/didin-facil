from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.social_auth import OAuthInitRequest, init_oauth
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_init_oauth_limit_exceeded():
    """Test init_oauth when limit is exceeded"""
    # Mock dependencies
    mock_service = AsyncMock()
    mock_service.can_use_feature = AsyncMock(return_value=False)
    
    current_user = {"id": "user-123"}
    
    request = OAuthInitRequest(
        platform="instagram",
        account_name="test_account"
    )
    
    # Expect HTTPException 402
    with pytest.raises(HTTPException) as exc_info:
        await init_oauth(
            data=request,
            current_user=current_user,
            service=mock_service
        )
    
    assert exc_info.value.status_code == 402
    assert "Limite de contas sociais atingido" in exc_info.value.detail
    
    # Verify service call
    mock_service.can_use_feature.assert_called_once_with(
        "user-123",
        "social_accounts",
        increment=1
    )
