"""Tool loader — imports all tool modules to populate the registry."""

from app.core.logging import get_logger

logger = get_logger(__name__)


def load_all_tools() -> None:
    """
    Import all tool definition modules to trigger @register_tool decorators.

    Add new tool modules here as the platform grows.
    """
    from app.infrastructure.tools.definitions import module_tools, user_tools  # noqa: F401

    logger.info("tools_loaded")
