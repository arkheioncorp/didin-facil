"""
Testes unitários para api/middleware/auth.py
Cobertura: JWT validation, get_current_user, token creation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


class TestCreateAccessToken:
    """Testes para create_access_token"""
    
    def test_create_access_token_basic(self):
        """Deve criar token com dados básicos"""
        with patch('api.middleware.auth.jwt.encode') as mock_encode:
            mock_encode.return_value = "test_token_123"
            
            from api.middleware.auth import create_access_token
            
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            token = create_access_token("user123", "hwid123", expires_at)
            
            assert token == "test_token_123"
            mock_encode.assert_called_once()
    
    def test_create_access_token_payload_structure(self):
        """Deve criar payload correto"""
        with patch('api.middleware.auth.jwt.encode') as mock_encode:
            mock_encode.return_value = "token"
            
            from api.middleware.auth import create_access_token
            
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            create_access_token("user123", "hwid456", expires_at)
            
            call_args = mock_encode.call_args[0][0]
            assert call_args["sub"] == "user123"
            assert call_args["hwid"] == "hwid456"
            assert "exp" in call_args
            assert "iat" in call_args


class TestGetUserById:
    """Testes para get_user_by_id"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self):
        """Deve retornar usuário quando encontrado"""
        mock_row = MagicMock()
        mock_row.__iter__ = lambda self: iter([
            ("id", "user123"),
            ("email", "test@example.com"),
            ("name", "Test User"),
            ("plan", "premium"),
            ("created_at", datetime.now(timezone.utc))
        ])
        mock_row.keys = lambda: ["id", "email", "name", "plan", "created_at"]
        
        # Simular dict(row)
        def to_dict():
            return {
                "id": "user123",
                "email": "test@example.com",
                "name": "Test User",
                "plan": "premium",
                "created_at": datetime.now(timezone.utc)
            }
        
        with patch('api.middleware.auth.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=MagicMock(
                __iter__=lambda self: iter([
                    ("id", "user123"),
                    ("email", "test@example.com"),
                    ("name", "Test User"),
                    ("plan", "premium"),
                    ("created_at", datetime.now(timezone.utc))
                ]),
                keys=lambda: ["id", "email", "name", "plan", "created_at"]
            ))
            
            from api.middleware.auth import get_user_by_id
            
            # Mock dict() conversion
            with patch('builtins.dict', return_value=to_dict()):
                await get_user_by_id("user123")
                
                mock_db.fetch_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self):
        """Deve retornar None quando usuário não existe"""
        with patch('api.middleware.auth.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=None)
            
            from api.middleware.auth import get_user_by_id
            
            user = await get_user_by_id("nonexistent")
            
            assert user is None


class TestGetCurrentUser:
    """Testes para get_current_user"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Deve retornar usuário para token válido"""
        from api.middleware.auth import get_current_user
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", 
            credentials="valid_token"
        )
        
        with patch('api.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {
                "sub": "user123",
                "hwid": "hwid123",
                "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
            }
            
            with patch('api.middleware.auth.get_user_by_id') as mock_get_user:
                mock_get_user.return_value = {
                    "id": "user123",
                    "email": "test@example.com",
                    "name": "Test User",
                    "plan": "premium"
                }
                
                user = await get_current_user(credentials)
                
                assert user["id"] == "user123"
                assert user["email"] == "test@example.com"
                assert user["plan"] == "premium"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Deve levantar exceção para token inválido"""
        from jose import JWTError
        from api.middleware.auth import get_current_user
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", 
            credentials="invalid_token"
        )
        
        with patch('api.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.side_effect = JWTError("Invalid token")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_sub_in_payload(self):
        """Deve levantar exceção quando payload não tem sub"""
        from api.middleware.auth import get_current_user
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", 
            credentials="token_without_sub"
        )
        
        with patch('api.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {
                "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
            }  # Sem "sub"
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)
            
            assert exc_info.value.status_code == 401
            assert "Invalid token payload" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self):
        """Deve levantar exceção para token expirado"""
        from api.middleware.auth import get_current_user
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", 
            credentials="expired_token"
        )
        
        with patch('api.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {
                "sub": "user123",
                "exp": (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()  # Expirado
            }
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)
            
            assert exc_info.value.status_code == 401
            assert "expired" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Deve levantar exceção quando usuário não existe no DB"""
        from api.middleware.auth import get_current_user
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", 
            credentials="valid_token"
        )
        
        with patch('api.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {
                "sub": "deleted_user",
                "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
            }
            
            with patch('api.middleware.auth.get_user_by_id') as mock_get_user:
                mock_get_user.return_value = None
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(credentials)
                
                assert exc_info.value.status_code == 401
                assert "User not found" in exc_info.value.detail


class TestJWTConstants:
    """Testes para constantes JWT"""
    
    def test_jwt_secret_key_exists(self):
        """Deve ter JWT_SECRET_KEY definido"""
        from api.middleware.auth import JWT_SECRET_KEY
        assert JWT_SECRET_KEY is not None
        assert len(JWT_SECRET_KEY) > 0
    
    def test_jwt_algorithm_is_hs256(self):
        """Deve usar algoritmo HS256"""
        from api.middleware.auth import JWT_ALGORITHM
        assert JWT_ALGORITHM == "HS256"
    
    def test_security_is_http_bearer(self):
        """Deve usar HTTPBearer como security scheme"""
        from api.middleware.auth import security
        from fastapi.security import HTTPBearer
        assert isinstance(security, HTTPBearer)
