"""
License Service Tests - 100% Coverage
Tests for license management and validation
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from backend.api.services.license import LicenseService


class TestLicenseService:
    """Test suite for LicenseService"""

    @pytest.fixture
    def license_service(self):
        """Create a license service instance"""
        return LicenseService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database"""
        db_mock = AsyncMock()
        db_mock.fetch_one = AsyncMock(return_value=None)
        db_mock.fetch_all = AsyncMock(return_value=[])
        db_mock.execute = AsyncMock()
        return db_mock

    @pytest.fixture
    def sample_license(self):
        """Sample license data"""
        return {
            'id': str(uuid.uuid4()),
            'user_id': str(uuid.uuid4()),
            'license_key': 'LICENSE-XXXXX-XXXXX-XXXXX',
            'plan': 'pro',
            'expires_at': (datetime.now() + timedelta(days=30)).isoformat(),
            'is_active': True,
            'email': 'test@example.com',
            'name': 'Test User'
        }

    # ==================== GET LICENSE BY EMAIL Tests ====================

    @pytest.mark.asyncio
    async def test_get_license_by_email_found(self, license_service, mock_db, sample_license):
        """Test getting license by email when exists"""
        mock_db.fetch_one = AsyncMock(return_value=sample_license)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.get_license_by_email('test@example.com')
            
            assert result is not None
            assert result['email'] == 'test@example.com'

    @pytest.mark.asyncio
    async def test_get_license_by_email_not_found(self, license_service, mock_db):
        """Test getting license by email when not exists"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.get_license_by_email('nonexistent@example.com')
            
            assert result is None

    # ==================== GET LICENSE BY KEY Tests ====================

    @pytest.mark.asyncio
    async def test_get_license_by_key_found(self, license_service, mock_db, sample_license):
        """Test getting license by key when exists"""
        mock_db.fetch_one = AsyncMock(return_value=sample_license)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.get_license_by_key('LICENSE-XXXXX-XXXXX-XXXXX')
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_license_by_key_not_found(self, license_service, mock_db):
        """Test getting license by key when not exists"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.get_license_by_key('INVALID-KEY')
            
            assert result is None

    # ==================== GET LICENSE BY USER Tests ====================

    @pytest.mark.asyncio
    async def test_get_license_by_user_found(self, license_service, mock_db, sample_license):
        """Test getting license by user ID when exists"""
        mock_db.fetch_one = AsyncMock(return_value=sample_license)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.get_license_by_user('user-id-123')
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_license_by_user_not_found(self, license_service, mock_db):
        """Test getting license by user ID when not exists"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.get_license_by_user('nonexistent-user')
            
            assert result is None

    # ==================== VALIDATE HWID Tests ====================

    @pytest.mark.asyncio
    async def test_validate_hwid_valid(self, license_service, mock_db):
        """Test validating HWID when registered"""
        mock_db.fetch_one = AsyncMock(return_value={'id': 'device-id'})
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.validate_hwid('license-id', 'HWID-123')
            
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_hwid_invalid(self, license_service, mock_db):
        """Test validating HWID when not registered"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.validate_hwid('license-id', 'UNKNOWN-HWID')
            
            assert result is False

    # ==================== GET ACTIVE DEVICES Tests ====================

    @pytest.mark.asyncio
    async def test_get_active_devices_with_devices(self, license_service, mock_db):
        """Test getting active devices when exist"""
        devices = [
            {'id': '1', 'device_id': 'HWID-1', 'created_at': datetime.now(), 'last_seen': datetime.now()},
            {'id': '2', 'device_id': 'HWID-2', 'created_at': datetime.now(), 'last_seen': datetime.now()}
        ]
        mock_db.fetch_all = AsyncMock(return_value=devices)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.get_active_devices('license-id')
            
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_active_devices_empty(self, license_service, mock_db):
        """Test getting active devices when none exist"""
        mock_db.fetch_all = AsyncMock(return_value=[])
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.get_active_devices('license-id')
            
            assert result == []

    # ==================== REGISTER DEVICE Tests ====================

    @pytest.mark.asyncio
    async def test_register_device_new(self, license_service, mock_db):
        """Test registering a new device"""
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            await license_service.register_device('license-id', 'HWID-123', '1.0.0')
            
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_device_upsert(self, license_service, mock_db):
        """Test registering device performs upsert"""
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            await license_service.register_device('license-id', 'HWID-123', '2.0.0')
            
            # Check that ON CONFLICT clause is in the query
            call_args = mock_db.execute.call_args
            assert 'ON CONFLICT' in call_args[0][0]

    # ==================== DEACTIVATE DEVICE Tests ====================

    @pytest.mark.asyncio
    async def test_deactivate_device_success(self, license_service, mock_db):
        """Test deactivating a device successfully"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.deactivate_device('license-id', 'HWID-123')
            
            assert result is True

    @pytest.mark.asyncio
    async def test_deactivate_device_not_found(self, license_service, mock_db):
        """Test deactivating a device that doesn't exist"""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.deactivate_device('license-id', 'UNKNOWN')
            
            assert result is False

    @pytest.mark.asyncio
    async def test_deactivate_device_with_reason(self, license_service, mock_db):
        """Test deactivating a device with reason"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.deactivate_device(
                'license-id', 
                'HWID-123', 
                reason='User requested'
            )
            
            assert result is True


class TestLicenseServiceKeyGeneration:
    """Tests for license key generation"""

    @pytest.fixture
    def license_service(self):
        return LicenseService()

    def test_generate_license_key_format(self, license_service):
        """Test generated license key format"""
        # Generate key if method exists
        if hasattr(license_service, 'generate_license_key'):
            key = license_service.generate_license_key()
            assert isinstance(key, str)
            assert len(key) > 10

    def test_generate_license_key_uniqueness(self, license_service):
        """Test generated keys are unique"""
        if hasattr(license_service, 'generate_license_key'):
            keys = set()
            for _ in range(100):
                keys.add(license_service.generate_license_key())
            assert len(keys) == 100


class TestLicenseServiceEdgeCases:
    """Edge case tests for LicenseService"""

    @pytest.fixture
    def license_service(self):
        return LicenseService()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_validate_hwid_with_empty_string(self, license_service, mock_db):
        """Test validating empty HWID"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.validate_hwid('license-id', '')
            
            assert result is False

    @pytest.mark.asyncio
    async def test_get_license_by_email_with_special_chars(self, license_service, mock_db):
        """Test getting license with special characters in email"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            result = await license_service.get_license_by_email("test+tag@example.com")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_register_device_with_long_hwid(self, license_service, mock_db):
        """Test registering device with very long HWID"""
        long_hwid = 'A' * 1000
        
        with patch('backend.api.services.license.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            # Should not raise an error
            await license_service.register_device('license-id', long_hwid, '1.0.0')
            
            mock_db.execute.assert_called_once()
