"""Unit tests for src/main.py.

Covers app metadata, CORS middleware, registered routes, root endpoint,
and both dependency-wiring paths (repo available vs env vars absent).

IMPORTANT — import order matters:
  src/logging/app_insights.py uses `from opentelemetry.ext.azure import AzureLogHandler`
  which is the legacy import path not provided by azure-monitor-opentelemetry-exporter.
  We stub both that module and src.logging.app_insights in sys.modules *before*
  importing src.main so the module-level side effects are contained.
"""

from __future__ import annotations

import importlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Stub incompatible Azure/OTel modules before src.main is imported ──────────
# app_insights.py does `from opentelemetry.ext.azure import AzureLogHandler`
# at module level; that symbol is absent from azure-monitor-opentelemetry-exporter.
sys.modules.setdefault("opentelemetry.ext.azure", MagicMock())
_mock_app_insights = MagicMock()
_mock_app_insights.setup_logging = MagicMock()
sys.modules.setdefault("src.logging.app_insights", _mock_app_insights)

from fastapi.testclient import TestClient  # noqa: E402

import src.main as main_module  # noqa: E402 — imported after stubs registered

from src.api.accounts import get_account_service  # noqa: E402
from src.api.profile import get_profile_service  # noqa: E402
from src.api.statements import get_statement_service  # noqa: E402


# ── Convenience client ────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def main_client() -> TestClient:
    """TestClient backed by the real src.main app (stubs applied at module level)."""
    return TestClient(main_module.app, raise_server_exceptions=False)


# ── App metadata ──────────────────────────────────────────────────────────────

class TestAppMetadata:
    """Tests for FastAPI app metadata set in the factory call."""

    def test_app_title_is_banking_system_api(self) -> None:
        assert main_module.app.title == "Banking System API"

    def test_app_version_is_1_0_0(self) -> None:
        assert main_module.app.version == "1.0.0"

    def test_app_description_mentions_banking(self) -> None:
        assert "banking" in main_module.app.description.lower()

    def test_app_is_fastapi_instance(self) -> None:
        from fastapi import FastAPI
        assert isinstance(main_module.app, FastAPI)


# ── CORS middleware ───────────────────────────────────────────────────────────

