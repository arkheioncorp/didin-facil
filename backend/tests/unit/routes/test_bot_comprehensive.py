"""
Comprehensive tests for bot.py routes.
Target: Increase coverage from 44% to 90%+
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock authenticated premium user."""
    return {"id": "user-123", "email": "premium@example.com", "name": "Premium User"}


@pytest.fixture
def mock_license_info():
    """Mock license information."""
    return {
        "plan": "premium_bot",
        "email": "premium@example.com",
        "valid_until": "2025-12-31"
    }


@pytest.fixture
def mock_task():
    """Mock task object."""
    from seller_bot.queue.models import TaskState
    mock = MagicMock()
    mock.id = "task-123"
    mock.task_type = "post_product"
    mock.state = TaskState.QUEUED  # Use actual enum
    mock.created_at = datetime(2024, 1, 1, 12, 0)
    mock.started_at = None
    mock.completed_at = None
    mock.error_message = None
    mock.screenshots = []
    mock.logs = []
    return mock


@pytest.fixture
def mock_profile():
    """Mock profile object."""
    mock = MagicMock()
    mock.id = "profile-123"
    mock.name = "Test Profile"
    mock.is_logged_in = True
    mock.last_used_at = datetime(2024, 1, 1)
    mock.created_at = datetime(2024, 1, 1)
    return mock


@pytest.fixture
def mock_queue_stats():
    """Mock queue statistics."""
    mock = MagicMock()
    mock.total_queued = 5
    mock.total_running = 1
    mock.total_completed = 10
    mock.total_failed = 2
    mock.by_task_type = {"post_product": 8, "analytics": 4, "reply_messages": 5}
    return mock


# ============================================
# METRICS HELPER TESTS
# ============================================

class TestMetricsHelpers:
    """Tests for metrics helper functions."""
    
    def test_record_task_created(self):
        """Test recording task creation metric."""
        with patch("api.routes.bot._metrics") as mock_metrics:
            from api.routes.bot import record_task_created
            record_task_created("post_product")
            mock_metrics.record_request.assert_called()
    
    def test_record_task_completed(self):
        """Test recording task completion metric."""
        with patch("api.routes.bot._metrics") as mock_metrics:
            from api.routes.bot import record_task_completed
            record_task_completed("analytics", 150.0)
            mock_metrics.record_success.assert_called()
    
    def test_record_task_failed(self):
        """Test recording task failure metric."""
        with patch("api.routes.bot._metrics") as mock_metrics:
            from api.routes.bot import record_task_failed
            record_task_failed("reply_messages", "Timeout error")
            mock_metrics.record_failure.assert_called()
    
    def test_record_profile_operation(self):
        """Test recording profile operation metric."""
        with patch("api.routes.bot._metrics") as mock_metrics:
            from api.routes.bot import record_profile_operation
            record_profile_operation("create")
            mock_metrics.record_request.assert_called()
    
    def test_record_api_latency(self):
        """Test recording API latency metric."""
        with patch("api.routes.bot._metrics") as mock_metrics:
            from api.routes.bot import record_api_latency
            record_api_latency("task_create", 100.0)
            mock_metrics.record_success.assert_called()


# ============================================
# WEBSOCKET HELPER TESTS
# ============================================

class TestWebSocketHelpers:
    """Tests for WebSocket notification helpers."""
    
    @pytest.mark.asyncio
    async def test_notify_task_update_success(self):
        """Test successful WebSocket notification."""
        with patch("api.routes.bot.publish_notification", new_callable=AsyncMock) as mock_publish:
            from api.routes.bot import notify_task_update
            
            await notify_task_update(
                task_id="task-123",
                notification_type="BOT_TASK_STARTED",
                title="Task Started",
                message="Test message",
                user_id="user-123",
                data={"key": "value"}
            )
            
            mock_publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_task_update_with_exception(self):
        """Test notification handling when exception occurs."""
        with patch("api.routes.bot.publish_notification", new_callable=AsyncMock) as mock_publish:
            mock_publish.side_effect = Exception("WebSocket error")
            
            from api.routes.bot import notify_task_update

            # Should not raise, just log warning
            await notify_task_update(
                task_id="task-123",
                notification_type="BOT_TASK_STARTED",
                title="Task Started",
                message="Test message"
            )


