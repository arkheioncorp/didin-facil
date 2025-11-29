"""
License Management Routes
Hardware-bound license validation
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from api.middleware.auth import get_current_user
from api.services.license import LicenseService


# JWT settings from environment
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "dev-secret-key-change-in-production"
)

router = APIRouter()


class ValidateLicenseRequest(BaseModel):
    """License validation request"""
    email: EmailStr
    hwid: str  # Hardware ID (CPU + MAC hash)
    app_version: str


class ValidateLicenseResponse(BaseModel):
    """License validation response"""
    valid: bool
    plan: str
    features: dict
    expires_at: Optional[datetime]
    jwt: str
    jwt_expires_at: datetime


class ActivateLicenseRequest(BaseModel):
    """License activation request"""
    license_key: str
    hwid: str
    email: EmailStr


class DeactivateLicenseRequest(BaseModel):
    """License deactivation request (for device transfer)"""
    hwid: str
    reason: Optional[str] = None


class PlanFeatures(BaseModel):
    """Plan features model"""
    name: str
    products_per_day: int
    copies_per_month: int
    favorites_limit: int
    export_formats: list
    priority_support: bool
    api_access: bool


@router.post("/validate", response_model=ValidateLicenseResponse)
async def validate_license(request: ValidateLicenseRequest):
    """
    Validate license and return JWT token.
    Called on app startup and every 12 hours.
    """
    license_service = LicenseService()
    
    # Get license by email
    license_info = await license_service.get_license_by_email(request.email)
    
    if not license_info:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No active license found for this email"
        )
    
    # Check expiration
    # Handle both timezone-aware and naive datetimes from database
    expires_at = license_info["expires_at"]
    if expires_at:
        # If naive datetime, assume UTC
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="License has expired"
            )
    
    # Validate HWID
    hwid_valid = await license_service.validate_hwid(
        license_id=license_info["id"],
        hwid=request.hwid
    )
    
    if not hwid_valid:
        # Security: Do not auto-register devices here.
        # User must use /activate endpoint with the license key to add a new device.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Device not registered. Please use your license key to activate this device.",
                "code": "DEVICE_NOT_REGISTERED"
            }
        )
    
    # Generate JWT
    jwt_expires = datetime.now(timezone.utc) + timedelta(hours=12)
    jwt_token = license_service.create_license_jwt(
        user_id=license_info["user_id"],
        hwid=request.hwid,
        plan=license_info["plan"],
        expires_at=jwt_expires
    )
    
    # Get plan features
    features = license_service.get_plan_features(license_info["plan"])
    
    return ValidateLicenseResponse(
        valid=True,
        plan=license_info["plan"],
        features=features,
        expires_at=license_info["expires_at"],
        jwt=jwt_token,
        jwt_expires_at=jwt_expires
    )


@router.post("/activate")
async def activate_license(request: ActivateLicenseRequest):
    """
    Activate a license key for first time use.
    Binds the license to email and first device.
    """
    license_service = LicenseService()
    
    # Validate license key format
    if not license_service.validate_key_format(request.license_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid license key format"
        )
    
    # Check if key exists
    license_info = await license_service.get_license_by_key(request.license_key)
    
    if not license_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License key not found"
        )
    
    # Scenario 1: First time activation
    if not license_info["activated_at"]:
        # Activate license
        await license_service.activate_license(
            license_id=license_info["id"],
            email=request.email,
            hwid=request.hwid
        )
        return {
            "message": "License activated successfully",
            "plan": license_info["plan"],
            "expires_at": license_info["expires_at"]
        }

    # Scenario 2: Adding a new device to existing license
    # Verify email matches
    user_license = await license_service.get_license_by_email(request.email)
    if not user_license or user_license["id"] != license_info["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="License key does not match the provided email"
        )

    # Check if device is already registered
    is_registered = await license_service.validate_hwid(license_info["id"], request.hwid)
    if is_registered:
        return {
            "message": "Device already registered",
            "plan": license_info["plan"],
            "expires_at": license_info["expires_at"]
        }

    # Check device limits
    active_devices = await license_service.get_active_devices(license_info["id"])
    if len(active_devices) >= license_info["max_devices"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Maximum devices reached. Deactivate another device first.",
                "active_devices": len(active_devices),
                "max_devices": license_info["max_devices"]
            }
        )

    # Register new device
    # We need to pass app_version, but it's not in ActivateLicenseRequest
    # We'll default to "1.0.0" or update the request model
    await license_service.register_device(
        license_id=license_info["id"],
        hwid=request.hwid,
        app_version="1.0.0" 
    )

    return {
        "message": "New device registered successfully",
        "plan": license_info["plan"],
        "expires_at": license_info["expires_at"]
    }


@router.post("/deactivate")
async def deactivate_device(
    request: DeactivateLicenseRequest,
    user: dict = Depends(get_current_user),
):
    """
    Deactivate a device from the license.
    Allows transferring license to a new device.
    """
    license_service = LicenseService()
    
    # Get user's license
    license_info = await license_service.get_license_by_user(user["id"])
    
    if not license_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No license found"
        )
    
    # Deactivate device
    success = await license_service.deactivate_device(
        license_id=license_info["id"],
        hwid=request.hwid,
        reason=request.reason
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found in active devices"
        )
    
    return {"message": "Device deactivated successfully"}


@router.get("/status")
async def get_license_status(user: dict = Depends(get_current_user)):
    """Get current license status and usage"""
    license_service = LicenseService()
    
    license_info = await license_service.get_license_by_user(user["id"])
    
    if not license_info:
        return {
            "has_license": False,
            "plan": "free",
            "features": license_service.get_plan_features("free")
        }
    
    usage = await license_service.get_usage_stats(license_info["id"])
    devices = await license_service.get_active_devices(license_info["id"])
    
    return {
        "has_license": True,
        "plan": license_info["plan"],
        "expires_at": license_info["expires_at"],
        "features": license_service.get_plan_features(license_info["plan"]),
        "usage": usage,
        "devices": {
            "active": len(devices),
            "max": license_info["max_devices"]
        }
    }


@router.get("/plans")
async def get_available_plans():
    """Get all available plans and their features"""
    license_service = LicenseService()
    
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "features": license_service.get_plan_features("free"),
                "description": "Para testar a plataforma"
            },
            {
                "id": "starter",
                "name": "Starter",
                "price": 29.90,
                "features": license_service.get_plan_features("starter"),
                "description": "Para iniciantes no dropshipping"
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 79.90,
                "features": license_service.get_plan_features("pro"),
                "description": "Para escalar suas vendas"
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": 199.90,
                "features": license_service.get_plan_features("enterprise"),
                "description": "Para grandes operações"
            }
        ]
    }
