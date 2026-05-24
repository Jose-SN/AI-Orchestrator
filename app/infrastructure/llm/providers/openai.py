"""OpenAI LLM provider."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider:
    def __init__(self) -> None:
        self._model: BaseChatModel | None = None

    @property
    def provider_name(self) -> str:
        return "openai"

    def get_chat_model(self) -> BaseChatModel:
        if not settings.openai_api_key:
            raise LLMProviderError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self._model is None:
            logger.info("initializing_openai", model=settings.openai_model)
            self._model = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=settings.openai_temperature,
            )
        return self._model
