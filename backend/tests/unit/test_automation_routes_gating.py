from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.automation import activate_workflow
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_activate_workflow_limit_exceeded():
    """Test activate_workflow when limit is exceeded"""
    from api.routes.automation import activate_workflow

    # Mock dependencies
    mock_service = AsyncMock()
    mock_service.can_use_feature = AsyncMock(return_value=False)
    
    current_user = {"id": "user-123"}
    workflow_id = "wf-123"
    
    # Expect HTTPException 402
    with pytest.raises(HTTPException) as exc_info:
        await activate_workflow(
            workflow_id=workflow_id,
            current_user=current_user,
            service=mock_service
        )
    
    assert exc_info.value.status_code == 402
    assert "Limite de automações atingido" in exc_info.value.detail
    
    # Verify service call
    mock_service.can_use_feature.assert_called_once_with(
        "user-123",
        "crm_automation",
        increment=1
    )

@pytest.mark.asyncio
async def test_activate_workflow_success():
    """Test activate_workflow when limit is not exceeded"""
    from api.routes.automation import activate_workflow

    # Mock dependencies
    mock_service = AsyncMock()
    mock_service.can_use_feature = AsyncMock(return_value=True)
    
    current_user = {"id": "user-123"}
    workflow_id = "wf-123"
    
    # Mock n8n client
    with patch('api.routes.automation.n8n_client') as mock_n8n:
        mock_n8n.activate_workflow = AsyncMock(return_value=True)
        
        response = await activate_workflow(
            workflow_id=workflow_id,
            current_user=current_user,
            service=mock_service
        )
        
        assert response["status"] == "activated"
        assert response["workflow_id"] == workflow_id
        
        # Verify service call
        mock_service.can_use_feature.assert_called_once_with(
            "user-123",
            "crm_automation",
            increment=1
        )
