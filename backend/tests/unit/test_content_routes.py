"""
Tests for Content Routes - Video Generation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


class MockUser:
    id = "user_123"
    email = "test@example.com"


@pytest.fixture
def mock_current_user():
    return MockUser()


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.DATA_DIR = "/tmp/test_data"
    return settings


@pytest.fixture
def mock_video_generator():
    generator = MagicMock()
    generator.generate_product_showcase = AsyncMock(return_value={
        "success": True,
        "path": "/tmp/test.mp4"
    })
    generator.generate_text_animation = AsyncMock(return_value={
        "success": True,
        "path": "/tmp/text.mp4"
    })
    generator.generate_deal_compilation = AsyncMock(return_value={
        "success": True,
        "path": "/tmp/deal.mp4"
    })
    return generator


@pytest.fixture
def mock_video_config():
    config = MagicMock()
    config.get_dimensions.return_value = (1080, 1920)
    return config


@pytest.mark.asyncio
async def test_generate_product_video_success(
    mock_current_user,
    mock_settings,
    mock_video_generator,
    mock_video_config
):
    from api.routes.content import (
        generate_product_video, ProductVideoRequest
    )
    
    with patch("api.routes.content.settings", mock_settings), \
         patch("os.makedirs"), \
         patch("api.routes.content.FFmpegVideoGenerator",
               return_value=mock_video_generator), \
         patch("api.routes.content.VideoConfig",
               return_value=mock_video_config):
        
        data = ProductVideoRequest(
            product_name="Test Product",
            price=99.99,
            original_price=149.99,
            store="Test Store",
            aspect_ratio="portrait",
            duration=15
        )
        
        result = await generate_product_video(data, mock_current_user)
        
        assert result["status"] == "success"
        assert "download_url" in result


@pytest.mark.asyncio
async def test_generate_product_video_failure(
    mock_current_user,
    mock_settings,
    mock_video_generator,
    mock_video_config
):
    from api.routes.content import (
        generate_product_video, ProductVideoRequest
    )
    
    mock_video_generator.generate_product_showcase.return_value = {
        "success": False,
        "error": "Generation failed"
    }
    
    with patch("api.routes.content.settings", mock_settings), \
         patch("os.makedirs"), \
         patch("api.routes.content.FFmpegVideoGenerator",
               return_value=mock_video_generator), \
         patch("api.routes.content.VideoConfig",
               return_value=mock_video_config):
        
        data = ProductVideoRequest(
            product_name="Test Product",
            price=99.99
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await generate_product_video(data, mock_current_user)
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_generate_text_video_success(
    mock_current_user,
    mock_settings,
    mock_video_generator,
    mock_video_config
):
    from api.routes.content import generate_text_video, TextVideoRequest
    
    with patch("api.routes.content.settings", mock_settings), \
         patch("os.makedirs"), \
         patch("api.routes.content.FFmpegVideoGenerator",
               return_value=mock_video_generator), \
         patch("api.routes.content.VideoConfig",
               return_value=mock_video_config):
        
        data = TextVideoRequest(
            slides=[
                {"text": "Slide 1", "duration": 3},
                {"text": "Slide 2", "duration": 3}
            ],
            aspect_ratio="portrait",
            background_color="#1a1a2e",
            text_color="#ffffff"
        )
        
        result = await generate_text_video(data, mock_current_user)
        
        assert result["status"] == "success"
        assert "download_url" in result


@pytest.mark.asyncio
async def test_generate_deal_alert_success(
    mock_current_user,
    mock_settings,
    mock_video_generator,
    mock_video_config
):
    from api.routes.content import generate_deal_alert, DealAlertRequest
    
    with patch("api.routes.content.settings", mock_settings), \
         patch("os.makedirs"), \
         patch("api.routes.content.FFmpegVideoGenerator",
               return_value=mock_video_generator), \
         patch("api.routes.content.VideoConfig",
               return_value=mock_video_config):
        
        data = DealAlertRequest(
            products=[
                {"name": "Product 1", "price": 49.99},
                {"name": "Product 2", "price": 79.99}
            ],
            title="🔥 OFERTAS DO DIA",
            aspect_ratio="portrait"
        )
        
        result = await generate_deal_alert(data, mock_current_user)
        
        assert result["status"] == "success"
        assert "download_url" in result


@pytest.mark.asyncio
async def test_generate_product_video_landscape(
    mock_current_user,
    mock_settings,
    mock_video_generator,
    mock_video_config
):
    from api.routes.content import (
        generate_product_video, ProductVideoRequest
    )
    
    with patch("api.routes.content.settings", mock_settings), \
         patch("os.makedirs"), \
         patch("api.routes.content.FFmpegVideoGenerator",
               return_value=mock_video_generator), \
         patch("api.routes.content.VideoConfig",
               return_value=mock_video_config):
        
        data = ProductVideoRequest(
            product_name="Test Product",
            price=99.99,
            aspect_ratio="landscape",
            duration=30
        )
        
        result = await generate_product_video(data, mock_current_user)
        
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_generate_product_video_square(
    mock_current_user,
    mock_settings,
    mock_video_generator,
    mock_video_config
):
    from api.routes.content import (
        generate_product_video, ProductVideoRequest
    )
    
    with patch("api.routes.content.settings", mock_settings), \
         patch("os.makedirs"), \
         patch("api.routes.content.FFmpegVideoGenerator",
               return_value=mock_video_generator), \
         patch("api.routes.content.VideoConfig",
               return_value=mock_video_config):
        
        data = ProductVideoRequest(
            product_name="Test Product",
            price=99.99,
            aspect_ratio="square"
        )
        
        result = await generate_product_video(data, mock_current_user)
        
        assert result["status"] == "success"
