"""
auth.py — Authentication endpoints for NyayaSaathi backend.
Routes under /api/auth:
  - POST /register
  - POST /login
  - GET /me
  - POST /google
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.database_models import User
from app.models.auth_schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    GoogleAuthRequest,
    UserResponse,
    AuthResponse,
)
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    verify_google_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to extract and validate the current authenticated user from Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/register", response_model=AuthResponse)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account with email and password."""
    normalized_email = request.email.strip().lower()
    
    # Check for duplicate user
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )
    
    hashed_pwd = hash_password(request.password)
    
    new_user = User(
        name=request.name.strip(),
        email=normalized_email,
        password_hash=hashed_pwd,
        auth_provider="local",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token({"sub": str(new_user.id)})
    user_resp = UserResponse.model_validate(new_user)
    
    return AuthResponse(
        success=True,
        access_token=token,
        token_type="bearer",
        user=user_resp,
    )


@router.post("/login", response_model=AuthResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate an existing user with email and password."""
    normalized_email = request.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    
    if not user or not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token({"sub": str(user.id)})
    user_resp = UserResponse.model_validate(user)
    
    return AuthResponse(
        success=True,
        access_token=token,
        token_type="bearer",
        user=user_resp,
    )


@router.get("/me", response_model=dict)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the profile details of the currently authenticated user."""
    user_resp = UserResponse.model_validate(current_user)
    return {
        "success": True,
        "user": user_resp,
    }


@router.post("/google", response_model=AuthResponse)
def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate or register a user using a Google OAuth ID Token credential."""
    try:
        google_data = verify_google_token(request.credential)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    google_sub = google_data.get("sub")
    email = google_data.get("email")
    name = google_data.get("name") or google_data.get("given_name") or "Google User"
    picture = google_data.get("picture")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account did not return a valid email address.",
        )
    
    normalized_email = email.strip().lower()
    
    # 1. Search by google_sub first
    user = db.query(User).filter(User.google_sub == google_sub).first()
    
    if not user:
        # 2. Search by email if not found by google_sub
        user = db.query(User).filter(User.email == normalized_email).first()
        if user:
            # Link existing user account with Google ID
            user.google_sub = google_sub
            if not user.profile_picture_url and picture:
                user.profile_picture_url = picture
            if user.auth_provider == "local":
                user.auth_provider = "hybrid"
            db.commit()
            db.refresh(user)
        else:
            # Create new user record for Google user
            user = User(
                name=name,
                email=normalized_email,
                password_hash=None,
                auth_provider="google",
                google_sub=google_sub,
                profile_picture_url=picture,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    else:
        # Update picture or name if changed in Google
        if picture and user.profile_picture_url != picture:
            user.profile_picture_url = picture
            db.commit()
            db.refresh(user)
    
    token = create_access_token({"sub": str(user.id)})
    user_resp = UserResponse.model_validate(user)
    
    return AuthResponse(
        success=True,
        access_token=token,
        token_type="bearer",
        user=user_resp,
    )
