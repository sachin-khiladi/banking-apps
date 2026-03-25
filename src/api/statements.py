"""Statement API route handlers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.oauth2 import get_current_user
from src.exceptions.domain_exceptions import ValidationException
from src.models.statement import StatementEmailRequest, StatementEmailResponse
from src.services.statement_service import StatementService

statement_router = APIRouter(prefix="/statements", tags=["statements"])


def get_statement_service() -> StatementService:
    """Dependency placeholder; real factory wired in main.py.

    Raises:
        HTTPException: Always raised with 503 when service is not wired.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Statement service unavailable: repositories and SMTP configuration "
            "must be set."
        ),
    )


StatementServiceDep = Annotated[StatementService, Depends(get_statement_service)]
CurrentUser = Annotated[dict, Depends(get_current_user)]


def _raise_http(exc: Exception) -> None:
    """Translate domain exceptions to HTTP responses.

    Args:
        exc: Exception instance raised from service layer.

    Raises:
        HTTPException: Always raised with mapped status code.
    """
    if isinstance(exc, ValidationException):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.errors,
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred.",
    )


@statement_router.post(
    "/email",
    response_model=StatementEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="E-mail monthly statement",
    description=(
        "Sends a statement e-mail to the authenticated user. If recipient_email "
        "is omitted, the profile e-mail is used."
    ),
)
async def email_statement(
    payload: StatementEmailRequest,
    service: StatementServiceDep,
    current_user: CurrentUser,
) -> StatementEmailResponse:
    """Dispatch a statement e-mail for the authenticated user.

    Args:
        payload: Statement request payload.
        service: Injected StatementService.
        current_user: Decoded JWT claims.

    Returns:
        StatementEmailResponse with effective recipient and period.
    """
    try:
        owner_id = current_user["sub"]
        return await service.email_statement(owner_id=owner_id, payload=payload)
    except Exception as exc:
        _raise_http(exc)