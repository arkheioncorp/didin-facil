"""
Tests for WhatsApp V2 Routes
Tests for the WhatsApp Hub integrated routes.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest


class TestWhatsAppV2Schemas:
    """Tests for WhatsApp V2 Pydantic schemas"""

    def test_instance_create_model(self):
        """Test InstanceCreate model"""
        from api.routes.whatsapp_v2 import InstanceCreate

        # Valid instance
        data = InstanceCreate(
            instance_name="test-instance",
            webhook_url="https://example.com/webhook",
            auto_configure_webhook=True
        )
        assert data.instance_name == "test-instance"
        assert data.webhook_url == "https://example.com/webhook"
        assert data.auto_configure_webhook is True

    def test_instance_create_minimal(self):
        """Test InstanceCreate with minimal data"""
        from api.routes.whatsapp_v2 import InstanceCreate
        
        data = InstanceCreate(instance_name="my-instance")
        assert data.instance_name == "my-instance"
        assert data.webhook_url is None
        assert data.auto_configure_webhook is True

    def test_instance_create_validation(self):
        """Test InstanceCreate validation"""
        from api.routes.whatsapp_v2 import InstanceCreate
        from pydantic import ValidationError

        # Too short
        with pytest.raises(ValidationError):
            InstanceCreate(instance_name="ab")
        
        # Invalid characters
        with pytest.raises(ValidationError):
            InstanceCreate(instance_name="Invalid Instance!")

    def test_instance_response_model(self):
        """Test InstanceResponse model"""
        from api.routes.whatsapp_v2 import InstanceResponse
        
        now = datetime.now(timezone.utc)
        data = InstanceResponse(
            name="test",
            state="connected",
            phone_connected="5511999999999",
            webhook_url="https://example.com/webhook",
            created_at=now
        )
        assert data.name == "test"
        assert data.state == "connected"
        assert data.phone_connected == "5511999999999"

    def test_webhook_config_request(self):
        """Test WebhookConfigRequest model"""
        from api.routes.whatsapp_v2 import WebhookConfigRequest
        
        data = WebhookConfigRequest(
            url="https://example.com/webhook",
            events=["messages.upsert", "connection.update"]
        )
        assert data.url == "https://example.com/webhook"
        assert len(data.events) == 2

    def test_send_text_request(self):
        """Test SendTextRequest model"""
        from api.routes.whatsapp_v2 import SendTextRequest
        
        data = SendTextRequest(
            to="5511999999999",
            text="Hello, World!",
            instance_name="my-instance",
            delay_ms=1000
        )
        assert data.to == "5511999999999"
        assert data.text == "Hello, World!"
        assert data.instance_name == "my-instance"
        assert data.delay_ms == 1000

    def test_send_text_request_minimal(self):
        """Test SendTextRequest with minimal data"""
        from api.routes.whatsapp_v2 import SendTextRequest
        
        data = SendTextRequest(
            to="5511999999999",
            text="Test"
        )
        assert data.delay_ms == 0
        assert data.instance_name is None

    def test_send_text_request_validation(self):
        """Test SendTextRequest validation"""
        from api.routes.whatsapp_v2 import SendTextRequest
        from pydantic import ValidationError

        # Empty text
        with pytest.raises(ValidationError):
            SendTextRequest(to="5511999999999", text="")
        
        # Delay too large
        with pytest.raises(ValidationError):
            SendTextRequest(to="5511999999999", text="Test", delay_ms=10000)

    def test_send_media_request(self):
        """Test SendMediaRequest model"""
        from api.routes.whatsapp_v2 import SendMediaRequest
        
        data = SendMediaRequest(
            to="5511999999999",
            media_url="https://example.com/image.jpg",
            caption="Check this out!"
        )
        assert data.to == "5511999999999"
        assert data.media_url == "https://example.com/image.jpg"
        assert data.caption == "Check this out!"

    def test_send_location_request(self):
        """Test SendLocationRequest model"""
        from api.routes.whatsapp_v2 import SendLocationRequest
        
        data = SendLocationRequest(
            to="5511999999999",
            latitude=-23.5505,
            longitude=-46.6333,
            name="São Paulo",
            address="Centro, São Paulo - SP"
        )
        assert data.latitude == -23.5505
        assert data.longitude == -46.6333
        assert data.name == "São Paulo"

    def test_send_buttons_request(self):
        """Test SendButtonsRequest model"""
        from api.routes.whatsapp_v2 import SendButtonsRequest
        
        data = SendButtonsRequest(
            to="5511999999999",
            title="Choose an option",
            description="Please select one",
            buttons=[
                {"buttonId": "1", "buttonText": {"displayText": "Option 1"}},
                {"buttonId": "2", "buttonText": {"displayText": "Option 2"}}
            ],
            footer="Thanks for using our service"
        )
        assert len(data.buttons) == 2
        assert data.footer == "Thanks for using our service"

    def test_send_list_request(self):
        """Test SendListRequest model"""
        from api.routes.whatsapp_v2 import SendListRequest
        
        data = SendListRequest(
            to="5511999999999",
            title="Menu",
            description="Select from list",
            button_text="View Options",
            sections=[
                {
                    "title": "Section 1",
                    "rows": [
                        {"rowId": "1", "title": "Item 1"}
                    ]
                }
            ]
        )
        assert data.button_text == "View Options"
        assert len(data.sections) == 1

    def test_message_response(self):
        """Test MessageResponse model"""
        from api.routes.whatsapp_v2 import MessageResponse
        
        data = MessageResponse(
            success=True,
            message_id="ABC123",
            details={"status": "sent"}
        )
        assert data.success is True
        assert data.message_id == "ABC123"

    def test_message_response_failure(self):
        """Test MessageResponse for failure"""
        from api.routes.whatsapp_v2 import MessageResponse
        
        data = MessageResponse(
            success=False,
            details={"error": "Connection failed"}
        )
        assert data.success is False
        assert data.message_id is None

    def test_check_number_request(self):
        """Test CheckNumberRequest model"""
        from api.routes.whatsapp_v2 import CheckNumberRequest
        
        data = CheckNumberRequest(
            phone="5511999999999",
            instance_name="test-instance"
        )
        assert data.phone == "5511999999999"

    def test_check_number_response(self):
        """Test CheckNumberResponse model"""
        from api.routes.whatsapp_v2 import CheckNumberResponse
        
        data = CheckNumberResponse(
            phone="5511999999999",
            exists=True,
            formatted="55 11 99999-9999"
        )
        assert data.exists is True
        assert data.formatted == "55 11 99999-9999"


class TestWhatsAppV2Router:
    """Tests for router configuration"""

    def test_router_exists(self):
        """Test that router is properly defined"""
        from api.routes.whatsapp_v2 import router
        assert router is not None
        assert router.prefix == "/v2/whatsapp"
        assert "WhatsApp Hub" in router.tags

    def test_router_routes_exist(self):
        """Test that all expected routes exist"""
        from api.routes.whatsapp_v2 import router

        routes = [r.path for r in router.routes]
        expected_patterns = [
            "instances",
            "instance_name",
            "qrcode",
            "disconnect",
            "webhook",
            "send",
        ]

        for pattern in expected_patterns:
            found = any(pattern in route for route in routes)
            assert found, f"Pattern '{pattern}' not found in routes"


class TestBulkMessageSchemas:
    """Tests for bulk message schemas"""

    def test_bulk_message_request(self):
        """Test bulk message request if exists"""
        try:
            from api.routes.whatsapp_v2 import BulkMessageRequest
            
            data = BulkMessageRequest(
                numbers=["5511999999999", "5521999999999"],
                text="Hello everyone!",
                instance_name="test"
            )
            assert len(data.numbers) == 2
        except ImportError:
            # Model may not exist
            pass

    def test_bulk_media_request(self):
        """Test bulk media request if exists"""
        try:
            from api.routes.whatsapp_v2 import BulkMediaRequest
            
            data = BulkMediaRequest(
                numbers=["5511999999999"],
                media_url="https://example.com/image.jpg"
            )
            assert len(data.numbers) == 1
        except ImportError:
            pass


class TestContactSchemas:
    """Tests for contact-related schemas"""

    def test_contact_info_model(self):
        """Test ContactInfo model if exists"""
        try:
            from api.routes.whatsapp_v2 import ContactInfo
            
            data = ContactInfo(
                jid="5511999999999@s.whatsapp.net",
                name="John Doe",
                phone="5511999999999"
            )
            assert data.name == "John Doe"
        except ImportError:
            pass

    def test_profile_picture_response(self):
        """Test ProfilePictureResponse if exists"""
        try:
            from api.routes.whatsapp_v2 import ProfilePictureResponse
            
            data = ProfilePictureResponse(
                url="https://pps.whatsapp.net/v/...",
                exists=True
            )
            assert data.exists is True
        except ImportError:
            pass


class TestGroupSchemas:
    """Tests for group-related schemas"""

    def test_group_info_model(self):
        """Test GroupInfo model if exists"""
        try:
            from api.routes.whatsapp_v2 import GroupInfo
            
            data = GroupInfo(
                id="123456789@g.us",
                subject="Test Group",
                owner="5511999999999@s.whatsapp.net",
                participants=[]
            )
            assert data.subject == "Test Group"
        except ImportError:
            pass

    def test_create_group_request(self):
        """Test CreateGroupRequest if exists"""
        try:
            from api.routes.whatsapp_v2 import CreateGroupRequest
            
            data = CreateGroupRequest(
                name="New Group",
                participants=["5511999999999"]
            )
            assert data.name == "New Group"
        except ImportError:
            pass


class TestMetricsSchemas:
    """Tests for metrics-related schemas"""

    def test_instance_metrics_model(self):
        """Test InstanceMetrics model if exists"""
        try:
            from api.routes.whatsapp_v2 import InstanceMetrics
            
            data = InstanceMetrics(
                messages_sent=100,
                messages_received=50,
                uptime_seconds=3600
            )
            assert data.messages_sent == 100
        except ImportError:
            pass


class TestImports:
    """Tests for proper imports"""

    def test_whatsapp_hub_imports(self):
        """Test that WhatsApp Hub dependencies are imported"""
        from api.routes.whatsapp_v2 import (ConnectionState, InstanceInfo,
                                            MessageType, WhatsAppHub,
                                            WhatsAppMessage, get_whatsapp_hub)
        assert WhatsAppHub is not None
        assert get_whatsapp_hub is not None

    def test_auth_import(self):
        """Test auth middleware import"""
        from api.routes.whatsapp_v2 import get_current_user
        assert get_current_user is not None

    def test_database_import(self):
        """Test database import"""
        from api.routes.whatsapp_v2 import database
        assert database is not None


class TestRouteHandlers:
    """Tests for route handler functions existence"""

    def test_create_instance_handler_exists(self):
        """Test create_instance handler exists"""
        from api.routes.whatsapp_v2 import create_instance
        assert callable(create_instance)

    def test_list_instances_handler_exists(self):
        """Test list_instances handler exists"""
        from api.routes.whatsapp_v2 import list_instances
        assert callable(list_instances)

    def test_get_instance_handler_exists(self):
        """Test get_instance handler exists"""
        from api.routes.whatsapp_v2 import get_instance
        assert callable(get_instance)

    def test_get_qr_code_handler_exists(self):
        """Test get_qr_code handler exists"""
        from api.routes.whatsapp_v2 import get_qr_code
        assert callable(get_qr_code)

    def test_delete_instance_handler_exists(self):
        """Test delete_instance handler exists"""
        from api.routes.whatsapp_v2 import delete_instance
        assert callable(delete_instance)

    def test_disconnect_instance_handler_exists(self):
        """Test disconnect_instance handler exists"""
        from api.routes.whatsapp_v2 import disconnect_instance
        assert callable(disconnect_instance)

    def test_configure_webhook_handler_exists(self):
        """Test configure_webhook handler exists"""
        from api.routes.whatsapp_v2 import configure_webhook
        assert callable(configure_webhook)

    def test_get_webhook_config_handler_exists(self):
        """Test get_webhook_config handler exists"""
        from api.routes.whatsapp_v2 import get_webhook_config
        assert callable(get_webhook_config)

    def test_send_text_message_handler_exists(self):
        """Test send_text_message handler exists"""
        from api.routes.whatsapp_v2 import send_text_message
        assert callable(send_text_message)

    def test_send_image_handler_exists(self):
        """Test send_image handler exists"""
        from api.routes.whatsapp_v2 import send_image
        assert callable(send_image)


class TestConnectionStateEnum:
    """Tests for ConnectionState enum"""

    def test_connection_state_values(self):
        """Test ConnectionState enum values"""
        from api.routes.whatsapp_v2 import ConnectionState

        # Check that enum exists and has expected values
        assert hasattr(ConnectionState, 'DISCONNECTED') or hasattr(ConnectionState, 'disconnected')

    def test_message_type_enum(self):
        """Test MessageType enum values"""
        from api.routes.whatsapp_v2 import MessageType

        # Check that enum exists
        assert MessageType is not None


class TestWhatsAppV2EndpointsWithMocks:
    """Tests for WhatsApp V2 endpoints with proper mocking"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user dict"""
        return {
            "id": str(uuid4()),
            "email": "test@example.com"
        }

    @pytest.fixture
    def mock_hub(self):
        """Create a mock WhatsApp Hub"""
        from unittest.mock import AsyncMock, MagicMock
        hub = MagicMock()
        hub.create_instance = AsyncMock()
        hub.list_instances = AsyncMock()
        hub.get_instance_status = AsyncMock()
        hub.get_qr_code = AsyncMock()
        hub.delete_instance = AsyncMock()
        hub.disconnect_instance = AsyncMock()
        hub.configure_webhook = AsyncMock()
        hub.get_webhook_config = AsyncMock()
        hub.send_text = AsyncMock()
        hub.send_image = AsyncMock()
        hub.send_video = AsyncMock()
        hub.send_audio = AsyncMock()
        hub.send_document = AsyncMock()
        hub.send_location = AsyncMock()
        hub.send_buttons = AsyncMock()
        hub.send_list = AsyncMock()
        hub.check_number = AsyncMock()
        hub.get_profile_picture = AsyncMock()
        hub.process_webhook = AsyncMock()
        hub.parse_webhook = MagicMock()
        hub.parse_connection_update = MagicMock()
        hub._format_phone = MagicMock(return_value="5511999999999")
        return hub

    @pytest.fixture
    def mock_database(self):
        """Create a mock database"""
        from unittest.mock import AsyncMock, MagicMock
        db = MagicMock()
        db.execute = AsyncMock()
        db.fetch_one = AsyncMock()
        db.fetch_all = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_create_instance_success(self, mock_user, mock_hub, mock_database):
        """Test successful instance creation"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import InstanceCreate, create_instance
        
        mock_instance = MagicMock()
        mock_instance.name = "test-instance"
        mock_instance.state = MagicMock()
        mock_instance.state.value = "created"
        mock_instance.created_at = datetime.now(timezone.utc)
        
        mock_hub.create_instance.return_value = mock_instance
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database', mock_database):
            
            data = InstanceCreate(instance_name="test-instance")
            result = await create_instance(data, mock_user)
            
            assert result.name == "test-instance"
            assert result.state == "created"

    @pytest.mark.asyncio
    async def test_create_instance_error(self, mock_user, mock_hub, mock_database):
        """Test instance creation error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import InstanceCreate, create_instance
        from fastapi import HTTPException
        
        mock_hub.create_instance.side_effect = Exception("Creation failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database', mock_database):
            
            data = InstanceCreate(instance_name="test-instance")
            
            with pytest.raises(HTTPException) as exc_info:
                await create_instance(data, mock_user)
            
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_list_instances_success(self, mock_user, mock_hub, mock_database):
        """Test listing instances"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import list_instances
        
        mock_inst = MagicMock()
        mock_inst.name = "my-instance"
        mock_inst.state = MagicMock()
        mock_inst.state.value = "connected"
        mock_inst.phone_connected = "5511999999999"
        
        mock_hub.list_instances.return_value = [mock_inst]
        
        mock_db_record = MagicMock()
        mock_db_record.name = "my-instance"
        mock_database.fetch_all.return_value = [mock_db_record]
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database', mock_database):
            
            result = await list_instances(mock_user)
            
            assert len(result) == 1
            assert result[0].name == "my-instance"

    @pytest.mark.asyncio
    async def test_list_instances_error(self, mock_user, mock_hub, mock_database):
        """Test listing instances with error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import list_instances
        from fastapi import HTTPException
        
        mock_hub.list_instances.side_effect = Exception("List failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            with pytest.raises(HTTPException) as exc_info:
                await list_instances(mock_user)
            
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_instance_success(self, mock_user, mock_hub, mock_database):
        """Test getting a specific instance"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import get_instance
        
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = mock_user["id"]
        mock_db_inst.webhook_url = "https://example.com/webhook"
        mock_database.fetch_one.return_value = mock_db_inst
        
        mock_inst = MagicMock()
        mock_inst.name = "test-instance"
        mock_inst.state = MagicMock()
        mock_inst.state.value = "connected"
        mock_inst.phone_connected = "5511999999999"
        mock_hub.get_instance_status.return_value = mock_inst
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database', mock_database):
            
            result = await get_instance("test-instance", mock_user)
            
            assert result.name == "test-instance"
            assert result.state == "connected"

    @pytest.mark.asyncio
    async def test_get_instance_not_found(self, mock_user, mock_hub, mock_database):
        """Test getting non-existent instance"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import get_instance
        from fastapi import HTTPException
        
        mock_database.fetch_one.return_value = None
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database', mock_database):
            
            with pytest.raises(HTTPException) as exc_info:
                await get_instance("non-existent", mock_user)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_instance_forbidden(self, mock_user, mock_hub, mock_database):
        """Test accessing another user's instance"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import get_instance
        from fastapi import HTTPException
        
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = "different-user-id"
        mock_database.fetch_one.return_value = mock_db_inst
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database', mock_database):
            
            with pytest.raises(HTTPException) as exc_info:
                await get_instance("test-instance", mock_user)
            
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_send_text_message_success(self, mock_user, mock_hub):
        """Test sending text message successfully"""
        from unittest.mock import AsyncMock, patch

        from api.routes.whatsapp_v2 import SendTextRequest, send_text_message
        
        mock_hub.send_text.return_value = {"key": {"id": "msg-123"}}
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._log_outgoing_message', new_callable=AsyncMock):
            
            data = SendTextRequest(to="5511999999999", text="Hello!")
            result = await send_text_message(data, mock_user)
            
            assert result.success is True
            assert result.message_id == "msg-123"

    @pytest.mark.asyncio
    async def test_send_text_message_error(self, mock_user, mock_hub):
        """Test sending text message with error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import SendTextRequest, send_text_message
        
        mock_hub.send_text.side_effect = Exception("Send failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            data = SendTextRequest(to="5511999999999", text="Hello!")
            result = await send_text_message(data, mock_user)
            
            assert result.success is False

    @pytest.mark.asyncio
    async def test_send_image_success(self, mock_user, mock_hub):
        """Test sending image successfully"""
        from unittest.mock import AsyncMock, patch

        from api.routes.whatsapp_v2 import SendMediaRequest, send_image
        
        mock_hub.send_image.return_value = {"key": {"id": "msg-456"}}
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._log_outgoing_message', new_callable=AsyncMock):
            
            data = SendMediaRequest(
                to="5511999999999",
                media_url="https://example.com/image.jpg",
                caption="Check this out!"
            )
            result = await send_image(data, mock_user)
            
            assert result.success is True
            assert result.message_id == "msg-456"

    @pytest.mark.asyncio
    async def test_send_image_error(self, mock_user, mock_hub):
        """Test sending image with error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import SendMediaRequest, send_image
        
        mock_hub.send_image.side_effect = Exception("Upload failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            data = SendMediaRequest(
                to="5511999999999",
                media_url="https://example.com/image.jpg"
            )
            result = await send_image(data, mock_user)
            
            assert result.success is False

    @pytest.mark.asyncio
    async def test_send_video_success(self, mock_user, mock_hub):
        """Test sending video successfully"""
        from unittest.mock import AsyncMock, patch

        from api.routes.whatsapp_v2 import SendMediaRequest, send_video
        
        mock_hub.send_video.return_value = {"key": {"id": "msg-789"}}
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._log_outgoing_message', new_callable=AsyncMock):
            
            data = SendMediaRequest(
                to="5511999999999",
                media_url="https://example.com/video.mp4"
            )
            result = await send_video(data, mock_user)
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_send_video_error(self, mock_user, mock_hub):
        """Test sending video with error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import SendMediaRequest, send_video
        
        mock_hub.send_video.side_effect = Exception("Video upload failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            data = SendMediaRequest(
                to="5511999999999",
                media_url="https://example.com/video.mp4"
            )
            result = await send_video(data, mock_user)
            
            assert result.success is False

    @pytest.mark.asyncio
    async def test_send_audio_success(self, mock_user, mock_hub):
        """Test sending audio successfully"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import send_audio
        
        mock_hub.send_audio.return_value = {"key": {"id": "msg-audio"}}
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            result = await send_audio(
                to="5511999999999",
                audio_url="https://example.com/audio.mp3",
                as_voice=True,
                current_user=mock_user
            )
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_send_audio_error(self, mock_user, mock_hub):
        """Test sending audio with error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import send_audio
        
        mock_hub.send_audio.side_effect = Exception("Audio failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            result = await send_audio(
                to="5511999999999",
                audio_url="https://example.com/audio.mp3",
                current_user=mock_user
            )
            
            assert result.success is False

    @pytest.mark.asyncio
    async def test_send_document_success(self, mock_user, mock_hub):
        """Test sending document successfully"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import send_document
        
        mock_hub.send_document.return_value = {"key": {"id": "msg-doc"}}
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            result = await send_document(
                to="5511999999999",
                document_url="https://example.com/doc.pdf",
                filename="document.pdf",
                caption="Check this document",
                current_user=mock_user
            )
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_send_document_error(self, mock_user, mock_hub):
        """Test sending document with error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import send_document
        
        mock_hub.send_document.side_effect = Exception("Document failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            result = await send_document(
                to="5511999999999",
                document_url="https://example.com/doc.pdf",
                filename="doc.pdf",
                current_user=mock_user
            )
            
            assert result.success is False

    @pytest.mark.asyncio
    async def test_send_location_success(self, mock_user, mock_hub):
        """Test sending location successfully"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import SendLocationRequest, send_location
        
        mock_hub.send_location.return_value = {"key": {"id": "msg-loc"}}
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            data = SendLocationRequest(
                to="5511999999999",
                latitude=-23.5505,
                longitude=-46.6333,
                name="São Paulo",
                address="Centro"
            )
            result = await send_location(data, mock_user)
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_send_location_error(self, mock_user, mock_hub):
        """Test sending location with error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import SendLocationRequest, send_location
        
        mock_hub.send_location.side_effect = Exception("Location failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            data = SendLocationRequest(
                to="5511999999999",
                latitude=-23.5505,
                longitude=-46.6333
            )
            result = await send_location(data, mock_user)
            
            assert result.success is False

    @pytest.mark.asyncio
    async def test_send_buttons_success(self, mock_user, mock_hub):
        """Test sending buttons successfully"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import SendButtonsRequest, send_buttons
        
        mock_hub.send_buttons.return_value = {"key": {"id": "msg-btns"}}
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            data = SendButtonsRequest(
                to="5511999999999",
                title="Choose",
                description="Select one",
                buttons=[{"buttonId": "1", "buttonText": {"displayText": "Yes"}}]
            )
            result = await send_buttons(data, mock_user)
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_send_buttons_error(self, mock_user, mock_hub):
        """Test sending buttons with error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import SendButtonsRequest, send_buttons
        
        mock_hub.send_buttons.side_effect = Exception("Buttons failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            data = SendButtonsRequest(
                to="5511999999999",
                title="Choose",
                description="Select one",
                buttons=[{"buttonId": "1", "buttonText": {"displayText": "Yes"}}]
            )
            result = await send_buttons(data, mock_user)
            
            assert result.success is False

    @pytest.mark.asyncio
    async def test_send_list_success(self, mock_user, mock_hub):
        """Test sending list successfully"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import SendListRequest, send_list
        
        mock_hub.send_list.return_value = {"key": {"id": "msg-list"}}
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            data = SendListRequest(
                to="5511999999999",
                title="Menu",
                description="Select item",
                button_text="View",
                sections=[{"title": "Items", "rows": []}]
            )
            result = await send_list(data, mock_user)
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_send_list_error(self, mock_user, mock_hub):
        """Test sending list with error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import SendListRequest, send_list
        
        mock_hub.send_list.side_effect = Exception("List failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            data = SendListRequest(
                to="5511999999999",
                title="Menu",
                description="Select",
                button_text="View",
                sections=[]
            )
            result = await send_list(data, mock_user)
            
            assert result.success is False

    @pytest.mark.asyncio
    async def test_check_number_success(self, mock_user, mock_hub):
        """Test checking number successfully"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import CheckNumberRequest, check_number
        
        mock_hub.check_number.return_value = True
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            data = CheckNumberRequest(phone="5511999999999")
            result = await check_number(data, mock_user)
            
            assert result.exists is True

    @pytest.mark.asyncio
    async def test_check_number_error(self, mock_user, mock_hub):
        """Test checking number with error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import CheckNumberRequest, check_number
        from fastapi import HTTPException
        
        mock_hub.check_number.side_effect = Exception("Check failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            data = CheckNumberRequest(phone="5511999999999")
            
            with pytest.raises(HTTPException) as exc_info:
                await check_number(data, mock_user)
            
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_profile_picture_success(self, mock_user, mock_hub):
        """Test getting profile picture successfully"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import get_profile_picture
        
        mock_hub.get_profile_picture.return_value = "https://example.com/pic.jpg"
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            result = await get_profile_picture("5511999999999", current_user=mock_user)
            
            assert result["profile_picture_url"] == "https://example.com/pic.jpg"

    @pytest.mark.asyncio
    async def test_get_profile_picture_error(self, mock_user, mock_hub):
        """Test getting profile picture with error"""
        from unittest.mock import patch

        from api.routes.whatsapp_v2 import get_profile_picture
        from fastapi import HTTPException
        
        mock_hub.get_profile_picture.side_effect = Exception("Profile failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            
            with pytest.raises(HTTPException) as exc_info:
                await get_profile_picture("5511999999999", current_user=mock_user)
            
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_instance_success(self, mock_user, mock_hub, mock_database):
        """Test deleting instance successfully"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import delete_instance
        
        mock_db_inst = MagicMock()
        mock_db_inst.id = str(uuid4())
        mock_db_inst.user_id = mock_user["id"]
        
        mock_database.fetch_one.return_value = mock_db_inst
        mock_hub.delete_instance.return_value = True
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database', mock_database), \
             patch('api.routes.whatsapp_v2._verify_instance_access', return_value=mock_db_inst):
            
            result = await delete_instance("test-instance", mock_user)
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_instance_error(self, mock_user, mock_hub, mock_database):
        """Test deleting instance with error"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import delete_instance
        from fastapi import HTTPException
        
        mock_db_inst = MagicMock()
        mock_db_inst.id = str(uuid4())
        mock_db_inst.user_id = mock_user["id"]
        
        mock_hub.delete_instance.side_effect = Exception("Delete failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database', mock_database), \
             patch('api.routes.whatsapp_v2._verify_instance_access', return_value=mock_db_inst):
            
            with pytest.raises(HTTPException) as exc_info:
                await delete_instance("test-instance", mock_user)
            
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_disconnect_instance_success(self, mock_user, mock_hub, mock_database):
        """Test disconnecting instance successfully"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import disconnect_instance
        
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = mock_user["id"]
        
        mock_hub.disconnect_instance.return_value = True
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', return_value=mock_db_inst):
            
            result = await disconnect_instance("test-instance", mock_user)
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_disconnect_instance_error(self, mock_user, mock_hub, mock_database):
        """Test disconnecting instance with error"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import disconnect_instance
        from fastapi import HTTPException
        
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = mock_user["id"]
        
        mock_hub.disconnect_instance.side_effect = Exception("Disconnect failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', return_value=mock_db_inst):
            
            with pytest.raises(HTTPException) as exc_info:
                await disconnect_instance("test-instance", mock_user)
            
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_configure_webhook_success(self, mock_user, mock_hub, mock_database):
        """Test configuring webhook successfully"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import (WebhookConfigRequest,
                                            configure_webhook)
        
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = mock_user["id"]
        
        mock_hub.configure_webhook.return_value = True
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database', mock_database), \
             patch('api.routes.whatsapp_v2._verify_instance_access', return_value=mock_db_inst):
            
            data = WebhookConfigRequest(url="https://example.com/webhook")
            result = await configure_webhook("test-instance", data, mock_user)
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_configure_webhook_error(self, mock_user, mock_hub, mock_database):
        """Test configuring webhook with error"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import (WebhookConfigRequest,
                                            configure_webhook)
        from fastapi import HTTPException
        
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = mock_user["id"]
        
        mock_hub.configure_webhook.side_effect = Exception("Config failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', return_value=mock_db_inst):
            
            data = WebhookConfigRequest(url="https://example.com/webhook")
            
            with pytest.raises(HTTPException) as exc_info:
                await configure_webhook("test-instance", data, mock_user)
            
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_webhook_config_success(self, mock_user, mock_hub, mock_database):
        """Test getting webhook config successfully"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import get_webhook_config
        
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = mock_user["id"]
        
        mock_hub.get_webhook_config.return_value = {"url": "https://example.com/webhook"}
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', return_value=mock_db_inst):
            
            result = await get_webhook_config("test-instance", mock_user)
            
            assert result["url"] == "https://example.com/webhook"

    @pytest.mark.asyncio
    async def test_get_webhook_config_error(self, mock_user, mock_hub, mock_database):
        """Test getting webhook config with error"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import get_webhook_config
        from fastapi import HTTPException
        
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = mock_user["id"]
        
        mock_hub.get_webhook_config.side_effect = Exception("Config failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', return_value=mock_db_inst):
            
            with pytest.raises(HTTPException) as exc_info:
                await get_webhook_config("test-instance", mock_user)
            
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_qr_code_success(self, mock_user, mock_hub, mock_database):
        """Test getting QR code successfully"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import get_qr_code
        
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = mock_user["id"]
        
        mock_hub.get_qr_code.return_value = "base64_qr_code"
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', return_value=mock_db_inst):
            
            result = await get_qr_code("test-instance", mock_user)
            
            assert result["qr_code"] == "base64_qr_code"

    @pytest.mark.asyncio
    async def test_get_qr_code_error(self, mock_user, mock_hub, mock_database):
        """Test getting QR code with error"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import get_qr_code
        from fastapi import HTTPException
        
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = mock_user["id"]
        
        mock_hub.get_qr_code.side_effect = Exception("QR failed")
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', return_value=mock_db_inst):
            
            with pytest.raises(HTTPException) as exc_info:
                await get_qr_code("test-instance", mock_user)
            
            assert exc_info.value.status_code == 400


class TestWebhookHandler:
    """Tests for webhook handler"""

    @pytest.mark.asyncio
    async def test_webhook_handler_success(self):
        """Test webhook handler success"""
        from unittest.mock import AsyncMock, MagicMock, patch

        from api.routes.whatsapp_v2 import webhook_handler
        
        mock_request = MagicMock()
        mock_request.json = AsyncMock(return_value={
            "event": "connection.update",
            "instance": "test-instance"
        })
        
        mock_hub = MagicMock()
        mock_hub.process_webhook = AsyncMock(return_value={"status": "ok"})
        mock_hub.parse_webhook = MagicMock(return_value=None)
        mock_hub.parse_connection_update = MagicMock(return_value=None)
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            result = await webhook_handler(mock_request)
            assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_webhook_handler_error(self):
        """Test webhook handler error"""
        from unittest.mock import AsyncMock, MagicMock, patch

        from api.routes.whatsapp_v2 import webhook_handler
        
        mock_request = MagicMock()
        mock_request.json = AsyncMock(side_effect=Exception("Parse error"))
        
        result = await webhook_handler(mock_request)
        assert result["status"] == "error"


class TestHelperFunctions:
    """Tests for helper functions"""

    @pytest.mark.asyncio
    async def test_verify_instance_access_not_found(self):
        """Test _verify_instance_access with non-existent instance"""
        from unittest.mock import AsyncMock, patch

        from api.routes.whatsapp_v2 import _verify_instance_access
        from fastapi import HTTPException
        
        mock_db = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        with patch('api.routes.whatsapp_v2.database', mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await _verify_instance_access("non-existent", {"id": "user-123"})
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_verify_instance_access_forbidden(self):
        """Test _verify_instance_access with wrong user"""
        from unittest.mock import AsyncMock, MagicMock, patch

        from api.routes.whatsapp_v2 import _verify_instance_access
        from fastapi import HTTPException
        
        mock_db = AsyncMock()
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = "other-user"
        mock_db.fetch_one = AsyncMock(return_value=mock_db_inst)
        
        with patch('api.routes.whatsapp_v2.database', mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await _verify_instance_access("test", {"id": "user-123"})
            
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_verify_instance_access_success(self):
        """Test _verify_instance_access success"""
        from unittest.mock import AsyncMock, MagicMock, patch

        from api.routes.whatsapp_v2 import _verify_instance_access
        
        mock_db = AsyncMock()
        mock_db_inst = MagicMock()
        mock_db_inst.user_id = "user-123"
        mock_db.fetch_one = AsyncMock(return_value=mock_db_inst)
        
        with patch('api.routes.whatsapp_v2.database', mock_db):
            result = await _verify_instance_access("test", {"id": "user-123"})
            assert result == mock_db_inst

    @pytest.mark.asyncio
    async def test_log_outgoing_message_no_instance(self):
        """Test _log_outgoing_message with no instance"""
        from unittest.mock import AsyncMock, patch

        from api.routes.whatsapp_v2 import _log_outgoing_message
        
        mock_db = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        with patch('api.routes.whatsapp_v2.database', mock_db):
            # Should not raise
            await _log_outgoing_message("instance", "to", "content", "text")

    @pytest.mark.asyncio
    async def test_save_incoming_message_no_instance(self):
        """Test _save_incoming_message with no instance"""
        from unittest.mock import AsyncMock, MagicMock, patch

        from api.routes.whatsapp_v2 import _save_incoming_message
        
        mock_db = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        mock_message = MagicMock()
        
        with patch('api.routes.whatsapp_v2.database', mock_db):
            # Should not raise
            await _save_incoming_message("instance", mock_message)

    @pytest.mark.asyncio
    async def test_forward_to_seller_bot_import_error(self):
        """Test _forward_to_seller_bot with import error"""
        from unittest.mock import MagicMock, patch

        from api.routes.whatsapp_v2 import _forward_to_seller_bot
        
        mock_message = MagicMock()
        mock_hub = MagicMock()
        
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch.dict('sys.modules', {'modules.chatbot.whatsapp_adapter': None}):
            # Should not raise - handles import error
            await _forward_to_seller_bot("instance", mock_message)
