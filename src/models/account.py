"""Pydantic v2 schemas and DTOs for the bank account domain.

Defines all request/response models for bank account lifecycle:
creation, update, closure, and retrieval.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AccountType(str, Enum):
    """Supported bank account types."""

    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"


class AccountStatus(str, Enum):
    """Lifecycle status of a bank account.

    ACTIVE – account is operational.
    CLOSED – soft-deleted; visible only to bank employees.
    """

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class AccountCreate(BaseModel):
    """Request body for opening a new bank account.

    The account number is server-generated; callers must not supply it.
    """

    account_type: AccountType = Field(..., description="Type of bank account to open.")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    initial_deposit: Decimal = Field(default=Decimal("0.00"), ge=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "account_type": "SAVINGS",
                "currency": "USD",
                "initial_deposit": 500.00,
            }
        }
    }


class AccountUpdate(BaseModel):
    """Request body for updating mutable fields of an active bank account."""

    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)

    model_config = {"json_schema_extra": {"example": {"currency": "EUR"}}}


class AccountCloseRequest(BaseModel):
    """Request body for closing (soft-deleting) a bank account."""

    closure_reason: str = Field(..., min_length=5, max_length=500)

    model_config = {
        "json_schema_extra": {
            "example": {"closure_reason": "Customer requested account closure."}
        }
    }


class AccountResponse(BaseModel):
    """Account representation returned to the account owner.

    Excludes soft-delete metadata (closure_reason, is_deleted).
    """

    account_number: str = Field(..., description="Unique 10-digit account number (primary key).")
    owner_id: str = Field(..., description="JWT sub of the account owner.")
    account_type: AccountType
    status: AccountStatus
    balance: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AccountBalanceResponse(BaseModel):
    """Balance snapshot for a specific account type — ISO 20022 aligned.

    Models the BankToCustomerAccountReport balance element with
    ``available_balance`` (CLAV — closing available) and a point-in-time
    ``as_of`` timestamp so consumers can detect stale data.
    """

    account_number: str = Field(..., description="Unique 10-digit account number.")
    account_type: AccountType = Field(..., description="Type of the queried account.")
    available_balance: Decimal = Field(
        ...,
        description="Current available/cleared balance (ISO 20022 CLAV, ≥ 0).",
    )
    currency: str = Field(..., description="ISO 4217 three-letter currency code.")
    status: AccountStatus = Field(..., description="Operational status of the account.")
    as_of: datetime = Field(
        ...,
        description="UTC timestamp at which the balance was captured (ISO 8601).",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "account_number": "4820193756",
                "account_type": "SAVINGS",
                "available_balance": "1250.75",
                "currency": "USD",
                "status": "ACTIVE",
                "as_of": "2026-03-19T10:30:00Z",
            }
        },
    }


class AccountAdminResponse(AccountResponse):
    """Extended account view returned to authorised bank employees.

    Adds soft-delete metadata not visible in the customer-facing response.
    """

    is_deleted: bool = Field(..., description="True when the account has been soft-deleted.")
    closure_reason: Optional[str] = None

    model_config = {"from_attributes": True}
