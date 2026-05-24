"""Module tools — call Module microservice APIs."""

from pydantic import BaseModel, Field

from app.domain.tools.context import ToolExecutionContext
from app.domain.tools.models import ToolOperation
from app.infrastructure.http.clients.microservices import ModuleServiceClient
from app.infrastructure.tools.base.api_tool import BaseAPITool
from app.infrastructure.tools.decorators import orchestrator_tool

_module_api = BaseAPITool(ModuleServiceClient())
_module_api.service_name = "module-service"
_module_api.resource_path = "/api/v1/modules"


class GetModulePermissionsInput(BaseModel):
    module_id: str = Field(description="The module ID to fetch permissions for")


class ListModulesInput(BaseModel):
    pass


@orchestrator_tool(
    name="list_modules",
    description="List all application modules the user has access to.",
    required_permissions=["modules:read"],
    service="module-service",
    operation=ToolOperation.LIST,
    category="modules",
    args_schema=ListModulesInput,
)
async def list_modules(ctx: ToolExecutionContext):
    return await _module_api.list(ctx, tool_name="list_modules")


@orchestrator_tool(
    name="get_module_permissions",
    description="Get permissions assigned to a specific module.",
    required_permissions=["modules:read", "permissions:read"],
    service="module-service",
    operation=ToolOperation.GET,
    category="modules",
    args_schema=GetModulePermissionsInput,
)
async def get_module_permissions(ctx: ToolExecutionContext, module_id: str):
    client = ModuleServiceClient()
    try:
        data = await client.get(f"/api/v1/modules/{module_id}/permissions", token=ctx.token)
        from app.domain.tools.response import ToolResponse
        return ToolResponse.ok(
            tool_name="get_module_permissions",
            operation=ToolOperation.GET,
            data=data,
            trace_id=ctx.trace_id,
        )
    finally:
        await client.close()
