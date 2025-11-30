"""
Cloudflare R2 Storage Service
Gerenciamento de upload de imagens
"""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
from pathlib import Path
import hashlib
import mimetypes
import logging
from datetime import datetime
import uuid

from .config import settings

logger = logging.getLogger(__name__)


class R2StorageService:
    """Serviço de storage usando Cloudflare R2 (S3-compatible)"""
    
    def __init__(self):
        self._client = None
        self._configured = False
        self._check_configuration()
    
    def _check_configuration(self) -> bool:
        """Verifica se R2 está configurado"""
        required = [
            settings.R2_ACCESS_KEY_ID,
            settings.R2_SECRET_ACCESS_KEY,
            settings.R2_ENDPOINT
        ]
        
        self._configured = all(
            val and not val.startswith("INSERIR_") 
            for val in required
        )
        
        if not self._configured:
            logger.warning(
                "⚠️ Cloudflare R2 não configurado. "
                "Uploads de imagens estarão desabilitados."
            )
        
        return self._configured
    
    @property
    def client(self):
        """Lazy initialization do cliente S3"""
        if not self._configured:
            raise RuntimeError(
                "R2 Storage não está configurado. "
                "Verifique as variáveis R2_* no .env"
            )
        
        if self._client is None:
            self._client = boto3.client(
                's3',
                endpoint_url=settings.R2_ENDPOINT,
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                config=Config(
                    signature_version='s3v4',
                    retries={'max_attempts': 3}
                )
            )
            logger.info("✅ Cloudflare R2 client inicializado")
        
        return self._client
    
    @property
    def is_configured(self) -> bool:
        """Verifica se o serviço está configurado"""
        return self._configured
    
    def _generate_key(
        self, 
        filename: str, 
        folder: str = "images"
    ) -> str:
        """Gera chave única para o arquivo"""
        ext = Path(filename).suffix.lower()
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y/%m/%d")
        
        # Hash do nome original para evitar conflitos
        name_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        
        return f"{folder}/{timestamp}/{name_hash}_{unique_id}{ext}"
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        folder: str = "images",
        content_type: Optional[str] = None
    ) -> dict:
        """
        Upload de arquivo para R2
        
        Args:
            file: Arquivo binário para upload
            filename: Nome original do arquivo
            folder: Pasta de destino (images, products, avatars)
            content_type: MIME type (detectado automaticamente se não fornecido)
        
        Returns:
            dict com url, key e metadata
        """
        if not self._configured:
            raise RuntimeError("R2 Storage não configurado")
        
        # Gerar chave única
        key = self._generate_key(filename, folder)
        
        # Detectar content-type
        if content_type is None:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or 'application/octet-stream'
        
        try:
            # Upload para R2
            self.client.upload_fileobj(
                file,
                settings.R2_BUCKET_NAME,
                key,
                ExtraArgs={
                    'ContentType': content_type,
                    'CacheControl': 'public, max-age=31536000',  # 1 ano
                }
            )
            
            # Construir URL pública
            public_url = f"{settings.CDN_URL}/{key}"
            
            logger.info(f"✅ Upload concluído: {key}")
            
            return {
                "success": True,
                "url": public_url,
                "key": key,
                "bucket": settings.R2_BUCKET_NAME,
                "content_type": content_type,
                "size": file.seek(0, 2)  # Get file size
            }
            
        except ClientError as e:
            logger.error(f"❌ Erro no upload R2: {e}")
            raise RuntimeError(f"Falha no upload: {e}")
    
    async def upload_from_url(
        self,
        image_url: str,
        folder: str = "products"
    ) -> dict:
        """
        Download e upload de imagem a partir de URL
        
        Args:
            image_url: URL da imagem para download
            folder: Pasta de destino
        
        Returns:
            dict com url pública no R2
        """
        import httpx
        from io import BytesIO
        
        if not self._configured:
            # Retornar URL original se R2 não configurado
            return {
                "success": False,
                "url": image_url,
                "reason": "R2 not configured"
            }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                
                # Extrair filename da URL
                filename = image_url.split("/")[-1].split("?")[0]
                if not filename or "." not in filename:
                    filename = f"image_{uuid.uuid4().hex[:8]}.jpg"
                
                # Upload para R2
                file_obj = BytesIO(response.content)
                content_type = response.headers.get(
                    "content-type", 
                    "image/jpeg"
                )
                
                return await self.upload_file(
                    file=file_obj,
                    filename=filename,
                    folder=folder,
                    content_type=content_type
                )
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar imagem de URL: {e}")
            return {
                "success": False,
                "url": image_url,
                "error": str(e)
            }
    
    async def delete_file(self, key: str) -> bool:
        """
        Remove arquivo do R2
        
        Args:
            key: Chave do arquivo no bucket
        
        Returns:
            True se deletado com sucesso
        """
        if not self._configured:
            return False
        
        try:
            self.client.delete_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=key
            )
            logger.info(f"🗑️ Arquivo deletado: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ Erro ao deletar: {e}")
            return False
    
    async def get_presigned_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Gera URL pré-assinada para upload direto
        
        Args:
            key: Chave do arquivo
            expires_in: Tempo de expiração em segundos (default: 1h)
        
        Returns:
            URL pré-assinada ou None
        """
        if not self._configured:
            return None
        
        try:
            url = self.client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.R2_BUCKET_NAME,
                    'Key': key
                },
                ExpiresIn=expires_in
            )
            return url
            
        except ClientError as e:
            logger.error(f"❌ Erro ao gerar presigned URL: {e}")
            return None
    
    async def list_files(
        self,
        prefix: str = "",
        max_keys: int = 100
    ) -> list:
        """
        Lista arquivos no bucket
        
        Args:
            prefix: Prefixo para filtrar (ex: "products/2025/")
            max_keys: Número máximo de resultados
        
        Returns:
            Lista de objetos
        """
        if not self._configured:
            return []
        
        try:
            response = self.client.list_objects_v2(
                Bucket=settings.R2_BUCKET_NAME,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat(),
                    "url": f"{settings.CDN_URL}/{obj['Key']}"
                })
            
            return files
            
        except ClientError as e:
            logger.error(f"❌ Erro ao listar arquivos: {e}")
            return []


# Singleton instance
storage = R2StorageService()
