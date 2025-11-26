"""
License Service
License management and validation
"""

import uuid
import secrets
from datetime import datetime, timedelta
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
        plan: str,
        duration_days: int = 30,
        payment_id: Optional[str] = None
    ) -> str:
        """Create a new license."""
        
        license_key = self.generate_license_key()
        license_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=duration_days)
        
        max_devices = {
            "free": 1,
            "starter": 2,
            "pro": 3,
            "enterprise": 5
        }.get(plan, 1)
        
        # Get or create user
        user = await self.db.fetch_one(
            "SELECT id FROM users WHERE email = :email",
            {"email": email}
        )
        
        if user:
            user_id = user["id"]
        else:
            user_id = str(uuid.uuid4())
            await self.db.execute(
                """
                INSERT INTO users (id, email, plan, is_active, created_at)
                VALUES (:id, :email, :plan, true, NOW())
                """,
                {"id": user_id, "email": email, "plan": plan}
            )
        
        # Create license
        await self.db.execute(
            """
            INSERT INTO licenses 
            (id, user_id, license_key, plan, max_devices, expires_at, is_active, created_at, payment_id)
            VALUES (:id, :user_id, :license_key, :plan, :max_devices, :expires_at, true, NOW(), :payment_id)
            """,
            {
                "id": license_id,
                "user_id": user_id,
                "license_key": license_key,
                "plan": plan,
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
        """Update license plan"""
        max_devices = {
            "free": 1,
            "starter": 2,
            "pro": 3,
            "enterprise": 5
        }.get(new_plan, 1)
        
        await self.db.execute(
            """
            UPDATE licenses
            SET plan = :plan, max_devices = :max_devices, updated_at = NOW()
            WHERE id = :license_id
            """,
            {"license_id": license_id, "plan": new_plan, "max_devices": max_devices}
        )
    
    async def get_usage_stats(self, license_id: str) -> dict:
        """Get license usage statistics"""
        
        result = await self.db.fetch_one(
            """
            SELECT 
                l.plan,
                (SELECT COUNT(*) FROM copy_history ch 
                    JOIN users u ON ch.user_id = u.id 
                    JOIN licenses l2 ON l2.user_id = u.id 
                    WHERE l2.id = :license_id 
                    AND ch.created_at >= date_trunc('month', CURRENT_DATE)) as copies_this_month,
                (SELECT COUNT(*) FROM license_devices ld 
                    WHERE ld.license_id = :license_id AND ld.is_active = true) as active_devices
            FROM licenses l
            WHERE l.id = :license_id
            """,
            {"license_id": license_id}
        )
        
        plan_limits = {
            "free": {"copies": 5, "products": 10},
            "starter": {"copies": 50, "products": 100},
            "pro": {"copies": 200, "products": 500},
            "enterprise": {"copies": 1000, "products": -1}  # -1 = unlimited
        }
        
        if result:
            limits = plan_limits.get(result["plan"], plan_limits["free"])
            return {
                "copies_used": result["copies_this_month"],
                "copies_limit": limits["copies"],
                "products_limit": limits["products"],
                "active_devices": result["active_devices"]
            }
        
        return {}
    
    def create_license_jwt(
        self,
        user_id: str,
        hwid: str,
        plan: str,
        expires_at: datetime
    ) -> str:
        """Create JWT token for license validation"""
        payload = {
            "sub": user_id,
            "hwid": hwid,
            "plan": plan,
            "exp": expires_at,
            "iat": datetime.utcnow(),
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
    def get_plan_features(plan: str) -> dict:
        """Get features for a plan"""
        features = {
            "free": {
                "products_per_day": 10,
                "copies_per_month": 5,
                "favorites_limit": 10,
                "export_formats": ["csv"],
                "priority_support": False,
                "api_access": False,
                "trending_alerts": False,
                "advanced_filters": False
            },
            "starter": {
                "products_per_day": 100,
                "copies_per_month": 50,
                "favorites_limit": 100,
                "export_formats": ["csv", "xlsx"],
                "priority_support": False,
                "api_access": False,
                "trending_alerts": True,
                "advanced_filters": True
            },
            "pro": {
                "products_per_day": 500,
                "copies_per_month": 200,
                "favorites_limit": 500,
                "export_formats": ["csv", "xlsx", "json"],
                "priority_support": True,
                "api_access": False,
                "trending_alerts": True,
                "advanced_filters": True
            },
            "enterprise": {
                "products_per_day": -1,  # Unlimited
                "copies_per_month": 1000,
                "favorites_limit": -1,  # Unlimited
                "export_formats": ["csv", "xlsx", "json", "api"],
                "priority_support": True,
                "api_access": True,
                "trending_alerts": True,
                "advanced_filters": True
            }
        }
        
        return features.get(plan, features["free"])
