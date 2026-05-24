from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AgentExecutionError,
    AuthenticationError,
    AuthorizationError,
    DownstreamServiceError,
    IAMServiceError,
    LLMProviderError,
    OrchestratorError,
    ValidationError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(_request: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(AuthorizationError)
    async def authz_error_handler(_request: Request, exc: AuthorizationError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(ValidationError)
    async def validation_error_handler(_request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(IAMServiceError)
    async def iam_error_handler(_request: Request, exc: IAMServiceError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(DownstreamServiceError)
    async def downstream_error_handler(_request: Request, exc: DownstreamServiceError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(LLMProviderError)
    async def llm_error_handler(_request: Request, exc: LLMProviderError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(AgentExecutionError)
    async def agent_error_handler(_request: Request, exc: AgentExecutionError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(OrchestratorError)
    async def orchestrator_error_handler(_request: Request, exc: OrchestratorError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(status_code=500, content={"error": "INTERNAL_SERVER_ERROR", "message": "Unexpected error"})
