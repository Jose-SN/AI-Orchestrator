"""Agent bounded context — multi-agent domain concepts."""

from enum import Enum

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    ORCHESTRATOR = "orchestrator"
    SPECIALIST = "specialist"
    SUPERVISOR = "supervisor"


class AgentDefinition(BaseModel):
    """Declarative agent config for the multi-agent registry."""

    id: str
    name: str
    description: str
    agent_type: AgentType = AgentType.ORCHESTRATOR
    system_prompt_key: str = "orchestrator"
    tool_categories: list[str] = Field(default_factory=list)
    enabled: bool = True
