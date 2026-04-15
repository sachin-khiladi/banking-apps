"""Unit tests for src/api/profile.py HTTP layer.

Uses a local test-app factory that mocks UserProfileService and
get_current_user so no real Cosmos DB connections are made.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from src.api.profile import get_profile_service, profile_router
from src.auth.oauth2 import get_current_user
from src.exceptions.domain_exceptions import UserProfileNotFoundException
from src.models.user_profile import UserProfileResponse

# ── Constants ──────────────────────────────────────────────────────────────────

OWNER_ID = "user-abc-123"
NOW_ISO = "2026-03-19T10:00:00+00:00"

PROFILE_DOC: dict = {
    "owner_id": OWNER_ID,
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
    "created_at": NOW_ISO,
    "updated_at": NOW_ISO,
}

VALID_PATCH_BODY: dict = {
    "email": "new.email@example.com",
    "mobile_no": "+442071234567",
}

CUSTOMER_USER: dict = {"sub": OWNER_ID, "role": "customer"}

# ── Test app factory ───────────────────────────────────────────────────────────


def _make_profile_app(
    user_identity: dict,
    mock_service: MagicMock,
) -> FastAPI:
    """Build a minimal FastAPI app with profile router and injected mocks."""
    app = FastAPI()
    app.include_router(profile_router)
    app.dependency_overrides[get_current_user] = lambda: user_identity
    app.dependency_overrides[get_profile_service] = lambda: mock_service
    return app


def _make_profile_app_no_service(user_identity: dict) -> FastAPI:
    """Build a FastAPI app without overriding get_profile_service (→ 503)."""
    app = FastAPI()
    app.include_router(profile_router)
    app.dependency_overrides[get_current_user] = lambda: user_identity
    return app


def _make_profile_app_no_auth(mock_service: MagicMock) -> FastAPI:
    """Build a FastAPI app with get_current_user raising 401."""
    app = FastAPI()
    app.include_router(profile_router)
    app.dependency_overrides[get_profile_service] = lambda: mock_service

    def _raise_401():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    app.dependency_overrides[get_current_user] = _raise_401
    return app


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_profile_service() -> MagicMock:
    """Provide a fully-mocked UserProfileService with sensible defaults."""
    service = MagicMock()
    profile_resp = UserProfileResponse(**PROFILE_DOC)
    service.get_profile = AsyncMock(return_value=profile_resp)
    service.update_profile = AsyncMock(return_value=profile_resp)
    return service


@pytest.fixture
def profile_client(mock_profile_service: MagicMock) -> TestClient:
    """TestClient with customer identity and mocked profile service."""
    return TestClient(
        _make_profile_app(CUSTOMER_USER, mock_profile_service),
        raise_server_exceptions=False,
    )


# ── GET /profile ───────────────────────────────────────────────────────────────


class TestGetProfileEndpoint:
    """Tests for GET /profile."""

    def test_get_profile_returns_200_on_happy_path(
        self, profile_client: TestClient
    ) -> None:
        response = profile_client.get("/profile")
        assert response.status_code == 200

    def test_get_profile_response_contains_owner_id(
        self, profile_client: TestClient
    ) -> None:
        response = profile_client.get("/profile")
        assert response.json()["owner_id"] == OWNER_ID

    def test_get_profile_response_contains_email(
        self, profile_client: TestClient
    ) -> None:
        response = profile_client.get("/profile")
        assert response.json()["email"] == "jane.doe@example.com"

    def test_get_profile_response_contains_mobile_no(
        self, profile_client: TestClient
    ) -> None:
        response = profile_client.get("/profile")
        assert response.json()["mobile_no"] == "+12065550100"

    def test_get_profile_calls_service_with_owner_id(
        self, profile_client: TestClient, mock_profile_service: MagicMock
    ) -> None:
        profile_client.get("/profile")
        mock_profile_service.get_profile.assert_called_once_with(OWNER_ID)

    def test_get_profile_returns_404_when_not_found(
        self, mock_profile_service: MagicMock
    ) -> None:
        mock_profile_service.get_profile = AsyncMock(
            side_effect=UserProfileNotFoundException(OWNER_ID)
        )
        client = TestClient(
            _make_profile_app(CUSTOMER_USER, mock_profile_service),
            raise_server_exceptions=False,
        )
        response = client.get("/profile")
        assert response.status_code == 404

    def test_get_profile_404_detail_mentions_not_found(
        self, mock_profile_service: MagicMock
    ) -> None:
        mock_profile_service.get_profile = AsyncMock(
            side_effect=UserProfileNotFoundException(OWNER_ID)
        )
        client = TestClient(
            _make_profile_app(CUSTOMER_USER, mock_profile_service),
            raise_server_exceptions=False,
        )
        response = client.get("/profile")
        assert "not found" in response.json()["detail"].lower()

    def test_get_profile_returns_401_when_no_token(
        self, mock_profile_service: MagicMock
    ) -> None:
        client = TestClient(
            _make_profile_app_no_auth(mock_profile_service),
            raise_server_exceptions=False,
        )
        response = client.get("/profile")
        assert response.status_code == 401

    def test_get_profile_returns_503_when_service_unavailable(self) -> None:
        client = TestClient(
            _make_profile_app_no_service(CUSTOMER_USER),
            raise_server_exceptions=False,
        )
        response = client.get("/profile")
        assert response.status_code == 503

    def test_get_profile_unexpected_exception_returns_500(
        self, mock_profile_service: MagicMock
    ) -> None:
        mock_profile_service.get_profile = AsyncMock(
            side_effect=RuntimeError("disk full")
        )
        client = TestClient(
            _make_profile_app(CUSTOMER_USER, mock_profile_service),
            raise_server_exceptions=False,
        )
        response = client.get("/profile")
        assert response.status_code == 500


# ── PATCH /profile ─────────────────────────────────────────────────────────────


class TestUpdateProfileEndpoint:
    """Tests for PATCH /profile."""

    def test_update_profile_returns_200_on_happy_path(
        self, profile_client: TestClient
    ) -> None:
        response = profile_client.patch("/profile", json=VALID_PATCH_BODY)
        assert response.status_code == 200

    def test_update_profile_response_contains_owner_id(
        self, profile_client: TestClient
    ) -> None:
        response = profile_client.patch("/profile", json=VALID_PATCH_BODY)
        assert response.json()["owner_id"] == OWNER_ID

    def test_update_profile_calls_service_update_profile(
        self, profile_client: TestClient, mock_profile_service: MagicMock
    ) -> None:
        profile_client.patch("/profile", json=VALID_PATCH_BODY)
        mock_profile_service.update_profile.assert_called_once()

    def test_update_profile_passes_owner_id_from_jwt(
        self, profile_client: TestClient, mock_profile_service: MagicMock
    ) -> None:
        profile_client.patch("/profile", json=VALID_PATCH_BODY)
        call_args = mock_profile_service.update_profile.call_args
        assert call_args[0][0] == OWNER_ID

    def test_update_profile_upsert_on_missing_profile_returns_200(
        self, mock_profile_service: MagicMock
    ) -> None:
        """PATCH must succeed (200) even when no existing profile (upsert)."""
        upserted_profile = UserProfileResponse(**PROFILE_DOC)
        mock_profile_service.update_profile = AsyncMock(return_value=upserted_profile)
        client = TestClient(
            _make_profile_app(CUSTOMER_USER, mock_profile_service),
            raise_server_exceptions=False,
        )
        response = client.patch("/profile", json=VALID_PATCH_BODY)
        assert response.status_code == 200

    def test_update_profile_invalid_email_returns_422(
        self, profile_client: TestClient
    ) -> None:
        response = profile_client.patch("/profile", json={"email": "not-an-email"})
        assert response.status_code == 422

    def test_update_profile_invalid_mobile_no_returns_422(
        self, profile_client: TestClient
    ) -> None:
        response = profile_client.patch("/profile", json={"mobile_no": "07700900123"})
        assert response.status_code == 422

    def test_update_profile_invalid_country_code_returns_422(
        self, profile_client: TestClient
    ) -> None:
        """Country code must be exactly 2 chars; 3-char code is invalid."""
        response = profile_client.patch(
            "/profile",
            json={
                "address": {
                    "line1": "123 Main Street",
                    "city": "Seattle",
                    "state": "WA",
                    "postal_code": "98101",
                    "country": "USA",  # 3-char — should fail max_length=2
                }
            },
        )
        assert response.status_code == 422

    def test_update_profile_empty_body_is_valid_no_op(
        self, profile_client: TestClient
    ) -> None:
        """Sending an empty body is valid — all fields are optional in PATCH."""
        response = profile_client.patch("/profile", json={})
        assert response.status_code == 200

    def test_update_profile_unexpected_exception_returns_500(
        self, mock_profile_service: MagicMock
    ) -> None:
        mock_profile_service.update_profile = AsyncMock(
            side_effect=RuntimeError("unexpected")
        )
        client = TestClient(
            _make_profile_app(CUSTOMER_USER, mock_profile_service),
            raise_server_exceptions=False,
        )
        response = client.patch("/profile", json=VALID_PATCH_BODY)
        assert response.status_code == 500
