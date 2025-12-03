"""
License Service Complete Coverage Tests
Additional tests to achieve 100% coverage on license.py
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jose import jwt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestLicenseServiceMarkForExpiration:
    """Tests for mark_for_expiration method"""
    
    @pytest.fixture
    def mock_db(self):
        db_mock = AsyncMock()
        db_mock.execute = AsyncMock()
        return db_mock
    
    @pytest.fixture
    def license_service(self, mock_db):
        with patch('api.services.license.database', mock_db):
            from api.services.license import LicenseService
            service = LicenseService()
            service.db = mock_db
            return service
    
    @pytest.mark.asyncio
    async def test_mark_for_expiration_success(self, license_service, mock_db):
        """Test marking a license to not auto-renew"""
        license_id = str(uuid.uuid4())
        
        await license_service.mark_for_expiration(license_id)
        
        mock_db.execute.assert_called_once()
        call_args = str(mock_db.execute.call_args)
        assert "auto_renew" in call_args
        assert "false" in call_args.lower()


class TestLicenseServiceUpdatePlan:
    """Tests for update_plan method"""
    
    @pytest.fixture
    def mock_db(self):
        db_mock = AsyncMock()
        db_mock.execute = AsyncMock()
        return db_mock
    
    @pytest.fixture
    def license_service(self, mock_db):
        with patch('api.services.license.database', mock_db):
            from api.services.license import LicenseService
            service = LicenseService()
            service.db = mock_db
            return service
    
    @pytest.mark.asyncio
    async def test_update_plan_to_lifetime(self, license_service, mock_db):
        """Test updating plan to lifetime"""
        license_id = str(uuid.uuid4())
        
        await license_service.update_plan(license_id, "lifetime")
        
        mock_db.execute.assert_called_once()
        call_args = str(mock_db.execute.call_args)
        assert "plan" in call_args
        assert "max_devices" in call_args

    @pytest.mark.asyncio
    async def test_update_plan_sets_max_devices_to_2(self, license_service, mock_db):
        """Test that update_plan always sets max_devices to 2"""
        license_id = str(uuid.uuid4())
        
        await license_service.update_plan(license_id, "premium")
        
        # Verify the parameters include max_devices = 2
        call_args = mock_db.execute.call_args
        params = call_args[0][1]  # Second positional arg is params dict
        assert params.get("max_devices") == 2


class TestActivateLifetimeLicense:
    """Tests for activate_lifetime_license method"""
    
    @pytest.fixture
    def mock_db(self):
        db_mock = AsyncMock()
        db_mock.fetch_one = AsyncMock()
        db_mock.execute = AsyncMock()
        return db_mock
    
    @pytest.fixture
    def license_service(self, mock_db):
        with patch('api.services.license.database', mock_db):
            from api.services.license import LicenseService
            service = LicenseService()
            service.db = mock_db
            return service
    
    @pytest.mark.asyncio
    async def test_activate_lifetime_license_user_not_found(
        self, license_service, mock_db
    ):
        """Test activating lifetime license for non-existent user"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        result = await license_service.activate_lifetime_license(
            email="nonexistent@example.com",
            payment_id="pay_123"
        )
        
        assert result is False
        mock_db.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_activate_lifetime_license_already_has_license(
        self, license_service, mock_db
    ):
        """Test activating lifetime license when user already has one"""
        mock_db.fetch_one = AsyncMock(return_value={
            "id": "user_123",
            "has_lifetime_license": True
        })
        
        result = await license_service.activate_lifetime_license(
            email="existing@example.com",
            payment_id="pay_123"
        )
        
        # Should return True since already licensed
        assert result is True
    
    @pytest.mark.asyncio
    async def test_activate_lifetime_license_success(
        self, license_service, mock_db
    ):
        """Test successfully activating lifetime license"""
        mock_db.fetch_one = AsyncMock(return_value={
            "id": "user_123",
            "has_lifetime_license": False
        })
        
        result = await license_service.activate_lifetime_license(
            email="new@example.com",
            payment_id="pay_123"
        )
        
        assert result is True
        # Should call execute twice: update user + log transaction
        assert mock_db.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_activate_lifetime_license_without_payment_id(
        self, license_service, mock_db
    ):
        """Test activating lifetime license without payment ID"""
        mock_db.fetch_one = AsyncMock(return_value={
            "id": "user_123",
            "has_lifetime_license": False
        })
        
        result = await license_service.activate_lifetime_license(
            email="free@example.com"
        )
        
        assert result is True


