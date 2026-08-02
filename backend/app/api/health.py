"""
Health check endpoint.

Exposes a simple liveness endpoint so external tooling (load balancers,
uptime monitors, deployment pipelines) can verify the service is
running, without depending on any other subsystem such as the AI engine.
"""

from typing import Final

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.settings import settings

router: Final[APIRouter] = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Response body for the health check endpoint."""

    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health_check() -> HealthResponse:
    """
    Report that the service is running.

    Returns:
        A HealthResponse confirming the service status, name, and
        current version, sourced from centralized application settings.
    """
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
    )