"""Pydantic v2 schemas and DTOs for statement e-mail delivery."""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class StatementEmailRequest(BaseModel):
    """Request payload for statement e-mail dispatch.

    Attributes:
        recipient_email: Optional explicit recipient e-mail address.
        start_date: Optional statement start date.
        end_date: Optional statement end date.
    """

    recipient_email: Optional[EmailStr] = Field(
        default=None,
        description="Explicit recipient e-mail. If omitted, profile e-mail is used.",
    )
    start_date: Optional[date] = Field(
        default=None,
        description="Optional statement period start date (YYYY-MM-DD).",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="Optional statement period end date (YYYY-MM-DD).",
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "examples": [
                {
                    "recipient_email": "customer@example.com",
                    "start_date": "2026-02-01",
                    "end_date": "2026-02-29",
                },
                {},
            ]
        },
    }


class StatementEmailResponse(BaseModel):
    """Response payload for statement e-mail dispatch.

    Attributes:
        recipient_email: Resolved recipient e-mail address.
        start_date: Effective statement start date.
        end_date: Effective statement end date.
        delivery_status: Delivery status indicator.
        message: Human-readable delivery message.
    """

    recipient_email: EmailStr = Field(..., description="Resolved recipient e-mail.")
    start_date: date = Field(..., description="Effective statement start date.")
    end_date: date = Field(..., description="Effective statement end date.")
    delivery_status: str = Field(..., description="Delivery status, e.g. SENT.")
    message: str = Field(..., description="Statement delivery confirmation message.")

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "recipient_email": "customer@example.com",
                "start_date": "2026-02-20",
                "end_date": "2026-03-20",
                "delivery_status": "SENT",
                "message": "Statement e-mail queued for delivery.",
            }
        },
    }
