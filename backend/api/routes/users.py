from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from api.middleware.auth import get_current_user
from api.database.connection import database
from passlib.context import CryptContext
from datetime import datetime

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserProfileUpdate(BaseModel):
    """Update user profile fields"""
    name: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    """Update user password"""
    current_password: str
    new_password: str


class UserProfileResponse(BaseModel):
    """User profile response model - aligned with frontend types"""
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    # License status
    has_lifetime_license: bool = False
    license_activated_at: Optional[datetime] = None
    # Account status
    is_active: bool = True
    is_email_verified: bool = False
    # Preferences
    language: str = "pt-BR"
    timezone: str = "America/Sao_Paulo"
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LicenseResponse(BaseModel):
    """License information response"""
    id: Optional[str] = None
    is_valid: bool = False
    is_lifetime: bool = False
    plan: str = "free"  # free | trial | lifetime
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    max_devices: int = 1
    active_devices: int = 0
    current_device_id: Optional[str] = None
    is_current_device_authorized: bool = False


class CreditsResponse(BaseModel):
    """Credits information response"""
    balance: int = 0
    total_purchased: int = 0
    total_used: int = 0
    last_purchase_at: Optional[datetime] = None
    bonus_balance: int = 0
    bonus_expires_at: Optional[datetime] = None


class FullProfileResponse(BaseModel):
    """Complete profile with user, license and credits"""
    user: UserProfileResponse
    license: LicenseResponse
    credits: CreditsResponse


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    query = """
        SELECT 
            u.id, u.email, u.name, u.avatar_url, u.phone,
            u.is_active, u.is_email_verified,
            u.language, u.timezone,
            u.created_at, u.updated_at, u.last_login_at,
            CASE WHEN l.plan = 'lifetime' THEN true ELSE false END as has_lifetime_license,
            l.activated_at as license_activated_at
        FROM users u
        LEFT JOIN licenses l ON l.user_id = u.id AND l.is_active = true
        WHERE u.id = :id
    """
    user = await database.fetch_one(query, {"id": current_user["id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me/full", response_model=FullProfileResponse)
async def get_full_profile(current_user: dict = Depends(get_current_user)):
    """Get complete profile with license and credits"""
    # Get user
    user_query = """
        SELECT 
            u.id, u.email, u.name, u.avatar_url, u.phone,
            u.is_active, u.is_email_verified,
            u.language, u.timezone,
            u.created_at, u.updated_at, u.last_login_at,
            CASE WHEN l.plan = 'lifetime' THEN true ELSE false END as has_lifetime_license,
            l.activated_at as license_activated_at
        FROM users u
        LEFT JOIN licenses l ON l.user_id = u.id AND l.is_active = true
        WHERE u.id = :id
    """
    user = await database.fetch_one(user_query, {"id": current_user["id"]})
    
    # Get license
    license_query = """
        SELECT 
            l.id::text, l.plan, l.is_active as is_valid,
            CASE WHEN l.plan = 'lifetime' THEN true ELSE false END as is_lifetime,
            l.activated_at, l.expires_at, l.max_devices,
            (SELECT COUNT(*) FROM license_devices ld WHERE ld.license_id = l.id AND ld.is_active = true) as active_devices
        FROM licenses l
        WHERE l.user_id = :user_id AND l.is_active = true
        LIMIT 1
    """
    license_data = await database.fetch_one(license_query, {"user_id": current_user["id"]})
    
    # Get credits
    credits_query = """
        SELECT 
            COALESCE(credits_balance, 0) as balance,
            COALESCE(credits_purchased, 0) as total_purchased,
            COALESCE(credits_used, 0) as total_used,
            last_purchase_at,
            COALESCE(bonus_balance, 0) as bonus_balance,
            bonus_expires_at
        FROM users
        WHERE id = :user_id
    """
    credits_data = await database.fetch_one(
        credits_query,
        {"user_id": current_user["id"]}
    )
    
    return {
        "user": user,
        "license": license_data or LicenseResponse(),
        "credits": credits_data or CreditsResponse()
    }


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile"""
    updates = []
    params = {"id": current_user["id"]}
    
    if profile_update.name is not None:
        updates.append("name = :name")
        params["name"] = profile_update.name
        
    if profile_update.phone is not None:
        updates.append("phone = :phone")
        params["phone"] = profile_update.phone
        
    if profile_update.language is not None:
        updates.append("language = :language")
        params["language"] = profile_update.language
        
    if profile_update.timezone is not None:
        updates.append("timezone = :timezone")
        params["timezone"] = profile_update.timezone
    
    if updates:
        updates.append("updated_at = NOW()")
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = :id RETURNING *"
        user = await database.fetch_one(query, params)
        return user
    
    # If no updates, return current user
    return await get_my_profile(current_user)

@router.put("/me/password")
async def update_my_password(
    password_update: UserPasswordUpdate,
    current_user: dict = Depends(get_current_user)
):
    query = "SELECT password_hash FROM users WHERE id = :id"
    user_db = await database.fetch_one(query, {"id": current_user["id"]})
    
    if not pwd_context.verify(password_update.current_password, user_db["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    new_hash = pwd_context.hash(password_update.new_password)
    update_query = "UPDATE users SET password_hash = :hash WHERE id = :id"
    await database.execute(update_query, {"hash": new_hash, "id": current_user["id"]})
    
    return {"message": "Password updated successfully"}
