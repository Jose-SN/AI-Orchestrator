"""Backward-compatible alias — delegates to ToolCallingAgent."""

from app.infrastructure.agents.tool_calling_agent import ToolCallingAgent

LangGraphOrchestratorAgent = ToolCallingAgent

__all__ = ["LangGraphOrchestratorAgent", "ToolCallingAgent"]
