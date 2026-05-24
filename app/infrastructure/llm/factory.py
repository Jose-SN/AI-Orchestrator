"""LLM provider factory."""

from app.core.config import LLMProvider as LLMProviderEnum
from app.core.config import settings
from app.core.exceptions import LLMProviderError
from app.infrastructure.llm.providers.ollama import OllamaProvider
from app.infrastructure.llm.providers.openai import OpenAIProvider


def create_llm_provider():
    if settings.llm_provider == LLMProviderEnum.OLLAMA:
        return OllamaProvider()
    if settings.llm_provider == LLMProviderEnum.OPENAI:
        return OpenAIProvider()
    raise LLMProviderError(f"Unsupported LLM provider: {settings.llm_provider}")
