"""Ollama LLM provider — local open-source models (Qwen2.5)."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaProvider:
    """Ollama-backed LLM provider for local inference."""

    def __init__(self) -> None:
        self._model: BaseChatModel | None = None

    @property
    def provider_name(self) -> str:
        return "ollama"

    def get_chat_model(self) -> BaseChatModel:
        if self._model is None:
            logger.info(
                "initializing_ollama",
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
            )
            self._model = ChatOllama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=settings.ollama_temperature,
                timeout=settings.ollama_timeout_seconds,
            )
        return self._model
