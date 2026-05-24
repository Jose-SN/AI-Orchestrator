"""Agent factory tests."""

from app.domain.agents.config import AgentConfig
from app.infrastructure.agents.factory import ToolCallingAgentFactory
from app.infrastructure.agents.prompts.builder import PromptBuilder


def test_factory_deterministic_config():
    config = AgentConfig(temperature=0.0, seed=42, model_name="qwen2.5:7b")
    factory = ToolCallingAgentFactory(config=config)
    assert factory.config.temperature == 0.0
    assert factory.config.seed == 42


def test_prompt_includes_no_sql_rule():
    builder = PromptBuilder()
    prompt = builder.build_system_prompt(available_tools=["get_customer"])
    assert "NEVER generate SQL" in prompt
    assert "get_customer" in prompt
    assert "TOOL CALLING RULES" in prompt


def test_create_ollama_llm():
    config = AgentConfig(provider="ollama", model_name="qwen2.5:7b", temperature=0.0)
    factory = ToolCallingAgentFactory(config=config)
    llm = factory.create_llm()
    assert llm is not None
