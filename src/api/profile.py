"""User profile API route handlers.

Single router group:
  profile_router (/profile) — authenticated user read/update of own profile.

All business logic is delegated to UserProfileService.
"""

from __future__ import annotations

import logging
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.oauth2 import get_current_user
from src.exceptions.domain_exceptions import UserProfileNotFoundException
from src.models.user_profile import UserProfileResponse, UserProfileUpdateRequest
from src.services.user_profile_service import UserProfileService

# ── Router ────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

profile_router = APIRouter(prefix="/profile", tags=["profile"])


# ── Dependency stubs — overridden in main.py ──────────────────────────────────


def get_profile_service() -> UserProfileService:
    """Dependency placeholder; real factory wired in main.py.

    Raises HTTP 503 so callers get a meaningful error when Cosmos DB is not
    configured (COSMOS_ACCOUNT_URL / COSMOS_DB_NAME env vars missing).
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Profile service unavailable: COSMOS_ACCOUNT_URL and COSMOS_DB_NAME must be set.",
    )


ProfileServiceDep = Annotated[UserProfileService, Depends(get_profile_service)]
CurrentUser = Annotated[dict, Depends(get_current_user)]


# ── Domain exception to HTTP response mapping ─────────────────────────────────


def _raise_http(exc: Exception) -> NoReturn:
    """Translate a domain exception to an HTTPException.

    Args:
        exc: Domain-layer exception to translate.

    Raises:
        HTTPException: Always raised with the appropriate HTTP status code.
    """
    if isinstance(exc, UserProfileNotFoundException):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    logger.exception("Unexpected exception in profile API handler", exc_info=exc)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred.",
    ) from exc


# ── Profile routes ────────────────────────────────────────────────────────────


@profile_router.get(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get own user profile",
    description="Returns the full user profile for the authenticated user.",
)
async def get_profile(
    service: ProfileServiceDep,
    current_user: CurrentUser,
) -> UserProfileResponse:
    """Return the user profile for the authenticated user.

    Args:
        service: Injected UserProfileService.
        current_user: Decoded JWT payload provided by get_current_user.

    Returns:
        UserProfileResponse for the authenticated user.

    Raises:
        HTTPException: 404 if no profile exists; 503 if service unavailable.
    """
    try:
        return await service.get_profile(current_user["sub"])
    except Exception as exc:
        _raise_http(exc)


@profile_router.patch(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update own user profile",
    description=(
        "Partially update the authenticated user's profile. "
        "Only supplied (non-null) fields are merged; omitted fields are unchanged. "
        "Creates the profile if it does not yet exist (upsert semantics)."
    ),
)
async def update_profile(
    payload: UserProfileUpdateRequest,
    service: ProfileServiceDep,
    current_user: CurrentUser,
) -> UserProfileResponse:
    """Partially update the user profile for the authenticated user.

    Args:
        payload: UserProfileUpdateRequest with optional fields to update.
        service: Injected UserProfileService.
        current_user: Decoded JWT payload provided by get_current_user.

    Returns:
        UserProfileResponse reflecting the merged state after the update.

    Raises:
        HTTPException: 422 for validation errors (automatic); 503 if service
            unavailable.
    """
    try:
        return await service.update_profile(current_user["sub"], payload)
    except Exception as exc:
        _raise_http(exc)