# ============================================
# VERIFY PREMIUM ACCESS TESTS
# ============================================

class TestVerifyPremiumAccess:
    """Tests for premium access verification."""
    
    @pytest.mark.asyncio
    async def test_verify_premium_access_success(self, mock_user, mock_license_info):
        """Test successful premium access verification."""
        with patch("api.routes.bot.LicenseService") as MockLicense:
            mock_service = MockLicense.return_value
            mock_service.get_license_by_email = AsyncMock(return_value=mock_license_info)
            
            with patch.object(MockLicense, "get_plan_features", return_value={"seller_bot": True}):
                from api.routes.bot import verify_premium_access
                result = await verify_premium_access(current_user=mock_user)
                assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_verify_premium_access_no_license(self, mock_user):
        """Test access denied when no license."""
        with patch("api.routes.bot.LicenseService") as MockLicense:
            mock_service = MockLicense.return_value
            mock_service.get_license_by_email = AsyncMock(return_value=None)
            
            from api.routes.bot import verify_premium_access
            
            with pytest.raises(HTTPException) as exc:
                await verify_premium_access(current_user=mock_user)
            
            assert exc.value.status_code == 402
            assert "Premium Bot" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_verify_premium_access_no_bot_feature(self, mock_user, mock_license_info):
        """Test access denied when plan doesn't include bot."""
        mock_license_info["plan"] = "basic"
        
        with patch("api.routes.bot.LicenseService") as MockLicense:
            mock_service = MockLicense.return_value
            mock_service.get_license_by_email = AsyncMock(return_value=mock_license_info)
            
            with patch.object(MockLicense, "get_plan_features", return_value={"seller_bot": False}):
                from api.routes.bot import verify_premium_access
                
                with pytest.raises(HTTPException) as exc:
                    await verify_premium_access(current_user=mock_user)
                
                assert exc.value.status_code == 402
                assert "Seu plano não inclui" in str(exc.value.detail)


# ============================================
# DEPENDENCY INJECTION TESTS
# ============================================

class TestDependencyInjection:
    """Tests for dependency injection functions."""
    
    def test_get_queue_manager_creates_instance(self):
        """Test queue manager is created on first call."""
        with patch("api.routes.bot._queue_manager", None):
            with patch("api.routes.bot.TaskQueueManager") as MockQueue:
                from api.routes.bot import get_queue_manager
                
                result = get_queue_manager()
                MockQueue.assert_called_once()
    
    def test_get_profile_manager_creates_instance(self):
        """Test profile manager is created on first call."""
        with patch("api.routes.bot._profile_manager", None):
            with patch("api.routes.bot.ProfileManager") as MockProfile:
                from api.routes.bot import get_profile_manager
                
                result = get_profile_manager()
                MockProfile.assert_called_once()


# ============================================
# TASK ENDPOINTS TESTS
# ============================================

class TestStartTask:
    """Tests for POST /tasks endpoint."""
    
    @pytest.mark.asyncio
    async def test_start_task_post_product(self, mock_user, mock_task):
        """Test starting a post_product task."""
        with patch("api.routes.bot.notify_task_update", new_callable=AsyncMock), \
             patch("api.routes.bot.record_task_created"), \
             patch("api.routes.bot.record_api_latency"):
            
            mock_queue = MagicMock()
            mock_queue.enqueue = AsyncMock(return_value=mock_task)
            
            from api.routes.bot import (StartTaskRequest, TaskPriority,
                                        start_task)
            
            request = StartTaskRequest(
                task_type="post_product",
                task_description="Test product post",
                task_data={"title": "Test Product"},
                priority=TaskPriority.NORMAL
            )
            
            result = await start_task(request=request, queue=mock_queue, user=mock_user)
            
            assert result.id == "task-123"
            assert result.task_type == "post_product"
    
    @pytest.mark.asyncio
    async def test_start_task_analytics(self, mock_user, mock_task):
        """Test starting an analytics task."""
        mock_task.task_type = "analytics"
        
        with patch("api.routes.bot.notify_task_update", new_callable=AsyncMock), \
             patch("api.routes.bot.record_task_created"), \
             patch("api.routes.bot.record_api_latency"):
            
            mock_queue = MagicMock()
            mock_queue.enqueue = AsyncMock(return_value=mock_task)
            
            from api.routes.bot import (StartTaskRequest, TaskPriority,
                                        start_task)
            
            request = StartTaskRequest(
                task_type="analytics",
                task_data={"action": "overview"},
                priority=TaskPriority.HIGH
            )
            
            result = await start_task(request=request, queue=mock_queue, user=mock_user)
            
            assert result.task_type == "analytics"


