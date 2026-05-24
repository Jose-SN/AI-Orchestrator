"""LLM provider protocol."""

from typing import Protocol

from langchain_core.language_models.chat_models import BaseChatModel


class LLMProvider(Protocol):
    """Contract for LLM provider implementations."""

    def get_chat_model(self) -> BaseChatModel:
        """Return a LangChain chat model instance."""
        ...

    @property
    def provider_name(self) -> str:
        """Human-readable provider identifier."""
        ...
