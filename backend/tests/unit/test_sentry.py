"""
Testes para Sentry Integration - shared/sentry.py
Cobertura simplificada: testa métodos do SentryService sem reload de módulo
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSentryServiceConfiguration:
    """Testes de configuração do SentryService"""
    
    def test_check_configuration_with_valid_dsn(self):
        """Deve retornar True quando DSN válido"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.ENVIRONMENT = "testing"
        mock_settings.is_production = False
        mock_settings.DEBUG = True
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            assert service.is_configured is True
    
    def test_check_configuration_without_dsn(self):
        """Deve retornar False quando DSN não configurado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = None
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            assert service.is_configured is False
    
    def test_check_configuration_with_placeholder_dsn(self):
        """Deve retornar False quando DSN é placeholder"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "INSERIR_SEU_DSN_AQUI"
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            assert service.is_configured is False


class TestSentryServiceInit:
    """Testes de inicialização do SentryService"""
    
    def test_is_initialized_default_false(self):
        """Deve iniciar como não inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            assert service.is_initialized is False
    
    def test_init_success(self):
        """Deve inicializar SDK com sucesso"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.ENVIRONMENT = "testing"
        mock_settings.is_production = False
        mock_settings.DEBUG = True
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                from shared.sentry import SentryService
                service = SentryService()
                result = service.init()
                
                assert result is True
                assert service.is_initialized is True
    
    def test_init_not_configured(self):
        """Deve retornar False se não configurado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = None
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            result = service.init()
            
            assert result is False
    
    def test_init_exception_handling(self):
        """Deve lidar com exceção na inicialização"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.ENVIRONMENT = "testing"
        mock_settings.is_production = False
        mock_settings.DEBUG = True
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                mock_sdk.init.side_effect = Exception("Init error")
                
                from shared.sentry import SentryService
                service = SentryService()
                result = service.init()
                
                assert result is False


class TestBeforeSend:
    """Testes dos filtros before_send"""
    
    def test_before_send_filters_cookies(self):
        """Deve filtrar cookies do request"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            
            event = {
                "request": {
                    "cookies": "session=abc123"
                }
            }
            
            result = service._before_send(event, {})
            assert result["request"]["cookies"] == "[FILTERED]"
    
    def test_before_send_filters_sensitive_headers(self):
        """Deve filtrar headers sensíveis"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            
            event = {
                "request": {
                    "headers": {
                        "authorization": "Bearer token123",
                        "cookie": "session=abc",
                        "x-api-key": "key123",
                        "content-type": "application/json"
                    }
                }
            }
            
            result = service._before_send(event, {})
            
            assert result["request"]["headers"]["authorization"] == "[FILTERED]"
            assert result["request"]["headers"]["cookie"] == "[FILTERED]"
            assert result["request"]["headers"]["x-api-key"] == "[FILTERED]"
            assert result["request"]["headers"]["content-type"] == "application/json"
    
    def test_before_send_filters_sensitive_body_fields(self):
        """Deve filtrar campos sensíveis do body"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            
            event = {
                "request": {
                    "data": {
                        "password": "secret123",
                        "email": "user@test.com",
                        "cpf": "123.456.789-00",
                        "username": "testuser"
                    }
                }
            }
            
            result = service._before_send(event, {})
            
            assert result["request"]["data"]["password"] == "[FILTERED]"
            assert result["request"]["data"]["email"] == "[FILTERED]"
            assert result["request"]["data"]["cpf"] == "[FILTERED]"
            assert result["request"]["data"]["username"] == "testuser"
    
    def test_before_send_filters_user_data(self):
        """Deve filtrar dados do usuário mantendo apenas campos permitidos"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            
            event = {
                "user": {
                    "id": "user123",
                    "ip_address": "192.168.1.1",
                    "email": "user@test.com",
                    "name": "Test User"
                }
            }
            
            result = service._before_send(event, {})
            
            assert result["user"]["id"] == "user123"
            assert result["user"]["ip_address"] == "192.168.1.1"
            assert "email" not in result["user"]
            assert "name" not in result["user"]
    
    def test_before_send_no_request(self):
        """Deve lidar com evento sem request"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            
            event = {"message": "test"}
            result = service._before_send(event, {})
            assert result == event


class TestBeforeSendTransaction:
    """Testes do filtro before_send_transaction"""
    
    def test_filters_health_check_transactions(self):
        """Deve ignorar transactions de health check"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            
            for path in ["/health", "/healthz", "/ready", "/"]:
                event = {"transaction": path}
                result = service._before_send_transaction(event, {})
                assert result is None, f"Should filter {path}"
    
    def test_filters_static_transactions(self):
        """Deve ignorar transactions de assets estáticos"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            
            event = {"transaction": "/static/js/app.js"}
            result = service._before_send_transaction(event, {})
            assert result is None
    
    def test_allows_api_transactions(self):
        """Deve permitir transactions de API"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            
            event = {"transaction": "/api/v1/products"}
            result = service._before_send_transaction(event, {})
            assert result == event