class TestBuildTaskDescription:
    """Tests for _build_task_description function."""
    
    def test_build_description_post_product_no_data(self):
        """Test post_product without task_data raises error."""
        from api.routes.bot import (StartTaskRequest, TaskPriority,
                                    _build_task_description)
        
        request = StartTaskRequest(
            task_type="post_product",
            task_data=None,
            priority=TaskPriority.NORMAL
        )
        
        with pytest.raises(HTTPException) as exc:
            _build_task_description(request)
        
        assert exc.value.status_code == 400
        assert "task_data é obrigatório" in str(exc.value.detail)
    
    def test_build_description_manage_orders_print_labels(self):
        """Test manage_orders with print_labels action."""
        with patch("api.routes.bot.ManageOrdersTask") as MockTask:
            MockTask.build_print_labels_prompt.return_value = "Print labels prompt"
            
            from api.routes.bot import (StartTaskRequest, TaskPriority,
                                        _build_task_description)
            
            request = StartTaskRequest(
                task_type="manage_orders",
                task_data={"action": "print_labels"},
                priority=TaskPriority.NORMAL
            )
            
            result = _build_task_description(request)
            MockTask.build_print_labels_prompt.assert_called_once()
    
    def test_build_description_manage_orders_process_returns(self):
        """Test manage_orders with process_returns action."""
        with patch("api.routes.bot.ManageOrdersTask") as MockTask:
            MockTask.build_process_returns_prompt.return_value = "Process returns prompt"
            
            from api.routes.bot import (StartTaskRequest, TaskPriority,
                                        _build_task_description)
            
            request = StartTaskRequest(
                task_type="manage_orders",
                task_data={"action": "process_returns"},
                priority=TaskPriority.NORMAL
            )
            
            result = _build_task_description(request)
            MockTask.build_process_returns_prompt.assert_called_once()
    
    def test_build_description_manage_orders_export(self):
        """Test manage_orders with export action."""
        with patch("api.routes.bot.ManageOrdersTask") as MockTask:
            MockTask.build_export_orders_prompt.return_value = "Export orders prompt"
            
            from api.routes.bot import (StartTaskRequest, TaskPriority,
                                        _build_task_description)
            
            request = StartTaskRequest(
                task_type="manage_orders",
                task_data={"action": "export_orders"},
                priority=TaskPriority.NORMAL
            )
            
            result = _build_task_description(request)
            MockTask.build_export_orders_prompt.assert_called_once()
    
    def test_build_description_reply_messages(self):
        """Test reply_messages task description."""
        with patch("api.routes.bot.ReplyMessagesTask") as MockTask:
            MockTask.build_reply_prompt.return_value = "Reply prompt"
            
            from api.routes.bot import (StartTaskRequest, TaskPriority,
                                        _build_task_description)
            
            request = StartTaskRequest(
                task_type="reply_messages",
                priority=TaskPriority.NORMAL
            )
            
            result = _build_task_description(request)
            MockTask.build_reply_prompt.assert_called_once()
    
    def test_build_description_analytics_top_products(self):
        """Test analytics with top_products action."""
        with patch("api.routes.bot.AnalyticsTask") as MockTask:
            MockTask.build_top_products_prompt.return_value = "Top products prompt"
            
            from api.routes.bot import (StartTaskRequest, TaskPriority,
                                        _build_task_description)
            
            request = StartTaskRequest(
                task_type="analytics",
                task_data={"action": "top_products"},
                priority=TaskPriority.NORMAL
            )
            
            result = _build_task_description(request)
            MockTask.build_top_products_prompt.assert_called_once()
    
    def test_build_description_analytics_orders_summary(self):
        """Test analytics with orders_summary action."""
        with patch("api.routes.bot.AnalyticsTask") as MockTask:
            MockTask.build_orders_summary_prompt.return_value = "Orders summary prompt"
            
            from api.routes.bot import (StartTaskRequest, TaskPriority,
                                        _build_task_description)
            
            request = StartTaskRequest(
                task_type="analytics",
                task_data={"action": "orders_summary"},
                priority=TaskPriority.NORMAL
            )
            
            result = _build_task_description(request)
            MockTask.build_orders_summary_prompt.assert_called_once()
    
    def test_build_description_unknown_task_type(self):
        """Test unknown task type raises error."""
        from api.routes.bot import (StartTaskRequest, TaskPriority,
                                    _build_task_description)
        
        request = StartTaskRequest(
            task_type="unknown_task",
            priority=TaskPriority.NORMAL
        )
        
        with pytest.raises(HTTPException) as exc:
            _build_task_description(request)
        
        assert exc.value.status_code == 400
        assert "Tipo de tarefa desconhecido" in str(exc.value.detail)


