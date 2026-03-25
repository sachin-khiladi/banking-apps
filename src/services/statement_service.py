"""Business logic for e-mailing account statements."""

from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage
from uuid import uuid4

from opentelemetry import trace

from src.exceptions.domain_exceptions import RepositoryException, ValidationException
from src.models.statement import StatementEmailRequest, StatementEmailResponse
from src.repository.interfaces.i_account_repository import IAccountRepository
from src.repository.interfaces.i_user_profile_repository import IUserProfileRepository

tracer = trace.get_tracer(__name__)


@dataclass(frozen=True)
class SmtpConfig:
    """SMTP configuration used by StatementService."""

    host: str
    port: int
    sender_email: str
    username: str | None
    password: str | None
    use_tls: bool
    timeout_seconds: int


class StatementService:
    """Business-logic layer for statement period resolution and e-mail dispatch."""

    _DEFAULT_PERIOD_DAYS = 30

    def __init__(
        self,
        account_repository: IAccountRepository,
        user_profile_repository: IUserProfileRepository,
    ) -> None:
        """Initialise service with injected repositories.

        Args:
            account_repository: Repository for account lookup operations.
            user_profile_repository: Repository for profile lookup operations.
        """
        self._account_repository = account_repository
        self._user_profile_repository = user_profile_repository

    async def email_statement(
        self,
        owner_id: str,
        payload: StatementEmailRequest,
    ) -> StatementEmailResponse:
        """Resolve recipient and period, then dispatch statement e-mail.

        Args:
            owner_id: Authenticated user ID (JWT sub).
            payload: Statement e-mail request details.

        Returns:
            StatementEmailResponse containing resolved details.

        Raises:
            ValidationException: If recipient or date range is invalid.
            RepositoryException: If SMTP delivery fails.
        """
        request_id = str(uuid4())
        with tracer.start_as_current_span("StatementService.email_statement") as span:
            span.set_attribute("operation_name", "email_statement")
            span.set_attribute("user_id", owner_id)
            span.set_attribute("request_id", request_id)

            start_date, end_date = self._resolve_date_range(
                payload.start_date,
                payload.end_date,
            )
            recipient_email, recipient_source = await self._resolve_recipient(
                owner_id, payload
            )
            span.set_attribute("recipient_source", recipient_source)
            span.set_attribute("period_days", (end_date - start_date).days)

            statement_payload = await self._build_statement_payload(
                owner_id,
                start_date,
                end_date,
            )
            email_body = self._render_statement_email_content(
                owner_id=owner_id,
                start_date=start_date,
                end_date=end_date,
                statement_payload=statement_payload,
            )
            self._send_email(
                recipient_email=recipient_email,
                email_body=email_body,
            )

            return StatementEmailResponse(
                recipient_email=recipient_email,
                start_date=start_date,
                end_date=end_date,
                delivery_status="SENT",
                message="Statement e-mail queued for delivery.",
            )

    async def _resolve_recipient(
        self,
        owner_id: str,
        payload: StatementEmailRequest,
    ) -> tuple[str, str]:
        """Resolve recipient e-mail from request first, then profile.

        Args:
            owner_id: Authenticated user ID.
            payload: Request payload.

        Returns:
            Tuple of (recipient_email, source).

        Raises:
            ValidationException: If no recipient e-mail is available.
        """
        if payload.recipient_email is not None:
            return str(payload.recipient_email), "request"

        profile = await self._user_profile_repository.get_by_owner_id(owner_id)
        profile_email = profile.get("email") if profile else None
        if profile_email:
            return str(profile_email), "profile"

        raise ValidationException(
            {
                "recipient_email": (
                    "Recipient e-mail is required. Provide recipient_email in the request "
                    "or configure an e-mail address in the user profile."
                )
            }
        )

    def _resolve_date_range(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> tuple[date, date]:
        """Resolve effective statement date range with one-month defaults.

        Args:
            start_date: Optional requested start date.
            end_date: Optional requested end date.

        Returns:
            Effective (start_date, end_date) tuple.

        Raises:
            ValidationException: If start_date is after end_date.
        """
        if start_date is None and end_date is None:
            resolved_end = datetime.now(timezone.utc).date()
            resolved_start = resolved_end - timedelta(days=self._DEFAULT_PERIOD_DAYS)
        elif start_date is not None and end_date is None:
            resolved_start = start_date
            resolved_end = resolved_start + timedelta(days=self._DEFAULT_PERIOD_DAYS)
        elif start_date is None and end_date is not None:
            resolved_end = end_date
            resolved_start = resolved_end - timedelta(days=self._DEFAULT_PERIOD_DAYS)
        else:
            resolved_start = start_date
            resolved_end = end_date

        if resolved_start > resolved_end:
            raise ValidationException(
                {"date_range": "start_date must be less than or equal to end_date."}
            )
        return resolved_start, resolved_end

    async def _build_statement_payload(
        self,
        owner_id: str,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Build a minimal statement payload for e-mail body rendering.

        Args:
            owner_id: Authenticated user ID.
            start_date: Effective statement start date.
            end_date: Effective statement end date.

        Returns:
            Dict containing summary values used by the e-mail template.
        """
        accounts = await self._account_repository.list_by_owner(
            owner_id, include_closed=False
        )
        total_balance = Decimal("0")
        currency = "USD"
        for account in accounts:
            account_balance = account.get("balance", "0")
            try:
                total_balance += Decimal(str(account_balance))
            except (InvalidOperation, TypeError):
                continue
            account_currency = account.get("currency")
            if account_currency:
                currency = str(account_currency)

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "account_count": len(accounts),
            "total_balance": f"{total_balance:.2f}",
            "currency": currency,
        }

    def _send_email(
        self,
        recipient_email: str,
        email_body: str,
    ) -> None:
        """Dispatch statement e-mail using SMTP configuration.

        Args:
            recipient_email: Resolved recipient e-mail address.
            email_body: Pre-rendered e-mail body content.

        Raises:
            RepositoryException: If SMTP config is invalid or send fails.
        """
        config = self._load_smtp_config()

        message = EmailMessage()
        message["Subject"] = "Your bank statement"
        message["From"] = config.sender_email
        message["To"] = recipient_email
        message.set_content(email_body)

        try:
            with smtplib.SMTP(
                config.host, config.port, timeout=config.timeout_seconds
            ) as client:
                if config.use_tls:
                    client.starttls()
                if config.username and config.password:
                    client.login(config.username, config.password)
                client.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            raise RepositoryException(
                "Failed to send statement e-mail.", cause=exc
            ) from exc

    def _render_statement_email_content(
        self,
        owner_id: str,
        start_date: date,
        end_date: date,
        statement_payload: dict,
    ) -> str:
        """Render plaintext statement e-mail content.

        Args:
            owner_id: Authenticated user ID.
            start_date: Effective statement start date.
            end_date: Effective statement end date.
            statement_payload: Statement summary payload.

        Returns:
            Plaintext content for the statement e-mail body.
        """
        total_balance = (
            f"{statement_payload['total_balance']} {statement_payload['currency']}"
        )
        return (
            "Your statement is ready.\n\n"
            f"Owner ID: {owner_id}\n"
            f"Period: {start_date.isoformat()} to {end_date.isoformat()}\n"
            f"Accounts included: {statement_payload['account_count']}\n"
            f"Total balance: {total_balance}\n"
        )

    def _load_smtp_config(self) -> SmtpConfig:
        """Read SMTP configuration from environment variables.

        Returns:
            Parsed SmtpConfig object.

        Raises:
            ValidationException: If required SMTP environment variables are missing.
        """
        host = os.environ.get("SMTP_HOST", "").strip()
        port_raw = os.environ.get("SMTP_PORT", "").strip()
        sender_email = os.environ.get("SMTP_SENDER_EMAIL", "").strip()
        username = os.environ.get("SMTP_USERNAME")
        password = os.environ.get("SMTP_PASSWORD")
        use_tls = os.environ.get("SMTP_USE_TLS", "true").strip().lower() in {
            "true",
            "1",
            "yes",
            "y",
        }
        timeout_raw = os.environ.get("SMTP_TIMEOUT_SECONDS", "15").strip()

        missing = []
        if not host:
            missing.append("SMTP_HOST")
        if not port_raw:
            missing.append("SMTP_PORT")
        if not sender_email:
            missing.append("SMTP_SENDER_EMAIL")
        if missing:
            raise ValidationException(
                {
                    "smtp": (
                        "Missing required SMTP configuration: " f"{', '.join(missing)}."
                    )
                }
            )

        try:
            port = int(port_raw)
            timeout_seconds = int(timeout_raw)
        except ValueError as exc:
            raise ValidationException(
                {"smtp": "SMTP_PORT and SMTP_TIMEOUT_SECONDS must be integers."}
            ) from exc

        return SmtpConfig(
            host=host,
            port=port,
            sender_email=sender_email,
            username=username,
            password=password,
            use_tls=use_tls,
            timeout_seconds=timeout_seconds,
        )
