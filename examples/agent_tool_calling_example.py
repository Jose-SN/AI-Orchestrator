"""
LangChain tool-calling agent examples.

Demonstrates deterministic, tool-only agent behavior with Ollama + Qwen2.5.
"""

from app.domain.agents.config import AgentConfig
from app.domain.auth.models import UserContext
from app.infrastructure.agents.config import load_agent_config
from app.infrastructure.agents.factory import ToolCallingAgentFactory
from app.infrastructure.agents.parsers.output_parser import AgentOutputParser
from app.infrastructure.agents.prompts.builder import PromptBuilder
from app.infrastructure.tools.loader import load_all_tools
from app.infrastructure.tools.registry import tool_registry


def example_agent_config():
    """Load agent config from environment (deterministic defaults)."""
    config = load_agent_config()
    print("Model:", config.model_name)
    print("Temperature:", config.temperature)  # 0.0 = deterministic
    print("Seed:", config.seed)
    print("Max iterations:", config.max_iterations)
    print("Prompt template:", config.prompt_template)


def example_custom_config():
    """Override config for stricter deterministic behavior."""
    config = AgentConfig(
        model_name="qwen2.5:7b",
        temperature=0.0,
        seed=42,
        max_iterations=5,
        prompt_template="orchestrator",
    )
    factory = ToolCallingAgentFactory(config=config)
    llm = factory.create_llm()
    print("LLM created:", type(llm).__name__)


def example_prompt_builder():
    """Build configurable system prompt with tool list."""
    builder = PromptBuilder(template_key="orchestrator")
    prompt = builder.build_system_prompt(
        user_display_name="Alice",
        available_tools=["get_customer", "list_customers", "search_customers"],
    )
    print("System prompt preview:", prompt[:200], "...")


def example_output_parser():
    """Parse structured agent output from mock LangGraph result."""
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    parser = AgentOutputParser()
    raw = {
        "messages": [
            HumanMessage(content="Find customer John"),
            AIMessage(content="", tool_calls=[{
                "id": "call_1", "name": "search_customers", "args": {"query": "John"}
            }]),
            ToolMessage(content='{"success":true,"data":[{"name":"John Doe"}]}', tool_call_id="call_1"),
            AIMessage(content="I found John Doe in the customer records."),
        ]
    }
    result = parser.parse(raw, conversation_id="conv-1", provider="ollama", model="qwen2.5:7b")
    print("Response:", result.response)
    print("Tools used:", [t.tool_name for t in result.tool_calls])


def example_tool_loading():
    """Show how IAM permissions filter available tools."""
    load_all_tools()
    user = UserContext(user_id="u1", permissions=["customers:read", "customers:search"])
    allowed = tool_registry.get_allowed_definitions(user.effective_permissions)
    print("Tools available to agent:", [t.name for t in allowed])


if __name__ == "__main__":
    example_agent_config()
    example_custom_config()
    example_prompt_builder()
    example_output_parser()
    example_tool_loading()
