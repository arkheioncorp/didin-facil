"""
Tests for CRM Feature Gating
Tests for CRM contacts creation limits
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


@pytest.fixture
def mock_subscription_service():
    """Mock SubscriptionService."""
    service = MagicMock()
    service.can_use_feature = AsyncMock(return_value=False)
    service.increment_usage = AsyncMock()
    return service


@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_contact_data():
    """Mock contact creation data."""
    from api.routes.crm import ContactCreate
    return ContactCreate(
        email="contact@example.com",
        name="Test Contact",
        phone="+5511999999999"
    )


class TestCRMContactGating:
    """Tests for CRM contact creation gating."""

    @pytest.mark.asyncio
    async def test_create_contact_limit_exceeded(
        self,
        mock_subscription_service,
        mock_current_user,
        mock_contact_data
    ):
        """Test that contact creation returns 402 when limit exceeded."""
        from api.routes.crm import create_contact
        
        with pytest.raises(HTTPException) as exc_info:
            await create_contact(
                data=mock_contact_data,
                user=mock_current_user,
                subscription_service=mock_subscription_service
            )
        
        assert exc_info.value.status_code == 402
        assert "Limite de contatos CRM" in exc_info.value.detail
        
        mock_subscription_service.can_use_feature.assert_called_once_with(
            "user-123",
            "crm_contacts"
        )

    @pytest.mark.asyncio
    async def test_create_contact_success_with_limit(
        self,
        mock_current_user,
        mock_contact_data
    ):
        """Test that contact creation works when under limit."""
        from api.routes.crm import create_contact

        # Mock service that allows feature
        mock_service = MagicMock()
        mock_service.can_use_feature = AsyncMock(return_value=True)
        mock_service.increment_usage = AsyncMock()
        
        # Mock CRM service
        mock_crm_service = MagicMock()
        mock_contact = MagicMock()
        mock_contact.to_dict = MagicMock(return_value={
            "id": "contact-1",
            "email": "contact@example.com",
            "name": "Test Contact"
        })
        mock_crm_service.contacts.create = AsyncMock(return_value=mock_contact)
        
        with patch(
            'api.routes.crm.get_crm_service',
            return_value=AsyncMock(return_value=mock_crm_service)
        ):
            # Patch the async function
            with patch(
                'api.routes.crm.get_crm_service',
                new=AsyncMock(return_value=mock_crm_service)
            ):
                result = await create_contact(
                    data=mock_contact_data,
                    user=mock_current_user,
                    subscription_service=mock_service
                )
                
                assert result["id"] == "contact-1"
                mock_service.can_use_feature.assert_called_once()
                mock_service.increment_usage.assert_called_once_with(
                    "user-123",
                    "crm_contacts",
                    1
                )
