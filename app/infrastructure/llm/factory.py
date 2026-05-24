"""LLM provider factory."""

from app.core.config import LLMProvider as LLMProviderEnum
from app.core.config import settings
from app.core.exceptions import LLMProviderError
from app.infrastructure.llm.base import LLMProvider
from app.infrastructure.llm.ollama_provider import OllamaProvider
from app.infrastructure.llm.openai_provider import OpenAIProvider


def create_llm_provider() -> LLMProvider:
    """Instantiate the configured LLM provider."""
    if settings.llm_provider == LLMProviderEnum.OLLAMA:
        return OllamaProvider()
    if settings.llm_provider == LLMProviderEnum.OPENAI:
        return OpenAIProvider()
    raise LLMProviderError(f"Unsupported LLM provider: {settings.llm_provider}")
