"""Application bootstrap — startup and shutdown."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.bootstrap.container import get_container
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.observability.tracing import setup_tracing
from app.infrastructure.tools.loader import load_all_tools

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    setup_tracing()
    load_all_tools()

    container = get_container()
    app.state.container = container

    logger.info(
        "application_started",
        app_name=settings.app_name,
        version=__version__,
        env=settings.app_env.value,
        llm_provider=settings.llm_provider.value,
    )
    yield
    await container.shutdown()
    logger.info("application_stopped")
