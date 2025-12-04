"""Testes abrangentes para YouTube Routes."""

import json
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from fastapi import HTTPException, UploadFile


@pytest.fixture
def mock_current_user():
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_subscription_service():
    service = AsyncMock()
    service.can_use_feature = AsyncMock(return_value=True)
    service.increment_usage = AsyncMock()
    return service


@pytest.fixture
def mock_youtube_client():
    client = AsyncMock()
    client.authenticate = AsyncMock()
    client.upload_video = AsyncMock(return_value={"video_id": "abc123"})
    return client


class TestModels:
    """Testes para os modelos."""

    def test_youtube_auth_request(self):
        """Teste do modelo YouTubeAuthRequest."""
        from api.routes.youtube import YouTubeAuthRequest
        req = YouTubeAuthRequest(account_name="main")
        assert req.account_name == "main"

    def test_youtube_upload_request_minimal(self):
        """Teste do modelo YouTubeUploadRequest mínimo."""
        from api.routes.youtube import YouTubeUploadRequest
        req = YouTubeUploadRequest(
            account_name="main",
            title="Test Video"
        )
        assert req.title == "Test Video"
        assert req.privacy == "private"

    def test_youtube_upload_request_full(self):
        """Teste do modelo YouTubeUploadRequest completo."""
        from api.routes.youtube import YouTubeUploadRequest
        future_time = datetime.now(timezone.utc)
        req = YouTubeUploadRequest(
            account_name="main",
            title="Test Video",
            description="A test description",
            tags=["tag1", "tag2"],
            privacy="public",
            category="22",
            is_short=True,
            publish_at=future_time
        )
        assert req.is_short is True
        assert req.category == "22"


class TestListAccounts:
    """Testes para list_accounts."""

    async def test_list_accounts_no_user(self):
        """Teste sem usuário autenticado."""
        from api.routes.youtube import list_accounts
        result = await list_accounts(current_user=None)
        assert result == {"accounts": []}

    async def test_list_accounts_no_dir(self, mock_current_user):
        """Teste quando diretório não existe."""
        from api.routes.youtube import list_accounts
        
        with patch("os.path.exists", return_value=False):
            result = await list_accounts(current_user=mock_current_user)
        
        assert result == {"accounts": []}

    async def test_list_accounts_with_accounts(self, mock_current_user):
        """Teste com contas existentes."""
        from api.routes.youtube import list_accounts
        
        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=["user-123_main.json", "user-123_secondary.json"]):
                result = await list_accounts(current_user=mock_current_user)
        
        assert len(result["accounts"]) == 2
        assert result["accounts"][0]["account_name"] == "main"


class TestDeleteAccount:
    """Testes para delete_account."""

    async def test_delete_account_success(self, mock_current_user):
        """Teste de exclusão bem-sucedida."""
        from api.routes.youtube import delete_account
        
        with patch("os.path.exists", return_value=True):
            with patch("os.remove") as mock_remove:
                result = await delete_account(
                    account_name="main",
                    current_user=mock_current_user
                )
        
        assert result["status"] == "success"
        mock_remove.assert_called_once()

    async def test_delete_account_not_found(self, mock_current_user):
        """Teste de conta não encontrada."""
        from api.routes.youtube import delete_account
        
        with patch("os.path.exists", return_value=False):
            with pytest.raises(HTTPException) as exc:
                await delete_account(
                    account_name="invalid",
                    current_user=mock_current_user
                )
        
        assert exc.value.status_code == 404

    async def test_delete_account_error(self, mock_current_user):
        """Teste de erro na exclusão."""
        from api.routes.youtube import delete_account
        
        with patch("os.path.exists", return_value=True):
            with patch("os.remove", side_effect=Exception("Delete failed")):
                with pytest.raises(HTTPException) as exc:
                    await delete_account(
                        account_name="main",
                        current_user=mock_current_user
                    )
        
        assert exc.value.status_code == 500


class TestInitAuth:
    """Testes para init_auth."""

    async def test_init_auth_no_credentials(self, mock_current_user):
        """Teste sem arquivo de credenciais."""
        from api.routes.youtube import YouTubeAuthRequest, init_auth
        
        request = YouTubeAuthRequest(account_name="main")
        
        with patch("os.path.exists", return_value=False):
            with patch("os.makedirs"):
                with pytest.raises(HTTPException) as exc:
                    await init_auth(data=request, current_user=mock_current_user)
        
        assert exc.value.status_code == 400
        assert "credenciais" in exc.value.detail.lower()


class TestRouterConfig:
    """Testes para configuração do router."""

    def test_router_exists(self):
        """Teste se router existe."""
        from api.routes.youtube import router
        assert router is not None

    def test_router_routes(self):
        """Teste se rotas existem."""
        from api.routes.youtube import router
        routes = [r.path for r in router.routes]
        assert "/auth/init" in routes
        assert "/accounts" in routes
        assert "/upload" in routes


