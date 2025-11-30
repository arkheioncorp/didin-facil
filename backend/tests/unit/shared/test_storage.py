"""
Testes para shared/storage.py

Testes do serviço de storage R2 (S3-compatible).
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from io import BytesIO
from botocore.exceptions import ClientError


class TestR2StorageServiceInit:
    """Testes para inicialização do serviço"""
    
    def test_service_init_not_configured(self):
        """Deve marcar como não configurado quando credenciais faltando"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = None
            mock_settings.R2_SECRET_ACCESS_KEY = None
            mock_settings.R2_ENDPOINT = None
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            assert service.is_configured is False
    
    def test_service_init_with_placeholder_values(self):
        """Deve marcar como não configurado com valores placeholder"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "INSERIR_ACCESS_KEY"
            mock_settings.R2_SECRET_ACCESS_KEY = "INSERIR_SECRET"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            assert service.is_configured is False
    
    def test_service_init_configured(self):
        """Deve marcar como configurado com credenciais válidas"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "real_access_key"
            mock_settings.R2_SECRET_ACCESS_KEY = "real_secret_key"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            assert service.is_configured is True


class TestR2StorageClient:
    """Testes para propriedade client"""
    
    def test_client_raises_when_not_configured(self):
        """Deve lançar erro ao acessar client sem configuração"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = None
            mock_settings.R2_SECRET_ACCESS_KEY = None
            mock_settings.R2_ENDPOINT = None
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            with pytest.raises(RuntimeError) as exc:
                _ = service.client
            
            assert "não está configurado" in str(exc.value)
    
    def test_client_lazy_initialization(self):
        """Deve inicializar cliente boto3 de forma lazy"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "access_key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret_key"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            
            with patch("shared.storage.boto3") as mock_boto3:
                mock_client = MagicMock()
                mock_boto3.client.return_value = mock_client
                
                from shared.storage import R2StorageService
                service = R2StorageService()
                
                # Acessar client duas vezes
                client1 = service.client
                client2 = service.client
                
                # Deve ter sido criado apenas uma vez
                assert mock_boto3.client.call_count == 1
                assert client1 is client2


class TestGenerateKey:
    """Testes para geração de chaves únicas"""
    
    def test_generate_key_format(self):
        """Deve gerar chave no formato correto"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            key = service._generate_key("photo.jpg", "images")
            
            assert key.startswith("images/")
            assert key.endswith(".jpg")
    
    def test_generate_key_preserves_extension(self):
        """Deve preservar extensão do arquivo"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            assert service._generate_key("file.png", "images").endswith(".png")
            assert service._generate_key("file.PDF", "docs").endswith(".pdf")
            assert service._generate_key("file.JPEG", "images").endswith(".jpeg")


