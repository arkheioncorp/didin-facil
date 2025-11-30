"""
Testes para api/routes/bot.py

Endpoints do Seller Bot que requerem licença Premium.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


class TestVerifyPremiumAccess:
    """Testes para verify_premium_access dependency"""
    
    @pytest.mark.asyncio
    async def test_verify_premium_access_no_license(self):
        """Deve retornar 402 quando usuário não tem licença"""
        from api.routes.bot import verify_premium_access
        
        mock_user = {"email": "user@test.com"}
        
        with patch("api.routes.bot.LicenseService") as MockLicense:
            mock_service = MagicMock()
            mock_service.get_license_by_email = AsyncMock(return_value=None)
            MockLicense.return_value = mock_service
            
            with pytest.raises(HTTPException) as exc:
                await verify_premium_access(mock_user)
            
            assert exc.value.status_code == 402
            assert "Premium Bot" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_verify_premium_access_wrong_plan(self):
        """Deve retornar 402 quando plano não inclui bot"""
        from api.routes.bot import verify_premium_access
        
        mock_user = {"email": "user@test.com"}
        
        with patch("api.routes.bot.LicenseService") as MockLicense:
            mock_service = MagicMock()
            mock_service.get_license_by_email = AsyncMock(return_value={
                "plan": "basic",
                "email": "user@test.com"
            })
            MockLicense.return_value = mock_service
            # Plano basic não tem seller_bot
            MockLicense.get_plan_features = MagicMock(return_value={
                "seller_bot": False
            })
            
            with pytest.raises(HTTPException) as exc:
                await verify_premium_access(mock_user)
            
            assert exc.value.status_code == 402
            assert "Seller Bot" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_verify_premium_access_success(self):
        """Deve retornar user quando tem acesso Premium"""
        from api.routes.bot import verify_premium_access
        
        mock_user = {"email": "premium@test.com", "id": "user-123"}
        
        with patch("api.routes.bot.LicenseService") as MockLicense:
            mock_service = MagicMock()
            mock_service.get_license_by_email = AsyncMock(return_value={
                "plan": "premium_bot",
                "email": "premium@test.com"
            })
            MockLicense.return_value = mock_service
            MockLicense.get_plan_features = MagicMock(return_value={
                "seller_bot": True
            })
            
            result = await verify_premium_access(mock_user)
            
            assert result == mock_user


class TestDependencies:
    """Testes para dependencies get_queue_manager e get_profile_manager"""
    
    def test_get_queue_manager_creates_singleton(self):
        """Deve criar singleton do TaskQueueManager"""
        import api.routes.bot as bot_module
        
        # Reset singleton
        bot_module._queue_manager = None
        
        with patch("api.routes.bot.TaskQueueManager") as MockQueue:
            mock_queue = MagicMock()
            MockQueue.return_value = mock_queue
            
            result1 = bot_module.get_queue_manager()
            result2 = bot_module.get_queue_manager()
            
            # Deve criar apenas uma vez
            assert MockQueue.call_count == 1
            assert result1 == result2
        
        # Reset depois do teste
        bot_module._queue_manager = None
    
    def test_get_profile_manager_creates_singleton(self):
        """Deve criar singleton do ProfileManager"""
        import api.routes.bot as bot_module
        
        # Reset singleton
        bot_module._profile_manager = None
        
        with patch("api.routes.bot.ProfileManager") as MockProfile:
            mock_profile = MagicMock()
            MockProfile.return_value = mock_profile
            
            result1 = bot_module.get_profile_manager()
            result2 = bot_module.get_profile_manager()
            
            # Deve criar apenas uma vez
            assert MockProfile.call_count == 1
            assert result1 == result2
        
        # Reset depois do teste
        bot_module._profile_manager = None


class TestBuildTaskDescription:
    """Testes para _build_task_description helper"""
    
    def test_build_post_product_no_data(self):
        """Deve lançar erro se post_product sem task_data"""
        from api.routes.bot import _build_task_description, StartTaskRequest
        
        request = StartTaskRequest(task_type="post_product")
        
        with pytest.raises(HTTPException) as exc:
            _build_task_description(request)
        
        assert exc.value.status_code == 400
        assert "task_data" in str(exc.value.detail)
    
    def test_build_post_product_with_data(self):
        """Deve construir prompt de post_product"""
        from api.routes.bot import _build_task_description, StartTaskRequest
        
        with patch("api.routes.bot.PostProductTask") as MockTask:
            MockTask.build_prompt.return_value = "Post product prompt"
            
            request = StartTaskRequest(
                task_type="post_product",
                task_data={
                    "title": "Product",
                    "description": "Desc",
                    "price": 100.0,
                    "category": "Electronics",
                    "images": ["img.jpg"]
                }
            )
            
            result = _build_task_description(request)
            
            assert result == "Post product prompt"
    
    def test_build_manage_orders_print_labels(self):
        """Deve construir prompt de print_labels"""
        from api.routes.bot import _build_task_description, StartTaskRequest
        
        with patch("api.routes.bot.ManageOrdersTask") as MockTask:
            MockTask.build_print_labels_prompt.return_value = "Print labels prompt"
            
            request = StartTaskRequest(
                task_type="manage_orders",
                task_data={"action": "print_labels"}
            )
            
            result = _build_task_description(request)
            
            assert result == "Print labels prompt"
    
    def test_build_manage_orders_process_returns(self):
        """Deve construir prompt de process_returns"""
        from api.routes.bot import _build_task_description, StartTaskRequest
        
        with patch("api.routes.bot.ManageOrdersTask") as MockTask:
            MockTask.build_process_returns_prompt.return_value = "Process returns"
            
            request = StartTaskRequest(
                task_type="manage_orders",
                task_data={"action": "process_returns"}
            )
            
            result = _build_task_description(request)
            
            assert result == "Process returns"
    
    def test_build_manage_orders_default(self):
        """Deve construir prompt de export_orders por default"""
        from api.routes.bot import _build_task_description, StartTaskRequest
        
        with patch("api.routes.bot.ManageOrdersTask") as MockTask:
            MockTask.build_export_orders_prompt.return_value = "Export orders"
            
            request = StartTaskRequest(
                task_type="manage_orders",
                task_data={"action": "export"}
            )
            
            result = _build_task_description(request)
            
            assert result == "Export orders"
    
    def test_build_reply_messages(self):
        """Deve construir prompt de reply_messages"""
        from api.routes.bot import _build_task_description, StartTaskRequest
        
        with patch("api.routes.bot.ReplyMessagesTask") as MockTask:
            MockTask.build_reply_prompt.return_value = "Reply prompt"
            
            request = StartTaskRequest(task_type="reply_messages")
            
            result = _build_task_description(request)
            
            assert result == "Reply prompt"
    
    def test_build_analytics_top_products(self):
        """Deve construir prompt de top_products"""
        from api.routes.bot import _build_task_description, StartTaskRequest
        
        with patch("api.routes.bot.AnalyticsTask") as MockTask:
            MockTask.build_top_products_prompt.return_value = "Top products"
            
            request = StartTaskRequest(
                task_type="analytics",
                task_data={"action": "top_products"}
            )
            
            result = _build_task_description(request)
            
            assert result == "Top products"
    
    def test_build_analytics_orders_summary(self):
        """Deve construir prompt de orders_summary"""
        from api.routes.bot import _build_task_description, StartTaskRequest
        
        with patch("api.routes.bot.AnalyticsTask") as MockTask:
            MockTask.build_orders_summary_prompt.return_value = "Orders summary"
            
            request = StartTaskRequest(
                task_type="analytics",
                task_data={"action": "orders_summary"}
            )
            
            result = _build_task_description(request)
            
            assert result == "Orders summary"
    
    def test_build_analytics_default(self):
        """Deve construir prompt de overview por default"""
        from api.routes.bot import _build_task_description, StartTaskRequest
        
        with patch("api.routes.bot.AnalyticsTask") as MockTask:
            MockTask.build_extract_overview_prompt.return_value = "Overview"
            
            request = StartTaskRequest(task_type="analytics")
            
            result = _build_task_description(request)
            
            assert result == "Overview"
    
    def test_build_unknown_task_type(self):
        """Deve lançar erro para tipo desconhecido"""
        from api.routes.bot import _build_task_description, StartTaskRequest
        
        request = StartTaskRequest(task_type="unknown")
        
        with pytest.raises(HTTPException) as exc:
            _build_task_description(request)
        
        assert exc.value.status_code == 400
        assert "desconhecido" in str(exc.value.detail)


class TestTaskEndpoints:
    """Testes para endpoints de tarefas"""
    
    @pytest.mark.asyncio
    async def test_start_task_success(self):
        """Deve iniciar tarefa com sucesso"""
        from api.routes.bot import start_task, StartTaskRequest
        from seller_bot.queue.models import TaskState
        
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.task_type = "reply_messages"
        mock_task.state = TaskState.QUEUED
        mock_task.created_at = datetime.now(timezone.utc)
        mock_task.screenshots = []
        mock_task.logs = []
        
        mock_queue = MagicMock()
        mock_queue.enqueue = AsyncMock(return_value=mock_task)
        
        mock_user = {"email": "user@test.com", "id": "user-123"}
        
        request = StartTaskRequest(
            task_type="reply_messages",
            task_description="Test task"
        )
        
        result = await start_task(request, mock_queue, mock_user)
        
        assert result.id == "task-123"
        assert result.task_type == "reply_messages"
    
    @pytest.mark.asyncio
    async def test_get_task_success(self):
        """Deve obter tarefa por ID"""
        from api.routes.bot import get_task
        from seller_bot.queue.models import TaskState
        
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.task_type = "analytics"
        mock_task.state = TaskState.COMPLETED
        mock_task.created_at = datetime.now(timezone.utc)
        mock_task.started_at = datetime.now(timezone.utc)
        mock_task.completed_at = datetime.now(timezone.utc)
        mock_task.error_message = None
        mock_task.screenshots = ["screen.png"]
        mock_task.logs = ["Log entry"]
        
        mock_queue = MagicMock()
        mock_queue.get_task = AsyncMock(return_value=mock_task)
        
        mock_user = {"email": "user@test.com"}
        
        result = await get_task("task-123", mock_queue, mock_user)
        
        assert result.id == "task-123"
        assert result.screenshots == ["screen.png"]
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self):
        """Deve retornar 404 se tarefa não existe"""
        from api.routes.bot import get_task
        
        mock_queue = MagicMock()
        mock_queue.get_task = AsyncMock(return_value=None)
        
        mock_user = {"email": "user@test.com"}
        
        with pytest.raises(HTTPException) as exc:
            await get_task("invalid-id", mock_queue, mock_user)
        
        assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_tasks_success(self):
        """Deve listar tarefas do usuário"""
        from api.routes.bot import list_tasks
        from seller_bot.queue.models import TaskState
        
        mock_task1 = MagicMock()
        mock_task1.id = "task-1"
        mock_task1.task_type = "analytics"
        mock_task1.state = TaskState.COMPLETED
        mock_task1.created_at = datetime.now(timezone.utc)
        mock_task1.started_at = None
        mock_task1.completed_at = None
        mock_task1.error_message = None
        mock_task1.screenshots = []
        mock_task1.logs = []
        
        mock_task2 = MagicMock()
        mock_task2.id = "task-2"
        mock_task2.task_type = "reply_messages"
        mock_task2.state = TaskState.RUNNING
        mock_task2.created_at = datetime.now(timezone.utc)
        mock_task2.started_at = datetime.now(timezone.utc)
        mock_task2.completed_at = None
        mock_task2.error_message = None
        mock_task2.screenshots = []
        mock_task2.logs = []
        
        mock_queue = MagicMock()
        mock_queue.get_user_tasks = AsyncMock(return_value=[mock_task1, mock_task2])
        
        mock_user = {"email": "user@test.com", "id": "user-123"}
        
        result = await list_tasks(mock_queue, mock_user)
        
        assert len(result) == 2
        assert result[0].id == "task-1"
        assert result[1].id == "task-2"
    
    @pytest.mark.asyncio
    async def test_cancel_task_success(self):
        """Deve cancelar tarefa com sucesso"""
        from api.routes.bot import cancel_task
        
        mock_queue = MagicMock()
        mock_queue.cancel = AsyncMock(return_value=True)
        
        mock_user = {"email": "user@test.com"}
        
        result = await cancel_task("task-123", mock_queue, mock_user)
        
        assert result["message"] == "Tarefa cancelada"
        assert result["task_id"] == "task-123"
    
    @pytest.mark.asyncio
    async def test_cancel_task_not_found(self):
        """Deve retornar 404 se tarefa não existe"""
        from api.routes.bot import cancel_task
        
        mock_queue = MagicMock()
        mock_queue.cancel = AsyncMock(return_value=False)
        
        mock_user = {"email": "user@test.com"}
        
        with pytest.raises(HTTPException) as exc:
            await cancel_task("invalid-id", mock_queue, mock_user)
        
        assert exc.value.status_code == 404


class TestStatsEndpoint:
    """Testes para endpoint de estatísticas"""
    
    @pytest.mark.asyncio
    async def test_get_stats_success(self):
        """Deve obter estatísticas da fila"""
        from api.routes.bot import get_stats
        
        mock_stats = MagicMock()
        mock_stats.total_queued = 10
        mock_stats.total_running = 2
        mock_stats.total_completed = 100
        mock_stats.total_failed = 5
        mock_stats.by_task_type = {"post_product": 50, "analytics": 30}
        
        mock_queue = MagicMock()
        mock_queue.get_stats = AsyncMock(return_value=mock_stats)
        
        mock_user = {"email": "user@test.com"}
        
        result = await get_stats(mock_queue, mock_user)
        
        assert result.total_queued == 10
        assert result.total_running == 2
        assert result.total_completed == 100


class TestProfileEndpoints:
    """Testes para endpoints de perfis"""
    
    @pytest.mark.asyncio
    async def test_create_profile_success(self):
        """Deve criar perfil com sucesso"""
        from api.routes.bot import create_profile, ProfileRequest
        
        mock_profile = MagicMock()
        mock_profile.id = "profile-123"
        mock_profile.name = "Test Profile"
        mock_profile.is_logged_in = False
        mock_profile.last_used_at = None
        mock_profile.created_at = datetime.now(timezone.utc)
        
        mock_profiles = MagicMock()
        mock_profiles.detect_system_chrome_profile.return_value = None
        mock_profiles.create_profile.return_value = mock_profile
        
        mock_user = {"email": "user@test.com", "id": "user-123"}
        
        request = ProfileRequest(name="Test Profile", clone_from_system=False)
        
        result = await create_profile(request, mock_profiles, mock_user)
        
        assert result.id == "profile-123"
        assert result.name == "Test Profile"
    
    @pytest.mark.asyncio
    async def test_create_profile_with_clone(self):
        """Deve criar perfil clonando do sistema"""
        from api.routes.bot import create_profile, ProfileRequest
        
        mock_profile = MagicMock()
        mock_profile.id = "profile-123"
        mock_profile.name = "Cloned Profile"
        mock_profile.is_logged_in = True
        mock_profile.last_used_at = None
        mock_profile.created_at = datetime.now(timezone.utc)
        
        mock_profiles = MagicMock()
        mock_profiles.detect_system_chrome_profile.return_value = "/path/to/chrome"
        mock_profiles.create_profile.return_value = mock_profile
        
        mock_user = {"email": "user@test.com", "id": "user-123"}
        
        request = ProfileRequest(name="Cloned Profile", clone_from_system=True)
        
        result = await create_profile(request, mock_profiles, mock_user)
        
        assert result.is_logged_in
        mock_profiles.create_profile.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_profile_clone_not_found(self):
        """Deve retornar 400 se clone_from_system mas não encontra Chrome"""
        from api.routes.bot import create_profile, ProfileRequest
        
        mock_profiles = MagicMock()
        mock_profiles.detect_system_chrome_profile.return_value = None
        
        mock_user = {"email": "user@test.com", "id": "user-123"}
        
        request = ProfileRequest(name="Test Profile", clone_from_system=True)
        
        with pytest.raises(HTTPException) as exc:
            await create_profile(request, mock_profiles, mock_user)
        
        assert exc.value.status_code == 400
        assert "Chrome" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_list_profiles_success(self):
        """Deve listar perfis do usuário"""
        from api.routes.bot import list_profiles
        
        mock_profile1 = MagicMock()
        mock_profile1.id = "profile-1"
        mock_profile1.name = "Profile 1"
        mock_profile1.is_logged_in = True
        mock_profile1.last_used_at = datetime.now(timezone.utc)
        mock_profile1.created_at = datetime.now(timezone.utc)
        
        mock_profile2 = MagicMock()
        mock_profile2.id = "profile-2"
        mock_profile2.name = "Profile 2"
        mock_profile2.is_logged_in = False
        mock_profile2.last_used_at = None
        mock_profile2.created_at = datetime.now(timezone.utc)
        
        mock_profiles = MagicMock()
        mock_profiles.get_user_profiles.return_value = [mock_profile1, mock_profile2]
        
        mock_user = {"email": "user@test.com", "id": "user-123"}
        
        result = await list_profiles(mock_profiles, mock_user)
        
        assert len(result) == 2
        assert result[0].name == "Profile 1"
    
    @pytest.mark.asyncio
    async def test_delete_profile_success(self):
        """Deve deletar perfil com sucesso"""
        from api.routes.bot import delete_profile
        
        mock_profiles = MagicMock()
        mock_profiles.delete_profile.return_value = True
        
        mock_user = {"email": "user@test.com"}
        
        result = await delete_profile("profile-123", mock_profiles, mock_user)
        
        assert result["message"] == "Perfil deletado"
        assert result["profile_id"] == "profile-123"
    
    @pytest.mark.asyncio
    async def test_delete_profile_not_found(self):
        """Deve retornar 404 se perfil não existe"""
        from api.routes.bot import delete_profile
        
        mock_profiles = MagicMock()
        mock_profiles.delete_profile.return_value = False
        
        mock_user = {"email": "user@test.com"}
        
        with pytest.raises(HTTPException) as exc:
            await delete_profile("invalid-id", mock_profiles, mock_user)
        
        assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_verify_profile_login_success(self):
        """Deve verificar login do perfil"""
        from api.routes.bot import verify_profile_login
        
        mock_profile = MagicMock()
        mock_profile.id = "profile-123"
        
        mock_profiles = MagicMock()
        mock_profiles.get_profile.return_value = mock_profile
        mock_profiles.verify_login_status = AsyncMock(return_value=True)
        
        mock_user = {"email": "user@test.com"}
        
        result = await verify_profile_login("profile-123", mock_profiles, mock_user)
        
        assert result["is_logged_in"]
        assert "Logado" in result["message"]
    
    @pytest.mark.asyncio
    async def test_verify_profile_login_not_logged(self):
        """Deve retornar not logged quando usuário não está logado"""
        from api.routes.bot import verify_profile_login
        
        mock_profile = MagicMock()
        mock_profile.id = "profile-123"
        
        mock_profiles = MagicMock()
        mock_profiles.get_profile.return_value = mock_profile
        mock_profiles.verify_login_status = AsyncMock(return_value=False)
        
        mock_user = {"email": "user@test.com"}
        
        result = await verify_profile_login("profile-123", mock_profiles, mock_user)
        
        assert not result["is_logged_in"]
        assert "Não logado" in result["message"]
    
    @pytest.mark.asyncio
    async def test_verify_profile_not_found(self):
        """Deve retornar 404 se perfil não existe"""
        from api.routes.bot import verify_profile_login
        
        mock_profiles = MagicMock()
        mock_profiles.get_profile.return_value = None
        
        mock_user = {"email": "user@test.com"}
        
        with pytest.raises(HTTPException) as exc:
            await verify_profile_login("invalid-id", mock_profiles, mock_user)
        
        assert exc.value.status_code == 404


class TestBotControlEndpoints:
    """Testes para endpoints de controle do bot"""
    
    @pytest.mark.asyncio
    async def test_start_bot_success(self):
        """Deve iniciar bot com sucesso"""
        from api.routes.bot import start_bot
        
        mock_queue = MagicMock()
        mock_queue.start = AsyncMock()
        
        mock_background_tasks = MagicMock()
        
        mock_user = {"email": "user@test.com"}
        
        result = await start_bot(mock_background_tasks, mock_queue, mock_user)
        
        assert result["message"] == "Bot iniciado"
        assert result["status"] == "running"
        mock_background_tasks.add_task.assert_called_once_with(mock_queue.start)
    
    @pytest.mark.asyncio
    async def test_stop_bot_success(self):
        """Deve parar bot com sucesso"""
        from api.routes.bot import stop_bot
        
        mock_queue = MagicMock()
        mock_queue.stop = AsyncMock()
        
        mock_user = {"email": "user@test.com"}
        
        result = await stop_bot(mock_queue, mock_user)
        
        assert result["message"] == "Bot parado"
        assert result["status"] == "stopped"
        mock_queue.stop.assert_awaited_once()


class TestModels:
    """Testes para modelos Pydantic"""
    
    def test_start_task_request_defaults(self):
        """Deve criar StartTaskRequest com defaults"""
        from api.routes.bot import StartTaskRequest
        
        request = StartTaskRequest(task_type="analytics")
        
        assert request.task_type == "analytics"
        assert request.task_description is None
        assert request.task_data is None
    
    def test_task_response_model(self):
        """Deve criar TaskResponse válido"""
        from api.routes.bot import TaskResponse
        from seller_bot.queue.models import TaskState
        
        response = TaskResponse(
            id="task-123",
            task_type="post_product",
            state=TaskState.QUEUED,
            created_at=datetime.now(timezone.utc)
        )
        
        assert response.id == "task-123"
        assert response.state == TaskState.QUEUED
    
    def test_profile_request_model(self):
        """Deve criar ProfileRequest válido"""
        from api.routes.bot import ProfileRequest
        
        request = ProfileRequest(
            name="Test Profile",
            clone_from_system=True
        )
        
        assert request.name == "Test Profile"
        assert request.clone_from_system
    
    def test_profile_response_model(self):
        """Deve criar ProfileResponse válido"""
        from api.routes.bot import ProfileResponse
        
        response = ProfileResponse(
            id="profile-123",
            name="Test Profile",
            is_logged_in=True,
            created_at=datetime.now(timezone.utc)
        )
        
        assert response.id == "profile-123"
        assert response.is_logged_in
    
    def test_queue_stats_response_model(self):
        """Deve criar QueueStatsResponse válido"""
        from api.routes.bot import QueueStatsResponse
        
        response = QueueStatsResponse(
            total_queued=10,
            total_running=2,
            total_completed=100,
            total_failed=5,
            by_task_type={"post_product": 50}
        )
        
        assert response.total_queued == 10
        assert response.by_task_type["post_product"] == 50
