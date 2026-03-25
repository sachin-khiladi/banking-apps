"""Unit tests for src/models/statement.py."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from src.models.statement import StatementEmailRequest, StatementEmailResponse


class TestStatementEmailRequest:
    """Tests for StatementEmailRequest schema behavior."""

    def test_request_allows_empty_payload_defaults_to_none(self) -> None:
        payload = StatementEmailRequest()
        assert payload.recipient_email is None

    def test_request_accepts_valid_email_and_dates(self) -> None:
        payload = StatementEmailRequest(
            recipient_email="customer@example.com",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
        )
        assert str(payload.recipient_email) == "customer@example.com"

    def test_request_forbids_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            StatementEmailRequest(unexpected="value")


class TestStatementEmailResponse:
    """Tests for StatementEmailResponse schema behavior."""

    def test_response_accepts_valid_payload(self) -> None:
        response = StatementEmailResponse(
            recipient_email="customer@example.com",
            start_date=date(2026, 2, 20),
            end_date=date(2026, 3, 20),
            delivery_status="SENT",
            message="Statement e-mail queued for delivery.",
        )
        assert response.delivery_status == "SENT"

    def test_response_forbids_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            StatementEmailResponse(
                recipient_email="customer@example.com",
                start_date=date(2026, 2, 20),
                end_date=date(2026, 3, 20),
                delivery_status="SENT",
                message="Statement e-mail queued for delivery.",
                unexpected="value",
            )
