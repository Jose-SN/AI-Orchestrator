"""Factory for LangChain tool-calling agents."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import StructuredTool
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from app.core.config import settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger
from app.domain.agents.config import AgentConfig
from app.infrastructure.agents.config import load_agent_config
from app.infrastructure.agents.memory.store import ConversationMemoryStore
from app.infrastructure.agents.parsers.output_parser import AgentOutputParser
from app.infrastructure.agents.prompts.builder import PromptBuilder
from app.infrastructure.llm.factory import create_llm_provider

logger = get_logger(__name__)


class ToolCallingAgentFactory:
    """
    Creates deterministic, tool-calling-only LangChain agents.

    - Ollama + Qwen2.5 by default
    - No SQL generation (enforced via prompts)
    - No autonomous behavior (bounded ReAct loop)
    - Structured output parsing
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        memory: ConversationMemoryStore | None = None,
        parser: AgentOutputParser | None = None,
    ) -> None:
        self._config = config or load_agent_config()
        self._memory = memory or ConversationMemoryStore()
        self._parser = parser or AgentOutputParser()
        self._prompt_builder = PromptBuilder(template_key=self._config.prompt_template)

    @property
    def config(self) -> AgentConfig:
        return self._config

    def create_llm(self) -> BaseChatModel:
        """Create a deterministic LLM instance for tool calling."""
        if self._config.provider == "ollama":
            logger.info(
                "creating_ollama_llm",
                model=self._config.model_name,
                temperature=self._config.temperature,
                seed=self._config.seed,
            )
            kwargs: dict = {
                "model": self._config.model_name,
                "base_url": settings.ollama_base_url,
                "temperature": self._config.temperature,
                "top_p": self._config.top_p,
                "timeout": self._config.timeout_seconds,
            }
            if self._config.seed is not None:
                kwargs["seed"] = self._config.seed
            return ChatOllama(**kwargs)

        provider = create_llm_provider()
        return provider.get_chat_model()

    def create_agent(self, tools: list[StructuredTool]):
        """Build a LangGraph ReAct agent bound to the provided tools only."""
        if not tools:
            raise LLMProviderError("Cannot create agent without tools")

        llm = self.create_llm()
        agent = create_react_agent(llm, tools)
        logger.info("agent_created", tool_count=len(tools), model=self._config.model_name)
        return agent

    def build_system_prompt(
        self,
        *,
        user_display_name: str | None = None,
        available_tools: list[str] | None = None,
    ) -> str:
        return self._prompt_builder.build_system_prompt(
            user_display_name=user_display_name,
            available_tools=available_tools,
        )

    def get_parser(self) -> AgentOutputParser:
        return self._parser

    def get_memory(self) -> ConversationMemoryStore:
        return self._memory
