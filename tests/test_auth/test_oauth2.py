"""Deeper unit tests for src/auth/oauth2.py.

Covers jwt dependency functions (get_current_user, require_bank_employee)
by isolating them from FastAPI routing using direct async invocation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from jose import jwt

from src.auth.oauth2 import (
    ALGORITHM,
    ROLE_BANK_EMPLOYEE,
    SECRET_KEY,
    _decode_token,
    create_access_token,
    get_current_user,
    require_bank_employee,
)


class TestGetCurrentUser:
    """Tests for get_current_user FastAPI dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token_returns_payload(self) -> None:
        # Arrange
        token = create_access_token({"sub": "user-1", "role": "customer"})

        # Act
        result = await get_current_user(token=token)

        # Assert
        assert result["sub"] == "user-1"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_raises_401(self) -> None:
        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="garbage.token.value")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_returns_full_payload_dict(self) -> None:
        # Arrange
        token = create_access_token({"sub": "user-2", "role": "bank_employee"})

        # Act
        result = await get_current_user(token=token)

        # Assert
        assert result["role"] == "bank_employee"
        assert "exp" in result


class TestRequireBankEmployee:
    """Tests for require_bank_employee FastAPI dependency."""

    @pytest.mark.asyncio
    async def test_require_bank_employee_correct_role_returns_user(self) -> None:
        # Arrange
        employee = {"sub": "emp-1", "role": ROLE_BANK_EMPLOYEE}

        # Act
        result = await require_bank_employee(current_user=employee)

        # Assert
        assert result["sub"] == "emp-1"

    @pytest.mark.asyncio
    async def test_require_bank_employee_customer_role_raises_403(self) -> None:
        # Arrange
        customer = {"sub": "cust-1", "role": "customer"}

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await require_bank_employee(current_user=customer)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_bank_employee_missing_role_raises_403(self) -> None:
        # Arrange
        user_no_role = {"sub": "user-3"}

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await require_bank_employee(current_user=user_no_role)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_bank_employee_403_message_describes_role(self) -> None:
        # Arrange
        customer = {"sub": "c", "role": "customer"}

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await require_bank_employee(current_user=customer)

        assert (
            "bank_employee" in exc_info.value.detail.lower()
            or "employee" in exc_info.value.detail.lower()
        )
