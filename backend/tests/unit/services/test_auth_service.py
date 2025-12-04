"""
Comprehensive tests for AuthService
Tests for authentication, JWT tokens, and password management
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAuthServicePasswordManagement:
    """Tests for password hashing and verification"""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance"""
        with patch('api.services.auth.get_security_config') as mock_config:
            mock_config.return_value = MagicMock(
                jwt_secret_key="test_secret_key_12345",
                jwt_algorithm="HS256"
            )
            from api.services.auth import AuthService
            return AuthService()
    
    def test_hash_password_returns_hash(self, auth_service):
        """Test that hash_password returns a bcrypt hash"""
        password = "SecurePassword123!"
        
        hashed = auth_service.hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2")  # bcrypt prefix
    
    def test_hash_password_different_for_same_input(self, auth_service):
        """Test that same password produces different hashes (salt)"""
        password = "SecurePassword123!"
        
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)
        
        # Different hashes due to salt
        assert hash1 != hash2
    
    def test_verify_password_correct(self, auth_service):
        """Test verify_password with correct password"""
        password = "SecurePassword123!"
        hashed = auth_service.hash_password(password)
        
        result = auth_service.verify_password(password, hashed)
        
        assert result is True
    
    def test_verify_password_incorrect(self, auth_service):
        """Test verify_password with wrong password"""
        password = "SecurePassword123!"
        hashed = auth_service.hash_password(password)
        
        result = auth_service.verify_password("WrongPassword", hashed)
        
        assert result is False
    
    def test_verify_password_empty_password(self, auth_service):
        """Test verify_password with empty password"""
        hashed = auth_service.hash_password("SomePassword")
        
        result = auth_service.verify_password("", hashed)
        
        assert result is False


class TestAuthServiceTokenManagement:
    """Tests for JWT token creation and verification"""
    
    @pytest.fixture
    def auth_service(self):
        with patch('api.services.auth.get_security_config') as mock_config:
            mock_config.return_value = MagicMock(
                jwt_secret_key="test_secret_key_12345",
                jwt_algorithm="HS256"
            )
            from api.services.auth import AuthService
            return AuthService()
    
    def test_create_token_returns_jwt(self, auth_service):
        """Test create_token returns a valid JWT string"""
        user_id = "user_123"
        hwid = "device_abc"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        token = auth_service.create_token(user_id, hwid, expires_at)
        
        assert token is not None
        assert isinstance(token, str)
        assert token.count(".") == 2  # JWT has 3 parts
    
    def test_verify_token_valid(self, auth_service):
        """Test verify_token with valid token"""
        user_id = "user_123"
        hwid = "device_abc"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        token = auth_service.create_token(user_id, hwid, expires_at)
        payload = auth_service.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["hwid"] == hwid
        assert payload["iss"] == "tiktrend-api"
    
    def test_verify_token_expired(self, auth_service):
        """Test verify_token with expired token"""
        user_id = "user_123"
        hwid = "device_abc"
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Past
        
        token = auth_service.create_token(user_id, hwid, expires_at)
        payload = auth_service.verify_token(token)
        
        assert payload is None
    
    def test_verify_token_invalid(self, auth_service):
        """Test verify_token with invalid token"""
        payload = auth_service.verify_token("invalid.token.here")
        
        assert payload is None
    
    def test_verify_token_tampered(self, auth_service):
        """Test verify_token with tampered token"""
        user_id = "user_123"
        hwid = "device_abc"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        token = auth_service.create_token(user_id, hwid, expires_at)
        # Tamper with token
        tampered = token[:-5] + "xxxxx"
        
        payload = auth_service.verify_token(tampered)
        
        assert payload is None


class TestAuthServiceAPIKey:
    """Tests for API key generation"""
    
    @pytest.fixture
    def auth_service(self):
        with patch('api.services.auth.get_security_config') as mock_config:
            mock_config.return_value = MagicMock(
                jwt_secret_key="test_secret_key_12345",
                jwt_algorithm="HS256"
            )
            from api.services.auth import AuthService
            return AuthService()
    
    def test_generate_api_key_format(self, auth_service):
        """Test API key has correct format"""
        api_key = auth_service.generate_api_key()
        
        assert api_key.startswith("tk_")
        assert len(api_key) > 10
    
    def test_generate_api_key_unique(self, auth_service):
        """Test API keys are unique"""
        keys = [auth_service.generate_api_key() for _ in range(100)]
        
        assert len(keys) == len(set(keys))  # All unique


