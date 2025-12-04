"""Authentication Routes
JWT-based authentication for desktop app

Uses centralized security configuration from shared/security_config.py
"""

import logging
from datetime import datetime, timedelta, timezone

from api.middleware.auth import get_current_user
from api.services.auth import AuthService
from api.services.email import get_email_service
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from shared.security_config import get_security_config

logger = logging.getLogger(__name__)

# Get security configuration (cached singleton)
_security = get_security_config()
JWT_SECRET_KEY = _security.jwt_secret_key
JWT_ALGORITHM = _security.jwt_algorithm


router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model"""

    email: EmailStr
    password: str
    hwid: str  # Hardware ID for license binding


class LoginResponse(BaseModel):
    """Login response model"""

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: dict


class RegisterRequest(BaseModel):
    """Registration request model"""

    email: EmailStr
    password: str
    name: str


class RefreshRequest(BaseModel):
    """Token refresh request"""

    hwid: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request"""

    token: str
    new_password: str
    confirm_password: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    Token is bound to hardware ID for license validation.
    """
    auth_service = AuthService()

    user = await auth_service.authenticate(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Validate HWID for license
    if not await auth_service.validate_hwid(user["id"], request.hwid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This license is bound to another device",
        )

    # Generate token
    expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
    token = auth_service.create_token(user["id"], request.hwid, expires_at)

    return LoginResponse(
        access_token=token,
        expires_at=expires_at,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "plan": user["plan"],
        },
    )


@router.post("/register")
async def register(
    request: RegisterRequest,
    background_tasks: BackgroundTasks
):
    """Register a new user account and send verification email"""
    auth_service = AuthService()

    # Check if user exists
    existing = await auth_service.get_user_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = await auth_service.create_user(
        email=request.email, password=request.password, name=request.name
    )

    # Generate verification token
    verification_token = await auth_service.create_verification_token(user["id"])

    # Send verification email in background
    async def send_verification():
        try:
            email_service = get_email_service()
            await email_service.send_verification_email(
                to=request.email,
                name=request.name,
                verification_token=verification_token
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")

    background_tasks.add_task(send_verification)

    return {
        "message": "User created successfully. Check your email for verification.",
        "user_id": user["id"]
    }


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: RefreshRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Refresh JWT token"""
    auth_service = AuthService()

    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        # Verify HWID matches
        if payload.get("hwid") != request.hwid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HWID mismatch",
            )

        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Generate new token
        expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
        token = auth_service.create_token(user_id, request.hwid, expires_at)

        return LoginResponse(
            access_token=token,
            expires_at=expires_at,
            user={
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "plan": user["plan"],
            },
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


@router.get("/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return user


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    Logout user (invalidate token on client side).
    Server-side token invalidation can be implemented with Redis blacklist.
    """
    # TODO: Add token to Redis blacklist for server-side invalidation
    return {"message": "Logged out successfully"}


@router.get("/verify-email")
async def verify_email(token: str):
    """Verify email address using token from verification email"""
    auth_service = AuthService()

    user = await auth_service.verify_email_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # Send welcome email (optional, best effort)
    try:
        email_service = get_email_service()
        await email_service.send_welcome(
            to=user["email"],
            name=user["name"]
        )
    except Exception as e:
        logger.warning(f"Failed to send welcome email: {e}")

    return {
        "message": "Email verified successfully",
        "email": user["email"]
    }


@router.post("/resend-verification")
async def resend_verification(
    request: ForgotPasswordRequest,  # Reusing model (just needs email)
    background_tasks: BackgroundTasks
):
    """Resend verification email"""
    auth_service = AuthService()

    user = await auth_service.get_user_by_email(request.email)

    if not user:
        # Don't reveal if user exists
        return {"message": "If the email exists, a verification link was sent"}

    # Check if already verified
    if await auth_service.is_email_verified(str(user["id"])):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified",
        )

    # Generate new verification token
    token = await auth_service.create_verification_token(str(user["id"]))

    # Send email in background
    async def send_email():
        try:
            email_service = get_email_service()
            await email_service.send_verification_email(
                to=user["email"],
                name=user["name"],
                verification_token=token
            )
        except Exception as e:
            logger.error(f"Failed to resend verification email: {e}")

    background_tasks.add_task(send_email)

    return {"message": "If the email exists, a verification link was sent"}


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks
):
    """Request password reset - sends email with reset link"""
    auth_service = AuthService()

    # Create reset token (returns None if user doesn't exist)
    reset_token = await auth_service.create_reset_token(request.email)

    # Always return success to not reveal if email exists
    if reset_token:
        # Get user info for email
        user = await auth_service.get_user_by_email(request.email)

        # Send reset email in background
        async def send_reset():
            try:
                email_service = get_email_service()
                await email_service.send_password_reset(
                    to=request.email,
                    name=user["name"] if user else "User",
                    reset_token=reset_token
                )
            except Exception as e:
                logger.error(f"Failed to send password reset email: {e}")

        background_tasks.add_task(send_reset)

    return {
        "message": "If the email is registered, a password reset link was sent"
    }


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password using token from email"""
    auth_service = AuthService()

    # Validate passwords match
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    # Validate password strength
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    # Reset password
    success = await auth_service.reset_password_with_token(
        token=request.token,
        new_password=request.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    return {"message": "Password reset successfully"}
