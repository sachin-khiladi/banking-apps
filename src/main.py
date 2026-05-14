"""FastAPI application entry point.

Initialises the app, registers middleware, mounts routers, and
wires all dependency-injection bindings.

The application startup path remains intentionally decoupled from CI/CD
or Terraform workflow sequencing. Deployment probes depend on the `/health`
route contract and do not require pipeline-state inputs.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.accounts import (
    admin_router,
    customer_router,
    get_account_service,
)
from src.api.health import router as health_router
from src.api.profile import get_profile_service, profile_router
from src.api.statements import get_statement_service, statement_router
from src.exceptions.domain_exceptions import RepositoryException
from src.logging.app_insights import setup_logging
from src.services.account_service import AccountService
from src.services.statement_service import StatementService
from src.services.user_profile_service import UserProfileService

logger = logging.getLogger(__name__)

_REQUIRED_IDENTITY_ENV_RULES: tuple[tuple[str, str, Callable[[str], bool]], ...] = (
    (
        "COSMOS_ACCOUNT_URL",
        "must be an HTTPS endpoint",
        lambda value: value.startswith("https://"),
    ),
    ("COSMOS_DB_NAME", "must be non-empty", lambda value: bool(value.strip())),
    (
        "AZURE_APP_CONFIG_ENDPOINT",
        "must be an HTTPS endpoint",
        lambda value: value.startswith("https://"),
    ),
    (
        "AZURE_KEY_VAULT_URI",
        "must be an HTTPS endpoint",
        lambda value: value.startswith("https://"),
    ),
)

_OPTIONAL_ACR_REFERENCE_ENV_NAMES: tuple[str, ...] = (
    "ACR_LOGIN_SERVER",
    "AZURE_ACR_LOGIN_SERVER",
    "CONTAINER_REGISTRY_URL",
)

# Load .env from the project root (no-op when the file is absent)
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# ── Application factory ───────────────────────────────────────────────────────

app = FastAPI(
    title="Banking System API",
    version="1.0.0",
    description="FastAPI banking backend running on Azure Container Apps.",
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict origins for production deployments.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Logging ───────────────────────────────────────────────────────────────────

setup_logging()


def _validate_identity_runtime_configuration() -> None:
    """Validate managed-identity runtime configuration before app startup.

    This check validates non-secret environment variables only. It intentionally
    does not instantiate Azure SDK clients.

    Raises:
        RepositoryException: If mandatory identity-dependent configuration is
            missing or malformed.
    """
    missing_required: list[str] = []
    invalid_required: list[str] = []

    for env_name, requirement, validator in _REQUIRED_IDENTITY_ENV_RULES:
        env_value = os.environ.get(env_name, "")
        if not env_value:
            missing_required.append(env_name)
            continue
        if not validator(env_value):
            invalid_required.append(f"{env_name} ({requirement})")

    invalid_optional_registry: list[str] = []
    for env_name in _OPTIONAL_ACR_REFERENCE_ENV_NAMES:
        env_value = os.environ.get(env_name)
        if env_value and not env_value.endswith(".azurecr.io"):
            invalid_optional_registry.append(f"{env_name} (must end with .azurecr.io)")

    missing_required = sorted(missing_required)
    invalid_required = sorted(invalid_required)
    invalid_optional_registry = sorted(invalid_optional_registry)

    if missing_required or invalid_required or invalid_optional_registry:
        if missing_required:
            logger.error(
                (
                    "Startup preflight failed. Missing required managed-identity "
                    "identity configuration keys: %s"
                ),
                ", ".join(missing_required),
            )
        if invalid_required:
            logger.error(
                (
                    "Startup preflight failed. Invalid required managed-identity "
                    "configuration keys: %s"
                ),
                ", ".join(invalid_required),
            )
        if invalid_optional_registry:
            logger.error(
                (
                    "Startup preflight failed. Invalid optional ACR endpoint "
                    "references: %s"
                ),
                ", ".join(invalid_optional_registry),
            )
        raise RepositoryException(
            (
                "Application startup preflight failed due to incomplete managed "
                "identity configuration. Verify required environment variables "
                "are set with valid endpoint values."
            )
        )

    logger.info("Startup preflight passed for managed-identity runtime configuration.")


@app.on_event("startup")
async def startup_preflight() -> None:
    """Run startup preflight checks for identity-dependent runtime configuration."""
    _validate_identity_runtime_configuration()


# ── Dependency wiring ─────────────────────────────────────────────────────────
# The concrete CosmosAccountRepository is injected here so service and API
# layers only ever depend on the IAccountRepository interface.
#
# cosmosdb-repo-agent will generate CosmosAccountRepository.
# Once that module exists, replace the lambda below with:
#
#   from src.repository.cosmos_account_repository import CosmosAccountRepository
#   _account_repo = CosmosAccountRepository()
#   app.dependency_overrides[get_account_service] = lambda: AccountService(_account_repo)

try:
    from src.repository.cosmos_account_repository import CosmosAccountRepository  # type: ignore

    _account_repo = CosmosAccountRepository()
    app.dependency_overrides[get_account_service] = lambda: AccountService(
        _account_repo
    )
except (ImportError, RepositoryException):
    # Repository not available (missing module or missing env vars).
    # Service will raise NotImplementedError at runtime until wired.
    _account_repo = None  # type: ignore[assignment]

try:
    from src.repository.cosmos_user_profile_repository import (  # type: ignore
        CosmosUserProfileRepository,
    )

    _user_profile_repo = CosmosUserProfileRepository()
    app.dependency_overrides[get_profile_service] = lambda: UserProfileService(
        _user_profile_repo
    )
except (ImportError, RepositoryException):
    # Repository not available (missing module or missing env vars).
    # Service will raise HTTP 503 at request time until wired.
    _user_profile_repo = None  # type: ignore[assignment]

if _account_repo is not None and _user_profile_repo is not None:
    statement_account_repo = _account_repo
    statement_profile_repo = _user_profile_repo
    app.dependency_overrides[get_statement_service] = lambda: StatementService(
        statement_account_repo,
        statement_profile_repo,
    )

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health_router)
app.include_router(customer_router)
app.include_router(admin_router)
app.include_router(profile_router)
app.include_router(statement_router)


# ── Root ──────────────────────────────────────────────────────────────────────


@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint — returns a welcome message."""
    return {"message": "Welcome to the Banking System API."}
