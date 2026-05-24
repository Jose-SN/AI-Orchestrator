"""OpenTelemetry tracing bootstrap — enable via OTEL_ENABLED=true."""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_tracing() -> None:
    """Initialize distributed tracing when OTEL is enabled."""
    if not settings.otel_enabled:
        logger.debug("tracing_disabled")
        return

    # Placeholder: wire opentelemetry-sdk + exporter when deploying to production
    logger.info(
        "tracing_ready",
        service=settings.otel_service_name,
        endpoint=settings.otel_exporter_endpoint or "default",
    )