class TestGetTask:
    """Tests for GET /tasks/{task_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_task_found(self, mock_user, mock_task):
        """Test getting an existing task."""
        mock_queue = MagicMock()
        mock_queue.get_task = AsyncMock(return_value=mock_task)
        
        from api.routes.bot import get_task
        
        result = await get_task(task_id="task-123", queue=mock_queue, user=mock_user)
        
        assert result.id == "task-123"
        mock_queue.get_task.assert_called_once_with("task-123")
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, mock_user):
        """Test getting non-existent task."""
        mock_queue = MagicMock()
        mock_queue.get_task = AsyncMock(return_value=None)
        
        from api.routes.bot import get_task
        
        with pytest.raises(HTTPException) as exc:
            await get_task(task_id="nonexistent", queue=mock_queue, user=mock_user)
        
        assert exc.value.status_code == 404


class TestListTasks:
    """Tests for GET /tasks endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_tasks_success(self, mock_user, mock_task):
        """Test listing user tasks."""
        mock_queue = MagicMock()
        mock_queue.get_user_tasks = AsyncMock(return_value=[mock_task, mock_task])
        
        from api.routes.bot import list_tasks
        
        result = await list_tasks(queue=mock_queue, user=mock_user)
        
        assert len(result) == 2
        assert all(t.id == "task-123" for t in result)
    
    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, mock_user):
        """Test listing tasks when none exist."""
        mock_queue = MagicMock()
        mock_queue.get_user_tasks = AsyncMock(return_value=[])
        
        from api.routes.bot import list_tasks
        
        result = await list_tasks(queue=mock_queue, user=mock_user)
        
        assert len(result) == 0


class TestCancelTask:
    """Tests for DELETE /tasks/{task_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_cancel_task_success(self, mock_user):
        """Test canceling a task."""
        mock_queue = MagicMock()
        mock_queue.cancel = AsyncMock(return_value=True)
        
        from api.routes.bot import cancel_task
        
        result = await cancel_task(task_id="task-123", queue=mock_queue, user=mock_user)
        
        assert result["message"] == "Tarefa cancelada"
        assert result["task_id"] == "task-123"
    
    @pytest.mark.asyncio
    async def test_cancel_task_not_found(self, mock_user):
        """Test canceling non-existent task."""
        mock_queue = MagicMock()
        mock_queue.cancel = AsyncMock(return_value=False)
        
        from api.routes.bot import cancel_task
        
        with pytest.raises(HTTPException) as exc:
            await cancel_task(task_id="nonexistent", queue=mock_queue, user=mock_user)
        
        assert exc.value.status_code == 404


class TestGetStats:
    """Tests for GET /stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_stats_success(self, mock_user, mock_queue_stats):
        """Test getting queue statistics."""
        mock_queue = MagicMock()
        mock_queue.get_stats = AsyncMock(return_value=mock_queue_stats)
        
        from api.routes.bot import get_stats
        
        result = await get_stats(queue=mock_queue, user=mock_user)
        
        assert result.total_queued == 5
        assert result.total_running == 1
        assert result.total_completed == 10
        assert result.total_failed == 2
        assert "post_product" in result.by_task_type


# ============================================
# PROFILE ENDPOINTS TESTS
# ============================================

