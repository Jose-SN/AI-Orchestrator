"""Base class for HTTP API-backed tools."""

from typing import Any

from app.core.exceptions import DownstreamServiceError
from app.domain.tools.context import ToolExecutionContext
from app.domain.tools.models import ToolOperation
from app.domain.tools.response import ToolResponse
from app.infrastructure.http.clients.base import BaseHTTPClient


class BaseAPITool:
    """
    Reusable base for tools that call existing microservice HTTP APIs.

    Subclasses define service client and path templates. Never accesses databases.
    """

    service_name: str = "unknown"
    resource_path: str = "/api/v1/resources"

    def __init__(self, client: BaseHTTPClient) -> None:
        self._client = client

    async def get(
        self,
        ctx: ToolExecutionContext,
        resource_id: str,
        *,
        tool_name: str,
    ) -> ToolResponse:
        return await self._execute(
            ctx, tool_name=tool_name, operation=ToolOperation.GET,
            handler=lambda: self._client.get(f"{self.resource_path}/{resource_id}", token=ctx.token),
        )

    async def list(
        self,
        ctx: ToolExecutionContext,
        *,
        tool_name: str,
        params: dict[str, Any] | None = None,
    ) -> ToolResponse:
        return await self._execute(
            ctx, tool_name=tool_name, operation=ToolOperation.LIST,
            handler=lambda: self._client.get(self.resource_path, token=ctx.token, params=params),
        )

    async def search(
        self,
        ctx: ToolExecutionContext,
        *,
        tool_name: str,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> ToolResponse:
        search_params = {"search": query, **(params or {})}
        return await self._execute(
            ctx, tool_name=tool_name, operation=ToolOperation.SEARCH,
            handler=lambda: self._client.get(
                f"{self.resource_path}/search", token=ctx.token, params=search_params
            ),
        )

    async def create(
        self,
        ctx: ToolExecutionContext,
        payload: dict[str, Any],
        *,
        tool_name: str,
    ) -> ToolResponse:
        return await self._execute(
            ctx, tool_name=tool_name, operation=ToolOperation.CREATE,
            handler=lambda: self._client.post(self.resource_path, token=ctx.token, json=payload),
        )

    async def update(
        self,
        ctx: ToolExecutionContext,
        resource_id: str,
        payload: dict[str, Any],
        *,
        tool_name: str,
    ) -> ToolResponse:
        return await self._execute(
            ctx, tool_name=tool_name, operation=ToolOperation.UPDATE,
            handler=lambda: self._client.put(
                f"{self.resource_path}/{resource_id}", token=ctx.token, json=payload
            ),
        )

    async def delete(
        self,
        ctx: ToolExecutionContext,
        resource_id: str,
        *,
        tool_name: str,
    ) -> ToolResponse:
        return await self._execute(
            ctx, tool_name=tool_name, operation=ToolOperation.DELETE,
            handler=lambda: self._client.delete(
                f"{self.resource_path}/{resource_id}", token=ctx.token
            ),
        )

    async def _execute(
        self,
        ctx: ToolExecutionContext,
        *,
        tool_name: str,
        operation: ToolOperation,
        handler,
    ) -> ToolResponse:
        try:
            data = await handler()
            return ToolResponse.ok(
                tool_name=tool_name,
                operation=operation,
                data=data,
                trace_id=ctx.trace_id,
            )
        except DownstreamServiceError as exc:
            return ToolResponse.fail(
                tool_name=tool_name,
                operation=operation,
                error=str(exc.message),
                error_code="DOWNSTREAM_ERROR",
                trace_id=ctx.trace_id,
            )