class TestUploadFile:
    """Testes para upload de arquivos"""
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self):
        """Deve fazer upload com sucesso"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            mock_settings.R2_BUCKET_NAME = "test-bucket"
            mock_settings.CDN_URL = "https://cdn.test.com"
            
            with patch("shared.storage.boto3") as mock_boto3:
                mock_client = MagicMock()
                mock_boto3.client.return_value = mock_client
                
                from shared.storage import R2StorageService
                service = R2StorageService()
                
                file_obj = BytesIO(b"test content")
                
                result = await service.upload_file(
                    file=file_obj,
                    filename="test.jpg",
                    folder="products"
                )
                
                assert result["success"] is True
                assert "url" in result
                assert "cdn.test.com" in result["url"]
                mock_client.upload_fileobj.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_not_configured(self):
        """Deve lançar erro quando não configurado"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = None
            mock_settings.R2_SECRET_ACCESS_KEY = None
            mock_settings.R2_ENDPOINT = None
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            file_obj = BytesIO(b"test content")
            
            with pytest.raises(RuntimeError):
                await service.upload_file(
                    file=file_obj,
                    filename="test.jpg"
                )
    
    @pytest.mark.asyncio
    async def test_upload_file_client_error(self):
        """Deve tratar erro do cliente S3"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            mock_settings.R2_BUCKET_NAME = "test-bucket"
            
            with patch("shared.storage.boto3") as mock_boto3:
                mock_client = MagicMock()
                mock_client.upload_fileobj.side_effect = ClientError(
                    {"Error": {"Code": "500", "Message": "Internal Error"}},
                    "upload_fileobj"
                )
                mock_boto3.client.return_value = mock_client
                
                from shared.storage import R2StorageService
                service = R2StorageService()
                
                file_obj = BytesIO(b"test content")
                
                with pytest.raises(RuntimeError) as exc:
                    await service.upload_file(
                        file=file_obj,
                        filename="test.jpg"
                    )
                
                assert "Falha no upload" in str(exc.value)


class TestUploadFromUrl:
    """Testes para upload a partir de URL"""
    
    @pytest.mark.asyncio
    async def test_upload_from_url_not_configured(self):
        """Deve retornar URL original quando não configurado"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = None
            mock_settings.R2_SECRET_ACCESS_KEY = None
            mock_settings.R2_ENDPOINT = None
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            result = await service.upload_from_url(
                "https://example.com/image.jpg"
            )
            
            assert result["success"] is False
            assert result["url"] == "https://example.com/image.jpg"
            assert result["reason"] == "R2 not configured"
    
    @pytest.mark.asyncio
    async def test_upload_from_url_success(self):
        """Deve fazer download e upload com sucesso"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            mock_settings.R2_BUCKET_NAME = "test-bucket"
            mock_settings.CDN_URL = "https://cdn.test.com"
            
            with patch("shared.storage.boto3") as mock_boto3:
                mock_client = MagicMock()
                mock_boto3.client.return_value = mock_client
                
                from shared.storage import R2StorageService
                service = R2StorageService()
                
                with patch("httpx.AsyncClient") as MockHttpxClient:
                    mock_response = MagicMock()
                    mock_response.content = b"image data"
                    mock_response.headers = {"content-type": "image/jpeg"}
                    mock_response.raise_for_status = MagicMock()
                    
                    mock_http = AsyncMock()
                    mock_http.__aenter__.return_value = mock_http
                    mock_http.__aexit__.return_value = None
                    mock_http.get = AsyncMock(return_value=mock_response)
                    
                    MockHttpxClient.return_value = mock_http
                    
                    result = await service.upload_from_url(
                        "https://example.com/photo.jpg"
                    )
                    
                    assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_upload_from_url_http_error(self):
        """Deve retornar erro quando download falha"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            with patch("httpx.AsyncClient") as MockHttpxClient:
                mock_http = AsyncMock()
                mock_http.__aenter__.return_value = mock_http
                mock_http.__aexit__.return_value = None
                mock_http.get = AsyncMock(side_effect=Exception("Network error"))
                
                MockHttpxClient.return_value = mock_http
                
                result = await service.upload_from_url(
                    "https://example.com/broken.jpg"
                )
                
                assert result["success"] is False
                assert "error" in result


class TestDeleteFile:
    """Testes para deleção de arquivos"""
    
    @pytest.mark.asyncio
    async def test_delete_file_success(self):
        """Deve deletar arquivo com sucesso"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            mock_settings.R2_BUCKET_NAME = "test-bucket"
            
            with patch("shared.storage.boto3") as mock_boto3:
                mock_client = MagicMock()
                mock_boto3.client.return_value = mock_client
                
                from shared.storage import R2StorageService
                service = R2StorageService()
                
                result = await service.delete_file("images/test.jpg")
                
                assert result is True
                mock_client.delete_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_file_not_configured(self):
        """Deve retornar False quando não configurado"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = None
            mock_settings.R2_SECRET_ACCESS_KEY = None
            mock_settings.R2_ENDPOINT = None
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            result = await service.delete_file("images/test.jpg")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_file_client_error(self):
        """Deve retornar False quando erro do S3"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            mock_settings.R2_BUCKET_NAME = "test-bucket"
            
            with patch("shared.storage.boto3") as mock_boto3:
                mock_client = MagicMock()
                mock_client.delete_object.side_effect = ClientError(
                    {"Error": {"Code": "404", "Message": "Not Found"}},
                    "delete_object"
                )
                mock_boto3.client.return_value = mock_client
                
                from shared.storage import R2StorageService
                service = R2StorageService()
                
                result = await service.delete_file("images/missing.jpg")
                
                assert result is False


class TestGetPresignedUrl:
    """Testes para geração de URLs pré-assinadas"""
    
    @pytest.mark.asyncio
    async def test_presigned_url_success(self):
        """Deve gerar URL pré-assinada"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            mock_settings.R2_BUCKET_NAME = "test-bucket"
            
            with patch("shared.storage.boto3") as mock_boto3:
                mock_client = MagicMock()
                mock_client.generate_presigned_url.return_value = "https://signed.url.com"
                mock_boto3.client.return_value = mock_client
                
                from shared.storage import R2StorageService
                service = R2StorageService()
                
                result = await service.get_presigned_url("images/test.jpg")
                
                assert result == "https://signed.url.com"
    
    @pytest.mark.asyncio
    async def test_presigned_url_not_configured(self):
        """Deve retornar None quando não configurado"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = None
            mock_settings.R2_SECRET_ACCESS_KEY = None
            mock_settings.R2_ENDPOINT = None
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            result = await service.get_presigned_url("images/test.jpg")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_presigned_url_client_error(self):
        """Deve retornar None quando erro do S3"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            mock_settings.R2_BUCKET_NAME = "test-bucket"
            
            with patch("shared.storage.boto3") as mock_boto3:
                mock_client = MagicMock()
                mock_client.generate_presigned_url.side_effect = ClientError(
                    {"Error": {"Code": "500", "Message": "Error"}},
                    "generate_presigned_url"
                )
                mock_boto3.client.return_value = mock_client
                
                from shared.storage import R2StorageService
                service = R2StorageService()
                
                result = await service.get_presigned_url("images/test.jpg")
                
                assert result is None


