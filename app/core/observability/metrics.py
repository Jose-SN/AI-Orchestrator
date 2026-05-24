"""Metrics hooks — ready for Prometheus/OpenTelemetry integration."""

from app.core.logging import get_logger

logger = get_logger(__name__)

_counters: dict[str, int] = {}


def increment_counter(name: str, value: int = 1, **labels: str) -> None:
    """In-process counter stub. Replace with OTel/Prometheus exporter in production."""
    key = f"{name}:{labels}" if labels else name
    _counters[key] = _counters.get(key, 0) + value
    logger.debug("metric_counter", name=name, value=value, labels=labels)


def get_counter(name: str) -> int:
    return _counters.get(name, 0)
