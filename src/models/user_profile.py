"""Pydantic v2 schemas and DTOs for the user profile domain.

Defines all request/response models for user profile lifecycle:
retrieval and partial update (PATCH semantics).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Address(BaseModel):
    """Physical postal address associated with a user profile.

    Attributes:
        line1: Primary street address line (required, max 100 chars).
        line2: Secondary address line, e.g. apartment number (optional, max 100 chars).
        city: City or town name (required, max 50 chars).
        state: State, province, or region (required, max 50 chars).
        postal_code: Postal / ZIP code matching alphanumeric + space/hyphen pattern.
        country: ISO 3166-1 alpha-2 two-letter uppercase country code.
    """

    line1: str = Field(..., max_length=100, description="Primary street address line.")
    line2: Optional[str] = Field(
        default=None, max_length=100, description="Secondary address line."
    )
    city: str = Field(..., max_length=50, description="City or town.")
    state: str = Field(..., max_length=50, description="State or province.")
    postal_code: str = Field(
        ...,
        pattern=r"^[A-Za-z0-9 \-]{3,10}$",
        description="Postal/ZIP code (3–10 alphanumeric chars, spaces and hyphens allowed).",
    )
    country: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 two-letter uppercase country code.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "line1": "123 Main Street",
                "line2": "Apt 4B",
                "city": "Seattle",
                "state": "WA",
                "postal_code": "98101",
                "country": "US",
            }
        }
    }


class UserProfileResponse(BaseModel):
    """Full user profile representation returned to the profile owner.

    Attributes:
        owner_id: JWT sub of the profile owner.
        email: Verified e-mail address (RFC-5322).
        mobile_no: E.164-formatted mobile number.
        address: Optional postal address.
        created_at: UTC timestamp of profile creation.
        updated_at: UTC timestamp of the most recent update.
    """

    owner_id: str = Field(..., description="JWT sub of the profile owner.")
    email: EmailStr = Field(..., description="Verified e-mail address.")
    mobile_no: str = Field(..., description="E.164 mobile number.")
    address: Optional[Address] = Field(default=None, description="Postal address.")
    created_at: datetime = Field(..., description="UTC timestamp of profile creation.")
    updated_at: datetime = Field(..., description="UTC timestamp of last update.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "owner_id": "auth0|abc123",
                "email": "jane.doe@example.com",
                "mobile_no": "+12065550100",
                "address": {
                    "line1": "123 Main Street",
                    "line2": "Apt 4B",
                    "city": "Seattle",
                    "state": "WA",
                    "postal_code": "98101",
                    "country": "US",
                },
                "created_at": "2026-01-15T08:30:00Z",
                "updated_at": "2026-03-19T10:00:00Z",
            }
        }
    }


class UserProfileUpdateRequest(BaseModel):
    """PATCH request body for updating mutable user profile fields.

    All fields are optional; only supplied (non-None) fields are merged
    into the existing profile document (true PATCH semantics).

    Attributes:
        email: Optional new e-mail address.
        mobile_no: Optional new E.164-formatted mobile number.
        address: Optional new or updated postal address.
    """

    email: Optional[EmailStr] = Field(default=None, description="New e-mail address.")
    mobile_no: Optional[str] = Field(
        default=None,
        pattern=r"^\+[1-9]\d{1,14}$",
        description="New E.164 mobile number (e.g. +12065550100).",
    )
    address: Optional[Address] = Field(
        default=None, description="New or updated postal address."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "new.email@example.com",
                "mobile_no": "+442071234567",
                "address": {
                    "line1": "10 Downing Street",
                    "city": "London",
                    "state": "England",
                    "postal_code": "SW1A 2AA",
                    "country": "GB",
                },
            }
        }
    }
