"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap.lifespan import lifespan
from app.core.config import settings
from app.presentation.http.middleware.error_handler import register_exception_handlers
from app.presentation.http.middleware.logging import LoggingMiddleware
from app.presentation.http.middleware.request_id import RequestIDMiddleware
from app.presentation.http.v1.router import api_v1_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI Orchestrator — conversational API orchestration layer.",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    register_exception_handlers(app)
    app.include_router(api_v1_router)

    if settings.websocket_enabled:
        from app.presentation.websocket.router import register_websocket_routes

        register_websocket_routes(app)

    return app
