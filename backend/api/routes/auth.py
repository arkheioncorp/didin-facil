"""Authentication Routes
JWT-based authentication for desktop app

Uses centralized security configuration from shared/security_config.py
"""

from datetime import datetime, timedelta, timezone

from api.middleware.auth import get_current_user
from api.services.auth import AuthService
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from shared.security_config import get_security_config

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
async def register(request: RegisterRequest):
    """Register a new user account"""
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

    return {"message": "User created successfully", "user_id": user["id"]}


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
        user_id = payload.get("sub")
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
        token = auth_service.create_token(
            str(user_id), request.hwid, expires_at
        )

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
    """Verify email address"""
    # Stub implementation
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Request password reset"""
    # Stub implementation
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password"""
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )
    # Stub implementation
    return {"message": "Password reset successfully"}
