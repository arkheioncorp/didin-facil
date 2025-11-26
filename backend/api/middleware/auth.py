"""
Authentication Middleware
JWT validation and user extraction
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from api.database.connection import database


# JWT settings from environment
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "dev-secret-key-change-in-production"
)
JWT_ALGORITHM = "HS256"


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
        if exp and datetime.utcnow().timestamp() > exp:
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
        SELECT id, email, name, plan, created_at
        FROM users
        WHERE id = :user_id AND is_active = true
        """,
        {"user_id": user_id}
    )
    if row:
        return dict(row)
    return None


def create_access_token(user_id: str, hwid: str, expires_at: datetime) -> str:
    """Create JWT access token"""
    payload = {
        "sub": user_id,
        "hwid": hwid,
        "exp": expires_at.timestamp(),
        "iat": datetime.utcnow().timestamp()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