class TestListFiles:
    """Testes para listagem de arquivos"""
    
    @pytest.mark.asyncio
    async def test_list_files_success(self):
        """Deve listar arquivos com sucesso"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            mock_settings.R2_BUCKET_NAME = "test-bucket"
            mock_settings.CDN_URL = "https://cdn.test.com"
            
            with patch("shared.storage.boto3") as mock_boto3:
                from datetime import datetime, timezone
                
                mock_client = MagicMock()
                mock_client.list_objects_v2.return_value = {
                    "Contents": [
                        {
                            "Key": "images/photo1.jpg",
                            "Size": 1024,
                            "LastModified": datetime.now(timezone.utc)
                        },
                        {
                            "Key": "images/photo2.png",
                            "Size": 2048,
                            "LastModified": datetime.now(timezone.utc)
                        }
                    ]
                }
                mock_boto3.client.return_value = mock_client
                
                from shared.storage import R2StorageService
                service = R2StorageService()
                
                result = await service.list_files(prefix="images/")
                
                assert len(result) == 2
                assert result[0]["key"] == "images/photo1.jpg"
                assert "url" in result[0]
    
    @pytest.mark.asyncio
    async def test_list_files_not_configured(self):
        """Deve retornar lista vazia quando não configurado"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = None
            mock_settings.R2_SECRET_ACCESS_KEY = None
            mock_settings.R2_ENDPOINT = None
            
            from shared.storage import R2StorageService
            service = R2StorageService()
            
            result = await service.list_files()
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_list_files_empty(self):
        """Deve retornar lista vazia quando não há arquivos"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            mock_settings.R2_BUCKET_NAME = "test-bucket"
            
            with patch("shared.storage.boto3") as mock_boto3:
                mock_client = MagicMock()
                mock_client.list_objects_v2.return_value = {}
                mock_boto3.client.return_value = mock_client
                
                from shared.storage import R2StorageService
                service = R2StorageService()
                
                result = await service.list_files()
                
                assert result == []
    
    @pytest.mark.asyncio
    async def test_list_files_client_error(self):
        """Deve retornar lista vazia quando erro do S3"""
        with patch("shared.storage.settings") as mock_settings:
            mock_settings.R2_ACCESS_KEY_ID = "key"
            mock_settings.R2_SECRET_ACCESS_KEY = "secret"
            mock_settings.R2_ENDPOINT = "https://r2.endpoint.com"
            mock_settings.R2_BUCKET_NAME = "test-bucket"
            
            with patch("shared.storage.boto3") as mock_boto3:
                mock_client = MagicMock()
                mock_client.list_objects_v2.side_effect = ClientError(
                    {"Error": {"Code": "500", "Message": "Error"}},
                    "list_objects_v2"
                )
                mock_boto3.client.return_value = mock_client
                
                from shared.storage import R2StorageService
                service = R2StorageService()
                
                result = await service.list_files()
                
                assert result == []


class TestSingletonInstance:
    """Testes para instância singleton"""
    
    def test_storage_singleton_exists(self):
        """Deve ter instância singleton exportada"""
        from shared.storage import storage
        
        assert storage is not None
