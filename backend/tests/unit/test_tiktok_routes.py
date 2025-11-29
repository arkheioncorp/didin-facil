"""
Tests for TikTok Routes
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from io import BytesIO


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


@pytest.mark.asyncio
async def test_tiktok_create_session(mock_current_user, mock_settings):
    from api.routes.tiktok import create_session, TikTokSessionSetup
    
    with patch("api.routes.tiktok.settings", mock_settings), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()):
        
        data = TikTokSessionSetup(
            account_name="myaccount",
            cookies=[{"name": "cookie1", "value": "val1"}]
        )
        
        result = await create_session(data, mock_current_user)
        
        assert result["status"] == "success"
        assert result["account_name"] == "myaccount"


@pytest.mark.asyncio
async def test_tiktok_list_sessions_empty(mock_current_user, mock_settings):
    from api.routes.tiktok import list_sessions
    
    with patch("api.routes.tiktok.settings", mock_settings), \
         patch("os.path.exists", return_value=False):
        
        result = await list_sessions(mock_current_user)
        
        assert result["sessions"] == []


@pytest.mark.asyncio
async def test_tiktok_list_sessions_with_data(
    mock_current_user,
    mock_settings
):
    from api.routes.tiktok import list_sessions
    
    with patch("api.routes.tiktok.settings", mock_settings), \
         patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=[
             f"{mock_current_user.id}_account1.json",
             f"{mock_current_user.id}_account2.json",
             "other_user_account.json"
         ]):
        
        result = await list_sessions(mock_current_user)
        
        assert len(result["sessions"]) == 2
        assert result["sessions"][0]["account_name"] == "account1"
        assert result["sessions"][1]["account_name"] == "account2"


@pytest.mark.asyncio
async def test_tiktok_upload_session_not_found(
    mock_current_user,
    mock_settings
):
    from api.routes.tiktok import upload_video
    
    mock_file = MagicMock()
    mock_file.filename = "test.mp4"
    mock_file.file = BytesIO(b"fake video")
    
    with patch("api.routes.tiktok.settings", mock_settings), \
         patch("os.path.exists", return_value=False):
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_video(
                account_name="nonexistent",
                caption="Test",
                hashtags="",
                privacy="public",
                file=mock_file,
                current_user=mock_current_user
            )
        
        assert exc_info.value.status_code == 404
        assert "não encontrada" in exc_info.value.detail