class TestCaptureException:
    """Testes de captura de exceções"""
    
    def test_capture_exception_when_initialized(self):
        """Deve capturar exceção quando inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.ENVIRONMENT = "testing"
        mock_settings.is_production = False
        mock_settings.DEBUG = True
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                mock_sdk.capture_exception.return_value = "event-123"
                
                from shared.sentry import SentryService
                service = SentryService()
                service.init()
                
                error = ValueError("Test error")
                result = service.capture_exception(error, context="test")
                
                assert result == "event-123"
    
    def test_capture_exception_not_initialized(self):
        """Deve retornar None quando não inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = None
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            
            error = ValueError("Test error")
            result = service.capture_exception(error)
            
            assert result is None


class TestCaptureMessage:
    """Testes de captura de mensagens"""
    
    def test_capture_message_when_initialized(self):
        """Deve capturar mensagem quando inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.ENVIRONMENT = "testing"
        mock_settings.is_production = False
        mock_settings.DEBUG = True
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                mock_sdk.capture_message.return_value = "msg-123"
                
                from shared.sentry import SentryService
                service = SentryService()
                service.init()
                
                result = service.capture_message("Test message", level="warning")
                assert result == "msg-123"
    
    def test_capture_message_not_initialized(self):
        """Deve retornar None quando não inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = None
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            result = service.capture_message("Test")
            assert result is None


class TestSetUser:
    """Testes de set_user"""
    
    def test_set_user_when_initialized(self):
        """Deve definir contexto de usuário"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.ENVIRONMENT = "testing"
        mock_settings.is_production = False
        mock_settings.DEBUG = True
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                from shared.sentry import SentryService
                service = SentryService()
                service.init()
                
                service.set_user("user123", email="test@test.com")
                mock_sdk.set_user.assert_called_once()
    
    def test_set_user_not_initialized(self):
        """Não deve fazer nada quando não inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = None
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                from shared.sentry import SentryService
                service = SentryService()
                
                service.set_user("user123")
                mock_sdk.set_user.assert_not_called()


class TestSetTagAndContext:
    """Testes de set_tag e set_context"""
    
    def test_set_tag_when_initialized(self):
        """Deve definir tag quando inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.ENVIRONMENT = "testing"
        mock_settings.is_production = False
        mock_settings.DEBUG = True
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                from shared.sentry import SentryService
                service = SentryService()
                service.init()
                
                service.set_tag("feature", "search")
                mock_sdk.set_tag.assert_called_once_with("feature", "search")
    
    def test_set_tag_not_initialized(self):
        """Não deve fazer nada quando não inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = None
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                from shared.sentry import SentryService
                service = SentryService()
                service.set_tag("feature", "search")
                mock_sdk.set_tag.assert_not_called()
    
    def test_set_context_when_initialized(self):
        """Deve definir contexto quando inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.ENVIRONMENT = "testing"
        mock_settings.is_production = False
        mock_settings.DEBUG = True
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                from shared.sentry import SentryService
                service = SentryService()
                service.init()
                
                service.set_context("order", {"id": "123"})
                mock_sdk.set_context.assert_called_once_with("order", {"id": "123"})
    
    def test_set_context_not_initialized(self):
        """Não deve fazer nada quando não inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = None
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                from shared.sentry import SentryService
                service = SentryService()
                service.set_context("order", {"id": "123"})
                mock_sdk.set_context.assert_not_called()


