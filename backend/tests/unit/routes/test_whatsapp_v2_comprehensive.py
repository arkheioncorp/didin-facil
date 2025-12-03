"""
Comprehensive tests for whatsapp_v2.py
Tests for WhatsApp Hub V2 routes.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError


# ============================================
# SCHEMA TESTS
# ============================================

class TestInstanceCreate:
    """Tests for InstanceCreate schema."""

    def test_valid_instance_name(self):
        from api.routes.whatsapp_v2 import InstanceCreate

        instance = InstanceCreate(
            instance_name="my-instance-123",
            webhook_url="https://example.com/webhook",
            auto_configure_webhook=True
        )
        assert instance.instance_name == "my-instance-123"

    def test_instance_name_pattern(self):
        from api.routes.whatsapp_v2 import InstanceCreate

        # Valid names
        InstanceCreate(instance_name="abc")
        InstanceCreate(instance_name="test-123")
        InstanceCreate(instance_name="my-instance")

    def test_instance_name_too_short(self):
        from api.routes.whatsapp_v2 import InstanceCreate

        with pytest.raises(ValidationError):
            InstanceCreate(instance_name="ab")

    def test_instance_name_too_long(self):
        from api.routes.whatsapp_v2 import InstanceCreate

        with pytest.raises(ValidationError):
            InstanceCreate(instance_name="a" * 51)

    def test_instance_default_auto_configure(self):
        from api.routes.whatsapp_v2 import InstanceCreate

        instance = InstanceCreate(instance_name="test-123")
        assert instance.auto_configure_webhook is True


class TestInstanceResponse:
    """Tests for InstanceResponse schema."""

    def test_full_response(self):
        from api.routes.whatsapp_v2 import InstanceResponse

        response = InstanceResponse(
            name="test-instance",
            state="connected",
            phone_connected="5511999999999",
            webhook_url="https://example.com/webhook",
            created_at=datetime.now(timezone.utc)
        )
        assert response.name == "test-instance"
        assert response.state == "connected"

    def test_minimal_response(self):
        from api.routes.whatsapp_v2 import InstanceResponse

        response = InstanceResponse(
            name="test",
            state="disconnected"
        )
        assert response.phone_connected is None
        assert response.webhook_url is None


class TestWebhookConfigRequest:
    """Tests for WebhookConfigRequest schema."""

    def test_with_url_only(self):
        from api.routes.whatsapp_v2 import WebhookConfigRequest

        config = WebhookConfigRequest(url="https://example.com/webhook")
        assert config.url == "https://example.com/webhook"
        assert config.events is None

    def test_with_events(self):
        from api.routes.whatsapp_v2 import WebhookConfigRequest

        config = WebhookConfigRequest(
            url="https://example.com/webhook",
            events=["messages.upsert", "connection.update"]
        )
        assert len(config.events) == 2


class TestSendTextRequest:
    """Tests for SendTextRequest schema."""

    def test_valid_request(self):
        from api.routes.whatsapp_v2 import SendTextRequest

        req = SendTextRequest(
            to="5511999999999",
            text="Hello, World!"
        )
        assert req.to == "5511999999999"
        assert req.text == "Hello, World!"
        assert req.delay_ms == 0

    def test_with_delay(self):
        from api.routes.whatsapp_v2 import SendTextRequest

        req = SendTextRequest(
            to="5511999999999",
            text="Hello",
            delay_ms=2000
        )
        assert req.delay_ms == 2000

    def test_max_delay(self):
        from api.routes.whatsapp_v2 import SendTextRequest

        req = SendTextRequest(
            to="5511999999999",
            text="Hello",
            delay_ms=5000
        )
        assert req.delay_ms == 5000

    def test_delay_over_max(self):
        from api.routes.whatsapp_v2 import SendTextRequest

        with pytest.raises(ValidationError):
            SendTextRequest(
                to="5511999999999",
                text="Hello",
                delay_ms=6000
            )

    def test_negative_delay(self):
        from api.routes.whatsapp_v2 import SendTextRequest

        with pytest.raises(ValidationError):
            SendTextRequest(
                to="5511999999999",
                text="Hello",
                delay_ms=-1
            )

    def test_empty_text(self):
        from api.routes.whatsapp_v2 import SendTextRequest

        with pytest.raises(ValidationError):
            SendTextRequest(
                to="5511999999999",
                text=""
            )

    def test_text_max_length(self):
        from api.routes.whatsapp_v2 import SendTextRequest

        # 4096 chars is valid
        req = SendTextRequest(
            to="5511999999999",
            text="A" * 4096
        )
        assert len(req.text) == 4096


class TestSendMediaRequest:
    """Tests for SendMediaRequest schema."""

    def test_valid_request(self):
        from api.routes.whatsapp_v2 import SendMediaRequest

        req = SendMediaRequest(
            to="5511999999999",
            media_url="https://example.com/image.jpg"
        )
        assert req.to == "5511999999999"
        assert req.caption is None

    def test_with_caption(self):
        from api.routes.whatsapp_v2 import SendMediaRequest

        req = SendMediaRequest(
            to="5511999999999",
            media_url="https://example.com/image.jpg",
            caption="My photo"
        )
        assert req.caption == "My photo"


class TestSendLocationRequest:
    """Tests for SendLocationRequest schema."""

    def test_valid_request(self):
        from api.routes.whatsapp_v2 import SendLocationRequest

        req = SendLocationRequest(
            to="5511999999999",
            latitude=-23.5505,
            longitude=-46.6333
        )
        assert req.latitude == -23.5505
        assert req.longitude == -46.6333

    def test_with_name_and_address(self):
        from api.routes.whatsapp_v2 import SendLocationRequest

        req = SendLocationRequest(
            to="5511999999999",
            latitude=-23.5505,
            longitude=-46.6333,
            name="Paulista Avenue",
            address="São Paulo, SP"
        )
        assert req.name == "Paulista Avenue"
        assert req.address == "São Paulo, SP"


class TestSendButtonsRequest:
    """Tests for SendButtonsRequest schema."""

    def test_valid_request(self):
        from api.routes.whatsapp_v2 import SendButtonsRequest

        req = SendButtonsRequest(
            to="5511999999999",
            title="Menu",
            description="Choose an option",
            buttons=[
                {"buttonId": "1", "buttonText": {"displayText": "Option 1"}}
            ]
        )
        assert req.title == "Menu"
        assert len(req.buttons) == 1


class TestSendListRequest:
    """Tests for SendListRequest schema."""

    def test_valid_request(self):
        from api.routes.whatsapp_v2 import SendListRequest

        req = SendListRequest(
            to="5511999999999",
            title="Products",
            description="Our products",
            button_text="View",
            sections=[
                {"title": "Category 1", "rows": []}
            ]
        )
        assert req.button_text == "View"


class TestMessageResponse:
    """Tests for MessageResponse schema."""

    def test_success_response(self):
        from api.routes.whatsapp_v2 import MessageResponse

        resp = MessageResponse(
            success=True,
            message_id="ABC123"
        )
        assert resp.success is True
        assert resp.message_id == "ABC123"

    def test_error_response(self):
        from api.routes.whatsapp_v2 import MessageResponse

        resp = MessageResponse(
            success=False,
            details={"error": "Connection failed"}
        )
        assert resp.success is False
        assert resp.details["error"] == "Connection failed"


class TestCheckNumberRequest:
    """Tests for CheckNumberRequest schema."""

    def test_valid_request(self):
        from api.routes.whatsapp_v2 import CheckNumberRequest

        req = CheckNumberRequest(phone="5511999999999")
        assert req.phone == "5511999999999"


class TestCheckNumberResponse:
    """Tests for CheckNumberResponse schema."""

    def test_exists_response(self):
        from api.routes.whatsapp_v2 import CheckNumberResponse

        resp = CheckNumberResponse(
            phone="5511999999999",
            exists=True,
            formatted="55 11 99999-9999"
        )
        assert resp.exists is True

    def test_not_exists_response(self):
        from api.routes.whatsapp_v2 import CheckNumberResponse

        resp = CheckNumberResponse(
            phone="5511999999999",
            exists=False
        )
        assert resp.exists is False
        assert resp.formatted is None


# ============================================
# ROUTER TESTS
# ============================================

class TestRouter:
    """Tests for router configuration."""

    def test_router_exists(self):
        from api.routes.whatsapp_v2 import router

        assert router is not None

    def test_router_prefix(self):
        from api.routes.whatsapp_v2 import router

        assert router.prefix == "/v2/whatsapp"

    def test_router_tags(self):
        from api.routes.whatsapp_v2 import router

        assert "WhatsApp Hub" in router.tags


# ============================================
# INSTANCE MANAGEMENT TESTS
# ============================================

class TestCreateInstance:
    """Tests for create_instance endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2.database")
    async def test_create_instance_success(self, mock_db, mock_get_hub):
        from api.routes.whatsapp_v2 import create_instance, InstanceCreate

        mock_hub = AsyncMock()
        mock_instance = MagicMock()
        mock_instance.name = "test-instance"
        mock_instance.state = MagicMock()
        mock_instance.state.value = "created"
        mock_instance.created_at = datetime.now(timezone.utc)
        mock_hub.create_instance = AsyncMock(return_value=mock_instance)
        mock_get_hub.return_value = mock_hub
        mock_db.execute = AsyncMock()

        data = InstanceCreate(instance_name="test-instance")
        current_user = {"id": str(uuid.uuid4())}

        result = await create_instance(data, current_user)

        assert result.name == "test-instance"
        mock_hub.create_instance.assert_called_once()

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    async def test_create_instance_error(self, mock_get_hub):
        from api.routes.whatsapp_v2 import create_instance, InstanceCreate
        from fastapi import HTTPException

        mock_hub = AsyncMock()
        mock_hub.create_instance = AsyncMock(side_effect=Exception("Failed"))
        mock_get_hub.return_value = mock_hub

        data = InstanceCreate(instance_name="test-instance")
        current_user = {"id": str(uuid.uuid4())}

        with pytest.raises(HTTPException) as exc_info:
            await create_instance(data, current_user)

        assert exc_info.value.status_code == 400


