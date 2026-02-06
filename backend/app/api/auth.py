"""
Authentication API Routes
User registration, login, token management
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models.user import User
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
    TokenRefresh,
    PasswordChange
)
from app.core.security import (
    hash_password,
    verify_password,
    create_token_pair,
    decode_token,
    get_current_user,
    get_current_active_user
)
from app.core.sanitizer import sanitizer
from app.core.rate_limiter import limiter


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **password**: Minimum 8 characters with uppercase, lowercase, and digit
    - **full_name**: Optional full name
    - **department**: Optional department
    """
    # Validate email
    if not sanitizer.validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Check if email already exists
    result = await session.execute(
        select(User).where(User.email == user_data.email.lower())
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=user_data.email.lower(),
        hashed_password=hash_password(user_data.password),
        full_name=sanitizer.sanitize_text(user_data.full_name) if user_data.full_name else None,
        department=sanitizer.sanitize_text(user_data.department) if user_data.department else None,
        role="analyst",  # Default role
        is_active=True,
        is_verified=False
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    session: AsyncSession = Depends(get_session)
):
    """
    Login and get access/refresh tokens.
    
    - **email**: Registered email address
    - **password**: Account password
    """
    # Find user
    result = await session.execute(
        select(User).where(User.email == credentials.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await session.commit()
    
    # Create tokens
    tokens = create_token_pair(
        user_id=user.user_id,
        email=user.email,
        role=user.role
    )
    
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    token_data: TokenRefresh,
    session: AsyncSession = Depends(get_session)
):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token from login
    """
    try:
        payload = decode_token(token_data.refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Find user
    user_id = payload.get("sub")
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    tokens = create_token_pair(
        user_id=user.user_id,
        email=user.email,
        role=user.role
    )
    
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Update current user's profile."""
    if update_data.full_name is not None:
        current_user.full_name = sanitizer.sanitize_text(update_data.full_name)
    
    if update_data.department is not None:
        current_user.department = sanitizer.sanitize_text(update_data.department)
    
    await session.commit()
    await session.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Change current user's password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    await session.commit()
    
    return {"success": True, "message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user.
    
    Note: JWT tokens are stateless. This endpoint is for client-side
    token cleanup. Consider implementing token blacklisting for
    enhanced security.
    """
    return {"success": True, "message": "Logged out successfully"}
