"""OAuth 2.0 authentication and authorisation helpers.

Provides:
  - Bearer token validation via FastAPI Depends().
  - get_current_user: extracts the authenticated user context from JWT.
  - require_bank_employee: enforces bank_employee role for admin endpoints.

JWT payload expected fields:
  sub   (str)  — unique user identifier.
  role  (str)  — 'customer' | 'bank_employee'.
  exp   (int)  — expiry timestamp.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from src.exceptions.domain_exceptions import (
    InvalidCredentialsException,
)

# ── Configuration ─────────────────────────────────────────────────────────────
# SECRET_KEY is read from the JWT_SECRET_KEY environment variable.
# For local dev set it in .env; for production inject via Azure Key Vault / Container Apps secret.
SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "local-dev-insecure-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "30"))
ROLE_BANK_EMPLOYEE = "bank_employee"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ── Token helpers ─────────────────────────────────────────────────────────────


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash.

    Args:
        plain_password: The raw password supplied by the user.
        hashed_password: The stored bcrypt hash.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Encode a JWT access token.

    Args:
        data: Payload claims to include (must contain 'sub' and 'role').
        expires_delta: Custom expiry window; defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Signed JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    """Decode and validate a JWT Bearer token.

    Args:
        token: Raw JWT string from the Authorization header.

    Returns:
        Decoded payload dict.

    Raises:
        HTTPException 401: If the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload: dict = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") is None:
            raise credentials_exception
        return payload
    except jwt.PyJWTError as exc:
        raise credentials_exception from exc


# ── FastAPI dependency functions ──────────────────────────────────────────────


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    """FastAPI dependency: validate Bearer token and return user context.

    Args:
        token: JWT extracted from the Authorization header by oauth2_scheme.

    Returns:
        Decoded JWT payload dict (contains at minimum 'sub' and 'role').

    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
    """
    return _decode_token(token)


async def require_bank_employee(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """FastAPI dependency: enforce bank_employee role.

    Use this as a dependency on admin-only endpoints. Composes on top of
    get_current_user so both authentication and authorisation are checked.

    Args:
        current_user: Injected by get_current_user.

    Returns:
        The current user dict if they hold the bank_employee role.

    Raises:
        HTTPException 403: If the user does not have the bank_employee role.
    """
    if current_user.get("role") != ROLE_BANK_EMPLOYEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bank employee role required.",
        )
    return current_user


# ── Dummy user store (dev/test only) ──────────────────────────────────────────
# Replace with a real user service backed by Cosmos DB or Entra ID.

@lru_cache(maxsize=1)
def _get_fake_users_db() -> dict[str, dict[str, object]]:
    """Return an in-memory user store for dev/test.

    This is intentionally lazy to avoid doing password hashing at import time,
    which can cause container startup failures when crypto backends are
    misconfigured.

    Returns:
        Dict keyed by username.
    """
    return {
        "johndoe": {
            "username": "johndoe",
            "email": "johndoe@example.com",
            "hashed_password": pwd_context.hash("secret"),
            "role": "customer",
            "disabled": False,
        },
        "bankadmin": {
            "username": "bankadmin",
            "email": "admin@bank.com",
            "hashed_password": pwd_context.hash("adminpass"),
            "role": ROLE_BANK_EMPLOYEE,
            "disabled": False,
        },
    }


async def authenticate_user(username: str, password: str) -> dict:
    """Authenticate a user against the dummy store.

    Args:
        username: Supplied username.
        password: Supplied plaintext password.

    Returns:
        User record dict on success.

    Raises:
        InvalidCredentialsException: If username or password is wrong.
    """
    user = _get_fake_users_db().get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        raise InvalidCredentialsException()
    return user
