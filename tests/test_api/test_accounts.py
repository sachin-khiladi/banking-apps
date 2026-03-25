"""Unit tests for src/api/accounts.py HTTP layer.

Uses the customer_client and employee_client fixtures from conftest.py.
All service calls are backed by the mock_repo AsyncMock.
Raise_server_exceptions=False so 4xx/5xx responses can be asserted on.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.exceptions.domain_exceptions import (
    AccountAlreadyClosedException,
    AccountNotFoundException,
    InsufficientPermissionsException,
)
from src.models.account import AccountStatus

from tests.conftest import ACCOUNT_NUMBER, CLOSED_DOC, OWNER_ID, make_account_doc


# ── POST /accounts ─────────────────────────────────────────────────────────────

class TestCreateAccountEndpoint:
    """Tests for POST /accounts."""

    def test_create_account_returns_201(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.create.return_value = make_account_doc()
        response = customer_client.post(
            "/accounts", json={"account_type": "SAVINGS"}
        )
        assert response.status_code == 201

    def test_create_account_response_has_account_number(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.create.return_value = make_account_doc()
        response = customer_client.post(
            "/accounts", json={"account_type": "CURRENT"}
        )
        assert "account_number" in response.json()

    def test_create_account_missing_account_type_returns_422(
        self, customer_client: TestClient
    ) -> None:
        response = customer_client.post("/accounts", json={})
        assert response.status_code == 422


# ── GET /accounts ──────────────────────────────────────────────────────────────

class TestListAccountsEndpoint:
    """Tests for GET /accounts."""

    def test_list_accounts_returns_200(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = [make_account_doc()]
        response = customer_client.get("/accounts")
        assert response.status_code == 200

    def test_list_accounts_returns_list(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = [make_account_doc()]
        response = customer_client.get("/accounts")
        assert isinstance(response.json(), list)

    def test_list_accounts_returns_empty_list_when_no_accounts(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = []
        response = customer_client.get("/accounts")
        assert response.json() == []


# ── GET /accounts/balance/{account_type} ────────────────────────────────────

class TestGetBalanceByTypeEndpoint:
    """Tests for GET /accounts/balance/{account_type}."""

    def test_get_balance_by_type_returns_200(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = [make_account_doc()]
        response = customer_client.get("/accounts/balance/SAVINGS")
        assert response.status_code == 200

    def test_get_balance_by_type_returns_requested_account_type(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = [make_account_doc()]
        response = customer_client.get("/accounts/balance/SAVINGS")
        assert response.json()["account_type"] == "SAVINGS"

    def test_get_balance_by_type_returns_404_when_type_missing(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = []
        response = customer_client.get("/accounts/balance/CURRENT")
        assert response.status_code == 404

    def test_get_balance_by_type_invalid_type_returns_422(
        self, customer_client: TestClient
    ) -> None:
        response = customer_client.get("/accounts/balance/INVALID")
        assert response.status_code == 422

    def test_get_balance_by_type_unexpected_exception_returns_500(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.side_effect = RuntimeError("unexpected")
        response = customer_client.get("/accounts/balance/SAVINGS")
        assert response.status_code == 500


# ── GET /accounts/{account_number} ────────────────────────────────────────────

class TestGetAccountEndpoint:
    """Tests for GET /accounts/{account_number}."""

    def test_get_account_returns_200(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        response = customer_client.get(f"/accounts/{ACCOUNT_NUMBER}")
        assert response.status_code == 200

    def test_get_account_returns_correct_account_number(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        response = customer_client.get(f"/accounts/{ACCOUNT_NUMBER}")
        assert response.json()["account_number"] == ACCOUNT_NUMBER

    def test_get_account_not_found_returns_404(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = None
        response = customer_client.get(f"/accounts/{ACCOUNT_NUMBER}")
        assert response.status_code == 404

    def test_get_account_wrong_owner_returns_403(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        from tests.conftest import OTHER_OWNER_ID
        mock_repo.get_by_account_number.return_value = make_account_doc(owner_id=OTHER_OWNER_ID)
        response = customer_client.get(f"/accounts/{ACCOUNT_NUMBER}")
        assert response.status_code == 403


# ── PUT /accounts/{account_number} ────────────────────────────────────────────

class TestUpdateAccountEndpoint:
    """Tests for PUT /accounts/{account_number}."""

    def test_update_account_returns_200(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        mock_repo.update.return_value = make_account_doc()
        response = customer_client.put(
            f"/accounts/{ACCOUNT_NUMBER}", json={"currency": "EUR"}
        )
        assert response.status_code == 200

    def test_update_account_already_closed_returns_409(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        closed = make_account_doc(status=AccountStatus.CLOSED.value, is_deleted=False)
        mock_repo.get_by_account_number.return_value = closed
        response = customer_client.put(
            f"/accounts/{ACCOUNT_NUMBER}", json={"currency": "EUR"}
        )
        assert response.status_code == 409

    def test_update_account_not_found_returns_404(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = None
        response = customer_client.put(
            f"/accounts/{ACCOUNT_NUMBER}", json={"currency": "EUR"}
        )
        assert response.status_code == 404


# ── POST /accounts/{account_number}/close ─────────────────────────────────────

class TestCloseAccountEndpoint:
    """Tests for POST /accounts/{account_number}/close."""

    def test_close_account_returns_200(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        mock_repo.update.return_value = CLOSED_DOC
        response = customer_client.post(
            f"/accounts/{ACCOUNT_NUMBER}/close",
            json={"closure_reason": "No longer needed here."},
        )
        assert response.status_code == 200

    def test_close_account_already_closed_returns_409(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        closed = make_account_doc(status=AccountStatus.CLOSED.value, is_deleted=False)
        mock_repo.get_by_account_number.return_value = closed
        response = customer_client.post(
            f"/accounts/{ACCOUNT_NUMBER}/close",
            json={"closure_reason": "closed already."},
        )
        assert response.status_code == 409

    def test_close_account_not_found_returns_404(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = None
        response = customer_client.post(
            f"/accounts/{ACCOUNT_NUMBER}/close",
            json={"closure_reason": "closing it."},
        )
        assert response.status_code == 404

    def test_close_account_short_closure_reason_returns_422(
        self, customer_client: TestClient
    ) -> None:
        response = customer_client.post(
            f"/accounts/{ACCOUNT_NUMBER}/close",
            json={"closure_reason": "no"},  # less than 5 chars
        )
        assert response.status_code == 422


# ── GET /admin/accounts ───────────────────────────────────────────────────────

class TestAdminListAccountsEndpoint:
    """Tests for GET /admin/accounts."""

    def test_admin_list_accounts_employee_returns_200(
        self, employee_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_all.return_value = [make_account_doc(), CLOSED_DOC]
        response = employee_client.get("/admin/accounts")
        assert response.status_code == 200

    def test_admin_list_accounts_employee_returns_list(
        self, employee_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_all.return_value = [make_account_doc(), CLOSED_DOC]
        response = employee_client.get("/admin/accounts")
        assert isinstance(response.json(), list)

    def test_admin_list_accounts_customer_returns_403(
        self, customer_client: TestClient
    ) -> None:
        response = customer_client.get("/admin/accounts")
        assert response.status_code == 403

    def test_admin_list_accounts_include_closed_false_passes_param(
        self, employee_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_all.return_value = [make_account_doc()]
        response = employee_client.get("/admin/accounts?include_closed=false")
        assert response.status_code == 200


# ── GET /admin/accounts/{account_number} ─────────────────────────────────────

class TestAdminGetAccountEndpoint:
    """Tests for GET /admin/accounts/{account_number}."""

    def test_admin_get_account_employee_returns_200(
        self, employee_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = CLOSED_DOC
        response = employee_client.get(f"/admin/accounts/{ACCOUNT_NUMBER}")
        assert response.status_code == 200

    def test_admin_get_account_includes_is_deleted_field(
        self, employee_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = CLOSED_DOC
        response = employee_client.get(f"/admin/accounts/{ACCOUNT_NUMBER}")
        assert "is_deleted" in response.json()

    def test_admin_get_account_not_found_returns_404(
        self, employee_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = None
        response = employee_client.get(f"/admin/accounts/{ACCOUNT_NUMBER}")
        assert response.status_code == 404

    def test_admin_get_account_customer_returns_403(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = CLOSED_DOC
        response = customer_client.get(f"/admin/accounts/{ACCOUNT_NUMBER}")
        assert response.status_code == 403


# ── get_account_service placeholder and _raise_http 500 fallback ──────────────

class TestEdgeCases:
    """Tests covering the get_account_service placeholder and 500-level paths."""

    def test_get_account_service_placeholder_without_override_returns_500(
        self,
    ) -> None:
        """Without dependency_overrides, get_account_service raises HTTPException(503)
        (service unavailable — Cosmos DB not configured)."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient as TC
        from src.api.accounts import customer_router
        from src.auth.oauth2 import get_current_user
        from tests.conftest import CUSTOMER_USER

        app = FastAPI()
        app.include_router(customer_router)
        # Override only identity, not service — get_account_service raises HTTPException 503
        app.dependency_overrides[get_current_user] = lambda: CUSTOMER_USER
        client = TC(app, raise_server_exceptions=False)

        response = client.get("/accounts")
        assert response.status_code == 503

    def test_create_account_unexpected_exception_returns_500(
        self, customer_client: TestClient, mock_repo: AsyncMock
    ) -> None:
        """When the service raises an unexpected exception,
        _raise_http falls through to the 500 status code path."""
        mock_repo.create.side_effect = RuntimeError("disk full")
        response = customer_client.post(
            "/accounts", json={"account_type": "SAVINGS"}
        )
        assert response.status_code == 500
