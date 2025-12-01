"""
Testes para Users Routes
=========================
Cobertura para api/routes/users.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi import HTTPException


class MockUser(dict):
    """Mock user com suporte a dict e atributos."""
    def __init__(self):
        super().__init__(id="user-123", email="test@example.com")
        self.id = "user-123"
        self.email = "test@example.com"


@pytest.fixture
def mock_user():
    return MockUser()


@pytest.fixture
def mock_database():
    return AsyncMock()


# ============================================
# TESTS: Get My Profile
# ============================================

class TestGetMyProfile:
    """Testes de get_my_profile"""

    @pytest.mark.asyncio
    async def test_get_profile_success(self, mock_user, mock_database):
        """Deve retornar perfil do usuário"""
        user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "avatar_url": None,
            "phone": "+5511999999999",
            "is_active": True,
            "is_email_verified": True,
            "language": "pt-BR",
            "timezone": "America/Sao_Paulo",
            "created_at": datetime(2024, 1, 1),
            "updated_at": None,
            "last_login_at": None,
            "has_lifetime_license": False,
            "license_activated_at": None
        }
        mock_database.fetch_one.return_value = user_data

        with patch("api.routes.users.database", mock_database):
            from api.routes.users import get_my_profile

            result = await get_my_profile(mock_user)

            assert result["id"] == "user-123"
            assert result["email"] == "test@example.com"
            mock_database.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, mock_user, mock_database):
        """Deve retornar 404 se usuário não encontrado"""
        mock_database.fetch_one.return_value = None

        with patch("api.routes.users.database", mock_database):
            from api.routes.users import get_my_profile

            with pytest.raises(HTTPException) as exc:
                await get_my_profile(mock_user)

            assert exc.value.status_code == 404


# ============================================
# TESTS: Get Full Profile
# ============================================

class TestGetFullProfile:
    """Testes de get_full_profile"""

    @pytest.mark.asyncio
    async def test_get_full_profile_with_license(
        self, mock_user, mock_database
    ):
        """Deve retornar perfil completo com licença"""
        user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "avatar_url": None,
            "phone": None,
            "is_active": True,
            "is_email_verified": True,
            "language": "pt-BR",
            "timezone": "America/Sao_Paulo",
            "created_at": datetime(2024, 1, 1),
            "updated_at": None,
            "last_login_at": None,
            "has_lifetime_license": True,
            "license_activated_at": datetime(2024, 1, 1)
        }
        license_data = {
            "id": "lic-123",
            "plan": "lifetime",
            "is_valid": True,
            "is_lifetime": True,
            "activated_at": datetime(2024, 1, 1),
            "expires_at": None,
            "max_devices": 3,
            "active_devices": 1
        }
        credits_data = {
            "balance": 1000,
            "total_purchased": 1000,
            "total_used": 0,
            "last_purchase_at": datetime(2024, 1, 1),
            "bonus_balance": 100,
            "bonus_expires_at": None
        }

        mock_database.fetch_one.side_effect = [
            user_data, license_data, credits_data
        ]

        with patch("api.routes.users.database", mock_database):
            from api.routes.users import get_full_profile

            result = await get_full_profile(mock_user)

            assert result["user"]["id"] == "user-123"
            assert result["license"]["is_lifetime"] is True
            assert result["credits"]["balance"] == 1000

    @pytest.mark.asyncio
    async def test_get_full_profile_without_license(
        self, mock_user, mock_database
    ):
        """Deve retornar defaults quando sem licença"""
        user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "avatar_url": None,
            "phone": None,
            "is_active": True,
            "is_email_verified": False,
            "language": "pt-BR",
            "timezone": "America/Sao_Paulo",
            "created_at": datetime(2024, 1, 1),
            "updated_at": None,
            "last_login_at": None,
            "has_lifetime_license": False,
            "license_activated_at": None
        }

        mock_database.fetch_one.side_effect = [user_data, None, None]

        with patch("api.routes.users.database", mock_database):
            from api.routes.users import get_full_profile, LicenseResponse

            result = await get_full_profile(mock_user)

            assert result["user"]["id"] == "user-123"
            # License defaults
            assert isinstance(
                result["license"],
                (LicenseResponse, dict, type(None))
            )


# ============================================
# TESTS: Update Profile
# ============================================

class TestUpdateProfile:
    """Testes de update_my_profile"""

    @pytest.mark.asyncio
    async def test_update_name(self, mock_user, mock_database):
        """Deve atualizar nome do usuário"""
        updated_user = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "New Name",
            "avatar_url": None,
            "phone": None,
            "is_active": True,
            "is_email_verified": True,
            "language": "pt-BR",
            "timezone": "America/Sao_Paulo",
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 2),
            "last_login_at": None,
            "has_lifetime_license": False,
            "license_activated_at": None
        }
        mock_database.fetch_one.return_value = updated_user

        with patch("api.routes.users.database", mock_database):
            from api.routes.users import (
                update_my_profile, UserProfileUpdate
            )

            update_data = UserProfileUpdate(name="New Name")
            result = await update_my_profile(update_data, mock_user)

            assert result["name"] == "New Name"
            mock_database.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, mock_user, mock_database):
        """Deve atualizar múltiplos campos"""
        updated_user = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "New Name",
            "avatar_url": None,
            "phone": "+5511988887777",
            "is_active": True,
            "is_email_verified": True,
            "language": "en-US",
            "timezone": "America/New_York",
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 2),
            "last_login_at": None,
            "has_lifetime_license": False,
            "license_activated_at": None
        }
        mock_database.fetch_one.return_value = updated_user

        with patch("api.routes.users.database", mock_database):
            from api.routes.users import (
                update_my_profile, UserProfileUpdate
            )

            update_data = UserProfileUpdate(
                name="New Name",
                phone="+5511988887777",
                language="en-US",
                timezone="America/New_York"
            )
            result = await update_my_profile(update_data, mock_user)

            assert result["name"] == "New Name"
            assert result["phone"] == "+5511988887777"
            assert result["language"] == "en-US"

    @pytest.mark.asyncio
    async def test_update_no_changes(self, mock_user, mock_database):
        """Deve retornar perfil atual se nenhuma mudança"""
        user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "avatar_url": None,
            "phone": None,
            "is_active": True,
            "is_email_verified": True,
            "language": "pt-BR",
            "timezone": "America/Sao_Paulo",
            "created_at": datetime(2024, 1, 1),
            "updated_at": None,
            "last_login_at": None,
            "has_lifetime_license": False,
            "license_activated_at": None
        }
        mock_database.fetch_one.return_value = user_data

        with patch("api.routes.users.database", mock_database):
            from api.routes.users import (
                update_my_profile, UserProfileUpdate
            )

            update_data = UserProfileUpdate()
            result = await update_my_profile(update_data, mock_user)

            assert result["id"] == "user-123"


# ============================================
# TESTS: Update Password
# ============================================

class TestUpdatePassword:
    """Testes de update_my_password"""

    @pytest.mark.asyncio
    async def test_update_password_success(self, mock_user, mock_database):
        """Deve atualizar senha com sucesso"""
        # Mock senha atual hasheada
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        current_hash = ctx.hash("old_password")

        mock_database.fetch_one.return_value = {
            "password_hash": current_hash
        }
        mock_database.execute = AsyncMock()

        with patch("api.routes.users.database", mock_database):
            from api.routes.users import (
                update_my_password, UserPasswordUpdate
            )

            update_data = UserPasswordUpdate(
                current_password="old_password",
                new_password="new_password123"
            )
            result = await update_my_password(update_data, mock_user)

            assert result["message"] == "Password updated successfully"
            mock_database.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_password_wrong_current(
        self, mock_user, mock_database
    ):
        """Deve falhar com senha atual incorreta"""
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        current_hash = ctx.hash("correct_password")

        mock_database.fetch_one.return_value = {
            "password_hash": current_hash
        }

        with patch("api.routes.users.database", mock_database):
            from api.routes.users import (
                update_my_password, UserPasswordUpdate
            )

            update_data = UserPasswordUpdate(
                current_password="wrong_password",
                new_password="new_password123"
            )

            with pytest.raises(HTTPException) as exc:
                await update_my_password(update_data, mock_user)

            assert exc.value.status_code == 400
            assert "Incorrect password" in exc.value.detail


# ============================================
# TESTS: Models
# ============================================

class TestUserModels:
    """Testes dos modelos Pydantic"""

    def test_user_profile_update_empty(self):
        """Deve aceitar update vazio"""
        from api.routes.users import UserProfileUpdate

        update = UserProfileUpdate()
        assert update.name is None
        assert update.phone is None

    def test_user_profile_update_partial(self):
        """Deve aceitar update parcial"""
        from api.routes.users import UserProfileUpdate

        update = UserProfileUpdate(name="Test", language="en-US")
        assert update.name == "Test"
        assert update.language == "en-US"
        assert update.phone is None

    def test_license_response_defaults(self):
        """Deve ter valores default corretos"""
        from api.routes.users import LicenseResponse

        license_resp = LicenseResponse()
        assert license_resp.is_valid is False
        assert license_resp.is_lifetime is False
        assert license_resp.plan == "free"

    def test_credits_response_defaults(self):
        """Deve ter valores default corretos"""
        from api.routes.users import CreditsResponse

        credits_resp = CreditsResponse()
        assert credits_resp.balance == 0
        assert credits_resp.bonus_balance == 0
