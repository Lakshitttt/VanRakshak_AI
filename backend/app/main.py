"""
Application entry point for the VanRakshak AI backend.

Creates and configures the FastAPI application instance. This file is
intentionally minimal: it wires together configuration, logging, and
middleware. No API routes, AI inference logic, or frontend logic live
here — those are added in later tasks per the approved architecture.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.exceptions import VanRakshakException
from app.core.logging import configure_logging, get_logger
from app.core.settings import settings

logger: logging.Logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manage application startup and shutdown events.

    On startup: configures logging so that every subsequent log call in
    the process is captured consistently. Future startup steps (such as
    loading the AI model singleton) will be added here once those
    features are implemented — none exist yet in this foundation task.

    On shutdown: logs a clean shutdown message. Future cleanup steps
    (such as releasing model resources) will be added here as needed.

    Args:
        app: The FastAPI application instance being started.
    """
    configure_logging()
    logger.info(
        "Starting %s v%s (%s environment)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )

    yield

    logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """
    Application factory for the VanRakshak AI FastAPI instance.

    Returns:
        A fully configured FastAPI application with lifespan events,
        CORS middleware, and a global exception handler registered.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # ==========================================
    # CORS Middleware configured for local frontend
    # ==========================================
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins (resolves the CORS error)
        allow_credentials=True,
        allow_methods=["*"],  # Allows all HTTP methods (POST, GET, OPTIONS, etc.)
        allow_headers=["*"],  # Allows all headers
    )
    
    # Include all API routes
    application.include_router(api_router)

    @application.exception_handler(VanRakshakException)
    async def vanrakshak_exception_handler(
        request: Request, exc: VanRakshakException
    ) -> JSONResponse:
        """
        Convert any VanRakshakException into a consistent JSON error response.

        This handler ensures that every custom application exception,
        regardless of which future service raises it, is surfaced to
        clients in the same shape.

        Args:
            request: The incoming request that triggered the exception.
            exc: The raised VanRakshakException (or subclass) instance.

        Returns:
            A JSONResponse with a consistent error payload shape.
        """
        logger.error(
            "VanRakshakException: %s | details=%s",
            exc.message,
            exc.details,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
            },
        )

    return application


app: FastAPI = create_app()