class TestGetUsageStats:
    """Tests for get_usage_stats method"""
    
    @pytest.fixture
    def mock_db(self):
        db_mock = AsyncMock()
        db_mock.fetch_one = AsyncMock()
        return db_mock
    
    @pytest.fixture
    def license_service(self, mock_db):
        with patch('api.services.license.database', mock_db):
            from api.services.license import LicenseService
            service = LicenseService()
            service.db = mock_db
            return service
    
    @pytest.mark.asyncio
    async def test_get_usage_stats_success(self, license_service, mock_db):
        """Test getting usage stats for valid license"""
        mock_db.fetch_one = AsyncMock(return_value={
            "is_lifetime": True,
            "credits_balance": 100,
            "active_devices": 2
        })
        
        result = await license_service.get_usage_stats("license_123")
        
        assert result is not None
        assert result["is_lifetime"] is True
        assert result["credits"] == 100
        assert result["active_devices"] == 2
        # Verify unlimited limits for lifetime
        assert result["searches_limit"] == -1
        assert result["favorites_limit"] == -1
        assert result["exports_limit"] == -1
    
    @pytest.mark.asyncio
    async def test_get_usage_stats_license_not_found(
        self, license_service, mock_db
    ):
        """Test getting usage stats for non-existent license"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        result = await license_service.get_usage_stats("invalid_license")
        
        assert result == {}


class TestCreateLicenseJWT:
    """Tests for create_license_jwt method"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def license_service(self, mock_db):
        with patch('api.services.license.database', mock_db):
            with patch('api.services.license.settings') as mock_settings:
                mock_settings.JWT_SECRET_KEY = "test-secret-key-for-jwt"
                mock_settings.JWT_ALGORITHM = "HS256"
                from api.services.license import LicenseService
                service = LicenseService()
                service.secret_key = "test-secret-key-for-jwt"
                service.algorithm = "HS256"
                return service
    
    def test_create_license_jwt_lifetime(self, license_service):
        """Test creating JWT for lifetime license"""
        token = license_service.create_license_jwt(
            user_id="user_123",
            hwid="HWID-ABC",
            is_lifetime=True
        )
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify payload
        payload = jwt.decode(
            token,
            "test-secret-key-for-jwt",
            algorithms=["HS256"]
        )
        
        assert payload["sub"] == "user_123"
        assert payload["hwid"] == "HWID-ABC"
        assert payload["is_lifetime"] is True
        assert payload["iss"] == "tiktrend-license-service"
    
    def test_create_license_jwt_with_expiration(self, license_service):
        """Test creating JWT with custom expiration"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        token = license_service.create_license_jwt(
            user_id="user_456",
            hwid="HWID-XYZ",
            is_lifetime=False,
            expires_at=expires_at
        )
        
        assert token is not None
        
        payload = jwt.decode(
            token,
            "test-secret-key-for-jwt",
            algorithms=["HS256"]
        )
        
        assert payload["is_lifetime"] is False


class TestValidateKeyFormat:
    """Tests for validate_key_format method"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def license_service(self, mock_db):
        with patch('api.services.license.database', mock_db):
            from api.services.license import LicenseService
            return LicenseService()
    
    def test_validate_key_format_valid(self, license_service):
        """Test validating correctly formatted key"""
        valid_key = "ABCD-EFGH-1234-5678"
        
        result = license_service.validate_key_format(valid_key)
        
        assert result is True
    
    def test_validate_key_format_invalid_length(self, license_service):
        """Test validating key with wrong length"""
        invalid_key = "ABCD-EFGH-1234"  # Too short
        
        result = license_service.validate_key_format(invalid_key)
        
        assert result is False
    
    def test_validate_key_format_wrong_parts(self, license_service):
        """Test validating key with wrong number of parts"""
        invalid_key = "ABCD-EFGH-12345678"  # Wrong format
        
        result = license_service.validate_key_format(invalid_key)
        
        assert result is False
    
    def test_validate_key_format_special_characters(self, license_service):
        """Test validating key with special characters"""
        invalid_key = "AB@D-EF#H-12$4-56%8"
        
        result = license_service.validate_key_format(invalid_key)
        
        assert result is False
    
    def test_validate_key_format_lowercase(self, license_service):
        """Test validating lowercase key (should be valid if alphanumeric)"""
        lowercase_key = "abcd-efgh-1234-5678"
        
        result = license_service.validate_key_format(lowercase_key)
        
        assert result is True  # Alphanumeric includes lowercase
    
    def test_validate_key_format_wrong_part_length(self, license_service):
        """Test validating key with wrong part lengths"""
        # Total length 19 but wrong distribution
        invalid_key = "ABCDE-FGH-1234-5678"
        
        result = license_service.validate_key_format(invalid_key)
        
        # Parts must be exactly 4 chars each
        assert result is False


