"""Application settings loaded from environment variables."""

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"


class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Central configuration — never hardcode secrets or URLs in code."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="AI Orchestrator", alias="APP_NAME")
    app_env: AppEnvironment = Field(default=AppEnvironment.DEVELOPMENT, alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=False, alias="LOG_JSON")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ORIGINS",
    )

    # LLM
    llm_provider: LLMProvider = Field(default=LLMProvider.OLLAMA, alias="LLM_PROVIDER")

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:7b", alias="OLLAMA_MODEL")
    ollama_temperature: float = Field(default=0.1, alias="OLLAMA_TEMPERATURE")
    ollama_timeout_seconds: int = Field(default=120, alias="OLLAMA_TIMEOUT_SECONDS")

    # OpenAI (future)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.1, alias="OPENAI_TEMPERATURE")

    # IAM
    iam_service_url: str = Field(default="http://localhost:3001", alias="IAM_SERVICE_URL")
    iam_permissions_path: str = Field(
        default="/api/v1/auth/permissions",
        alias="IAM_PERMISSIONS_PATH",
    )
    iam_validate_token_path: str = Field(
        default="/api/v1/auth/validate",
        alias="IAM_VALIDATE_TOKEN_PATH",
    )
    iam_timeout_seconds: int = Field(default=10, alias="IAM_TIMEOUT_SECONDS")

    # Microservices
    user_service_url: str = Field(default="http://localhost:8001", alias="USER_SERVICE_URL")
    module_service_url: str = Field(
        default="http://localhost:8002",
        alias="MODULE_SERVICE_URL",
    )

    # Agent
    agent_max_iterations: int = Field(default=10, alias="AGENT_MAX_ITERATIONS")
    agent_verbose: bool = Field(default=False, alias="AGENT_VERBOSE")

    # Future channels
    whatsapp_enabled: bool = Field(default=False, alias="WHATSAPP_ENABLED")
    whatsapp_webhook_path: str = Field(
        default="/webhooks/whatsapp",
        alias="WHATSAPP_WEBHOOK_PATH",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnvironment.PRODUCTION

    @property
    def iam_permissions_url(self) -> str:
        return f"{self.iam_service_url.rstrip('/')}{self.iam_permissions_path}"

    @property
    def iam_validate_token_url(self) -> str:
        return f"{self.iam_service_url.rstrip('/')}{self.iam_validate_token_path}"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


settings: Settings = get_settings()
