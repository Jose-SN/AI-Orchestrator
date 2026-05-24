"""IAM API response parsing — infrastructure layer."""

from typing import Any

from pydantic import BaseModel, Field

from app.domain.auth.models import IAMUserProfile, ModuleAccess


class TokenValidationResult(BaseModel):
    valid: bool = True
    user_id: str | None = None
    expires_at: str | None = None
    roles: list[str] = Field(default_factory=list)


def parse_iam_profile(data: dict[str, Any]) -> IAMUserProfile:
    """Parse IAM API response into a domain profile."""
    modules_raw = data.get("modules") or data.get("moduleAccess") or []
    modules = [
        ModuleAccess(
            module_id=str(m.get("moduleId") or m.get("module_id") or m.get("id", "")),
            module_name=m.get("moduleName") or m.get("module_name") or m.get("name"),
            permissions=m.get("permissions", []),
            enabled=m.get("enabled", True),
        )
        for m in modules_raw
        if isinstance(m, dict)
    ]

    module_perms: list[str] = list(data.get("modulePermissions") or data.get("module_permissions") or [])
    for mod in modules:
        module_perms.extend(mod.permissions)

    allowed_actions = list(
        data.get("allowedActions") or data.get("allowed_actions") or data.get("actions") or []
    )

    return IAMUserProfile(
        user_id=str(data.get("userId") or data.get("user_id") or data.get("id", "")),
        email=data.get("email"),
        display_name=data.get("displayName") or data.get("display_name"),
        roles=data.get("roles", []),
        permissions=data.get("permissions", []),
        module_permissions=list(set(module_perms)),
        modules=modules,
        allowed_actions=allowed_actions,
    )
