"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.dependencies import get_iam_client, get_microservice_factory
from app.api.middleware.error_handler import register_exception_handlers
from app.api.middleware.logging_middleware import LoggingMiddleware
from app.api.middleware.request_id import RequestIDMiddleware
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.infrastructure.tools.loader import load_all_tools

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    setup_logging()
    load_all_tools()
    logger.info(
        "application_started",
        app_name=settings.app_name,
        version=__version__,
        env=settings.app_env.value,
        llm_provider=settings.llm_provider.value,
    )
    yield
    await get_iam_client().close()
    await get_microservice_factory().close_all()
    logger.info("application_stopped")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI Orchestrator — conversational layer that orchestrates "
            "existing microservice APIs via LangChain tool calling."
        ),
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

    return app


app = create_app()
