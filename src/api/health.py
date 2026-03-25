"""Health-check API routes."""

from fastapi import APIRouter, status

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Return service health for deployment/runtime probes."""
    return {"status": "healthy"}
