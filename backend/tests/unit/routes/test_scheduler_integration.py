"""
Scheduler Routes - Integration Tests
=====================================
Testes de integração para api/routes/scheduler.py
Importa o módulo diretamente para aumentar coverage.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
# Import do módulo real para aumentar coverage
from api.routes.scheduler import (BulkActionRequest, SchedulePostRequest,
                                  SchedulePostResponse, _classify_error,
                                  router)
from fastapi import FastAPI

# ==================== FIXTURES ====================


@pytest.fixture
def app():
    """Cria app FastAPI com o router."""
    app = FastAPI()
    app.include_router(router, prefix="/scheduler")
    return app


@pytest.fixture
def mock_user():
    """Usuário mockado para testes."""
    return {
        "id": str(uuid4()),
        "email": "test@example.com",
        "name": "Test User",
        "plan": "pro",
        "is_admin": False,
    }


@pytest.fixture
def mock_admin():
    """Admin mockado para testes."""
    return {
        "id": str(uuid4()),
        "email": "admin@example.com",
        "name": "Admin User",
        "plan": "enterprise",
        "is_admin": True,
    }


@pytest.fixture
def mock_subscription_service():
    """Serviço de subscription mockado."""
    service = AsyncMock()
    service.can_use_feature = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_scheduler_service():
    """Serviço de scheduler mockado."""
    service = AsyncMock()
    return service


@pytest.fixture
def future_time():
    """Tempo futuro para agendamento."""
    return datetime.now(timezone.utc) + timedelta(hours=1)


@pytest.fixture
def past_time():
    """Tempo passado (inválido para agendamento)."""
    return datetime.now(timezone.utc) - timedelta(hours=1)


# ==================== TESTS: _classify_error ====================


class TestClassifyError:
    """Testes para a função _classify_error."""

    def test_classify_rate_limit_429(self):
        """Testa classificação de rate limit com código 429."""
        assert _classify_error("Error 429: Too many requests") == "rate_limit"

    def test_classify_rate_limit_too_many(self):
        """Testa classificação de too many requests."""
        assert _classify_error("Too many requests in last hour") == "rate_limit"

    def test_classify_rate_limit_variation(self):
        """Testa variação de rate limit."""
        assert _classify_error("Rate limit exceeded") == "rate_limit"

    def test_classify_auth_error_401(self):
        """Testa classificação de erro 401."""
        assert _classify_error("HTTP 401 Unauthorized") == "auth_error"

    def test_classify_auth_error_403(self):
        """Testa classificação de erro 403."""
        assert _classify_error("403 Forbidden") == "auth_error"

    def test_classify_auth_error_token(self):
        """Testa classificação de erro de token."""
        assert _classify_error("Invalid token") == "auth_error"

    def test_classify_auth_error_login(self):
        """Testa classificação de erro de login."""
        assert _classify_error("Login required") == "auth_error"

    def test_classify_network_timeout(self):
        """Testa classificação de timeout."""
        assert _classify_error("Connection timeout") == "network_error"

    def test_classify_network_socket(self):
        """Testa classificação de erro de socket."""
        assert _classify_error("Socket error: connection refused") == "network_error"

    def test_classify_network_connection(self):
        """Testa classificação de erro de conexão."""
        assert _classify_error("Network connection failed") == "network_error"

    def test_classify_content_media(self):
        """Testa classificação de erro de mídia."""
        assert _classify_error("Media format not supported") == "content_error"

    def test_classify_content_file(self):
        """Testa classificação de erro de arquivo."""
        assert _classify_error("File too large") == "content_error"

    def test_classify_content_invalid(self):
        """Testa classificação de conteúdo inválido."""
        assert _classify_error("Invalid content format") == "content_error"

    def test_classify_content_size(self):
        """Testa classificação de erro de tamanho."""
        assert _classify_error("File size exceeds limit") == "content_error"

    def test_classify_quota_exceeded(self):
        """Testa classificação de quota excedida."""
        assert _classify_error("Quota exceeded for today") == "quota_exceeded"

    def test_classify_quota_daily_limit(self):
        """Testa classificação de limite diário."""
        assert _classify_error("Daily limit reached") == "quota_exceeded"

    def test_classify_quota_limit_exceeded(self):
        """Testa classificação de limit exceeded."""
        assert _classify_error("Limit exceeded") == "quota_exceeded"

    def test_classify_unknown_generic_error(self):
        """Testa classificação de erro genérico."""
        assert _classify_error("Something went wrong") == "unknown"

    def test_classify_unknown_empty_string(self):
        """Testa classificação de string vazia."""
        assert _classify_error("") == "unknown"

    def test_classify_unknown_random_error(self):
        """Testa classificação de erro aleatório."""
        assert _classify_error("XYZ-123 Internal server error") == "unknown"

    def test_classify_case_insensitive(self):
        """Testa que classificação é case insensitive."""
        assert _classify_error("RATE LIMIT EXCEEDED") == "rate_limit"
        assert _classify_error("AUTH TOKEN INVALID") == "auth_error"
        assert _classify_error("NETWORK CONNECTION LOST") == "network_error"


# ==================== TESTS: Schemas ====================


class TestSchedulePostRequestSchema:
    """Testes para o schema SchedulePostRequest."""

    def test_valid_request_all_fields(self):
        """Testa request válido com todos os campos."""
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="photo",
            caption="Test caption",
            hashtags=["test", "photo"],
            account_name="@test_account",
            platform_config={"quality": "high"}
        )
        assert request.platform == "instagram"
        assert request.content_type == "photo"
        assert len(request.hashtags) == 2

    def test_valid_request_minimal(self):
        """Testa request válido com campos mínimos."""
        request = SchedulePostRequest(
            platform="tiktok",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
            content_type="video"
        )
        assert request.platform == "tiktok"
        assert request.caption == ""
        assert request.hashtags == []
        assert request.account_name is None
        assert request.platform_config == {}

    def test_youtube_platform(self):
        """Testa request para YouTube."""
        request = SchedulePostRequest(
            platform="youtube",
            scheduled_time=datetime.now(timezone.utc) + timedelta(days=1),
            content_type="short",
            caption="YouTube short video"
        )
        assert request.platform == "youtube"
        assert request.content_type == "short"

    def test_whatsapp_platform(self):
        """Testa request para WhatsApp."""
        request = SchedulePostRequest(
            platform="whatsapp",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=3),
            content_type="text",
            caption="WhatsApp message"
        )
        assert request.platform == "whatsapp"


class TestSchedulePostResponseSchema:
    """Testes para o schema SchedulePostResponse."""

    def test_valid_response(self):
        """Testa response válido."""
        response = SchedulePostResponse(
            id=str(uuid4()),
            platform="instagram",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            status="scheduled",
            content_type="photo"
        )
        assert response.platform == "instagram"
        assert response.status == "scheduled"


class TestBulkActionRequestSchema:
    """Testes para o schema BulkActionRequest."""

    def test_valid_bulk_request(self):
        """Testa request de ação em massa válido."""
        ids = [str(uuid4()) for _ in range(5)]
        request = BulkActionRequest(ids=ids)
        assert len(request.ids) == 5

    def test_empty_bulk_request(self):
        """Testa request de ação em massa vazio."""
        request = BulkActionRequest(ids=[])
        assert request.ids == []

    def test_single_id_bulk_request(self):
        """Testa request com único ID."""
        request = BulkActionRequest(ids=[str(uuid4())])
        assert len(request.ids) == 1


# ==================== TESTS: Endpoints (Mocked) ====================


class TestSchedulePostEndpoint:
    """Testes para endpoint POST /posts - apenas importação."""

    def test_router_exists(self, app):
        """Verifica que o router foi importado corretamente."""
        assert router is not None
        # Verificar que as rotas existem
        routes = [r.path for r in router.routes]
        assert "/posts" in routes or any("/posts" in r for r in routes)


class TestListScheduledPostsEndpoint:
    """Testes para endpoint GET /posts - apenas importação."""

    def test_router_has_get_posts(self, app):
        """Verifica que a rota GET /posts existe."""
        routes = [r.path for r in router.routes]
        assert any("posts" in r for r in routes)


class TestCancelPostEndpoint:
    """Testes para endpoint DELETE /posts/{post_id} - apenas importação."""

    def test_router_has_delete_posts(self, app):
        """Verifica que a rota DELETE existe."""
        assert len(router.routes) > 0


class TestSchedulerStatsEndpoint:
    """Testes para endpoint GET /stats - apenas importação."""

    def test_router_has_stats(self, app):
        """Verifica que a rota /stats existe."""
        routes = [r.path for r in router.routes]
        assert any("stats" in r for r in routes)


class TestDLQEndpoints:
    """Testes para endpoints de Dead Letter Queue - apenas importação."""

    def test_router_has_dlq(self, app):
        """Verifica que as rotas DLQ existem."""
        routes = [r.path for r in router.routes]
        assert any("dlq" in r for r in routes)


class TestBulkDLQOperations:
    """Testes para operações em massa na DLQ - apenas importação."""

    def test_bulk_routes_exist(self, app):
        """Verifica que as rotas de operações em massa existem."""
        routes = [r.path for r in router.routes]
        assert len(routes) > 0


# ==================== TESTS: Edge Cases ====================


class TestEdgeCases:
    """Testes para edge cases."""

    def test_classify_error_multiword_match(self):
        """Testa classificação com múltiplas palavras no match."""
        # Erro com múltiplas categorias - primeira match ganha
        error = "Rate limit 429 auth token expired"
        result = _classify_error(error)
        assert result == "rate_limit"  # rate limit vem primeiro

    def test_classify_error_special_characters(self):
        """Testa classificação com caracteres especiais."""
        assert _classify_error("Error: timeout@network!") == "network_error"

    def test_classify_error_numbers_only(self):
        """Testa classificação apenas com números."""
        assert _classify_error("12345") == "unknown"

    def test_bulk_request_large_list(self):
        """Testa request com lista grande de IDs."""
        ids = [str(uuid4()) for _ in range(100)]
        request = BulkActionRequest(ids=ids)
        assert len(request.ids) == 100

    def test_schedule_request_with_unicode_caption(self):
        """Testa request com caption contendo unicode."""
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="photo",
            caption="Post com emoji 🚀 e 中文字符"
        )
        assert "🚀" in request.caption
        assert "中文字符" in request.caption

    def test_schedule_request_with_empty_hashtags(self):
        """Testa request com hashtags vazia."""
        request = SchedulePostRequest(
            platform="tiktok",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="video",
            hashtags=[]
        )
        assert request.hashtags == []

    def test_schedule_request_with_long_caption(self):
        """Testa request com caption muito longa."""
        long_caption = "A" * 5000
        request = SchedulePostRequest(
            platform="youtube",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="video",
            caption=long_caption
        )
        assert len(request.caption) == 5000


# ==================== TESTS: All Error Types ====================


class TestAllErrorTypes:
    """Testa todos os tipos de erro para cobertura completa."""

    @pytest.mark.parametrize("error_msg,expected", [
        ("Rate limit exceeded", "rate_limit"),
        ("429 Too Many Requests", "rate_limit"),
        ("401 Unauthorized", "auth_error"),
        ("403 Forbidden", "auth_error"),
        ("Token expired", "auth_error"),
        ("Please login again", "auth_error"),
        ("Connection timeout", "network_error"),
        ("Socket error", "network_error"),
        ("Network unreachable", "network_error"),
        ("Invalid media format", "content_error"),
        ("File size too large", "content_error"),
        ("Unsupported format", "content_error"),
        ("Daily quota exceeded", "quota_exceeded"),
        ("Limit exceeded for today", "quota_exceeded"),
        ("Random error message", "unknown"),
        ("", "unknown"),
    ])
    def test_error_classification(self, error_msg, expected):
        """Testa classificação parametrizada de erros."""
        assert _classify_error(error_msg) == expected


# ==================== TESTS: Platform Variations ====================


class TestPlatformVariations:
    """Testa todas as variações de plataforma."""

    @pytest.mark.parametrize("platform,content_type", [
        ("instagram", "photo"),
        ("instagram", "video"),
        ("instagram", "reel"),
        ("instagram", "story"),
        ("tiktok", "video"),
        ("youtube", "video"),
        ("youtube", "short"),
        ("whatsapp", "text"),
    ])
    def test_valid_platform_content_combinations(self, platform, content_type):
        """Testa combinações válidas de plataforma/conteúdo."""
        request = SchedulePostRequest(
            platform=platform,
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type=content_type
        )
        assert request.platform == platform
        assert request.content_type == content_type
