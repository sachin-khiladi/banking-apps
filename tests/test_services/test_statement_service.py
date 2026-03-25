"""Unit tests for src/services/statement_service.py."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.exceptions.domain_exceptions import RepositoryException, ValidationException
from src.models.statement import StatementEmailRequest
from src.services.statement_service import StatementService


OWNER_ID = "user-abc-123"


@pytest.fixture
def mock_account_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.list_by_owner.return_value = [{"balance": "10.50", "currency": "USD"}]
    return repo


@pytest.fixture
def mock_profile_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_owner_id.return_value = {"email": "profile@example.com"}
    return repo


@pytest.fixture
def statement_service(mock_account_repo: AsyncMock, mock_profile_repo: AsyncMock) -> StatementService:
    return StatementService(
        account_repository=mock_account_repo,
        user_profile_repository=mock_profile_repo,
    )


@pytest.fixture
def smtp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_SENDER_EMAIL", "noreply@example.com")
    monkeypatch.setenv("SMTP_USERNAME", "smtp-user")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-pass")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("SMTP_TIMEOUT_SECONDS", "15")


class TestEmailStatement:
    """Tests for StatementService.email_statement()."""

    @pytest.mark.asyncio
    async def test_email_statement_prefers_request_recipient_over_profile(
        self,
        statement_service: StatementService,
        mock_profile_repo: AsyncMock,
        mock_account_repo: AsyncMock,
        smtp_env: None,
        mocker,
    ) -> None:
        smtp_client = MagicMock()
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = smtp_client
        smtp_context.__exit__.return_value = False
        mocker.patch("src.services.statement_service.smtplib.SMTP", return_value=smtp_context)

        payload = StatementEmailRequest(
            recipient_email="request@example.com",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 3, 2),
        )

        result = await statement_service.email_statement(owner_id=OWNER_ID, payload=payload)

        assert str(result.recipient_email) == "request@example.com"
        mock_profile_repo.get_by_owner_id.assert_not_called()
        mock_account_repo.list_by_owner.assert_called_once_with(OWNER_ID, include_closed=False)
        smtp_client.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_statement_uses_profile_recipient_when_request_omitted(
        self,
        statement_service: StatementService,
        smtp_env: None,
        mocker,
    ) -> None:
        smtp_client = MagicMock()
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = smtp_client
        smtp_context.__exit__.return_value = False
        mocker.patch("src.services.statement_service.smtplib.SMTP", return_value=smtp_context)

        payload = StatementEmailRequest(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 3, 2),
        )

        result = await statement_service.email_statement(owner_id=OWNER_ID, payload=payload)

        assert str(result.recipient_email) == "profile@example.com"

    @pytest.mark.asyncio
    async def test_email_statement_raises_validation_when_recipient_missing(
        self,
        statement_service: StatementService,
        mock_profile_repo: AsyncMock,
    ) -> None:
        mock_profile_repo.get_by_owner_id.return_value = {}

        with pytest.raises(ValidationException) as exc_info:
            await statement_service.email_statement(
                owner_id=OWNER_ID,
                payload=StatementEmailRequest(),
            )

        assert "recipient_email" in exc_info.value.errors

    @pytest.mark.asyncio
    async def test_email_statement_sets_expected_span_attributes(
        self,
        statement_service: StatementService,
        smtp_env: None,
        mocker,
    ) -> None:
        smtp_client = MagicMock()
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = smtp_client
        smtp_context.__exit__.return_value = False
        mocker.patch("src.services.statement_service.smtplib.SMTP", return_value=smtp_context)

        mock_span = MagicMock()
        span_context = MagicMock()
        span_context.__enter__.return_value = mock_span
        span_context.__exit__.return_value = False
        mocker.patch(
            "src.services.statement_service.tracer.start_as_current_span",
            return_value=span_context,
        )

        await statement_service.email_statement(
            owner_id=OWNER_ID,
            payload=StatementEmailRequest(recipient_email="request@example.com"),
        )

        mock_span.set_attribute.assert_any_call("operation_name", "email_statement")
        mock_span.set_attribute.assert_any_call("user_id", OWNER_ID)
        mock_span.set_attribute.assert_any_call("request_id", mocker.ANY)


class TestDateResolution:
    """Tests for statement period defaulting and validation."""

    def test_resolve_date_range_defaults_to_30_days_when_omitted(
        self,
        statement_service: StatementService,
    ) -> None:
        start_date, end_date = statement_service._resolve_date_range(None, None)
        assert (end_date - start_date).days == 30

    def test_resolve_date_range_derives_end_when_only_start_supplied(
        self,
        statement_service: StatementService,
    ) -> None:
        start_date, end_date = statement_service._resolve_date_range(date(2026, 3, 1), None)
        assert end_date == date(2026, 3, 31)

    def test_resolve_date_range_derives_start_when_only_end_supplied(
        self,
        statement_service: StatementService,
    ) -> None:
        start_date, end_date = statement_service._resolve_date_range(None, date(2026, 3, 31))
        assert start_date == date(2026, 3, 1)

    def test_resolve_date_range_raises_when_start_after_end(
        self,
        statement_service: StatementService,
    ) -> None:
        with pytest.raises(ValidationException):
            statement_service._resolve_date_range(date(2026, 4, 1), date(2026, 3, 1))


class TestSmtpConfigAndSend:
    """Tests for SMTP config validation and send error mapping."""

    def test_load_smtp_config_raises_for_missing_required_env(
        self,
        statement_service: StatementService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_PORT", raising=False)
        monkeypatch.delenv("SMTP_SENDER_EMAIL", raising=False)

        with pytest.raises(ValidationException) as exc_info:
            statement_service._load_smtp_config()

        assert "smtp" in exc_info.value.errors

    def test_load_smtp_config_raises_for_invalid_integer_values(
        self,
        statement_service: StatementService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "not-an-int")
        monkeypatch.setenv("SMTP_SENDER_EMAIL", "noreply@example.com")
        monkeypatch.setenv("SMTP_TIMEOUT_SECONDS", "also-not-an-int")

        with pytest.raises(ValidationException):
            statement_service._load_smtp_config()

    def test_send_email_raises_repository_exception_on_smtp_error(
        self,
        statement_service: StatementService,
        smtp_env: None,
        mocker,
    ) -> None:
        mocker.patch(
            "src.services.statement_service.smtplib.SMTP",
            side_effect=OSError("smtp unavailable"),
        )

        with pytest.raises(RepositoryException):
            statement_service._send_email(
                recipient_email="customer@example.com",
                email_body="hello",
            )


class TestStatementPayloadBuild:
    """Tests for statement payload aggregation logic."""

    @pytest.mark.asyncio
    async def test_build_statement_payload_skips_invalid_balances(
        self,
        statement_service: StatementService,
        mock_account_repo: AsyncMock,
    ) -> None:
        mock_account_repo.list_by_owner.return_value = [
            {"balance": "bad-value", "currency": "USD"},
            {"balance": "10.00", "currency": "USD"},
        ]

        payload = await statement_service._build_statement_payload(
            owner_id=OWNER_ID,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 3, 2),
        )

        assert payload["total_balance"] == "10.00"
