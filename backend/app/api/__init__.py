"""
API package for the VanRakshak AI backend.

Aggregates all versioned API routers into a single `api_router` that the
application entry point can include. Individual endpoint modules
(health, predict, location) define their own routes; this file only
composes them under the shared API version prefix.
"""

from typing import Final

from fastapi import APIRouter

from app.api import health, location, predict
from app.core.constants import API_V1_PREFIX

api_router: Final[APIRouter] = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(health.router)
api_router.include_router(predict.router)
api_router.include_router(location.router)

__all__ = ["api_router"]
