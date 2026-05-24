"""Multi-agent supervisor — future LangGraph supervisor pattern."""

from app.core.logging import get_logger

logger = get_logger(__name__)


class SupervisorAgent:
    """
    Placeholder for multi-agent orchestration.

    Future: route to specialist agents (billing, users, modules)
    via LangGraph supervisor node.
    """

    async def route(self, message: str, *, agent_ids: list[str]) -> str:
        logger.info("supervisor_route", agent_count=len(agent_ids))
        raise NotImplementedError("Multi-agent supervisor not yet implemented")
