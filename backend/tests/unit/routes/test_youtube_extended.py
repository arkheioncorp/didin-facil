"""
Extended tests for YouTube routes - quota management and edge cases.
Coverage target: Cover all quota-related functions and edge cases.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.youtube import (QUOTA_COSTS, YOUTUBE_DAILY_QUOTA,
                                _check_quota_alerts, _track_quota_usage,
                                get_quota_history, get_quota_status,
                                upload_video)

# ==================== FIXTURES ====================

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock()
    user.__getitem__ = lambda s, k: {"id": "user-123"}[k]
    return user


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.lpush = AsyncMock()
    return redis


@pytest.fixture
def mock_subscription_service():
    """Mock subscription service."""
    service = AsyncMock()
    service.can_use_feature = AsyncMock(return_value=True)
    service.increment_usage = AsyncMock()
    return service


# ==================== QUOTA CONSTANTS TESTS ====================

class TestQuotaConstants:
    """Test quota-related constants."""
    
    def test_youtube_daily_quota(self):
        """Test YouTube daily quota constant."""
        assert YOUTUBE_DAILY_QUOTA == 10000
    
    def test_quota_costs_upload(self):
        """Test upload quota cost."""
        assert QUOTA_COSTS["upload"] == 1600
    
    def test_quota_costs_update(self):
        """Test update quota cost."""
        assert QUOTA_COSTS["update"] == 50
    
    def test_quota_costs_delete(self):
        """Test delete quota cost."""
        assert QUOTA_COSTS["delete"] == 50
    
    def test_quota_costs_list(self):
        """Test list quota cost."""
        assert QUOTA_COSTS["list"] == 1
    
    def test_quota_costs_read(self):
        """Test read quota cost."""
        assert QUOTA_COSTS["read"] == 1
    
    def test_quota_costs_thumbnail(self):
        """Test thumbnail quota cost."""
        assert QUOTA_COSTS["thumbnail"] == 50
    
    def test_quota_costs_playlist(self):
        """Test playlist insert quota cost."""
        assert QUOTA_COSTS["playlist_insert"] == 50


# ==================== TRACK QUOTA USAGE TESTS ====================

class TestTrackQuotaUsage:
    """Test _track_quota_usage function."""
    
    @pytest.mark.asyncio
    async def test_track_quota_first_usage(self, mock_redis):
        """Test tracking quota for first usage of the day."""
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _track_quota_usage("user-123", "upload", 1600)
            
            # Verify redis.set was called with new usage data
            mock_redis.set.assert_called()
            call_args = mock_redis.set.call_args
            saved_data = json.loads(call_args[0][1])
            assert saved_data["total"] == 1600
            assert saved_data["operations"]["upload"] == 1600
    
    @pytest.mark.asyncio
    async def test_track_quota_incremental_usage(self, mock_redis):
        """Test tracking quota increments existing usage."""
        existing_data = json.dumps({"total": 1000, "operations": {"list": 1000}})
        mock_redis.get = AsyncMock(return_value=existing_data)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _track_quota_usage("user-123", "upload", 1600)
            
            call_args = mock_redis.set.call_args
            saved_data = json.loads(call_args[0][1])
            assert saved_data["total"] == 2600
            assert saved_data["operations"]["list"] == 1000
            assert saved_data["operations"]["upload"] == 1600
    
    @pytest.mark.asyncio
    async def test_track_quota_uses_default_cost(self, mock_redis):
        """Test tracking quota uses default cost from QUOTA_COSTS."""
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _track_quota_usage("user-123", "upload")  # No cost specified
            
            call_args = mock_redis.set.call_args
            saved_data = json.loads(call_args[0][1])
            assert saved_data["total"] == 1600  # Default for upload
    
    @pytest.mark.asyncio
    async def test_track_quota_unknown_operation(self, mock_redis):
        """Test tracking quota with unknown operation defaults to 1."""
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _track_quota_usage("user-123", "unknown_operation")
            
            call_args = mock_redis.set.call_args
            saved_data = json.loads(call_args[0][1])
            assert saved_data["total"] == 1  # Default fallback
    
    @pytest.mark.asyncio
    async def test_track_quota_set_expiration(self, mock_redis):
        """Test tracking quota sets correct expiration."""
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _track_quota_usage("user-123", "upload")
            
            call_args = mock_redis.set.call_args
            assert call_args.kwargs.get('ex') == 172800  # 2 days
    
    @pytest.mark.asyncio
    async def test_track_quota_same_operation_twice(self, mock_redis):
        """Test tracking same operation multiple times."""
        existing_data = json.dumps({"total": 1600, "operations": {"upload": 1600}})
        mock_redis.get = AsyncMock(return_value=existing_data)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _track_quota_usage("user-123", "upload", 1600)
            
            call_args = mock_redis.set.call_args
            saved_data = json.loads(call_args[0][1])
            assert saved_data["total"] == 3200
            assert saved_data["operations"]["upload"] == 3200


# ==================== CHECK QUOTA ALERTS TESTS ====================

class TestCheckQuotaAlerts:
    """Test _check_quota_alerts function."""
    
    @pytest.mark.asyncio
    async def test_no_alert_under_threshold(self, mock_redis):
        """Test no alert when under all thresholds."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _check_quota_alerts("user-123", 5000)  # 50% - under 70%
            
            mock_redis.lpush.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_warning_alert_70_percent(self, mock_redis):
        """Test warning alert at 70% usage."""
        mock_redis.get = AsyncMock(return_value=None)  # Alert not yet sent
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _check_quota_alerts("user-123", 7000)  # 70%
            
            # Should set alert key and push notification
            mock_redis.set.assert_called()
            mock_redis.lpush.assert_called()
    
    @pytest.mark.asyncio
    async def test_critical_alert_85_percent(self, mock_redis):
        """Test critical alert at 85% usage."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _check_quota_alerts("user-123", 8500)  # 85%
            
            mock_redis.lpush.assert_called()
    
    @pytest.mark.asyncio
    async def test_exhausted_alert_95_percent(self, mock_redis):
        """Test exhausted alert at 95% usage."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _check_quota_alerts("user-123", 9500)  # 95%
            
            mock_redis.lpush.assert_called()
    
    @pytest.mark.asyncio
    async def test_alert_not_sent_twice(self, mock_redis):
        """Test that alerts are not sent twice on same day."""
        mock_redis.get = AsyncMock(return_value="1")  # Alert already sent
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _check_quota_alerts("user-123", 9500)
            
            mock_redis.lpush.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_alert_notification_content(self, mock_redis):
        """Test alert notification contains correct data."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            await _check_quota_alerts("user-123", 7000)
            
            # Check lpush was called with correct notification
            lpush_call = mock_redis.lpush.call_args
            notification = json.loads(lpush_call[0][1])
            
            assert notification["type"] == "youtube_quota"
            assert notification["level"] == "warning"
            assert notification["usage"] == 7000
            assert notification["limit"] == YOUTUBE_DAILY_QUOTA
            assert notification["percentage"] == 70


# ==================== GET QUOTA STATUS TESTS ====================

class TestGetQuotaStatus:
    """Test get_quota_status endpoint."""
    
    @pytest.mark.asyncio
    async def test_quota_status_unauthenticated(self):
        """Test quota status for unauthenticated user."""
        result = await get_quota_status(current_user=None)
        
        assert result["quota"]["daily_limit"] == YOUTUBE_DAILY_QUOTA
        assert result["quota"]["used"] == 0
        assert result["quota"]["remaining"] == YOUTUBE_DAILY_QUOTA
        assert result["quota"]["percentage_used"] == 0
    
    @pytest.mark.asyncio
    async def test_quota_status_no_usage(self, mock_user, mock_redis):
        """Test quota status with no usage data."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            result = await get_quota_status(current_user=mock_user)
            
            assert result["quota"]["used"] == 0
            assert result["quota"]["remaining"] == YOUTUBE_DAILY_QUOTA
    
    @pytest.mark.asyncio
    async def test_quota_status_with_usage(self, mock_user, mock_redis):
        """Test quota status with existing usage."""
        usage_data = json.dumps({
            "total": 3200,
            "operations": {"upload": 3200}
        })
        mock_redis.get = AsyncMock(return_value=usage_data)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            result = await get_quota_status(current_user=mock_user)
            
            assert result["quota"]["used"] == 3200
            assert result["quota"]["remaining"] == YOUTUBE_DAILY_QUOTA - 3200
            assert result["quota"]["percentage_used"] == 32.0
            assert result["operations"]["upload"] == 3200
    
    @pytest.mark.asyncio
    async def test_quota_status_estimates(self, mock_user, mock_redis):
        """Test quota status includes correct estimates."""
        usage_data = json.dumps({"total": 0, "operations": {}})
        mock_redis.get = AsyncMock(return_value=usage_data)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            result = await get_quota_status(current_user=mock_user)
            
            assert result["estimates"]["uploads_remaining"] == YOUTUBE_DAILY_QUOTA // QUOTA_COSTS["upload"]
            assert result["estimates"]["updates_remaining"] == YOUTUBE_DAILY_QUOTA // QUOTA_COSTS["update"]
    
    @pytest.mark.asyncio
    async def test_quota_status_reset_time(self, mock_user, mock_redis):
        """Test quota status includes reset time."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            result = await get_quota_status(current_user=mock_user)
            
            assert result["reset_time"] == "00:00 PST (Pacific Time)"


# ==================== GET QUOTA HISTORY TESTS ====================

class TestGetQuotaHistory:
    """Test get_quota_history endpoint."""
    
    @pytest.mark.asyncio
    async def test_quota_history_default_days(self, mock_user, mock_redis):
        """Test quota history returns 7 days by default."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            result = await get_quota_history(days=7, current_user=mock_user)
            
            assert result["days"] == 7
            assert len(result["history"]) == 7
    
    @pytest.mark.asyncio
    async def test_quota_history_custom_days(self, mock_user, mock_redis):
        """Test quota history with custom days."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            result = await get_quota_history(days=14, current_user=mock_user)
            
            assert result["days"] == 14
            assert len(result["history"]) == 14
    
    @pytest.mark.asyncio
    async def test_quota_history_with_data(self, mock_user, mock_redis):
        """Test quota history with existing usage data."""
        usage_data = json.dumps({
            "total": 5000,
            "operations": {"upload": 3200, "update": 1800}
        })
        mock_redis.get = AsyncMock(return_value=usage_data)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            result = await get_quota_history(days=3, current_user=mock_user)
            
            # All 3 days should have the same mocked data
            for day in result["history"]:
                assert day["total_used"] == 5000
                assert day["operations"]["upload"] == 3200
    
    @pytest.mark.asyncio
    async def test_quota_history_no_data(self, mock_user, mock_redis):
        """Test quota history with no usage data returns zeros."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            result = await get_quota_history(days=3, current_user=mock_user)
            
            for day in result["history"]:
                assert day["total_used"] == 0
                assert day["operations"] == {}
    
    @pytest.mark.asyncio
    async def test_quota_history_date_format(self, mock_user, mock_redis):
        """Test quota history has correct date format."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.youtube.get_redis', return_value=mock_redis):
            result = await get_quota_history(days=1, current_user=mock_user)
            
            # Date should be in YYYY-MM-DD format
            date = result["history"][0]["date"]
            assert len(date) == 10
            assert date[4] == "-"
            assert date[7] == "-"


# ==================== UPLOAD VIDEO EXTENDED TESTS ====================

class TestUploadVideoExtended:
    """Extended tests for upload_video function."""
    
    @pytest.mark.asyncio
    async def test_upload_tracks_quota(self, mock_user, mock_subscription_service, mock_redis):
        """Test that successful upload tracks quota usage."""
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file = MagicMock()
        mock_file.file.read = MagicMock(return_value=b"video data")
        
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        
        mock_upload_result = MagicMock()
        mock_upload_result.success = True
        mock_upload_result.video_id = "video-123"
        mock_upload_result.url = "https://youtube.com/watch?v=video-123"
        mock_upload_result.error = None
        mock_client.upload_video = AsyncMock(return_value=mock_upload_result)
        
        with patch('api.routes.youtube.os.path.exists', return_value=True), \
             patch('api.routes.youtube.os.makedirs'), \
             patch('api.routes.youtube.shutil.copyfileobj'), \
             patch('api.routes.youtube.os.remove'), \
             patch('api.routes.youtube.YouTubeClient', return_value=mock_client), \
             patch('api.routes.youtube._track_quota_usage', new_callable=AsyncMock) as mock_track, \
             patch('api.routes.youtube.settings') as mock_settings:
            
            mock_settings.DATA_DIR = "/tmp/data"
            
            result = await upload_video(
                account_name="test_channel",
                title="Test Video",
                description="Description",
                tags="tag1,tag2",
                privacy="public",
                category="26",
                is_short=False,
                file=mock_file,
                thumbnail=None,
                current_user=mock_user,
                service=mock_subscription_service
            )
            
            assert result["status"] == "success"
            assert result["video_id"] == "video-123"
            mock_track.assert_called_once_with("user-123", "upload", 1600)
    
    @pytest.mark.asyncio
    async def test_upload_with_thumbnail(self, mock_user, mock_subscription_service):
        """Test upload with thumbnail file."""
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file = MagicMock()
        
        mock_thumb = MagicMock()
        mock_thumb.filename = "thumb.jpg"
        mock_thumb.file = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        
        mock_upload_result = MagicMock()
        mock_upload_result.success = True
        mock_upload_result.video_id = "video-123"
        mock_upload_result.url = None  # Test fallback URL generation
        mock_upload_result.error = None
        mock_client.upload_video = AsyncMock(return_value=mock_upload_result)
        
        with patch('api.routes.youtube.os.path.exists', return_value=True), \
             patch('api.routes.youtube.os.makedirs'), \
             patch('api.routes.youtube.shutil.copyfileobj'), \
             patch('api.routes.youtube.os.remove'), \
             patch('api.routes.youtube.YouTubeClient', return_value=mock_client), \
             patch('api.routes.youtube._track_quota_usage', new_callable=AsyncMock), \
             patch('api.routes.youtube.settings') as mock_settings:
            
            mock_settings.DATA_DIR = "/tmp/data"
            
            result = await upload_video(
                account_name="test_channel",
                title="Test Video",
                description="",
                tags="",
                privacy="private",
                category="26",
                is_short=True,
                file=mock_file,
                thumbnail=mock_thumb,
                current_user=mock_user,
                service=mock_subscription_service
            )
            
            assert result["status"] == "success"
            # URL should be generated from video_id
            assert "video-123" in result["url"]
    
    @pytest.mark.asyncio
    async def test_upload_failed_result(self, mock_user, mock_subscription_service):
        """Test upload when YouTube returns failure."""
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        
        mock_upload_result = MagicMock()
        mock_upload_result.success = False
        mock_upload_result.video_id = None
        mock_upload_result.url = None
        mock_upload_result.error = "Video rejected"
        mock_client.upload_video = AsyncMock(return_value=mock_upload_result)
        
        with patch('api.routes.youtube.os.path.exists', return_value=True), \
             patch('api.routes.youtube.os.makedirs'), \
             patch('api.routes.youtube.shutil.copyfileobj'), \
             patch('api.routes.youtube.os.remove'), \
             patch('api.routes.youtube.YouTubeClient', return_value=mock_client), \
             patch('api.routes.youtube.settings') as mock_settings:
            
            mock_settings.DATA_DIR = "/tmp/data"
            
            with pytest.raises(Exception) as exc_info:
                await upload_video(
                    account_name="test_channel",
                    title="Test Video",
                    description="",
                    tags="",
                    privacy="private",
                    category="26",
                    is_short=False,
                    file=mock_file,
                    thumbnail=None,
                    current_user=mock_user,
                    service=mock_subscription_service
                )
            
            assert exc_info.value.status_code == 500
            assert "Video rejected" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_upload_cleans_temp_files(self, mock_user, mock_subscription_service):
        """Test that upload cleans up temp files even on error."""
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock(side_effect=Exception("Auth failed"))
        
        with patch('api.routes.youtube.os.path.exists', return_value=True), \
             patch('api.routes.youtube.os.makedirs'), \
             patch('api.routes.youtube.shutil.copyfileobj'), \
             patch('api.routes.youtube.os.remove') as mock_remove, \
             patch('api.routes.youtube.YouTubeClient', return_value=mock_client), \
             patch('api.routes.youtube.settings') as mock_settings:
            
            mock_settings.DATA_DIR = "/tmp/data"
            
            with pytest.raises(Exception):
                await upload_video(
                    account_name="test_channel",
                    title="Test Video",
                    description="",
                    tags="",
                    privacy="private",
                    category="26",
                    is_short=False,
                    file=mock_file,
                    thumbnail=None,
                    current_user=mock_user,
                    service=mock_subscription_service
                )
            
            # Should still clean up temp file
            mock_remove.assert_called()
    
    @pytest.mark.asyncio
    async def test_upload_privacy_mapping(self, mock_user, mock_subscription_service):
        """Test upload handles different privacy values."""
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        
        mock_upload_result = MagicMock()
        mock_upload_result.success = True
        mock_upload_result.video_id = "video-123"
        mock_upload_result.url = "https://youtube.com/watch?v=video-123"
        mock_upload_result.error = None
        mock_client.upload_video = AsyncMock(return_value=mock_upload_result)
        
        for privacy in ["public", "private", "unlisted"]:
            with patch('api.routes.youtube.os.path.exists', return_value=True), \
                 patch('api.routes.youtube.os.makedirs'), \
                 patch('api.routes.youtube.shutil.copyfileobj'), \
                 patch('api.routes.youtube.os.remove'), \
                 patch('api.routes.youtube.YouTubeClient', return_value=mock_client), \
                 patch('api.routes.youtube._track_quota_usage', new_callable=AsyncMock), \
                 patch('api.routes.youtube.settings') as mock_settings:
                
                mock_settings.DATA_DIR = "/tmp/data"
                
                result = await upload_video(
                    account_name="test_channel",
                    title="Test Video",
                    description="",
                    tags="",
                    privacy=privacy,
                    category="26",
                    is_short=False,
                    file=mock_file,
                    thumbnail=None,
                    current_user=mock_user,
                    service=mock_subscription_service
                )
                
                assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_upload_parse_tags(self, mock_user, mock_subscription_service):
        """Test upload correctly parses comma-separated tags."""
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        
        mock_upload_result = MagicMock()
        mock_upload_result.success = True
        mock_upload_result.video_id = "video-123"
        mock_upload_result.url = "https://youtube.com/watch?v=video-123"
        mock_upload_result.error = None
        mock_client.upload_video = AsyncMock(return_value=mock_upload_result)
        
        with patch('api.routes.youtube.os.path.exists', return_value=True), \
             patch('api.routes.youtube.os.makedirs'), \
             patch('api.routes.youtube.shutil.copyfileobj'), \
             patch('api.routes.youtube.os.remove'), \
             patch('api.routes.youtube.YouTubeClient', return_value=mock_client), \
             patch('api.routes.youtube._track_quota_usage', new_callable=AsyncMock), \
             patch('api.routes.youtube.settings') as mock_settings:
            
            mock_settings.DATA_DIR = "/tmp/data"
            
            result = await upload_video(
                account_name="test_channel",
                title="Test Video",
                description="",
                tags="tag1, tag2, , tag3",  # With spaces and empty
                privacy="private",
                category="26",
                is_short=False,
                file=mock_file,
                thumbnail=None,
                current_user=mock_user,
                service=mock_subscription_service
            )
            
            assert result["status"] == "success"
            # Verify the tags were parsed correctly by checking upload call
            upload_call = mock_client.upload_video.call_args
            metadata = upload_call[0][1]
            assert len(metadata.tags) == 3
            assert "tag1" in metadata.tags
            assert "tag2" in metadata.tags
            assert "tag3" in metadata.tags
