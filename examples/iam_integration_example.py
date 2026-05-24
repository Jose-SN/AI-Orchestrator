"""
IAM integration examples for the AI Orchestrator.

These examples show how IAM drives dynamic tool availability.
"""

import asyncio

from app.application.permissions.service import PermissionService
from app.application.tools.service import ToolRegistryService
from app.domain.auth.models import UserContext, ModuleAccess
from app.infrastructure.iam.cache import IAMPermissionCache
from app.infrastructure.iam.client import IAMClient
from app.infrastructure.iam.schemas import parse_iam_profile
from app.infrastructure.tools.loader import load_all_tools


# ── Example 1: Parse IAM API response ───────────────────────────────────────

def example_parse_iam_response():
    iam_json = {
        "userId": "user-42",
        "email": "admin@petax.ai",
        "permissions": ["customers:read", "customers:create"],
        "modulePermissions": ["modules:read"],
        "modules": [
            {"moduleId": "crm", "moduleName": "CRM", "permissions": ["customers:read"]},
        ],
        "allowedActions": ["customers:search"],
    }
    profile = parse_iam_profile(iam_json)
    user = UserContext.from_profile(profile)
    print("Effective permissions:", user.effective_permissions)
    # → ['customers:create', 'customers:read', 'customers:search', 'modules:read']


# ── Example 2: Permission-aware tool loading ────────────────────────────────

def example_dynamic_tool_loading():
    load_all_tools()
    user = UserContext(
        user_id="user-42",
        permissions=["customers:read"],
        allowed_actions=["customers:search"],
    )

    tool_service = ToolRegistryService()
    snapshot = tool_service.get_snapshot(user)
    print("Allowed tools:", snapshot.allowed_tools)
    print("Denied tools:", snapshot.denied_tools)


# ── Example 3: Full IAM client flow (requires running IAM service) ──────────

async def example_iam_client_flow(token: str):
    client = IAMClient(cache=IAMPermissionCache(ttl_seconds=300))

    validation = await client.validate_token(token)
    print("Token valid:", validation.valid)

    modules = await client.fetch_module_access(token)
    print("Modules:", [m.module_id for m in modules])

    actions = await client.fetch_allowed_actions(token)
    print("Actions:", actions)

    user = await client.resolve_user_context(token)
    print("User:", user.user_id, "permissions:", len(user.effective_permissions))

    permission_service = PermissionService(client, ToolRegistryService())
    tools = permission_service.get_allowed_tools(user)
    print("Agent will receive tools:", tools)

    await client.close()


# ── Example 4: Module access check ──────────────────────────────────────────

def example_module_access_check():
    user = UserContext(
        user_id="user-1",
        modules=[ModuleAccess(module_id="crm", module_name="CRM", permissions=["customers:read"])],
    )
    print("Has CRM access:", user.has_module_access("crm"))
    print("Has billing access:", user.has_module_access("billing"))


if __name__ == "__main__":
    example_parse_iam_response()
    example_dynamic_tool_loading()
    example_module_access_check()
    # asyncio.run(example_iam_client_flow("your-jwt-token-here"))
