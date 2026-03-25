"""FastAPI application entry point.

Initialises the app, registers middleware, mounts routers, and
wires all dependency-injection bindings.
"""

from __future__ import annotations

from pathlib import Path

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
    app.dependency_overrides[get_account_service] = lambda: AccountService(_account_repo)
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