class TestAuthServiceAuthenticate:
    """Tests for authenticate method"""
    
    @pytest.fixture
    def auth_service(self):
        with patch('api.services.auth.get_security_config') as mock_config:
            mock_config.return_value = MagicMock(
                jwt_secret_key="test_secret_key_12345",
                jwt_algorithm="HS256"
            )
            from api.services.auth import AuthService
            return AuthService()
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database"""
        with patch('api.services.auth.database') as mock_db:
            yield mock_db
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self, auth_service, mock_database):
        """Test successful authentication"""
        password = "CorrectPassword123"
        password_hash = auth_service.hash_password(password)
        
        mock_database.fetch_one = AsyncMock(return_value={
            "id": 1,
            "email": "user@example.com",
            "name": "Test User",
            "password_hash": password_hash,
            "plan": "pro",
            "is_active": True
        })
        
        result = await auth_service.authenticate("user@example.com", password)
        
        assert result is not None
        assert result["id"] == "1"
        assert result["email"] == "user@example.com"
        assert result["name"] == "Test User"
        assert result["plan"] == "pro"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_database):
        """Test authentication with non-existent user"""
        mock_database.fetch_one = AsyncMock(return_value=None)
        
        result = await auth_service.authenticate("nobody@example.com", "password")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, auth_service, mock_database):
        """Test authentication with inactive user"""
        mock_database.fetch_one = AsyncMock(return_value={
            "id": 1,
            "email": "user@example.com",
            "name": "Test User",
            "password_hash": "hash",
            "plan": "pro",
            "is_active": False
        })
        
        result = await auth_service.authenticate("user@example.com", "password")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, auth_service, mock_database):
        """Test authentication with wrong password"""
        correct_password = "CorrectPassword123"
        password_hash = auth_service.hash_password(correct_password)
        
        mock_database.fetch_one = AsyncMock(return_value={
            "id": 1,
            "email": "user@example.com",
            "name": "Test User",
            "password_hash": password_hash,
            "plan": "pro",
            "is_active": True
        })
        
        result = await auth_service.authenticate("user@example.com", "WrongPassword")
        
        assert result is None


class TestAuthServiceUserManagement:
    """Tests for user CRUD operations"""
    
    @pytest.fixture
    def auth_service(self):
        with patch('api.services.auth.get_security_config') as mock_config:
            mock_config.return_value = MagicMock(
                jwt_secret_key="test_secret_key_12345",
                jwt_algorithm="HS256"
            )
            from api.services.auth import AuthService
            return AuthService()
    
    @pytest.fixture
    def mock_database(self):
        with patch('api.services.auth.database') as mock_db:
            yield mock_db
    
    @pytest.mark.asyncio
    async def test_create_user(self, auth_service, mock_database):
        """Test user creation"""
        mock_database.fetch_one = AsyncMock(return_value={
            "id": 1,
            "email": "new@example.com",
            "name": "New User",
            "plan": "free"
        })
        
        result = await auth_service.create_user(
            email="new@example.com",
            password="SecurePass123!",
            name="New User"
        )
        
        assert result is not None
        assert result["email"] == "new@example.com"
        assert result["name"] == "New User"
        assert result["plan"] == "free"
        
        # Verify password was hashed
        call_args = mock_database.fetch_one.call_args
        assert "password_hash" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, auth_service, mock_database):
        """Test get_user_by_email when user exists"""
        mock_database.fetch_one = AsyncMock(return_value={
            "id": 1,
            "email": "user@example.com",
            "name": "Test User",
            "plan": "pro",
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        })
        
        result = await auth_service.get_user_by_email("user@example.com")
        
        assert result is not None
        assert result["email"] == "user@example.com"
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, auth_service, mock_database):
        """Test get_user_by_email when user doesn't exist"""
        mock_database.fetch_one = AsyncMock(return_value=None)
        
        result = await auth_service.get_user_by_email("nobody@example.com")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, auth_service, mock_database):
        """Test get_user_by_id when user exists"""
        mock_database.fetch_one = AsyncMock(return_value={
            "id": 1,
            "email": "user@example.com",
            "name": "Test User",
            "plan": "pro",
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        })
        
        result = await auth_service.get_user_by_id("1")
        
        assert result is not None
        assert result["id"] == 1
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, auth_service, mock_database):
        """Test get_user_by_id when user doesn't exist"""
        mock_database.fetch_one = AsyncMock(return_value=None)
        
        result = await auth_service.get_user_by_id("99999")
        
        assert result is None


class TestAuthServiceHWIDValidation:
    """Tests for hardware ID validation"""
    
    @pytest.fixture
    def auth_service(self):
        with patch('api.services.auth.get_security_config') as mock_config:
            mock_config.return_value = MagicMock(
                jwt_secret_key="test_secret_key_12345",
                jwt_algorithm="HS256"
            )
            from api.services.auth import AuthService
            return AuthService()
    
    @pytest.fixture
    def mock_database(self):
        with patch('api.services.auth.database') as mock_db:
            yield mock_db
    
    @pytest.mark.asyncio
    async def test_validate_hwid_no_license_allows(self, auth_service, mock_database):
        """Test HWID validation allows when no license exists"""
        mock_database.fetch_one = AsyncMock(return_value=None)
        
        result = await auth_service.validate_hwid("user_123", "device_abc")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_hwid_existing_device(self, auth_service, mock_database):
        """Test HWID validation with existing registered device"""
        # First call returns license, second returns device
        mock_database.fetch_one = AsyncMock(side_effect=[
            {"id": 1, "max_devices": 3},  # License
            {"id": 10}  # Existing device
        ])
        mock_database.execute = AsyncMock()
        
        result = await auth_service.validate_hwid("user_123", "device_abc")
        
        assert result is True
        # Should update last_seen
        mock_database.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_hwid_new_device_under_limit(self, auth_service, mock_database):
        """Test HWID validation registers new device when under limit"""
        mock_database.fetch_one = AsyncMock(side_effect=[
            {"id": 1, "max_devices": 3},  # License
            None,  # No existing device
            {"count": 1}  # 1 device registered, limit is 3
        ])
        mock_database.execute = AsyncMock()
        
        result = await auth_service.validate_hwid("user_123", "new_device")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_hwid_device_limit_reached(self, auth_service, mock_database):
        """Test HWID validation rejects when device limit reached"""
        mock_database.fetch_one = AsyncMock(side_effect=[
            {"id": 1, "max_devices": 2},  # License
            None,  # No existing device
            {"count": 2}  # Already at limit
        ])
        
        result = await auth_service.validate_hwid("user_123", "new_device")
        
        assert result is False
