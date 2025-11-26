"""
Authentication Service
User authentication and JWT token management
"""

import os
from datetime import datetime
from typing import Optional
import secrets

from jose import jwt
from passlib.context import CryptContext

from api.database.connection import database


# JWT settings from environment
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management"""
    
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
    
    async def authenticate(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user by email and password"""
        result = await database.fetch_one(
            """
            SELECT id, email, name, password_hash, plan, is_active
            FROM users
            WHERE email = :email
            """,
            {"email": email}
        )
        
        if not result:
            return None
        
        if not result["is_active"]:
            return None
        
        if not self.verify_password(password, result["password_hash"]):
            return None
        
        return {
            "id": str(result["id"]),
            "email": result["email"],
            "name": result["name"],
            "plan": result["plan"]
        }
    
    async def validate_hwid(self, user_id: str, hwid: str) -> bool:
        """
        Validate hardware ID for license binding.
        Returns True if HWID matches or if this is the first device.
        """
        # Get license for user
        license_info = await database.fetch_one(
            """
            SELECT l.id, l.max_devices
            FROM licenses l
            WHERE l.user_id = :user_id AND l.status = 'active'
            """,
            {"user_id": user_id}
        )
        
        if not license_info:
            # No license - allow (free tier)
            return True
        
        # Check if HWID is already registered
        device = await database.fetch_one(
            """
            SELECT id FROM license_devices
            WHERE license_id = :license_id AND device_id = :hwid
            """,
            {"license_id": license_info["id"], "hwid": hwid}
        )
        
        if device:
            # Update last seen
            await database.execute(
                """
                UPDATE license_devices
                SET last_seen = NOW()
                WHERE id = :id
                """,
                {"id": device["id"]}
            )
            return True
        
        # Check device count
        device_count = await database.fetch_one(
            """
            SELECT COUNT(*) as count
            FROM license_devices
            WHERE license_id = :license_id
            """,
            {"license_id": license_info["id"]}
        )
        
        if device_count["count"] >= license_info["max_devices"]:
            return False
        
        # Register new device
        await database.execute(
            """
            INSERT INTO license_devices (license_id, device_id, last_seen)
            VALUES (:license_id, :hwid, NOW())
            """,
            {"license_id": license_info["id"], "hwid": hwid}
        )
        
        return True
    
    async def create_user(self, email: str, password: str, name: str) -> dict:
        """Create a new user"""
        password_hash = self.hash_password(password)
        
        result = await database.fetch_one(
            """
            INSERT INTO users (email, password_hash, name, plan, is_active, created_at)
            VALUES (:email, :password_hash, :name, 'free', true, NOW())
            RETURNING id, email, name, plan
            """,
            {
                "email": email,
                "password_hash": password_hash,
                "name": name
            }
        )
        
        return {
            "id": str(result["id"]),
            "email": result["email"],
            "name": result["name"],
            "plan": result["plan"]
        }
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        result = await database.fetch_one(
            """
            SELECT id, email, name, plan, is_active, created_at
            FROM users
            WHERE email = :email
            """,
            {"email": email}
        )
        
        if not result:
            return None
        
        return dict(result)
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        result = await database.fetch_one(
            """
            SELECT id, email, name, plan, is_active, created_at
            FROM users
            WHERE id = :user_id
            """,
            {"user_id": user_id}
        )
        
        if not result:
            return None
        
        return dict(result)
    
    def create_token(self, user_id: str, hwid: str, expires_at: datetime) -> str:
        """Create JWT token"""
        payload = {
            "sub": user_id,
            "hwid": hwid,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "iss": "tiktrend-api"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.JWTError:
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(password, password_hash)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a random API key"""
        return f"tk_{secrets.token_urlsafe(32)}"