class TestGenerateLicenseKey:
    """Tests for generate_license_key static method"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def license_service(self, mock_db):
        with patch('api.services.license.database', mock_db):
            from api.services.license import LicenseService
            return LicenseService()
    
    def test_generate_license_key_format(self, license_service):
        """Test generated key has correct format"""
        from api.services.license import LicenseService
        
        key = LicenseService.generate_license_key()
        
        assert len(key) == 19  # XXXX-XXXX-XXXX-XXXX
        parts = key.split("-")
        assert len(parts) == 4
        for part in parts:
            assert len(part) == 4
            assert part.isalnum()
    
    def test_generate_license_key_no_confusing_chars(self, license_service):
        """Test generated key excludes confusing characters"""
        from api.services.license import LicenseService

        # Generate many keys and check for confusing chars
        # Only 0, O, 1, I are excluded in the actual implementation
        confusing_chars = set("0O1I")
        
        for _ in range(100):
            key = LicenseService.generate_license_key()
            key_chars = set(key.replace("-", ""))
            assert key_chars.isdisjoint(confusing_chars), \
                f"Key {key} contains confusing character"
    
    def test_generate_license_key_uniqueness(self, license_service):
        """Test generated keys are unique"""
        from api.services.license import LicenseService
        
        keys = set()
        for _ in range(500):
            keys.add(LicenseService.generate_license_key())
        
        assert len(keys) == 500


class TestGetLifetimeFeatures:
    """Tests for get_lifetime_features static method"""
    
    def test_get_lifetime_features_structure(self):
        """Test lifetime features has correct structure"""
        from api.services.license import LicenseService
        
        features = LicenseService.get_lifetime_features()
        
        assert features is not None
        assert isinstance(features, dict)
        
        # Verify expected keys exist
        expected_keys = [
            "unlimited_searches",
            "unlimited_favorites",
            "unlimited_exports",
            "multi_source",
            "advanced_filters",
            "export_formats",
            "max_devices",
            "free_updates",
            "priority_support",
            "api_access",
            "seller_bot"
        ]
        
        for key in expected_keys:
            assert key in features, f"Missing key: {key}"
    
    def test_get_lifetime_features_values(self):
        """Test lifetime features have correct values"""
        from api.services.license import LicenseService
        
        features = LicenseService.get_lifetime_features()
        
        assert features["unlimited_searches"] is True
        assert features["unlimited_favorites"] is True
        assert features["unlimited_exports"] is True
        assert features["max_devices"] == 2
        assert features["seller_bot"] is False  # Requires premium
        assert "csv" in features["export_formats"]


class TestGetPremiumBotFeatures:
    """Tests for get_premium_bot_features static method"""
    
    def test_get_premium_bot_features_structure(self):
        """Test premium bot features has correct structure"""
        from api.services.license import LicenseService
        
        features = LicenseService.get_premium_bot_features()
        
        assert features is not None
        assert isinstance(features, dict)
        assert features["seller_bot"] is True
        assert "seller_bot_features" in features
    
    def test_get_premium_bot_features_values(self):
        """Test premium bot features have correct values"""
        from api.services.license import LicenseService
        
        features = LicenseService.get_premium_bot_features()
        
        assert features["max_devices"] == 3  # Extra for bot
        assert features["priority_support"] is True
        assert features["api_access"] is True
        
        bot_features = features["seller_bot_features"]
        assert bot_features["post_products"] is True
        assert bot_features["max_tasks_per_day"] == 50


class TestGetPlanFeatures:
    """Tests for get_plan_features static method"""
    
    def test_get_plan_features_lifetime(self):
        """Test getting features for lifetime plan"""
        from api.services.license import LicenseService
        
        features = LicenseService.get_plan_features("lifetime")
        
        assert features["unlimited_searches"] is True
    
    def test_get_plan_features_premium_bot(self):
        """Test getting features for premium_bot plan"""
        from api.services.license import LicenseService
        
        features = LicenseService.get_plan_features("premium_bot")
        
        assert features["seller_bot"] is True
    
    def test_get_plan_features_legacy_plan(self):
        """Test getting features for legacy/unknown plan"""
        from api.services.license import LicenseService
        
        features = LicenseService.get_plan_features("basic")
        
        # Legacy plans get restricted features
        assert features["unlimited_searches"] is False
        assert features["max_devices"] == 0
        assert features["export_formats"] == []
    
    def test_get_plan_features_unknown_plan(self):
        """Test getting features for completely unknown plan"""
        from api.services.license import LicenseService
        
        features = LicenseService.get_plan_features("nonexistent")
        
        # Should return restricted defaults
        assert features is not None
        assert features["unlimited_searches"] is False


class TestAddCreditsEdgeCases:
    """Additional tests for add_credits edge cases"""
    
    @pytest.fixture
    def mock_db(self):
        db_mock = AsyncMock()
        db_mock.fetch_one = AsyncMock()
        db_mock.execute = AsyncMock()
        return db_mock
    
    @pytest.fixture
    def license_service(self, mock_db):
        with patch('api.services.license.database', mock_db):
            from api.services.license import LicenseService
            service = LicenseService()
            service.db = mock_db
            return service
    
    @pytest.mark.asyncio
    async def test_add_credits_user_not_found_returns_zero(
        self, license_service, mock_db
    ):
        """Test add_credits returns 0 when user not found"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        result = await license_service.add_credits(
            email="missing@example.com",
            amount=100,
            payment_id="pay_123"
        )
        
        assert result == 0
        # Should not try to update credits
        mock_db.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_add_credits_large_amount(
        self, license_service, mock_db
    ):
        """Test adding large amount of credits"""
        mock_db.fetch_one = AsyncMock(return_value={
            "id": "user_123",
            "credits_balance": 1000
        })
        
        result = await license_service.add_credits(
            email="rich@example.com",
            amount=1000000,
            payment_id="pay_mega"
        )
        
        assert result == 1001000  # 1000 + 1000000
    
    @pytest.mark.asyncio
    async def test_add_credits_zero_initial_balance(
        self, license_service, mock_db
    ):
        """Test adding credits when user has zero balance"""
        mock_db.fetch_one = AsyncMock(return_value={
            "id": "user_123",
            "credits_balance": 0
        })
        
        result = await license_service.add_credits(
            email="newuser@example.com",
            amount=50,
            payment_id="pay_first"
        )
        
        assert result == 50