class TestAddBreadcrumb:
    """Testes de add_breadcrumb"""
    
    def test_add_breadcrumb_when_initialized(self):
        """Deve adicionar breadcrumb quando inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.ENVIRONMENT = "testing"
        mock_settings.is_production = False
        mock_settings.DEBUG = True
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                from shared.sentry import SentryService
                service = SentryService()
                service.init()
                
                service.add_breadcrumb(
                    message="User clicked button",
                    category="ui",
                    level="info",
                    data={"button_id": "submit"}
                )
                
                mock_sdk.add_breadcrumb.assert_called_once()
    
    def test_add_breadcrumb_not_initialized(self):
        """Não deve fazer nada quando não inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = None
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                from shared.sentry import SentryService
                service = SentryService()
                service.add_breadcrumb("Test")
                mock_sdk.add_breadcrumb.assert_not_called()


class TestStartTransaction:
    """Testes de start_transaction"""
    
    def test_start_transaction_when_initialized(self):
        """Deve iniciar transaction quando inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.ENVIRONMENT = "testing"
        mock_settings.is_production = False
        mock_settings.DEBUG = True
        
        with patch("shared.sentry.settings", mock_settings):
            with patch("shared.sentry.sentry_sdk") as mock_sdk:
                mock_transaction = MagicMock()
                mock_sdk.start_transaction.return_value = mock_transaction
                
                from shared.sentry import SentryService
                service = SentryService()
                service.init()
                
                result = service.start_transaction("test_op", op="task")
                
                mock_sdk.start_transaction.assert_called_once_with(name="test_op", op="task")
                assert result == mock_transaction
    
    def test_start_transaction_not_initialized(self):
        """Deve retornar nullcontext quando não inicializado"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = None
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import SentryService
            service = SentryService()
            result = service.start_transaction("test_op")
            
            # Deve ser um context manager que não faz nada
            with result:
                pass  # Não deve lançar exceção


class TestFlush:
    """Testes de flush"""
    
    def test_flush_when_initialized(self):
        """Deve chamar flush quando inicializado"""
        with patch("shared.sentry.sentry_sdk") as mock_sdk:
            from shared.sentry import SentryService
            service = SentryService()
            service._initialized = True  # Simular inicialização
            
            service.flush(timeout=3.0)
            mock_sdk.flush.assert_called_once_with(timeout=3.0)
    
    def test_flush_not_initialized(self):
        """Não deve chamar flush quando não inicializado"""
        with patch("shared.sentry.sentry_sdk") as mock_sdk:
            from shared.sentry import SentryService
            service = SentryService()
            service._initialized = False
            service.flush()
            mock_sdk.flush.assert_not_called()


class TestAsyncioIsAsync:
    """Testes da função auxiliar asyncio_is_async"""
    
    def test_detects_async_function(self):
        """Deve detectar função assíncrona"""
        from shared.sentry import asyncio_is_async
        
        async def async_func():
            pass
        
        assert asyncio_is_async(async_func) is True
    
    def test_detects_sync_function(self):
        """Deve detectar função síncrona"""
        from shared.sentry import asyncio_is_async
        
        def sync_func():
            pass
        
        assert asyncio_is_async(sync_func) is False


class TestSentrySingleton:
    """Testes do singleton sentry"""
    
    def test_singleton_exists(self):
        """Deve existir instância singleton"""
        from shared.sentry import sentry
        assert sentry is not None


class TestSentryTraceDecorator:
    """Testes do decorator sentry_trace"""
    
    @pytest.mark.asyncio
    async def test_sentry_trace_async_function_not_initialized(self):
        """Deve executar função assíncrona mesmo sem Sentry"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = None
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import sentry_trace
            
            @sentry_trace("db.query")
            async def test_func():
                return "result"
            
            result = await test_func()
            assert result == "result"
    
    def test_sentry_trace_sync_function(self):
        """Deve executar função síncrona"""
        mock_settings = MagicMock()
        mock_settings.SENTRY_DSN = None
        
        with patch("shared.sentry.settings", mock_settings):
            from shared.sentry import sentry_trace
            
            @sentry_trace("http.request")
            def test_func():
                return "sync_result"
            
            result = test_func()
            assert result == "sync_result"
