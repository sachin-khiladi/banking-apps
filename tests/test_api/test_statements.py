"""Unit tests for src/api/statements.py HTTP layer."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from src.api.statements import get_statement_service, statement_router
from src.auth.oauth2 import get_current_user
from src.exceptions.domain_exceptions import ValidationException
from src.models.statement import StatementEmailResponse


OWNER_ID = "user-abc-123"
CUSTOMER_USER: dict = {"sub": OWNER_ID, "role": "customer"}


def _make_statements_app(user_identity: dict, mock_service: MagicMock) -> FastAPI:
    app = FastAPI()
    app.include_router(statement_router)
    app.dependency_overrides[get_current_user] = lambda: user_identity
    app.dependency_overrides[get_statement_service] = lambda: mock_service
    return app


def _make_statements_app_no_service(user_identity: dict) -> FastAPI:
    app = FastAPI()
    app.include_router(statement_router)
    app.dependency_overrides[get_current_user] = lambda: user_identity
    return app


def _make_statements_app_no_auth(mock_service: MagicMock) -> FastAPI:
    app = FastAPI()
    app.include_router(statement_router)
    app.dependency_overrides[get_statement_service] = lambda: mock_service

    def _raise_401():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    app.dependency_overrides[get_current_user] = _raise_401
    return app


@pytest.fixture
def mock_statement_service() -> MagicMock:
    service = MagicMock()
    service.email_statement = AsyncMock(
        return_value=StatementEmailResponse(
            recipient_email="customer@example.com",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 3, 2),
            delivery_status="SENT",
            message="Statement e-mail queued for delivery.",
        )
    )
    return service


@pytest.fixture
def statements_client(mock_statement_service: MagicMock) -> TestClient:
    return TestClient(
        _make_statements_app(CUSTOMER_USER, mock_statement_service),
        raise_server_exceptions=False,
    )


class TestEmailStatementEndpoint:
    """Tests for POST /statements/email."""

    def test_email_statement_returns_200_on_happy_path(self, statements_client: TestClient) -> None:
        response = statements_client.post(
            "/statements/email",
            json={"recipient_email": "request@example.com"},
        )
        assert response.status_code == 200

    def test_email_statement_response_contains_sent_status(
        self,
        statements_client: TestClient,
    ) -> None:
        response = statements_client.post(
            "/statements/email",
            json={"recipient_email": "request@example.com"},
        )
        assert response.json()["delivery_status"] == "SENT"

    def test_email_statement_passes_owner_id_from_jwt(
        self,
        statements_client: TestClient,
        mock_statement_service: MagicMock,
    ) -> None:
        statements_client.post(
            "/statements/email",
            json={"recipient_email": "request@example.com"},
        )
        call_kwargs = mock_statement_service.email_statement.call_args.kwargs
        assert call_kwargs["owner_id"] == OWNER_ID

    def test_email_statement_returns_400_for_validation_exception(
        self,
        mock_statement_service: MagicMock,
    ) -> None:
        mock_statement_service.email_statement = AsyncMock(
            side_effect=ValidationException({"recipient_email": "required"})
        )
        client = TestClient(
            _make_statements_app(CUSTOMER_USER, mock_statement_service),
            raise_server_exceptions=False,
        )

        response = client.post("/statements/email", json={})
        assert response.status_code == 400

    def test_email_statement_400_detail_contains_validation_errors(
        self,
        mock_statement_service: MagicMock,
    ) -> None:
        errors = {"recipient_email": "required"}
        mock_statement_service.email_statement = AsyncMock(side_effect=ValidationException(errors))
        client = TestClient(
            _make_statements_app(CUSTOMER_USER, mock_statement_service),
            raise_server_exceptions=False,
        )

        response = client.post("/statements/email", json={})
        assert response.json()["detail"] == errors

    def test_email_statement_returns_500_for_unhandled_exception(
        self,
        mock_statement_service: MagicMock,
    ) -> None:
        mock_statement_service.email_statement = AsyncMock(side_effect=RuntimeError("boom"))
        client = TestClient(
            _make_statements_app(CUSTOMER_USER, mock_statement_service),
            raise_server_exceptions=False,
        )

        response = client.post("/statements/email", json={})
        assert response.status_code == 500

    def test_email_statement_returns_503_when_service_unavailable(self) -> None:
        client = TestClient(
            _make_statements_app_no_service(CUSTOMER_USER),
            raise_server_exceptions=False,
        )
        response = client.post("/statements/email", json={})
        assert response.status_code == 503

    def test_email_statement_returns_401_when_not_authenticated(
        self,
        mock_statement_service: MagicMock,
    ) -> None:
        client = TestClient(
            _make_statements_app_no_auth(mock_statement_service),
            raise_server_exceptions=False,
        )
        response = client.post("/statements/email", json={})
        assert response.status_code == 401
