"""Bank account API route handlers.

Two router groups:
  customer_router (/accounts)        — authenticated user CRUD on own accounts.
  admin_router    (/admin/accounts)  — bank-employee read access to all accounts.

All business logic is delegated to AccountService.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.auth.oauth2 import get_current_user, require_bank_employee
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
    AccountType,
    AccountUpdate,
)
from src.services.account_service import AccountService

# ── Routers ───────────────────────────────────────────────────────────────────

customer_router = APIRouter(prefix="/accounts", tags=["accounts"])
admin_router = APIRouter(prefix="/admin/accounts", tags=["admin-accounts"])


# ── Dependency stubs — overridden in main.py ──────────────────────────────────


def get_account_service() -> AccountService:
    """Dependency placeholder; real factory wired in main.py.

    Raises HTTP 503 so callers get a meaningful error when Cosmos DB is not
    configured (COSMOS_ACCOUNT_URL / COSMOS_DB_NAME env vars missing).
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Account service unavailable: COSMOS_ACCOUNT_URL and COSMOS_DB_NAME must be set.",
    )


ServiceDep = Annotated[AccountService, Depends(get_account_service)]
CurrentUser = Annotated[dict, Depends(get_current_user)]
BankEmployee = Annotated[dict, Depends(require_bank_employee)]


# ── Domain exception to HTTP response mapping ─────────────────────────────────


def _raise_http(exc: Exception) -> None:
    """Translate a domain exception to an HTTPException.

    Args:
        exc: Domain-layer exception to translate.

    Raises:
        HTTPException: Always raised with the appropriate HTTP status code.
    """
    if isinstance(exc, AccountNotFoundException):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, AccountTypeNotFoundException):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, AccountAlreadyClosedException):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, InsufficientPermissionsException):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred.",
    )


# ── Customer routes ───────────────────────────────────────────────────────────


@customer_router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a bank account",
    description=(
        "Opens a new bank account. "
        "A unique 10-digit account number is generated server-side."
    ),
)
async def create_account(
    payload: AccountCreate,
    service: ServiceDep,
    current_user: CurrentUser,
) -> AccountResponse:
    """Create a new bank account for the authenticated user."""
    try:
        return await service.create_account(payload, owner_id=current_user["sub"])
    except Exception as exc:
        _raise_http(exc)


@customer_router.get(
    "",
    response_model=list[AccountResponse],
    summary="List own active accounts",
)
async def list_accounts(
    service: ServiceDep,
    current_user: CurrentUser,
) -> list[AccountResponse]:
    """Return all ACTIVE accounts belonging to the authenticated user."""
    return await service.list_accounts(owner_id=current_user["sub"])


# ── Balance endpoints ─────────────────────────────────────────────────────────


@customer_router.get(
    "/balance/{account_type}",
    response_model=AccountBalanceResponse,
    summary="Get balance by account type",
    description=(
        "Returns the current available balance for the authenticated user's "
        "SAVINGS, CURRENT, or FIXED_DEPOSIT account.  "
        "Responds with HTTP 404 if the user has no active account of the "
        "requested type.  "
        "The ``as_of`` field in the response carries a UTC timestamp so "
        "consumers can detect stale data.  Compatible with ISO 20022 "
        "BankToCustomerAccountReport balance semantics (CLAV)."
    ),
    responses={
        200: {"description": "Balance retrieved successfully."},
        401: {"description": "Bearer token missing or invalid."},
        404: {"description": "No active account of the requested type for this user."},
    },
)
async def get_balance_by_account_type(
    account_type: AccountType,
    service: ServiceDep,
    current_user: CurrentUser,
) -> AccountBalanceResponse:
    """Return the available balance for the specified account type.

    Path parameter ``account_type`` is validated against the ``AccountType``
    enum by FastAPI before reaching this handler, so invalid values produce a
    standards-compliant HTTP 422 Unprocessable Entity automatically.
    """
    try:
        return await service.get_balance_by_type(
            account_type=account_type,
            owner_id=current_user["sub"],
        )
    except Exception as exc:
        _raise_http(exc)


@customer_router.get(
    "/{account_number}",
    response_model=AccountResponse,
    summary="Get a specific account",
)
async def get_account(
    account_number: str,
    service: ServiceDep,
    current_user: CurrentUser,
) -> AccountResponse:
    """Retrieve a single active account by its account number."""
    try:
        return await service.get_account(account_number, owner_id=current_user["sub"])
    except Exception as exc:
        _raise_http(exc)


@customer_router.put(
    "/{account_number}",
    response_model=AccountResponse,
    summary="Update account details",
)
async def update_account(
    account_number: str,
    payload: AccountUpdate,
    service: ServiceDep,
    current_user: CurrentUser,
) -> AccountResponse:
    """Apply a partial update to an active account (owner only)."""
    try:
        return await service.update_account(
            account_number, payload, owner_id=current_user["sub"]
        )
    except Exception as exc:
        _raise_http(exc)


@customer_router.post(
    "/{account_number}/close",
    response_model=AccountResponse,
    summary="Close (soft-delete) an account",
    description=(
        "Marks the account CLOSED. Data is retained and visible to authorised "
        "bank employees only. This action cannot be reversed via this API."
    ),
)
async def close_account(
    account_number: str,
    payload: AccountCloseRequest,
    service: ServiceDep,
    current_user: CurrentUser,
) -> AccountResponse:
    """Soft-delete a bank account (status=CLOSED, is_deleted=True)."""
    try:
        return await service.close_account(
            account_number, payload, owner_id=current_user["sub"]
        )
    except Exception as exc:
        _raise_http(exc)


# ── Admin routes ──────────────────────────────────────────────────────────────


@admin_router.get(
    "",
    response_model=list[AccountAdminResponse],
    summary="[Admin] List all accounts",
    description=(
        "Returns all accounts system-wide including CLOSED ones. "
        "Requires bank_employee role."
    ),
)
async def admin_list_accounts(
    service: ServiceDep,
    _employee: BankEmployee,
    include_closed: bool = Query(default=True, description="Include CLOSED accounts."),
) -> list[AccountAdminResponse]:
    """Admin: list all accounts, optionally including soft-deleted ones."""
    return await service.admin_list_all_accounts(include_closed=include_closed)


@admin_router.get(
    "/{account_number}",
    response_model=AccountAdminResponse,
    summary="[Admin] Get any account",
    description=(
        "Returns full details for any account including CLOSED. "
        "Requires bank_employee role."
    ),
)
async def admin_get_account(
    account_number: str,
    service: ServiceDep,
    _employee: BankEmployee,
) -> AccountAdminResponse:
    """Admin: retrieve any account by number, including closed accounts."""
    try:
        return await service.admin_get_account(account_number)
    except Exception as exc:
        _raise_http(exc)
