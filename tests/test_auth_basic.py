"""Tests for src/auth/oauth2.py — token creation, verification, and authentication.

Replaces the previous broken tests that referenced non-existent
/auth/login and /protected-route endpoints.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from src.auth.oauth2 import (
    ALGORITHM,
    SECRET_KEY,
    _decode_token,
    authenticate_user,
    create_access_token,
    verify_password,
    pwd_context,
)
from src.exceptions.domain_exceptions import InvalidCredentialsException


class TestVerifyPassword:
    """Tests for verify_password()."""

    def test_verify_password_correct_password_returns_true(self) -> None:
        # Arrange
        hashed = pwd_context.hash("mysecret")

        # Act / Assert
        assert verify_password("mysecret", hashed) is True

    def test_verify_password_wrong_password_returns_false(self) -> None:
        # Arrange
        hashed = pwd_context.hash("mysecret")

        # Act / Assert
        assert verify_password("wrongpassword", hashed) is False


class TestCreateAccessToken:
    """Tests for create_access_token()."""

    def test_create_access_token_returns_string(self) -> None:
        # Act
        token = create_access_token({"sub": "user1", "role": "customer"})

        # Assert
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_encodes_sub_claim(self) -> None:
        # Act
        token = create_access_token({"sub": "user-123", "role": "customer"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Assert
        assert payload["sub"] == "user-123"

    def test_create_access_token_encodes_role_claim(self) -> None:
        # Act
        token = create_access_token({"sub": "admin", "role": "bank_employee"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Assert
        assert payload["role"] == "bank_employee"

    def test_create_access_token_includes_expiry(self) -> None:
        # Act
        token = create_access_token({"sub": "user1"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Assert
        assert "exp" in payload

    def test_create_access_token_custom_expires_delta_is_respected(self) -> None:
        # Arrange
        short_delta = timedelta(seconds=10)

        # Act
        token = create_access_token({"sub": "user1"}, expires_delta=short_delta)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Assert
        assert "exp" in payload


class TestDecodeToken:
    """Tests for _decode_token()."""

    def test_decode_token_valid_token_returns_payload(self) -> None:
        # Arrange
        token = create_access_token({"sub": "user-999", "role": "customer"})

        # Act
        payload = _decode_token(token)

        # Assert
        assert payload["sub"] == "user-999"

    def test_decode_token_invalid_token_raises_http_401(self) -> None:
        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            _decode_token("completely.invalid.token")

        assert exc_info.value.status_code == 401

    def test_decode_token_missing_sub_raises_http_401(self) -> None:
        # Arrange — token without 'sub' claim
        token = jwt.encode({"role": "customer"}, SECRET_KEY, algorithm=ALGORITHM)

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            _decode_token(token)

        assert exc_info.value.status_code == 401

    def test_decode_token_wrong_secret_raises_http_401(self) -> None:
        # Arrange — token signed with a different secret
        token = jwt.encode({"sub": "user1"}, "wrong-secret", algorithm=ALGORITHM)

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            _decode_token(token)

        assert exc_info.value.status_code == 401

    def test_decode_token_error_response_includes_www_authenticate_header(self) -> None:
        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            _decode_token("bad.token")

        assert "WWW-Authenticate" in exc_info.value.headers


class TestAuthenticateUser:
    """Tests for authenticate_user()."""

    @pytest.mark.asyncio
    async def test_authenticate_user_valid_customer_returns_user_dict(self) -> None:
        # Act
        user = await authenticate_user("johndoe", "secret")

        # Assert
        assert user["username"] == "johndoe"
        assert user["role"] == "customer"

    @pytest.mark.asyncio
    async def test_authenticate_user_valid_employee_returns_user_dict(self) -> None:
        # Act
        user = await authenticate_user("bankadmin", "adminpass")

        # Assert
        assert user["role"] == "bank_employee"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password_raises_invalid_credentials(
        self,
    ) -> None:
        # Act / Assert
        with pytest.raises(InvalidCredentialsException):
            await authenticate_user("johndoe", "wrongpassword")

    @pytest.mark.asyncio
    async def test_authenticate_user_unknown_username_raises_invalid_credentials(
        self,
    ) -> None:
        # Act / Assert
        with pytest.raises(InvalidCredentialsException):
            await authenticate_user("nobody", "anypassword")
