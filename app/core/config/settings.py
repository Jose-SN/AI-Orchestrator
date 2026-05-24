"""Application settings loaded from environment variables."""

from enum import Enum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"


class VectorStoreProvider(str, Enum):
    NONE = "none"
    QDRANT = "qdrant"
    PGVECTOR = "pgvector"


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

    # Logging & audit
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=False, alias="LOG_JSON")
    audit_enabled: bool = Field(default=True, alias="AUDIT_ENABLED")

    # Observability / tracing
    otel_enabled: bool = Field(default=False, alias="OTEL_ENABLED")
    otel_service_name: str = Field(default="ai-orchestrator", alias="OTEL_SERVICE_NAME")
    otel_exporter_endpoint: str = Field(default="", alias="OTEL_EXPORTER_ENDPOINT")

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000"], alias="CORS_ORIGINS")

    # LLM
    llm_provider: LLMProvider = Field(default=LLMProvider.OLLAMA, alias="LLM_PROVIDER")

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:7b", alias="OLLAMA_MODEL")
    ollama_temperature: float = Field(default=0.1, alias="OLLAMA_TEMPERATURE")
    ollama_timeout_seconds: int = Field(default=120, alias="OLLAMA_TIMEOUT_SECONDS")

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.1, alias="OPENAI_TEMPERATURE")

    # Vector store (future RAG)
    vector_store_provider: VectorStoreProvider = Field(
        default=VectorStoreProvider.NONE,
        alias="VECTOR_STORE_PROVIDER",
    )
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="orchestrator", alias="QDRANT_COLLECTION")

    # IAM
    iam_service_url: str = Field(default="http://localhost:3001", alias="IAM_SERVICE_URL")
    iam_permissions_path: str = Field(default="/api/v1/auth/permissions", alias="IAM_PERMISSIONS_PATH")
    iam_validate_token_path: str = Field(
        default="/api/v1/auth/validate",
        alias="IAM_VALIDATE_TOKEN_PATH",
    )
    iam_timeout_seconds: int = Field(default=10, alias="IAM_TIMEOUT_SECONDS")
    iam_cache_ttl_seconds: int = Field(default=300, alias="IAM_CACHE_TTL_SECONDS")
    iam_retry_attempts: int = Field(default=3, alias="IAM_RETRY_ATTEMPTS")
    iam_modules_path: str = Field(default="/api/v1/auth/modules", alias="IAM_MODULES_PATH")
    iam_actions_path: str = Field(default="/api/v1/auth/actions", alias="IAM_ACTIONS_PATH")

    # Microservices
    user_service_url: str = Field(default="http://localhost:8001", alias="USER_SERVICE_URL")
    module_service_url: str = Field(default="http://localhost:8002", alias="MODULE_SERVICE_URL")
    customer_service_url: str = Field(default="http://localhost:8003", alias="CUSTOMER_SERVICE_URL")

    # Agents
    agent_max_iterations: int = Field(default=8, alias="AGENT_MAX_ITERATIONS")
    agent_max_tool_calls: int = Field(default=5, alias="AGENT_MAX_TOOL_CALLS")
    agent_temperature: float = Field(default=0.0, alias="AGENT_TEMPERATURE")
    agent_top_p: float = Field(default=1.0, alias="AGENT_TOP_P")
    agent_seed: int | None = Field(default=42, alias="AGENT_SEED")
    agent_prompt_template: str = Field(default="orchestrator", alias="AGENT_PROMPT_TEMPLATE")
    agent_memory_enabled: bool = Field(default=False, alias="AGENT_MEMORY_ENABLED")
    agent_verbose: bool = Field(default=False, alias="AGENT_VERBOSE")
    default_agent_id: str = Field(default="orchestrator", alias="DEFAULT_AGENT_ID")

    # Channels
    whatsapp_enabled: bool = Field(default=False, alias="WHATSAPP_ENABLED")
    whatsapp_webhook_path: str = Field(default="/webhooks/whatsapp", alias="WHATSAPP_WEBHOOK_PATH")
    websocket_enabled: bool = Field(default=False, alias="WEBSOCKET_ENABLED")

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
    return Settings()


settings: Settings = get_settings()