class TestBlacklistService:
    """Tests for BlacklistService (JWT token blacklisting)"""
    
    @pytest.fixture
    def mock_redis(self):
        redis_mock = AsyncMock()
        redis_mock.setex = AsyncMock()
        redis_mock.exists = AsyncMock(return_value=0)
        return redis_mock
    
    @pytest.fixture
    def blacklist_service(self, mock_redis):
        with patch('api.services.blacklist.get_redis_pool', 
                   AsyncMock(return_value=mock_redis)):
            from api.services.blacklist import BlacklistService
            return BlacklistService()
    
    @pytest.mark.asyncio
    async def test_add_token_to_blacklist(self, blacklist_service, mock_redis):
        """Test adding a token to blacklist"""
        with patch('api.services.blacklist.get_redis_pool', 
                   AsyncMock(return_value=mock_redis)):
            result = await blacklist_service.add(
                token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                ttl=3600
            )
            
            assert result is True
            mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_token_not_blacklisted(self, blacklist_service, mock_redis):
        """Test checking token that is not blacklisted"""
        mock_redis.exists = AsyncMock(return_value=0)
        
        with patch('api.services.blacklist.get_redis_pool', 
                   AsyncMock(return_value=mock_redis)):
            result = await blacklist_service.is_blacklisted(
                token="valid_token"
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_token_is_blacklisted(self, blacklist_service, mock_redis):
        """Test checking token that is blacklisted"""
        mock_redis.exists = AsyncMock(return_value=1)
        
        with patch('api.services.blacklist.get_redis_pool', 
                   AsyncMock(return_value=mock_redis)):
            result = await blacklist_service.is_blacklisted(
                token="revoked_token"
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_blacklist_key_prefix(self, blacklist_service, mock_redis):
        """Test blacklist uses correct key prefix"""
        with patch('api.services.blacklist.get_redis_pool', 
                   AsyncMock(return_value=mock_redis)):
            await blacklist_service.add(
                token="test_token",
                ttl=1800
            )
            
            # Verify key includes prefix
            call_args = mock_redis.setex.call_args
            key = call_args[0][0]
            assert key.startswith("blacklist:")
            assert key.startswith("blacklist:")
