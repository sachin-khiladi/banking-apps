"""Bank account service — business logic for account lifecycle.

Encodes all domain rules for creating, reading, updating, and closing
bank accounts.  Depends only on IAccountRepository (injected) and never
imports the Cosmos SDK directly (Dependency Inversion Principle).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from opentelemetry import trace

from src.exceptions.domain_exceptions import (
    AccountAlreadyClosedException,
    AccountNotFoundException,
    AccountTypeNotFoundException,
    InsufficientPermissionsException,
)
from src.models.account import (
    AccountAdminResponse,
    AccountBalanceResponse,
    AccountCloseRequest,
    AccountCreate,
    AccountResponse,
    AccountStatus,
    AccountType,
    AccountUpdate,
)
from src.repository.interfaces.i_account_repository import IAccountRepository

tracer = trace.get_tracer(__name__)


class AccountService:
    """Business-logic layer for bank account lifecycle management.

    Responsibilities:
    - Unique 10-digit account-number generation.
    - Ownership enforcement (customers access only their own accounts).
    - Soft-delete on closure (data retained, visible to bank employees).
    - Admin-level access to all accounts including closed ones.

    Attributes:
        _repo: Injected IAccountRepository implementation.
    """

    def __init__(self, repository: IAccountRepository) -> None:
        """Initialise the service with an injected repository.

        Args:
            repository: Concrete implementation of IAccountRepository.
        """
        self._repo = repository

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _generate_account_number() -> str:
        """Generate a unique 10-digit numeric account number.

        Uses UUID4 integer entropy, zero-padded to 10 digits.
        Collision probability ~1 in 10^10 per generation.

        Returns:
            A 10-character zero-padded digit string (e.g. '3741829056').
        """
        return str(uuid.uuid4().int)[:10].zfill(10)

    # ── Customer operations ───────────────────────────────────────────────────

    async def create_account(
        self, payload: AccountCreate, owner_id: str
    ) -> AccountResponse:
        """Create a new bank account for the authenticated user.

        Args:
            payload: Validated AccountCreate data.
            owner_id: JWT sub of the requesting user.

        Returns:
            AccountResponse for the newly created account.
        """
        with tracer.start_as_current_span("AccountService.create_account") as span:
            span.set_attribute("owner_id", owner_id)
            span.set_attribute("account_type", payload.account_type.value)

            account_number = self._generate_account_number()
            now = datetime.now(timezone.utc)

            document: dict = {
                "account_number": account_number,
                "owner_id": owner_id,
                "account_type": payload.account_type.value,
                "status": AccountStatus.ACTIVE.value,
                "balance": str(payload.initial_deposit),
                "currency": payload.currency.upper(),
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "closed_at": None,
                "closure_reason": None,
                "is_deleted": False,
            }

            created = await self._repo.create(document)
            span.set_attribute("account_number", account_number)
            return AccountResponse(**created)

    async def get_account(self, account_number: str, owner_id: str) -> AccountResponse:
        """Retrieve an active account belonging to the authenticated user.

        Args:
            account_number: The 10-digit account number.
            owner_id: JWT sub of the requesting user.

        Returns:
            AccountResponse for the account.

        Raises:
            AccountNotFoundException: If account is missing or soft-deleted.
            InsufficientPermissionsException: If account belongs to another user.
        """
        with tracer.start_as_current_span("AccountService.get_account") as span:
            span.set_attribute("account_number", account_number)

            doc = await self._repo.get_by_account_number(account_number)
            if doc is None or doc.get("is_deleted"):
                raise AccountNotFoundException(account_number)
            if doc["owner_id"] != owner_id:
                raise InsufficientPermissionsException(
                    f"Account {account_number} belongs to a different user."
                )
            return AccountResponse(**doc)

    async def list_accounts(self, owner_id: str) -> list[AccountResponse]:
        """List all active accounts for the authenticated user.

        Args:
            owner_id: JWT sub of the requesting user.

        Returns:
            List of AccountResponse objects (empty list if none).
        """
        with tracer.start_as_current_span("AccountService.list_accounts") as span:
            span.set_attribute("owner_id", owner_id)
            docs = await self._repo.list_by_owner(owner_id, include_closed=False)
            return [AccountResponse(**d) for d in docs]

    async def get_balance_by_type(
        self, account_type: AccountType, owner_id: str
    ) -> AccountBalanceResponse:
        """Return the balance for a specific account type owned by the user.

        Fetches all active accounts for the owner and filters by the requested
        type.  If the user has no active account of that type, raises
        ``AccountTypeNotFoundException`` so the API layer returns HTTP 404
        with a meaningful, stack-trace-free message.

        If the user holds multiple active accounts of the same type (edge case),
        the most recently updated one is selected.

        Args:
            account_type: The ``AccountType`` enum value to query
                (SAVINGS | CURRENT | FIXED_DEPOSIT).
            owner_id: JWT sub of the requesting user.

        Returns:
            ``AccountBalanceResponse`` with ISO 20022–aligned fields and a
            point-in-time ``as_of`` UTC timestamp.

        Raises:
            AccountTypeNotFoundException: When the user has no active account
                of the requested type.
        """
        with tracer.start_as_current_span("AccountService.get_balance_by_type") as span:
            span.set_attribute("owner_id", owner_id)
            span.set_attribute("account_type", account_type.value)

            docs = await self._repo.list_by_owner(owner_id, include_closed=False)
            matching = [d for d in docs if d.get("account_type") == account_type.value]

            if not matching:
                raise AccountTypeNotFoundException(account_type.value)

            # Deterministic selection: prefer the most recently updated account
            account = max(matching, key=lambda d: d.get("updated_at", ""))

            span.set_attribute("account_number", account["account_number"])
            return AccountBalanceResponse(
                account_number=account["account_number"],
                account_type=account_type,
                available_balance=Decimal(str(account["balance"])),
                currency=account["currency"],
                status=AccountStatus(account["status"]),
                as_of=datetime.now(timezone.utc),
            )

    async def update_account(
        self, account_number: str, payload: AccountUpdate, owner_id: str
    ) -> AccountResponse:
        """Update mutable fields of an active account.

        Args:
            account_number: The 10-digit account number.
            payload: Validated AccountUpdate data.
            owner_id: JWT sub of the requesting user.

        Returns:
            AccountResponse reflecting the update.

        Raises:
            AccountNotFoundException: If account is missing or soft-deleted.
            InsufficientPermissionsException: If account belongs to another user.
            AccountAlreadyClosedException: If account status is CLOSED.
        """
        with tracer.start_as_current_span("AccountService.update_account") as span:
            span.set_attribute("account_number", account_number)

            doc = await self._repo.get_by_account_number(account_number)
            if doc is None or doc.get("is_deleted"):
                raise AccountNotFoundException(account_number)
            if doc["owner_id"] != owner_id:
                raise InsufficientPermissionsException(
                    f"Account {account_number} belongs to a different user."
                )
            if doc["status"] == AccountStatus.CLOSED.value:
                raise AccountAlreadyClosedException(account_number)

            updates: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
            if payload.currency is not None:
                updates["currency"] = payload.currency.upper()

            updated = await self._repo.update(account_number, updates)
            return AccountResponse(**updated)

    async def close_account(
        self, account_number: str, payload: AccountCloseRequest, owner_id: str
    ) -> AccountResponse:
        """Soft-delete (close) a bank account owned by the requesting user.

        Sets status=CLOSED, is_deleted=True, records closed_at and
        closure_reason.  Data is retained and accessible to bank employees.

        Args:
            account_number: The 10-digit account number.
            payload: Validated AccountCloseRequest.
            owner_id: JWT sub of the requesting user.

        Returns:
            AccountResponse reflecting the closed state.

        Raises:
            AccountNotFoundException: If account is missing or already deleted.
            InsufficientPermissionsException: If account belongs to another user.
            AccountAlreadyClosedException: If account is already CLOSED.
        """
        with tracer.start_as_current_span("AccountService.close_account") as span:
            span.set_attribute("account_number", account_number)
            span.set_attribute("owner_id", owner_id)

            doc = await self._repo.get_by_account_number(account_number)
            if doc is None or doc.get("is_deleted"):
                raise AccountNotFoundException(account_number)
            if doc["owner_id"] != owner_id:
                raise InsufficientPermissionsException(
                    f"Account {account_number} belongs to a different user."
                )
            if doc["status"] == AccountStatus.CLOSED.value:
                raise AccountAlreadyClosedException(account_number)

            now = datetime.now(timezone.utc)
            updates = {
                "status": AccountStatus.CLOSED.value,
                "is_deleted": True,
                "closed_at": now.isoformat(),
                "closure_reason": payload.closure_reason,
                "updated_at": now.isoformat(),
            }

            updated = await self._repo.update(account_number, updates)
            return AccountResponse(**updated)

    # ── Admin operations ──────────────────────────────────────────────────────

    async def admin_list_all_accounts(
        self, include_closed: bool = True
    ) -> list[AccountAdminResponse]:
        """List all accounts system-wide (admin only).

        Args:
            include_closed: When True (default), includes CLOSED accounts.

        Returns:
            List of AccountAdminResponse objects.
        """
        with tracer.start_as_current_span("AccountService.admin_list_all"):
            docs = await self._repo.list_all(include_closed=include_closed)
            return [AccountAdminResponse(**d) for d in docs]

    async def admin_get_account(self, account_number: str) -> AccountAdminResponse:
        """Retrieve any account including closed ones (admin only).

        Args:
            account_number: The 10-digit account number.

        Returns:
            AccountAdminResponse including soft-delete metadata.

        Raises:
            AccountNotFoundException: If account does not exist at all.
        """
        with tracer.start_as_current_span("AccountService.admin_get_account") as span:
            span.set_attribute("account_number", account_number)
            doc = await self._repo.get_by_account_number(account_number)
            if doc is None:
                raise AccountNotFoundException(account_number)
            return AccountAdminResponse(**doc)
