"""Unit tests for src/api/health.py.

Tests the /health endpoint using a minimal FastAPI test app.
Does NOT import src.main to remain isolated from main.py source bugs.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.health import router as health_router


@pytest.fixture(scope="module")
def health_client() -> TestClient:
    """Create a minimal FastAPI app containing only the health router."""
    app = FastAPI()
    app.include_router(health_router)
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_check_returns_200(self, health_client: TestClient) -> None:
        # Arrange / Act
        response = health_client.get("/health")

        # Assert
        assert response.status_code == 200

    def test_health_check_returns_healthy_status(self, health_client: TestClient) -> None:
        # Arrange / Act
        response = health_client.get("/health")

        # Assert
        assert response.json() == {"status": "healthy"}

    def test_health_check_content_type_is_json(self, health_client: TestClient) -> None:
        # Arrange / Act
        response = health_client.get("/health")

        # Assert
        assert "application/json" in response.headers["content-type"]

    def test_health_check_unknown_path_returns_404(self, health_client: TestClient) -> None:
        # Arrange / Act
        response = health_client.get("/healthz")

        # Assert
        assert response.status_code == 404

    def test_health_check_versioned_path_returns_404(self, health_client: TestClient) -> None:
        # Arrange / Act
        response = health_client.get("/v1/health")

        # Assert
        assert response.status_code == 404
