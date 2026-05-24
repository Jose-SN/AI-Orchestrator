"""Application-specific exception hierarchy."""

from typing import Any


class OrchestratorError(Exception):
    """Base exception for all orchestrator errors."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "ORCHESTRATOR_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class AuthenticationError(OrchestratorError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        super().__init__(message, code="AUTHENTICATION_ERROR", **kwargs)


class AuthorizationError(OrchestratorError):
    """Raised when the user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions", **kwargs: Any) -> None:
        super().__init__(message, code="AUTHORIZATION_ERROR", **kwargs)


class IAMServiceError(OrchestratorError):
    """Raised when the IAM service is unreachable or returns an error."""

    def __init__(self, message: str = "IAM service error", **kwargs: Any) -> None:
        super().__init__(message, code="IAM_SERVICE_ERROR", **kwargs)


class DownstreamServiceError(OrchestratorError):
    """Raised when a downstream microservice call fails."""

    def __init__(
        self,
        message: str,
        *,
        service: str,
        status_code: int | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {}) or {}
        details.update({"service": service, "status_code": status_code})
        super().__init__(message, code="DOWNSTREAM_SERVICE_ERROR", details=details, **kwargs)
        self.service = service
        self.status_code = status_code


class LLMProviderError(OrchestratorError):
    """Raised when the LLM provider fails."""

    def __init__(self, message: str = "LLM provider error", **kwargs: Any) -> None:
        super().__init__(message, code="LLM_PROVIDER_ERROR", **kwargs)


class AgentExecutionError(OrchestratorError):
    """Raised when the LangChain agent fails during execution."""

    def __init__(self, message: str = "Agent execution failed", **kwargs: Any) -> None:
        super().__init__(message, code="AGENT_EXECUTION_ERROR", **kwargs)


class ToolNotFoundError(OrchestratorError):
    """Raised when a requested tool is not registered."""

    def __init__(self, tool_name: str, **kwargs: Any) -> None:
        super().__init__(
            f"Tool '{tool_name}' is not registered",
            code="TOOL_NOT_FOUND",
            details={"tool_name": tool_name},
            **kwargs,
        )


class ValidationError(OrchestratorError):
    """Raised for domain validation failures."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)