class TestCreateProfile:
    """Tests for POST /profiles endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_profile_success(self, mock_user, mock_profile):
        """Test creating a profile."""
        with patch("api.routes.bot.record_profile_operation"), \
             patch("api.routes.bot.record_api_latency"):
            
            mock_profiles = MagicMock()
            mock_profiles.create_profile.return_value = mock_profile
            mock_profiles.detect_system_chrome_profile.return_value = None
            
            from api.routes.bot import ProfileRequest, create_profile
            
            request = ProfileRequest(name="Test Profile", clone_from_system=False)
            
            result = await create_profile(request=request, profiles=mock_profiles, user=mock_user)
            
            assert result.name == "Test Profile"
    
    @pytest.mark.asyncio
    async def test_create_profile_with_clone(self, mock_user, mock_profile):
        """Test creating a profile cloned from system Chrome."""
        with patch("api.routes.bot.record_profile_operation"), \
             patch("api.routes.bot.record_api_latency"):
            
            mock_profiles = MagicMock()
            mock_profiles.create_profile.return_value = mock_profile
            mock_profiles.detect_system_chrome_profile.return_value = "/path/to/chrome/profile"
            
            from api.routes.bot import ProfileRequest, create_profile
            
            request = ProfileRequest(name="Cloned Profile", clone_from_system=True)
            
            result = await create_profile(request=request, profiles=mock_profiles, user=mock_user)
            
            assert result.id == "profile-123"
            mock_profiles.detect_system_chrome_profile.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_profile_clone_failed(self, mock_user):
        """Test creating profile when Chrome detection fails."""
        with patch("api.routes.bot.record_profile_operation"):
            mock_profiles = MagicMock()
            mock_profiles.detect_system_chrome_profile.return_value = None
            
            from api.routes.bot import ProfileRequest, create_profile
            
            request = ProfileRequest(name="Failed Clone", clone_from_system=True)
            
            with pytest.raises(HTTPException) as exc:
                await create_profile(request=request, profiles=mock_profiles, user=mock_user)
            
            assert exc.value.status_code == 400
            assert "Chrome" in str(exc.value.detail)


class TestListProfiles:
    """Tests for GET /profiles endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_profiles_success(self, mock_user, mock_profile):
        """Test listing user profiles."""
        with patch("api.routes.bot.record_profile_operation"), \
             patch("api.routes.bot.record_api_latency"):
            
            mock_profiles = MagicMock()
            mock_profiles.get_user_profiles.return_value = [mock_profile, mock_profile]
            
            from api.routes.bot import list_profiles
            
            result = await list_profiles(profiles=mock_profiles, user=mock_user)
            
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_list_profiles_empty(self, mock_user):
        """Test listing profiles when none exist."""
        with patch("api.routes.bot.record_profile_operation"), \
             patch("api.routes.bot.record_api_latency"):
            
            mock_profiles = MagicMock()
            mock_profiles.get_user_profiles.return_value = []
            
            from api.routes.bot import list_profiles
            
            result = await list_profiles(profiles=mock_profiles, user=mock_user)
            
            assert len(result) == 0


