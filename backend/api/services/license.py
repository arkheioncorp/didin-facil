"""
License Service
License management and validation
"""

import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from jose import jwt

from shared.config import settings
from api.database.connection import database


class LicenseService:
    """License management service"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.db = database
    
    async def get_license_by_email(self, email: str) -> Optional[dict]:
        """Get license by user email"""
        result = await self.db.fetch_one(
                """
                SELECT l.*, u.email, u.name
                FROM licenses l
                JOIN users u ON l.user_id = u.id
                WHERE u.email = :email AND l.is_active = true
                """,
                {"email": email}
            )
        
        return dict(result) if result else None
    
    async def get_license_by_key(self, license_key: str) -> Optional[dict]:
        """Get license by license key"""
        result = await self.db.fetch_one(
            """
            SELECT * FROM licenses
            WHERE license_key = :license_key
            """,
            {"license_key": license_key}
        )
        
        return dict(result) if result else None
    
    async def get_license_by_user(self, user_id: str) -> Optional[dict]:
        """Get license by user ID."""
        result = await self.db.fetch_one(
            """
            SELECT * FROM licenses
            WHERE user_id = :user_id AND is_active = true
            """,
            {"user_id": user_id}
        )
        
        return dict(result) if result else None
    
    async def validate_hwid(self, license_id: str, hwid: str) -> bool:
        """Check if HWID is registered for this license."""
        result = await self.db.fetch_one(
            """
            SELECT id FROM license_devices
            WHERE license_id = :license_id AND device_id = :hwid AND is_active = true
            """,
            {"license_id": license_id, "hwid": hwid}
        )
        
        return result is not None
    
    async def get_active_devices(self, license_id: str) -> List[dict]:
        """Get all active devices for a license"""
        results = await self.db.fetch_all(
            """
            SELECT id, device_id as hwid, created_at as first_seen_at, last_seen as last_seen_at
            FROM license_devices
            WHERE license_id = :license_id AND is_active = true
            """,
            {"license_id": license_id}
        )
        
        return [dict(r) for r in results]
    
    async def register_device(
        self,
        license_id: str,
        hwid: str,
        app_version: str
    ):
        """Register a new device for a license."""
        import json
        device_info = json.dumps({"app_version": app_version})
        
        await self.db.execute(
            """
            INSERT INTO license_devices 
            (id, license_id, device_id, device_info, created_at, last_seen, is_active)
            VALUES (:id, :license_id, :hwid, :device_info, NOW(), NOW(), true)
            ON CONFLICT (license_id, device_id) DO UPDATE SET
                last_seen = NOW(),
                device_info = :device_info,
                is_active = true
            """,
            {
                "id": str(uuid.uuid4()),
                "license_id": license_id,
                "hwid": hwid,
                "device_info": device_info
            }
        )
    
    async def deactivate_device(
        self,
        license_id: str,
        hwid: str,
        reason: Optional[str] = None
    ) -> bool:
        """Deactivate a device from a license."""
        await self.db.execute(
            """
            UPDATE license_devices
            SET is_active = false
            WHERE license_id = :license_id AND device_id = :hwid AND is_active = true
            """,
            {"license_id": license_id, "hwid": hwid}
        )
        
        return True
    
    async def create_license(
        self,
        email: str,
        plan: str = "lifetime",
        duration_days: int = -1,  # -1 = lifetime
        payment_id: Optional[str] = None
    ) -> str:
        """Create a new lifetime license."""
        
        license_key = self.generate_license_key()
        license_id = str(uuid.uuid4())
        
        # Lifetime license: no expiration
        expires_at = None if duration_days == -1 else datetime.now(timezone.utc) + timedelta(days=duration_days)
        
        # All lifetime licenses get 2 devices
        max_devices = 2
        
        # Get or create user
        user = await self.db.fetch_one(
            "SELECT id FROM users WHERE email = :email",
            {"email": email}
        )
        
        if user:
            user_id = user["id"]
            # Update existing user to lifetime
            await self.db.execute(
                """
                UPDATE users SET 
                    has_lifetime_license = true,
                    updated_at = NOW()
                WHERE id = :id
                """,
                {"id": user_id}
            )
        else:
            user_id = str(uuid.uuid4())
            await self.db.execute(
                """
                INSERT INTO users (id, email, has_lifetime_license, credits_balance, is_active, created_at)
                VALUES (:id, :email, true, 0, true, NOW())
                """,
                {"id": user_id, "email": email}
            )
        
        # Create license
        await self.db.execute(
            """
            INSERT INTO licenses 
            (id, user_id, license_key, is_lifetime, max_devices, expires_at, is_active, created_at, payment_id)
            VALUES (:id, :user_id, :license_key, true, :max_devices, :expires_at, true, NOW(), :payment_id)
            """,
            {
                "id": license_id,
                "user_id": user_id,
                "license_key": license_key,
                "max_devices": max_devices,
                "expires_at": expires_at,
                "payment_id": payment_id
            }
        )
        
        return license_key
    
    async def activate_license(
        self,
        license_id: str,
        email: str,
        hwid: str
    ):
        """Activate a license for first use."""
        
        # Update license
        await self.db.execute(
            """
            UPDATE licenses
            SET activated_at = NOW()
            WHERE id = :license_id
            """,
            {"license_id": license_id}
        )
        
        # Register first device
        await self.register_device(license_id, hwid, "1.0.0")
    
    async def extend_license(
        self,
        license_id: str,
        days: int,
        payment_id: Optional[str] = None
    ):
        """Extend license expiration"""
        
        await self.db.execute(
            """
            UPDATE licenses
            SET expires_at = CASE 
                WHEN expires_at > NOW() THEN expires_at + INTERVAL ':days days'
                ELSE NOW() + INTERVAL ':days days'
            END,
            last_payment_id = :payment_id,
            updated_at = NOW()
            WHERE id = :license_id
            """,
            {"license_id": license_id, "days": days, "payment_id": payment_id}
        )
    
    async def deactivate_license(self, license_id: str, reason: str):
        """Deactivate a license"""
        
        await self.db.execute(
            """
            UPDATE licenses
            SET is_active = false, deactivation_reason = :reason, deactivated_at = NOW()
            WHERE id = :license_id
            """,
            {"license_id": license_id, "reason": reason}
        )
    
    async def mark_for_expiration(self, license_id: str):
        """Mark license to not renew (subscription cancelled)"""
        
        await self.db.execute(
            """
            UPDATE licenses
            SET auto_renew = false
            WHERE id = :license_id
            """,
            {"license_id": license_id}
        )
    
    async def update_plan(self, license_id: str, new_plan: str):
        """Update license plan (legacy - all plans are now lifetime)"""
        max_devices = 2  # All lifetime licenses get 2 devices

        await self.db.execute(
            """
            UPDATE licenses
            SET plan = :plan, max_devices = :max_devices, updated_at = NOW()
            WHERE id = :license_id
            """,
            {"license_id": license_id, "plan": new_plan, "max_devices": max_devices}
        )

    async def activate_lifetime_license(
        self,
        email: str,
        payment_id: Optional[str] = None
    ) -> bool:
        """
        Activate lifetime license for user.
        Called when user purchases a package that includes license.
        """
        # Get user by email
        user = await self.db.fetch_one(
            "SELECT id, has_lifetime_license FROM users WHERE email = :email",
            {"email": email}
        )

        if not user:
            return False

        # Already has license
        if user["has_lifetime_license"]:
            return True

        user_id = user["id"]

        # Activate lifetime license on user
        await self.db.execute(
            """
            UPDATE users
            SET has_lifetime_license = true,
                license_activated_at = NOW()
            WHERE id = :user_id
            """,
            {"user_id": user_id}
        )

        # Log activation in financial_transactions
        await self.db.execute(
            """
            INSERT INTO financial_transactions
            (id, user_id, transaction_type, amount_brl, 
             payment_id, payment_status, description, created_at)
            VALUES (:id, :user_id, 'license_activation', 0, 
                    :payment_id, 'completed', 'Lifetime license activated', NOW())
            """,
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "payment_id": payment_id
            }
        )

        return True

    async def add_credits(
        self,
        email: str,
        amount: int,
        payment_id: Optional[str] = None
    ) -> int:
        """Add credits to user account after payment"""
        # Get user by email
        user = await self.db.fetch_one(
            "SELECT id, credits_balance FROM users WHERE email = :email",
            {"email": email}
        )

        if not user:
            return 0

        user_id = user["id"]
        new_balance = user["credits_balance"] + amount

        # Update user credits
        await self.db.execute(
            """
            UPDATE users
            SET credits_balance = credits_balance + :amount,
                credits_purchased = credits_purchased + :amount
            WHERE id = :user_id
            """,
            {"user_id": user_id, "amount": amount}
        )

        # Log to financial_transactions
        await self.db.execute(
            """
            INSERT INTO financial_transactions
            (id, user_id, transaction_type, amount_brl, credits_amount, 
             payment_id, payment_status, created_at)
            VALUES (:id, :user_id, 'credit_purchase', 0, :amount, 
                    :payment_id, 'completed', NOW())
            """,
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "amount": amount,
                "payment_id": payment_id
            }
        )

        return new_balance
    
    async def get_usage_stats(self, license_id: str) -> dict:
        """Get license usage statistics"""

        result = await self.db.fetch_one(
            """
            SELECT
                l.is_lifetime,
                u.credits_balance,
                (SELECT COUNT(*) FROM license_devices ld
                    WHERE ld.license_id = :license_id
                    AND ld.is_active = true) as active_devices
            FROM licenses l
            JOIN users u ON l.user_id = u.id
            WHERE l.id = :license_id
            """,
            {"license_id": license_id}
        )

        if result:
            return {
                "is_lifetime": result["is_lifetime"],
                "credits": result["credits_balance"],
                "active_devices": result["active_devices"],
                # Lifetime = unlimited everything except credits
                "searches_limit": -1,
                "favorites_limit": -1,
                "exports_limit": -1
            }

        return {}
    
    def create_license_jwt(
        self,
        user_id: str,
        hwid: str,
        is_lifetime: bool,
        expires_at: datetime = None
    ) -> str:
        """Create JWT token for license validation"""
        payload = {
            "sub": user_id,
            "hwid": hwid,
            "is_lifetime": is_lifetime,
            "exp": expires_at if expires_at else datetime.now(timezone.utc) + timedelta(days=365*100),  # 100 years for lifetime
            "iat": datetime.now(timezone.utc),
            "iss": "tiktrend-license-service"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_key_format(self, license_key: str) -> bool:
        """Validate license key format"""
        # Format: XXXX-XXXX-XXXX-XXXX (16 chars + 3 dashes)
        if len(license_key) != 19:
            return False
        
        parts = license_key.split("-")
        if len(parts) != 4:
            return False
        
        for part in parts:
            if len(part) != 4 or not part.isalnum():
                return False
        
        return True
    
    @staticmethod
    def generate_license_key() -> str:
        """Generate a new license key"""
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Exclude confusing chars
        parts = []
        
        for _ in range(4):
            part = "".join(secrets.choice(chars) for _ in range(4))
            parts.append(part)
        
        return "-".join(parts)
    
    @staticmethod
    def get_lifetime_features() -> dict:
        """Get features included in lifetime license"""
        return {
            "unlimited_searches": True,
            "unlimited_favorites": True,
            "unlimited_exports": True,
            "multi_source": True,  # TikTok, AliExpress
            "advanced_filters": True,
            "export_formats": ["csv", "xlsx", "json"],
            "max_devices": 2,
            "free_updates": True,
            "priority_support": False,  # Available as add-on
            "api_access": False,  # Future expansion
            "seller_bot": False  # Requires Premium Bot subscription
        }

    @staticmethod
    def get_premium_bot_features() -> dict:
        """Get features for Premium Bot subscription (R$149.90/month)."""
        return {
            # Includes all lifetime features
            "unlimited_searches": True,
            "unlimited_favorites": True,
            "unlimited_exports": True,
            "multi_source": True,
            "advanced_filters": True,
            "export_formats": ["csv", "xlsx", "json"],
            "max_devices": 3,  # Extra device for bot
            "free_updates": True,
            "priority_support": True,  # Included in Premium
            "api_access": True,  # REST API access
            # Premium Bot exclusive features
            "seller_bot": True,
            "seller_bot_features": {
                "post_products": True,
                "manage_orders": True,
                "reply_messages": True,
                "extract_analytics": True,
                "max_tasks_per_day": 50,
                "max_concurrent_tasks": 2,
                "browser_profiles": 3,
                "ai_powered_responses": True,
            }
        }

    @staticmethod
    def get_plan_features(plan: str) -> dict:
        """Get features for a plan."""
        if plan == "lifetime":
            return LicenseService.get_lifetime_features()

        if plan == "premium_bot":
            return LicenseService.get_premium_bot_features()

        # Legacy plans - all redirect to needing lifetime
        return {
            "unlimited_searches": False,
            "unlimited_favorites": False,
            "unlimited_exports": False,
            "multi_source": False,
            "advanced_filters": False,
            "export_formats": [],
            "max_devices": 0,
            "free_updates": False,
            "priority_support": False,
            "api_access": False,
            "seller_bot": False
        }