class TestListInstances:
    """Tests for list_instances endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2.database")
    async def test_list_instances_success(self, mock_db, mock_get_hub):
        from api.routes.whatsapp_v2 import list_instances

        mock_hub = AsyncMock()
        mock_instance = MagicMock()
        mock_instance.name = "test"
        mock_instance.state = MagicMock()
        mock_instance.state.value = "connected"
        mock_instance.phone_connected = "5511999999999"
        mock_hub.list_instances = AsyncMock(return_value=[mock_instance])
        mock_get_hub.return_value = mock_hub

        mock_db.fetch_all = AsyncMock(return_value=[MagicMock(name="test")])

        current_user = {"id": str(uuid.uuid4())}

        result = await list_instances(current_user)

        assert len(result) == 1
        assert result[0].name == "test"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    async def test_list_instances_error(self, mock_get_hub):
        from api.routes.whatsapp_v2 import list_instances
        from fastapi import HTTPException

        mock_hub = AsyncMock()
        mock_hub.list_instances = AsyncMock(side_effect=Exception("Error"))
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        with pytest.raises(HTTPException) as exc_info:
            await list_instances(current_user)

        assert exc_info.value.status_code == 500


class TestGetInstance:
    """Tests for get_instance endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2.database")
    async def test_get_instance_not_found(self, mock_db, mock_get_hub):
        from api.routes.whatsapp_v2 import get_instance
        from fastapi import HTTPException

        mock_db.fetch_one = AsyncMock(return_value=None)

        current_user = {"id": str(uuid.uuid4())}

        with pytest.raises(HTTPException) as exc_info:
            await get_instance("nonexistent", current_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2.database")
    async def test_get_instance_not_authorized(self, mock_db, mock_get_hub):
        from api.routes.whatsapp_v2 import get_instance
        from fastapi import HTTPException

        mock_db_instance = MagicMock()
        mock_db_instance.user_id = str(uuid.uuid4())  # Different user
        mock_db.fetch_one = AsyncMock(return_value=mock_db_instance)

        current_user = {"id": str(uuid.uuid4())}

        with pytest.raises(HTTPException) as exc_info:
            await get_instance("test-instance", current_user)

        assert exc_info.value.status_code == 403


# ============================================
# MESSAGING ROUTE TESTS
# ============================================

class TestSendTextMessage:
    """Tests for send_text_message endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._log_outgoing_message")
    async def test_send_text_success(self, mock_log, mock_get_hub):
        from api.routes.whatsapp_v2 import send_text_message, SendTextRequest

        mock_hub = AsyncMock()
        mock_hub.send_text = AsyncMock(return_value={
            "key": {"id": "MSG123"}
        })
        mock_get_hub.return_value = mock_hub

        data = SendTextRequest(to="5511999999999", text="Hello")
        current_user = {"id": str(uuid.uuid4())}

        result = await send_text_message(data, current_user)

        assert result.success is True
        assert result.message_id == "MSG123"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    async def test_send_text_error(self, mock_get_hub):
        from api.routes.whatsapp_v2 import send_text_message, SendTextRequest

        mock_hub = AsyncMock()
        mock_hub.send_text = AsyncMock(side_effect=Exception("Failed"))
        mock_get_hub.return_value = mock_hub

        data = SendTextRequest(to="5511999999999", text="Hello")
        current_user = {"id": str(uuid.uuid4())}

        result = await send_text_message(data, current_user)

        assert result.success is False
        assert "error" in result.details


class TestSendImage:
    """Tests for send_image endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._log_outgoing_message")
    async def test_send_image_success(self, mock_log, mock_get_hub):
        from api.routes.whatsapp_v2 import send_image, SendMediaRequest

        mock_hub = AsyncMock()
        mock_hub.send_image = AsyncMock(return_value={
            "key": {"id": "IMG123"}
        })
        mock_get_hub.return_value = mock_hub

        data = SendMediaRequest(
            to="5511999999999",
            media_url="https://example.com/image.jpg"
        )
        current_user = {"id": str(uuid.uuid4())}

        result = await send_image(data, current_user)

        assert result.success is True

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    async def test_send_image_error(self, mock_get_hub):
        from api.routes.whatsapp_v2 import send_image, SendMediaRequest

        mock_hub = AsyncMock()
        mock_hub.send_image = AsyncMock(side_effect=Exception("Failed"))
        mock_get_hub.return_value = mock_hub

        data = SendMediaRequest(
            to="5511999999999",
            media_url="https://example.com/image.jpg"
        )
        current_user = {"id": str(uuid.uuid4())}

        result = await send_image(data, current_user)

        assert result.success is False


class TestSendVideo:
    """Tests for send_video endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._log_outgoing_message")
    async def test_send_video_success(self, mock_log, mock_get_hub):
        from api.routes.whatsapp_v2 import send_video, SendMediaRequest

        mock_hub = AsyncMock()
        mock_hub.send_video = AsyncMock(return_value={
            "key": {"id": "VID123"}
        })
        mock_get_hub.return_value = mock_hub

        data = SendMediaRequest(
            to="5511999999999",
            media_url="https://example.com/video.mp4"
        )
        current_user = {"id": str(uuid.uuid4())}

        result = await send_video(data, current_user)

        assert result.success is True


class TestSendLocation:
    """Tests for send_location endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    async def test_send_location_success(self, mock_get_hub):
        from api.routes.whatsapp_v2 import send_location, SendLocationRequest

        mock_hub = AsyncMock()
        mock_hub.send_location = AsyncMock(return_value={
            "key": {"id": "LOC123"}
        })
        mock_get_hub.return_value = mock_hub

        data = SendLocationRequest(
            to="5511999999999",
            latitude=-23.5505,
            longitude=-46.6333
        )
        current_user = {"id": str(uuid.uuid4())}

        result = await send_location(data, current_user)

        assert result.success is True

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    async def test_send_location_error(self, mock_get_hub):
        from api.routes.whatsapp_v2 import send_location, SendLocationRequest

        mock_hub = AsyncMock()
        mock_hub.send_location = AsyncMock(side_effect=Exception("Failed"))
        mock_get_hub.return_value = mock_hub

        data = SendLocationRequest(
            to="5511999999999",
            latitude=-23.5505,
            longitude=-46.6333
        )
        current_user = {"id": str(uuid.uuid4())}

        result = await send_location(data, current_user)

        assert result.success is False


class TestSendAudio:
    """Tests for send_audio endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    async def test_send_audio_success(self, mock_get_hub):
        from api.routes.whatsapp_v2 import send_audio

        mock_hub = AsyncMock()
        mock_hub.send_audio = AsyncMock(return_value={
            "key": {"id": "AUD123"}
        })
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        result = await send_audio(
            to="5511999999999",
            audio_url="https://example.com/audio.mp3",
            as_voice=True,
            instance_name=None,
            current_user=current_user
        )

        assert result.success is True

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    async def test_send_audio_error(self, mock_get_hub):
        from api.routes.whatsapp_v2 import send_audio

        mock_hub = AsyncMock()
        mock_hub.send_audio = AsyncMock(side_effect=Exception("Failed"))
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        result = await send_audio(
            to="5511999999999",
            audio_url="https://example.com/audio.mp3",
            as_voice=True,
            instance_name=None,
            current_user=current_user
        )

        assert result.success is False


class TestSendDocument:
    """Tests for send_document endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    async def test_send_document_success(self, mock_get_hub):
        from api.routes.whatsapp_v2 import send_document

        mock_hub = AsyncMock()
        mock_hub.send_document = AsyncMock(return_value={
            "key": {"id": "DOC123"}
        })
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        result = await send_document(
            to="5511999999999",
            document_url="https://example.com/file.pdf",
            filename="document.pdf",
            caption="My document",
            instance_name=None,
            current_user=current_user
        )

        assert result.success is True

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    async def test_send_document_error(self, mock_get_hub):
        from api.routes.whatsapp_v2 import send_document

        mock_hub = AsyncMock()
        mock_hub.send_document = AsyncMock(side_effect=Exception("Failed"))
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        result = await send_document(
            to="5511999999999",
            document_url="https://example.com/file.pdf",
            filename="document.pdf",
            caption=None,
            instance_name=None,
            current_user=current_user
        )

        assert result.success is False


class TestSendButtons:
    """Tests for send_buttons endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    async def test_send_buttons_success(self, mock_get_hub):
        from api.routes.whatsapp_v2 import send_buttons, SendButtonsRequest

        mock_hub = AsyncMock()
        mock_hub.send_buttons = AsyncMock(return_value={
            "key": {"id": "BTN123"}
        })
        mock_get_hub.return_value = mock_hub

        data = SendButtonsRequest(
            to="5511999999999",
            title="Menu",
            description="Choose an option",
            buttons=[{"buttonId": "1", "buttonText": {"displayText": "Option 1"}}]
        )
        current_user = {"id": str(uuid.uuid4())}

        result = await send_buttons(data, current_user)

        assert result.success is True


# ============================================
# DELETE INSTANCE TESTS
# ============================================

class TestDeleteInstance:
    """Tests for delete_instance endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._verify_instance_access")
    @patch("api.routes.whatsapp_v2.database")
    async def test_delete_instance_success(self, mock_db, mock_verify, mock_get_hub):
        from api.routes.whatsapp_v2 import delete_instance

        mock_db_instance = MagicMock()
        mock_db_instance.id = uuid.uuid4()
        mock_verify.return_value = mock_db_instance

        mock_hub = AsyncMock()
        mock_hub.delete_instance = AsyncMock(return_value=True)
        mock_get_hub.return_value = mock_hub

        mock_db.execute = AsyncMock()

        current_user = {"id": str(uuid.uuid4())}

        result = await delete_instance("test-instance", current_user)

        assert result["success"] is True
        assert result["instance_name"] == "test-instance"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._verify_instance_access")
    async def test_delete_instance_error(self, mock_verify, mock_get_hub):
        from api.routes.whatsapp_v2 import delete_instance
        from fastapi import HTTPException

        mock_db_instance = MagicMock()
        mock_verify.return_value = mock_db_instance

        mock_hub = AsyncMock()
        mock_hub.delete_instance = AsyncMock(side_effect=Exception("Failed"))
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        with pytest.raises(HTTPException) as exc_info:
            await delete_instance("test-instance", current_user)

        assert exc_info.value.status_code == 400


class TestDisconnectInstance:
    """Tests for disconnect_instance endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._verify_instance_access")
    async def test_disconnect_instance_success(self, mock_verify, mock_get_hub):
        from api.routes.whatsapp_v2 import disconnect_instance

        mock_hub = AsyncMock()
        mock_hub.disconnect_instance = AsyncMock(return_value=True)
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        result = await disconnect_instance("test-instance", current_user)

        assert result["success"] is True

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._verify_instance_access")
    async def test_disconnect_instance_error(self, mock_verify, mock_get_hub):
        from api.routes.whatsapp_v2 import disconnect_instance
        from fastapi import HTTPException

        mock_hub = AsyncMock()
        mock_hub.disconnect_instance = AsyncMock(side_effect=Exception("Failed"))
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        with pytest.raises(HTTPException) as exc_info:
            await disconnect_instance("test-instance", current_user)

        assert exc_info.value.status_code == 400


# ============================================
# QR CODE TESTS
# ============================================

class TestGetQRCode:
    """Tests for get_qr_code endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._verify_instance_access")
    async def test_get_qr_code_success(self, mock_verify, mock_get_hub):
        from api.routes.whatsapp_v2 import get_qr_code

        mock_hub = AsyncMock()
        mock_hub.get_qr_code = AsyncMock(return_value="data:image/png;base64,...")
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        result = await get_qr_code("test-instance", current_user)

        assert result["instance_name"] == "test-instance"
        assert "qr_code" in result

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._verify_instance_access")
    async def test_get_qr_code_error(self, mock_verify, mock_get_hub):
        from api.routes.whatsapp_v2 import get_qr_code
        from fastapi import HTTPException

        mock_hub = AsyncMock()
        mock_hub.get_qr_code = AsyncMock(side_effect=Exception("Failed"))
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        with pytest.raises(HTTPException) as exc_info:
            await get_qr_code("test-instance", current_user)

        assert exc_info.value.status_code == 400


# ============================================
# WEBHOOK CONFIGURATION TESTS
# ============================================

class TestConfigureWebhook:
    """Tests for configure_webhook endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._verify_instance_access")
    @patch("api.routes.whatsapp_v2.database")
    async def test_configure_webhook_success(self, mock_db, mock_verify, mock_get_hub):
        from api.routes.whatsapp_v2 import configure_webhook, WebhookConfigRequest

        mock_hub = AsyncMock()
        mock_hub.configure_webhook = AsyncMock(return_value=True)
        mock_get_hub.return_value = mock_hub
        mock_db.execute = AsyncMock()

        data = WebhookConfigRequest(url="https://example.com/webhook")
        current_user = {"id": str(uuid.uuid4())}

        result = await configure_webhook("test-instance", data, current_user)

        assert result["success"] is True

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._verify_instance_access")
    async def test_configure_webhook_error(self, mock_verify, mock_get_hub):
        from api.routes.whatsapp_v2 import configure_webhook, WebhookConfigRequest
        from fastapi import HTTPException

        mock_hub = AsyncMock()
        mock_hub.configure_webhook = AsyncMock(side_effect=Exception("Failed"))
        mock_get_hub.return_value = mock_hub

        data = WebhookConfigRequest(url="https://example.com/webhook")
        current_user = {"id": str(uuid.uuid4())}

        with pytest.raises(HTTPException) as exc_info:
            await configure_webhook("test-instance", data, current_user)

        assert exc_info.value.status_code == 400


class TestGetWebhookConfig:
    """Tests for get_webhook_config endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._verify_instance_access")
    async def test_get_webhook_config_success(self, mock_verify, mock_get_hub):
        from api.routes.whatsapp_v2 import get_webhook_config

        mock_hub = AsyncMock()
        mock_hub.get_webhook_config = AsyncMock(return_value={
            "url": "https://example.com/webhook",
            "events": ["messages.upsert"]
        })
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        result = await get_webhook_config("test-instance", current_user)

        assert result["url"] == "https://example.com/webhook"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_v2.get_whatsapp_hub")
    @patch("api.routes.whatsapp_v2._verify_instance_access")
    async def test_get_webhook_config_error(self, mock_verify, mock_get_hub):
        from api.routes.whatsapp_v2 import get_webhook_config
        from fastapi import HTTPException

        mock_hub = AsyncMock()
        mock_hub.get_webhook_config = AsyncMock(side_effect=Exception("Failed"))
        mock_get_hub.return_value = mock_hub

        current_user = {"id": str(uuid.uuid4())}

        with pytest.raises(HTTPException) as exc_info:
            await get_webhook_config("test-instance", current_user)

        assert exc_info.value.status_code == 400
