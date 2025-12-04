"""Authentication Middleware
JWT validation and user extraction

Uses centralized security configuration from shared/security_config.py
"""

from datetime import datetime, timezone
from typing import Optional

from api.database.connection import database
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from shared.security_config import get_security_config

# Get security configuration (cached singleton)
_security = get_security_config()
JWT_SECRET_KEY = _security.jwt_secret_key
JWT_ALGORITHM = _security.jwt_algorithm


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Validate JWT token and return current user.
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # Get user from database
        user = await get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "plan": user["plan"],
            "is_admin": user.get("is_admin", False),
            "credits_balance": user.get("credits_balance", 0),
            "hwid": payload.get("hwid")
        }
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID from database"""
    row = await database.fetch_one(
        """
        SELECT id, email, name, plan, is_admin, credits_balance, 
               credits_purchased, credits_used, created_at
        FROM users
        WHERE id = :user_id AND is_active = true
        """,
        {"user_id": user_id}
    )
    if row:
        return dict(row)
    return None


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Validate JWT token and ensure user is admin.
    
    Raises:
        HTTPException: If token is invalid, expired, or user is not admin
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # Get user from database
        user = await get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check admin status
        if not user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": True,
            "hwid": payload.get("hwid")
        }
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that work with or without authentication.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def create_access_token(user_id: str, hwid: str, expires_at: datetime) -> str:
    """Create JWT access token"""
    payload = {
        "sub": user_id,
        "hwid": hwid,
        "exp": expires_at.timestamp(),
        "iat": datetime.now(timezone.utc).timestamp()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
