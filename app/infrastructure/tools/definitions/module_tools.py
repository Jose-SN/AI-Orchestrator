"""Module-related tools — call Module microservice APIs."""

import json

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.infrastructure.http.clients.microservices import ModuleServiceClient
from app.infrastructure.tools.registry import register_tool

logger = get_logger(__name__)
_module_client = ModuleServiceClient()


class ListModulesInput(BaseModel):
    pass


@register_tool(
    name="list_modules",
    description=(
        "List all application modules the user has access to. "
        "Use when the user asks about available modules, features, or app sections."
    ),
    required_permissions=["modules:read"],
    service="module-service",
    category="modules",
    args_schema=ListModulesInput,
)
async def list_modules(
    *,
    token: str,
    user_id: str,  # noqa: ARG001
) -> str:
    logger.info("tool_list_modules")
    try:
        data = await _module_client.get("/api/v1/modules", token=token)
        return json.dumps(data, default=str)
    except Exception as exc:
        logger.error("tool_list_modules_failed", error=str(exc))
        return f"Unable to list modules: {exc}"


class GetModulePermissionsInput(BaseModel):
    module_id: str = Field(description="The module ID to fetch permissions for")


@register_tool(
    name="get_module_permissions",
    description=(
        "Get permissions assigned to a specific module. "
        "Use when the user asks about module access, permissions, or capabilities."
    ),
    required_permissions=["modules:read", "permissions:read"],
    service="module-service",
    category="modules",
    args_schema=GetModulePermissionsInput,
)
async def get_module_permissions(
    *,
    token: str,
    user_id: str,  # noqa: ARG001
    module_id: str,
) -> str:
    logger.info("tool_get_module_permissions", module_id=module_id)
    try:
        data = await _module_client.get(
            f"/api/v1/modules/{module_id}/permissions",
            token=token,
        )
        return json.dumps(data, default=str)
    except Exception as exc:
        logger.error("tool_get_module_permissions_failed", error=str(exc))
        return f"Unable to get module permissions: {exc}"