class TestDeleteProfile:
    """Tests for DELETE /profiles/{profile_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_profile_success(self, mock_user):
        """Test deleting a profile."""
        with patch("api.routes.bot.record_profile_operation"):
            mock_profiles = MagicMock()
            mock_profiles.delete_profile.return_value = True
            
            from api.routes.bot import delete_profile
            
            result = await delete_profile(
                profile_id="profile-123",
                profiles=mock_profiles,
                user=mock_user
            )
            
            assert result["message"] == "Perfil deletado"
    
    @pytest.mark.asyncio
    async def test_delete_profile_not_found(self, mock_user):
        """Test deleting non-existent profile."""
        with patch("api.routes.bot.record_profile_operation"):
            mock_profiles = MagicMock()
            mock_profiles.delete_profile.return_value = False
            
            from api.routes.bot import delete_profile
            
            with pytest.raises(HTTPException) as exc:
                await delete_profile(
                    profile_id="nonexistent",
                    profiles=mock_profiles,
                    user=mock_user
                )
            
            assert exc.value.status_code == 404


class TestVerifyProfileLogin:
    """Tests for POST /profiles/{profile_id}/verify endpoint."""
    
    @pytest.mark.asyncio
    async def test_verify_profile_logged_in(self, mock_user, mock_profile):
        """Test verifying logged-in profile."""
        mock_profiles = MagicMock()
        mock_profiles.get_profile.return_value = mock_profile
        mock_profiles.verify_login_status = AsyncMock(return_value=True)
        
        from api.routes.bot import verify_profile_login
        
        result = await verify_profile_login(
            profile_id="profile-123",
            profiles=mock_profiles,
            user=mock_user
        )
        
        assert result["is_logged_in"] is True
        assert "Logado" in result["message"]
    
    @pytest.mark.asyncio
    async def test_verify_profile_not_logged_in(self, mock_user, mock_profile):
        """Test verifying non-logged-in profile."""
        mock_profiles = MagicMock()
        mock_profiles.get_profile.return_value = mock_profile
        mock_profiles.verify_login_status = AsyncMock(return_value=False)
        
        from api.routes.bot import verify_profile_login
        
        result = await verify_profile_login(
            profile_id="profile-123",
            profiles=mock_profiles,
            user=mock_user
        )
        
        assert result["is_logged_in"] is False
        assert "Não logado" in result["message"]
    
    @pytest.mark.asyncio
    async def test_verify_profile_not_found(self, mock_user):
        """Test verifying non-existent profile."""
        mock_profiles = MagicMock()
        mock_profiles.get_profile.return_value = None
        
        from api.routes.bot import verify_profile_login
        
        with pytest.raises(HTTPException) as exc:
            await verify_profile_login(
                profile_id="nonexistent",
                profiles=mock_profiles,
                user=mock_user
            )
        
        assert exc.value.status_code == 404


# ============================================
# BOT CONTROL ENDPOINTS TESTS
# ============================================

class TestStartBot:
    """Tests for POST /start endpoint."""
    
    @pytest.mark.asyncio
    async def test_start_bot_success(self, mock_user):
        """Test starting the bot."""
        with patch("api.routes.bot.notify_task_update", new_callable=AsyncMock):
            mock_queue = MagicMock()
            mock_background = MagicMock()
            
            from api.routes.bot import start_bot
            
            result = await start_bot(
                background_tasks=mock_background,
                queue=mock_queue,
                user=mock_user
            )
            
            assert result["status"] == "running"
            mock_background.add_task.assert_called_once_with(mock_queue.start)


class TestStopBot:
    """Tests for POST /stop endpoint."""
    
    @pytest.mark.asyncio
    async def test_stop_bot_success(self, mock_user):
        """Test stopping the bot."""
        with patch("api.routes.bot.notify_task_update", new_callable=AsyncMock):
            mock_queue = MagicMock()
            mock_queue.stop = AsyncMock()
            
            from api.routes.bot import stop_bot
            
            result = await stop_bot(queue=mock_queue, user=mock_user)
            
            assert result["status"] == "stopped"
            mock_queue.stop.assert_called_once()


# ============================================
# REQUEST/RESPONSE MODEL TESTS
# ============================================

class TestRequestResponseModels:
    """Tests for Pydantic models."""
    
    def test_start_task_request_valid(self):
        """Test valid StartTaskRequest."""
        from api.routes.bot import StartTaskRequest, TaskPriority
        
        request = StartTaskRequest(
            task_type="post_product",
            task_description="Test description",
            task_data={"key": "value"},
            priority=TaskPriority.HIGH
        )
        
        assert request.task_type == "post_product"
        assert request.priority == TaskPriority.HIGH
    
    def test_start_task_request_defaults(self):
        """Test StartTaskRequest with defaults."""
        from api.routes.bot import StartTaskRequest, TaskPriority
        
        request = StartTaskRequest(task_type="analytics")
        
        assert request.task_description is None
        assert request.task_data is None
        assert request.priority == TaskPriority.NORMAL
    
    def test_profile_request_valid(self):
        """Test valid ProfileRequest."""
        from api.routes.bot import ProfileRequest
        
        request = ProfileRequest(name="Test Profile", clone_from_system=True)
        
        assert request.name == "Test Profile"
        assert request.clone_from_system is True
    
    def test_profile_request_defaults(self):
        """Test ProfileRequest with defaults."""
        from api.routes.bot import ProfileRequest
        
        request = ProfileRequest(name="Test Profile")
        
        assert request.clone_from_system is False
