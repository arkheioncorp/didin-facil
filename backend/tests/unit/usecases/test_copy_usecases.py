"""
Tests for Copy Generation Use Cases
====================================

Unit tests for AI copy generation use cases.
Uses mock services to test business logic in isolation.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from domain.usecases.copy import (COPY_COSTS, GenerateCopyInput,
                                  GenerateCopyUseCase, GetCopyHistoryInput,
                                  GetCopyHistoryUseCase)

# ==================== Fixtures ====================

@pytest.fixture
def mock_copy_history_repo():
    """Create mock copy history repository."""
    return AsyncMock()


@pytest.fixture
def mock_ai_service():
    """Create mock AI service."""
    return AsyncMock()


@pytest.fixture
def mock_credit_service():
    """Create mock credit service."""
    return AsyncMock()


@pytest.fixture
def mock_product_repo():
    """Create mock product repository."""
    return AsyncMock()


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return uuid4()


@pytest.fixture
def sample_product_id():
    """Sample product ID."""
    return uuid4()


@pytest.fixture
def sample_product(sample_product_id):
    """Sample product data."""
    return {
        "id": sample_product_id,
        "title": "Amazing Gadget",
        "description": "The best gadget ever made",
        "price": 149.99,
    }


@pytest.fixture
def sample_copy_record(sample_user_id, sample_product_id):
    """Sample copy history record."""
    return {
        "id": uuid4(),
        "user_id": sample_user_id,
        "product_id": sample_product_id,
        "copy_type": "tiktok_caption",
        "tone": "casual",
        "prompt": "Generate a tiktok_caption...",
        "result": "🔥 Check out this amazing gadget! #trending",
        "tokens_used": 150,
        "created_at": datetime.now(timezone.utc),
    }


# ==================== GenerateCopyUseCase Tests ====================

class TestGenerateCopyUseCase:
    """Tests for GenerateCopyUseCase."""
    
    @pytest.mark.asyncio
    async def test_generate_copy_success(
        self,
        mock_copy_history_repo,
        mock_ai_service,
        mock_credit_service,
        mock_product_repo,
        sample_user_id,
        sample_product_id,
        sample_product,
        sample_copy_record,
    ):
        """Should successfully generate copy."""
        # Arrange
        mock_credit_service.has_credits.return_value = True
        mock_product_repo.get_by_id.return_value = sample_product
        mock_ai_service.generate_copy.return_value = (
            "🔥 Check out this amazing gadget! #trending",
            150
        )
        mock_copy_history_repo.save.return_value = sample_copy_record
        
        use_case = GenerateCopyUseCase(
            copy_history_repo=mock_copy_history_repo,
            ai_service=mock_ai_service,
            credit_service=mock_credit_service,
            product_repo=mock_product_repo,
        )
        
        input_data = GenerateCopyInput(
            user_id=sample_user_id,
            product_id=sample_product_id,
            copy_type="tiktok_caption",
            tone="casual",
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is True
        assert result.data is not None
        assert "amazing gadget" in result.data.content.lower()
        assert result.data.tokens_used == 150
        assert result.data.credits_charged == COPY_COSTS["tiktok_caption"]
        
        mock_credit_service.deduct_credits.assert_called_once()
        mock_copy_history_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_copy_insufficient_credits(
        self,
        mock_copy_history_repo,
        mock_ai_service,
        mock_credit_service,
        mock_product_repo,
        sample_user_id,
    ):
        """Should fail if user has insufficient credits."""
        # Arrange
        mock_credit_service.has_credits.return_value = False
        
        use_case = GenerateCopyUseCase(
            copy_history_repo=mock_copy_history_repo,
            ai_service=mock_ai_service,
            credit_service=mock_credit_service,
            product_repo=mock_product_repo,
        )
        
        input_data = GenerateCopyInput(
            user_id=sample_user_id,
            product_id=None,
            copy_type="blog_post",  # Most expensive
            tone="professional",
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is False
        assert result.error_code == "INSUFFICIENT_CREDITS"
        mock_ai_service.generate_copy.assert_not_called()
        mock_credit_service.deduct_credits.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_copy_ai_error(
        self,
        mock_copy_history_repo,
        mock_ai_service,
        mock_credit_service,
        mock_product_repo,
        sample_user_id,
    ):
        """Should handle AI service errors gracefully."""
        # Arrange
        mock_credit_service.has_credits.return_value = True
        mock_ai_service.generate_copy.side_effect = Exception("API rate limit")
        
        use_case = GenerateCopyUseCase(
            copy_history_repo=mock_copy_history_repo,
            ai_service=mock_ai_service,
            credit_service=mock_credit_service,
            product_repo=mock_product_repo,
        )
        
        input_data = GenerateCopyInput(
            user_id=sample_user_id,
            product_id=None,
            copy_type="tiktok_caption",
            tone="casual",
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is False
        assert result.error_code == "AI_ERROR"
        assert "rate limit" in result.error.lower()
        # Credits should NOT be deducted on error
        mock_credit_service.deduct_credits.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_copy_with_product_context(
        self,
        mock_copy_history_repo,
        mock_ai_service,
        mock_credit_service,
        mock_product_repo,
        sample_user_id,
        sample_product_id,
        sample_product,
        sample_copy_record,
    ):
        """Should include product details in prompt."""
        # Arrange
        mock_credit_service.has_credits.return_value = True
        mock_product_repo.get_by_id.return_value = sample_product
        mock_ai_service.generate_copy.return_value = ("Great copy!", 100)
        mock_copy_history_repo.save.return_value = sample_copy_record
        
        use_case = GenerateCopyUseCase(
            copy_history_repo=mock_copy_history_repo,
            ai_service=mock_ai_service,
            credit_service=mock_credit_service,
            product_repo=mock_product_repo,
        )
        
        input_data = GenerateCopyInput(
            user_id=sample_user_id,
            product_id=sample_product_id,
            copy_type="product_description",
            tone="professional",
        )
        
        # Act
        await use_case.execute(input_data)
        
        # Assert - verify product was fetched
        mock_product_repo.get_by_id.assert_called_once_with(sample_product_id)
    
    @pytest.mark.asyncio
    async def test_copy_costs_vary_by_type(
        self,
        mock_copy_history_repo,
        mock_ai_service,
        mock_credit_service,
        mock_product_repo,
        sample_user_id,
        sample_copy_record,
    ):
        """Should charge different credits based on copy type."""
        # Arrange
        mock_credit_service.has_credits.return_value = True
        mock_ai_service.generate_copy.return_value = ("Copy!", 100)
        mock_copy_history_repo.save.return_value = sample_copy_record
        
        use_case = GenerateCopyUseCase(
            copy_history_repo=mock_copy_history_repo,
            ai_service=mock_ai_service,
            credit_service=mock_credit_service,
            product_repo=mock_product_repo,
        )
        
        # Test different copy types
        test_cases = [
            ("tiktok_caption", 1),
            ("product_description", 2),
            ("blog_post", 5),
        ]
        
        for copy_type, expected_cost in test_cases:
            mock_credit_service.reset_mock()
            
            input_data = GenerateCopyInput(
                user_id=sample_user_id,
                product_id=None,
                copy_type=copy_type,
                tone="casual",
            )
            
            result = await use_case.execute(input_data)
            
            assert result.success is True
            assert result.data.credits_charged == expected_cost


# ==================== GetCopyHistoryUseCase Tests ====================

class TestGetCopyHistoryUseCase:
    """Tests for GetCopyHistoryUseCase."""
    
    @pytest.mark.asyncio
    async def test_get_history_success(
        self,
        mock_copy_history_repo,
        sample_user_id,
        sample_copy_record,
    ):
        """Should successfully get copy history."""
        # Arrange
        mock_copy_history_repo.list_by_user.return_value = [sample_copy_record]
        mock_copy_history_repo.count_by_user.return_value = 1
        
        use_case = GetCopyHistoryUseCase(copy_history_repo=mock_copy_history_repo)
        
        input_data = GetCopyHistoryInput(
            user_id=sample_user_id,
            limit=10,
            offset=0,
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is True
        assert len(result.data.items) == 1
        assert result.data.total == 1
        assert result.data.items[0].copy_type == "tiktok_caption"
    
    @pytest.mark.asyncio
    async def test_get_history_empty(
        self,
        mock_copy_history_repo,
        sample_user_id,
    ):
        """Should return empty list for new user."""
        # Arrange
        mock_copy_history_repo.list_by_user.return_value = []
        mock_copy_history_repo.count_by_user.return_value = 0
        
        use_case = GetCopyHistoryUseCase(copy_history_repo=mock_copy_history_repo)
        
        input_data = GetCopyHistoryInput(user_id=sample_user_id)
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is True
        assert len(result.data.items) == 0
        assert result.data.total == 0
        assert result.data.has_more is False
    
    @pytest.mark.asyncio
    async def test_get_history_filter_by_type(
        self,
        mock_copy_history_repo,
        sample_user_id,
    ):
        """Should filter by copy type."""
        # Arrange
        mock_copy_history_repo.list_by_user.return_value = []
        mock_copy_history_repo.count_by_user.return_value = 0
        
        use_case = GetCopyHistoryUseCase(copy_history_repo=mock_copy_history_repo)
        
        input_data = GetCopyHistoryInput(
            user_id=sample_user_id,
            copy_type="tiktok_caption",
        )
        
        # Act
        await use_case.execute(input_data)
        
        # Assert
        mock_copy_history_repo.list_by_user.assert_called_once_with(
            user_id=sample_user_id,
            limit=50,
            offset=0,
            copy_type="tiktok_caption",
        )
    
    @pytest.mark.asyncio
    async def test_get_history_pagination(
        self,
        mock_copy_history_repo,
        sample_user_id,
        sample_copy_record,
    ):
        """Should correctly calculate has_more."""
        # Arrange
        mock_copy_history_repo.list_by_user.return_value = [
            sample_copy_record for _ in range(10)
        ]
        mock_copy_history_repo.count_by_user.return_value = 25
        
        use_case = GetCopyHistoryUseCase(copy_history_repo=mock_copy_history_repo)
        
        input_data = GetCopyHistoryInput(
            user_id=sample_user_id,
            limit=10,
            offset=0,
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is True
        assert result.data.has_more is True
        assert result.data.total == 25
