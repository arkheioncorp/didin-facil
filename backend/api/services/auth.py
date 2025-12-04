"""Authentication Service
User authentication and JWT token management

Uses centralized security configuration from shared/security_config.py
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from api.database.connection import database
from jose import jwt
from passlib.context import CryptContext
from shared.security_config import get_security_config

# Token expiration times
VERIFICATION_TOKEN_EXPIRES_HOURS = 24
RESET_TOKEN_EXPIRES_HOURS = 1

# Get security configuration (cached singleton)
_security = get_security_config()
JWT_SECRET_KEY = _security.jwt_secret_key
JWT_ALGORITHM = _security.jwt_algorithm

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
            "iat": datetime.now(timezone.utc),
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

    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure password reset token"""
        return secrets.token_urlsafe(32)

    # ==========================================
    # EMAIL VERIFICATION
    # ==========================================

    async def create_verification_token(self, user_id: str) -> str:
        """
        Create and store email verification token.
        Returns the token to be sent via email.
        """
        token = self.generate_verification_token()

        await database.execute(
            """
            UPDATE users
            SET verification_token = :token
            WHERE id = :user_id
            """,
            {"token": token, "user_id": user_id}
        )

        return token

    async def verify_email_token(self, token: str) -> Optional[dict]:
        """
        Verify email verification token.
        Returns user dict if valid, None otherwise.
        """
        result = await database.fetch_one(
            """
            SELECT id, email, name, plan
            FROM users
            WHERE verification_token = :token
            """,
            {"token": token}
        )

        if not result:
            return None

        # Mark email as verified and clear token
        await database.execute(
            """
            UPDATE users
            SET is_email_verified = true,
                verification_token = NULL
            WHERE id = :user_id
            """,
            {"user_id": result["id"]}
        )

        return {
            "id": str(result["id"]),
            "email": result["email"],
            "name": result["name"],
            "plan": result["plan"]
        }

    async def is_email_verified(self, user_id: str) -> bool:
        """Check if user's email is verified"""
        result = await database.fetch_one(
            """
            SELECT is_email_verified
            FROM users
            WHERE id = :user_id
            """,
            {"user_id": user_id}
        )

        return result["is_email_verified"] if result else False

    # ==========================================
    # PASSWORD RESET
    # ==========================================

    async def create_reset_token(self, email: str) -> Optional[str]:
        """
        Create password reset token for user.
        Returns token if user exists, None otherwise.
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None

        token = self.generate_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=RESET_TOKEN_EXPIRES_HOURS
        )

        await database.execute(
            """
            UPDATE users
            SET reset_token = :token,
                reset_token_expires = :expires_at
            WHERE email = :email
            """,
            {"token": token, "expires_at": expires_at, "email": email}
        )

        return token

    async def verify_reset_token(self, token: str) -> Optional[dict]:
        """
        Verify password reset token.
        Returns user dict if valid and not expired, None otherwise.
        """
        result = await database.fetch_one(
            """
            SELECT id, email, name, reset_token_expires
            FROM users
            WHERE reset_token = :token
            """,
            {"token": token}
        )

        if not result:
            return None

        # Check expiration
        expires_at = result["reset_token_expires"]
        if expires_at and expires_at < datetime.now(timezone.utc):
            # Token expired - clear it
            await database.execute(
                """
                UPDATE users
                SET reset_token = NULL, reset_token_expires = NULL
                WHERE id = :user_id
                """,
                {"user_id": result["id"]}
            )
            return None

        return {
            "id": str(result["id"]),
            "email": result["email"],
            "name": result["name"]
        }

    async def reset_password_with_token(
        self, token: str, new_password: str
    ) -> bool:
        """
        Reset user password using valid reset token.
        Returns True if successful, False otherwise.
        """
        user = await self.verify_reset_token(token)
        if not user:
            return False

        password_hash = self.hash_password(new_password)

        await database.execute(
            """
            UPDATE users
            SET password_hash = :password_hash,
                reset_token = NULL,
                reset_token_expires = NULL
            WHERE id = :user_id
            """,
            {"password_hash": password_hash, "user_id": user["id"]}
        )

        return True

    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp"""
        await database.execute(
            """
            UPDATE users
            SET last_login_at = NOW()
            WHERE id = :user_id
            """,
            {"user_id": user_id}
        )
