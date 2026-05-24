"""Application-specific exception hierarchy."""

from typing import Any


class OrchestratorError(Exception):
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
    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        super().__init__(message, code="AUTHENTICATION_ERROR", **kwargs)


class AuthorizationError(OrchestratorError):
    def __init__(self, message: str = "Insufficient permissions", **kwargs: Any) -> None:
        super().__init__(message, code="AUTHORIZATION_ERROR", **kwargs)


class IAMServiceError(OrchestratorError):
    def __init__(self, message: str = "IAM service error", **kwargs: Any) -> None:
        super().__init__(message, code="IAM_SERVICE_ERROR", **kwargs)


class DownstreamServiceError(OrchestratorError):
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
    def __init__(self, message: str = "LLM provider error", **kwargs: Any) -> None:
        super().__init__(message, code="LLM_PROVIDER_ERROR", **kwargs)


class AgentExecutionError(OrchestratorError):
    def __init__(self, message: str = "Agent execution failed", **kwargs: Any) -> None:
        super().__init__(message, code="AGENT_EXECUTION_ERROR", **kwargs)


class ToolNotFoundError(OrchestratorError):
    def __init__(self, tool_name: str, **kwargs: Any) -> None:
        super().__init__(
            f"Tool '{tool_name}' is not registered",
            code="TOOL_NOT_FOUND",
            details={"tool_name": tool_name},
            **kwargs,
        )


class ValidationError(OrchestratorError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)
