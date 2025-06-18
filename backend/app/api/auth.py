"""Authentication routes for the API."""

from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_user_by_email,
    verify_password,
)
from app.db.session import get_session
from app.schemas import Token


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


router = APIRouter()


@router.post("/login", response_model=Token)
def login(data: LoginRequest, session: Session = Depends(get_session)) -> Token:
    """Authenticate a user and issue JWT tokens."""

    user = get_user_by_email(data.email, session)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return Token(access_token=access_token, refresh_token=refresh_token)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=Token)
def refresh_token(data: RefreshRequest) -> Token:
    """Issue a new access token given a valid refresh token."""

    from jose import JWTError, jwt
    from app.core.config import settings

    try:
        payload = jwt.decode(data.refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    # In a real system you would validate token revocation here
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    return Token(access_token=access_token, refresh_token=refresh_token)