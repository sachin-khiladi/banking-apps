"""Shared pytest fixtures for the banking system test suite.

All Azure SDK clients, Cosmos DB connections, and external HTTP calls are mocked.
No real credentials, endpoints, or databases are used in any test.

Source-code gaps (src/main.py) noted at bottom of this file.
"""

from __future__ import annotations

import os
from typing import Optional
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── Set env vars BEFORE any src imports to prevent RepositoryException ────────
# CosmosAccountRepository.__init__ raises RepositoryException (not ImportError)
# when COSMOS_ACCOUNT_URL / COSMOS_DB_NAME are absent.  Setting them here means
# the try-block in src/main.py won't raise when the module is first imported.
os.environ.setdefault("COSMOS_ACCOUNT_URL", "https://test.documents.azure.com:443/")
os.environ.setdefault("COSMOS_DB_NAME", "test_banking_db")
os.environ.setdefault("AZURE_APP_CONFIG_ENDPOINT", "https://appconfig-test.azconfig.io")
os.environ.setdefault("AZURE_KEY_VAULT_URI", "https://kv-test.vault.azure.net/")

from src.api.accounts import (
    admin_router,
    customer_router,
    get_account_service,
)  # noqa: E402
from src.auth.oauth2 import get_current_user  # noqa: E402
from src.models.account import AccountStatus, AccountType  # noqa: E402
from src.services.account_service import AccountService  # noqa: E402

# ── Shared test constants ─────────────────────────────────────────────────────

OWNER_ID = "user-abc-123"
OTHER_OWNER_ID = "user-xyz-999"
ACCOUNT_NUMBER = "1234567890"
NOW_ISO = "2026-03-08T00:00:00+00:00"

CUSTOMER_USER: dict = {"sub": OWNER_ID, "role": "customer"}
EMPLOYEE_USER: dict = {"sub": "employee-xyz", "role": "bank_employee"}


# ── Account document factory ──────────────────────────────────────────────────


def make_account_doc(
    *,
    owner_id: str = OWNER_ID,
    account_number: str = ACCOUNT_NUMBER,
    status: str = AccountStatus.ACTIVE.value,
    is_deleted: bool = False,
    closed_at: Optional[str] = None,
    closure_reason: Optional[str] = None,
) -> dict:
    """Build a minimal valid account document dict for use in AsyncMock returns."""
    return {
        "account_number": account_number,
        "owner_id": owner_id,
        "account_type": AccountType.SAVINGS.value,
        "status": status,
        "balance": "500.00",
        "currency": "USD",
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
        "closed_at": closed_at,
        "closure_reason": closure_reason,
        "is_deleted": is_deleted,
    }


CLOSED_DOC: dict = make_account_doc(
    status=AccountStatus.CLOSED.value,
    is_deleted=True,
    closed_at=NOW_ISO,
    closure_reason="Customer requested closure.",
)


# ── Mock repository fixture ───────────────────────────────────────────────────


@pytest.fixture
def mock_repo() -> AsyncMock:
    """Provide a fully-mocked IAccountRepository with sensible defaults.

    All repository methods are AsyncMock so they can be awaited in service tests.
    """
    repo = AsyncMock()
    repo.create.return_value = make_account_doc()
    repo.get_by_account_number.return_value = make_account_doc()
    repo.list_by_owner.return_value = [make_account_doc()]
    repo.list_all.return_value = [
        make_account_doc(),
        make_account_doc(
            account_number="9999999999",
            is_deleted=True,
            status=AccountStatus.CLOSED.value,
            closed_at=NOW_ISO,
            closure_reason="Test closure",
        ),
    ]
    repo.update.return_value = make_account_doc()
    return repo


@pytest.fixture
def account_service(mock_repo: AsyncMock) -> AccountService:
    """Provide AccountService backed by the mock repository."""
    return AccountService(repository=mock_repo)


# ── Test FastAPI app factory ──────────────────────────────────────────────────
# NOTE: src.main.app is NOT imported here due to two source-level bugs:
#   Bug 1 — include_router(health_check): health_check is a coroutine function,
#            not an APIRouter.  Fix: export `router` from src/api/health.py and
#            import `from src.api.health import router as health_router` in main.
#   Bug 2 — CosmosAccountRepository() in try block raises RepositoryException
#            (not ImportError) when env vars are absent, so the except ImportError
#            guard does not catch it.  Fix: widen to `except Exception` or check
#            env vars before instantiation.
# Both source gaps require changes in src/main.py by the python-coding-agent.


def _make_test_app(user_identity: dict, service: AccountService) -> FastAPI:
    """Create a fresh FastAPI app with account routers and injected dependencies.

    Args:
        user_identity: JWT payload dict to return from get_current_user override.
        service:       AccountService instance backed by mock repository.

    Returns:
        Configured FastAPI app ready for TestClient construction.
    """
    app = FastAPI()
    app.include_router(customer_router)
    app.include_router(admin_router)
    app.dependency_overrides[get_account_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: user_identity
    return app


@pytest.fixture
def customer_client(account_service: AccountService) -> TestClient:
    """TestClient with customer-role identity and mock AccountService."""
    return TestClient(
        _make_test_app(CUSTOMER_USER, account_service), raise_server_exceptions=False
    )


@pytest.fixture
def employee_client(account_service: AccountService) -> TestClient:
    """TestClient with bank_employee-role identity and mock AccountService."""
    return TestClient(
        _make_test_app(EMPLOYEE_USER, account_service), raise_server_exceptions=False
    )