class TestCorsMiddleware:
    """Tests that CORS middleware is present and functional."""

    def test_cors_middleware_is_registered(self) -> None:
        # user_middleware is a list of starlette Middleware(cls, **kwargs) namedtuples
        class_names = [m.cls.__name__ for m in main_module.app.user_middleware
                       if hasattr(m, "cls")]
        assert any("CORS" in n for n in class_names)

    def test_cors_preflight_includes_allow_origin_header(
        self, main_client: TestClient
    ) -> None:
        response = main_client.options(
            "/health",
            headers={
                "Origin": "http://testclient.test",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in response.headers


# ── Route registration ────────────────────────────────────────────────────────

class TestRouteRegistration:
    """Tests that all expected routes are registered on the app."""

    def _route_paths(self) -> list[str]:
        return [r.path for r in main_module.app.routes if hasattr(r, "path")]

    def test_health_route_is_registered(self) -> None:
        assert "/health" in self._route_paths()

    def test_root_route_is_registered(self) -> None:
        assert "/" in self._route_paths()

    def test_accounts_customer_route_is_registered(self) -> None:
        assert any("/accounts" in p for p in self._route_paths())

    def test_accounts_admin_route_is_registered(self) -> None:
        assert any("/admin/accounts" in p for p in self._route_paths())

    def test_statements_email_route_is_registered(self) -> None:
        assert "/statements/email" in self._route_paths()


# ── /health endpoint ──────────────────────────────────────────────────────────

class TestHealthEndpointViaMainApp:
    """Tests GET /health through the fully-assembled src.main app."""

    def test_health_returns_200(self, main_client: TestClient) -> None:
        response = main_client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, main_client: TestClient) -> None:
        response = main_client.get("/health")
        assert response.json() == {"status": "healthy"}

    def test_health_content_type_is_json(self, main_client: TestClient) -> None:
        response = main_client.get("/health")
        assert "application/json" in response.headers["content-type"]


# ── / root endpoint ───────────────────────────────────────────────────────────

class TestRootEndpoint:
    """Tests GET / through the fully-assembled src.main app."""

    def test_root_returns_200(self, main_client: TestClient) -> None:
        response = main_client.get("/")
        assert response.status_code == 200

    def test_root_response_contains_message_key(self, main_client: TestClient) -> None:
        response = main_client.get("/")
        assert "message" in response.json()

    def test_root_message_mentions_banking(self, main_client: TestClient) -> None:
        response = main_client.get("/")
        assert "Banking" in response.json()["message"]


# ── Dependency wiring — repo available ───────────────────────────────────────

class TestDependencyWiringRepoAvailable:
    """Tests the happy path where CosmosAccountRepository is available."""

    def test_get_account_service_override_is_set(self) -> None:
        # conftest.py sets COSMOS_ACCOUNT_URL + COSMOS_DB_NAME before tests run,
        # so src.main's try-block succeeds and registers the override.
        assert get_account_service in main_module.app.dependency_overrides

    def test_get_account_service_override_is_callable(self) -> None:
        override = main_module.app.dependency_overrides[get_account_service]
        assert callable(override)

    def test_account_repo_module_variable_is_not_none(self) -> None:
        assert main_module._account_repo is not None

    def test_get_profile_service_override_is_set(self) -> None:
        assert get_profile_service in main_module.app.dependency_overrides

    def test_statement_service_override_is_set_when_repos_available(self) -> None:
        assert get_statement_service in main_module.app.dependency_overrides


# ── Dependency wiring — env vars absent ──────────────────────────────────────

class TestDependencyWiringEnvVarsAbsent:
    """Tests the fallback path when env vars are missing."""

    def test_account_repo_is_none_when_env_vars_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Remove env vars so CosmosAccountRepository.__init__ raises RepositoryException
        monkeypatch.delenv("COSMOS_ACCOUNT_URL", raising=False)
        monkeypatch.delenv("COSMOS_DB_NAME", raising=False)

        # Reload the module so the try/except block re-executes without env vars
        with patch.dict(sys.modules, {"src.logging.app_insights": _mock_app_insights}):
            importlib.reload(main_module)

        assert main_module._account_repo is None

        # Restore: re-reload with env vars so other tests are not affected
        monkeypatch.setenv("COSMOS_ACCOUNT_URL", "https://test.documents.azure.com:443/")
        monkeypatch.setenv("COSMOS_DB_NAME", "test_banking_db")
        with patch.dict(sys.modules, {"src.logging.app_insights": _mock_app_insights}):
            importlib.reload(main_module)

    def test_profile_repo_is_none_when_profile_repository_import_fails(self) -> None:
        original_import = __import__

        def _raise_for_profile_repo(name, globals_=None, locals_=None, fromlist=(), level=0):
            if name == "src.repository.cosmos_user_profile_repository":
                raise ImportError("simulated profile repository import failure")
            return original_import(name, globals_, locals_, fromlist, level)

        with patch("builtins.__import__", side_effect=_raise_for_profile_repo):
            with patch.dict(sys.modules, {"src.logging.app_insights": _mock_app_insights}):
                importlib.reload(main_module)

        assert main_module._user_profile_repo is None
        assert get_profile_service not in main_module.app.dependency_overrides
        assert get_statement_service not in main_module.app.dependency_overrides

        with patch.dict(sys.modules, {"src.logging.app_insights": _mock_app_insights}):
            importlib.reload(main_module)

    def test_app_is_still_usable_when_repo_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("COSMOS_ACCOUNT_URL", raising=False)
        monkeypatch.delenv("COSMOS_DB_NAME", raising=False)

        with patch.dict(sys.modules, {"src.logging.app_insights": _mock_app_insights}):
            importlib.reload(main_module)

        client = TestClient(main_module.app, raise_server_exceptions=False)
        response = client.get("/health")
        assert response.status_code == 200

        # Restore
        monkeypatch.setenv("COSMOS_ACCOUNT_URL", "https://test.documents.azure.com:443/")
        monkeypatch.setenv("COSMOS_DB_NAME", "test_banking_db")
        with patch.dict(sys.modules, {"src.logging.app_insights": _mock_app_insights}):
            importlib.reload(main_module)

    def test_statement_service_override_not_set_when_account_repo_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("COSMOS_ACCOUNT_URL", raising=False)
        monkeypatch.delenv("COSMOS_DB_NAME", raising=False)

        with patch.dict(sys.modules, {"src.logging.app_insights": _mock_app_insights}):
            importlib.reload(main_module)

        assert get_statement_service not in main_module.app.dependency_overrides

        monkeypatch.setenv("COSMOS_ACCOUNT_URL", "https://test.documents.azure.com:443/")
        monkeypatch.setenv("COSMOS_DB_NAME", "test_banking_db")
        with patch.dict(sys.modules, {"src.logging.app_insights": _mock_app_insights}):
            importlib.reload(main_module)
