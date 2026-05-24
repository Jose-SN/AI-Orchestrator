"""Agent configuration loader from application settings."""

from app.core.config import settings
from app.domain.agents.config import AgentConfig


def load_agent_config(
    *,
    prompt_template: str | None = None,
    temperature: float | None = None,
) -> AgentConfig:
    """Build AgentConfig from environment settings."""
    return AgentConfig(
        model_name=settings.ollama_model,
        provider=settings.llm_provider.value,
        temperature=temperature if temperature is not None else settings.agent_temperature,
        top_p=settings.agent_top_p,
        seed=settings.agent_seed,
        max_iterations=settings.agent_max_iterations,
        max_tool_calls=settings.agent_max_tool_calls,
        timeout_seconds=settings.ollama_timeout_seconds,
        prompt_template=prompt_template or settings.agent_prompt_template,
        enable_memory=settings.agent_memory_enabled,
        verbose=settings.agent_verbose,
    )
