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
