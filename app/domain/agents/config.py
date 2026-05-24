"""Agent behavior configuration."""

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Deterministic, tool-calling-only agent configuration."""

    model_name: str = "qwen2.5:7b"
    provider: str = "ollama"
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    seed: int | None = 42
    max_iterations: int = Field(default=8, ge=1, le=20)
    max_tool_calls: int = Field(default=5, ge=1, le=20)
    timeout_seconds: int = 120
    prompt_template: str = "orchestrator"
    enable_memory: bool = False
    verbose: bool = False

    model_config = {"frozen": True}
